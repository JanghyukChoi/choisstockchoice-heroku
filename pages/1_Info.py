import yfinance as yf
import streamlit as st
import time
import numpy as np

st.set_page_config(page_title="KOSPI Chart Info", page_icon="📈")

st.markdown("# KOSPI Chart Info")
st.sidebar.header("KOSPI Chart Info")


st.write("""

Shown are the stock **closing price** and ***volume*** of KOSPI!

""")

# https://towardsdatascience.com/how-to-get-stock-data-using-python-c0de1df17e75
# define the ticker symbol
tickerSymbol = 'GOOGL'
# get data on this ticker
tickerData = yf.Ticker(tickerSymbol)
# get the historical prices for this ticker
tickerDf = tickerData.history(period='1d', start='2010-5-31', end='2020-5-31')
# Open	High	Low	Close	Volume	Dividends	Stock Splits

st.write("""
## Closing Price
""")
st.line_chart(tickerDf.Close)
st.write("""
## Volume Price
""")
st.line_chart(tickerDf.Volume)
