"""
Implementation Guide: Individual Item QR Codes
This file shows the code changes needed to implement individual item QR codes
"""

# ============================================================================
# 1. DATABASE SCHEMA CHANGES
# ============================================================================

def init_db():
    """Modified init_db to include items table"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Existing tables (keep as is)
    # ... users, products, orders, cart tables ...
    
    # NEW: Items table for individual stock items
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            qr_code TEXT UNIQUE NOT NULL,
            status TEXT DEFAULT 'available' CHECK(status IN ('available', 'reserved', 'sold', 'damaged')),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            order_id INTEGER NULL,
            FOREIGN KEY (product_id) REFERENCES products(id),
            FOREIGN KEY (order_id) REFERENCES orders(id)
        )
    ''')
    
    # Remove qr_code from products table (optional - can keep for backward compatibility)
    # Products now don't need individual QR codes, items have them
    
    conn.commit()
    cursor.close()
    conn.close()


# ============================================================================
# 2. HELPER FUNCTIONS
# ============================================================================

def generate_unique_item_qr_code():
    """Generate unique QR code for individual item"""
    import secrets
    qr_code = secrets.token_urlsafe(16)
    max_attempts = 50
    attempts = 0
    is_duplicate = True
    
    while is_duplicate and attempts < max_attempts:
        # Check in items table
        dup_in_items = query_db('SELECT id FROM items WHERE qr_code = ?', (qr_code,), one=True)
        
        # Check in products table
        dup_in_products = query_db('SELECT id FROM products WHERE qr_code = ?', (qr_code,), one=True)
        
        # Check in orders table
        dup_in_orders = query_db('SELECT id FROM orders WHERE qr_code = ?', (qr_code,), one=True)
        
        if dup_in_items or dup_in_products or dup_in_orders:
            qr_code = secrets.token_urlsafe(16)
            attempts += 1
        else:
            is_duplicate = False
    
    if attempts >= max_attempts:
        raise Exception("Failed to generate unique QR code after 50 attempts")
    
    return qr_code


def get_product_stock(product_id):
    """Get available stock count from items table"""
    count = query_db(
        'SELECT COUNT(*) as count FROM items WHERE product_id = ? AND status = ?',
        (product_id, 'available'),
        one=True
    )
    return count['count'] if count else 0


def update_product_stock(product_id):
    """Update product stock from items count"""
    query_db('''
        UPDATE products 
        SET stock = (SELECT COUNT(*) FROM items WHERE product_id = ? AND status = 'available')
        WHERE id = ?
    ''', (product_id, product_id))


# ============================================================================
# 3. MODIFIED: Admin Add Product
# ============================================================================

@app.route('/admin/products', methods=['GET', 'POST'])
def admin_products():
    if 'loggedin' not in session or session['user_type'] != 'admin':
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        category = request.form['category']
        size = request.form['size']
        color = request.form['color']
        stock_quantity = int(request.form['stock'])  # Number of items to create
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Check if product exists
        cursor.execute(
            'SELECT id FROM products WHERE category = ? AND size = ? AND color = ?',
            (category, size, color)
        )
        existing = cursor.fetchone()
        
        if existing:
            # Product exists - add more items
            product_id = existing['id']
        else:
            # Create new product (stock will be calculated from items)
            image_url = get_product_image_url(category, color)
            cursor.execute(
                'INSERT INTO products (category, size, color, stock, image_url) VALUES (?, ?, ?, 0, ?)',
                (category, size, color, image_url)
            )
            product_id = cursor.lastrowid
        
        # Create individual items with unique QR codes
        items_created = 0
        for i in range(stock_quantity):
            try:
                item_qr_code = generate_unique_item_qr_code()
                cursor.execute(
                    'INSERT INTO items (product_id, qr_code, status) VALUES (?, ?, ?)',
                    (product_id, item_qr_code, 'available')
                )
                items_created += 1
            except Exception as e:
                print(f"Error creating item {i+1}: {e}")
                # Continue with next item
        
        # Update product stock count
        update_product_stock(product_id)
        
        conn.commit()
        cursor.close()
        conn.close()
        
        flash(f'Product added/updated successfully! {items_created} items created with unique QR codes.', 'success')
        return redirect(url_for('admin_products'))
    
    # GET request - show products
    products = query_db('SELECT * FROM products ORDER BY category, color, size')
    products = [dict(row) for row in products]
    
    # Update stock counts from items
    for product in products:
        product['stock'] = get_product_stock(product['id'])
    
    return render_template('admin/products.html', products=products)


# ============================================================================
# 4. MODIFIED: Checkout (Customer)
# ============================================================================

@app.route('/checkout', methods=['POST'])
def checkout():
    if 'loggedin' not in session or session['user_type'] != 'customer':
        return redirect(url_for('login'))
    
    # Get cart items
    cart_items = query_db('''
        SELECT c.product_id, c.quantity
        FROM cart c
        WHERE c.user_id = ?
    ''', (session['id'],))
    cart_items = [dict(row) for row in cart_items]
    
    # Validate stock availability
    for item in cart_items:
        available_stock = get_product_stock(item['product_id'])
        if item['quantity'] > available_stock:
            flash(f'Insufficient stock. Available: {available_stock}, Requested: {item["quantity"]}', 'error')
            return redirect(url_for('cart'))
    
    # Generate unique order QR code
    order_qr_code = secrets.token_urlsafe(16)
    max_attempts = 50
    attempts = 0
    is_duplicate = True
    
    while is_duplicate and attempts < max_attempts:
        dup_order = query_db('SELECT id FROM orders WHERE qr_code = ?', (order_qr_code,), one=True)
        dup_product = query_db('SELECT id FROM products WHERE qr_code = ?', (order_qr_code,), one=True)
        dup_item = query_db('SELECT id FROM items WHERE qr_code = ?', (order_qr_code,), one=True)
        
        if dup_order or dup_product or dup_item:
            order_qr_code = secrets.token_urlsafe(16)
            attempts += 1
        else:
            is_duplicate = False
    
    if attempts >= max_attempts:
        flash('Error generating unique order QR code. Please try again.', 'error')
        return redirect(url_for('cart'))
    
    # Create order
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute(
        'INSERT INTO orders (user_id, qr_code, status) VALUES (?, ?, ?)',
        (session['id'], order_qr_code, 'pending')
    )
    order_id = cursor.lastrowid
    
    # Reserve items for this order
    for item in cart_items:
        # Get available items for this product
        available_items = query_db('''
            SELECT id, qr_code 
            FROM items 
            WHERE product_id = ? AND status = 'available'
            LIMIT ?
        ''', (item['product_id'], item['quantity']))
        
        if len(available_items) < item['quantity']:
            # Rollback - not enough items available
            conn.rollback()
            cursor.close()
            conn.close()
            flash(f'Insufficient stock for product ID {item["product_id"]}. Please try again.', 'error')
            return redirect(url_for('cart'))
        
        # Reserve items (assign to order)
        for item_record in available_items:
            cursor.execute(
                'UPDATE items SET status = ?, order_id = ? WHERE id = ?',
                ('reserved', order_id, item_record['id'])
            )
    
    # Clear cart
    cursor.execute('DELETE FROM cart WHERE user_id = ?', (session['id'],))
    
    # Update product stock counts
    product_ids = set(item['product_id'] for item in cart_items)
    for product_id in product_ids:
        cursor.execute('''
            UPDATE products 
            SET stock = (SELECT COUNT(*) FROM items WHERE product_id = ? AND status = 'available')
            WHERE id = ?
        ''', (product_id, product_id))
    
    conn.commit()
    cursor.close()
    conn.close()
    
    flash('Order placed successfully! Waiting for approval.', 'success')
    return redirect(url_for('orders'))


# ============================================================================
# 5. MODIFIED: Order Approval
# ============================================================================

@app.route('/approval/approve_order/<int:order_id>', methods=['POST'])
def approve_order(order_id):
    if 'loggedin' not in session or session['user_type'] != 'approval_admin':
        return redirect(url_for('login'))
    
    try:
        # Get order
        order = query_db('SELECT qr_code FROM orders WHERE id = ?', (order_id,), one=True)
        if not order:
            flash('Order not found', 'error')
            return redirect(url_for('approval_orders'))
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Update order status
        cursor.execute('UPDATE orders SET status = ? WHERE id = ?', ('confirmed', order_id))
        
        # Update items: reserved → sold
        cursor.execute(
            'UPDATE items SET status = ? WHERE order_id = ? AND status = ?',
            ('sold', order_id, 'reserved')
        )
        
        # Get product IDs that had items in this order
        product_ids = query_db('SELECT DISTINCT product_id FROM items WHERE order_id = ?', (order_id,))
        
        # Update product stock counts
        for product in product_ids:
            cursor.execute('''
                UPDATE products 
                SET stock = (SELECT COUNT(*) FROM items WHERE product_id = ? AND status = 'available')
                WHERE id = ?
            ''', (product['product_id'], product['product_id']))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        flash('Order confirmed successfully! Items marked as sold.', 'success')
        return redirect(url_for('approval_orders'))
    except Exception as e:
        print(f"Error approving order: {e}")
        flash(f'Error processing order: {str(e)}', 'error')
        return redirect(url_for('approval_orders'))


# ============================================================================
# 6. MODIFIED: Display Products (Update stock from items)
# ============================================================================

@app.route('/products')
def products():
    if 'loggedin' not in session or session['user_type'] != 'customer':
        return redirect(url_for('login'))
    
    category = request.args.get('category', 'T-Shirt')
    
    # Get products with stock calculated from items
    products_list = query_db('''
        SELECT p.*, 
               (SELECT COUNT(*) FROM items WHERE product_id = p.id AND status = 'available') as stock
        FROM products p
        WHERE p.category = ?
        HAVING stock > 0
        ORDER BY p.color, p.size
    ''', (category,))
    
    products_list = [dict(row) for row in products_list]
    
    return render_template('products.html', products=products_list, category=category)


# ============================================================================
# 7. NEW: View Individual Items (Admin)
# ============================================================================

@app.route('/admin/items/<int:product_id>')
def admin_items(product_id):
    """View all items for a specific product"""
    if 'loggedin' not in session or session['user_type'] != 'admin':
        return redirect(url_for('login'))
    
    product = query_db('SELECT * FROM products WHERE id = ?', (product_id,), one=True)
    if not product:
        flash('Product not found', 'error')
        return redirect(url_for('admin_products'))
    
    # Get all items for this product
    items = query_db('''
        SELECT i.*, o.qr_code as order_qr_code, o.status as order_status
        FROM items i
        LEFT JOIN orders o ON i.order_id = o.id
        WHERE i.product_id = ?
        ORDER BY i.status, i.created_at
    ''', (product_id,))
    items = [dict(row) for row in items]
    
    return render_template('admin/items.html', product=product, items=items)


# ============================================================================
# 8. NEW: Generate QR Code Image for Individual Item
# ============================================================================

@app.route('/admin/item_qr/<int:item_id>')
def generate_item_qr(item_id):
    """Generate QR code image for individual item"""
    if 'loggedin' not in session or session['user_type'] != 'admin':
        return redirect(url_for('login'))
    
    item = query_db('''
        SELECT i.*, p.category, p.size, p.color
        FROM items i
        JOIN products p ON i.product_id = p.id
        WHERE i.id = ?
    ''', (item_id,), one=True)
    
    if not item:
        flash('Item not found', 'error')
        return redirect(url_for('admin_products'))
    
    # Generate QR code image
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(item['qr_code'])
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    img_buffer = BytesIO()
    img.save(img_buffer, format='PNG')
    img_str = base64.b64encode(img_buffer.getvalue()).decode()
    
    item_info = f"{item['category']} {item['size']} {item['color']} - Item #{item['id']}"
    
    return render_template('admin/item_qr.html', 
                         item=item,
                         qr_code=item['qr_code'], 
                         qr_image=img_str,
                         item_info=item_info)























