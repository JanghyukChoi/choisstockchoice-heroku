from fastapi import FastAPI, HTTPException
from typing import Dict
from pydantic import BaseModel
import yfinance as yf
from datetime import datetime
import pandas as pd
import firebase_admin
from datetime import timedelta
from firebase_admin import credentials, firestore
from fastapi.responses import JSONResponse
import FinanceDataReader as fdr
import numpy as np
import streamlit as st
import requests

import numpy as np
import pandas as pd


@st.cache(ttl=800)
def cached_update_sector_info(country):
    """주식 정보를 가져오는 함수입니다."""
    response = requests.get(f"{BASE_URL}/sector/calculate/{country}")
    if response.status_code == 200:
        return response.json()
    else:
        return None

BASE_URL = "https://fastapi-app-ozus.onrender.com"

@st.cache(ttl=800)
def get_sector(country):
    response = requests.get(f"{BASE_URL}/sector/fetch/{country}")
    if response.status_code == 200:
        return response.json()
    else:
        return None

def display_sectors(country):
    sector_data = get_sector(country)
    if sector_data:
        df = pd.DataFrame.from_dict(sector_data, orient='index')  # Convert dictionary to DataFrame
        df = df.sort_index()  # Sort by sector names if needed
        st.dataframe(df)  # Display the DataFrame as a table in Streamlit
    else:
        st.write("No sector data available for the specified country.")

# Streamlit UI components
def main():
    st.title("Sector Performance Dashboard")
    st.write("시기별로 각 업종의 수익률을 보여드립니다. 이를 통해 업종의 눌림목과 돌파 시기를 파악할 수 있습니다")
    country = st.selectbox("Choose a country", ["KR", "US"])  # Example countries
    if st.button("Show Sector Data"):
        display_sectors(country)
        cached_update_sector_info(country)

if __name__ == "__main__":
    main()
