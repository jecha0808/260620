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
@st.cache_data(ttl=300) # 5분간 캐싱 (실시간 데이터 갱신)
def get_earthquake_data(min_magnitude):
    # 최근 7일간의 데이터 가져오기
    endtime = datetime.utcnow().isoformat()
    starttime = (datetime.utcnow() - timedelta(days=7)).isoformat()
    
    url = f"https://earthquake.usgs.gov/fdsnws/event/1/query"
    params = {
        "format": "geojson",
        "starttime": starttime,
        "endtime": endtime,
        "minmagnitude": min_magnitude
    }
    
    try:
        response = requests.get(url, params=params)
        data = response.json()
        
        # 데이터프레임 변환용 리스트 생성
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
st.sidebar.title("🛠️ 설정 및 필터")

# OpenAI API Key 입력 (Streamlit Secrets 사용 권장, 없을 시 사이드바 입력 가능)
api_key = st.sidebar.text_input("OpenAI API Key 입력", type="password", value=st.secrets.get("OPENAI_API_KEY", ""))

st.sidebar.markdown("---")
min_mag = st.sidebar.slider("최소 지진 규모(Magnitude)", 1.0, 8.0, 4.5, step=0.1)

# 데이터 로드
df = get_earthquake_data(min_mag)

# --- 메인 화면 레이아웃 ---
st.title("🌋 실시간 글로벌 지진 모니터링 & AI 대피 가이드")
st.caption("USGS(미국 지질조사국)의 실시간 지진 데이터와 OpenAI를 결합한 웹앱입니다.")

# 탭 구성 (시각화 맵 / AI 챗봇)
tab1, tab2 = st.tabs(["🗺️ 전세계 지진 시각화 맵", "💬 지진 안전 AI 챗봇"])

# --- TAB 1: 전세계 지진 시각화 맵 ---
with tab1:
    st.subheader(f"최근 7일간 발생한 규모 {min_mag} 이상의 지진 (총 {len(df)}건)")
    
    if not df.empty:
        # 최근 가장 강한 지진 알림 경고
        max_eq = df.iloc[df['Magnitude'].idxmax()]
        st.warning(f"🚨 **최근 가장 강력한 지진:** {max_eq['Place']} (규모: {max_eq['Magnitude']}) - 발생 시각: {max_eq['Time']}")
        
        # Folium 지도 생성
        m = folium.Map(location=[20, 0], zoom_start=2, tiles="CartoDB positron")
        
        # 지도에 지진 마커 추가
        for _, row in df.iterrows():
            # 규모가 클수록 색상을 붉게, 크기를 크게 설정
            if row['Magnitude'] >= 6.0:
                color = '#ff0000' # 적색
                radius = 12
            elif row['Magnitude'] >= 5.0:
                color = '#ff6600' # 주황
                radius = 8
            else:
                color = '#ffcc00' # 노랑
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
            
        # 스트림릿에 지도 렌더링
        st_folium(m, width="100%", height=500, returned_objects=[])
        
        # 데이터프레임 표 출력
        st.subheader("📊 지진 데이터 상세보기")
        st.dataframe(df[['Time', 'Magnitude', 'Place', 'Depth (km)']], use_container_width=True)
    else:
        st.info("선택한 규모 이상의 지진 데이터가 최근 7일간 존재하지 않습니다.")

# --- TAB 2: 지진 안전 AI 챗봇 ---
with tab2:
    st.subheader("💬 AI 지진 안전 비서")
    st.write("지진 발생 시 대피 요령, 지진 용어 설명, 혹은 현재 발생한 위험 지역에 대해 물어보세요.")
    
    if not api_key:
        st.info("💡 챗봇을 사용하려면 사이드바에 **OpenAI API Key**를 입력하거나 Streamlit Secrets 설정을 완료해주세요.")
    else:
        # OpenAI 클라이언트 초기화
        client = OpenAI(api_key=api_key)
        
        # 세션 상태로 대화 내역 저장
        if "messages" not in st.session_state:
            st.session_state.messages = [
                {"role": "system", "content": "너는 전세계 지진 전문가이자 재난 안전 가이드야. 사용자의 질문에 친절하고 정확하게 답변해줘. 만약 최근 지진 현황을 묻는다면 대답할 수 있는 선에서 침착하게 안내해줘."}
            ]
            
        # 기존 대화 표시 (시스템 메시지 제외)
        for msg in st.session_state.messages:
            if msg["role"] != "system":
                with st.chat_message(msg["role"]):
                    st.write(msg["content"])
                    
        # 사용자 입력창
        if user_input := st.chat_input("질문을 입력하세요... (예: 지진이 났을 때 식탁 밑으로 들어가야 하는 이유가 뭐야?)"):
            # 사용자 메시지 추가 및 화면 표시
            st.session_state.messages.append({"role": "user", "content": user_input})
            with st.chat_message("user"):
                st.write(user_input)
                
            # 최근 지진 정보를 프롬프트에 컨텍스트로 살짝 얹어주는 간단한 RAG 기능 적용
            # "최근 지진" 이라는 키워드가 들어왔을 때 상위 3개 데이터를 넘겨줌
            if "최근" in user_input or "지진 현황" in user_input:
                if not df.empty:
                    top_3 = df.head(3)[['Place', 'Magnitude', 'Time']].to_string()
                    context_prompt = f"\n\n 참고로 현재 USGS API 기준 최근 가장 주요한 지진 3개는 다음과 같아:\n{top_3}"
                    st.session_state.messages[-1]["content"] += context_prompt

            # AI 응답 생성
            with st.chat_message("assistant"):
                with st.spinner("생각 중..."):
                    try:
                        response = client.chat.completions.create(
                            model="gpt-4o-mini", # 가성비가 좋은 최신 모델 사용
                            messages=st.session_state.messages
                        )
                        ans_text = response.choices[0].message.content
                        st.write(ans_text)
                        st.session_state.messages.append({"role": "assistant", "content": ans_text})
                    except Exception as e:
                        st.error(f"OpenAI API 호출 에러: {e}")
