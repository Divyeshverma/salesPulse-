
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA_FILE = ROOT / "data" / "sales.csv"

REQUIRED_COLUMNS = {
    "order_id",
    "date",
    "product",
    "category",
    "quantity",
    "unit_price",
    "unit_cost",
    "revenue",
    "profit",
}


def load_sales_data(file_path=DEFAULT_DATA_FILE) -> pd.DataFrame:
    """Load sales data and validate its required columns."""
    df = pd.read_csv(file_path)

    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(
            f"Missing required columns: {sorted(missing)}"
        )

    df["date"] = pd.to_datetime(df["date"], errors="coerce")

    numeric_columns = [
        "quantity",
        "unit_price",
        "unit_cost",
        "revenue",
        "profit",
    ]

    for column in numeric_columns:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    if df["date"].isna().any():
        raise ValueError("Some dates are missing or invalid.")

    if df[numeric_columns].isna().any().any():
        raise ValueError("Some numeric values are missing or invalid.")

    if df["order_id"].duplicated().any():
        raise ValueError("Duplicate order IDs found.")

    if (df["quantity"] <= 0).any():
        raise ValueError("Quantity must be positive.")

    # Recalculate financial fields instead of blindly trusting
    # the values stored in the input file.
    expected_revenue = df["quantity"] * df["unit_price"]
    expected_profit = df["quantity"] * (
        df["unit_price"] - df["unit_cost"]
    )

    if not (
        (df["revenue"] - expected_revenue).abs() < 0.01
    ).all():
        raise ValueError("Revenue calculation mismatch.")

    if not (
        (df["profit"] - expected_profit).abs() < 0.01
    ).all():
        raise ValueError("Profit calculation mismatch.")

    return df.sort_values("date").reset_index(drop=True)


def get_kpis(df: pd.DataFrame) -> dict:
    """Calculate headline business metrics."""
    total_revenue = float(df["revenue"].sum())
    total_profit = float(df["profit"].sum())
    total_orders = int(df["order_id"].nunique())
    units_sold = int(df["quantity"].sum())

    average_order_value = (
        total_revenue / total_orders if total_orders else 0.0
    )

    profit_margin = (
        total_profit / total_revenue * 100
        if total_revenue else 0.0
    )

    return {
        "total_revenue": total_revenue,
        "total_profit": total_profit,
        "total_orders": total_orders,
        "units_sold": units_sold,
        "average_order_value": average_order_value,
        "profit_margin_pct": profit_margin,
    }


def get_monthly_sales(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate revenue and profit by calendar month."""
    result = (
        df.assign(month=df["date"].dt.to_period("M").dt.to_timestamp())
        .groupby("month", as_index=False)
        .agg(
            revenue=("revenue", "sum"),
            profit=("profit", "sum"),
            orders=("order_id", "nunique"),
        )
        .sort_values("month")
        .reset_index(drop=True)
    )

    return result


def get_top_products(
    df: pd.DataFrame, limit: int = 5
) -> pd.DataFrame:
    """Rank products by revenue."""
    if limit < 1:
        raise ValueError("limit must be at least 1.")

    return (
        df.groupby("product", as_index=False)
        .agg(
            revenue=("revenue", "sum"),
            profit=("profit", "sum"),
            units_sold=("quantity", "sum"),
        )
        .sort_values(
            ["revenue", "product"],
            ascending=[False, True],
        )
        .head(limit)
        .reset_index(drop=True)
    )


def get_category_performance(df: pd.DataFrame) -> pd.DataFrame:
    """Summarise revenue and profit by category."""
    result = (
        df.groupby("category", as_index=False)
        .agg(
            revenue=("revenue", "sum"),
            profit=("profit", "sum"),
            units_sold=("quantity", "sum"),
            orders=("order_id", "nunique"),
        )
        .sort_values("revenue", ascending=False)
        .reset_index(drop=True)
    )

    result["profit_margin_pct"] = (
        result["profit"]
        .div(result["revenue"].where(result["revenue"] != 0))
        .mul(100)
        .fillna(0)
    )

    return result


def filter_sales(
    df: pd.DataFrame,
    start_date=None,
    end_date=None,
    category=None,
) -> pd.DataFrame:
    """Filter rows using inclusive calendar dates and category."""
    result = df.copy()

    if start_date is not None:
        start = pd.Timestamp(start_date).normalize()
        result = result[result["date"] >= start]

    if end_date is not None:
        end = pd.Timestamp(end_date).normalize()
        result = result[result["date"] < end + pd.Timedelta(days=1)]

    if category is not None:
        result = result[result["category"] == category]

    return result.reset_index(drop=True)
