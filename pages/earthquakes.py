import streamlit as st
import requests
import pandas as pd
import folium
from streamlit_folium import st_folium
from datetime import datetime, timedelta
from openai import OpenAI

# 페이지 기본 설정
st.set_page_config(
    page_title="글로벌 지진 알리미 & 챗봇",
    page_icon="🌋",
    layout="wide"
)

# --- 1. USGS API 데이터 로드 함수 ---
@st.cache_data(ttl=300) # 5분간 캐싱
def get_earthquake_data():
    endtime = datetime.utcnow().isoformat()
    starttime = (datetime.utcnow() - timedelta(days=7)).isoformat()
    
    url = f"https://earthquake.usgs.gov/fdsnws/event/1/query"
    params = {
        "format": "geojson",
        "starttime": starttime,
        "endtime": endtime,
        "minmagnitude": 1.0
    }
    
    try:
        response = requests.get(url, params=params)
        data = response.json()
        
        features = data.get("features", [])
        eq_list = []
        for f in features:
            props = f["properties"]
            geom = f["geometry"]
            eq_list.append({
                "Place": props["place"],
                "Magnitude": props["mag"],
                "Time": pd.to_datetime(props["time"], unit="ms"),
                "Latitude": geom["coordinates"][1],
                "Longitude": geom["coordinates"][0],
                "Depth (km)": geom["coordinates"][2],
                "URL": props["url"]
            })
        return pd.DataFrame(eq_list)
    except Exception as e:
        st.error(f"지진 데이터를 불러오는 중 오류 발생: {e}")
        return pd.DataFrame()

# --- 사이드바 설정 ---
st.sidebar.title("🛠️ 설정 및 검색")

# OpenAI API Key 입력
api_key = st.sidebar.text_input("OpenAI API Key 입력", type="password", value=st.secrets.get("OPENAI_API_KEY", ""))

st.sidebar.markdown("---")

# 지역 및 국가 검색창
search_query = st.sidebar.text_input("🔍 지역/국가 검색 (예: Japan, California)", "").strip()

# 최소 규모 슬라이더
min_mag = st.sidebar.slider("최소 지진 규모(Magnitude)", 1.0, 8.0, 4.0, step=0.1)

# 원본 데이터 로드
raw_df = get_earthquake_data()

# --- 데이터 필터링 로직 ---
if not raw_df.empty:
    # 1. 규모 필터 적용
    df = raw_df[raw_df['Magnitude'] >= min_mag]
    
    # 2. 검색어 필터 적용 (대소문자 구분 없음)
    if search_query:
        df = df[df['Place'].str.contains(search_query, case=False, na=False)]
else:
    df = pd.DataFrame()

# --- 메인 화면 레이아웃 ---
st.title("🌋 실시간 글로벌 지진 모니터링 & AI 대피 가이드")
st.caption("USGS(미국 지질조사국)의 실시간 지진 데이터와 OpenAI를 결합한 웹앱입니다.")

# ⭐ 탭 정의 (에러 방지를 위해 확실하게 메인 상단에 위치)
tab1, tab2 = st.tabs(["🗺️ 전세계 지진 시각화 맵", "💬 지진 안전 AI 챗봇"])

# --- TAB 1: 전세계 지진 시각화 맵 ---
with tab1:
    search_msg = f" 중 '{search_query}' 검색 결과" if search_query else ""
    st.subheader(f"최근 7일간 발생한 규모 {min_mag} 이상 지진{search_msg} (총 {len(df)}건)")
    
    # 1. 데이터가 완전히 비어있지 않을 때만 로직 실행
    if not df.empty:
        # 최근 가장 강한 지진 알림 경고
        max_eq = df.iloc[df['Magnitude'].idxmax()]
        st.warning(f"🚨 **현재 조건 내 가장 강력한 지진:** {max_eq['Place']} (규모: {max_eq['Magnitude']}) - 발생 시각: {max_eq['Time']}")
        
        # 지도 중심점 설정
        map_center = [df.iloc[0]['Latitude'], df.iloc[0]['Longitude']] if search_query else [20, 0]
        zoom_level = 5 if search_query else 2
        
        m = folium.Map(location=map_center, zoom_start=zoom_level, tiles="CartoDB positron")
        
        # 지도에 지진 마커 추가
        for _, row in df.iterrows():
            if row['Magnitude'] >= 6.0:
                color = '#ff0000'
                radius = 12
            elif row['Magnitude'] >= 5.0:
                color = '#ff6600'
                radius = 8
            else
