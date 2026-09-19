import streamlit as st
import pandas as pd
import plotly.express as px
import os 

# PAGE CONFIG

st.set_page_config(
    page_title="Executive Summary",
    page_icon="📊",
    layout="wide"
)

# TITLE

st.title("📊 Executive Summary")
st.markdown(
    "Management-level summary of sales, inventory, forecasting and risk."
)

# Project root folder
BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)


sales_path= os.path.join(
    BASE_DIR,
    "data",
    "cleaned",
    "sales_daily_clean.xls"
)

sku_path= os.path.join(
    BASE_DIR,
    "data",
    "cleaned",
    "sku_master_clean.xls"
)

inventory_path= os.path.join(
    BASE_DIR,
    "data",
    "cleaned",
    "inventory_snapshots_clean.xls"
)

risk_path= os.path.join(
    BASE_DIR,
    "data",
    "cleaned",
    "inventory_risk.xls"
)

forecast_path= os.path.join(
    BASE_DIR,
    "data",
    "cleaned",
    "demand_forecast.xls"
)

model_path= os.path.join(
    BASE_DIR,
    "data",
    "cleaned",
    "model_comparison.xls"
)

# LOAD DATA

@st.cache_data
def load_data():

    sales = pd.read_csv(
        sales_path,
        parse_dates=["Date"]
    )

    sku = pd.read_csv(
        sku_path,
        parse_dates=["Launch_Date"]
    )

    inventory = pd.read_csv(
        inventory_path,
        parse_dates=["Snapshot_Date"]
    )

    risk = pd.read_csv(risk_path)

    forecast = pd.read_csv(forecast_path)

    model = pd.read_csv(model_path)

    return sales, sku, inventory, risk, forecast, model


try:

    sales, sku, inventory, risk, forecast, model = load_data()

except Exception as e:

    st.error("Unable to load one or more cleaned datasets.")

    st.exception(e)

    st.stop()

# VALIDATE IMPORTANT COLUMNS

required_sales = [
    "Date",
    "SKU",
    "Units_Sold",
    "Revenue"
]

required_inventory = [
    "Snapshot_Date",
    "SKU",
    "Current_Stock",
    "Reorder_Point",
    "Inventory_Value"
]


missing_sales = [
    col for col in required_sales
    if col not in sales.columns
]

missing_inventory = [
    col for col in required_inventory
    if col not in inventory.columns
]


if missing_sales:

    st.error(
        f"Missing columns in sales_daily_clean.xls: {missing_sales}"
    )

    st.stop()


if missing_inventory:

    st.error(
        f"Missing columns in inventory_snapshots_clean.xls: "
        f"{missing_inventory}"
    )

    st.stop()

# BUSINESS KPIs

total_revenue = sales["Revenue"].sum()

total_units = sales["Units_Sold"].sum()

total_skus = sku["SKU"].nunique()

latest_inventory_date = inventory["Snapshot_Date"].max()

latest_inventory = inventory[
    inventory["Snapshot_Date"] == latest_inventory_date
].copy()


current_stock = latest_inventory["Current_Stock"].sum()

inventory_value = latest_inventory["Inventory_Value"].sum()

below_reorder = (
    latest_inventory["Current_Stock"]
    < latest_inventory["Reorder_Point"]
).sum()

# HIGH / MEDIUM / LOW RISK

high_risk = 0
medium_risk = 0
low_risk = 0


if "Risk_Level" in risk.columns:

    risk_levels = (
        risk["Risk_Level"]
        .astype(str)
        .str.strip()
        .str.lower()
    )

    high_risk = (
        risk_levels == "high risk"
    ).sum()

    medium_risk = (
        risk_levels == "medium risk"
    ).sum()

    low_risk = (
        risk_levels == "low risk"
    ).sum()


# KPI SECTION

st.subheader("Business Overview")

k1, k2, k3, k4, k5, k6 = st.columns(6)


with k1:

    st.metric(
        "Total Revenue",
        f"₹{total_revenue:,.0f}"
    )


with k2:

    st.metric(
        "Units Sold",
        f"{total_units:,.0f}"
    )


with k3:

    st.metric(
        "Total SKUs",
        f"{total_skus:,}"
    )


with k4:

    st.metric(
        "Current Stock",
        f"{current_stock:,.0f}"
    )


with k5:

    st.metric(
        "Inventory Value",
        f"₹{inventory_value:,.0f}"
    )


with k6:

    st.metric(
        "Below Reorder Point",
        f"{below_reorder:,}"
    )


# SALES OVERVIEW

st.subheader("Sales Overview")


sales_monthly = (
    sales
    .assign(
        Month=sales["Date"].dt.to_period("M").astype(str)
    )
    .groupby("Month", as_index=False)
    .agg(
        Revenue=("Revenue", "sum"),
        Units_Sold=("Units_Sold", "sum")
    )
    .sort_values("Month")
)

# Monthly Revenue

fig_revenue = px.line(
    sales_monthly,
    x="Month",
    y="Revenue",
    markers=True,
    title="Monthly Revenue"
)

fig_revenue.update_layout(
    xaxis_title="Month",
    yaxis_title="Revenue (₹)"
)

st.plotly_chart(
    fig_revenue,
    use_container_width=True
)


# Monthly Units Sold

fig_units = px.line(
    sales_monthly,
    x="Month",
    y="Units_Sold",
    markers=True,
    title="Monthly Units Sold"
)

fig_units.update_layout(
    xaxis_title="Month",
    yaxis_title="Units Sold"
)

st.plotly_chart(
    fig_units,
    use_container_width=True
)

# INVENTORY OVERVIEW

st.subheader("Inventory Overview")


inventory_summary = latest_inventory.copy()

# Current Stock vs Reorder Point

inventory_summary = inventory_summary.sort_values(
    "SKU",
    key=lambda x: pd.to_numeric(
        x.str.extract(r"(\d+)")[0],
        errors="coerce"
    )
)


fig_inventory = px.bar(
    inventory_summary,
    x="SKU",
    y=["Current_Stock", "Reorder_Point"],
    barmode="group",
    title="Current Stock vs Reorder Point"
)

fig_inventory.update_layout(
    xaxis_title="SKU",
    yaxis_title="Stock Units"
)

st.plotly_chart(
    fig_inventory,
    use_container_width=True
)


# RISK OVERVIEW

st.subheader("Inventory Risk Overview")


# Use latest inventory snapshot
risk_inventory = latest_inventory.copy()


# Calculate Risk Level

risk_inventory["Risk_Level"] = "Low Risk"

risk_inventory.loc[
    risk_inventory["Current_Stock"] < risk_inventory["Reorder_Point"],
    "Risk_Level"
] = "Medium Risk"

risk_inventory.loc[
    risk_inventory["Current_Stock"] < risk_inventory["Safety_Stock"],
    "Risk_Level"
] = "High Risk"

# Risk Counts

risk_data = (
    risk_inventory["Risk_Level"]
    .value_counts()
    .reindex(
        ["High Risk", "Medium Risk", "Low Risk"],
        fill_value=0
    )
    .reset_index()
)

risk_data.columns = [
    "Risk Level",
    "Number of SKUs"
]

# Risk Distribution Chart

fig_risk = px.bar(
    risk_data,
    x="Risk Level",
    y="Number of SKUs",
    title="Inventory Risk Distribution"
)

fig_risk.update_layout(
    xaxis_title="Risk Level",
    yaxis_title="Number of SKUs"
)

st.plotly_chart(
    fig_risk,
    use_container_width=True
)

# Risk Summary Table

st.dataframe(
    risk_data,
    use_container_width=True,
    hide_index=True
)

# FORECAST / MODEL PERFORMANCE

st.subheader("Forecast Model Performance")


if not model.empty:

    st.dataframe(
        model,
        use_container_width=True,
        hide_index=True
    )

else:

    st.info(
        "No model comparison records available."
    )

# FORECAST DATA PREVIEW

if not forecast.empty:

    with st.expander("Forecast Data"):

        st.dataframe(
            forecast.head(20),
            use_container_width=True,
            hide_index=True
        )


# EXECUTIVE INSIGHTS

st.subheader("Executive Insights")


st.write(
    f"• The business recorded total revenue of "
    f"₹{total_revenue:,.2f}."
)

st.write(
    f"• Total units sold across the available sales data are "
    f"{total_units:,.0f}."
)

st.write(
    f"• The product master contains {total_skus:,} unique SKUs."
)

st.write(
    f"• Current inventory position contains "
    f"{current_stock:,.0f} units."
)

st.write(
    f"• Current inventory value is "
    f"₹{inventory_value:,.2f}."
)

st.write(
    f"• {below_reorder:,} SKUs are below their reorder point "
    f"on the latest inventory snapshot."
)

st.write(
    f"• Risk classification contains "
    f"{high_risk:,} High Risk, "
    f"{medium_risk:,} Medium Risk and "
    f"{low_risk:,} Low Risk SKUs."
)

# DATASET INFORMATION

with st.expander("Dataset Information"):

    st.write(
        f"Sales: {sales.shape[0]:,} rows × "
        f"{sales.shape[1]} columns"
    )

    st.write(
        f"SKU Master: {sku.shape[0]:,} rows × "
        f"{sku.shape[1]} columns"
    )

    st.write(
        f"Inventory: {inventory.shape[0]:,} rows × "
        f"{inventory.shape[1]} columns"
    )

    st.write(
        f"Risk: {risk.shape[0]:,} rows × "
        f"{risk.shape[1]} columns"
    )

    st.write(
        f"Forecast: {forecast.shape[0]:,} rows × "
        f"{forecast.shape[1]} columns"
    )

    st.write(
        f"Model Comparison: {model.shape[0]:,} rows × "
        f"{model.shape[1]} columns"
    )
