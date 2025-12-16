from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import sqlite3
import secrets
import qrcode
from io import BytesIO
import base64
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this-in-production'

# SQLite Database Configuration
# For serverless (Vercel): use /tmp directory
# For traditional hosting (Railway, Render, etc): use current directory
if os.environ.get('VERCEL_ENV') or os.environ.get('VERCEL'):
    DATABASE = '/tmp/qr_app.db'
    try:
        os.makedirs('/tmp', exist_ok=True)
    except Exception as e:
        print(f"⚠ Warning: Could not create /tmp directory: {e}")
else:
    # Use persistent storage for traditional hosting
    DATABASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'qr_app.db')

# Helper function to get database connection
def get_db():
    """Get database connection with error handling to prevent function crashes"""
    try:
        # Add timeout to prevent hanging on locked database
        conn = sqlite3.connect(DATABASE, timeout=10.0)
        conn.row_factory = sqlite3.Row  # This makes rows behave like dicts
        return conn
    except sqlite3.Error as e:
        print(f"❌ Database connection error: {e}")
        # Re-raise to be caught by route handlers
        raise
    except Exception as e:
        print(f"❌ Unexpected error connecting to database: {e}")
        raise

# Helper function to execute queries and return dict-like results
def query_db(query, args=(), one=False):
    """Execute database query with error handling"""
    conn = None
    try:
        conn = get_db()
        cur = conn.execute(query, args)
        rv = cur.fetchall()
        conn.commit()
        cur.close()
        return (rv[0] if rv else None) if one else rv
    except sqlite3.Error as e:
        print(f"❌ Database query error: {e}")
        print(f"Query: {query[:100]}...")  # Log first 100 chars of query
        if conn:
            conn.rollback()
        raise  # Re-raise to be caught by route handlers
    except Exception as e:
        print(f"❌ Unexpected error in query_db: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()

# Initialize database tables
def init_db():
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                user_type TEXT NOT NULL CHECK(user_type IN ('customer', 'admin', 'approval_admin')),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Products table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                size TEXT NOT NULL,
                color TEXT NOT NULL,
                stock INTEGER NOT NULL DEFAULT 0,
                qr_code TEXT UNIQUE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(category, size, color)
            )
        ''')
        
        # Add qr_code column if it doesn't exist (for existing databases)
        try:
            cursor.execute('ALTER TABLE products ADD COLUMN qr_code TEXT UNIQUE')
        except:
            pass  # Column already exists
        
        # Add image_url column if it doesn't exist
        try:
            cursor.execute('ALTER TABLE products ADD COLUMN image_url TEXT')
        except:
            pass  # Column already exists
        
        # Orders table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL DEFAULT 1,
                qr_code TEXT UNIQUE,
                status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'approved', 'confirmed', 'cancelled')),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (product_id) REFERENCES products(id)
            )
        ''')
        
        # Cart table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cart (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (product_id) REFERENCES products(id)
            )
        ''')
        
        conn.commit()
        cursor.close()
        conn.close()
        
        # Create default users if they don't exist
        create_default_users()
        print("Database initialized successfully!")
    except Exception as e:
        print(f"Error initializing database: {e}")
        print("\nThe app will continue but database operations may fail.")

def create_default_users():
    try:
        default_users = [
            ('customer1', 'customer123', 'customer'),
            ('admin1', 'admin123', 'admin'),
            ('approval_admin1', 'approval123', 'approval_admin')
        ]
        
        for username, password, user_type in default_users:
            existing = query_db('SELECT id FROM users WHERE username = ?', (username,), one=True)
            if not existing:
                query_db('INSERT INTO users (username, password, user_type) VALUES (?, ?, ?)',
                        (username, password, user_type))
    except Exception as e:
        print(f"Error creating default users: {e}")

# Routes

@app.route('/')
def index():
    if 'loggedin' in session:
        if session['user_type'] == 'customer':
            return redirect(url_for('homepage'))
        elif session['user_type'] == 'admin':
            return redirect(url_for('admin_dashboard'))
        elif session['user_type'] == 'approval_admin':
            return redirect(url_for('approval_dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']
        user_type = request.form.get('user_type', 'customer')
        
        account = query_db('SELECT * FROM users WHERE username = ? AND password = ? AND user_type = ?',
                          (username, password, user_type), one=True)
        
        if account:
            session['loggedin'] = True
            session['id'] = account['id']
            session['username'] = account['username']
            session['user_type'] = account['user_type']
            
            if user_type == 'customer':
                return redirect(url_for('homepage'))
            elif user_type == 'admin':
                return redirect(url_for('admin_dashboard'))
            elif user_type == 'approval_admin':
                return redirect(url_for('approval_dashboard'))
        else:
            msg = 'Incorrect username/password!'
    
    return render_template('login.html', msg=msg)

@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    session.pop('user_type', None)
    return redirect(url_for('login'))

# Customer Routes

@app.route('/homepage')
def homepage():
    if 'loggedin' not in session or session['user_type'] != 'customer':
        return redirect(url_for('login'))
    
    categories = query_db('SELECT DISTINCT category FROM products WHERE stock > 0')
    categories = [dict(row) for row in categories]
    
    return render_template('homepage.html', categories=categories, username=session['username'])

@app.route('/products')
def products():
    if 'loggedin' not in session or session['user_type'] != 'customer':
        return redirect(url_for('login'))
    
    category = request.args.get('category', 'T-Shirt')
    products_list = query_db('''
        SELECT * FROM products 
        WHERE category = ? AND stock > 0
        ORDER BY color, size
    ''', (category,))
    products_list = [dict(row) for row in products_list]
    
    # Ensure all products have image URLs based on category
    for product in products_list:
        if not product.get('image_url') or product.get('image_url') == '' or product.get('image_url') is None:
            product['image_url'] = get_product_image_url(product['category'], product['color'])
    
    return render_template('products.html', products=products_list, category=category)

@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    if 'loggedin' not in session or session['user_type'] != 'customer':
        return jsonify({'success': False, 'message': 'Please login'})
    
    product_id = request.form.get('product_id')
    quantity = int(request.form.get('quantity', 1))
    
    # Check stock availability
    product = query_db('SELECT stock FROM products WHERE id = ?', (product_id,), one=True)
    
    if not product or product['stock'] < quantity:
        return jsonify({'success': False, 'message': 'Insufficient stock'})
    
    # Check if item already in cart
    cart_item = query_db('SELECT id, quantity FROM cart WHERE user_id = ? AND product_id = ?',
                        (session['id'], product_id), one=True)
    
    conn = get_db()
    if cart_item:
        new_quantity = cart_item['quantity'] + quantity
        if new_quantity > product['stock']:
            conn.close()
            return jsonify({'success': False, 'message': 'Insufficient stock'})
        conn.execute('UPDATE cart SET quantity = ? WHERE id = ?', (new_quantity, cart_item['id']))
    else:
        conn.execute('INSERT INTO cart (user_id, product_id, quantity) VALUES (?, ?, ?)',
                    (session['id'], product_id, quantity))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Added to cart successfully'})

@app.route('/cart')
def cart():
    if 'loggedin' not in session or session['user_type'] != 'customer':
        return redirect(url_for('login'))
    
    cart_items = query_db('''
        SELECT c.id, c.quantity, p.id as product_id, p.category, p.size, p.color, p.stock
        FROM cart c
        JOIN products p ON c.product_id = p.id
        WHERE c.user_id = ?
    ''', (session['id'],))
    cart_items = [dict(row) for row in cart_items]
    
    return render_template('cart.html', cart_items=cart_items)

@app.route('/remove_from_cart/<int:cart_id>')
def remove_from_cart(cart_id):
    if 'loggedin' not in session or session['user_type'] != 'customer':
        return redirect(url_for('login'))
    
    query_db('DELETE FROM cart WHERE id = ? AND user_id = ?', (cart_id, session['id']))
    
    return redirect(url_for('cart'))

@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    if 'loggedin' not in session or session['user_type'] != 'customer':
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        # Get cart items
        cart_items = query_db('''
            SELECT c.product_id, c.quantity, p.stock
            FROM cart c
            JOIN products p ON c.product_id = p.id
            WHERE c.user_id = ?
        ''', (session['id'],))
        cart_items = [dict(row) for row in cart_items]
        
        # Validate stock and cart
        if not cart_items or len(cart_items) == 0:
            flash('Your cart is empty. Please add items to cart first.', 'error')
            return redirect(url_for('cart'))
        
        # Validate stock
        for item in cart_items:
            if item['quantity'] > item['stock']:
                flash(f'Insufficient stock. Available: {item["stock"]}, Requested: {item["quantity"]}', 'error')
                return redirect(url_for('cart'))
        
        # Create orders and generate QR codes
        conn = get_db()
        cursor = conn.cursor()
        
        print(f"DEBUG: Creating orders for {len(cart_items)} items")
        
        for item in cart_items:
            # Generate unique QR code - check both orders and products
            print(f"DEBUG: Generating unique QR code for order (product_id: {item['product_id']})...")
            qr_code = secrets.token_urlsafe(16)
            max_attempts = 50
            attempts = 0
            is_duplicate = True
            
            # Keep generating until we find a unique QR code
            while is_duplicate and attempts < max_attempts:
                # Check in orders table
                cursor.execute('SELECT id FROM orders WHERE qr_code = ?', (qr_code,))
                dup_in_orders = cursor.fetchone()
                
                # Check in products table (to ensure uniqueness across entire system)
                cursor.execute('SELECT id FROM products WHERE qr_code = ?', (qr_code,))
                dup_in_products = cursor.fetchone()
                
                if dup_in_orders or dup_in_products:
                    # Duplicate found, generate new one
                    if attempts < 3:  # Only log first few attempts to avoid spam
                        print(f"DEBUG: Duplicate QR code found (attempt {attempts + 1}), generating new one...")
                    qr_code = secrets.token_urlsafe(16)
                    attempts += 1
                else:
                    # Unique QR code found
                    is_duplicate = False
                    if attempts > 0:
                        print(f"DEBUG: Unique QR code generated after {attempts} attempts: {qr_code[:20]}...")
                    else:
                        print(f"DEBUG: Unique QR code generated on first try: {qr_code[:20]}...")
            
            if attempts >= max_attempts:
                flash('Error generating unique QR code. Please try again.', 'error')
                conn.rollback()
                cursor.close()
                conn.close()
                return redirect(url_for('cart'))
            
            # Insert order with unique QR code
            cursor.execute('''
                INSERT INTO orders (user_id, product_id, quantity, qr_code, status)
                VALUES (?, ?, ?, ?, 'pending')
            ''', (session['id'], item['product_id'], item['quantity'], qr_code))
            order_id = cursor.lastrowid
            print(f"DEBUG: Created order {order_id} with unique QR code {qr_code[:20]}... (status: pending)")
        
        # Clear cart
        cursor.execute('DELETE FROM cart WHERE user_id = ?', (session['id'],))
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"DEBUG: Order created successfully. Cart cleared.")
        flash('Order placed successfully! Waiting for approval.', 'success')
        return redirect(url_for('orders'))
    
    # GET request - show checkout page
    cart_items = query_db('''
        SELECT c.id, c.quantity, p.category, p.size, p.color, p.stock
        FROM cart c
        JOIN products p ON c.product_id = p.id
        WHERE c.user_id = ?
    ''', (session['id'],))
    cart_items = [dict(row) for row in cart_items]
    
    return render_template('checkout.html', cart_items=cart_items)

@app.route('/orders')
def orders():
    if 'loggedin' not in session or session['user_type'] != 'customer':
        return redirect(url_for('login'))
    
    orders_list = query_db('''
        SELECT o.id, o.quantity, o.qr_code, o.status, 
               datetime(o.created_at) as created_at,
               p.category, p.size, p.color
        FROM orders o
        JOIN products p ON o.product_id = p.id
        WHERE o.user_id = ?
        ORDER BY o.created_at DESC
    ''', (session['id'],))
    orders_list = [dict(row) for row in orders_list]
    
    return render_template('orders.html', orders=orders_list)

@app.route('/notify_me', methods=['POST'])
def notify_me():
    if 'loggedin' not in session or session['user_type'] != 'customer':
        return jsonify({'success': False})
    
    product_id = request.form.get('product_id')
    # In a real app, you would store notification preferences
    flash('You will be notified when this product is back in stock!', 'info')
    return jsonify({'success': True})

# Admin Routes

@app.route('/admin/dashboard')
def admin_dashboard():
    if 'loggedin' not in session or session['user_type'] != 'admin':
        return redirect(url_for('login'))
    
    total_products = query_db('SELECT COUNT(*) as total FROM products', one=True)['total']
    total_orders = query_db('SELECT COUNT(*) as total FROM orders', one=True)['total']
    
    return render_template('admin/dashboard.html', 
                         total_products=total_products, 
                         total_orders=total_orders,
                         username=session['username'])

@app.route('/admin/products', methods=['GET', 'POST'])
def admin_products():
    if 'loggedin' not in session or session['user_type'] != 'admin':
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        category = request.form['category']
        size = request.form['size']
        color = request.form['color']
        stock = int(request.form['stock'])
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Check if product exists
        cursor.execute('SELECT id, stock, qr_code FROM products WHERE category = ? AND size = ? AND color = ?',
                      (category, size, color))
        existing = cursor.fetchone()
        
        if existing:
            # Update stock (keep existing QR code)
            new_stock = existing['stock'] + stock
            cursor.execute('UPDATE products SET stock = ? WHERE id = ?', (new_stock, existing['id']))
        else:
            # Generate unique QR code for new product - check BOTH products and orders tables
            print(f"DEBUG: Generating unique QR code for new product: {category} {size} {color}")
            qr_code = secrets.token_urlsafe(16)
            max_attempts = 50
            attempts = 0
            is_duplicate = True
            
            # Keep generating until we find a unique QR code
            while is_duplicate and attempts < max_attempts:
                # Check in products table
                cursor.execute('SELECT id FROM products WHERE qr_code = ?', (qr_code,))
                dup_in_products = cursor.fetchone()
                
                # Check in orders table (to ensure uniqueness across entire system)
                cursor.execute('SELECT id FROM orders WHERE qr_code = ?', (qr_code,))
                dup_in_orders = cursor.fetchone()
                
                if dup_in_products or dup_in_orders:
                    # Duplicate found, generate new one
                    print(f"DEBUG: Duplicate QR code found (attempt {attempts + 1}), generating new one...")
                    qr_code = secrets.token_urlsafe(16)
                    attempts += 1
                else:
                    # Unique QR code found
                    is_duplicate = False
                    print(f"DEBUG: Unique QR code generated: {qr_code[:20]}... (after {attempts} attempts)")
            
            if attempts >= max_attempts:
                flash('Error generating unique QR code. Please try again.', 'error')
                conn.rollback()
                cursor.close()
                conn.close()
                return redirect(url_for('admin_products'))
            
            # Generate image URL based on category and color
            image_url = get_product_image_url(category, color)
            
            # Insert new product with unique QR code and image
            cursor.execute('INSERT INTO products (category, size, color, stock, qr_code, image_url) VALUES (?, ?, ?, ?, ?, ?)',
                          (category, size, color, stock, qr_code, image_url))
            product_id = cursor.lastrowid
            print(f"DEBUG: Product {product_id} created with unique QR code: {qr_code}")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        flash('Product added/updated successfully!', 'success')
        return redirect(url_for('admin_products'))
    
    products = query_db('SELECT * FROM products ORDER BY category, color, size')
    products = [dict(row) for row in products]
    
    # Ensure all products have image URLs based on category
    for product in products:
        if not product.get('image_url') or product.get('image_url') == '' or product.get('image_url') is None:
            product['image_url'] = get_product_image_url(product['category'], product['color'])
    
    return render_template('admin/products.html', products=products)

@app.route('/admin/products/edit/<int:product_id>', methods=['GET', 'POST'])
def edit_product(product_id):
    if 'loggedin' not in session or session['user_type'] != 'admin':
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        category = request.form['category']
        size = request.form['size']
        color = request.form['color']
        stock = int(request.form['stock'])
        
        query_db('''
            UPDATE products 
            SET category = ?, size = ?, color = ?, stock = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (category, size, color, stock, product_id))
        
        flash('Product updated successfully!', 'success')
        return redirect(url_for('admin_products'))
    
    product = query_db('SELECT * FROM products WHERE id = ?', (product_id,), one=True)
    product = dict(product) if product else None
    
    if not product:
        flash('Product not found', 'error')
        return redirect(url_for('admin_products'))
    
    return render_template('admin/edit_product.html', product=product)

@app.route('/admin/products/delete/<int:product_id>')
def delete_product(product_id):
    if 'loggedin' not in session or session['user_type'] != 'admin':
        return redirect(url_for('login'))
    
    try:
        # Get product info before deletion
        product = query_db('SELECT category, size, color FROM products WHERE id = ?', (product_id,), one=True)
        
        if not product:
            flash('Product not found', 'error')
            return redirect(url_for('admin_products'))
        
        # Find all orders for this product (pending and confirmed)
        orders = query_db('''
            SELECT id, user_id, status 
            FROM orders 
            WHERE product_id = ? AND status IN ('pending', 'confirmed')
        ''', (product_id,))
        orders = [dict(row) for row in orders]
        
        # Cancel all pending and confirmed orders for this product
        conn = get_db()
        cursor = conn.cursor()
        
        cancelled_count = 0
        for order in orders:
            # Update order status to cancelled
            cursor.execute('UPDATE orders SET status = ? WHERE id = ?', ('cancelled', order['id']))
            cancelled_count += 1
            print(f"DEBUG: Cancelled order {order['id']} due to product {product_id} deletion")
        
        # Delete the product
        cursor.execute('DELETE FROM products WHERE id = ?', (product_id,))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        if cancelled_count > 0:
            flash(f'Product deleted successfully! {cancelled_count} order(s) have been cancelled. Customers will see a message to contact support: 1234567890', 'success')
        else:
            flash('Product deleted successfully!', 'success')
        
        return redirect(url_for('admin_products'))
    except Exception as e:
        print(f"ERROR in delete_product: {e}")
        flash(f'Error deleting product: {str(e)}', 'error')
        return redirect(url_for('admin_products'))

@app.route('/admin/generate_qr_product/<int:product_id>')
def generate_qr_product(product_id):
    if 'loggedin' not in session or session['user_type'] != 'admin':
        return redirect(url_for('login'))
    
    product = query_db('SELECT qr_code, category, size, color FROM products WHERE id = ?', (product_id,), one=True)
    
    if not product:
        flash('Product not found', 'error')
        return redirect(url_for('admin_products'))
    
    # If product doesn't have QR code, generate one
    if not product['qr_code']:
        print(f"DEBUG: Product {product_id} doesn't have QR code, generating unique one...")
        conn = get_db()
        cursor = conn.cursor()
        qr_code = secrets.token_urlsafe(16)
        max_attempts = 50
        attempts = 0
        is_duplicate = True
        
        # Keep generating until we find a unique QR code
        while is_duplicate and attempts < max_attempts:
            # Check in products table
            cursor.execute('SELECT id FROM products WHERE qr_code = ?', (qr_code,))
            dup_in_products = cursor.fetchone()
            
            # Check in orders table (to ensure uniqueness across entire system)
            cursor.execute('SELECT id FROM orders WHERE qr_code = ?', (qr_code,))
            dup_in_orders = cursor.fetchone()
            
            if dup_in_products or dup_in_orders:
                # Duplicate found, generate new one
                print(f"DEBUG: Duplicate QR code found (attempt {attempts + 1}), generating new one...")
                qr_code = secrets.token_urlsafe(16)
                attempts += 1
            else:
                # Unique QR code found
                is_duplicate = False
                print(f"DEBUG: Unique QR code generated: {qr_code[:20]}... (after {attempts} attempts)")
        
        if attempts >= max_attempts:
            flash('Error generating unique QR code. Please try again.', 'error')
            conn.rollback()
            cursor.close()
            conn.close()
            return redirect(url_for('admin_products'))
        
        cursor.execute('UPDATE products SET qr_code = ? WHERE id = ?', (qr_code, product_id))
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"DEBUG: Product {product_id} updated with unique QR code: {qr_code}")
        
        # Reload product with new QR code
        product = query_db('SELECT qr_code, category, size, color FROM products WHERE id = ?', (product_id,), one=True)
    
    # Generate QR code image
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(product['qr_code'])
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    img_buffer = BytesIO()
    img.save(img_buffer, format='PNG')
    img_str = base64.b64encode(img_buffer.getvalue()).decode()
    
    product_info = f"{product['category']} - Size: {product['size']}, Color: {product['color']}"
    
    return render_template('admin/qr_code.html', 
                         qr_code=product['qr_code'], 
                         qr_image=img_str,
                         product_info=product_info,
                         is_product=True)

@app.route('/admin/generate_qr/<int:order_id>')
def generate_qr(order_id):
    if 'loggedin' not in session or session['user_type'] != 'admin':
        return redirect(url_for('login'))
    
    order = query_db('SELECT qr_code FROM orders WHERE id = ?', (order_id,), one=True)
    
    if not order:
        flash('Order not found', 'error')
        return redirect(url_for('admin_orders'))
    
    # Generate QR code image
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(order['qr_code'])
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    img_buffer = BytesIO()
    img.save(img_buffer, format='PNG')
    img_str = base64.b64encode(img_buffer.getvalue()).decode()
    
    return render_template('admin/qr_code.html', qr_code=order['qr_code'], qr_image=img_str, is_product=False)

@app.route('/admin/orders')
def admin_orders():
    if 'loggedin' not in session or session['user_type'] != 'admin':
        return redirect(url_for('login'))
    
    orders_list = query_db('''
        SELECT o.id, o.quantity, o.qr_code, o.status, 
               datetime(o.created_at) as created_at,
               p.category, p.size, p.color, u.username
        FROM orders o
        JOIN products p ON o.product_id = p.id
        JOIN users u ON o.user_id = u.id
        ORDER BY o.created_at DESC
    ''')
    orders_list = [dict(row) for row in orders_list]
    
    return render_template('admin/orders.html', orders=orders_list)

# Approval Admin Routes

@app.route('/approval/dashboard')
def approval_dashboard():
    if 'loggedin' not in session or session['user_type'] != 'approval_admin':
        return redirect(url_for('login'))
    
    pending_orders = query_db('SELECT COUNT(*) as total FROM orders WHERE status = ?', ('pending',), one=True)['total']
    
    return render_template('approval/dashboard.html', 
                         pending_orders=pending_orders,
                         username=session['username'])

@app.route('/approval/orders')
def approval_orders():
    if 'loggedin' not in session or session['user_type'] != 'approval_admin':
        return redirect(url_for('login'))
    
    orders_list = query_db('''
        SELECT o.id, o.quantity, o.qr_code, o.status, 
               datetime(o.created_at) as created_at,
               p.category, p.size, p.color, u.username
        FROM orders o
        JOIN products p ON o.product_id = p.id
        JOIN users u ON o.user_id = u.id
        WHERE o.status = ?
        ORDER BY o.created_at ASC
    ''', ('pending',))
    orders_list = [dict(row) for row in orders_list]
    
    print(f"DEBUG: Approval orders page - Found {len(orders_list)} pending orders")
    for order in orders_list:
        print(f"  Order {order['id']}: {order['username']} - {order['category']} {order['size']} {order['color']}")
    
    return render_template('approval/orders.html', orders=orders_list)

@app.route('/approval/validate_qr', methods=['POST'])
def validate_qr():
    if 'loggedin' not in session or session['user_type'] != 'approval_admin':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    qr_code = request.form.get('qr_code')
    order_id = request.form.get('order_id')
    
    # Check for duplicate QR code across ALL stocks (products and orders)
    # Check in products table
    duplicate_product = query_db('SELECT id FROM products WHERE qr_code = ?', (qr_code,), one=True)
    
    # Check in orders table (excluding current order)
    duplicate_order = query_db('SELECT id FROM orders WHERE qr_code = ? AND id != ?', (qr_code, order_id), one=True)
    
    if duplicate_product or duplicate_order:
        return jsonify({
            'success': False, 
            'message': 'Duplicate QR code detected! Please contact customer support team: 1234567890'
        })
    
    # QR code is unique - can proceed with approval
    return jsonify({'success': True, 'message': 'QR code is unique. You can approve the order.'})

@app.route('/approval/approve_order/<int:order_id>', methods=['POST'])
def approve_order(order_id):
    print(f"=== APPROVE ORDER ROUTE CALLED ===")
    print(f"Order ID: {order_id}")
    print(f"Session: loggedin={session.get('loggedin')}, user_type={session.get('user_type')}")
    
    if 'loggedin' not in session or session['user_type'] != 'approval_admin':
        print("ERROR: Not logged in as approval admin")
        return redirect(url_for('login'))
    
    try:
        # Get order with QR code
        order = query_db('SELECT qr_code, user_id FROM orders WHERE id = ?', (order_id,), one=True)
        
        if not order:
            flash('Order not found', 'error')
            return redirect(url_for('approval_orders'))
        
        qr_code = order['qr_code']
        print(f"DEBUG: Approving order {order_id} with QR code: {qr_code}")
        
        # Step 1: Confirm the order first (as per flowchart: QR Code Validation → Confirm order)
        print(f"DEBUG: Step 1 - Confirming order {order_id}")
        order_details = query_db('SELECT product_id, quantity FROM orders WHERE id = ?', (order_id,), one=True)
        
        conn = get_db()
        cursor = conn.cursor()
        # Update order status to confirmed
        cursor.execute('UPDATE orders SET status = ? WHERE id = ?', ('confirmed', order_id))
        # Reduce stock
        cursor.execute('UPDATE products SET stock = stock - ? WHERE id = ?',
                      (order_details['quantity'], order_details['product_id']))
        conn.commit()
        cursor.close()
        conn.close()
        
        # Step 2: After confirming order, check for duplicate QR code (as per flowchart)
        print(f"DEBUG: Step 2 - Checking for duplicate QR code after confirmation...")
        print(f"DEBUG: Validating QR code: {qr_code}")
        
        # Check in products table
        duplicate_in_products = query_db('SELECT id FROM products WHERE qr_code = ?', (qr_code,), one=True)
        print(f"DEBUG: Duplicate in products: {duplicate_in_products is not None}")
        if duplicate_in_products:
            print(f"DEBUG: Found duplicate in products table - Product ID: {duplicate_in_products['id']}")
        
        # Check in other confirmed/pending orders (excluding current order)
        duplicate_in_other_orders = query_db('''
            SELECT id FROM orders 
            WHERE qr_code = ? AND id != ? AND status IN ('confirmed', 'pending')
        ''', (qr_code, order_id), one=True)
        print(f"DEBUG: Duplicate in other orders: {duplicate_in_other_orders is not None}")
        if duplicate_in_other_orders:
            print(f"DEBUG: Found duplicate in orders table - Order ID: {duplicate_in_other_orders['id']}")
        
        if duplicate_in_products or duplicate_in_other_orders:
            # Duplicate QR code found after confirmation - update status and notify
            print(f"DEBUG: ❌ DUPLICATE QR CODE DETECTED AFTER CONFIRMATION")
            print(f"DEBUG: Order {order_id} status changed to 'cancelled'")
            query_db('UPDATE orders SET status = ? WHERE id = ?', ('cancelled', order_id))
            flash('❌ Validation Failed: Duplicate QR code detected! The customer should contact support team: 1234567890', 'error')
        else:
            # QR code is unique - order confirmed successfully
            print(f"DEBUG: ✅ Order {order_id} confirmed successfully - QR code is unique")
            flash('✅ Validation Successful: Customer confirmed your order! QR code is unique and order is confirmed.', 'success')
        
        return redirect(url_for('approval_orders'))
    except Exception as e:
        print(f"ERROR in approve_order: {e}")
        flash(f'Error processing order: {str(e)}', 'error')
        return redirect(url_for('approval_orders'))

@app.route('/approval/cancel_order/<int:order_id>', methods=['POST'])
def cancel_order(order_id):
    print(f"=== CANCEL ORDER ROUTE CALLED ===")
    print(f"Order ID: {order_id}")
    print(f"Session: loggedin={session.get('loggedin')}, user_type={session.get('user_type')}")
    
    if 'loggedin' not in session or session['user_type'] != 'approval_admin':
        print("ERROR: Not logged in as approval admin")
        return redirect(url_for('login'))
    
    try:
        # Get order details
        order = query_db('SELECT id, user_id, product_id, quantity FROM orders WHERE id = ?', (order_id,), one=True)
        
        if not order:
            flash('Order not found', 'error')
            return redirect(url_for('approval_orders'))
        
        # Update order status to cancelled
        print(f"DEBUG: Cancelling order {order_id}")
        query_db('UPDATE orders SET status = ? WHERE id = ?', ('cancelled', order_id))
        
        print(f"DEBUG: Order {order_id} cancelled successfully")
        flash(f'Order #{order_id} has been cancelled. Customer will see a message to contact support: 1234567890', 'success')
        return redirect(url_for('approval_orders'))
    except Exception as e:
        print(f"ERROR in cancel_order: {e}")
        flash(f'Error cancelling order: {str(e)}', 'error')
        return redirect(url_for('approval_orders'))

@app.route('/approval/confirm_order/<int:order_id>')
def confirm_order(order_id):
    if 'loggedin' not in session or session['user_type'] != 'approval_admin':
        return redirect(url_for('login'))
    
    query_db('UPDATE orders SET status = ? WHERE id = ?', ('confirmed', order_id))
    
    flash('Order confirmed!', 'success')
    return redirect(url_for('approval_orders'))

def get_product_image_url(category, color):
    """Generate product image URL - using one sample T-shirt picture for all products"""
    # Single sample T-shirt image URL for all products
    # Using local image from static folder
    # Return relative path that works both in Flask context and outside
    try:
        # Try to use url_for if in Flask context
        return url_for('static', filename='images/tshirt.png')
    except RuntimeError:
        # If outside Flask context, return relative path
        return '/static/images/tshirt.png'

# Database will be initialized on first request or when running locally
# This prevents import-time errors in serverless environments
_db_init_attempted = False
_db_init_success = False

def ensure_db_initialized():
    """Ensure database is initialized (lazy initialization)"""
    global _db_init_attempted, _db_init_success
    
    # If already successfully initialized, skip
    if _db_init_success:
        return
    
    if not _db_init_attempted:
        _db_init_attempted = True
        try:
            print("Initializing database...")
            print(f"Database path: {DATABASE}")
            init_db()
            _db_init_success = True
            print("✓ Database initialized successfully")
        except Exception as e:
            print(f"⚠ Warning: Database initialization failed: {e}")
            import traceback
            traceback.print_exc()
            # Don't mark as success, but don't retry immediately to avoid loops
            # Will retry on next request if needed

# Initialize database on startup for Railway/Render (not serverless)
# This ensures database is ready before first request
if not (os.environ.get('VERCEL_ENV') or os.environ.get('VERCEL')):
    try:
        print("=== Initializing database on startup ===")
        ensure_db_initialized()
        print("=== Database ready ===")
    except Exception as e:
        print(f"⚠ Database init on startup failed, will retry on first request: {e}")

# Initialize database when running locally
if __name__ == '__main__':
    print("Starting QR App (SQLite Version)...")
    print("=" * 50)
    try:
        init_db()
    except Exception as e:
        print(f"Warning: Database initialization failed: {e}")
    print("\nServer starting on http://127.0.0.1:5000")
    print("Press CTRL+C to stop the server")
    print("=" * 50)
    app.run(debug=True, host='127.0.0.1', port=5000)
