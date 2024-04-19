import streamlit as st
from datetime import date
import streamlit as st
import requests
import yfinance as yf
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from datetime import datetime
import pandas as pd
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import yfinance as yf
from prophet import Prophet
import FinanceDataReader as fdr
from prophet.plot import plot_plotly
from plotly import graph_objs as go
import numpy as np


START = "2020-01-01"
TODAY = date.today().strftime("%Y-%m-%d")

# Firebase Admin SDK 초기화 (이미 초기화되어 있는 경우 생략)
if not firebase_admin._apps:
# Streamlit Cloud의 Secrets에서 설정한 환경 변수 불러오기
    firebase_credentials = dict(st.secrets["FIREBASE_CREDENTIALS"])
    
    # private_key를 명시적으로 문자열로 처리
    firebase_credentials['private_key'] = str(firebase_credentials['private_key'])
    
    cred = credentials.Certificate(firebase_credentials)
    firebase_admin.initialize_app(cred)


db = firestore.client()

def get_ticker_from_firebase(company_name, country):
    """Firebase에서 주어진 회사 이름에 해당하는 티커를 조회합니다."""
    collection_name = 'stockRecommendationsKR' if country == 'KR' else 'stockRecommendationsUS'
    docs = db.collection(collection_name).where(
        'company_name', '==', company_name).get()
    for doc in docs:
        return doc.id  # Document ID가 티커와 일치한다고 가정
    return None
# FastAPI 백엔드 서버 URL
BASE_URL = "https://fastapi-app-ozus.onrender.com"

@st.cache
def load_data(ticker):
    data = yf.download(ticker, START, TODAY)
    data.reset_index(inplace=True)
    return data

@st.cache
def load_data_kr(ticker):
    data = fdr.DataReader(ticker, START, TODAY)
    data.reset_index(inplace=True)
    return data


st.title('머신러닝으로 주가 예측하기')

st.write('이 페이지는 제가 직접 선정한 주식 목록을 바탕으로, 머신러닝 기법을 활용하여 향후 한 달간의 주가 예측을 제공하는 공간입니다.')

# 탭 생성
tab1, tab2, tab3 = st.tabs(["미국 주식", "한국 주식", "Help"])


with tab1:
    st.header("미국 주식")
    country = 'US'

    response = requests.get(f"{BASE_URL}/stocks/{country}")
    if response.status_code == 200:
        stocks = response.json()
        stocks_list = [[info['company_name'], info['recommendation_reason'], info['recommendation_date'], '+' + str(info['target_return']) + '%', info['ing']]
                       for symbol, info in stocks.items()]
        stocks_df = pd.DataFrame(stocks_list, columns=['회사명', '추천 이유', '추천 날짜', '목표 수익률', '진행 여부'])
        st.write("## 상세 정보를 보고 싶은 종목을 선택하세요:")
        symbol_selected = st.selectbox("", stocks_df['회사명'])

        st.markdown(
            """
            <div style='background-color: white; height: 2px; margin: 30px 0;'></div>
            """,
            unsafe_allow_html=True
        )
        st.write("")
        if symbol_selected:
            ticker = get_ticker_from_firebase(symbol_selected, country)
            if ticker:
                st.session_state['selected_symbol'] = ticker

                data = load_data(ticker)

                # Predict forecast with Prophet.
                df_train = data[['Date', 'Close']]
                df_train = df_train.rename(columns={"Date": "ds", "Close": "y"})
                
                # 모델 초기화 with a larger changepoint_prior_scale
                m = Prophet(changepoint_prior_scale=0.1)
                m.fit(df_train)
                future = m.make_future_dataframe(periods=20)
                forecast = m.predict(future)

                                # 예측 결과 요약
                last_price = data['Close'].iloc[-1]
                predicted_price = forecast['yhat'].iloc[-1]
                change_percent = ((predicted_price - last_price) / last_price) * 100

                st.write(f"### 예측 요약")
                st.write(f"현재 가격: ${last_price:.2f}")
                st.write(f"1개월 후 예상 가격: ${predicted_price:.2f}")
                if change_percent > 0:
                    st.markdown(f'<span style="color:green; font-weight:bold;">예상 수익률: {change_percent:.2f}%</span>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<span style="color:red; font-weight:bold;">예상 수익률: {change_percent:.2f}%</span>', unsafe_allow_html=True)

                st.markdown(
                    """
                    <div style='background-color: white; height: 2px; margin: 30px 0;'></div>
                    """,
                    unsafe_allow_html=True
                )



                st.write("")

                                # 서브헤더 추가
                st.subheader('Actual data')
                
                # 그래프 그리기
                fig, ax = plt.subplots()
                ax.plot(data['Date'], data['Open'], label='Stock Open')
                ax.plot(data['Date'], data['Close'], label='Stock Close')
                ax.legend()
                ax.set_xlabel('Date')
                ax.set_ylabel('Price')
                ax.set_title('Stock Prices: Open vs Close')

                # 날짜 레이블의 기울기 조정
                ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))  # 6개월 간격으로 레이블 표시
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))  # 년-월 형식으로 날짜 포맷 설정
                plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)  # 레이블을 45도로 기울임

                
                # Streamlit을 통해 그래프 표시
                st.pyplot(fig)
                
                # Show and plot forecast
                st.subheader('Forecast data')
                st.write(forecast.tail(10))
                
                st.write('Forecast plot for 1 month')

                # fig1 = m.plot(forecast)
                # st.write(fig1)

                fig, ax = plt.subplots()
                m.plot(forecast, ax=ax)
                
                # 과거 6개월 및 앞으로 1개월 데이터 범위 계산
                last_date = forecast['ds'].max()
                start_date = last_date - pd.DateOffset(months=6)
                
                # x축 범위 설정
                ax.set_xlim([start_date, last_date])
                
                # Streamlit에 그래프 표시
                st.pyplot(fig)
                
                st.write("Forecast components")
                fig2 = m.plot_components(forecast)
                st.write(fig2)
            else:
                st.error("선택한 회사의 티커를 찾을 수 없습니다.")
    else:
        st.error("종목 리스트를 가져오는 데 실패했습니다.")
    

with tab2:
    st.header("한국 주식")
    country = 'KR'
    # 여기에 차트와 관련된 컨텐츠를 넣습니다.

    response = requests.get(f"{BASE_URL}/stocks/{country}")
    if response.status_code == 200:
        stocks = response.json()
        stocks_list = [[info['company_name'], info['recommendation_reason'], info['recommendation_date'], '+' + str(info['target_return']) + '%', info['ing']]
                       for symbol, info in stocks.items()]
        stocks_df = pd.DataFrame(stocks_list, columns=['회사명', '추천 이유', '추천 날짜', '목표 수익률', '진행 여부'])
        st.write("## 상세 정보를 보고 싶은 종목을 선택하세요:")
        symbol_selected = st.selectbox("", stocks_df['회사명'])


        st.markdown(
            """
            <div style='background-color: white; height: 2px; margin: 30px 0;'></div>
            """,
            unsafe_allow_html=True
        )
        st.write("")
        if symbol_selected:
            ticker = get_ticker_from_firebase(symbol_selected, country)
            
            if ticker:
                st.session_state['selected_symbol'] = ticker

                data = load_data_kr(ticker)

                # Predict forecast with Prophet.
                df_train = data[['Date', 'Close']]
                df_train = df_train.rename(columns={"Date": "ds", "Close": "y"})
                
                # m = Prophet()
                # m.fit(df_train)
                
                # 모델 초기화 with a larger changepoint_prior_scale
                m = Prophet(changepoint_prior_scale=0.1)
                m.fit(df_train)
                future = m.make_future_dataframe(periods=20)
                forecast = m.predict(future)
                                

                                # 예측 결과 요약
                last_price = data['Close'].iloc[-1]
                predicted_price = forecast['yhat'].iloc[-1]
                change_percent = ((predicted_price - last_price) / last_price) * 100

                st.write(f"### 예측 요약")
                st.write(f"현재 가격: ${last_price:.2f}")
                st.write(f"1개월 후 예상 가격: ${predicted_price:.2f}")
                if change_percent > 0:
                    st.markdown(f'<span style="color:green; font-weight:bold;">예상 수익률: {change_percent:.2f}%</span>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<span style="color:red; font-weight:bold;">예상 수익률: {change_percent:.2f}%</span>', unsafe_allow_html=True)

                st.markdown(
                    """
                    <div style='background-color: white; height: 2px; margin: 30px 0;'></div>
                    """,
                    unsafe_allow_html=True
                )


                st.write("")
                st.subheader('Actual data')
                
                # 그래프 그리기
                fig, ax = plt.subplots()
                ax.plot(data['Date'], data['Open'], label='Stock Open')
                ax.plot(data['Date'], data['Close'], label='Stock Close')
                ax.legend()
                ax.set_xlabel('Date')
                ax.set_ylabel('Price')
                ax.set_title('Stock Prices: Open vs Close')
                
                # 날짜 레이블의 기울기 조정
                ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))  # 6개월 간격으로 레이블 표시
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))  # 년-월 형식으로 날짜 포맷 설정
                plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)  # 레이블을 45도로 기울임

                
                st.pyplot(fig)
                
                # Show and plot forecast
                st.subheader('Forecast data')
                st.write(forecast.tail(10))
                
                st.write('Forecast plot for 1 month')

                # fig1 = m.plot(forecast)
                # st.write(fig1)

                fig, ax = plt.subplots()
                m.plot(forecast, ax=ax)
                
                # 과거 6개월 및 앞으로 1개월 데이터 범위 계산
                last_date = forecast['ds'].max()
                start_date = last_date - pd.DateOffset(months=6)
                
                # x축 범위 설정
                ax.set_xlim([start_date, last_date])
                
                # Streamlit에 그래프 표시
                st.pyplot(fig)
                
                st.write("Forecast components")
                fig2 = m.plot_components(forecast)
                st.write(fig2)
            else:
                st.error("선택한 회사의 티커를 찾을 수 없습니다.")
    else:
        st.error("종목 리스트를 가져오는 데 실패했습니다.")
    

with tab3:
    st.write("""
    
앱의 왼쪽 상단 모서리에 있는 사이드바(▶️)를 열어 다른 페이지로 이동하세요. 사이드바에서 설정과 필터를 변경할 수도 있습니다. 질문이나 제안이 있으시면 이메일, 레딧 또는 디스코드를 통해 연락해주세요.

최신 데이터를 가져오기 위해 앱을 다시 실행하세요. 주식 가격은 5분에서 3시간마다 업데이트되며, 기본적인 정보는 24시간마다 업데이트됩니다. 필터는 사이드바에 있습니다 📊. 제 블로그도 같이 읽어보세요: [Naver Blog](https://blog.naver.com/jangsdaytrading).

제공되는 정보는 '있는 그대로'의 정보 제공 목적으로만 사용되며, 투자의 책임 소재는 당사자에게 있음을 알려드립니다.
    """)
