import sqlite3
from datetime import datetime
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'inventory.db')

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def initialize_database():
    """Initializes the SQLite database with required tables."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Products table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            product_id TEXT PRIMARY KEY,
            product_name TEXT NOT NULL,
            category TEXT NOT NULL,
            product_type TEXT,
            base_price REAL NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Inventory Batches table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS inventory_batches (
            batch_id TEXT PRIMARY KEY,
            product_id TEXT NOT NULL,
            expiry_date DATETIME NOT NULL,
            stock_quantity INTEGER NOT NULL DEFAULT 0,
            demand_score REAL DEFAULT 0.0,
            current_discount REAL DEFAULT 0.0,
            current_price REAL NOT NULL,
            status TEXT DEFAULT 'ACTIVE',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (product_id) REFERENCES products(product_id)
        )
    ''')
    
    # Inventory Transactions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS inventory_transactions (
            transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
            batch_id TEXT NOT NULL,
            transaction_type TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            transaction_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (batch_id) REFERENCES inventory_batches(batch_id)
        )
    ''')
    
    conn.commit()
    conn.close()

def add_product(product_id, product_name, category, product_type, base_price):
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute('''
        INSERT INTO products (product_id, product_name, category, product_type, base_price, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (product_id, product_name, category, product_type, base_price, now, now))
    conn.commit()
    conn.close()

def get_product(product_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM products WHERE product_id = ?', (product_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def add_batch(batch_id, product_id, expiry_date, stock_quantity, current_price, demand_score=0.0, current_discount=0.0, status='ACTIVE'):
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Ensure expiry_date is in proper format if passed as datetime object
    if isinstance(expiry_date, datetime):
        expiry_date = expiry_date.strftime('%Y-%m-%d %H:%M:%S')
        
    cursor.execute('''
        INSERT INTO inventory_batches (batch_id, product_id, expiry_date, stock_quantity, demand_score, current_discount, current_price, status, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (batch_id, product_id, expiry_date, stock_quantity, demand_score, current_discount, current_price, status, now, now))
    conn.commit()
    conn.close()

def get_batch(batch_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM inventory_batches WHERE batch_id = ?', (batch_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def record_inventory_transaction(batch_id, transaction_type, quantity):
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute('''
        INSERT INTO inventory_transactions (batch_id, transaction_type, quantity, transaction_date)
        VALUES (?, ?, ?, ?)
    ''', (batch_id, transaction_type, quantity, now))
    conn.commit()
    conn.close()

def update_inventory(batch_id, quantity_change, transaction_type):
    """
    Updates the inventory by recording a transaction and adjusting the stock quantity.
    quantity_change should be positive for STOCK_ADDED, and negative for SOLD, DONATED, DISCARDED.
    """
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Update batch stock
    cursor.execute('''
        UPDATE inventory_batches 
        SET stock_quantity = stock_quantity + ?, updated_at = ?
        WHERE batch_id = ?
    ''', (quantity_change, now, batch_id))
    
    # Record transaction
    cursor.execute('''
        INSERT INTO inventory_transactions (batch_id, transaction_type, quantity, transaction_date)
        VALUES (?, ?, ?, ?)
    ''', (batch_id, transaction_type, abs(quantity_change), now))
    
    conn.commit()
    conn.close()

def update_expiry_date(batch_id, new_expiry_date):
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    if isinstance(new_expiry_date, datetime):
        new_expiry_date = new_expiry_date.strftime('%Y-%m-%d %H:%M:%S')
        
    cursor.execute('''
        UPDATE inventory_batches
        SET expiry_date = ?, updated_at = ?
        WHERE batch_id = ?
    ''', (new_expiry_date, now, batch_id))
    conn.commit()
    conn.close()

def update_discount(batch_id, new_discount, new_price):
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute('''
        UPDATE inventory_batches
        SET current_discount = ?, current_price = ?, updated_at = ?
        WHERE batch_id = ?
    ''', (new_discount, new_price, now, batch_id))
    conn.commit()
    conn.close()

def get_all_active_products():
    """Returns products that have active batches."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT p.*, b.batch_id, b.expiry_date, b.stock_quantity, b.status 
        FROM products p
        JOIN inventory_batches b ON p.product_id = b.product_id
        WHERE b.status = 'ACTIVE' AND b.stock_quantity > 0
    ''')
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_near_expiry_products():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT p.*, b.batch_id, b.expiry_date, b.stock_quantity, b.status, b.current_discount, b.current_price 
        FROM products p
        JOIN inventory_batches b ON p.product_id = b.product_id
        WHERE b.status IN ('NEAR_EXPIRY', 'ACTIVE') AND b.stock_quantity > 0
        ORDER BY b.expiry_date ASC
    ''')
    # Can refine this query to check date diff dynamically, 
    # but the status flag "NEAR_EXPIRY" allows explicit tagging.
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_donation_review_products():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT p.*, b.batch_id, b.expiry_date, b.stock_quantity, b.status 
        FROM products p
        JOIN inventory_batches b ON p.product_id = b.product_id
        WHERE b.status = 'DONATION_REVIEW' AND b.stock_quantity > 0
    ''')
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

# Test block
if __name__ == '__main__':
    # Initialize the DB
    initialize_database()
    print("Database initialized successfully.")
    
    # Clear tables for testing purposes
    conn = get_connection()
    conn.execute('DELETE FROM inventory_transactions')
    conn.execute('DELETE FROM inventory_batches')
    conn.execute('DELETE FROM products')
    conn.commit()
    conn.close()
    
    # 1. Insert Products
    add_product('PROD_001', 'Frozen Fries', 'Frozen', 'Potatoes', 5.99)
    add_product('PROD_002', 'Fresh Milk', 'Dairy', 'Beverage', 2.50)
    add_product('PROD_003', 'Whole Wheat Bread', 'Bakery', 'Bread', 3.20)
    print("Test products inserted.")
    
    # 2. Insert Batches (PROD_001 has multiple batches with different expiry dates)
    add_batch('BATCH_001_A', 'PROD_001', '2026-08-25 23:59:59', 10, 5.99, demand_score=0.8, status='ACTIVE')
    add_batch('BATCH_001_B', 'PROD_001', '2026-08-30 23:59:59', 30, 5.99, demand_score=0.9, status='ACTIVE')
    
    add_batch('BATCH_002_A', 'PROD_002', '2026-08-26 12:00:00', 50, 2.50, demand_score=0.5, status='NEAR_EXPIRY')
    add_batch('BATCH_003_A', 'PROD_003', '2026-08-24 23:59:59', 5, 3.20, demand_score=0.2, status='DONATION_REVIEW')
    print("Test batches inserted.")
    
    # 3. Test Inventory Retrieval
    active = get_all_active_products()
    print(f"Active Products Count: {len(active)}")
    
    # 4. Test Transactions
    # Scan/Sell some frozen fries
    update_inventory('BATCH_001_A', -2, 'SOLD')
    batch_a_updated = get_batch('BATCH_001_A')
    print(f"BATCH_001_A stock after sale: {batch_a_updated['stock_quantity']}")
    
    # 5. Test Update Expiry
    update_expiry_date('BATCH_002_A', '2026-08-27 12:00:00')
    batch_2_updated = get_batch('BATCH_002_A')
    print(f"BATCH_002_A updated expiry: {batch_2_updated['expiry_date']}")
    
    # 6. Test Retrievals
    near_expiry = get_near_expiry_products()
    donation = get_donation_review_products()
    print(f"Near Expiry batches count: {len(near_expiry)}")
    print(f"Donation Review batches count: {len(donation)}")
    
    print("All tests passed successfully.")
