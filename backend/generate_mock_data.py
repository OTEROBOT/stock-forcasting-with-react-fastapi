import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
from db import get_db

def get_all_product_ids(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM products")
    return [row[0] for row in cursor.fetchall()]

# Initialize database
DATABASE = "inventory.db"

def get_all_product_ids(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM products")
    return [row[0] for row in cursor.fetchall()]


def init_database():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # Drop existing tables
    cursor.execute("DROP TABLE IF EXISTS transactions")
    cursor.execute("DROP TABLE IF EXISTS sales_history")
    cursor.execute("DROP TABLE IF EXISTS products")
    
    # Create tables
    cursor.execute("""
        CREATE TABLE products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            category TEXT,
            unit TEXT,
            unit_cost REAL,
            ordering_cost REAL,
            holding_cost_percentage REAL,
            lead_time_days INTEGER,
            current_stock INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE TABLE sales_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER,
            sale_date DATE,
            quantity INTEGER,
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER,
            transaction_type TEXT,
            quantity INTEGER,
            transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            note TEXT,
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    """)
    
    conn.commit()
    return conn

def generate_seasonal_pattern(base_demand, num_days, trend=0.0, seasonality_strength=0.3):
    """Generate sales with trend and seasonality"""
    days = np.arange(num_days)
    
    # Trend component
    trend_component = base_demand + (trend * days / 365)
    
    # Seasonal component (yearly cycle)
    seasonal_component = seasonality_strength * base_demand * np.sin(2 * np.pi * days / 365)
    
    # Weekly pattern (weekends vs weekdays)
    weekly_pattern = np.array([1.2 if i % 7 in [5, 6] else 1.0 for i in range(num_days)])
    
    # Random noise
    noise = np.random.normal(0, base_demand * 0.15, num_days)
    
    # Combine components
    sales = (trend_component + seasonal_component) * weekly_pattern + noise
    sales = np.maximum(sales, 0)  # No negative sales
    
    return np.round(sales).astype(int)

def insert_products(conn):
    """Insert alcohol products"""
    products = [
        # Whiskey
        {
            'code': 'WHI001',
            'name': 'Johnnie Walker Black Label 750ml',
            'category': 'Whiskey',
            'unit': 'ขวด',
            'unit_cost': 1200.0,
            'ordering_cost': 800.0,
            'holding_cost_percentage': 0.20,
            'lead_time_days': 14,
            'base_demand': 25,
            'trend': 2.0,
            'seasonality': 0.4
        },
        {
            'code': 'WHI002',
            'name': 'Chivas Regal 12 Years 700ml',
            'category': 'Whiskey',
            'unit': 'ขวด',
            'unit_cost': 1500.0,
            'ordering_cost': 800.0,
            'holding_cost_percentage': 0.20,
            'lead_time_days': 14,
            'base_demand': 18,
            'trend': 1.0,
            'seasonality': 0.3
        },
        {
            'code': 'WHI003',
            'name': 'Jack Daniels 750ml',
            'category': 'Whiskey',
            'unit': 'ขวด',
            'unit_cost': 1100.0,
            'ordering_cost': 800.0,
            'holding_cost_percentage': 0.20,
            'lead_time_days': 10,
            'base_demand': 30,
            'trend': 3.0,
            'seasonality': 0.35
        },
        # Vodka
        {
            'code': 'VOD001',
            'name': 'Absolut Vodka 750ml',
            'category': 'Vodka',
            'unit': 'ขวด',
            'unit_cost': 800.0,
            'ordering_cost': 600.0,
            'holding_cost_percentage': 0.18,
            'lead_time_days': 10,
            'base_demand': 35,
            'trend': 1.5,
            'seasonality': 0.25
        },
        {
            'code': 'VOD002',
            'name': 'Smirnoff Red 750ml',
            'category': 'Vodka',
            'unit': 'ขวด',
            'unit_cost': 600.0,
            'ordering_cost': 500.0,
            'holding_cost_percentage': 0.18,
            'lead_time_days': 7,
            'base_demand': 45,
            'trend': 2.0,
            'seasonality': 0.2
        },
        # Rum
        {
            'code': 'RUM001',
            'name': 'Bacardi Superior 750ml',
            'category': 'Rum',
            'unit': 'ขวด',
            'unit_cost': 700.0,
            'ordering_cost': 600.0,
            'holding_cost_percentage': 0.18,
            'lead_time_days': 10,
            'base_demand': 28,
            'trend': 1.0,
            'seasonality': 0.4
        },
        {
            'code': 'RUM002',
            'name': 'Captain Morgan Spiced 750ml',
            'category': 'Rum',
            'unit': 'ขวด',
            'unit_cost': 750.0,
            'ordering_cost': 600.0,
            'holding_cost_percentage': 0.18,
            'lead_time_days': 12,
            'base_demand': 22,
            'trend': 0.5,
            'seasonality': 0.3
        },
        # Beer
        {
            'code': 'BEE001',
            'name': 'Heineken 330ml (ลัง 24 ขวด)',
            'category': 'Beer',
            'unit': 'ลัง',
            'unit_cost': 450.0,
            'ordering_cost': 400.0,
            'holding_cost_percentage': 0.15,
            'lead_time_days': 5,
            'base_demand': 80,
            'trend': 5.0,
            'seasonality': 0.5
        },
        {
            'code': 'BEE002',
            'name': 'Singha 330ml (ลัง 24 ขวด)',
            'category': 'Beer',
            'unit': 'ลัง',
            'unit_cost': 400.0,
            'ordering_cost': 400.0,
            'holding_cost_percentage': 0.15,
            'lead_time_days': 3,
            'base_demand': 100,
            'trend': 8.0,
            'seasonality': 0.45
        },
        {
            'code': 'BEE003',
            'name': 'Chang 320ml (ลัง 24 ขวด)',
            'category': 'Beer',
            'unit': 'ลัง',
            'unit_cost': 380.0,
            'ordering_cost': 400.0,
            'holding_cost_percentage': 0.15,
            'lead_time_days': 3,
            'base_demand': 90,
            'trend': 6.0,
            'seasonality': 0.4
        },
        # Wine
        {
            'code': 'WIN001',
            'name': 'Yellow Tail Shiraz 750ml',
            'category': 'Wine',
            'unit': 'ขวด',
            'unit_cost': 350.0,
            'ordering_cost': 500.0,
            'holding_cost_percentage': 0.20,
            'lead_time_days': 15,
            'base_demand': 15,
            'trend': 1.5,
            'seasonality': 0.35
        },
        {
            'code': 'WIN002',
            'name': 'Casillero del Diablo Cabernet 750ml',
            'category': 'Wine',
            'unit': 'ขวด',
            'unit_cost': 500.0,
            'ordering_cost': 500.0,
            'holding_cost_percentage': 0.20,
            'lead_time_days': 15,
            'base_demand': 12,
            'trend': 0.8,
            'seasonality': 0.3
        },
        # Liqueur
        {
            'code': 'LIQ001',
            'name': 'Baileys Irish Cream 750ml',
            'category': 'Liqueur',
            'unit': 'ขวด',
            'unit_cost': 900.0,
            'ordering_cost': 600.0,
            'holding_cost_percentage': 0.20,
            'lead_time_days': 12,
            'base_demand': 20,
            'trend': 1.0,
            'seasonality': 0.5
        },
        {
            'code': 'LIQ002',
            'name': 'Jägermeister 700ml',
            'category': 'Liqueur',
            'unit': 'ขวด',
            'unit_cost': 950.0,
            'ordering_cost': 600.0,
            'holding_cost_percentage': 0.20,
            'lead_time_days': 12,
            'base_demand': 16,
            'trend': 0.5,
            'seasonality': 0.3
        },
        # Gin
        {
            'code': 'GIN001',
            'name': 'Bombay Sapphire 750ml',
            'category': 'Gin',
            'unit': 'ขวด',
            'unit_cost': 1000.0,
            'ordering_cost': 700.0,
            'holding_cost_percentage': 0.20,
            'lead_time_days': 12,
            'base_demand': 18,
            'trend': 2.0,
            'seasonality': 0.25
        }
    ]
    
    cursor = conn.cursor()
    product_ids = []
    
    for product in products:
        cursor.execute("""
            INSERT INTO products (code, name, category, unit, unit_cost, 
                                ordering_cost, holding_cost_percentage, 
                                lead_time_days, current_stock)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            product['code'], product['name'], product['category'], 
            product['unit'], product['unit_cost'], product['ordering_cost'],
            product['holding_cost_percentage'], product['lead_time_days'],
            random.randint(50, 200)  # Random initial stock
        ))
        product_ids.append((cursor.lastrowid, product))
    
    conn.commit()
    return product_ids

def generate_sales_data(conn, product_ids, months=36):
    """Generate 36 months of sales data"""
    cursor = conn.cursor()
    
    # Calculate date range
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=months * 30)
    num_days = (end_date - start_date).days
    
    for product_id, product_info in product_ids:
        # Generate sales pattern
        sales = generate_seasonal_pattern(
            base_demand=product_info['base_demand'],
            num_days=num_days,
            trend=product_info['trend'],
            seasonality_strength=product_info['seasonality']
        )
        
        # Insert daily sales
        current_date = start_date
        for i in range(num_days):
            if sales[i] > 0:  # Only insert non-zero sales
                cursor.execute("""
                    INSERT INTO sales_history (product_id, sale_date, quantity)
                    VALUES (?, ?, ?)
                """, (product_id, current_date.strftime('%Y-%m-%d'), int(sales[i])))
            
            current_date += timedelta(days=1)
    
    conn.commit()
    print(f"Generated {num_days} days of sales data for {len(product_ids)} products")

def generate_recent_transactions(conn, product_ids):
    """Generate some recent transactions"""
    cursor = conn.cursor()
    
    transaction_types = ['in', 'out']
    notes = [
        'รับเข้าจากผู้จัดจำหน่าย',
        'จ่ายออกตามคำสั่งซื้อ',
        'ตรวจนับสต๊อก - ปรับปรุง',
        'รับคืนจากลูกค้า',
        'จ่ายให้สาขา'
    ]
    
    # Generate 50 random transactions in the last 30 days
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    for _ in range(50):
        product_id, _ = random.choice(product_ids)
        trans_type = random.choice(transaction_types)
        quantity = random.randint(10, 100)
        trans_date = start_date + timedelta(
            days=random.randint(0, 30),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59)
        )
        note = random.choice(notes)
        
        cursor.execute("""
            INSERT INTO transactions 
            (product_id, transaction_type, quantity, transaction_date, note)
            VALUES (?, ?, ?, ?, ?)
        """, (product_id, trans_type, quantity, trans_date.strftime('%Y-%m-%d %H:%M:%S'), note))
    
    conn.commit()
    print("Generated 50 recent transactions")

def main():
    print("Initializing database...")
    conn = init_database()
    
    print("Inserting products...")
    product_ids = insert_products(conn)
    print(f"Inserted {len(product_ids)} products")
    
    print("Generating 36 months of sales data...")
    generate_sales_data(conn, product_ids, months=36)
    
    print("Generating recent transactions...")
    generate_recent_transactions(conn, product_ids)
    
    conn.close()
    print("\n✅ Mock data generation completed successfully!")
    print(f"Database file: {DATABASE}")
    
    # Display summary
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM products")
    product_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM sales_history")
    sales_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM transactions")
    trans_count = cursor.fetchone()[0]
    
    print(f"\nSummary:")
    print(f"  Products: {product_count}")
    print(f"  Sales records: {sales_count}")
    print(f"  Transactions: {trans_count}")
    
    conn.close()
    
    

if __name__ == "__main__":
    main()
    
    