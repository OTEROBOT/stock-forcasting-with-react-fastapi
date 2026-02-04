from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from database import init_db, get_db
from generate_mock_data import generate_sales_data, get_all_product_ids
import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import io
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.stattools import adfuller
import itertools
import warnings
warnings.filterwarnings('ignore')

app = FastAPI(title="Inventory Forecasting System")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ตอนส่งงาน/โปรเจกต์ให้ใช้ *
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database setup
DATABASE = "inventory.db"

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    
    # Products table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
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
    
    # Sales history table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sales_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER,
            sale_date DATE,
            quantity INTEGER,
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    """)
    
    # Transactions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
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
    conn.close()

# Pydantic models
class Product(BaseModel):
    code: str
    name: str
    category: Optional[str] = None
    unit: str = "ขวด"
    unit_cost: float
    ordering_cost: float = 500.0
    holding_cost_percentage: float = 0.2
    lead_time_days: int = 7
    current_stock: int = 0

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    unit: Optional[str] = None
    unit_cost: Optional[float] = None
    ordering_cost: Optional[float] = None
    holding_cost_percentage: Optional[float] = None
    lead_time_days: Optional[int] = None

class Transaction(BaseModel):
    product_id: int
    transaction_type: str  # 'in' or 'out'
    quantity: int
    note: Optional[str] = None

class SalesData(BaseModel):
    product_id: int
    sale_date: str
    quantity: int

# ARIMA Functions
def find_best_arima_params(data, max_p=3, max_d=2, max_q=3):
    """Find best ARIMA parameters using AIC"""
    best_aic = np.inf
    best_params = None
    
    # Check if data is stationary
    adf_result = adfuller(data)
    is_stationary = adf_result[1] < 0.05
    
    d_range = range(0, 1) if is_stationary else range(1, max_d + 1)
    
    for p, d, q in itertools.product(range(max_p + 1), d_range, range(max_q + 1)):
        if p == 0 and q == 0:
            continue
        try:
            model = ARIMA(data, order=(p, d, q))
            fitted_model = model.fit()
            if fitted_model.aic < best_aic:
                best_aic = fitted_model.aic
                best_params = (p, d, q)
        except:
            continue
    
    return best_params if best_params else (1, 1, 1)

def forecast_demand(sales_data, periods=30):
    """Forecast demand using ARIMA"""
    if len(sales_data) < 10:
        return None, None, None
    
    # Prepare data
    df = pd.DataFrame(sales_data)
    df['sale_date'] = pd.to_datetime(df['sale_date'])
    df = df.sort_values('sale_date')
    df.set_index('sale_date', inplace=True)
    
    # Resample to daily and fill missing dates
    daily_sales = df.resample('D')['quantity'].sum().fillna(0)
    
    # Find best parameters
    best_params = find_best_arima_params(daily_sales.values)
    
    # Fit model
    model = ARIMA(daily_sales, order=best_params)
    fitted_model = model.fit()
    
    # Forecast
    forecast_result = fitted_model.forecast(steps=periods)
    forecast_values = np.maximum(forecast_result, 0)  # No negative forecasts
    
    # Calculate confidence intervals
    forecast_obj = fitted_model.get_forecast(steps=periods)
    forecast_ci = forecast_obj.conf_int()
    
    return forecast_values.tolist(), forecast_ci.values.tolist(), best_params

def calculate_eoq(annual_demand, ordering_cost, holding_cost):
    """Calculate Economic Order Quantity"""
    if annual_demand <= 0 or holding_cost <= 0:
        return 0
    eoq = np.sqrt((2 * annual_demand * ordering_cost) / holding_cost)
    return round(eoq, 2)

def calculate_safety_stock(demand_std, lead_time_days, service_level=0.95):
    """Calculate Safety Stock using Z-score method"""
    from scipy import stats
    z_score = stats.norm.ppf(service_level)
    safety_stock = z_score * demand_std * np.sqrt(lead_time_days)
    return round(safety_stock, 2)

def calculate_rop(avg_daily_demand, lead_time_days, safety_stock):
    """Calculate Reorder Point"""
    lead_time_demand = avg_daily_demand * lead_time_days
    rop = lead_time_demand + safety_stock
    return round(rop, 2)

def get_all_product_ids(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM products")
    rows = cursor.fetchall()
    return [row[0] for row in rows]


# API Endpoints
# ==============================
# FastAPI Startup Event
# ==============================
from fastapi import FastAPI
from database import init_db, get_db
from generate_mock_data import (
    init_database,
    insert_products,
    generate_sales_data,
    generate_recent_transactions,
    get_all_product_ids
)
import os
import sqlite3
from init_db import init_db
from db import get_db
from generate_mock_data import get_all_product_ids, generate_sales_data

app = FastAPI()

DATABASE = "inventory.db"

from generate_mock_data import (
    init_database,
    get_all_product_ids,
    insert_products,
    generate_sales_data,
    generate_recent_transactions
)

@app.on_event("startup")
async def startup():
    # 1️⃣ สร้าง DB + TABLE ก่อนเสมอ
    conn = init_database()

    # 2️⃣ ค่อยดึง product_ids
    product_ids = get_all_product_ids(conn)

    # 3️⃣ ถ้ายังว่าง → seed mock data
    if len(product_ids) == 0:
        print("Generating mock data...")
        product_ids = insert_products(conn)
        generate_sales_data(conn, product_ids)
        generate_recent_transactions(conn, product_ids)

    conn.close()
    print("✅ Application startup complete")







@app.get("/")
async def root():
    return {"message": "Inventory Forecasting System API - Working!"}

# Products endpoints
@app.post("/products")
async def create_product(product: Product):
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO products (code, name, category, unit, unit_cost, 
                                ordering_cost, holding_cost_percentage, 
                                lead_time_days, current_stock)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (product.code, product.name, product.category, product.unit,
              product.unit_cost, product.ordering_cost, 
              product.holding_cost_percentage, product.lead_time_days,
              product.current_stock))
        conn.commit()
        product_id = cursor.lastrowid
        return {"id": product_id, "message": "Product created successfully"}
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Product code already exists")
    finally:
        conn.close()

@app.get("/products")
async def get_products(search: Optional[str] = None):
    conn = get_db()
    cursor = conn.cursor()
    
    if search:
        cursor.execute("""
            SELECT * FROM products 
            WHERE code LIKE ? OR name LIKE ? OR category LIKE ?
        """, (f"%{search}%", f"%{search}%", f"%{search}%"))
    else:
        cursor.execute("SELECT * FROM products")
    
    products = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return products

@app.get("/products/{product_id}")
async def get_product(product_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
    product = cursor.fetchone()
    conn.close()
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return dict(product)

@app.put("/products/{product_id}")
async def update_product(product_id: int, product: ProductUpdate):
    conn = get_db()
    cursor = conn.cursor()
    
    update_fields = []
    values = []
    
    if product.name is not None:
        update_fields.append("name = ?")
        values.append(product.name)
    if product.category is not None:
        update_fields.append("category = ?")
        values.append(product.category)
    if product.unit is not None:
        update_fields.append("unit = ?")
        values.append(product.unit)
    if product.unit_cost is not None:
        update_fields.append("unit_cost = ?")
        values.append(product.unit_cost)
    if product.ordering_cost is not None:
        update_fields.append("ordering_cost = ?")
        values.append(product.ordering_cost)
    if product.holding_cost_percentage is not None:
        update_fields.append("holding_cost_percentage = ?")
        values.append(product.holding_cost_percentage)
    if product.lead_time_days is not None:
        update_fields.append("lead_time_days = ?")
        values.append(product.lead_time_days)
    
    if not update_fields:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    values.append(product_id)
    query = f"UPDATE products SET {', '.join(update_fields)} WHERE id = ?"
    
    cursor.execute(query, values)
    conn.commit()
    conn.close()
    
    return {"message": "Product updated successfully"}

@app.delete("/products/{product_id}")
async def delete_product(product_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
    conn.commit()
    
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Product not found")
    
    conn.close()
    return {"message": "Product deleted successfully"}

# Transactions endpoints
@app.post("/transactions")
async def create_transaction(transaction: Transaction):
    conn = get_db()
    cursor = conn.cursor()
    
    # Check if product exists
    cursor.execute("SELECT current_stock FROM products WHERE id = ?", 
                  (transaction.product_id,))
    result = cursor.fetchone()
    
    if not result:
        conn.close()
        raise HTTPException(status_code=404, detail="Product not found")
    
    current_stock = result[0]
    
    # Calculate new stock
    if transaction.transaction_type == 'in':
        new_stock = current_stock + transaction.quantity
    elif transaction.transaction_type == 'out':
        if current_stock < transaction.quantity:
            conn.close()
            raise HTTPException(status_code=400, detail="Insufficient stock")
        new_stock = current_stock - transaction.quantity
    else:
        conn.close()
        raise HTTPException(status_code=400, detail="Invalid transaction type")
    
    # Insert transaction
    cursor.execute("""
        INSERT INTO transactions (product_id, transaction_type, quantity, note)
        VALUES (?, ?, ?, ?)
    """, (transaction.product_id, transaction.transaction_type, 
          transaction.quantity, transaction.note))
    
    # Update product stock
    cursor.execute("UPDATE products SET current_stock = ? WHERE id = ?",
                  (new_stock, transaction.product_id))
    
    conn.commit()
    conn.close()
    
    return {"message": "Transaction recorded successfully", "new_stock": new_stock}

@app.get("/transactions")
async def get_transactions(product_id: Optional[int] = None):
    conn = get_db()
    cursor = conn.cursor()
    
    if product_id:
        cursor.execute("""
            SELECT t.*, p.name as product_name, p.code as product_code
            FROM transactions t
            JOIN products p ON t.product_id = p.id
            WHERE t.product_id = ?
            ORDER BY t.transaction_date DESC
        """, (product_id,))
    else:
        cursor.execute("""
            SELECT t.*, p.name as product_name, p.code as product_code
            FROM transactions t
            JOIN products p ON t.product_id = p.id
            ORDER BY t.transaction_date DESC
        """)
    
    transactions = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return transactions

# Sales endpoints
@app.post("/sales/bulk")
async def create_bulk_sales(sales: List[SalesData]):
    conn = get_db()
    cursor = conn.cursor()
    
    for sale in sales:
        cursor.execute("""
            INSERT INTO sales_history (product_id, sale_date, quantity)
            VALUES (?, ?, ?)
        """, (sale.product_id, sale.sale_date, sale.quantity))
    
    conn.commit()
    conn.close()
    
    return {"message": f"{len(sales)} sales records created successfully"}

@app.post("/sales/upload")
async def upload_sales_csv(file: UploadFile = File(...)):
    """Upload sales data from CSV file
    Expected format: product_code, date, quantity
    """
    try:
        contents = await file.read()
        df = pd.read_csv(io.BytesIO(contents))
        
        # Validate columns
        required_cols = ['product_code', 'date', 'quantity']
        if not all(col in df.columns for col in required_cols):
            raise HTTPException(status_code=400, 
                              detail=f"CSV must contain columns: {required_cols}")
        
        conn = get_db()
        cursor = conn.cursor()
        
        inserted = 0
        for _, row in df.iterrows():
            # Get product_id from code
            cursor.execute("SELECT id FROM products WHERE code = ?", 
                          (row['product_code'],))
            result = cursor.fetchone()
            
            if result:
                product_id = result[0]
                cursor.execute("""
                    INSERT INTO sales_history (product_id, sale_date, quantity)
                    VALUES (?, ?, ?)
                """, (product_id, row['date'], int(row['quantity'])))
                inserted += 1
        
        conn.commit()
        conn.close()
        
        return {"message": f"Uploaded {inserted} sales records successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/sales/{product_id}")
async def get_sales_history(product_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM sales_history 
        WHERE product_id = ?
        ORDER BY sale_date
    """, (product_id,))
    
    sales = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return sales

# Forecasting endpoints
@app.get("/forecast/{product_id}")
async def get_forecast(product_id: int, periods: int = 30):
    conn = get_db()
    cursor = conn.cursor()
    
    # Get product info
    cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
    product = cursor.fetchone()
    
    if not product:
        conn.close()
        raise HTTPException(status_code=404, detail="Product not found")
    
    product = dict(product)
    
    # Get sales history
    cursor.execute("""
        SELECT sale_date, quantity FROM sales_history 
        WHERE product_id = ?
        ORDER BY sale_date
    """, (product_id,))
    
    sales_data = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    if len(sales_data) < 10:
        raise HTTPException(status_code=400, 
                          detail="Insufficient sales data for forecasting (minimum 10 records)")
    
    # Forecast
    forecast_values, forecast_ci, arima_params = forecast_demand(sales_data, periods)
    
    if forecast_values is None:
        raise HTTPException(status_code=500, detail="Forecasting failed")
    
    # Calculate statistics
    df = pd.DataFrame(sales_data)
    df['sale_date'] = pd.to_datetime(df['sale_date'])
    daily_sales = df.resample('D', on='sale_date')['quantity'].sum()
    
    avg_daily_demand = daily_sales.mean()
    demand_std = daily_sales.std()
    annual_demand = avg_daily_demand * 365
    
    # Calculate inventory metrics
    holding_cost = product['unit_cost'] * product['holding_cost_percentage']
    
    eoq = calculate_eoq(annual_demand, product['ordering_cost'], holding_cost)
    safety_stock = calculate_safety_stock(demand_std, product['lead_time_days'])
    rop = calculate_rop(avg_daily_demand, product['lead_time_days'], safety_stock)
    
    # Prepare forecast dates
    last_date = pd.to_datetime(sales_data[-1]['sale_date'])
    forecast_dates = [(last_date + timedelta(days=i+1)).strftime('%Y-%m-%d') 
                     for i in range(periods)]
    
    return {
        "product": product,
        "forecast": {
            "dates": forecast_dates,
            "values": forecast_values,
            "confidence_intervals": forecast_ci,
            "arima_params": {"p": arima_params[0], "d": arima_params[1], "q": arima_params[2]}
        },
        "metrics": {
            "avg_daily_demand": round(avg_daily_demand, 2),
            "demand_std": round(demand_std, 2),
            "annual_demand": round(annual_demand, 2),
            "eoq": eoq,
            "safety_stock": safety_stock,
            "reorder_point": rop,
            "current_stock": product['current_stock'],
            "stock_status": "ต้องสั่งซื้อ" if product['current_stock'] <= rop else "ปกติ"
        }
    }

# Dashboard endpoint
@app.get("/dashboard")
async def get_dashboard():
    conn = get_db()
    cursor = conn.cursor()
    
    # Total products
    cursor.execute("SELECT COUNT(*) as total FROM products")
    total_products = cursor.fetchone()[0]
    
    # Products needing reorder
    cursor.execute("""
        SELECT p.*, 
               (SELECT AVG(quantity) FROM sales_history WHERE product_id = p.id) as avg_sales
        FROM products p
    """)
    products = cursor.fetchall()
    
    low_stock_count = 0
    for product in products:
        product = dict(product)
        if product['avg_sales']:
            avg_daily = product['avg_sales'] / 30
            demand_std = product['avg_sales'] * 0.3  # Simplified
            safety_stock = calculate_safety_stock(demand_std, product['lead_time_days'])
            rop = calculate_rop(avg_daily, product['lead_time_days'], safety_stock)
            
            if product['current_stock'] <= rop:
                low_stock_count += 1
    
    # Total stock value
    cursor.execute("SELECT SUM(current_stock * unit_cost) as total_value FROM products")
    total_value = cursor.fetchone()[0] or 0
    
    # Recent transactions
    cursor.execute("""
        SELECT t.*, p.name as product_name 
        FROM transactions t
        JOIN products p ON t.product_id = p.id
        ORDER BY t.transaction_date DESC
        LIMIT 10
    """)
    recent_transactions = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    
    return {
        "total_products": total_products,
        "low_stock_count": low_stock_count,
        "total_stock_value": round(total_value, 2),
        "recent_transactions": recent_transactions
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)