import streamlit as st

# Page configuration
st.set_page_config(
    page_title="Project Foresight",
    page_icon="📊",
    layout="wide"
)

# Title
st.title("📊 Project Foresight")

st.subheader(
    "AI-Powered Demand Forecasting & Inventory Risk Management"
)

st.markdown("---")

# Business Problem
st.header("🎯 Business Problem")

st.write(
    """
    Businesses need to maintain the right amount of inventory.
    Too much inventory increases holding costs, while too little
    inventory can cause stockouts and lost sales.

    Project Foresight uses historical sales, product, calendar,
    and inventory data to forecast demand and identify inventory risks.
    """
)

# Objective
st.header("🚀 Project Objective")

st.write(
    """
    The objective of Project Foresight is to:

    - Analyze historical sales data
    - Forecast future product demand
    - Monitor inventory levels
    - Identify high-risk products
    - Support better inventory planning and decision-making
    """
)



