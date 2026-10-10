
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
OUTPUT_FILE = DATA_DIR / "sales.csv"


def generate_sales_data(rows: int = 1000) -> pd.DataFrame:
    rng = np.random.default_rng(42)

    products = {
        "Laptop": {"price": 55000, "cost": 46000},
        "Mouse": {"price": 700, "cost": 350},
        "Keyboard": {"price": 1500, "cost": 800},
        "Monitor": {"price": 12000, "cost": 9500},
        "Headphones": {"price": 2200, "cost": 1400},
        "Webcam": {"price": 1800, "cost": 1100},
    }

    product_names = list(products.keys())
    weights = [0.12, 0.25, 0.18, 0.12, 0.20, 0.13]
    selected = rng.choice(product_names, size=rows, p=weights)

    dates = pd.to_datetime(
        rng.integers(
            pd.Timestamp("2025-01-01").value // 10**9,
            pd.Timestamp("2026-10-01").value // 10**9,
            size=rows,
        ),
        unit="s",
    ).normalize()

    quantities = rng.integers(1, 6, size=rows)

    df = pd.DataFrame({
        "order_id": [f"ORD-{i:05d}" for i in range(1, rows + 1)],
        "date": dates,
        "product": selected,
        "category": [
            "Computers" if p in ["Laptop", "Monitor"]
            else "Accessories"
            for p in selected
        ],
        "quantity": quantities,
        "unit_price": [
            products[p]["price"] for p in selected
        ],
        "unit_cost": [
            products[p]["cost"] for p in selected
        ],
    })

    df["revenue"] = df["quantity"] * df["unit_price"]
    df["profit"] = (
        df["quantity"] * (df["unit_price"] - df["unit_cost"])
    )

    return df.sort_values("date").reset_index(drop=True)


if __name__ == "__main__":
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    sales = generate_sales_data()
    sales.to_csv(OUTPUT_FILE, index=False)

    print(f"Dataset saved: {OUTPUT_FILE}")
    print(f"Rows: {len(sales)}")
    print(f"Columns: {', '.join(sales.columns)}")
    print(f"Total revenue: ₹{sales['revenue'].sum():,.0f}")
