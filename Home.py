import streamlit as st
import requests
import yfinance as yf
import matplotlib.pyplot as plt
from datetime import datetime
import pandas as pd
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore


def get_stock_info(country, symbol):
    """주식 정보를 가져오는 함수입니다."""
    response = requests.get(f"{BASE_URL}/stocks/{country}/{symbol}")
    if response.status_code == 200:
        return response.json()
    else:
        return None


def get_stock_history(symbol, recommendation_date, current_date):
    """주식의 히스토리 데이터를 가져오는 함수입니다."""
    stock = yf.Ticker(symbol)
    hist = stock.history(start=recommendation_date, end=current_date)
    return hist


# 데이터 캐싱을 위한 st.cache_data 데코레이터 사용
cached_get_stock_info = st.cache_data(get_stock_info)
cached_get_stock_history = st.cache_data(get_stock_history)


def create_link(country, symbol):
    """주식 종목의 Yahoo Finance 페이지로의 링크를 생성합니다."""
    if country == 'KR':
        return f"https://finance.naver.com/item/main.naver?code={symbol}"
    else:
        return f"https://finance.yahoo.com/quote/{symbol}"


def show_stock_details(country, symbol, name):
    with st.spinner('주식 정보를 불러오는 중...'):
        # Ensure this function can handle async call
        stock_info = cached_get_stock_info(country, symbol)
        if stock_info:
            st.write(f"### {name} 종목 상세 정보")
            # Assuming `create_link` generates a clickable link to view more details
            st.write(create_link(country, symbol))
            st.write(f"**마지막 종가:** {round(stock_info['last_close'], 2)}")
            st.write(
                f"**추천 날짜 종가:** {round(stock_info['recommendation_close'], 2)}")
            st.write(f"**목표 수익률:** {stock_info['target_return']}")
            color = "green" if stock_info['return_rate'] >= 0 else "red"
            st.markdown(f"<span style='color: {color};'>**현재 수익률: {round(stock_info['return_rate'], 2)}%**</span>", unsafe_allow_html=True)
            st.markdown(f"**추천 이유:**<br> <br> {stock_info['recommendation_reason']}", unsafe_allow_html=True)

            # Parse the dates from string to datetime objects
            dates = pd.to_datetime(list(stock_info['price'].keys()))
            prices = list(stock_info['price'].values())

            plt.figure(figsize=(10, 5))
            plt.plot(dates, prices, label='Close Price',
                     marker='o', linestyle='-', markersize=5)
            plt.title(f"{symbol} Closing Price Chart")
            plt.xlabel("Date")
            plt.ylabel("Close Price (USD)")
            plt.xticks(rotation=45)  # Rotate dates for better readability
            plt.tight_layout()  # Adjust layout to make room for the rotated date labels
            plt.legend()
            st.pyplot(plt)
        else:
            st.error("선택한 종목의 상세 정보를 가져올 수 없습니다.")


# 지수 정보를 가져오는 함수 정의
def get_index_info(ticker_symbol, index_name):
    nasdaq_data = yf.download(ticker_symbol, period="2d")
    # Extract closing prices
    closing_prices = nasdaq_data['Close']
    latest_close = closing_prices.iloc[-1]
    previous_close = closing_prices.iloc[-2]
    change = latest_close - previous_close
    percent_change = (change / previous_close) * 100

    return index_name, latest_close, change, percent_change


# Firebase Admin SDK 초기화 (이미 초기화되어 있는 경우 생략)
if not firebase_admin._apps:
    cred = credentials.Certificate("credentials.json")
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
BASE_URL = "http://127.0.0.1:8000"

# 세션 상태 초기화
if 'selected_symbol' not in st.session_state:
    st.session_state['selected_symbol'] = None

# Streamlit 앱의 기본 설정
st.set_page_config(page_title="주식 추천 사이트",
                   page_icon=":chart_with_upwards_trend:")

st.title("Choi's Stock Choice 📈 ")


st.write('미국 & 한국 주식 시장에서 개인적인 관심 종목들을 선별해 공유하는 공간입니다. ')


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
            st.metric(label=name, value=f"{last_close:,.2f}", delta=f"{change:+,.2f}")
        else:
            st.metric(label=name, value=f"${last_close:,.2f}", delta=f"{change:+,.2f}")
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
            lambda x: x if len(x) <= 25 else x[:25] + '...')

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
        stocks_list = [[info['company_name']] + list(info.values())[1:]  # 첫 번째 값을 'company_name'으로 설정
                       for symbol, info in stocks.items()]
        stocks_df = pd.DataFrame(stocks_list, columns=[
            '회사명', '추천 이유', '추천 날짜', '목표 수익률', '진행 여부'])

        stocks_df['추천 이유'] = stocks_df['추천 이유'].apply(
            lambda x: x if len(x) <= 25 else x[:25] + '...')

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


