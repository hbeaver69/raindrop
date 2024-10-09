import pandas as pd
import streamlit as st
from streamlit_autorefresh import st_autorefresh
from raindrop import make_raindrop_chart
from datetime import datetime, timedelta

# Set Streamlit page configuration
st.set_page_config(layout="wide", page_title="Raindrop Charts")

# Load tickers from CSV
tickers = pd.read_csv("tickers.csv")

# Streamlit App Title
st.title("Raindrop Charts using Yfinance, Streamlit, & Plotly")

# Automatically use the last 7 days
start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
end_date = datetime.now().strftime("%Y-%m-%d")

# Sidebar inputs (without date selector)
company = st.sidebar.selectbox(label="Company", options=tickers["Company"])
vwap_margin = st.sidebar.number_input(label="VWAP Margin", value=0.1, step=0.01, min_value=0., format="%.2f")

# Increase bin size flexibility beyond 60 minutes
frequency = st.sidebar.number_input(label="Bin Size (minutes)", value=30, step=1, min_value=5, max_value=1440)  # 1440 = 24 hours

# Get the ticker symbol for the selected company
ticker = tickers.loc[tickers["Company"] == company, "Ticker"].values[0]

# Try generating the raindrop chart with the last 7 days
try:
    raindrop_chart, vwap_open, vwap_close, ohlc = make_raindrop_chart(
        ticker=ticker,
        start=start_date,
        end=end_date,
        interval="1m",  # You can adjust this based on your needs
        frequency_value=frequency,
        margin=vwap_margin
    )

    # Create 3 columns for displaying metrics
    col1, col2, col3 = st.columns(3)

    # Display VWAP metrics
    col1.metric("VWAP (Current vs Previous)", f"{str(vwap_close)}$", f"{str(vwap_close - vwap_open)}$")
    col2.metric("Current Prices (Close vs Open)", f"{str(ohlc['Close'])}$", f"{str(ohlc['Close'] - ohlc['Open'])}$")
    col3.metric("Last Update", str(pd.Timestamp.now().floor("s")))

    # Display the raindrop chart
    st.plotly_chart(raindrop_chart, use_container_width=True)

except ValueError as e:
    # Catch and display detailed error message
    st.error(f"Error generating raindrop chart: {e}")
except Exception as e:
    # Catch any other errors and display message
    st.error(f"An unexpected error occurred: {e}")
