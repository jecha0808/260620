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
@st.cache_data(ttl=300)
def get_earthquake_data():
    endtime = datetime.utcnow().isoformat()
    starttime = (datetime.utcnow() - timedelta(days=7)).isoformat()
    
    base_url = "https://earthquake.usgs.gov/fdsnws/event/1/query".strip()
    
    params = {
        "format": "geojson",
        "starttime": starttime,
        "endtime": endtime,
        "minmagnitude": 1.0
    }
    
    try:
        response = requests.get(base_url, params=params)
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
    df = raw_df[raw_df['Magnitude'] >= min_mag].copy()
    if search_query:
        df = df[df['Place'].str.contains(search_query, case=False, na=False)]
else:
    df = pd.DataFrame()

# --- 메인 화면 레이아웃 ---
st.title("🌋 실시간 글로벌 지진 모니터링 & AI 대피 가이드")
st.caption("USGS(미국 지질조사국)의 실시간 지진 데이터와 OpenAI를 결합한 웹앱입니다.")

# 탭 정의
tab1, tab2 = st.tabs(["🗺️ 전세계 지진 시각화 맵", "💬 지진 안전 AI 챗봇"])

# --- TAB 1: 전세계 지진 시각화 맵 ---
with tab1:
    search_msg = f" 중 '{search_query}' 검색 결과" if search_query else ""
    st.subheader(f"최근 7일간 발생한 규모 {min_mag} 이상 지진{search_msg} (총 {len(df)}건)")
    
    # 변경 포인트 🚨: 에러를 유발하는 idxmax()를 쓰지 않고 데이터 개수로만 조건 판단
    if len(df) > 0:
        # 정렬 알고리즘으로 안전하게 첫 번째(최대값) 추출
        sorted_df = df.sort_values(by='Magnitude', ascending=False)
        max_eq = sorted_df.iloc[0]
        
        st.warning(f"🚨 **현재 조건 내 가장 강력한 지진:** {max_eq['Place']} (규모: {max_eq['Magnitude']}) - 발생 시각: {max_eq['Time']}")
        
        # 지도 중심점 설정
        map_center = [df.iloc[0]['Latitude'], df.iloc[0]['Longitude']] if search_query else [20, 0]
        zoom_level = 5 if search_query else 2
        
        m = folium.Map(location=map_center, zoom_start=zoom_level, tiles="CartoDB positron")
        
        for _, row in df.iterrows():
            if row['Magnitude'] >= 6.0:
                color = '#ff0000'
                radius = 12
            elif row['Magnitude'] >= 5.0:
                color = '#ff6600'
                radius = 8
            else:
                color = '#ffcc00'
                radius = 5
                
            popup_text = f"""
            <b>위치:</b> {row['Place']}<br>
            <b>규모:</b> {row['Magnitude']}<br>
            <b>시간:</b> {row['Time'].strftime('%Y-%m-%d %H:%M:%S')}<br>
            <b>깊이:</b> {row['Depth (km)']} km<br>
            <a href='{row['URL']}' target='_blank'>상세 정보 보기</a>
            """
            
            folium.CircleMarker(
                location=[row['Latitude'], row['Longitude']],
                radius=radius,
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.6,
                popup=folium.Popup(popup_text, max_width=300)
            ).add_to(m)
            
        st_folium(m, width="100%", height=500, returned_objects=[])
        
        st.subheader("📊 지진 데이터 상세보기")
        st.dataframe(df[['Time', 'Magnitude', 'Place', 'Depth (km)']], use_container_width=True)
    else:
        st.info("검색 조건에 맞는 지진 데이터가 최근 7일간 존재하지 않습니다. 검색어나 규모를 조절해 보세요.")

# --- TAB 2: 지진 안전 AI 챗봇 ---
with tab2:
    st.subheader("💬 AI 지진 안전 비서")
    st.write("지진 발생 시 대피 요령, 지진 용어 설명, 혹은 현재 발생한 위험 지역에 대해 물어보세요.")
    
    if not api_key:
        st.info("💡 챗봇을 사용하려면 사이드바에 **OpenAI API Key**를 입력하거나 Streamlit Secrets 설정을 완료해주세요.")
    else:
        client = OpenAI(api_key=api_key)
        
        if "messages" not in st.session_state:
            st.session_state.messages = [
                {"role": "system", "content": "너는 전세계 지진 전문가이자 재난 안전 가이드야. 사용자의 질문에 친절하고 정확하게 답변해줘."}
            ]
            
        for msg in st.session_state.messages:
            if msg["role"] != "system":
                with st.chat_message(msg["role"]):
                    st.write(msg["content"])
                    
        if user_input := st.chat_input("질문을 입력하세요..."):
            st.session_state.messages.append({"role": "user", "content": user_input})
            with st.chat_message("user"):
                st.write(user_input)
                
            if ("최근" in user_input or "지진 현황" in user_input) and not df.empty:
                top_3 = df.head(3)[['Place', 'Magnitude', 'Time']].to_string()
                context_prompt = f"\n\n 참고로 현재 사용자가 검색한 조건 내 주요 지진 3개는 다음과 같아:\n{top_3}"
                st.session_state.messages[-1]["content"] += context_prompt

            with st.chat_message("assistant"):
                with st.spinner("생각 중..."):
                    try:
                        response = client.chat.completions.create(
                            model="gpt-4o-mini",
                            messages=st.session_state.messages
                        )
                        ans_text = response.choices[0].message.content
                        st.write(ans_text)
                        st.session_state.messages.append({"role": "assistant", "content": ans_text})
                    except Exception as e:
                        st.error(f"OpenAI API 호출 에러: {e}")
