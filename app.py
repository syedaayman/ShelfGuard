from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import argparse
import sqlite3
import os
import database
from pricing_model import predict_discount

app = FastAPI(title="SmartShelf AI Backend")

# Allow CORS for development if needed, though we are serving static files directly
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- API Endpoints ---

from typing import Any

def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

def query_db(query, args=(), one=False) -> Any:
    conn = sqlite3.connect(database.DB_PATH)
    conn.row_factory = dict_factory
    cur = conn.cursor()
    cur.execute(query, args)
    rv = cur.fetchall()
    conn.close()
    return (rv[0] if rv else None) if one else rv


# --- Single source of truth for expiry status ---
# This is intentionally separate from the DB "status" column, which we reserve
# for the donation lifecycle (ACTIVE / DONATION_REVIEW / DONATED / DECLINED).
# Expiry status is always derived live from expiry_date, never stored.

def calculate_product_status(expiry_date_str: str, db_status: str) -> str:
    """
    Returns one of: EXPIRED, CRITICAL, WARNING, SAFE
    based on time remaining until expiry_date.
    """
    try:
        # SQLite DATETIME columns are typically 'YYYY-MM-DD HH:MM:SS'
        expiry = datetime.fromisoformat(expiry_date_str)
    except (ValueError, TypeError):
        # Fallback in case of unexpected formatting
        return "UNKNOWN"

    now = datetime.now()
    remaining = (expiry - now).total_seconds()

    if remaining <= 0:
        return "EXPIRED"
    elif remaining <= 6 * 3600 or db_status == "DONATION_REVIEW":
        return "CRITICAL"
    elif remaining <= 7 * 24 * 3600:
        return "WARNING"
    else:
        return "SAFE"


def attach_expiry_status(rows: list) -> list:
    """Computes and overwrites the 'status' field for each row dict, in place."""
    for row in rows:
        row["status"] = calculate_product_status(row["expiry_date"], row.get("status", ""))
    return rows


class DiscountRequest(BaseModel):
    days_to_expiry: float = Field(ge=0)
    stock_level: float = Field(ge=0)
    remaining_shelf_life_pct: float = Field(ge=0, le=100)
    supplier_score: float = Field(ge=6, le=10)
    is_promoted: int = Field(ge=0, le=1)


@app.post("/api/predict-discount")
async def predict_product_discount(request: DiscountRequest):
    try:
        discount_fraction = predict_discount(
            days_to_expiry=request.days_to_expiry,
            stock_level=request.stock_level,
            remaining_shelf_life_pct=request.remaining_shelf_life_pct,
            supplier_score=request.supplier_score,
            is_promoted=request.is_promoted,
        )
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error

    return {
        "discount_fraction": discount_fraction,
        "discount_percent": discount_fraction * 100,
    }


@app.get("/api/stats")
async def get_stats():
    total_products = query_db("SELECT COUNT(*) as count FROM products", one=True)['count']
    total_stock = query_db("SELECT SUM(stock_quantity) as total FROM inventory_batches", one=True)['total'] or 0

    # Fetch all batches to compute stats using single source of truth
    rows = query_db("SELECT expiry_date, status FROM inventory_batches WHERE stock_quantity > 0")
    rows_with_status = attach_expiry_status(rows)

    expired = sum(1 for r in rows_with_status if r["status"] == "EXPIRED")
    near_expiry = sum(1 for r in rows_with_status if r["status"] in ("WARNING", "CRITICAL"))
    critical = sum(1 for r in rows_with_status if r["status"] == "CRITICAL")

    return {
        "total_products": total_products,
        "total_stock": total_stock,
        "expired": expired,
        "near_expiry": near_expiry,
        "critical": critical
    }


@app.get("/api/inventory")
async def get_inventory():
    query = """
        SELECT b.batch_id, p.product_name, p.category, b.stock_quantity, b.expiry_date,
               b.current_price, b.current_discount, b.status, b.demand_score
        FROM inventory_batches b
        JOIN products p ON b.product_id = p.product_id
        WHERE b.stock_quantity > 0
        ORDER BY b.expiry_date ASC
    """
    rows = query_db(query)
    return attach_expiry_status(rows)


@app.get("/api/near-expiry")
async def get_near_expiry():
    # Fetch all, then filter using the single source of truth
    query = """
        SELECT b.batch_id, p.product_name, p.category, b.stock_quantity, b.expiry_date,
               b.current_price, b.current_discount, b.status, b.demand_score
        FROM inventory_batches b
        JOIN products p ON b.product_id = p.product_id
        WHERE b.stock_quantity > 0 
        ORDER BY b.expiry_date ASC
    """
    rows = query_db(query)
    rows_with_status = attach_expiry_status(rows)
    return [r for r in rows_with_status if r["status"] in ("WARNING", "CRITICAL")]


@app.get("/api/donations")
async def get_donations():
    # Fetch all, then filter using the single source of truth
    query = """
        SELECT b.batch_id, p.product_name, p.category, b.stock_quantity, b.expiry_date, 
               b.current_price, b.current_discount, b.status, b.demand_score
        FROM inventory_batches b
        JOIN products p ON b.product_id = p.product_id
        WHERE b.stock_quantity > 0
        ORDER BY b.expiry_date ASC
    """
    rows = query_db(query)
    rows_with_status = attach_expiry_status(rows)
    return [r for r in rows_with_status if r["status"] == "CRITICAL"]

@app.get("/api/expired")
async def get_expired():
    # Fetch all, then filter using the single source of truth
    query = """
        SELECT b.batch_id, p.product_name, p.category, b.stock_quantity, b.expiry_date,
               b.current_price, b.current_discount, b.status, b.demand_score
        FROM inventory_batches b
        JOIN products p ON b.product_id = p.product_id
        WHERE b.stock_quantity > 0 
        ORDER BY b.expiry_date DESC
    """
    rows = query_db(query)
    rows_with_status = attach_expiry_status(rows)
    return [r for r in rows_with_status if r["status"] == "EXPIRED"]

# --- Serve Frontend ---
frontend_path = os.path.join(os.path.dirname(__file__), "frontend")
os.makedirs(frontend_path, exist_ok=True)
app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")
def main():
    parser = argparse.ArgumentParser(
        description="Predict a discount for a perishable product."
    )
    parser.add_argument("--days-to-expiry", type=float, required=True)
    parser.add_argument("--stock-level", type=float, required=True)
    parser.add_argument("--remaining-shelf-life", type=float, required=True)
    parser.add_argument("--supplier-score", type=float, required=True)
    parser.add_argument("--promoted", type=int, choices=(0, 1), required=True)
    args = parser.parse_args()

    discount_fraction = predict_discount(
        days_to_expiry=args.days_to_expiry,
        stock_level=args.stock_level,
        remaining_shelf_life_pct=args.remaining_shelf_life,
        supplier_score=args.supplier_score,
        is_promoted=args.promoted,
    )

    print(f"Recommended discount: {discount_fraction * 100:.2f}%")


if __name__ == "__main__":
	main()
