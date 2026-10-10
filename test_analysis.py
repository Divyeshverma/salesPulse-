
from pandas.testing import assert_frame_equal

from src.analysis import (
    filter_sales,
    get_category_performance,
    get_kpis,
    get_monthly_sales,
    get_top_products,
    load_sales_data,
)


def main():
    df = load_sales_data()

    assert len(df) == 1000
    assert df["order_id"].nunique() == 1000
    assert df["date"].notna().all()

    # Verify the source financial calculations.
    assert (
        df["revenue"] == df["quantity"] * df["unit_price"]
    ).all()

    assert (
        df["profit"]
        == df["quantity"] * (df["unit_price"] - df["unit_cost"])
    ).all()

    kpis = get_kpis(df)

    assert kpis["total_revenue"] == df["revenue"].sum()
    assert kpis["total_profit"] == df["profit"].sum()
    assert kpis["total_orders"] == 1000
    assert kpis["units_sold"] == df["quantity"].sum()

    monthly = get_monthly_sales(df)
    assert monthly["month"].is_monotonic_increasing
    assert abs(monthly["revenue"].sum() - kpis["total_revenue"]) < 0.01

    top_products = get_top_products(df, limit=5)
    assert len(top_products) == 5
    assert top_products["revenue"].is_monotonic_decreasing

    categories = get_category_performance(df)
    assert abs(categories["revenue"].sum() - kpis["total_revenue"]) < 0.01

    filtered = filter_sales(df, category="Computers")
    assert not filtered.empty
    assert filtered["category"].eq("Computers").all()

    # Verify that a full date range preserves all records.
    full_range = filter_sales(
        df,
        start_date=df["date"].min().date(),
        end_date=df["date"].max().date(),
    )
    assert_frame_equal(
        full_range.reset_index(drop=True),
        df.reset_index(drop=True),
    )

    print("PASS: Dataset validation")
    print("PASS: Financial calculations")
    print("PASS: KPI calculations")
    print("PASS: Monthly aggregation")
    print("PASS: Top product ranking")
    print("PASS: Category aggregation")
    print("PASS: Category and date filters")
    print("\nAll Stage 3 tests passed.")
    print(f"Total revenue: ₹{kpis['total_revenue']:,.2f}")
    print(f"Total profit: ₹{kpis['total_profit']:,.2f}")
    print(f"Total orders: {kpis['total_orders']}")


if __name__ == "__main__":
    main()
