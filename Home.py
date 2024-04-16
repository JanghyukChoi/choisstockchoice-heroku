import streamlit as st
import requests
import yfinance as yf
import matplotlib.pyplot as plt
from datetime import datetime
import pandas as pd
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import os
import json


# FastAPI backend server URL
BASE_URL = "https://fastapi-app-ozus.onrender.com"

@st.cache_data(ttl=60)
def cached_get_stock_info(country, symbol):
    response = requests.get(f"{BASE_URL}/stocks/{country}/{symbol}")
    if response.status_code == 200:
        return response.json()
    else:
        return None

def create_link(country, symbol):
    if country == 'KR':
        return f"https://finance.naver.com/item/main.naver?code={symbol}"
    else:
        return f"https://finance.yahoo.com/quote/{symbol}"

def show_stock_details(country, symbol, name):
    with st.spinner('Loading stock information...'):
        stock_info = cached_get_stock_info(country, symbol)
        if stock_info:
            st.write(f"### {name} Stock Details")
            st.write(create_link(country, symbol))
            st.write(f"**Last Close Price:** {round(stock_info['last_close'], 2)}")
            st.write(f"**Recommendation Close Price:** {round(stock_info['recommendation_close'], 2)}")
            st.write(f"**Target Return:** {stock_info['target_return']}")
            color = "green" if stock_info['return_rate'] >= 0 else "red"
            st.markdown(f"<span style='color: {color};'>**Current Return: {round(stock_info['return_rate'], 2)}%**</span>", unsafe_allow_html=True)
            st.markdown(f"**Recommendation Reason:**<br><br>{stock_info['recommendation_reason']}", unsafe_allow_html=True)
            dates = pd.to_datetime(list(stock_info['price']._keys()))
            prices = list(stock_info['price'].values())
            plt.figure(figsize=(10, 5))
            plt.plot(dates, prices, label='Close Price', marker='o', linestyle='-', markersize=5)
            plt.title(f"{symbol} Closing Price Chart")
            plt.xlabel("Date")
            plt.ylabel("Close Price (USD)")
            plt.xticks(rotation=45)
            plt.tight_layout()
            plt.legend()
            st.pyplot(plt)
        else:
            st.error("Failed to fetch details for the selected stock.")


def get_index_info(ticker_symbol, index_name):
    try:
        nasdaq_data = yf.download(ticker_symbol, period="20d")
        closing_prices = nasdaq_data['Close'].dropna()
        if len(closing_prices) >= 2:
            latest_close = closing_prices.iloc[-1]
            previous_close = closing_prices.iloc[-2]
            change = latest_close - previous_close
            percent_change = (change / previous_close) * 100
            return index_name, latest_close, change, percent_change
        else:
            raise ValueError("Not enough data to calculate changes.")
    except Exception as e:
        st.error(f"Error retrieving data for {index_name}: {str(e)}")
        return index_name, None, None, None




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

# 세션 상태 초기화
if 'selected_symbol' not in st.session_state:
    st.session_state['selected_symbol'] = None



# Streamlit 앱의 기본 설정
st.set_page_config(page_title="주식 추천 사이트",
                   page_icon=":chart_with_upwards_trend:",layout="wide")



st.title("Choi's Stock Choice 📈 ")


st.write('''
미국 & 한국 주식 시장에서 개인적인 관심 종목들을 선별해 공유하는 공간입니다. 

제가 추천하는 종목들은 한 달간의 목표 수익률을 설정하고 있으며, 만약 한 달 이내에 이 목표를 달성하면 수익을 실현합니다. 반대로, 한 달 내에 목표 수익률의 절반 이상 손실이 발생하면 즉시 손절매를 진행합니다. 
''')


# 나스닥, S&P 500, 다우존스 정보 가져오기
indices_info = [
    get_index_info("^IXIC", "NASDAQ"),
    get_index_info("^GSPC", "S&P 500"),
    get_index_info("^KS11", "KOSPI"),
    get_index_info("^KQ11", "KOSDAQ")
]

# 사이드바 설정
st.sidebar.header("Main Page")

status_option = st.sidebar.selectbox(
    "목표수익률 달성 여부",
    options=["전체", "진행중", "완료", "실패"],
    index=0  # '전체'를 기본값으로 설정
)

# 지수 정보를 표시하는 컨테이너 생성
container = st.container()
col1, col2, col3, col4 = container.columns(4)
n = 0
# 각 지수 정보를 해당 컬럼에 표시
for col, (name, last_close, change, percent_change) in zip([col1, col2, col3, col4], indices_info):
    # with col:
    #     st.subheader(name)
    #     st.metric(label="Last Close", value=f"${last_close:,.2f}")
    #     st.metric(label="Change", value=f"{
    #               change:+,.2f} ({percent_change:+,.2f}%)", delta_color="inverse")
    with col:
        if n >= 2:
            st.metric(label=name, value=f"{last_close:,.2f}", delta=f"{change:+,.2f}",  label_visibility="collapsed")
        else:
            st.metric(label=name, value=f"${last_close:,.2f}", delta=f"{change:+,.2f}",  label_visibility="collapsed")
        n = n + 1


st.markdown(
    """
    <div style='background-color: white; height: 2px; margin: 30px 0;'></div>
    """,
    unsafe_allow_html=True
)
st.write("")


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
        stocks_list = [[info['company_name']] + [info['recommendation_reason']] + [info['recommendation_date']] + [info['target_return']] + [info['ing']]  # 첫 번째 값을 'company_name'으로 설정
                       for symbol, info in stocks.items()]
        stocks_df = pd.DataFrame(stocks_list, columns=[
            '회사명', '추천 이유', '추천 날짜', '목표 수익률', '진행 여부'])

        stocks_df['추천 이유'] = stocks_df['추천 이유'].apply(
            lambda x: x if len(x) <= 35 else x[:35] + '...')

        # 필터링된 데이터 표시 (수정)
        if status_option == "전체":
            filtered_df = stocks_df
        else:
            filtered_df = stocks_df[stocks_df['진행 여부'] == status_option]

        st.table(filtered_df)  # 수정: stocks_df -> filtered_df

        st.markdown(
            """
        <div style='background-color: white; height: 2px; margin: 30px 0;'></div>
        """,
            unsafe_allow_html=True
        )
        st.write("")

        st.write("### 상세 정보를 보고 싶은 종목을 선택하세요:")
        symbol_selected = st.selectbox("", stocks_df['회사명'])

    if symbol_selected:
        # 회사 이름에 해당하는 티커를 Firebase에서 조회
        ticker = get_ticker_from_firebase(symbol_selected, country)
        if ticker:
            st.session_state['selected_symbol'] = ticker
            show_stock_details(country, ticker, symbol_selected)
        else:
            st.error("선택한 회사의 티커를 찾을 수 없습니다.")
    else:
        st.error("종목 리스트를 가져오는 데 실패했습니다.")


with tab2:
    st.header("한국 주식")
    country = 'KR'
    # 여기에 차트와 관련된 컨텐츠를 넣습니다.

    # 모든 주식 종목 가져오기
    response = requests.get(f"{BASE_URL}/stocks/{country}")
    if response.status_code == 200:
        stocks = response.json()
        stocks_list = [[info['company_name']] + [info['recommendation_reason']] + [info['recommendation_date']] + [info['target_return']] + [info['ing']]  # 첫 번째 값을 'company_name'으로 설정
                       for symbol, info in stocks.items()]
        stocks_df = pd.DataFrame(stocks_list, columns=[
            '회사명', '추천 이유', '추천 날짜', '목표 수익률', '진행 여부'])

        stocks_df['추천 이유'] = stocks_df['추천 이유'].apply(
            lambda x: x if len(x) <= 35 else x[:35] + '...')

        # 필터링된 데이터 표시 (수정)
        if status_option == "전체":
            filtered_df = stocks_df
        else:
            filtered_df = stocks_df[stocks_df['진행 여부'] == status_option]

        st.table(filtered_df)  # 수정: stocks_df -> filtered_df

        st.markdown(
            """
        <div style='background-color: white; height: 2px; margin: 30px 0;'></div>
        """,
            unsafe_allow_html=True
        )
        st.write("")

        st.write("### 상세 정보를 보고 싶은 종목을 선택하세요:")
        symbol_selected = st.selectbox("", stocks_df['회사명'])

        if symbol_selected:
            # 회사 이름에 해당하는 티커를 Firebase에서 조회
            ticker = get_ticker_from_firebase(symbol_selected, country)
            if ticker:
                st.session_state['selected_symbol'] = ticker
                show_stock_details(country, ticker, symbol_selected)
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






