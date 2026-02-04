# ===============================
# Inventory Forecasting System
# main.py (FULL VERSION)
# ===============================

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import io
import itertools
import warnings
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.stattools import adfuller

warnings.filterwarnings("ignore")

# ===============================
# App Init
# ===============================
app = FastAPI(title="Inventory Forecasting System")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DATABASE = "inventory.db"

# ===============================
# Database
# ===============================
def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT UNIQUE,
        name TEXT,
        category TEXT,
        unit TEXT,
        unit_cost REAL,
        ordering_cost REAL,
        holding_cost_percentage REAL,
        lead_time_days INTEGER,
        current_stock INTEGER DEFAULT 0
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS sales_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER,
        sale_date DATE,
        quantity INTEGER
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER,
        transaction_type TEXT,
        quantity INTEGER,
        transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        note TEXT
    )
    """)

    conn.commit()
    conn.close()

# ===============================
# Models
# ===============================
class Product(BaseModel):
    code: str
    name: str
    category: Optional[str] = None
    unit: str = "ชิ้น"
    unit_cost: float
    ordering_cost: float = 500
    holding_cost_percentage: float = 0.2
    lead_time_days: int = 7
    current_stock: int = 0

class ProductUpdate(BaseModel):
    name: Optional[str]
    category: Optional[str]
    unit: Optional[str]
    unit_cost: Optional[float]
    ordering_cost: Optional[float]
    holding_cost_percentage: Optional[float]
    lead_time_days: Optional[int]

class Transaction(BaseModel):
    product_id: int
    transaction_type: str
    quantity: int
    note: Optional[str] = None

class SalesData(BaseModel):
    product_id: int
    sale_date: str
    quantity: int

# ===============================
# ARIMA
# ===============================
def find_best_arima(data):
    best_aic = np.inf
    best_order = (1,1,1)

    for p, d, q in itertools.product(range(3), range(2), range(3)):
        try:
            model = ARIMA(data, order=(p,d,q))
            result = model.fit()
            if result.aic < best_aic:
                best_aic = result.aic
                best_order = (p,d,q)
        except:
            continue
    return best_order

def forecast_demand(sales, days=30):
    df = pd.DataFrame(sales)
    df["sale_date"] = pd.to_datetime(df["sale_date"])
    df.set_index("sale_date", inplace=True)

    daily = df.resample("D")["quantity"].sum().fillna(0)

    order = find_best_arima(daily.values)
    model = ARIMA(daily, order=order)
    fit = model.fit()

    forecast = fit.forecast(days)
    return forecast.tolist(), order

# ===============================
# Startup
# ===============================
@app.on_event("startup")
def startup():
    init_db()
    print("✅ Backend ready")

# ===============================
# Routes
# ===============================
@app.get("/")
def root():
    return {"status": "Inventory Forecasting API working"}

@app.post("/products")
def add_product(p: Product):
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("""
        INSERT INTO products VALUES (NULL,?,?,?,?,?,?,?,?,?)
        """, (
            p.code, p.name, p.category, p.unit,
            p.unit_cost, p.ordering_cost,
            p.holding_cost_percentage, p.lead_time_days,
            p.current_stock
        ))
        conn.commit()
    except:
        raise HTTPException(400, "Duplicate product code")
    finally:
        conn.close()
    return {"message": "Product added"}

@app.get("/products")
def get_products():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM products")
    data = [dict(r) for r in cur.fetchall()]
    conn.close()
    return data

@app.post("/transactions")
def add_transaction(t: Transaction):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT current_stock FROM products WHERE id=?", (t.product_id,))
    row = cur.fetchone()
    if not row:
        raise HTTPException(404, "Product not found")

    stock = row["current_stock"]
    new_stock = stock + t.quantity if t.transaction_type == "in" else stock - t.quantity

    if new_stock < 0:
        raise HTTPException(400, "Insufficient stock")

    cur.execute("""
    INSERT INTO transactions (product_id, transaction_type, quantity, note)
    VALUES (?,?,?,?)
    """, (t.product_id, t.transaction_type, t.quantity, t.note))

    cur.execute("UPDATE products SET current_stock=? WHERE id=?",
                (new_stock, t.product_id))

    conn.commit()
    conn.close()
    return {"new_stock": new_stock}

@app.post("/sales/bulk")
def bulk_sales(data: List[SalesData]):
    conn = get_db()
    cur = conn.cursor()
    for s in data:
        cur.execute("""
        INSERT INTO sales_history (product_id, sale_date, quantity)
        VALUES (?,?,?)
        """, (s.product_id, s.sale_date, s.quantity))
    conn.commit()
    conn.close()
    return {"inserted": len(data)}

@app.get("/forecast/{product_id}")
def forecast(product_id: int):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    SELECT sale_date, quantity FROM sales_history
    WHERE product_id=?
    """, (product_id,))
    sales = [dict(r) for r in cur.fetchall()]
    conn.close()

    if len(sales) < 10:
        raise HTTPException(400, "Not enough data")

    forecast, order = forecast_demand(sales)

    return {
        "arima": {"p": order[0], "d": order[1], "q": order[2]},
        "forecast_30_days": forecast
    }

# ===============================
# Run
# ===============================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
