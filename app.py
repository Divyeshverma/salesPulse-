import streamlit as st
import plotly.express as px

from src.analysis import (
    filter_sales,
    get_category_performance,
    get_kpis,
    get_monthly_sales,
    get_top_products,
    load_sales_data,
)

st.set_page_config(
    page_title="SalesPulse | Analytics",
    page_icon="S",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------- Premium dashboard styling ----------
st.markdown(
    """
    <style>
    :root {
        --sp-bg: #0b1020;
        --sp-panel: #131b2e;
        --sp-border: rgba(148, 163, 184, 0.16);
        --sp-text: #f1f5f9;
        --sp-muted: #94a3b8;
        --sp-blue: #60a5fa;
    }

    .stApp {
        background:
            radial-gradient(ellipse at 12% 0%, #172747 0%, transparent 38%),
            var(--sp-bg);
        color: var(--sp-text);
    }

    [data-testid="stHeader"] {
        background: rgba(11, 16, 32, 0.85);
    }

    .block-container {
        max-width: 1500px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }

    [data-testid="stSidebar"] {
        background: #0e1526;
        border-right: 1px solid var(--sp-border);
    }

    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] label {
        color: var(--sp-text);
    }

    .sp-brand {
        font-size: 13px;
        font-weight: 700;
        letter-spacing: 3px;
        color: var(--sp-blue);
        text-transform: uppercase;
        margin-bottom: 8px;
    }

    .sp-title {
        font-size: clamp(30px, 3vw, 42px);
        font-weight: 750;
        letter-spacing: -1.5px;
        line-height: 1.15;
        color: #f8fafc;
        margin: 0;
    }

    .sp-subtitle {
        color: var(--sp-muted);
        font-size: 14px;
        margin-top: 9px;
        margin-bottom: 24px;
    }

    .sp-section {
        font-size: 19px;
        font-weight: 650;
        letter-spacing: -0.35px;
        color: #f1f5f9;
        margin: 10px 0 14px 0;
    }

    div[data-testid="stMetric"] {
        background: linear-gradient(145deg, #172239, #111a2d);
        border: 1px solid var(--sp-border);
        border-radius: 16px;
        padding: 20px 20px 18px;
        min-height: 125px;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
    }

    div[data-testid="stMetricLabel"] p {
        color: #aab8cc;
        font-size: 13px;
        font-weight: 500;
    }

    div[data-testid="stMetricValue"] {
        color: #f8fafc;
        font-size: clamp(21px, 2vw, 30px);
        font-weight: 700;
    }

    div[data-testid="stPlotlyChart"] {
        background: #111a2b;
        border: 1px solid var(--sp-border);
        border-radius: 16px;
        padding: 10px 10px 2px;
    }

    div[data-testid="stDataFrame"] {
        border: 1px solid var(--sp-border);
        border-radius: 12px;
        overflow: hidden;
    }

    .sp-note {
        color: #8493aa;
        font-size: 12px;
        padding-top: 10px;
    }

    div.stButton > button,
    div.stDownloadButton > button {
        border-radius: 9px;
        border: 1px solid rgba(96, 165, 250, 0.4);
        font-weight: 600;
    }

    div.stButton > button:hover,
    div.stDownloadButton > button:hover {
        border-color: #60a5fa;
        color: #93c5fd;
    }

    hr {
        border-color: var(--sp-border);
        margin-top: 24px;
        margin-bottom: 24px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def money(value):
    return f"Rs {value:,.0f}"


def style_chart(fig, height=340):
    fig.update_layout(
        template="plotly_dark",
        height=height,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Arial, sans-serif", color="#cbd5e1", size=12),
        margin=dict(l=18, r=18, t=48, b=18),
        title=dict(font=dict(size=15, color="#f1f5f9")),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, title_text=""),
        hoverlabel=dict(
            bgcolor="#172239",
            bordercolor="#334155",
            font_color="#f8fafc",
        ),
    )
    fig.update_xaxes(
        showgrid=False,
        zeroline=False,
        linecolor="rgba(148,163,184,0.15)",
    )
    fig.update_yaxes(
        gridcolor="rgba(148,163,184,0.10)",
        zeroline=False,
    )
    return fig


# ---------- Load data ----------
try:
    sales = load_sales_data()
except (OSError, ValueError, KeyError) as exc:
    st.error(f"Could not load sales data: {exc}")
    st.info("Check that data/sales.csv exists and follows the required schema.")
    st.stop()

if sales.empty:
    st.warning("The dataset contains no sales records.")
    st.stop()


# ---------- Sidebar ----------
with st.sidebar:
    st.markdown(
        '<div class="sp-brand">SALES PULSE</div>',
        unsafe_allow_html=True,
    )
    st.title("Analytics")
    st.caption("Business performance workspace")
    st.divider()

    st.markdown("### Filters")

    min_date = sales["date"].min().date()
    max_date = sales["date"].max().date()

    selected_dates = st.date_input(
        "Reporting period",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )

    categories = sorted(
        sales["category"].dropna().unique().tolist()
    )

    selected_category = st.selectbox(
        "Product category",
        ["All categories"] + categories,
    )

    st.divider()
    st.caption("DATA SOURCE")
    st.markdown("Synthetic sales dataset")
    st.caption(
        f"{len(sales):,} source records | "
        f"{min_date:%d %b %Y} – {max_date:%d %b %Y}"
    )


# ---------- Date handling ----------
if isinstance(selected_dates, (tuple, list)):
    if len(selected_dates) == 2:
        start_date, end_date = selected_dates
    elif len(selected_dates) == 1:
        start_date = end_date = selected_dates[0]
    else:
        start_date = min_date
        end_date = max_date
else:
    start_date = end_date = selected_dates

category_filter = (
    None
    if selected_category == "All categories"
    else selected_category
)

filtered_sales = filter_sales(
    sales,
    start_date=start_date,
    end_date=end_date,
    category=category_filter,
)


# ---------- Dashboard header ----------
st.markdown(
    '<div class="sp-brand">BUSINESS INTELLIGENCE / OVERVIEW</div>'
    '<div class="sp-title">Sales performance</div>'
    '<div class="sp-subtitle">'
    'Understand revenue, profitability and product performance '
    'from one workspace.'
    '</div>',
    unsafe_allow_html=True,
)

st.markdown(
    f'<div class="sp-note">REPORTING PERIOD &nbsp; '
    f'{start_date:%d %b %Y} — {end_date:%d %b %Y}'
    f' &nbsp; | &nbsp; {len(filtered_sales):,} matching records</div>',
    unsafe_allow_html=True,
)

if filtered_sales.empty:
    st.warning("No records match the selected filters. Try a wider date range.")
    st.stop()


# ---------- KPI cards ----------
st.markdown(
    '<div class="sp-section">Business overview</div>',
    unsafe_allow_html=True,
)

kpis = get_kpis(filtered_sales)

row1 = st.columns(3, gap="medium")
row1[0].metric("TOTAL REVENUE", money(kpis["total_revenue"]))
row1[1].metric("TOTAL PROFIT", money(kpis["total_profit"]))
row1[2].metric("TOTAL ORDERS", f'{kpis["total_orders"]:,}')

row2 = st.columns(3, gap="medium")
row2[0].metric("UNITS SOLD", f'{kpis["units_sold"]:,}')
row2[1].metric(
    "AVERAGE ORDER VALUE",
    money(kpis["average_order_value"]),
)
row2[2].metric(
    "PROFIT MARGIN",
    f'{kpis["profit_margin_pct"]:.1f}%',
)

st.divider()


# ---------- Monthly trend ----------
st.markdown(
    '<div class="sp-section">Revenue & profitability</div>',
    unsafe_allow_html=True,
)

monthly = get_monthly_sales(filtered_sales)

if monthly.empty:
    st.info("No monthly data is available for this filter.")
else:
    trend = px.line(
        monthly,
        x="month",
        y=["revenue", "profit"],
        markers=True,
        color_discrete_sequence=["#60a5fa", "#34d399"],
        labels={
            "month": "Month",
            "value": "Amount (Rs)",
            "variable": "Metric",
        },
        title="Monthly revenue vs profit",
    )
    trend.update_traces(line=dict(width=3), marker=dict(size=6))
    trend.update_layout(hovermode="x unified")
    style_chart(trend, height=370)
    st.plotly_chart(trend, use_container_width=True)


# ---------- Product and category charts ----------
left, right = st.columns(2, gap="large")

with left:
    st.markdown(
        '<div class="sp-section">Product performance</div>',
        unsafe_allow_html=True,
    )

    top_products = get_top_products(filtered_sales, limit=5)

    if top_products.empty:
        st.info("No product data available.")
    else:
        product_fig = px.bar(
            top_products.sort_values("revenue"),
            x="revenue",
            y="product",
            orientation="h",
            text="revenue",
            color="revenue",
            color_continuous_scale=["#243653", "#60a5fa"],
            labels={"revenue": "Revenue (Rs)", "product": ""},
            title="Top products by revenue",
        )
        product_fig.update_traces(
            texttemplate="Rs %{x:,.0f}",
            textposition="outside",
            cliponaxis=False,
        )
        product_fig.update_layout(
            showlegend=False,
            coloraxis_showscale=False,
            xaxis=dict(automargin=True),
        )
        style_chart(product_fig, height=350)
        st.plotly_chart(product_fig, use_container_width=True)

with right:
    st.markdown(
        '<div class="sp-section">Revenue mix</div>',
        unsafe_allow_html=True,
    )

    category_data = get_category_performance(filtered_sales)

    if category_data.empty:
        st.info("No category data available.")
    else:
        category_fig = px.pie(
            category_data,
            names="category",
            values="revenue",
            hole=0.68,
            color_discrete_sequence=[
                "#60a5fa",
                "#34d399",
                "#a78bfa",
                "#fbbf24",
                "#f87171",
            ],
            title="Revenue share by category",
        )
        category_fig.update_traces(
            textposition="inside",
            textinfo="percent",
            hole=0.68,
            marker=dict(line=dict(color="#111a2b", width=3)),
        )
        style_chart(category_fig, height=350)
        st.plotly_chart(category_fig, use_container_width=True)


# ---------- Transaction explorer ----------
st.divider()

st.markdown(
    '<div class="sp-section">Sales data explorer</div>',
    unsafe_allow_html=True,
)
st.caption(
    "Search transactions, inspect the underlying records and export "
    "the filtered data."
)

search_term = st.text_input(
    "Search order ID or product",
    placeholder="Try ORD-00010 or Laptop",
)

display_data = filtered_sales.copy()

if search_term.strip():
    term = search_term.strip()
    mask = (
        display_data["order_id"].astype(str).str.contains(
            term, case=False, regex=False
        )
        | display_data["product"].astype(str).str.contains(
            term, case=False, regex=False
        )
    )
    display_data = display_data[mask]

st.caption(f"{len(display_data):,} records found")

st.dataframe(
    display_data,
    use_container_width=True,
    hide_index=True,
)

st.download_button(
    label="Download filtered CSV",
    data=display_data.to_csv(index=False).encode("utf-8"),
    file_name="salespulse_filtered_sales.csv",
    mime="text/csv",
)

st.markdown(
    '<div class="sp-note">'
    'DEMO ENVIRONMENT — figures are generated from synthetic data and '
    'do not represent actual client results.'
    '</div>',
    unsafe_allow_html=True,
)

