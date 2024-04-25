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



import streamlit as st
import pandas as pd

def display_sectors(country):
    sector_data = get_sector(country)
    if sector_data:
        # Convert dictionary to DataFrame and reorder columns
        column_order = ['1 Day', '1 Week', '1 Month', '3 Months', '6 Months', '1 Year']
        df = pd.DataFrame.from_dict(sector_data, orient='index')
        df = df[column_order]  # Reorder columns according to the specified list

        # Round data to two decimals and append '%'
        df = df.applymap(lambda x: f"{x:.2f}%")

        # Sort by sector names if needed
        df = df.sort_index()

        # Custom CSS for styling
        st.markdown("""
            <style>
                .dataframe {
                    font-size: 20px; /* Increase font size */
                    width: 80%; /* Full width */
                    height: 100%;
                    margin-left: auto; /* Centering the table */
                    margin-right: auto;
                }
                .dataframe thead {
                    background-color: #b8e994; /* Light green background for headers */
                }
                .dataframe tbody tr th {
                    background-color: #b8e994; /* Light green background for index */
                }
                .dataframe th, .dataframe td {
                    font-weight: bold; /* Bold font for all cells */
                }
            </style>
            """, unsafe_allow_html=True)

        # Display the DataFrame with container width maximized
        st.dataframe(df.style.background_gradient(), use_container_width=True, height=(len(df) + 1) * 35 + 3)
        #st.dataframe(df.style.highlight_min(axis=0, color='salmon').highlight_max(axis=0, color="green"), use_container_width=True, height=(len(df) + 1) * 35 + 3)
    else:
# Streamlit UI components
        st.write("No sector data available for the specified country.")
def main():
    st.title("업종별 수익률 대시보드")
    st.markdown('''
시기별로 각 업종의 수익률을 보여드립니다.  
이를 통해 업종의 <span style="color: green;">**눌림목**</span>과 <span style="color: green;">**돌파시기**</span>를 파악할 수 있습니다
''', unsafe_allow_html=True)
    country = st.selectbox("Choose a country", ["KR", "US"])  # Example countries
    if st.button("Show Sector Data"):
        display_sectors(country)
        cached_update_sector_info(country)

if __name__ == "__main__":
    main()
