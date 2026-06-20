import streamlit as st
import pandas as pd
import random

# 1. 샘플 식당 데이터 생성
@st.cache_data
def load_data():
    # 실제 앱에서는 이 부분을 CSV 파일을 읽거나 API를 호출하는 코드로 바꿀 수 있습니다.
    data = {
        "지역": ["강남", "강남", "강남", "홍대", "홍대", "홍대", "명동", "명동", "이태원", "이태원"],
        "메뉴분류": ["한식", "일식", "양식", "한식", "일식", "양식", "한식", "중식", "양식", "이색음식"],
        "식당이름": ["강남불고기", "스시마스터 강남", "테라스파스타", "홍대돼지국밥", "라멘팩토리", "연남동스테이크", "명동칼국수", "취영루 명동점", "이태원버거", "타코하우스"],
        "대표메뉴": ["바싹불고기", "모듬초밥", "고르곤졸라 & 까르보나라", "부산식 돼지국밥", "돈코츠라멘", "티본 스테이크", "칼국수와 만두", "짜장면 & 탕수육", "수제 치즈버거", "비프 타코"],
        "별점": [4.5, 4.8, 4.2, 4.6, 4.4, 4.7, 4.5, 4.3, 4.6, 4.4]
    }
    return pd.DataFrame(data)

df = load_data()

# 2. 앱 헤더 설정
st.set_page_config(page_title="오늘 뭐 먹지? 식당 추천 앱", page_icon="🍴", layout="centered")
st.title("🍴 오늘 뭐 먹지? 맞춤 식당 추천")
st.markdown("메뉴 고민부터 식당 검색까지 한번에 해결해보세요!")

st.markdown("---")

# 3. 1단계: 결정장애를 위한 메뉴 무작위 추천
st.header("🎲 1단계: 메뉴가 고민되시나요?")
if st.button("오늘의 추천 메뉴 뽑기"):
    all_menus = df["대표메뉴"].unique()
    picked_menu = random.choice(all_menus)
    # 선택된 메뉴의 카테고리 찾기
    category = df[df["대표메menu" if "대표메menu" in df else "대표메뉴"] == picked_menu]["메뉴분류"].values[0]
    
    st.success(f"오늘 추천하는 메뉴는 **[{category}] {picked_menu}** 입니다! 어떠신가요?")

st.markdown("---")

# 4. 2단계: 지역 및 메뉴 선택 필터
st.header("🔍 2단계: 원하는 식당 찾기")

col1, col2 = st.columns(2)

with col1:
    # 지역 선택 (전체 옵션 추가)
    location_list = ["전체"] + list(df["지역"].unique())
    selected_location = st.selectbox("어디서 드시나요? (지역 선택)", location_list)

with col2:
    # 메뉴 분류 선택 (전체 옵션 추가)
    menu_list = ["전체"] + list(df["메뉴분류"].unique())
    selected_menu = st.selectbox("어떤 장르가 당기시나요? (메뉴 선택)", menu_list)

# 5. 3단계: 조건에 맞는 식당 필터링 및 출력
filtered_df = df.copy()

if selected_location != "전체":
    filtered_df = filtered_df[filtered_df["지역"] == selected_location]

if selected_menu != "전체":
    filtered_df = filtered_df[filtered_df["메뉴분류"] == selected_menu]

st.markdown("### 📋 추천 식당 리스트")

if filtered_df.empty:
    st.info("선택하신 조건에 맞는 식당이 없습니다. 다른 조건으로 검색해보세요!")
else:
    # 별점이 높은 순으로 정렬하여 보기 좋게 인덱스 재설정
    results = filtered_df.sort_values(by="별점", ascending=False).reset_index(drop=True)
    
    # 식당 카드로 예쁘게 출력
    for idx, row in results.iterrows():
        # 별점 개수만큼 ⭐️ 아이콘 생성
        stars = "⭐" * int(row['별점']) + (" 점" if row['별점'] % 1 == 0 else "점")
        
        with st.container():
            st.markdown(f"#### {idx+1}. {row['식당이름']} ({row['지역']})")
            st.text(f"🔹 분류: {row['메뉴분류']}  |  대표메뉴: {row['대표메뉴']}")
            st.markdown(f"🏅 **별점: {row['별점']}** ({stars})")
            st.markdown("""<hr style="height:1px;border:none;color:#e0e0e0;background-color:#e0e0e0;" />""", unsafe_url_allowed=True)
