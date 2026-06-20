# --- TAB 1: 전세계 지진 시각화 맵 ---
with tab1:
    search_msg = f" 중 '{search_query}' 검색 결과" if search_query else ""
    st.subheader(f"최근 7일간 발생한 규모 {min_mag} 이상 지진{search_msg} (총 {len(df)}건)")
    
    # 데이터가 '존재할 때만' 가장 강한 지진을 추출하도록 수정!
    if not df.empty:
        max_eq = df.iloc[df['Magnitude'].idxmax()]
        st.warning(f"🚨 **현재 조건 내 가장 강력한 지진:** {max_eq['Place']} (규모: {max_eq['Magnitude']}) - 발생 시각: {max_eq['Time']}")
        
        # Folium 지도 생성 (검색된 결과가 있으면 첫 번째 결과 위치로 중심점 이동, 없으면 세계 지도 중심)
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
            
        # 지도 렌더링
        st_folium(m, width="100%", height=500, returned_objects=[])
        
        # 데이터프레임 표 출력
        st.subheader("📊 지진 데이터 상세보기")
        st.dataframe(df[['Time', 'Magnitude', 'Place', 'Depth (km)']], use_container_width=True)
    else:
        # 데이터가 없을 때는 안전하게 안내 메시지만 출력!
        st.info("검색 조건에 맞는 지진 데이터가 최근 7일간 존재하지 않습니다. 검색어나 규모를 조절해 보세요.")
