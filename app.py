# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import sqlite3
import secrets
import qrcode
from io import BytesIO
import base64
from datetime import datetime
import os
import sys

# Fix Windows encoding issues
if sys.platform == 'win32':
    import codecs
    # Set UTF-8 encoding for stdout/stderr on Windows
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8')
    # Also set environment variable
    os.environ['PYTHONIOENCODING'] = 'utf-8'

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
        # Ensure database directory exists
        db_dir = os.path.dirname(os.path.abspath(DATABASE))
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
        
        # Add timeout to prevent hanging on locked database
        conn = sqlite3.connect(DATABASE, timeout=10.0)
        conn.row_factory = sqlite3.Row  # This makes rows behave like dicts
        return conn
    except sqlite3.Error as e:
        print(f"[ERROR] Database connection error: {e}")
        print(f"Database path: {DATABASE}")
        # Re-raise to be caught by route handlers
        raise
    except Exception as e:
        print(f"[ERROR] Unexpected error connecting to database: {e}")
        print(f"Database path: {DATABASE}")
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
        print(f"[ERROR] Database query error: {e}")
        print(f"Query: {query[:100]}...")  # Log first 100 chars of query
        if conn:
            conn.rollback()
        raise  # Re-raise to be caught by route handlers
    except Exception as e:
        print(f"[ERROR] Unexpected error in query_db: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()

def generate_unique_item_qr_code(cursor):
    """Generate unique QR code for individual item"""
    qr_code = secrets.token_urlsafe(16)
    max_attempts = 50
    attempts = 0
    is_duplicate = True
    
    while is_duplicate and attempts < max_attempts:
        # Check in items table
        cursor.execute('SELECT id FROM items WHERE qr_code = ?', (qr_code,))
        dup_in_items = cursor.fetchone()
        
        # Check in products table
        cursor.execute('SELECT id FROM products WHERE qr_code = ?', (qr_code,))
        dup_in_products = cursor.fetchone()
        
        # Note: Orders no longer have QR codes, only items have QR codes
        if dup_in_items or dup_in_products:
            qr_code = secrets.token_urlsafe(16)
            attempts += 1
        else:
            is_duplicate = False
    
    if attempts >= max_attempts:
        raise Exception("Failed to generate unique QR code after 50 attempts")
    
    return qr_code

def get_product_stock(product_id):
    """Get available stock count from items table (only validated items)"""
    count = query_db(
        'SELECT COUNT(*) as count FROM items WHERE product_id = ? AND status = ? AND validated = 1',
        (product_id, 'available'),
        one=True
    )
    return dict(count)['count'] if count else 0

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
        
        # Items table - Individual stock items with unique QR codes
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                qr_code TEXT UNIQUE NOT NULL,
                status TEXT DEFAULT 'available' CHECK(status IN ('available', 'reserved', 'sold', 'damaged')),
                validated BOOLEAN DEFAULT 0,
                validated_at DATETIME NULL,
                validated_by INTEGER NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                order_id INTEGER NULL,
                FOREIGN KEY (product_id) REFERENCES products(id),
                FOREIGN KEY (order_id) REFERENCES orders(id),
                FOREIGN KEY (validated_by) REFERENCES users(id)
            )
        ''')
        
        # Add validation columns if they don't exist (for existing databases)
        try:
            cursor.execute('ALTER TABLE items ADD COLUMN validated BOOLEAN DEFAULT 0')
        except:
            pass  # Column already exists
        try:
            cursor.execute('ALTER TABLE items ADD COLUMN validated_at DATETIME NULL')
        except:
            pass
        try:
            cursor.execute('ALTER TABLE items ADD COLUMN validated_by INTEGER NULL')
        except:
            pass
        
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
    
    # Get categories that have products with items (validated or not)
    # This shows all categories, and products page will filter by validated items
    categories_result = query_db('''
        SELECT DISTINCT p.category
        FROM products p
        INNER JOIN items i ON p.id = i.product_id
        WHERE i.status = 'available'
        ORDER BY p.category
    ''')
    categories = [dict(row) for row in categories_result] if categories_result else []
    
    # If no categories with items, show categories that have products (in case items haven't been created yet)
    if not categories:
        categories_result = query_db('''
            SELECT DISTINCT category
            FROM products
            ORDER BY category
        ''')
        categories = [dict(row) for row in categories_result] if categories_result else []
    
    return render_template('homepage.html', categories=categories, username=session['username'])

@app.route('/products')
def products():
    if 'loggedin' not in session or session['user_type'] != 'customer':
        return redirect(url_for('login'))
    
    category = request.args.get('category', 'T-Shirt')
    products_list = query_db('''
        SELECT * FROM products 
        WHERE category = ?
        ORDER BY color, size
    ''', (category,))
    products_list = [dict(row) for row in products_list]
    
    # Calculate available stock from items table (validated items only for purchasing)
    # But show products even if they have unvalidated items
    filtered_products = []
    for product in products_list:
        # Get validated available stock (for purchasing)
        available_stock = get_product_stock(product['id'])
        
        # Get total available items (validated or not) - for display
        total_available = query_db(
            'SELECT COUNT(*) as count FROM items WHERE product_id = ? AND status = ?',
            (product['id'], 'available'),
            one=True
        )
        total_available_count = dict(total_available)['count'] if total_available else 0
        
        # Show product if it has any available items (validated or not)
        if total_available_count > 0:
            product['stock'] = available_stock  # Validated stock for purchasing
            product['total_available'] = total_available_count  # Total items for display
            # Items are validated when created by admin, so no validation needed
            product['needs_validation'] = False
            filtered_products.append(product)
    
    # Ensure all products have image URLs based on category
    for product in filtered_products:
        if not product.get('image_url') or product.get('image_url') == '' or product.get('image_url') is None:
            product['image_url'] = get_product_image_url(product['category'], product['color'])
    
    return render_template('products.html', products=filtered_products, category=category)

@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    if 'loggedin' not in session or session['user_type'] != 'customer':
        return jsonify({'success': False, 'message': 'Please login'})
    
    product_id = request.form.get('product_id')
    quantity = int(request.form.get('quantity', 1))
    
    # Check stock availability from items table
    available_stock = get_product_stock(product_id)
    
    if available_stock < quantity:
        return jsonify({'success': False, 'message': f'Insufficient stock. Available: {available_stock}'})
    
    # Check if item already in cart
    cart_item = query_db('SELECT id, quantity FROM cart WHERE user_id = ? AND product_id = ?',
                        (session['id'], product_id), one=True)
    
    conn = get_db()
    if cart_item:
        new_quantity = cart_item['quantity'] + quantity
        # Check available stock again
        current_available = get_product_stock(product_id)
        if new_quantity > current_available:
            conn.close()
            return jsonify({'success': False, 'message': f'Insufficient stock. Available: {current_available}'})
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
        SELECT c.id, c.quantity, p.id as product_id, p.category, p.size, p.color
        FROM cart c
        JOIN products p ON c.product_id = p.id
        WHERE c.user_id = ?
    ''', (session['id'],))
    cart_items = [dict(row) for row in cart_items]
    
    # Add available stock from items table
    for item in cart_items:
        item['stock'] = get_product_stock(item['product_id'])
    
    return render_template('cart.html', cart_items=cart_items)

@app.route('/remove_from_cart/<int:cart_id>')
def remove_from_cart(cart_id):
    if 'loggedin' not in session or session['user_type'] != 'customer':
        return redirect(url_for('login'))
    
    query_db('DELETE FROM cart WHERE id = ? AND user_id = ?', (cart_id, session['id']))
    
    return redirect(url_for('cart'))

@app.route('/update_cart_quantity', methods=['POST'])
def update_cart_quantity():
    """Update quantity of an item in the cart"""
    if 'loggedin' not in session or session['user_type'] != 'customer':
        return jsonify({'success': False, 'message': 'Please login'})
    
    cart_id = request.form.get('cart_id')
    new_quantity = int(request.form.get('quantity', 1))
    
    if new_quantity < 1:
        return jsonify({'success': False, 'message': 'Quantity must be at least 1'})
    
    # Get cart item details
    cart_item = query_db('''
        SELECT c.product_id, c.quantity
        FROM cart c
        WHERE c.id = ? AND c.user_id = ?
    ''', (cart_id, session['id']), one=True)
    
    if not cart_item:
        return jsonify({'success': False, 'message': 'Cart item not found'})
    
    # Check available stock
    available_stock = get_product_stock(cart_item['product_id'])
    
    if new_quantity > available_stock:
        return jsonify({'success': False, 'message': f'Insufficient stock. Available: {available_stock}'})
    
    # Update quantity
    conn = get_db()
    conn.execute('UPDATE cart SET quantity = ? WHERE id = ? AND user_id = ?', 
                 (new_quantity, cart_id, session['id']))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Quantity updated successfully'})

@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    if 'loggedin' not in session or session['user_type'] != 'customer':
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        # Get cart items
        cart_items = query_db('''
            SELECT c.product_id, c.quantity
            FROM cart c
            WHERE c.user_id = ?
        ''', (session['id'],))
        cart_items = [dict(row) for row in cart_items]
        
        # Validate stock and cart
        if not cart_items or len(cart_items) == 0:
            flash('Your cart is empty. Please add items to cart first.', 'error')
            return redirect(url_for('cart'))
        
        # Validate stock from items table
        for item in cart_items:
            available_stock = get_product_stock(item['product_id'])
            if item['quantity'] > available_stock:
                flash(f'Insufficient stock. Available: {available_stock}, Requested: {item["quantity"]}', 'error')
                return redirect(url_for('cart'))
        
        # Create orders, reserve items, and generate QR codes
        conn = get_db()
        cursor = conn.cursor()
        
        print(f"DEBUG: Creating orders for {len(cart_items)} items")
        
        for item in cart_items:
            # Insert order without QR code (only items have QR codes)
            cursor.execute('''
                INSERT INTO orders (user_id, product_id, quantity, status)
                VALUES (?, ?, ?, 'pending')
            ''', (session['id'], item['product_id'], item['quantity']))
            order_id = cursor.lastrowid
            print(f"DEBUG: Created order {order_id} (status: pending)")
            
            # Reserve items for this order - only validated items (change status from 'available' to 'reserved')
            cursor.execute('''
                SELECT id FROM items 
                WHERE product_id = ? AND status = 'available' AND validated = 1
                LIMIT ?
            ''', (item['product_id'], item['quantity']))
            available_items = cursor.fetchall()
            
            if len(available_items) < item['quantity']:
                # Check if there are unvalidated items
                cursor.execute('''
                    SELECT COUNT(*) as count FROM items 
                    WHERE product_id = ? AND status = 'available' AND validated = 0
                ''', (item['product_id'],))
                unvalidated_count = cursor.fetchone()
                unvalidated = unvalidated_count[0] if unvalidated_count else 0
                
                # Rollback
                conn.rollback()
                cursor.close()
                conn.close()
                
                flash(f'Insufficient stock for product. Available items: {len(available_items)}, Requested: {item["quantity"]}', 'error')
                return redirect(url_for('cart'))
            
            # Reserve validated items and reset validated status (will be set when scanned via mobile for this order)
            for item_row in available_items:
                item_id = item_row['id'] if isinstance(item_row, dict) else item_row[0]
                cursor.execute('''
                    UPDATE items 
                    SET status = ?, order_id = ?, validated = 0, validated_at = NULL
                    WHERE id = ?
                ''', ('reserved', order_id, item_id))
                print(f"DEBUG: Reserved item {item_id} for order {order_id} - validated status reset to 0")
            
            # Update product stock count from available items
            cursor.execute('''
                UPDATE products 
                SET stock = (SELECT COUNT(*) FROM items WHERE product_id = ? AND status = 'available')
                WHERE id = ?
            ''', (item['product_id'], item['product_id']))
        
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
        SELECT c.id, c.quantity, p.category, p.size, p.color, p.id as product_id
        FROM cart c
        JOIN products p ON c.product_id = p.id
        WHERE c.user_id = ?
    ''', (session['id'],))
    cart_items = [dict(row) for row in cart_items]
    
    # Add available stock from items table
    for item in cart_items:
        item['stock'] = get_product_stock(item['product_id'])
    
    return render_template('checkout.html', cart_items=cart_items)

@app.route('/orders')
def orders():
    if 'loggedin' not in session or session['user_type'] != 'customer':
        return redirect(url_for('login'))
    
    orders_result = query_db('''
        SELECT o.id, o.quantity, o.status, 
               datetime(o.created_at) as created_at,
               p.category, p.size, p.color
        FROM orders o
        JOIN products p ON o.product_id = p.id
        WHERE o.user_id = ?
        ORDER BY o.created_at DESC
    ''', (session['id'],))
    orders_list = []
    
    # Check for newly confirmed orders and show notification
    has_confirmed_orders = False
    confirmed_count = 0
    
    # Convert to dicts and get item QR codes for each order
    for row in orders_result:
        order = dict(row)  # Convert sqlite3.Row to dict to avoid .items() method conflict
        items = query_db('''
            SELECT i.qr_code, i.id as item_id
            FROM items i
            WHERE i.order_id = ?
        ''', (order['id'],))
        order['items'] = [dict(item) for item in items] if items else []
        
        # Check if order is confirmed
        if order['status'] == 'confirmed':
            has_confirmed_orders = True
            confirmed_count += 1
        
        orders_list.append(order)
    
    # Show flash message if there are confirmed orders
    if has_confirmed_orders:
        if confirmed_count == 1:
            flash('🎉 Great news! One of your orders has been confirmed! All items have been scanned and validated.', 'success')
        else:
            flash(f'🎉 Great news! {confirmed_count} of your orders have been confirmed! All items have been scanned and validated.', 'success')
    
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
            # Product exists - create new items with unique QR codes
            product_id = existing['id']
            items_created = 0
            
            for i in range(stock):
                try:
                    item_qr_code = generate_unique_item_qr_code(cursor)
                    # Items are validated when created by admin - ready for customer orders
                    cursor.execute(
                        'INSERT INTO items (product_id, qr_code, status, validated, validated_at) VALUES (?, ?, ?, 1, CURRENT_TIMESTAMP)',
                        (product_id, item_qr_code, 'available')
                    )
                    items_created += 1
                except Exception as e:
                    print(f"Error creating item {i+1}: {e}")
            
            # Update product stock count from items
            cursor.execute('''
                UPDATE products 
                SET stock = (SELECT COUNT(*) FROM items WHERE product_id = ? AND status = 'available')
                WHERE id = ?
            ''', (product_id, product_id))
            
            if items_created > 0:
                print(f"DEBUG: Created {items_created} items with unique QR codes for existing product {product_id}")
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
                
                # Check in items table
                cursor.execute('SELECT id FROM items WHERE qr_code = ?', (qr_code,))
                dup_in_items = cursor.fetchone()
                
                if dup_in_products or dup_in_items:
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
            
            # Insert new product (without QR code - items have QR codes now)
            cursor.execute('INSERT INTO products (category, size, color, stock, image_url) VALUES (?, ?, ?, 0, ?)',
                          (category, size, color, image_url))
            product_id = cursor.lastrowid
            
            # Create individual items with unique QR codes
            # Items start as unvalidated - only validated when scanned via mobile
            items_created = 0
            for i in range(stock):
                try:
                    item_qr_code = generate_unique_item_qr_code(cursor)
                    # Items are validated when created by admin - ready for customer orders
                    cursor.execute(
                        'INSERT INTO items (product_id, qr_code, status, validated, validated_at) VALUES (?, ?, ?, 1, CURRENT_TIMESTAMP)',
                        (product_id, item_qr_code, 'available')
                    )
                    items_created += 1
                except Exception as e:
                    print(f"Error creating item {i+1}: {e}")
            
            # Update product stock count from items
            cursor.execute('''
                UPDATE products 
                SET stock = (SELECT COUNT(*) FROM items WHERE product_id = ? AND status = 'available')
                WHERE id = ?
            ''', (product_id, product_id))
            
            print(f"DEBUG: Product {product_id} created with {items_created} items, each with unique QR code")
        
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
            
            # Note: Orders no longer have QR codes, only products and items have QR codes
            if dup_in_products:
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
    
    # Generate QR code image with error correction for better scanning
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=5
    )
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
    items_result = query_db('''
        SELECT i.*, o.status as order_status
        FROM items i
        LEFT JOIN orders o ON i.order_id = o.id
        WHERE i.product_id = ?
        ORDER BY i.status, i.created_at
    ''', (product_id,))
    items = [dict(row) for row in items_result] if items_result else []
    
    # Count items by status
    status_counts = {
        'available': sum(1 for item in items if item['status'] == 'available'),
        'reserved': sum(1 for item in items if item['status'] == 'reserved'),
        'sold': sum(1 for item in items if item['status'] == 'sold'),
        'damaged': sum(1 for item in items if item['status'] == 'damaged')
    }
    
    return render_template('admin/items.html', product=product, items=items, status_counts=status_counts)

@app.route('/admin/validate_items/<int:product_id>', methods=['POST'])
def validate_items_bulk(product_id):
    """Bulk validate all unvalidated items for a product"""
    if 'loggedin' not in session or session['user_type'] != 'admin':
        return redirect(url_for('login'))
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Validate all unvalidated available items for this product
    cursor.execute('''
        UPDATE items 
        SET validated = 1, validated_at = CURRENT_TIMESTAMP, validated_by = ?
        WHERE product_id = ? AND validated = 0 AND status = 'available'
    ''', (session['id'], product_id))
    
    updated_count = cursor.rowcount
    
    # Update product stock count
    cursor.execute('''
        UPDATE products 
        SET stock = (SELECT COUNT(*) FROM items WHERE product_id = ? AND status = 'available' AND validated = 1)
        WHERE id = ?
    ''', (product_id, product_id))
    
    conn.commit()
    cursor.close()
    conn.close()
    
    flash(f'Successfully validated {updated_count} items!', 'success')
    return redirect(url_for('admin_items', product_id=product_id))

@app.route('/admin/product_items_qr/<int:product_id>')
def product_items_qr(product_id):
    """View all item QR codes for a product in a grid layout"""
    if 'loggedin' not in session or session['user_type'] != 'admin':
        return redirect(url_for('login'))
    
    product_result = query_db('SELECT * FROM products WHERE id = ?', (product_id,), one=True)
    if not product_result:
        flash('Product not found', 'error')
        return redirect(url_for('admin_products'))
    
    product = dict(product_result) if product_result else None
    
    # Get all items for this product
    items_result = query_db('''
        SELECT i.*, o.status as order_status
        FROM items i
        LEFT JOIN orders o ON i.order_id = o.id
        WHERE i.product_id = ?
        ORDER BY i.status, i.created_at
    ''', (product_id,))
    items = [dict(row) for row in items_result] if items_result else []
    
    # Generate QR code images for all items with error correction
    for item in items:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=8,
            border=4
        )
        qr.add_data(item['qr_code'])
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        img_buffer = BytesIO()
        img.save(img_buffer, format='PNG')
        item['qr_image'] = base64.b64encode(img_buffer.getvalue()).decode()
    
    # Count items by status
    status_counts = {
        'available': sum(1 for item in items if item['status'] == 'available'),
        'reserved': sum(1 for item in items if item['status'] == 'reserved'),
        'sold': sum(1 for item in items if item['status'] == 'sold'),
        'damaged': sum(1 for item in items if item['status'] == 'damaged')
    }
    
    return render_template('admin/product_items_qr.html', product=product, items=items, status_counts=status_counts)

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
    
    item = dict(item) if item else None
    
    # Generate QR code image with error correction for better scanning
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=5
    )
    qr.add_data(item['qr_code'])
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    img_buffer = BytesIO()
    img.save(img_buffer, format='PNG')
    img_str = base64.b64encode(img_buffer.getvalue()).decode()
    
    item_info = f"{item['category']} {item['size']} {item['color']} - Item #{item['id']} (Status: {item['status']})"
    
    return render_template('admin/item_qr.html', 
                         item=item,
                         qr_code=item['qr_code'], 
                         qr_image=img_str,
                         item_info=item_info)


@app.route('/admin/orders')
def admin_orders():
    if 'loggedin' not in session or session['user_type'] != 'admin':
        return redirect(url_for('login'))
    
    orders_result = query_db('''
        SELECT o.id, o.quantity, o.status, 
               datetime(o.created_at) as created_at,
               p.category, p.size, p.color, u.username
        FROM orders o
        JOIN products p ON o.product_id = p.id
        JOIN users u ON o.user_id = u.id
        ORDER BY o.created_at DESC
    ''')
    orders_list = []
    
    # Convert to dicts and get item QR codes for each order
    for row in orders_result:
        order = dict(row)  # Convert sqlite3.Row to dict
        items = query_db('''
            SELECT i.qr_code, i.id as item_id, i.status as item_status, i.validated
            FROM items i
            WHERE i.order_id = ?
        ''', (order['id'],))
        order['items'] = [dict(item) for item in items] if items else []
        orders_list.append(order)
    
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
    
    orders_result = query_db('''
        SELECT o.id, o.quantity, o.status, 
               datetime(o.created_at) as created_at,
               p.category, p.size, p.color, u.username
        FROM orders o
        JOIN products p ON o.product_id = p.id
        JOIN users u ON o.user_id = u.id
        WHERE o.status = ?
        ORDER BY o.created_at ASC
    ''', ('pending',))
    orders_list = []
    
    # Convert to dicts and get item QR codes for each order
    for row in orders_result:
        order = dict(row)  # Convert sqlite3.Row to dict
        items = query_db('''
            SELECT i.qr_code, i.id as item_id, i.status as item_status, i.validated
            FROM items i
            WHERE i.order_id = ?
        ''', (order['id'],))
        order['items'] = [dict(item) for item in items] if items else []
        orders_list.append(order)
    
    print(f"DEBUG: Approval orders page - Found {len(orders_list)} pending orders")
    for order in orders_list:
        print(f"  Order {order['id']}: {order['username']} - {order['category']} {order['size']} {order['color']}")
    
    return render_template('approval/orders.html', orders=orders_list)

@app.route('/approval/scan_order_qr/<int:order_id>')
def scan_order_qr(order_id):
    """Display QR codes for all items in an order for scanning"""
    if 'loggedin' not in session or session['user_type'] != 'approval_admin':
        return redirect(url_for('login'))
    
    # Get order details
    order_result = query_db('''
        SELECT o.id, o.quantity, o.status,
               p.category, p.size, p.color, u.username
        FROM orders o
        JOIN products p ON o.product_id = p.id
        JOIN users u ON o.user_id = u.id
        WHERE o.id = ?
    ''', (order_id,), one=True)
    
    if not order_result:
        flash('Order not found', 'error')
        return redirect(url_for('approval_orders'))
    
    order = dict(order_result)
    
    # Get all items for this order
    items_result = query_db('''
        SELECT i.id, i.qr_code, i.status, i.validated
        FROM items i
        WHERE i.order_id = ?
        ORDER BY i.id
    ''', (order_id,))
    items = [dict(row) for row in items_result] if items_result else []
    
    if not items:
        flash('No items found for this order', 'error')
        return redirect(url_for('approval_orders'))
    
    # Generate QR code images with scan URLs
    # Get the actual server URL - prioritize Railway/public URL over local IP
    # Check if running on Railway (has RAILWAY_ENVIRONMENT or PORT env var)
    is_railway = os.environ.get('RAILWAY_ENVIRONMENT') or os.environ.get('RAILWAY_SERVICE_NAME')
    
    # Check for custom server URL first (highest priority)
    server_url = os.environ.get('SERVER_URL')
    
    if server_url:
        # Use custom server URL if provided (for production or specific network setup)
        base_url = server_url.rstrip('/')
        print(f"DEBUG: Using custom SERVER_URL: {base_url}")
    elif is_railway:
        # On Railway, use the public Railway URL from request
        base_url = request.url_root.rstrip('/')
        # Remove any port numbers as Railway handles that
        if ':5000' in base_url:
            base_url = base_url.replace(':5000', '')
        print(f"DEBUG: Using Railway URL: {base_url}")
    else:
        # Local development - use request URL but replace localhost/127.0.0.1 with actual network IP
        base_url = request.host_url.rstrip('/')
        
        # Always detect and use the network IP for mobile access (even if accessed via IP)
        import socket
        try:
            # Connect to a remote address to get the local IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))  # Google DNS
            local_ip = s.getsockname()[0]
            s.close()
            
            # Always use the detected network IP for QR codes (for mobile access)
            # Replace any localhost/127.0.0.1 or even if accessed via different IP
            if 'localhost' in base_url or '127.0.0.1' in base_url:
                base_url = base_url.replace('localhost', local_ip).replace('127.0.0.1', local_ip)
            else:
                # Even if accessed via IP, use the detected network IP to ensure consistency
                # Extract port if present
                port = ':5000' if ':5000' in base_url else ''
                base_url = f"http://{local_ip}{port}"
            
            print(f"DEBUG: Using network IP for QR codes: {base_url}")
            print(f"DEBUG: Detected network IP: {local_ip}")
        except Exception as e:
            print(f"WARNING: Could not detect network IP: {e}")
            print("NOTE: Mobile devices may not be able to access the scan URL.")
            print("TIP: Set SERVER_URL environment variable or use your computer's IP address manually.")
    
    from urllib.parse import quote
    
    # Get network IP for display
    network_ip = None
    try:
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        network_ip = s.getsockname()[0]
        s.close()
    except:
        pass
    
    for item in items:
        # Create scan URL that mobile will access - properly encode QR code
        qr_code_encoded = quote(item['qr_code'], safe='')
        scan_url = f"{base_url}/scan/item/{qr_code_encoded}"
        
        # Generate QR code image with proper error correction for mobile scanning
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,  # Higher error correction for mobile
            box_size=12,  # Larger size for easier mobile scanning
            border=4
        )
        qr.add_data(scan_url)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        img_buffer = BytesIO()
        img.save(img_buffer, format='PNG')
        item['qr_image'] = base64.b64encode(img_buffer.getvalue()).decode()
        item['scan_url'] = scan_url
    
    return render_template('approval/scan_order_qr.html', 
                         order=order, 
                         items=items, 
                         network_ip=network_ip,
                         base_url=base_url)

@app.route('/test/scan/<qr_code>')
def test_scan_direct(qr_code):
    """Direct test endpoint for scan - accessible from mobile"""
    try:
        # Find item
        item_result = query_db('''
            SELECT i.*, p.category, p.size, p.color
            FROM items i
            JOIN products p ON i.product_id = p.id
            WHERE i.qr_code = ?
        ''', (qr_code,), one=True)
        
        if not item_result:
            return f'''
            <!DOCTYPE html>
            <html><head><title>Test - QR Not Found</title></head>
            <body style="font-family: Arial; padding: 20px;">
                <h1>QR Code Not Found</h1>
                <p>QR Code: {qr_code}</p>
                <p><a href="/test/network">Back to Network Test</a></p>
            </body></html>
            '''
        
        item = dict(item_result)
        return f'''
        <!DOCTYPE html>
        <html><head>
            <title>Test Scan - Success</title>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="font-family: Arial; padding: 20px; background: #f0f0f0;">
            <div style="background: white; padding: 20px; border-radius: 10px; max-width: 500px; margin: 0 auto;">
                <h1 style="color: green;">✓ Scan Route is Working!</h1>
                <h2>Product Details:</h2>
                <p><strong>Category:</strong> {item.get('category', 'N/A')}</p>
                <p><strong>Size:</strong> {item.get('size', 'N/A')}</p>
                <p><strong>Color:</strong> {item.get('color', 'N/A')}</p>
                <p><strong>Status:</strong> {item.get('status', 'N/A')}</p>
                <p><strong>QR Code:</strong> {qr_code}</p>
                <hr>
                <p><a href="/scan/item/{qr_code}">View Full Product Details</a></p>
                <p><a href="/test/network">Back to Network Test</a></p>
            </div>
        </body></html>
        '''
    except Exception as e:
        return f"Error: {e}"

@app.route('/status')
def status_page():
    """Server status dashboard page"""
    import platform
    try:
        import flask
        flask_version = flask.__version__
    except:
        flask_version = "Unknown"
    
    python_version = platform.python_version()
    environment = "Development" if app.debug else "Production"
    debug_mode = "Enabled" if app.debug else "Disabled"
    
    return render_template('status.html',
                         flask_version=flask_version,
                         python_version=python_version,
                         environment=environment,
                         debug_mode=debug_mode)

@app.route('/api/status')
def api_status():
    """API endpoint for status check"""
    import time
    try:
        # Test database connection
        test_db = query_db('SELECT 1', one=True)
        db_status = "connected" if test_db else "error"
    except:
        db_status = "error"
    
    return jsonify({
        'status': 'online',
        'database': db_status,
        'timestamp': time.time()
    })

@app.route('/api/check_order_updates')
def check_order_updates():
    """API endpoint to check if customer has any order status updates"""
    if 'loggedin' not in session or session['user_type'] != 'customer':
        return jsonify({'has_updates': False, 'message': 'Unauthorized'}), 401
    
    try:
        # Check if user has any confirmed orders
        confirmed_orders = query_db('''
            SELECT COUNT(*) as count
            FROM orders
            WHERE user_id = ? AND status = 'confirmed'
        ''', (session['id'],), one=True)
        
        has_confirmed = confirmed_orders and dict(confirmed_orders).get('count', 0) > 0
        
        return jsonify({
            'has_updates': has_confirmed,
            'confirmed_count': dict(confirmed_orders).get('count', 0) if confirmed_orders else 0
        })
    except Exception as e:
        print(f"ERROR in check_order_updates: {e}")
        return jsonify({'has_updates': False, 'error': str(e)})

@app.route('/test/network')
def test_network():
    """Test endpoint to verify network connectivity - Mobile Friendly"""
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return f'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Network Test - Mobile QR Scanning</title>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    padding: 20px;
                    max-width: 600px;
                    margin: 0 auto;
                    background: #f5f5f5;
                }}
                .card {{
                    background: white;
                    border-radius: 10px;
                    padding: 25px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    margin-bottom: 20px;
                }}
                h1 {{
                    color: #28a745;
                    margin-top: 0;
                }}
                .status {{
                    background: #d4edda;
                    color: #155724;
                    padding: 15px;
                    border-radius: 5px;
                    margin: 15px 0;
                    font-weight: bold;
                }}
                .ip-box {{
                    background: #e7f3ff;
                    border: 2px solid #0066cc;
                    padding: 15px;
                    border-radius: 5px;
                    margin: 15px 0;
                    font-size: 18px;
                    text-align: center;
                    word-break: break-all;
                }}
                .instructions {{
                    background: #fff3cd;
                    border-left: 4px solid #ffc107;
                    padding: 15px;
                    margin: 15px 0;
                }}
                .instructions ol {{
                    margin: 10px 0;
                    padding-left: 20px;
                }}
                .troubleshoot {{
                    background: #f8d7da;
                    border-left: 4px solid #dc3545;
                    padding: 15px;
                    margin: 15px 0;
                }}
                code {{
                    background: #f4f4f4;
                    padding: 2px 6px;
                    border-radius: 3px;
                    font-family: monospace;
                }}
                .btn {{
                    display: inline-block;
                    background: #007bff;
                    color: white;
                    padding: 10px 20px;
                    text-decoration: none;
                    border-radius: 5px;
                    margin: 10px 5px 10px 0;
                }}
                .btn:hover {{
                    background: #0056b3;
                }}
            </style>
        </head>
        <body>
            <div class="card">
                <h1>✓ Network Test - Server is Running!</h1>
                <div class="status">✓ Server is accessible from network</div>
                
                <h3>Your Network IP Address:</h3>
                <div class="ip-box">
                    <strong>{local_ip}</strong>
                </div>
                
                <h3>Server URL:</h3>
                <div class="ip-box">
                    <code>http://{local_ip}:5000</code>
                </div>
            </div>
            
            <div class="card">
                <h2>📱 Mobile QR Scanning Instructions:</h2>
                <div class="instructions">
                    <ol>
                        <li><strong>Make sure your mobile phone is on the SAME Wi-Fi network</strong> as this computer</li>
                        <li>On your computer, go to the order page with QR codes</li>
                        <li>Open your phone's <strong>camera app</strong> (no special QR app needed)</li>
                        <li>Point the camera at a QR code on your computer screen</li>
                        <li>A notification/link will appear - <strong>tap it</strong></li>
                        <li>The product details page will open on your phone</li>
                        <li>The computer page will automatically update when scanned</li>
                    </ol>
                </div>
                
                <h3>Test Mobile Access:</h3>
                <p>On your mobile phone browser, try opening:</p>
                <div class="ip-box" style="font-size: 16px;">
                    <code>http://{local_ip}:5000</code>
                </div>
                <p>If you see this page on your phone, mobile scanning will work! ✓</p>
            </div>
            
            <div class="card">
                <h2>⚠ Troubleshooting:</h2>
                <div class="troubleshoot">
                    <p><strong>If mobile cannot access or scan QR codes:</strong></p>
                    <ol>
                        <li><strong>Check Wi-Fi:</strong> Both devices must be on the same network</li>
                        <li><strong>Windows Firewall:</strong> Allow Python/Flask through firewall on port 5000
                            <ul>
                                <li>Windows Security → Firewall → Allow an app</li>
                                <li>Find Python and allow it, or create rule for port 5000</li>
                            </ul>
                        </li>
                        <li><strong>Router Settings:</strong> Some routers block device-to-device communication
                            <ul>
                                <li>Check if "AP Isolation" or "Client Isolation" is enabled - disable it</li>
                            </ul>
                        </li>
                        <li><strong>Test Connection:</strong> Try typing <code>http://{local_ip}:5000</code> directly in mobile browser</li>
                        <li><strong>Server Status:</strong> Make sure server shows "Running on http://0.0.0.0:5000" (not just localhost)</li>
                    </ol>
                </div>
            </div>
            
            <div class="card">
                <h3>Quick Links:</h3>
                <a href="/" class="btn">🏠 Home</a>
                <a href="/approval/orders" class="btn">📦 Orders</a>
            </div>
        </body>
        </html>
        '''
    except Exception as e:
        return f'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Network Test Error</title>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="font-family: Arial; padding: 20px;">
            <h1 style="color: red;">⚠ Network Detection Error</h1>
            <p>Could not detect network IP address.</p>
            <p>Error: {e}</p>
            <p>Mobile scanning may not work. Please check your network connection.</p>
        </body>
        </html>
        '''

@app.route('/scan/item/<path:qr_code>')
def scan_item_mobile(qr_code):
    """Mobile endpoint - shows product details when QR code is scanned"""
    try:
        from urllib.parse import unquote
        
        # Clean up the QR code (remove any URL encoding or extra characters)
        qr_code = qr_code.strip()
        print(f"DEBUG: Scanning QR code (raw): {qr_code}")
        
        # Try multiple decoding strategies
        search_codes = [qr_code]  # Start with original
        
        # Try URL-decoded version
        decoded_qr = unquote(qr_code)
        if decoded_qr != qr_code:
            search_codes.append(decoded_qr)
            print(f"DEBUG: Added URL-decoded QR code: {decoded_qr}")
        
        # Try double-decoded (in case of double encoding)
        double_decoded = unquote(decoded_qr)
        if double_decoded != decoded_qr and double_decoded not in search_codes:
            search_codes.append(double_decoded)
            print(f"DEBUG: Added double-decoded QR code: {double_decoded}")
        
        # Try removing any trailing slashes or extra path components
        clean_qr = qr_code.split('/')[0].split('?')[0].split('#')[0]
        if clean_qr not in search_codes:
            search_codes.append(clean_qr)
            print(f"DEBUG: Added cleaned QR code: {clean_qr}")
        
        # Find item by QR code - try all variations
        item_result = None
        for search_code in search_codes:
            print(f"DEBUG: Trying to find QR code: {search_code}")
            item_result = query_db('''
                SELECT i.*, p.category, p.size, p.color,
                       o.id as order_id, o.status as order_status
                FROM items i
                JOIN products p ON i.product_id = p.id
                LEFT JOIN orders o ON i.order_id = o.id
                WHERE i.qr_code = ?
            ''', (search_code,), one=True)
            
            if item_result:
                print(f"DEBUG: Found item with QR code: {search_code}")
                qr_code = search_code  # Use the matched code
                break
        
        print(f"DEBUG: Query result: {item_result}")
        
        if not item_result:
            print(f"DEBUG: QR code not found in database: {qr_code}")
            # Show helpful error with all available QR codes for debugging
            all_qr_codes = query_db('SELECT qr_code FROM items LIMIT 5')
            qr_list = [dict(r)['qr_code'] for r in all_qr_codes] if all_qr_codes else []
            return render_template('scan/item_not_found.html', qr_code=qr_code, available_qr_codes=qr_list)
        
        item = dict(item_result)
        
        # Debug: Print item data
        print(f"DEBUG: Item found - ID: {item.get('id')}, Category: {item.get('category')}, QR: {qr_code}")
        
        # Ensure all required fields are present
        if not item.get('category'):
            print(f"WARNING: Item missing category field. Item data: {item}")
        
        # Mark item as scanned and validated
        try:
            conn = get_db()
            cursor = conn.cursor()
            
            # Update item as validated
            cursor.execute('''
                UPDATE items 
                SET validated = 1, validated_at = CURRENT_TIMESTAMP
                WHERE qr_code = ? AND validated = 0
            ''', (qr_code,))
            
            # Check if this item belongs to an order
            if item.get('order_id'):
                # Check if all items in this order are now validated
                cursor.execute('''
                    SELECT COUNT(*) as total, 
                           SUM(CASE WHEN validated = 1 THEN 1 ELSE 0 END) as validated_count
                    FROM items 
                    WHERE order_id = ?
                ''', (item['order_id'],))
                order_check = cursor.fetchone()
                
                if order_check:
                    total_items = order_check[0] if isinstance(order_check, tuple) else order_check['total']
                    validated_count = order_check[1] if isinstance(order_check, tuple) else order_check['validated_count']
                    
                    # If all items are validated, auto-confirm the order and notify customer
                    if validated_count == total_items:
                        print(f"DEBUG: All items scanned! Order {item['order_id']}: {validated_count}/{total_items} items validated")
                        # Auto-confirm order
                        try:
                            # Get order details for customer notification
                            order_details = query_db('''
                                SELECT o.*, u.username, u.email, p.category, p.size, p.color
                                FROM orders o
                                JOIN users u ON o.user_id = u.id
                                JOIN products p ON o.product_id = p.id
                                WHERE o.id = ?
                            ''', (item['order_id'],), one=True)
                            
                            if order_details:
                                order_details = dict(order_details)
                                # Update order status to confirmed
                                cursor.execute('UPDATE orders SET status = ? WHERE id = ?', ('confirmed', item['order_id']))
                                
                                # Mark reserved items as sold
                                cursor.execute('''
                                    UPDATE items 
                                    SET status = 'sold' 
                                    WHERE order_id = ? AND status = 'reserved'
                                ''', (item['order_id'],))
                                
                                # Update product stock
                                cursor.execute('''
                                    UPDATE products 
                                    SET stock = (SELECT COUNT(*) FROM items WHERE product_id = ? AND status = 'available')
                                    WHERE id = ?
                                ''', (order_details['product_id'], order_details['product_id']))
                                
                                conn.commit()
                                
                                print(f"DEBUG: [SUCCESS] Order {item['order_id']} auto-confirmed! Customer: {order_details.get('username', 'N/A')}")
                                print(f"DEBUG: [NOTIFICATION] Customer notification: Order confirmed for {order_details.get('category', '')} {order_details.get('size', '')} {order_details.get('color', '')}")
                        except Exception as e:
                            print(f"ERROR auto-confirming order: {e}")
                            import traceback
                            traceback.print_exc()
                    else:
                        print(f"DEBUG: Item {item.get('id')} scanned. Order {item['order_id']}: {validated_count}/{total_items} items validated")
            
            conn.commit()
            cursor.close()
            conn.close()
        except Exception as e:
            print(f"ERROR updating item validation: {e}")
            import traceback
            traceback.print_exc()
            # Continue even if validation update fails
        
        # Ensure item has all required fields with defaults
        item.setdefault('category', 'N/A')
        item.setdefault('size', 'N/A')
        item.setdefault('color', 'N/A')
        item.setdefault('status', 'available')
        # Price is not stored in items table, set to None
        # If you need price, it should come from products table or be calculated
        item.setdefault('price', None)
        item.setdefault('qr_code', qr_code)  # Ensure QR code is in item dict
        
        print(f"DEBUG: Rendering template with item: {item}")
        
        try:
            return render_template('scan/item_details.html', item=item)
        except Exception as template_error:
            print(f"ERROR rendering template: {template_error}")
            import traceback
            traceback.print_exc()
            # Return a simple HTML page with item data
            return f'''
            <!DOCTYPE html>
            <html>
            <head>
                <title>Product Details</title>
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <style>
                    body {{ font-family: Arial; padding: 20px; background: #f0f0f0; }}
                    .container {{ background: white; padding: 20px; border-radius: 10px; max-width: 500px; margin: 0 auto; }}
                    h1 {{ color: #333; }}
                    .detail {{ margin: 10px 0; padding: 10px; background: #f9f9f9; border-radius: 5px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>Product Details</h1>
                    <div class="detail"><strong>Category:</strong> {item.get('category', 'N/A')}</div>
                    <div class="detail"><strong>Size:</strong> {item.get('size', 'N/A')}</div>
                    <div class="detail"><strong>Color:</strong> {item.get('color', 'N/A')}</div>
                    <div class="detail"><strong>Price:</strong> ${item.get('price', 0) or 0:.2f}</div>
                    <div class="detail"><strong>Status:</strong> {item.get('status', 'N/A')}</div>
                    <div class="detail"><strong>QR Code:</strong> {item.get('qr_code', qr_code)}</div>
                    <p style="margin-top: 20px; color: green;">Item scanned and validated successfully!</p>
                </div>
            </body>
            </html>
            '''
    except Exception as e:
        # Safely handle error message encoding
        try:
            error_msg = str(e)
            # Try to encode as ASCII, removing problematic characters
            error_msg_safe = error_msg.encode('ascii', 'ignore').decode('ascii')
        except:
            error_msg_safe = "An error occurred while processing your scan"
        
        # Print error safely
        try:
            print(f"ERROR in scan_item_mobile: {error_msg_safe}")
        except:
            print("ERROR in scan_item_mobile: Encoding error occurred")
        
        # Print traceback safely
        try:
            import traceback
            traceback.print_exc()
        except UnicodeEncodeError:
            print("ERROR: Could not print traceback due to encoding issue")
        
        # Return a simple error page
        return f'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Error</title>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <meta charset="UTF-8">
        </head>
        <body style="font-family: Arial, sans-serif; padding: 20px; text-align: center; background: #f5f5f5;">
            <div style="background: white; border-radius: 10px; padding: 30px; max-width: 500px; margin: 50px auto; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                <div style="font-size: 48px; color: #dc3545; margin-bottom: 20px;">!</div>
                <h1 style="color: #333; margin-bottom: 15px;">Error Loading Page</h1>
                <p style="color: #666; margin-bottom: 20px;">An error occurred while processing your scan.</p>
                <p style="color: #666; margin-bottom: 30px;">Please try again or contact support.</p>
                <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin-top: 20px;">
                    <p style="color: #666; font-size: 12px; margin: 0;">Error: {error_msg_safe[:100]}</p>
                </div>
                <button onclick="window.location.reload()" style="background: #007bff; color: white; border: none; padding: 12px 30px; border-radius: 5px; font-size: 16px; cursor: pointer; margin-top: 20px;">
                    Try Again
                </button>
            </div>
        </body>
        </html>
        ''', 500

@app.route('/approval/check_scan_status/<int:order_id>')
def check_scan_status(order_id):
    """API endpoint to check if all items in order are scanned"""
    if 'loggedin' not in session or session['user_type'] != 'approval_admin':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    # Get all items for this order with validation timestamp
    items_result = query_db('''
        SELECT i.id, i.qr_code, i.validated, i.validated_at
        FROM items i
        WHERE i.order_id = ?
        ORDER BY i.id
    ''', (order_id,))
    items = [dict(row) for row in items_result] if items_result else []
    
    if not items:
        return jsonify({'success': False, 'message': 'No items found'})
    
    total_items = len(items)
    scanned_items = sum(1 for item in items if item['validated'])
    all_scanned = scanned_items == total_items
    
    # Check if order is confirmed
    order_status = query_db('SELECT status FROM orders WHERE id = ?', (order_id,), one=True)
    order_confirmed = order_status and dict(order_status).get('status') == 'confirmed'
    
    return jsonify({
        'success': True,
        'total_items': total_items,
        'scanned_items': scanned_items,
        'all_scanned': all_scanned,
        'order_confirmed': order_confirmed,
        'items': items
    })

@app.route('/approval/check_order_complete/<int:order_id>')
def check_order_complete(order_id):
    """API endpoint to check if order is complete (for mobile scanning)"""
    try:
        # Get order status
        order_result = query_db('''
            SELECT o.status, o.id,
                   COUNT(i.id) as total_items,
                   SUM(CASE WHEN i.validated = 1 THEN 1 ELSE 0 END) as scanned_items
            FROM orders o
            LEFT JOIN items i ON o.id = i.order_id
            WHERE o.id = ?
            GROUP BY o.id, o.status
        ''', (order_id,), one=True)
        
        if not order_result:
            return jsonify({'success': False, 'message': 'Order not found'})
        
        order = dict(order_result)
        all_scanned = order.get('scanned_items', 0) == order.get('total_items', 0)
        order_confirmed = order.get('status') == 'confirmed'
        
        return jsonify({
            'success': True,
            'all_scanned': all_scanned,
            'order_confirmed': order_confirmed,
            'order_status': order.get('status'),
            'message': 'Order confirmed! You will receive a confirmation message.' if order_confirmed else 'Scanning in progress...'
        })
    except Exception as e:
        print(f"ERROR in check_order_complete: {e}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/approval/validate_qr_scanner')
def validate_qr_scanner_page():
    """QR Code validation scanner page with camera"""
    if 'loggedin' not in session or session['user_type'] != 'approval_admin':
        return redirect(url_for('login'))
    
    return render_template('approval/validate_qr_scanner.html')

@app.route('/approval/validate_qr_code', methods=['POST'])
def validate_qr_code_scanner():
    """Validate QR code from scanner/camera"""
    if 'loggedin' not in session or session['user_type'] != 'approval_admin':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    data = request.get_json()
    qr_code = data.get('qr_code', '').strip()
    
    if not qr_code:
        return jsonify({'success': False, 'message': 'QR code is required'})
    
    # Find item by QR code
    item_result = query_db('''
        SELECT i.*, p.category, p.size, p.color
        FROM items i
        JOIN products p ON i.product_id = p.id
        WHERE i.qr_code = ?
    ''', (qr_code,), one=True)
    
    if not item_result:
        return jsonify({'success': False, 'message': 'QR code not found in system'})
    
    item = dict(item_result) if item_result else None
    was_already_validated = item.get('validated', False)
    
    # Validate the item (update even if already validated - allows re-validation)
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE items 
        SET validated = 1, validated_at = CURRENT_TIMESTAMP, validated_by = ?
        WHERE qr_code = ?
    ''', (session['id'], qr_code))
    conn.commit()
    cursor.close()
    conn.close()
    
    product_info = f"{item['category']} {item['size']} {item['color']}"
    
    if was_already_validated:
        message = f"QR code was already validated. Re-validated successfully! Item is ready for orders."
    else:
        message = "QR code validated successfully! Item is now ready for customer orders!"
    
    return jsonify({
        'success': True,
        'item_id': item['id'],
        'qr_code': qr_code,
        'product_info': product_info,
        'status': item['status'],
        'message': message
    })

@app.route('/approval/validate_qr', methods=['POST'])
def validate_qr():
    if 'loggedin' not in session or session['user_type'] != 'approval_admin':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    qr_code = request.form.get('qr_code')
    order_id = request.form.get('order_id')
    
    # Check for duplicate QR code across items and products
    # Check in items table
    duplicate_item = query_db('SELECT id FROM items WHERE qr_code = ?', (qr_code,), one=True)
    
    # Check in products table
    duplicate_product = query_db('SELECT id FROM products WHERE qr_code = ?', (qr_code,), one=True)
    
    if duplicate_item or duplicate_product:
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
        # Get order details
        order = query_db('SELECT user_id FROM orders WHERE id = ?', (order_id,), one=True)
        
        if not order:
            flash('Order not found', 'error')
            return redirect(url_for('approval_orders'))
        
        print(f"DEBUG: Approving order {order_id}")
        
        # Get order details
        order_details = query_db('SELECT product_id, quantity FROM orders WHERE id = ?', (order_id,), one=True)
        order_details = dict(order_details) if order_details else None
        
        if not order_details:
            flash('Order details not found', 'error')
            return redirect(url_for('approval_orders'))
        
        # Get all item QR codes for this order to validate uniqueness
        order_items = query_db('''
            SELECT i.qr_code, i.id
            FROM items i
            WHERE i.order_id = ?
        ''', (order_id,))
        order_items = [dict(item) for item in order_items] if order_items else []
        
        # Validate that all item QR codes are unique
        conn = get_db()
        cursor = conn.cursor()
        duplicate_found = False
        
        for item in order_items:
            qr_code = item['qr_code']
            # Check for duplicates in items table (excluding current item)
            cursor.execute('''
                SELECT id FROM items 
                WHERE qr_code = ? AND id != ?
            ''', (qr_code, item['id']))
            dup_item = cursor.fetchone()
            
            # Check in products table
            cursor.execute('SELECT id FROM products WHERE qr_code = ?', (qr_code,))
            dup_product = cursor.fetchone()
            
            if dup_item or dup_product:
                duplicate_found = True
                print(f"DEBUG: Duplicate QR code found: {qr_code[:20]}...")
                break
        
        if duplicate_found:
            # Duplicate item QR code found - cancel order
            print(f"DEBUG: [DUPLICATE] DUPLICATE ITEM QR CODE DETECTED")
            cursor.execute('UPDATE orders SET status = ? WHERE id = ?', ('cancelled', order_id))
            conn.commit()
            cursor.close()
            conn.close()
            flash('[ERROR] Approval Failed: Duplicate item QR code detected! The customer should contact support team: 1234567890', 'error')
            
            # Check if this is an AJAX request
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({
                    'success': False,
                    'message': 'Duplicate item QR code detected! The customer should contact support team: 1234567890'
                })
        else:
            # All item QR codes are unique - confirm order
            print(f"DEBUG: [SUCCESS] All item QR codes are unique - confirming order {order_id}")
            
            # Update order status to confirmed
            cursor.execute('UPDATE orders SET status = ? WHERE id = ?', ('confirmed', order_id))
            
            # Mark reserved items as sold
            cursor.execute('''
                UPDATE items 
                SET status = 'sold' 
                WHERE order_id = ? AND status = 'reserved'
            ''', (order_id,))
            
            # Update product stock count from available items
            cursor.execute('''
                UPDATE products 
                SET stock = (SELECT COUNT(*) FROM items WHERE product_id = ? AND status = 'available')
                WHERE id = ?
            ''', (order_details['product_id'], order_details['product_id']))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            flash('[SUCCESS] All item QR codes are unique! Order confirmed successfully. Customer will see "Your order has been confirmed!" message.', 'success')
        
        # Check if this is an AJAX request
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'success': True,
                'message': 'Order confirmed successfully',
                'redirect_url': url_for('approval_orders')
            })
        
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
            print("[OK] Database initialized successfully")
        except Exception as e:
            print(f"[WARNING] Database initialization failed: {e}")
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
        print(f"[WARNING] Database init on startup failed, will retry on first request: {e}")

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
    # Bind to 0.0.0.0 to allow access from mobile devices on the same network
    # Print network information for mobile access
    import socket
    
    print("\n" + "="*70)
    print("STARTING FLASK SERVER")
    print("="*70)
    
    # Check if port is available
    port = 5000
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    port_in_use = sock.connect_ex(('127.0.0.1', port)) == 0
    sock.close()
    
    if port_in_use:
        print(f"\n[WARNING] Port {port} appears to be in use!")
        print("Another process might be using this port.")
        print("Try closing other Flask/Python processes or use a different port.")
        print("\nTo use a different port, modify the app.run() line at the bottom of app.py")
        print("="*70 + "\n")
    else:
        print(f"[OK] Port {port} is available")
    
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        
        print(f"\n[SUCCESS] Server will be accessible at:")
        print(f"  Local:    http://127.0.0.1:{port}")
        print(f"  Network:  http://{local_ip}:{port}")
        print(f"\n[STATUS DASHBOARD]")
        print(f"  View output screen: http://127.0.0.1:{port}/status")
        print(f"\n[MOBILE ACCESS]")
        print(f"  URL: http://{local_ip}:{port}")
        print(f"  Make sure mobile is on the SAME Wi-Fi network!")
        print(f"\n[TEST ENDPOINTS]")
        print(f"  Network test: http://{local_ip}:{port}/test/network")
        print(f"  Local test:   http://127.0.0.1:{port}/test/network")
        print("\n[FIREWALL]")
        print("  If mobile cannot connect, check Windows Firewall:")
        print("  1. Allow Python through firewall")
        print("  2. Or create rule for port 5000")
        print("  3. See NETWORK_TROUBLESHOOTING.md for details")
        print("="*70 + "\n")
    except Exception as e:
        print(f"[WARNING] Could not detect network IP: {e}")
        print(f"  Local access: http://127.0.0.1:{port}")
        print(f"  Network access may not work")
        print("="*70 + "\n")
    
    # Log startup info to file
    try:
        with open('server_startup.log', 'a', encoding='utf-8') as f:
            f.write(f"\n{'='*70}\n")
            f.write(f"Server Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"{'='*70}\n")
            f.write(f"Port: {port}\n")
            f.write(f"Local URL: http://127.0.0.1:{port}\n")
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.connect(("8.8.8.8", 80))
                local_ip = s.getsockname()[0]
                s.close()
                f.write(f"Network URL: http://{local_ip}:{port}\n")
            except:
                f.write(f"Network URL: Could not detect\n")
            f.write(f"{'='*70}\n\n")
    except Exception as e:
        pass  # Don't fail if logging fails
    
    try:
        app.run(debug=True, host='0.0.0.0', port=port, threaded=True)
    except OSError as e:
        if "Address already in use" in str(e) or "address is already in use" in str(e).lower():
            print(f"\n[ERROR] Port {port} is already in use!")
            print("Another process is using this port.")
            print("\nSolutions:")
            print("1. Close other Flask/Python processes")
            print("2. Find and kill the process:")
            print(f"   netstat -ano | findstr :{port}")
            print("   Then: taskkill /PID <PID> /F")
            print("3. Use a different port (modify app.run() line)")
        else:
            print(f"\n[ERROR] Failed to start server: {e}")
        sys.exit(1)
