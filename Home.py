

import streamlit as st
import requests
import yfinance as yf
import matplotlib.pyplot as plt
from datetime import datetime
import pandas as pd
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore, storage
import os
import json

# 데이터프레임을 받아 스타일을 적용하고 인덱스를 숨기는 함수
def display_dataframe(df):
    st.dataframe(df.style.apply(highlight_status, axis=1).hide_index())


# 데이터프레임에 스타일을 적용하는 함수
def highlight_status(row):
    if row['진행 여부'] == '성공':
        return ['background-color: green']*len(row)
    elif row['진행 여부'] == '실패':
        return ['background-color: red']*len(row)
    else:
        return ['background-color: none']*len(row)


custom_css = """
<style>
    .metric-container {
        background-color: #000000;  /* Black background */
        color: #ffffff;             /* White text */
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 10px;
        text-align: center;
        box-shadow: 0 4px 8px 0 rgba(255,255,255,0.2); /* Light shadow for depth */
        transition: 0.3s;
    }
    .metric-container:hover {
        box-shadow: 0 8px 16px 0 rgba(255,255,255,0.2);
    }
    .metric-label {
        font-size: 16px;
        margin-bottom: 5px;
        font-weight: bold;
    }
    .metric-value {
        font-size: 24px;
    }
</style>
"""

@st.cache(ttl=180)
def cached_get_stock_info(country, symbol):
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
            st.write(f"**사이트:** {create_link(country, symbol)}")
            st.write(f"**마지막 종가:** {round((stock_info['last_close']), 2)}")
            st.write(
                f"**추천 날짜 종가:** {round((stock_info['recommendation_close']), 2)}")
            st.write(f"**목표 수익률:** {stock_info['target_return']}")
            color = "green" if stock_info['return_rate'] >= 0 else "red"
            st.markdown(f"<span style='color: {color};'>**현재 수익률: {round(stock_info['return_rate'], 2)}%**</span>", unsafe_allow_html=True)

            # if st.button("머신러닝 모델이 도출한 " + name + " 의 기대수익률은?"):
            #     st.switch_page("pages/1_머신러닝을 활용한 주가예측.py")

            with st.container():

                col1, col2, col3 = st.columns([1, 2, 1])  # 중앙 정렬을 위해 컬럼을 사용합니다.
                with col2:  # 중앙 컬럼에 버튼을 위치시킵니다.
                    if st.button(f"머신러닝 모델로 도출한 {name}의 예상 수익률은?"):
                        st.switch_page("pages/1_머신러닝을 활용한 주가예측.py")
                
                st.write("")  # 여백 추가



            
            file_path = f"{name}/스크린샷_myfile.png"
            # 스토리지 버킷에서 파일에 대한 참조 생성
            blob = bucket.blob(file_path)
            
            # 파일의 공개 URL 생성 (영구적인 공개 URL)
            blob.make_public()
            st.image(blob.public_url , caption='차트 분석 이미지')
            st.write("")

            #여기다
            
            metric_keys = ['Sharpe Ratio', 'Maximum Drawdown', 'Beta', 'Alpha', 'Treynor Ratio']
            col1, col2, col3, col4, col5 = st.columns(5)
            columns = [col1, col2, col3, col4, col5]
        
            for col, key in zip(columns, metric_keys):
                value = round(stock_info['financial_metrics'][key], 3)
                with col:
                    st.markdown(custom_css, unsafe_allow_html=True)  # Apply custom CSS
                    st.markdown(
                        f"""
                        <div class="metric-container">
                            <div class="metric-label">
                                {key}
                            </div>
                            <div class="metric-value">
                                {value}
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )




            
            st.write("")
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




def get_index_info(ticker_symbol, index_name):
    try:
        # 주말 및 공휴일을 고려하여 최대 7일간의 데이터를 가져옵니다.
        nasdaq_data = yf.download(ticker_symbol, period="7d")
        # 데이터 프레임에서 마지막으로 사용 가능한 두 개의 데이터를 추출합니다.
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
    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred, {
        'storageBucket': 'stockrecommendationforme.appspot.com'
    })


db = firestore.client()

# Storage 버킷 접근
bucket = storage.bucket('stockrecommendationforme.appspot.com')


def get_ticker_from_firebase(company_name, country):
    """Firebase에서 주어진 회사 이름에 해당하는 티커를 조회합니다."""
    collection_name = 'stockRecommendationsKR' if country == 'KR' else 'stockRecommendationsUS'
    docs = db.collection(collection_name).where(
        'company_name', '==', company_name).get()
    for doc in docs:
        return doc.id  # Document ID가 티커와 일치한다고 가정
    return None

def get_image_url(file_path):
    # 스토리지 내 파일에 대한 참조 생성
    blob = bucket.blob(file_path)
    
    # 파일의 공개 URL 생성
    # 옵션: 서명된 URL 생성, 유효 기간 설정 가능
    url = blob.generate_signed_url(version='v4', expiration=datetime.timedelta(seconds=300), method='GET')
    return url




# FastAPI 백엔드 서버 URL
BASE_URL = "https://fastapi-app-ozus.onrender.com"

# 세션 상태 초기화
if 'selected_symbol' not in st.session_state:
    st.session_state['selected_symbol'] = None




#==========================================
# Define the custom CSS for the page header design with modifications
header_css = """
<style>
    .header-container {
        text-align: center;
        margin-bottom: 20px;
    }
    .header-title {
        font-size: 48px;
        font-weight: bold;
        margin-bottom: 0;
    }
    .header-subtitle {
        font-size: 24px;
         color: green;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-top: 0;
    }
    .header-subtitle:before,
    .header-subtitle:after {
        content: '';
        flex: 1;
        border-bottom: 3px solid green;
        margin: 0px 5px; /* Adjust the spacing around the lines */
    }

</style>
"""

# Streamlit app main code
# ...
st.set_page_config(page_title="주식 추천 사이트",
                   page_icon=":chart_with_upwards_trend:", layout="wide")

# Insert the custom header at the very top of the page
st.markdown(header_css, unsafe_allow_html=True)
st.markdown(
    """
    <div class="header-container">
        <h1 class="header-title">CHOI'S STOCK CHOICE</h1>
        <p class="header-subtitle">US & KR MARKET</p>
    </div>
    """,
    unsafe_allow_html=True
)
#==========================================

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
    options=["전체", "진행중", "성공", "실패"],
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
            st.metric(label=name, value=f"{last_close:,.2f}", delta=f"{percent_change:+,.2f}%")
        else:
            st.metric(label=name, value=f"${last_close:,.2f}", delta=f"{percent_change:+,.2f}%")
        n = n + 1

st.write("")
st.write("")

st.write('''
📈 **미국 & 한국 주식 시장 관심 종목** 📈

개인적인 관심 종목들을 선별해 공유하는 공간입니다.

- 목표 수익률 : 제 관심 종목은 한 달간의 목표 수익률을 설정하고 있습니다.
- 성공 조건 : 만약 한 달 이내에 이 목표를 달성하면 수익을 실현합니다.
- 실패 조건 : 반대로, 한 달 내에 목표 수익률의 절반 이상 손실 혹은 주요 지지선 이탈시 즉시 손절을 진행하고 울면서 나옵니다.
''')



st.markdown(
    """
    <div style='background-color: white; height: 2px; margin: 30px 0;'></div>
    """,
    unsafe_allow_html=True
)
st.write("")


#---------------------------------------------
def calculate_success_rate():
    response = requests.get(f"{BASE_URL}/stocks/success/")
    if response.status_code == 200:
        stocks = response.json()
        total_success = stocks['성공']
        total_failure = stocks['실패']
        ing = stocks['진행중']
        total_finished = total_success + total_failure
        if total_finished > 0:
            success_rate = (total_success / total_finished) * 100
        else:
            success_rate = 0
        return success_rate, total_success, total_failure, ing
    
success_rate, total_success, total_failure, ing = calculate_success_rate()
#---------------------------------------------

# 성과 통계 제목
st.write("### 평가 정확도 📊 ")

# 성과 통계를 나란히 표시하기 위한 컬럼 설정
cols = st.columns(4)

with cols[0]:
    st.metric(label="Success Rate", value=f"{success_rate:.2f}%", delta=None)

with cols[1]:
    st.metric(label="Total Success", value=f"{total_success}", delta=None)

with cols[2]:
    st.metric(label="Total Failure", value=f"{total_failure}", delta=None)

with cols[3]:
    st.metric(label="In Progress", value=f"{ing}", delta=None)


st.markdown(
    """
    <div style='background-color: white; height: 1px; margin: 30px 0;'></div>
    """,
    unsafe_allow_html=True
)
st.write("")

# 제목
st.write("### 선정 종목 👀")


# 탭 생성
tab1, tab2, tab3 = st.tabs(["미국 주식", "한국 주식", "Help"])

with tab1:
    st.write(" #### 미국 주식")
    country = 'US'
    # 여기에 Magic Formula와 관련된 컨텐츠를 넣습니다.

    # 모든 주식 종목 가져오기
    response = requests.get(f"{BASE_URL}/stocks/{country}")
    #===============================
    if response.status_code == 200:
        stocks = response.json()
        stocks_list = [
            [
                info['company_name'],
                info['recommendation_reason'],
                info['recommendation_date'],
                f"{info['target_return']}%",
                info['ing']
            ]
            for symbol, info in stocks.items()
        ]
        stocks_df = pd.DataFrame(
            stocks_list,
            columns=['회사명', '추천 이유', '추천 날짜', '목표 수익률', '진행 여부']
        )
        stocks_df['추천 이유'] = stocks_df['추천 이유'].apply(
            lambda x: x if len(x) <= 35 else x[:35] + '...'
        )
        if status_option == "전체":
            filtered_df = stocks_df
        else:
            filtered_df = stocks_df[stocks_df['진행 여부'] == status_option]

        # 데이터프레임을 스타일링하고 너비를 조정하며 인덱스를 숨깁니다.
        # 데이터프레임을 스타일링하고 너비를 조정하며 인덱스를 숨깁니다.
        # st.dataframe(
        #     filtered_df.style.apply(highlight_status, axis=1),
        #     width=700,  # 원하는 너비로 조정하세요
        #     height=300,  # 원하는 높이로 조정하세요
        # )
        filtered_df = filtered_df.set_index(filtered_df.columns[0])
        st.dataframe(filtered_df.style.apply(highlight_status, axis=1))
        # st.write(filtered_df.to_html(index=False), unsafe_allow_html=True)  # 인덱스 없이 HTML로 변환하여 표시
        
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
            show_stock_details(country, ticker, symbol_selected) #여기다
        else:
            st.error("선택한 회사의 티커를 찾을 수 없습니다.")
    else:
        st.error("종목 리스트를 가져오는 데 실패했습니다.")


with tab2:
    st.write(" #### 한국 주식")
    country = 'KR'
    # 여기에 차트와 관련된 컨텐츠를 넣습니다.

    # 모든 주식 종목 가져오기
    response = requests.get(f"{BASE_URL}/stocks/{country}")
    #===============================
    if response.status_code == 200:
        stocks = response.json()
        stocks_list = [
            [
                info['company_name'],
                info['recommendation_reason'],
                info['recommendation_date'],
                f"{info['target_return']}%",
                info['ing']
            ]
            for symbol, info in stocks.items()
        ]
        stocks_df = pd.DataFrame(
            stocks_list,
            columns=['회사명', '추천 이유', '추천 날짜', '목표 수익률', '진행 여부']
        )
        stocks_df['추천 이유'] = stocks_df['추천 이유'].apply(
            lambda x: x if len(x) <= 35 else x[:35] + '...'
        )
        if status_option == "전체":
            filtered_df = stocks_df
        else:
            filtered_df = stocks_df[stocks_df['진행 여부'] == status_option]

        # 데이터프레임을 스타일링하고 너비를 조정하며 인덱스를 숨깁니다.
        # 데이터프레임을 스타일링하고 너비를 조정하며 인덱스를 숨깁니다.
        # st.dataframe(
        #     filtered_df.style.apply(highlight_status, axis=1),
        #     width=700,  # 원하는 너비로 조정하세요
        #     height=300,  # 원하는 높이로 조정하세요
        # )
        filtered_df = filtered_df.set_index(filtered_df.columns[0])
        st.dataframe(filtered_df.style.apply(highlight_status, axis=1))
        # st.write(filtered_df.to_html(index=False), unsafe_allow_html=True)  # 인덱스 없이 HTML로 변환하여 표시
        
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



