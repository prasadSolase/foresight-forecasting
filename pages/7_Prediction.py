import streamlit as st
import pandas as pd
import plotly.express as px
import os

# PAGE CONFIGURATION

st.set_page_config(
    page_title="Prediction Dashboard",
    page_icon="📈",
    layout="wide"
)

# TITLE

st.title("📈 Demand Prediction Dashboard")

st.write(
    "Actual demand vs predicted demand analysis for Project Foresight."
)

# Project root folder
BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

# FILE PATH

file_path= os.path.join(
    BASE_DIR,
    "data",
    "cleaned",
    "demand_forecast.xls"
)
forecast = pd.read_csv(file_path)

# DATA VALIDATION

required_columns = [
    "Date",
    "SKU",
    "Units_Sold",
    "Predicted_Demand",
    "Forecast_Error",
    "Absolute_Error"
]

missing_columns = [
    col for col in required_columns
    if col not in forecast.columns
]

if missing_columns:
    st.error(
        f"Missing required columns: {missing_columns}"
    )
    st.stop()


# Convert Date to datetime
forecast["Date"] = pd.to_datetime(
    forecast["Date"],
    errors="coerce"
)


# Remove invalid dates
forecast = forecast.dropna(
    subset=["Date"]
).copy()

# NATURAL SKU SORTING

forecast["SKU_Number"] = pd.to_numeric(
    forecast["SKU"].str.extract(r"(\d+)")[0],
    errors="coerce"
)

forecast = forecast.sort_values(
    ["SKU_Number", "SKU", "Date"]
).drop(
    columns=["SKU_Number"]
)

# SIDEBAR FILTERS

st.sidebar.header("Prediction Filters")


# SKU selection
sku_list = sorted(
    forecast["SKU"].dropna().unique(),
    key=lambda x: int(
        ''.join(filter(str.isdigit, x))
    ) if any(char.isdigit() for char in x) else 0
)

selected_sku = st.sidebar.selectbox(
    "Select SKU",
    sku_list
)


# Date range
min_date = forecast["Date"].min().date()
max_date = forecast["Date"].max().date()

selected_dates = st.sidebar.date_input(
    "Select Date Range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

# FILTER DATA

sku_data = forecast[
    forecast["SKU"] == selected_sku
].copy()


if len(selected_dates) == 2:

    start_date, end_date = selected_dates

    sku_data = sku_data[
        (sku_data["Date"].dt.date >= start_date)
        &
        (sku_data["Date"].dt.date <= end_date)
    ].copy()

# CHECK DATA

if sku_data.empty:

    st.warning(
        "No prediction data available for the selected filters."
    )

    st.stop()


# KPI CALCULATIONS

total_actual = sku_data["Units_Sold"].sum()

total_predicted = sku_data["Predicted_Demand"].sum()

average_prediction = sku_data[
    "Predicted_Demand"
].mean()

mae = sku_data[
    "Absolute_Error"
].mean()

# KPI DISPLAY

col1, col2, col3, col4 = st.columns(4)


with col1:
    st.metric(
        "Total Actual Demand",
        f"{total_actual:,.0f}"
    )


with col2:
    st.metric(
        "Total Predicted Demand",
        f"{total_predicted:,.0f}"
    )


with col3:
    st.metric(
        "Average Predicted Demand",
        f"{average_prediction:,.2f}"
    )


with col4:
    st.metric(
        "Mean Absolute Error",
        f"{mae:,.2f}"
    )

# ACTUAL VS PREDICTED DEMAND

st.subheader("Actual vs Predicted Demand")


plot_data = sku_data[
    [
        "Date",
        "Units_Sold",
        "Predicted_Demand"
    ]
].copy()


fig_actual_predicted = px.line(
    plot_data,
    x="Date",
    y=[
        "Units_Sold",
        "Predicted_Demand"
    ],
    markers=True,
    title=f"Actual vs Predicted Demand — {selected_sku}"
)


fig_actual_predicted.update_layout(
    xaxis_title="Date",
    yaxis_title="Demand (Units)",
    legend_title="Demand Type"
)


st.plotly_chart(
    fig_actual_predicted,
    use_container_width=True
)

# FORECAST ERROR

st.subheader("Forecast Error")


fig_error = px.line(
    sku_data,
    x="Date",
    y="Forecast_Error",
    markers=True,
    title=f"Forecast Error — {selected_sku}"
)


fig_error.add_hline(
    y=0,
    line_dash="dash"
)


fig_error.update_layout(
    xaxis_title="Date",
    yaxis_title="Forecast Error (Units)"
)


st.plotly_chart(
    fig_error,
    use_container_width=True
)

# PREDICTED DEMAND BY SKU

st.subheader("Predicted Demand by SKU")


sku_prediction = (
    forecast
    .groupby("SKU", as_index=False)
    ["Predicted_Demand"]
    .sum()
)


# Natural SKU order
sku_prediction["SKU_Number"] = pd.to_numeric(
    sku_prediction["SKU"].str.extract(r"(\d+)")[0],
    errors="coerce"
)

sku_prediction = sku_prediction.sort_values(
    ["SKU_Number", "SKU"]
).drop(
    columns=["SKU_Number"]
)


fig_sku_prediction = px.bar(
    sku_prediction,
    x="SKU",
    y="Predicted_Demand",
    title="Total Predicted Demand by SKU"
)


fig_sku_prediction.update_layout(
    xaxis_title="SKU",
    yaxis_title="Predicted Demand (Units)"
)


st.plotly_chart(
    fig_sku_prediction,
    use_container_width=True
)

# PREDICTION DETAILS

st.subheader(
    f"Prediction Details — {selected_sku}"
)


display_data = sku_data[
    [
        "Date",
        "SKU",
        "Units_Sold",
        "Predicted_Demand",
        "Forecast_Error",
        "Absolute_Error"
    ]
].copy()


display_data["Date"] = display_data[
    "Date"
].dt.strftime("%Y-%m-%d")


st.dataframe(
    display_data,
    use_container_width=True,
    hide_index=True
)

# DATASET INFORMATION

with st.expander("Dataset Information"):

    col1, col2 = st.columns(2)

    with col1:

        st.write(
            "**Dataset Shape:**",
            forecast.shape
        )

        st.write(
            "**Total SKUs:**",
            forecast["SKU"].nunique()
        )

    with col2:

        st.write(
            "**Start Date:**",
            forecast["Date"].min().date()
        )

        st.write(
            "**End Date:**",
            forecast["Date"].max().date()
        )
