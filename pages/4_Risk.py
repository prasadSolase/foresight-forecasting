import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# PAGE CONFIGURATION

st.set_page_config(
    page_title="Foresight - Risk Dashboard",
    page_icon="⚠️",
    layout="wide"
)

st.title("⚠️ Risk Dashboard")
st.caption("Project Foresight | Inventory Risk Monitoring")


# FILE PATH

FEATURE_PATH = r"C:\foresight\data\cleaned\feature_engineered.xls"

# LOAD DATA

@st.cache_data
def load_feature_data():

    df = pd.read_csv(FEATURE_PATH)

    # Clean column names
    df.columns = df.columns.str.strip()

    # Convert date
    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(
            df["Date"],
            errors="coerce"
        )

    if "Snapshot_Date" in df.columns:
        df["Snapshot_Date"] = pd.to_datetime(
            df["Snapshot_Date"],
            errors="coerce"
        )

    # Convert SKU to string
    df["SKU"] = (
        df["SKU"]
        .astype(str)
        .str.strip()
    )

    # Numeric columns
    numeric_columns = [
        "Current_Stock",
        "On_Order",
        "Lead_Time_Days",
        "Safety_Stock",
        "Reorder_Point",
        "Stock_Gap"
    ]

    for column in numeric_columns:

        if column in df.columns:

            df[column] = pd.to_numeric(
                df[column],
                errors="coerce"
            )

    return df


# LOAD DATA

try:

    data = load_feature_data()

except Exception as e:

    st.error(
        f"Error loading feature engineered data: {e}"
    )

    st.stop()


# REQUIRED COLUMNS

required_columns = [
    "SKU",
    "Current_Stock",
    "Safety_Stock",
    "Reorder_Point",
    "Stock_Gap",
    "Lead_Time_Days"
]

missing_columns = [
    column
    for column in required_columns
    if column not in data.columns
]

if missing_columns:

    st.error(
        f"Missing required columns: {missing_columns}"
    )

    st.stop()

# NATURAL SKU SORTING

def natural_sku_sort(df):

    result = df.copy()

    result["SKU_Number"] = pd.to_numeric(
        result["SKU"]
        .astype(str)
        .str.extract(r"(\d+)")[0],
        errors="coerce"
    )

    result = result.sort_values(
        ["SKU_Number", "SKU"]
    )

    return result.drop(
        columns=["SKU_Number"]
    )


# REMOVE INVALID INVENTORY RECORDS

risk_data = data.dropna(
    subset=[
        "SKU",
        "Current_Stock",
        "Safety_Stock",
        "Reorder_Point",
        "Stock_Gap"
    ]
).copy()

# CREATE RISK LEVEL

def assign_risk(row):

    if row["Current_Stock"] < row["Safety_Stock"]:

        return "High Risk"

    elif row["Current_Stock"] < row["Reorder_Point"]:

        return "Medium Risk"

    else:

        return "Low Risk"


risk_data["Risk_Level"] = risk_data.apply(
    assign_risk,
    axis=1
)


# SIDEBAR

st.sidebar.header("Risk Filters")

# SKU FILTER

sku_list = (
    risk_data["SKU"]
    .dropna()
    .unique()
    .tolist()
)

sku_df = pd.DataFrame({
    "SKU": sku_list
})

sku_df = natural_sku_sort(
    sku_df
)

sku_list = sku_df["SKU"].tolist()

selected_sku = st.sidebar.selectbox(
    "Select SKU",
    ["All SKUs"] + sku_list
)


# DATE FILTER

date_column = None

if "Snapshot_Date" in risk_data.columns:
    date_column = "Snapshot_Date"

elif "Date" in risk_data.columns:
    date_column = "Date"


if date_column is not None:

    available_dates = sorted(
        risk_data[date_column]
        .dropna()
        .unique()
    )

    date_options = ["Latest Date"] + [
        pd.Timestamp(date).strftime("%Y-%m-%d")
        for date in available_dates
    ]

    selected_date = st.sidebar.selectbox(
        "Date",
        date_options
    )

else:

    selected_date = None


# APPLY DATE FILTER

filtered_data = risk_data.copy()


if date_column is not None:

    if selected_date == "Latest Date":

        latest_date = filtered_data[
            date_column
        ].max()

        filtered_data = filtered_data[
            filtered_data[date_column]
            == latest_date
        ].copy()

    else:

        selected_date_value = pd.to_datetime(
            selected_date
        )

        filtered_data = filtered_data[
            filtered_data[date_column]
            == selected_date_value
        ].copy()


# APPLY SKU FILTER


if selected_sku != "All SKUs":

    filtered_data = filtered_data[
        filtered_data["SKU"] == selected_sku
    ].copy()


# EMPTY DATA CHECK

if filtered_data.empty:

    st.warning(
        "No risk data available for the selected filters."
    )

    st.stop()

# SORT DATA BY SKU

filtered_data = natural_sku_sort(
    filtered_data
)

# KPI CALCULATIONS

total_skus = filtered_data["SKU"].nunique()

high_risk = (
    filtered_data["Risk_Level"]
    == "High Risk"
).sum()

medium_risk = (
    filtered_data["Risk_Level"]
    == "Medium Risk"
).sum()

low_risk = (
    filtered_data["Risk_Level"]
    == "Low Risk"
).sum()


# KPI SECTION

st.subheader("Risk Overview")

col1, col2, col3, col4 = st.columns(4)


with col1:

    st.metric(
        "Total SKUs",
        f"{total_skus:,.0f}"
    )


with col2:

    st.metric(
        "High Risk",
        f"{high_risk:,.0f}"
    )


with col3:

    st.metric(
        "Medium Risk",
        f"{medium_risk:,.0f}"
    )


with col4:

    st.metric(
        "Low Risk",
        f"{low_risk:,.0f}"
    )

# CHART 1
# RISK DISTRIBUTION

st.subheader("Risk Distribution")

risk_order = [
    "High Risk",
    "Medium Risk",
    "Low Risk"
]

risk_distribution = (
    filtered_data["Risk_Level"]
    .value_counts()
    .reindex(
        risk_order,
        fill_value=0
    )
    .reset_index()
)

risk_distribution.columns = [
    "Risk_Level",
    "SKU_Count"
]


fig, ax = plt.subplots(
    figsize=(9, 5)
)

ax.bar(
    risk_distribution["Risk_Level"],
    risk_distribution["SKU_Count"]
)

# X-axis = Risk Level
ax.set_xlabel("Risk Level")

# Y-axis = Number of SKUs
ax.set_ylabel("Number of SKUs")

ax.set_title(
    "Risk Distribution"
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


# CHART 2
# STOCK GAP BY SKU

st.subheader("Stock Gap by SKU")


sku_risk_data = (
    filtered_data
    .groupby("SKU", as_index=False)
    .agg(
        Stock_Gap=("Stock_Gap", "mean")
    )
)

sku_risk_data = natural_sku_sort(
    sku_risk_data
)


fig, ax = plt.subplots(
    figsize=(14, 6)
)

ax.bar(
    sku_risk_data["SKU"],
    sku_risk_data["Stock_Gap"]
)

# X-axis = SKU
ax.set_xlabel("SKU")

# Y-axis = Stock Gap in units
ax.set_ylabel("Stock Gap (Units)")

ax.set_title(
    "Stock Gap by SKU"
)

ax.axhline(
    0,
    linewidth=1
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

# CHART 3
# LEAD TIME BY RISK LEVEL

st.subheader("Average Lead Time by Risk Level")

lead_time_risk = (
    filtered_data
    .groupby("Risk_Level", as_index=False)
    .agg(
        Average_Lead_Time_Days=(
            "Lead_Time_Days",
            "mean"
        )
    )
)

lead_time_risk["Risk_Level"] = pd.Categorical(
    lead_time_risk["Risk_Level"],
    categories=risk_order,
    ordered=True
)

lead_time_risk = lead_time_risk.sort_values(
    "Risk_Level"
)


fig, ax = plt.subplots(
    figsize=(9, 5)
)

ax.bar(
    lead_time_risk["Risk_Level"],
    lead_time_risk["Average_Lead_Time_Days"]
)

# X-axis = Risk Level
ax.set_xlabel("Risk Level")

# Y-axis = Average Lead Time
ax.set_ylabel("Average Lead Time (Days)")

ax.set_title(
    "Average Lead Time by Risk Level"
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

# HIGH-RISK SKU TABLE

st.subheader("High-Risk SKUs")

high_risk_data = filtered_data[
    filtered_data["Risk_Level"]
    == "High Risk"
].copy()


if high_risk_data.empty:

    st.success(
        "No high-risk SKUs found."
    )

else:

    high_risk_columns = [
        "SKU",
        "Current_Stock",
        "Safety_Stock",
        "Reorder_Point",
        "Stock_Gap",
        "On_Order",
        "Lead_Time_Days",
        "Risk_Level"
    ]

    high_risk_data = high_risk_data[
        high_risk_columns
    ]

    high_risk_data = natural_sku_sort(
        high_risk_data
    )

    st.dataframe(
        high_risk_data,
        use_container_width=True,
        hide_index=True
    )

# RISK DETAILS

st.subheader("Risk Details")

risk_detail_columns = [
    "SKU",
    "Current_Stock",
    "Safety_Stock",
    "Reorder_Point",
    "Stock_Gap",
    "On_Order",
    "Lead_Time_Days",
    "Risk_Level"
]

risk_details = filtered_data[
    risk_detail_columns
].copy()

risk_details = natural_sku_sort(
    risk_details
)

st.dataframe(
    risk_details,
    use_container_width=True,
    hide_index=True
)

# DATA INFORMATION

with st.expander("Dataset Information"):

    col1, col2 = st.columns(2)

    with col1:

        st.write(
            f"Total Records: {len(data):,}"
        )

        st.write(
            f"Total SKUs: {data['SKU'].nunique():,}"
        )

    with col2:

        if "Date" in data.columns:

            st.write(
                f"First Date: "
                f"{data['Date'].min().date()}"
            )

            st.write(
                f"Latest Date: "
                f"{data['Date'].max().date()}"
            )

        elif "Snapshot_Date" in data.columns:

            st.write(
                f"First Snapshot: "
                f"{data['Snapshot_Date'].min().date()}"
            )

            st.write(
                f"Latest Snapshot: "
                f"{data['Snapshot_Date'].max().date()}"
            )