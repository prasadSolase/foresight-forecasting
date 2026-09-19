import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

from sklearn.metrics import mean_absolute_error, mean_squared_error


# PAGE CONFIGURATION

st.set_page_config(
    page_title="Foresight - Forecast",
    page_icon="📈",
    layout="wide"
)

st.title("📈 Demand Forecast")
st.write("Project Foresight | Demand Forecasting")

# Project root folder
BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

# DATA PATH
sales_path = os.path.join(
    BASE_DIR,
    "data",
    "cleaned",
    "sales_daily_clean.xls"
)


# LOAD DATA

@st.cache_data
def load_sales_data():

    sales = pd.read_csv(sales_path)

    sales.columns = sales.columns.str.strip()

    sales["Date"] = pd.to_datetime(
        sales["Date"],
        errors="coerce"
    )

    sales["Units_Sold"] = pd.to_numeric(
        sales["Units_Sold"],
        errors="coerce"
    )

    sales = sales.dropna(
        subset=["Date", "SKU", "Units_Sold"]
    )

    sales = sales.sort_values(
        ["SKU", "Date"]
    )

    return sales


# LOAD DATA

try:

    sales = load_sales_data()

except Exception as e:

    st.error(f"Error loading sales data: {e}")
    st.stop()

# BASIC VALIDATION

required_columns = [
    "Date",
    "SKU",
    "Units_Sold"
]

missing_columns = [
    column
    for column in required_columns
    if column not in sales.columns
]

if missing_columns:

    st.error(
        f"Missing columns: {missing_columns}"
    )

    st.stop()

# SIDEBAR

st.sidebar.header("Forecast Controls")


sku_list = sorted(
    sales["SKU"].unique()
)


selected_sku = st.sidebar.selectbox(
    "Select SKU",
    sku_list
)


forecast_days = st.sidebar.selectbox(
    "Forecast Horizon",
    [7, 14, 30],
    index=2
)


validation_days = st.sidebar.selectbox(
    "Validation Period",
    [7, 14, 30],
    index=1
)


# SELECT SKU

sku_data = sales[
    sales["SKU"] == selected_sku
].copy()


sku_data = sku_data.sort_values("Date")

# DAILY DEMAND

daily_demand = (
    sku_data
    .groupby("Date")["Units_Sold"]
    .sum()
    .asfreq("D")
    .fillna(0)
)

# CHECK DATA

if len(daily_demand) <= validation_days:

    st.warning(
        "Not enough historical data for forecasting."
    )

    st.stop()

# TRAIN / VALIDATION SPLIT

train = daily_demand.iloc[
    :-validation_days
]

validation = daily_demand.iloc[
    -validation_days:
]

# BASELINE MODEL

lookback_days = min(
    7,
    len(train)
)


baseline_prediction = train.tail(
    lookback_days
).mean()


validation_prediction = pd.Series(
    baseline_prediction,
    index=validation.index
)

# MODEL EVALUATION

mae = mean_absolute_error(
    validation,
    validation_prediction
)


rmse = np.sqrt(
    mean_squared_error(
        validation,
        validation_prediction
    )
)


non_zero_actual = validation != 0


if non_zero_actual.sum() > 0:

    mape = (
        np.mean(
            np.abs(
                (
                    validation[non_zero_actual]
                    - validation_prediction[non_zero_actual]
                )
                /
                validation[non_zero_actual]
            )
        )
        * 100
    )

else:

    mape = np.nan

# FUTURE FORECAST

last_date = daily_demand.index.max()


future_dates = pd.date_range(
    start=last_date + pd.Timedelta(days=1),
    periods=forecast_days,
    freq="D"
)


future_forecast = pd.DataFrame({

    "Date": future_dates,

    "Forecast_Units": baseline_prediction

})


future_forecast["Forecast_Units"] = (
    future_forecast["Forecast_Units"]
    .clip(lower=0)
)

# KPI

st.subheader("Forecast Overview")


col1, col2, col3, col4 = st.columns(4)


with col1:

    st.metric(
        "Selected SKU",
        selected_sku
    )


with col2:

    st.metric(
        "Historical Avg / Day",
        f"{daily_demand.mean():.2f}"
    )


with col3:

    st.metric(
        "Forecast Units",
        f"{future_forecast['Forecast_Units'].sum():.0f}"
    )


with col4:

    st.metric(
        "Recent 7-Day Avg",
        f"{baseline_prediction:.2f}"
    )

# HISTORICAL DEMAND

st.subheader("Historical Demand")


monthly_demand = (
    daily_demand
    .resample("MS")
    .sum()
)


fig, ax = plt.subplots(
    figsize=(12, 5)
)


ax.plot(
    monthly_demand.index,
    monthly_demand.values,
    marker="o"
)


ax.set_title(
    f"Monthly Demand - {selected_sku}"
)


ax.set_xlabel("Date")

ax.set_ylabel("Units Sold")

ax.grid(True, alpha=0.3)

fig.autofmt_xdate()


st.pyplot(
    fig,
    use_container_width=True
)


plt.close(fig)

# ACTUAL VS PREDICTED

st.subheader("Actual vs Baseline Forecast")


fig, ax = plt.subplots(
    figsize=(12, 5)
)


ax.plot(
    validation.index,
    validation.values,
    marker="o",
    label="Actual"
)


ax.plot(
    validation_prediction.index,
    validation_prediction.values,
    marker="o",
    linestyle="--",
    label="Predicted"
)


ax.set_title(
    f"Validation Forecast - {selected_sku}"
)


ax.set_xlabel("Date")

ax.set_ylabel("Units Sold")

ax.legend()

ax.grid(True, alpha=0.3)

fig.autofmt_xdate()


st.pyplot(
    fig,
    use_container_width=True
)


plt.close(fig)

# MODEL PERFORMANCE

st.subheader("Model Performance")


col1, col2, col3 = st.columns(3)


with col1:

    st.metric(
        "MAE",
        f"{mae:.2f}"
    )


with col2:

    st.metric(
        "RMSE",
        f"{rmse:.2f}"
    )


with col3:

    if np.isnan(mape):

        st.metric(
            "MAPE",
            "N/A"
        )

    else:

        st.metric(
            "MAPE",
            f"{mape:.2f}%"
        )

# FUTURE FORECAST

st.subheader(
    f"Next {forecast_days} Days Forecast"
)


fig, ax = plt.subplots(
    figsize=(12, 5)
)


ax.plot(
    future_forecast["Date"],
    future_forecast["Forecast_Units"],
    marker="o"
)


ax.set_title(
    f"Future Demand Forecast - {selected_sku}"
)


ax.set_xlabel("Date")

ax.set_ylabel("Forecast Units")

ax.grid(True, alpha=0.3)

fig.autofmt_xdate()


st.pyplot(
    fig,
    use_container_width=True
)


plt.close(fig)


# FORECAST TABLE

st.subheader("Forecast Details")


display_forecast = future_forecast.copy()


display_forecast["Date"] = (
    display_forecast["Date"]
    .dt.strftime("%Y-%m-%d")
)


display_forecast["Forecast_Units"] = (
    display_forecast["Forecast_Units"]
    .round(2)
)


st.dataframe(
    display_forecast,
    use_container_width=True,
    hide_index=True
)

# DATA INFORMATION

with st.expander("Dataset Information"):

    col1, col2 = st.columns(2)


    with col1:

        st.write(
            f"Total Sales Records: {len(sales):,}"
        )

        st.write(
            f"Total SKUs: {sales['SKU'].nunique():,}"
        )


    with col2:

        st.write(
            f"Data Start: {sales['Date'].min().date()}"
        )

        st.write(
            f"Data End: {sales['Date'].max().date()}"
        )
