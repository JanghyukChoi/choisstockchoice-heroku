import streamlit as st
from datetime import date
import streamlit as st
import requests
import yfinance as yf
import matplotlib.pyplot as plt
from datetime import datetime
import pandas as pd
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import yfinance as yf
from prophet import Prophet
from prophet.plot import plot_plotly
from plotly import graph_objs as go

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


st.title('Stock Forecast App')

# 탭 생성
tab1, tab2, tab3 = st.tabs(["미국 주식", "한국 주식", "Help"])

with tab1:
    st.header("미국 주식")
    country = 'US'
    # 여기에 Magic Formula와 관련된 컨텐츠를 넣습니다.

    # 모든 주식 종목 가져오기
    response = requests.get(f"{BASE_URL}/stocks/{country}")
    if response.status_code == 200:
        stocks = response.json()
        stocks_list = [[info['company_name']] + [info['recommendation_reason']] + [info['recommendation_date']] + [str('+') + str(info['target_return']) + '%'] + [info['ing']]  # 첫 번째 값을 'company_name'으로 설정
                       for symbol, info in stocks.items()]
        stocks_df = pd.DataFrame(stocks_list, columns=[
            '회사명', '추천 이유', '추천 날짜', '목표 수익률', '진행 여부'])

        st.write("### 상세 정보를 보고 싶은 종목을 선택하세요:")
        symbol_selected = st.selectbox("", stocks_df['회사명'])

    if symbol_selected:
        # 회사 이름에 해당하는 티커를 Firebase에서 조회
        ticker = get_ticker_from_firebase(symbol_selected, country)
        if ticker:
                st.session_state['selected_symbol'] = ticker
                show_stock_details(country, ticker, symbol_selected)

	        data_load_state = st.text('Loading data...')
	        data = load_data(selected_stock)
	        data_load_state.text('Loading data... done!')
		
	        st.subheader('Raw data')
	        st.write(data.tail())
	        plot_raw_data()

	    # Predict forecast with Prophet.
		df_train = data[['Date','Close']]
		df_train = df_train.rename(columns={"Date": "ds", "Close": "y"})
		
		m = Prophet()
		m.fit(df_train)
		future = m.make_future_dataframe(periods=period)
		forecast = m.predict(future)
		
		# Show and plot forecast
		st.subheader('Forecast data')
		st.write(forecast.tail())
		    
		st.write(f'Forecast plot for 1 months')
		fig1 = plot_plotly(m, forecast)
		st.plotly_chart(fig1)
		
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
        stocks_list = [[info['company_name']] + [info['recommendation_reason']] + [info['recommendation_date']] + [str('+') + str(info['target_return']) + '%'] + [info['ing']]  # 첫 번째 값을 'company_name'으로 설정
                       for symbol, info in stocks.items()]
        stocks_df = pd.DataFrame(stocks_list, columns=[
            '회사명', '추천 이유', '추천 날짜', '목표 수익률', '진행 여부'])

        st.write("### 상세 정보를 보고 싶은 종목을 선택하세요:")
        symbol_selected = st.selectbox("", stocks_df['회사명'])

    if symbol_selected:
        # 회사 이름에 해당하는 티커를 Firebase에서 조회
        ticker = get_ticker_from_firebase(symbol_selected, country)
        if ticker:
                st.session_state['selected_symbol'] = ticker
                show_stock_details(country, ticker, symbol_selected)

	        data_load_state = st.text('Loading data...')
	        data = load_data(selected_stock)
	        data_load_state.text('Loading data... done!')
		
	        st.subheader('Raw data')
	        st.write(data.tail())
	        plot_raw_data()

	    # Predict forecast with Prophet.
		df_train = data[['Date','Close']]
		df_train = df_train.rename(columns={"Date": "ds", "Close": "y"})
		
		m = Prophet()
		m.fit(df_train)
		future = m.make_future_dataframe(periods=period)
		forecast = m.predict(future)
		
		# Show and plot forecast
		st.subheader('Forecast data')
		st.write(forecast.tail())
		    
		st.write(f'Forecast plot for 1 months')
		fig1 = plot_plotly(m, forecast)
		st.plotly_chart(fig1)
		
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


