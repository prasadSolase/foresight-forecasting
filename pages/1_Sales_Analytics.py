import streamlit as st
import pandas as pd
import os

# Project root folder
BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

# Sales file path
sales_path = os.path.join(
    BASE_DIR,
    "data",
    "cleaned",
    "sales_daily_clean.xls"
)

# Load sales data
sales = pd.read_csv(sales_path)

# Convert Date column
sales["Date"] = pd.to_datetime(
    sales["Date"]
)
# Title
st.title("📈 Sales Analytics Dashboard")

st.write(
    "Analyze historical sales, revenue, demand, and product performance."
)

st.markdown("---")

# Filters

st.sidebar.header("Sales Filters")

min_date = sales["Date"].min()
max_date = sales["Date"].max()

date_range = st.sidebar.date_input(
    "Select Date Range",
    value=(min_date.date(), max_date.date()),
    min_value=min_date.date(),
    max_value=max_date.date()
)

sku_list = ["All"] + sorted(sales["SKU"].unique().tolist())

selected_sku = st.sidebar.selectbox(
    "Select SKU",
    sku_list
)

# Apply date filter
if len(date_range) == 2:

    start_date = pd.to_datetime(date_range[0])
    end_date = pd.to_datetime(date_range[1])

    filtered_sales = sales[
        (sales["Date"] >= start_date) &
        (sales["Date"] <= end_date)
    ].copy()

else:
    filtered_sales = sales.copy()

# Apply SKU filter
if selected_sku != "All":
    filtered_sales = filtered_sales[
        filtered_sales["SKU"] == selected_sku
    ]

# KPI Section

st.header("📊 Sales Overview")

col1, col2, col3, col4 = st.columns(4)

total_units = filtered_sales["Units_Sold"].sum()
total_revenue = filtered_sales["Revenue"].sum()
average_price = filtered_sales["Price"].mean()
total_skus = filtered_sales["SKU"].nunique()

with col1:
    st.metric(
        "Total Units Sold",
        f"{total_units:,.0f}"
    )

with col2:
    st.metric(
        "Total Revenue",
        f"₹{total_revenue:,.0f}"
    )

with col3:
    st.metric(
        "Average Price",
        f"₹{average_price:,.2f}"
    )

with col4:
    st.metric(
        "Active SKUs",
        total_skus
    )

st.markdown("---")

# Daily Sales Trend

st.header("📈 Daily Sales Trend")

# Convert Date to datetime
sales["Date"] = pd.to_datetime(sales["Date"])

# Create monthly sales
monthly_sales = (
    sales.groupby(sales["Date"].dt.to_period("M"))["Units_Sold"]
    .sum()
    .reset_index()
)

# Convert Period to string
monthly_sales["Date"] = monthly_sales["Date"].astype(str)

# Set Date as index
monthly_sales = monthly_sales.set_index("Date")

# Display chart
st.line_chart(monthly_sales["Units_Sold"])

# Daily Revenue Trend

st.header("💰 Daily Revenue Trend")

monthly_revenue = (
    sales.groupby(sales["Date"].dt.to_period("M"))["Revenue"]
    .sum()
    .reset_index()
)

monthly_revenue["Date"] = monthly_revenue["Date"].astype(str)

monthly_revenue = monthly_revenue.set_index("Date")

st.line_chart(monthly_revenue["Revenue"])

# Top Products

st.header("🏆 Top 10 Products by Units Sold")

# Calculate total units sold for each SKU
top_products = (
    sales.groupby("SKU", as_index=False)["Units_Sold"]
    .sum()
    .sort_values("Units_Sold", ascending=False)
    .head(10)
)

st.subheader("Top 10 Products by Units Sold")

# Show values
st.dataframe(top_products)

# Chart
st.bar_chart(
    top_products.set_index("SKU")
)

# Promotion Analysis

st.header("🎯 Promotion Analysis")

promotion_summary = (
    filtered_sales
    .groupby("Promotion")["Units_Sold"]
    .mean()
    .reset_index()
)

promotion_summary["Promotion"] = (
    promotion_summary["Promotion"]
    .map({
        0: "No Promotion",
        1: "Promotion"
    })
    .fillna(promotion_summary["Promotion"].astype(str))
)

st.dataframe(
    promotion_summary,
    use_container_width=True
)

# Sales Data

st.header("📋 Sales Data")

st.dataframe(
    filtered_sales.head(100),
    use_container_width=True
)