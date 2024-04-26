import streamlit as st
import pandas as pd
import pydeck as pdk
# ... Rest of your mapping demo code ...

st.set_page_config(page_title="Mapping Demo", page_icon="🌍")
# ... Rest of your code for the mapping demo ...


st.markdown("# About this website")
st.sidebar.header("About this website & About Me ")

st.write("")
st.write("")

st.write("""
         
**Choi's Stock Choice** 웹사이트는 개인적인 관심사에서 출발한 프로젝트로, 미국과 한국의 주식 시장에서 ***저의 관심을 끈 종목들을 선별해 공유하는 공간***입니다. 
         
이전에는 네이버 블로그를 통해 이런 정보를 나누었지만, 관심 종목들의 정보를 한눈에 볼 수 있는 플랫폼을 마련하고자 이 웹사이트를 개설했습니다. 더 나아가, 실시간 수익률을 포함하여 종목별 성과를 직관적으로 확인할 수 있게 하여 이를 통해 저만의 분석 방법과 생각을 투명하게 나누고자 합니다. 💪

본 웹사이트의 주된 목적은 저와 같은 투자자들이 기술적 분석, 재무제표 해석 등 다양한 방법론을 통해 자신만의 투자 전략을 개발할 수 있도록 지원하는 데 있습니다. 
         
이는 어떤 형태로든 투자 권유를 목적으로 하지 않으며, 순수하게 정보 공유와 학습을 위한 플랫폼으로 운영됩니다. 📝

앞으로도 증시 동향, 기업 분석 보고서 등 보다 심층적인 내용을 다루어 방문자 여러분께 유익한 정보를 제공할 계획입니다. 이 공간이 많은 개인투자자들의 투자 지식을 확장하는 데 조금이나마 도움이 되길 바라며, 함께 성장해 나가는 과정에서 의견과 피드백을 나눌 수 있기를 기대합니다 😄 
         
감사합니다.
         """
         )
st.write("")

# Adding "About Me" section
st.sidebar.markdown("## About Me")

# Personal details and credentials
st.sidebar.write(f"""
- **학교**: 한양대학교 경제금융학과
- **이메일**: kevin9921@naver.com
- **자격증**:
  - 투자자산운용사
  - TOEIC 965
- **이력**:
  - Google ML 부트캠프
  - 미쉐린 데이터분석팀 인턴
  - 한국투자증권 잠실 PB지점 인턴
  - UFIC 연합투자동아리 16대 회장
""")
