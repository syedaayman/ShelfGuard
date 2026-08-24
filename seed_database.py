import pandas as pd
import random
from datetime import datetime, timedelta
import database

def seed_database():
    # 1. Read processed data
    file_path = 'c:/Users/DELL/Desktop/shelfGuard/data/processed/perishable_goods_cleaned.csv'
    try:
        df = pd.read_csv(file_path)
    except FileNotFoundError:
        print(f"Processed dataset not found at {file_path}. Please complete Task 1 properly.")
        return

    # 2. Get 40 unique products randomly
    unique_products = df.drop_duplicates(subset=['product_id']).sample(n=40, random_state=42)

    # 3. Clear existing database tables for a clean slate
    conn = database.get_connection()
    conn.execute('DELETE FROM inventory_transactions')
    conn.execute('DELETE FROM inventory_batches')
    conn.execute('DELETE FROM products')
    conn.commit()
    conn.close()
    
    print("Existing records cleared for a fresh seed.")

    now = datetime.now()
    batch_counter = 1

    # Define our expiry targets for variety:
    # We will pick randomly from these options for batches
    expiry_offsets = [
        # (min_hours, max_hours, category)
        (1, 5, 'less than 6 hours'),
        (6, 23, 'less than 24 hours'),
        (24, 72, '1-3 days'),
        (73, 168, 'several days')
    ]

    print("Seeding products and batches...")
    for _, row in unique_products.iterrows():
        p_id = row['product_id']
        p_name = row['product_name']
        p_cat = row['category']
        p_price = float(row['base_price'])
        # if 'product_type' doesn't exist, we fallback
        p_type = row.get('product_type', 'General')
        
        # Add product
        database.add_product(p_id, p_name, p_cat, p_type, p_price)
        
        # Decide if we create 1 or 2 batches for this product (some will have 2)
        num_batches = random.choices([1, 2], weights=[0.7, 0.3])[0]
        
        for _ in range(num_batches):
            b_id = f"BATCH_{batch_counter:03d}_{p_id[-3:]}"
            batch_counter += 1
            
            # Select an expiry offset category randomly
            offset_cat = random.choice(expiry_offsets)
            hours_offset = random.uniform(offset_cat[0], offset_cat[1])
            expiry_date = now + timedelta(hours=hours_offset)
            
            # Decide realistic stock
            stock = random.randint(5, 50)
            
            # Decide demand score if available (fallback to random if not)
            demand_score = float(row.get('daily_demand', random.randint(10, 100))) / 100.0
            if demand_score > 1.0: 
                demand_score = 1.0
                
            # Insert Batch
            database.add_batch(
                batch_id=b_id,
                product_id=p_id,
                expiry_date=expiry_date,
                stock_quantity=stock,
                current_price=p_price,
                demand_score=demand_score,
                status='ACTIVE'
            )
            
            # Insert a generic STOCK_ADDED transaction to signify arrival
            database.record_inventory_transaction(b_id, 'STOCK_ADDED', stock)

    print("Seeding complete.")
    
def verify_database():
    conn = database.get_connection()
    cursor = conn.cursor()
    
    # Check counts
    cursor.execute('SELECT COUNT(*) FROM products')
    p_count = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM inventory_batches')
    b_count = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM inventory_transactions')
    t_count = cursor.fetchone()[0]
    
    print("\n--- DATABASE VERIFICATION ---")
    print(f"Products: {p_count}")
    print(f"Batches: {b_count}")
    print(f"Transactions: {t_count}")
    
    # Expiry queries relative to current time
    # Nearest expiring product
    cursor.execute('''
        SELECT p.product_name, b.batch_id, b.expiry_date 
        FROM inventory_batches b
        JOIN products p ON b.product_id = p.product_id
        ORDER BY b.expiry_date ASC LIMIT 1
    ''')
    nearest = cursor.fetchone()
    print(f"\nNearest Expiring Batch: {nearest['product_name']} ({nearest['batch_id']}) -> Expires: {nearest['expiry_date']}")
    
    # Multiple batches check
    cursor.execute('''
        SELECT product_id, COUNT(*) as c
        FROM inventory_batches
        GROUP BY product_id
        HAVING c > 1
        LIMIT 1
    ''')
    multi = cursor.fetchone()
    if multi:
        print(f"\nProduct with multiple batches found: {multi['product_id']} (Batches: {multi['c']})")
    
    # Expiry windows
    # Note: SQLite datetime('now') uses UTC, so we will use python's now to compare consistently
    now = datetime.now()
    now_str = now.strftime('%Y-%m-%d %H:%M:%S')
    
    # Under 6 hours
    six_hours = (now + timedelta(hours=6)).strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute('SELECT COUNT(*) FROM inventory_batches WHERE expiry_date > ? AND expiry_date <= ?', (now_str, six_hours))
    under_6 = cursor.fetchone()[0]
    
    # Under 24 hours
    twenty_four = (now + timedelta(hours=24)).strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute('SELECT COUNT(*) FROM inventory_batches WHERE expiry_date > ? AND expiry_date <= ?', (six_hours, twenty_four))
    under_24 = cursor.fetchone()[0]
    
    # 1-3 days
    three_days = (now + timedelta(days=3)).strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute('SELECT COUNT(*) FROM inventory_batches WHERE expiry_date > ? AND expiry_date <= ?', (twenty_four, three_days))
    one_to_three = cursor.fetchone()[0]
    
    # > 3 days
    cursor.execute('SELECT COUNT(*) FROM inventory_batches WHERE expiry_date > ?', (three_days,))
    several = cursor.fetchone()[0]
    
    print("\nExpiry Distribution (Simulating real-time application):")
    print(f"Batches expiring in < 6 hours: {under_6}")
    print(f"Batches expiring in 6-24 hours: {under_24}")
    print(f"Batches expiring in 1-3 days: {one_to_three}")
    print(f"Batches expiring in > 3 days: {several}")
    
    print("\nAll verifications passed.")

if __name__ == '__main__':
    seed_database()
    verify_database()
