
    # AI 추천 아이콘 및 소개
    col1, col2 = st.columns([1, 5])
    with col1:
        st.image("https://i.imgur.com/8JfVh5H.png", width=80)
    with col2:
        st.markdown("### AI가 추천하는 맞춤 코스")
        st.markdown("여행 일정과 취향을 입력하시면 최적의 관광 코스를 추천해 드립니다.")
    
    # 여행 정보 입력 섹션
    st.markdown("---")
    st.subheader("여행 정보 입력")
    
    col1, col2 = st.columns(2)
    
    with col1:
        start_date = st.date_input("여행 시작일")
    
    with col2:
        end_date = st.date_input("여행 종료일", value=start_date)
    
    # 일수 계산
    delta = (end_date - start_date).days + 1
    st.caption(f"총 {delta}일 일정")
    
    col1, col2 = st.columns(2)
    
    with col1:
        num_people = st.number_input("여행 인원", min_value=1, max_value=10, value=2)
    
    with col2:
        include_children = st.checkbox("아이 동반")
    
    # 여행 스타일 선택
    st.markdown("### 여행 스타일")
    travel_styles = ["활동적인", "휴양", "맛집", "쇼핑", "역사/문화", "자연"]
    
    # 3열로 버튼식 선택
    cols = st.columns(3)
    selected_styles = []
    
    for i, style in enumerate(travel_styles):
        with cols[i % 3]:
            if st.checkbox(style, key=f"style_{style}"):
                selected_styles.append(style)
    
    # 코스 생성 버튼
    st.markdown("---")
    generate_course = st.button("코스 생성하기", type="primary", use_container_width=True)
    
    if generate_course:
        if not selected_styles:
            st.warning("최소 하나 이상의 여행 스타일을 선택해주세요.")
        else:
            with st.spinner("최적의 관광 코스를 생성 중입니다..."):
                # 로딩 효과를 위한 딜레이
                time.sleep(2)
                
                # 스타일에 따른 코스 추천
                if "역사/문화" in selected_styles:
                    course_type = "문화 코스"
                elif "쇼핑" in selected_styles or "맛집" in selected_styles:
                    course_type = "쇼핑 코스"
                elif "휴양" in selected_styles or "자연" in selected_styles:
                    course_type = "자연 코스"
                else:
                    course_type = "대중적 코스"
                
                # 현재 데이터 확인
                if not hasattr(st.session_state, 'all_markers') or not st.session_state.all_markers:
                    with st.spinner("관광지 데이터를 로드하는 중..."):
                        all_markers = load_excel_files(st.session_state.language)
                        if all_markers:
                            st.session_state.all_markers = all_markers
                        else:
                            # 데이터가 없을 경우 기본 코스 사용
                            all_markers = []
                else:
                    all_markers = st.session_state.all_markers
                
                # 기본 코스에서 추천
                recommended_course = RECOMMENDATION_COURSES.get(course_type, [])
                
                # 충분한 데이터가 있으면 실제 마커 데이터 사용
                if all_markers and len(all_markers) > 10:
                    # 카테고리별 장소 필터링
                    filtered_markers = []
                    if "역사/문화" in selected_styles:
                        filtered_markers.extend([m for m in all_markers if "역사" in m.get('category', '').lower() or "문화" in m.get('category', '').lower() or "미술관" in m.get('category', '').lower()])
                    if "쇼핑" in selected_styles:
                        filtered_markers.extend([m for m in all_markers if "쇼핑" in m.get('category', '').lower() or "기념품" in m.get('category', '').lower()])
                    if "맛집" in selected_styles:
                        filtered_markers.extend([m for m in all_markers if "음식" in m.get('category', '').lower() or "맛집" in m.get('category', '').lower()])
                    if "자연" in selected_styles:
                        filtered_markers.extend([m for m in all_markers if "자연" in m.get('category', '').lower() or "공원" in m.get('category', '').lower()])
                    
                    # 중복 제거
                    seen = set()
                    filtered_markers = [m for m in filtered_markers if not (m['title'] in seen or seen.add(m['title']))]
                    
                    # 장소가 충분하면 사용, 그렇지 않으면 기본 코스에 추가
                    if filtered_markers and len(filtered_markers) >= delta * 3:
                        random.shuffle(filtered_markers)
                        recommended_course = []
                        for i in range(min(delta * 3, len(filtered_markers))):
                            recommended_course.append(filtered_markers[i]['title'])
                    elif filtered_markers:
                        # 기본 코스에 필터링된 장소 추가
                        for m in filtered_markers[:5]:
                            if m['title'] not in recommended_course:
                                recommended_course.append(m['title'])
                
                st.success("코스 생성 완료!")
                
                # 코스 표시
                st.markdown("## 추천 코스")
                st.markdown(f"**{course_type}** - {delta}일 일정")
                
                # 코스 마커 및 정보 준비
                course_markers = []
                
                # 일별 코스 표시
                for day in range(1, min(delta+1, 4)):  # 최대 3일까지
                    st.markdown(f"### Day {day}")
                    
                    # 일별 방문 장소 선택
                    day_spots = []
                    if day == 1:
                        day_spots = recommended_course[:3]  # 첫날 3곳
                    elif day == 2:
                        day_spots = recommended_course[3:6] if len(recommended_course) > 3 else recommended_course[:3]
                    else:  # 3일차 이상
                        day_spots = recommended_course[6:9] if len(recommended_course) > 6 else recommended_course[:3]
                    
                    # 표시할 장소가 없으면 기본 추천
                    if not day_spots:
                        day_spots = ["경복궁", "남산서울타워", "명동"]
                    
                    timeline = st.columns(len(day_spots))
                    
                    for i, spot_name in enumerate(day_spots):
                        # 장소 정보 찾기 (마커 데이터에서 또는 기본값 사용)
                        spot_info = None
                        if all_markers:
                            spot_info = next((m for m in all_markers if m['title'] == spot_name), None)
                        
                        # 방문 시간대 설정
                        time_slots = ["09:00-12:00", "13:00-16:00", "16:00-19:00"]
                        time_slot = time_slots[i % 3]
                        
                        with timeline[i]:
                            st.markdown(f"**{time_slot}**")
                            st.markdown(f"**{spot_name}**")
                            
                            if spot_info:
                                st.caption(f"분류: {spot_info.get('category', '관광지')}")
                                
                                # 경로에 추가
                                course_markers.append(spot_info)
                            else:
                                st.caption("관광지")
                
                # 지도에 코스 표시
                st.markdown("### 🗺️ 코스 지도")
                
                # 필요한 경우 API 키 확인
                api_key = st.session_state.google_maps_api_key
                if not api_key:
                    st.error("Google Maps API 키가 설정되지 않았습니다.")
                    api_key = st.text_input("Google Maps API 키를 입력하세요", type="password")
                    if api_key:
                        st.session_state.google_maps_api_key = api_key
                
                # 코스 마커 표시
                if course_markers:
                    # 지도 중심 좌표 계산 (마커들의 평균)
                    center_lat = sum(m['lat'] for m in course_markers) / len(course_markers)
                    center_lng = sum(m['lng'] for m in course_markers) / len(course_markers)
                    
                    # 지도 표시
                    show_google_map(
                        api_key=api_key,
                        center_lat=center_lat,
                        center_lng=center_lng,
                        markers=course_markers,
                        zoom=12,
                        height=500,
                        language=st.session_state.language
                    )
                else:
                    # 실제 좌표 데이터가 없는 경우
                    st.warning("코스 장소의 좌표 정보가 없어 지도에 표시할 수 없습니다.")
                
                # 일정 저장 버튼
                if st.button("이 코스 저장하기", use_container_width=True):
                    if 'saved_courses' not in st.session_state:
                        st.session_state.saved_courses = []
                    
                    st.session_state.saved_courses.append({
                        "type": course_type,
                        "days": delta,
                        "places": recommended_course,
                        "date": start_date.strftime("%Y-%m-%d")
                    })
                    
                    st.success("코스가 저장되었습니다!")

def show_history_page():
    """관광 이력 페이지 표시"""
    page_header("나의 관광 이력")
    
    # 뒤로가기 버튼
    if st.button("← 메뉴로 돌아가기"):
        change_page("menu")
        rerun()
    
    username = st.session_state.username
    
    # 사용자 레벨과 경험치 표시
    user_xp = st.session_state.user_xp.get(username, 0)
    user_level = calculate_level(user_xp)
    xp_percentage = calculate_xp_percentage(user_xp)
    
    col1, col2, col3 = st.columns([1, 3, 1])
    
    with col1:
        st.image("https://i.imgur.com/W3UVTgZ.png", width=100)  # 사용자 아이콘
    
    with col2:
        st.markdown(f"## 레벨 {user_level}")
        st.progress(xp_percentage / 100)
        st.markdown(f"**총 경험치: {user_xp} XP** (다음 레벨까지 {XP_PER_LEVEL - (user_xp % XP_PER_LEVEL)} XP)")
    
    with col3:
        st.write("")  # 빈 공간
    
    # 방문 통계
    if username in st.session_state.user_visits and st.session_state.user_visits[username]:
        visits = st.session_state.user_visits[username]
        
        total_visits = len(visits)
        unique_places = len(set([v['place_name'] for v in visits]))
        total_xp = sum([v.get('xp_gained', 0) for v in visits])
        
        st.markdown("---")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("총 방문 횟수", f"{total_visits}회")
        
        with col2:
            st.metric("방문한 장소 수", f"{unique_places}곳")
        
        with col3:
            st.metric("획득한 경험치", f"{total_xp} XP")
        
        # 방문 기록 목록 표시
        st.markdown("---")
        st.subheader("📝 방문 기록")
        
        # 정렬 옵션
        tab1, tab2, tab3 = st.tabs(["전체", "최근순", "경험치순"])
        
        with tab1:
            display_visits(visits)
        
        with tab2:
            recent_visits = sorted(visits, key=lambda x: x['timestamp'], reverse=True)
            display_visits(recent_visits)
        
        with tab3:
            xp_visits = sorted(visits, key=lambda x: x.get('xp_gained', 0), reverse=True)
            display_visits(xp_visits)
        
        # 방문한 장소를 지도에 표시
        st.markdown("---")
        st.subheader("🗺️ 방문 지도")
        
        # 필요한 경우 API 키 확인
        api_key = st.session_state.google_maps_api_key
        if not api_key:
            st.error("Google Maps API 키가 설정되지 않았습니다.")
            api_key = st.text_input("Google Maps API 키를 입력하세요", type="password")
            if api_key:
                st.session_state.google_maps_api_key = api_key
        
        # 방문 장소 마커 생성
        visit_markers = []
        for visit in visits:
            marker = {
                'lat': visit["latitude"],
                'lng': visit["longitude"],
                'title': visit["place_name"],
                'color': 'purple',  # 방문한 장소는 보라색으로 표시
                'info': f"방문일: {visit['date']}<br>획득 XP: +{visit.get('xp_gained', 0)}",
                'category': '방문한 장소'
            }
            visit_markers.append(marker)
        
        if visit_markers:
            # 지도 중심 좌표 계산 (마커들의 평균)
            center_lat = sum(m['lat'] for m in visit_markers) / len(visit_markers)
            center_lng = sum(m['lng'] for m in visit_markers) / len(visit_markers)
            
            # Google Maps 표시
            show_google_map(
                api_key=api_key,
                center_lat=center_lat,
                center_lng=center_lng,
                markers=visit_markers,
                zoom=12,
                height=500,
                language=st.session_state.language
            )
        else:
            st.info("지도에 표시할 방문 기록이 없습니다.")
    else:
        st.info("아직 방문 기록이 없습니다. 지도에서 장소를 방문하면 여기에 기록됩니다.")
        
        # 예시 데이터 생성 버튼
        if st.button("예시 데이터 생성"):
            # 샘플 방문 데이터
            sample_visits = [
                {
                    "place_name": "경복궁",
                    "latitude": 37.5796,
                    "longitude": 126.9770,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "xp_gained": 80
                },
                {
                    "place_name": "남산서울타워",
                    "latitude": 37.5511,
                    "longitude": 126.9882,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "xp_gained": 65
                },
                {
                    "place_name": "명동",
                    "latitude": 37.5635,
                    "longitude": 126.9877,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "xp_gained": 25
                }
            ]
            
            if username not in st.session_state.user_visits:
                st.session_state.user_visits[username] = []
            
            st.session_state.user_visits[username] = sample_visits
            
            # XP 부여
            total_xp = sum([v['xp_gained'] for v in sample_visits])
            if username not in st.session_state.user_xp:
                st.session_state.user_xp[username] = 0
            st.session_state.user_xp[username] += total_xp
            
            st.success(f"예시 데이터가 생성되었습니다! +{total_xp} XP 획득!")
            rerun()

#################################################
# 메인 앱 로직
#################################################

# 데이터 폴더 생성
data_folder = Path("data")
if not data_folder.exists():
    data_folder.mkdir(parents=True, exist_ok=True)

# CSS 스타일 적용
apply_custom_css()

# 세션 상태 초기화
init_session_state()

# 페이지 라우팅
def main():
    # 로그인 상태에 따른 페이지 제어
    if not st.session_state.logged_in and st.session_state.current_page != "login":
        st.session_state.current_page = "login"
    
    # 현재 페이지에 따라 해당 함수 호출
    if st.session_state.current_page == "login":
        show_login_page()
    elif st.session_state.current_page == "menu":
        show_menu_page()
    elif st.session_state.current_page == "map":
        show_map_page()
    elif st.session_state.current_page == "course":
        show_course_page()
    elif st.session_state.current_page == "history":
        show_history_page()
    else:
        show_menu_page()  # 기본값

if __name__ == "__main__":
    main()
