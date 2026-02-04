# ===============================
# Inventory Forecasting System
# main.py (FULL VERSION – FIXED)
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
from scipy import stats

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

    cur.execute("""
    CREATE TABLE IF NOT EXISTS sales_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER,
        sale_date DATE,
        quantity INTEGER,
        FOREIGN KEY (product_id) REFERENCES products(id)
    )
    """)

    cur.execute("""
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

# ===============================
# Models
# ===============================
class Product(BaseModel):
    code: str
    name: str
    category: Optional[str] = None
    unit: str = "ขวด"
    unit_cost: float
    ordering_cost: float = 500
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
    transaction_type: str  # in / out
    quantity: int
    note: Optional[str] = None


class SalesData(BaseModel):
    product_id: int
    sale_date: str
    quantity: int

# ===============================
# ARIMA + Inventory Logic
# ===============================
def find_best_arima_params(data, max_p=3, max_d=2, max_q=3):
    best_aic = np.inf
    best_params = (1, 1, 1)

    try:
        p_value = adfuller(data)[1]
        d_range = range(0, 1) if p_value < 0.05 else range(1, max_d + 1)
    except:
        d_range = range(1, 2)

    for p, d, q in itertools.product(range(max_p + 1), d_range, range(max_q + 1)):
        if p == 0 and q == 0:
            continue
        try:
            model = ARIMA(data, order=(p, d, q))
            result = model.fit()
            if result.aic < best_aic:
                best_aic = result.aic
                best_params = (p, d, q)
        except:
            continue

    return best_params


def forecast_demand(sales_data, periods=30):
    df = pd.DataFrame(sales_data)
    df["sale_date"] = pd.to_datetime(df["sale_date"])
    df.set_index("sale_date", inplace=True)

    daily_sales = df.resample("D")["quantity"].sum().fillna(0)

    order = find_best_arima_params(daily_sales.values)
    model = ARIMA(daily_sales, order=order)
    fit = model.fit()

    forecast = np.maximum(fit.forecast(periods), 0)
    ci = fit.get_forecast(periods).conf_int()

    return forecast.tolist(), ci.values.tolist(), order


def calculate_eoq(annual_demand, ordering_cost, holding_cost):
    if annual_demand <= 0 or holding_cost <= 0:
        return 0
    return round(np.sqrt((2 * annual_demand * ordering_cost) / holding_cost), 2)


def calculate_safety_stock(demand_std, lead_time_days, service_level=0.95):
    z = stats.norm.ppf(service_level)
    return round(z * demand_std * np.sqrt(lead_time_days), 2)


def calculate_rop(avg_daily_demand, lead_time_days, safety_stock):
    return round(avg_daily_demand * lead_time_days + safety_stock, 2)

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
    return {"message": "Inventory Forecasting API working"}

# ---------- Products ----------
@app.post("/api/products")
def create_product(p: Product):
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("""
        INSERT INTO products
        (code,name,category,unit,unit_cost,ordering_cost,
         holding_cost_percentage,lead_time_days,current_stock)
        VALUES (?,?,?,?,?,?,?,?,?)
        """, (
            p.code, p.name, p.category, p.unit,
            p.unit_cost, p.ordering_cost,
            p.holding_cost_percentage, p.lead_time_days,
            p.current_stock
        ))
        conn.commit()
    except sqlite3.IntegrityError:
        raise HTTPException(400, "Product code already exists")
    finally:
        conn.close()
    return {"message": "Product created"}

@app.get("/api/products")
def get_products():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM products")
    data = [dict(r) for r in cur.fetchall()]
    conn.close()
    return data

# ---------- Transactions ----------
@app.post("/api/transactions")
def create_transaction(t: Transaction):
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
    INSERT INTO transactions (product_id,transaction_type,quantity,note)
    VALUES (?,?,?,?)
    """, (t.product_id, t.transaction_type, t.quantity, t.note))

    cur.execute("UPDATE products SET current_stock=? WHERE id=?",
                (new_stock, t.product_id))

    conn.commit()
    conn.close()
    return {"new_stock": new_stock}

# ---------- Forecast ----------
@app.get("/api/forecast/{product_id}")
def forecast(product_id: int):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM products WHERE id=?", (product_id,))
    product = cur.fetchone()
    if not product:
        raise HTTPException(404, "Product not found")

    cur.execute("""
    SELECT sale_date,quantity FROM sales_history
    WHERE product_id=? ORDER BY sale_date
    """, (product_id,))
    sales = [dict(r) for r in cur.fetchall()]
    conn.close()

    if len(sales) < 10:
        raise HTTPException(400, "Insufficient sales data")

    forecast_values, ci, order = forecast_demand(sales)

    return {
        "arima": {"p": order[0], "d": order[1], "q": order[2]},
        "forecast": forecast_values,
        "confidence_intervals": ci
    }

# ===============================
# Run local
# ===============================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
