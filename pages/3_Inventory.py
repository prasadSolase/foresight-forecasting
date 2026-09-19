import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os

# PAGE CONFIGURATION

st.set_page_config(
    page_title="Foresight - Inventory Dashboard",
    page_icon="📦",
    layout="wide"
)

st.title("📦 Inventory Dashboard")
st.caption("Project Foresight | Inventory Monitoring")


# Project root folder
BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

# FILE PATH

inventory_path = os.path.join(
    BASE_DIR,
    "data",
    "cleaned",
    "inventory_snapshots_clean.xls"
)


# LOAD DATA

@st.cache_data
def load_inventory():

    inventory = pd.read_csv(inventory_path)

    # Clean column names
    inventory.columns = inventory.columns.str.strip()

    # Convert date
    inventory["Snapshot_Date"] = pd.to_datetime(
        inventory["Snapshot_Date"],
        errors="coerce"
    )

    # Convert numeric columns
    numeric_columns = [
        "Current_Stock",
        "On_Order",
        "Lead_Time_Days",
        "Safety_Stock",
        "Reorder_Point",
        "Inventory_Value"
    ]

    for column in numeric_columns:
        inventory[column] = pd.to_numeric(
            inventory[column],
            errors="coerce"
        )

    # Remove invalid essential records
    inventory = inventory.dropna(
        subset=["Snapshot_Date", "SKU"]
    )

    # Convert SKU to string
    inventory["SKU"] = inventory["SKU"].astype(str).str.strip()

    return inventory.reset_index(drop=True)


# LOAD DATA

try:

    inventory = load_inventory()

except Exception as e:

    st.error(f"Error loading inventory data: {e}")
    st.stop()


# VALIDATE REQUIRED COLUMNS

required_columns = [
    "Snapshot_Date",
    "SKU",
    "Current_Stock",
    "On_Order",
    "Lead_Time_Days",
    "Safety_Stock",
    "Reorder_Point",
    "Inventory_Value"
]

missing_columns = [
    column
    for column in required_columns
    if column not in inventory.columns
]

if missing_columns:

    st.error(
        f"Missing columns: {missing_columns}"
    )

    st.stop()


# NATURAL SKU SORTING

def natural_sku_sort(df):

    result = df.copy()

    result["SKU_Number"] = pd.to_numeric(
        result["SKU"].str.extract(r"(\d+)")[0],
        errors="coerce"
    )

    result = result.sort_values(
        ["SKU_Number", "SKU"]
    )

    return result.drop(
        columns=["SKU_Number"]
    )


# CREATE INVENTORY METRICS

inventory["Stock_Gap"] = (
    inventory["Current_Stock"]
    - inventory["Reorder_Point"]
)

inventory["Below_Reorder_Point"] = (
    inventory["Current_Stock"]
    < inventory["Reorder_Point"]
)

inventory["Below_Safety_Stock"] = (
    inventory["Current_Stock"]
    < inventory["Safety_Stock"]
)

inventory["Total_Stock_Position"] = (
    inventory["Current_Stock"]
    + inventory["On_Order"]
)


# SIDEBAR FILTERS

st.sidebar.header("Inventory Filters")


# SKU FILTER


sku_list = (
    inventory["SKU"]
    .dropna()
    .unique()
    .tolist()
)

sku_filter_df = pd.DataFrame({
    "SKU": sku_list
})

sku_filter_df = natural_sku_sort(
    sku_filter_df
)

sku_list = sku_filter_df["SKU"].tolist()

selected_sku = st.sidebar.selectbox(
    "Select SKU",
    ["All SKUs"] + sku_list
)

# SNAPSHOT DATE FILTER

snapshot_dates = sorted(
    inventory["Snapshot_Date"].dropna().unique()
)

date_options = ["Latest Snapshot"] + [
    pd.Timestamp(date).strftime("%Y-%m-%d")
    for date in snapshot_dates
]

selected_date = st.sidebar.selectbox(
    "Snapshot Date",
    date_options
)

# SELECT SNAPSHOT

if selected_date == "Latest Snapshot":

    selected_snapshot_date = inventory[
        "Snapshot_Date"
    ].max()

else:

    selected_snapshot_date = pd.to_datetime(
        selected_date
    )


snapshot = inventory[
    inventory["Snapshot_Date"]
    == selected_snapshot_date
].copy()

# SKU FILTER

if selected_sku != "All SKUs":

    snapshot = snapshot[
        snapshot["SKU"] == selected_sku
    ].copy()


# EMPTY DATA CHECK

if snapshot.empty:

    st.warning(
        "No inventory data available for the selected filters."
    )

    st.stop()

# SORT SNAPSHOT BY SKU

snapshot = natural_sku_sort(snapshot)


# KPI CALCULATIONS

current_stock = snapshot[
    "Current_Stock"
].sum()

on_order = snapshot[
    "On_Order"
].sum()

inventory_value = snapshot[
    "Inventory_Value"
].sum()

below_reorder = snapshot[
    "Below_Reorder_Point"
].sum()

below_safety = snapshot[
    "Below_Safety_Stock"
].sum()


# KPI SECTION

st.subheader("Inventory Overview")

col1, col2, col3, col4, col5 = st.columns(5)


with col1:

    st.metric(
        "Current Stock",
        f"{current_stock:,.0f}"
    )


with col2:

    st.metric(
        "On Order",
        f"{on_order:,.0f}"
    )


with col3:

    st.metric(
        "Inventory Value",
        f"₹{inventory_value:,.0f}"
    )


with col4:

    st.metric(
        "Below Reorder",
        f"{below_reorder:,.0f}"
    )


with col5:

    st.metric(
        "Below Safety Stock",
        f"{below_safety:,.0f}"
    )


st.caption(
    f"Snapshot Date: {selected_snapshot_date.date()}"
)

# CHART 1
# CURRENT STOCK VS REORDER POINT

st.subheader("Current Stock vs Reorder Point")


chart_data = natural_sku_sort(
    snapshot
)

fig, ax = plt.subplots(
    figsize=(14, 6)
)

x = range(len(chart_data))

ax.bar(
    [i - 0.2 for i in x],
    chart_data["Current_Stock"],
    width=0.4,
    label="Current Stock"
)

ax.bar(
    [i + 0.2 for i in x],
    chart_data["Reorder_Point"],
    width=0.4,
    label="Reorder Point"
)

ax.set_xticks(list(x))

ax.set_xticklabels(
    chart_data["SKU"],
    rotation=45,
    ha="right"
)

ax.set_xlabel("SKU")

ax.set_ylabel("Units")

ax.set_title(
    "Current Stock vs Reorder Point"
)

ax.legend()

ax.grid(
    axis="y",
    alpha=0.3
)

plt.tight_layout()

st.pyplot(
    fig,
    use_container_width=True
)

plt.close(fig)

# CHART 2
# INVENTORY VALUE BY SKU

st.subheader("Inventory Value by SKU")

# IMPORTANT:
# Do NOT sort by Inventory_Value.
# Keep SKU001, SKU002, SKU003... order.

value_data = natural_sku_sort(
    snapshot
)

fig, ax = plt.subplots(
    figsize=(14, 6)
)

ax.bar(
    value_data["SKU"],
    value_data["Inventory_Value"]
)

# X-axis = SKU
ax.set_xlabel("SKU")

# Y-axis = Inventory Value
ax.set_ylabel(
    "Inventory Value (₹)"
)

ax.set_title(
    "Inventory Value by SKU"
)

ax.tick_params(
    axis="x",
    rotation=45
)

ax.grid(
    axis="y",
    alpha=0.3
)

plt.tight_layout()

st.pyplot(
    fig,
    use_container_width=True
)

plt.close(fig)


# LOW STOCK SKUs

st.subheader("SKUs Below Reorder Point")

low_stock = snapshot[
    snapshot["Below_Reorder_Point"]
].copy()


if low_stock.empty:

    st.success(
        "No SKUs are below the reorder point."
    )

else:

    low_stock = low_stock[
        [
            "SKU",
            "Current_Stock",
            "On_Order",
            "Safety_Stock",
            "Reorder_Point",
            "Stock_Gap",
            "Lead_Time_Days",
            "Inventory_Value"
        ]
    ]

    low_stock = low_stock.sort_values(
        "Stock_Gap"
    )

    st.dataframe(
        low_stock,
        use_container_width=True,
        hide_index=True
    )

# INVENTORY DETAILS

st.subheader("Inventory Details")

display_columns = [
    "Snapshot_Date",
    "SKU",
    "Current_Stock",
    "On_Order",
    "Lead_Time_Days",
    "Safety_Stock",
    "Reorder_Point",
    "Stock_Gap",
    "Total_Stock_Position",
    "Inventory_Value"
]

details_data = snapshot[
    display_columns
].copy()

details_data = natural_sku_sort(
    details_data
)

st.dataframe(
    details_data,
    use_container_width=True,
    hide_index=True
)

# INVENTORY TREND

st.subheader("Inventory Trend")

inventory_trend = (
    inventory
    .groupby("Snapshot_Date")
    .agg(
        Current_Stock=("Current_Stock", "sum"),
        Inventory_Value=("Inventory_Value", "sum")
    )
    .reset_index()
    .sort_values("Snapshot_Date")
)


fig, ax = plt.subplots(
    figsize=(12, 5)
)

ax.plot(
    inventory_trend["Snapshot_Date"],
    inventory_trend["Current_Stock"],
    marker="o"
)

ax.set_title(
    "Total Current Stock Trend"
)

ax.set_xlabel(
    "Snapshot Date"
)

ax.set_ylabel(
    "Current Stock"
)

ax.grid(
    True,
    alpha=0.3
)

fig.autofmt_xdate()

plt.tight_layout()

st.pyplot(
    fig,
    use_container_width=True
)

plt.close(fig)

# DATA INFORMATION

with st.expander("Dataset Information"):

    col1, col2 = st.columns(2)

    with col1:

        st.write(
            f"Total Records: {len(inventory):,}"
        )

        st.write(
            f"Total SKUs: {inventory['SKU'].nunique():,}"
        )

    with col2:

        st.write(
            f"First Snapshot: "
            f"{inventory['Snapshot_Date'].min().date()}"
        )

        st.write(
            f"Latest Snapshot: "
            f"{inventory['Snapshot_Date'].max().date()}"
        )
