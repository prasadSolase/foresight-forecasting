import streamlit as st
import pandas as pd
import plotly.express as px
<<<<<<< HEAD
import os 

# PAGE CONFIGURATION

st.set_page_config(
    page_title="Product Details",
    page_icon="📦",
    layout="wide"
)

# TITLE

st.title("📦 Product Details")
st.markdown(
    "Detailed product, sales, pricing and inventory analysis for each SKU."
)

# Project root folder
BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

# FILE PATH

sku_path= os.path.join(
    BASE_DIR,
    "data",
    "cleaned",
    "sku_master_clean.xls"
)

sales_path= os.path.join(
    BASE_DIR,
    "data",
    "cleaned",
    "sales_daily_clean.xls"
)

inventory_path= os.path.join(
    BASE_DIR,
    "data",
    "cleaned",
    "inventory_snapshots_clean.xls"
)

# LOAD DATA

@st.cache_data
def load_data():

    sku = pd.read_csv(
        sku_path,
        parse_dates=["Launch_Date"]
    )

    sales = pd.read_csv(
        sales_path,
        parse_dates=["Date"]
    )

    inventory = pd.read_csv(
        inventory_path,
        parse_dates=["Snapshot_Date"]
    )

    return sku, sales, inventory


try:
    sku, sales, inventory = load_data()

except Exception as e:
    st.error("Unable to load the cleaned datasets.")
    st.exception(e)
    st.stop()


# BASIC VALIDATION

required_sku_columns = [
    "SKU",
    "Product_Name",
    "Category",
    "Subcategory",
    "Launch_Date",
    "Cost_Price",
    "Selling_Price",
    "Gross_Margin_Per_Unit"
]

required_sales_columns = [
    "Date",
    "SKU",
    "Units_Sold",
    "Revenue",
    "Price",
    "Promotion"
]

required_inventory_columns = [
    "Snapshot_Date",
    "SKU",
    "Current_Stock",
    "On_Order",
    "Lead_Time_Days",
    "Safety_Stock",
    "Reorder_Point",
    "Inventory_Value"
]


missing_sku = [
    col for col in required_sku_columns
    if col not in sku.columns
]

missing_sales = [
    col for col in required_sales_columns
    if col not in sales.columns
]

missing_inventory = [
    col for col in required_inventory_columns
    if col not in inventory.columns
]


if missing_sku:
    st.error(f"Missing columns in SKU dataset: {missing_sku}")
    st.stop()

if missing_sales:
    st.error(f"Missing columns in Sales dataset: {missing_sales}")
    st.stop()

if missing_inventory:
    st.error(f"Missing columns in Inventory dataset: {missing_inventory}")
    st.stop()

# SKU ORDER

sku_list = sku["SKU"].dropna().astype(str).unique().tolist()

sku_list = sorted(
    sku_list,
    key=lambda x: int(
        "".join(filter(str.isdigit, x))
    ) if any(char.isdigit() for char in x) else 999999
)

# SIDEBAR

st.sidebar.header("Product Selection")

selected_sku = st.sidebar.selectbox(
    "Select SKU",
    sku_list
)

# FILTER SELECTED PRODUCT

product = sku[
    sku["SKU"].astype(str) == selected_sku
].copy()

product_sales = sales[
    sales["SKU"].astype(str) == selected_sku
].copy()

product_inventory = inventory[
    inventory["SKU"].astype(str) == selected_sku
].copy()


if product.empty:
    st.error("Selected SKU was not found in SKU Master.")
    st.stop()


# PRODUCT INFORMATION

product_row = product.iloc[0]

st.subheader("Product Information")

info_col1, info_col2, info_col3, info_col4, info_col5 = st.columns(5)

with info_col1:
    st.metric(
        "SKU",
        product_row["SKU"]
    )

with info_col2:
    st.metric(
        "Product",
        product_row["Product_Name"]
    )

with info_col3:
    st.metric(
        "Category",
        product_row["Category"]
    )

with info_col4:
    st.metric(
        "Subcategory",
        product_row["Subcategory"]
    )

with info_col5:
    launch_date = product_row["Launch_Date"]

    if pd.notna(launch_date):
        launch_text = launch_date.strftime("%Y-%m-%d")
    else:
        launch_text = "N/A"

    st.metric(
        "Launch Date",
        launch_text
    )

# PRICING INFORMATION

st.subheader("Pricing & Profitability")

price_col1, price_col2, price_col3 = st.columns(3)

with price_col1:
    st.metric(
        "Cost Price",
        f"₹{product_row['Cost_Price']:,.2f}"
    )

with price_col2:
    st.metric(
        "Selling Price",
        f"₹{product_row['Selling_Price']:,.2f}"
    )

with price_col3:
    st.metric(
        "Gross Margin / Unit",
        f"₹{product_row['Gross_Margin_Per_Unit']:,.2f}"
    )

# SALES CALCULATIONS

total_units = product_sales["Units_Sold"].sum()

total_revenue = product_sales["Revenue"].sum()

average_price = product_sales["Price"].mean()

sales_days = product_sales["Date"].nunique()

promotion_days = (
    product_sales["Promotion"]
    .fillna(0)
    .astype(int)
    .sum()
)

# SALES KPIs

st.subheader("Sales Performance")

sales_col1, sales_col2, sales_col3, sales_col4, sales_col5 = st.columns(5)

with sales_col1:
    st.metric(
        "Total Units Sold",
        f"{total_units:,.0f}"
    )

with sales_col2:
    st.metric(
        "Total Revenue",
        f"₹{total_revenue:,.2f}"
    )

with sales_col3:
    st.metric(
        "Average Price",
        f"₹{average_price:,.2f}"
    )

with sales_col4:
    st.metric(
        "Sales Days",
        f"{sales_days:,}"
    )

with sales_col5:
    st.metric(
        "Promotion Days",
        f"{promotion_days:,}"
    )

# INVENTORY LATEST SNAPSHOT

st.subheader("Current Inventory Position")

if product_inventory.empty:

    st.warning(
        "No inventory records found for the selected SKU."
    )

else:

    product_inventory = product_inventory.sort_values(
        "Snapshot_Date"
    )

    latest_inventory = product_inventory.iloc[-1]

    inventory_col1, inventory_col2, inventory_col3, inventory_col4, inventory_col5 = st.columns(5)

    with inventory_col1:
        st.metric(
            "Current Stock",
            f"{latest_inventory['Current_Stock']:,.0f}"
        )

    with inventory_col2:
        st.metric(
            "On Order",
            f"{latest_inventory['On_Order']:,.0f}"
        )

    with inventory_col3:
        st.metric(
            "Safety Stock",
            f"{latest_inventory['Safety_Stock']:,.0f}"
        )

    with inventory_col4:
        st.metric(
            "Reorder Point",
            f"{latest_inventory['Reorder_Point']:,.0f}"
        )

    with inventory_col5:
        st.metric(
            "Inventory Value",
            f"₹{latest_inventory['Inventory_Value']:,.2f}"
        )

# SALES TREND

st.subheader("Daily Units Sold")

if not product_sales.empty:

    sales_chart_data = (
        product_sales
        .groupby("Date", as_index=False)["Units_Sold"]
        .sum()
        .sort_values("Date")
    )

    fig_sales = px.line(
        sales_chart_data,
        x="Date",
        y="Units_Sold",
        markers=True,
        title=f"Daily Units Sold — {selected_sku}"
    )

    fig_sales.update_layout(
        xaxis_title="Date",
        yaxis_title="Units Sold"
    )

    st.plotly_chart(
        fig_sales,
        use_container_width=True
    )

else:

    st.info("No sales data available for this SKU.")


# REVENUE TREND

st.subheader("Daily Revenue")

if not product_sales.empty:

    revenue_chart_data = (
        product_sales
        .groupby("Date", as_index=False)["Revenue"]
        .sum()
        .sort_values("Date")
    )

    fig_revenue = px.line(
        revenue_chart_data,
        x="Date",
        y="Revenue",
        markers=True,
        title=f"Daily Revenue — {selected_sku}"
    )

    fig_revenue.update_layout(
        xaxis_title="Date",
        yaxis_title="Revenue (₹)"
    )

    st.plotly_chart(
        fig_revenue,
        use_container_width=True
    )

else:

    st.info("No revenue data available for this SKU.")


# INVENTORY TREND

st.subheader("Inventory Trend")

if not product_inventory.empty:

    inventory_chart_data = (
        product_inventory[
            [
                "Snapshot_Date",
                "Current_Stock",
                "Safety_Stock",
                "Reorder_Point"
            ]
        ]
        .sort_values("Snapshot_Date")
    )

    fig_inventory = px.line(
        inventory_chart_data,
        x="Snapshot_Date",
        y=[
            "Current_Stock",
            "Safety_Stock",
            "Reorder_Point"
        ],
        markers=True,
        title=f"Inventory Position — {selected_sku}"
    )

    fig_inventory.update_layout(
        xaxis_title="Snapshot Date",
        yaxis_title="Stock Units",
        legend_title="Inventory Metric"
    )

    st.plotly_chart(
        fig_inventory,
        use_container_width=True
    )

else:

    st.info("No inventory data available for this SKU.")

# PRODUCT DETAILS TABLE

st.subheader("Product Master Details")

display_product = product[
    [
        "SKU",
        "Product_Name",
        "Category",
        "Subcategory",
        "Launch_Date",
        "Cost_Price",
        "Selling_Price",
        "Gross_Margin_Per_Unit"
    ]
].copy()

st.dataframe(
    display_product,
    use_container_width=True,
    hide_index=True
)

# INVENTORY DETAILS TABLE

if not product_inventory.empty:

    st.subheader("Inventory Details")

    st.dataframe(
        product_inventory.sort_values(
            "Snapshot_Date",
            ascending=False
        ),
        use_container_width=True,
        hide_index=True
    )


# DATASET INFORMATION

with st.expander("Dataset Information"):

    st.write(
        f"SKU Master: {sku.shape[0]:,} rows × {sku.shape[1]} columns"
    )

    st.write(
        f"Sales: {sales.shape[0]:,} rows × {sales.shape[1]} columns"
    )

    st.write(
        f"Inventory: {inventory.shape[0]:,} rows × {inventory.shape[1]} columns"
    )
