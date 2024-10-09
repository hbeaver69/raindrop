import pandas as pd
import streamlit as st
from streamlit_autorefresh import st_autorefresh
from raindrop import make_raindrop_chart

# Set Streamlit page configuration
st.set_page_config(layout="wide", page_title="Raindrop Charts")

# Load tickers from CSV
tickers = pd.read_csv("tickers.csv")

# Streamlit App Title
st.title("Raindrop Charts using Yfinance, Streamlit, & Plotly")

# Set default date to the previous business day
default_date = pd.Timestamp.now()
default_date -= pd.offsets.BusinessDay(1)

# Sidebar inputs
date = st.sidebar.date_input(label="Date Range", value=default_date)
company = st.sidebar.selectbox(label="Company", options=tickers["Company"])
vwap_margin = st.sidebar.number_input(label="VWAP Margin", value=0.1, step=0.01, min_value=0., format="%.2f")
frequency = st.sidebar.number_input(label="Bin Size (minutes)", value=30, step=1, min_value=5, max_value=60)

# Get the ticker symbol for the selected company
ticker = tickers.loc[tickers["Company"] == company, "Ticker"].values[0]

# Check if selected date is valid
if pd.Timestamp(date) >= pd.Timestamp.now().floor("d"):
    # Auto-refresh every 5 seconds
    count = st_autorefresh(interval=5000, limit=100, key="fizzbuzzcounter")

# Generate raindrop chart using the inputs
raindrop_chart, vwap_open, vwap_close, ohlc = make_raindrop_chart(
    ticker=ticker,
    start=date.strftime("%Y-%m-%d"),
    end=(date + pd.Timedelta(days=1)).strftime("%Y-%m-%d"),
    interval="1m",
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
