########### 지도 시각화

# from streamlit_js_eval import get_geolocation

# st.title("🗺️ 서울시 공공 위치 데이터 통합 지도")

# # ----------------------------------------
# # 🌐 언어 선택 (오른쪽 상단 위치 느낌으로 배치)
# col1, col2, col3 = st.columns([6, 1, 2])  # 비율 조정: col3이 오른쪽

# with col3:
#     selected_language = st.selectbox("🌏 Language", ["🇰🇷 한국어", "🇺🇸 English", "🇨🇳 中文"])
# # 日本語

# # 선택된 언어에 따른 내부 코드 매핑
# language_map = {
#     "🇰🇷 한국어": "한국어",
#     "🇺🇸 English": "영어",
#     "🇨🇳 中文": "중국어"
# #    "🇯🇵 日本語": "일본어"
# }
# language = language_map[selected_language]


# # 📁 파일 및 좌표 컬럼 정보 설정 (언어별 분리)
# csv_info_ko = {
#     "서울시 외국인전용 관광기념품 판매점 정보(국문).csv": ("위치정보(Y)", "위치정보(X)"),
#     "서울시 문화행사 공공서비스예약 정보(국문).csv": ("장소Y좌표", "장소X좌표"),
#     "서울시립미술관 전시정보 (국문).csv": ("y좌표", "x좌표"),
#     "서울시 체육시설 공연행사 정보 (국문).csv": ("y좌표", "x좌표"),
#     "서울시 종로구 관광데이터 정보 (국문).csv": ("Y 좌표", "X 좌표")
# }
# excel_info_ko = {
#     "서울시 자랑스러운 한국음식점 정보 (한국어,영어).xlsx": ("Latitude", "Longitude")
# }

# csv_info_en = {
#     "서울시 외국인전용 관광기념품 판매점 정보(영문).csv": ("Location Information (Y Coordinate)", "Location Information (X Coordinate)"),
#     "서울시 문화행사 공공서비스예약 정보(영문).csv": ("Location Y Coordinate", "Location X Coordinate"),
#     "서울시립미술관 전시정보 (영문).csv": ("y Coordinate", "x Coordinate"),
#     "서울시 체육시설 공연행사 정보 (영문).csv": ("Y Coordinate", "X Coordinate"),
#     "서울시 종로구 관광데이터 정보 (영문).csv": ("Y 좌표", "X 좌표")
# }

# csv_info_cn = {
#     "서울시 외국인전용 관광기념품 판매점 정보(중문).csv": ("位置坐标(Y)","位置坐标(X)"),
#     "서울시 문화행사 공공서비스예약 정보(중문).csv": ("场所Y坐标", "场所X坐标"),
#     "서울시립미술관 전시정보 (중문).csv": ("y坐标","x坐标"),
#     "서울시 체육시설 공연행사 정보 (중문).csv": ("y 坐标","x 坐标"),
#     "서울시 종로구 관광데이터 정보 (중문).csv": ("Y 좌표", "X 좌표")
# }

# ############################ 나중에  사용할거임
# # 명칭(이름) 컬럼명 매핑
# # name_column_map = {
# #     "한국어": "명칭(한국어)",
# #     "영어": "명칭(영어)"
# #     # "중국어": "명칭(중국어)",  # 아직 없으니 기본 사용
# #     # "일본어": "명칭"   # 향후 확장 대비
# # }
# ############################ 나중에  사용할거임


# # 🧱 아이콘 및 색상 지정 (공통)
# icon_config = {
#     # 관광기념품 판매점
#     "서울시 외국인전용 관광기념품 판매점 정보(국문).csv": ("blue", "gift"),
#     "서울시 외국인전용 관광기념품 판매점 정보(영문).csv": ("blue", "gift"),
#     "서울시 외국인전용 관광기념품 판매점 정보(중문).csv": ("blue", "gift"),

#     # 문화행사
#     "서울시 문화행사 공공서비스예약 정보(국문).csv": ("purple", "star"),
#     "서울시 문화행사 공공서비스예약 정보(영문).csv": ("purple", "star"),
#     "서울시 문화행사 공공서비스예약 정보(중문).csv": ("purple", "star"),

#     # 미술관 전시
#     "서울시립미술관 전시 정보 (국문).csv": ("orange", "paint-brush"),
#     "서울시립미술관 전시 정보 (영문).csv": ("orange", "paint-brush"),
#     "서울시립미술관 전시 정보 (중문).csv": ("orange", "paint-brush"),

#     # 체육시설 공연행사
#     "서울시 체육시설 공연행사 정보(국문).csv": ("cadetblue", "music"),
#     "서울시 체육시설 공연행사 정보(영문).csv": ("cadetblue", "music"),
#     "서울시 체육시설 공연행사 정보(중문).csv": ("cadetblue", "music"),

#     # 종로구 관광정보
#     "서울시 종로구 관광데이터 정보 (국문).csv": ("red", "camera"),
#     "서울시 종로구 관광데이터 정보 (영문).csv": ("red", "camera"),
#     "서울시 종로구 관광데이터 정보 (중문).csv": ("red", "camera"),

#     # 자랑스러운 한국음식점 (엑셀, 언어공통)
#     "서울시 자랑스러운 한국음식점 정보 (한국어,영어).xlsx": ("green", "cutlery")
# }


# # 언어에 따라 전체 파일 리스트 구성
# if language == "한국어":
#     all_info = {**csv_info_ko, **excel_info_ko}
# elif language == "영어":
#     all_info = csv_info_en
# elif language == "중국어":
#     all_info = csv_info_cn

# # ----------------------------------------
# # 🧭 사용자 현재 위치
# user_location = get_geolocation()

# ############ st.write("📦 사용자 위치 데이터:", user_location)

# if (
#     user_location
#     and "coords" in user_location
#     and "latitude" in user_location["coords"]
#     and "longitude" in user_location["coords"]
# ):
#     lat = user_location["coords"]["latitude"]
#     lng = user_location["coords"]["longitude"]
#     center = [lat, lng]
#     st.success(f"📍 현재 위치: {center}")
# else:
#     center = [37.5665, 126.9780]  # 서울 중심
#     st.warning("⚠️ 현재 위치 정보를 가져올 수 없어 기본 위치로 설정합니다.")

# # ----------------------------------------
# # 📌 카테고리 선택
# category_options = ["전체"] + list(all_info.keys())
# selected_category = st.selectbox(
#     "📂 확인할 카테고리를 선택하세요:",
#     category_options,
#     format_func=lambda x: "전체 보기" if x == "전체" else x.replace(".csv", "").replace(".xlsx", "")
# )

# # ----------------------------------------
# # 🗺️ 지도 생성
# m = folium.Map(location=center, zoom_start=12)
# marker_cluster = MarkerCluster().add_to(m)

# # ----------------------------------------

# # 📍 마커 생성 함수
# def add_markers(file_name, lat_col, lng_col):
#     color, icon = icon_config.get(file_name, ("gray", "info-sign"))
#     try:
#         # 파일 읽기
#         if file_name.endswith(".csv"):
#             if "영어" in file_name or "중국" in file_name:
#                 df = pd.read_csv(file_name, encoding="cp949")
#             elif "영문" in file_name:
#                 df = pd.read_csv(file_name, encoding="utf-8-sig")
#             else:
#                 df = pd.read_csv(file_name)
#         else:
#             df = pd.read_excel(file_name)

#         # 데이터 절반만 사용
#         df_half = df.head(len(df) // 2)

#         for _, row in df_half.iterrows():
#             lat, lng = row[lat_col], row[lng_col]
#             if pd.notna(lat) and pd.notna(lng):
#                 directions_url = f"https://www.google.com/maps/dir/?api=1&origin=My+Location&destination={lat},{lng}"
#                 popup_html = f'<a href="{directions_url}" target="_blank">📍 길찾기 (구글 지도)</a>'
#                 folium.Marker(
#                     location=[lat, lng],
#                     tooltip=file_name.replace(".csv", "").replace(".xlsx", ""),
#                     popup=folium.Popup(popup_html, max_width=300),
#                     icon=folium.Icon(color=color, icon=icon, prefix="fa")
#                 ).add_to(marker_cluster)
#     except Exception as e:
#         st.error(f"❌ {file_name} 처리 중 오류 발생: {e}")

# # ----------------------------------------
# # 🎯 선택된 카테고리만 지도에 표시
# if selected_category == "전체":
#     for file, (lat_col, lng_col) in all_info.items():
#         add_markers(file, lat_col, lng_col)
# else:
#     lat_col, lng_col = all_info[selected_category]
#     add_markers(selected_category, lat_col, lng_col)

# # ----------------------------------------
# # 📍 지도 출력
# folium_static(m, width=1000, height=600)







###########################################



###################################################


# import requests
# import xml.etree.ElementTree as ET


# # 인증키와 API 기본 URL 설정
# API_KEY = "616d73735a6c6b613338414d616d78"
# BASE_URL = f"http://openapi.seoul.go.kr:8088/{API_KEY}/xml/culturalSpaceInfo"

# # Streamlit UI
# st.title("서울시 문화공간 정보 전체 보기")

# start = st.number_input("시작 인덱스", min_value=1, value=1)
# end = st.number_input("끝 인덱스", min_value=start, value=start + 9)

# if st.button("데이터 불러오기"):
#     url = f"{BASE_URL}/{start}/{end}/"
#     response = requests.get(url)

#     if response.status_code == 200:
#         root = ET.fromstring(response.content)

#         rows = []
#         for item in root.findall(".//row"):
#             row_data = {
#                 "번호": item.findtext("NUM"),
#                 "주제분류": item.findtext("SUBJCODE"),
#                 "문화시설명": item.findtext("FAC_NAME"),
#                 "주소": item.findtext("ADDR"),
#                 "위도": item.findtext("X_COORD"),
#                 "경도": item.findtext("Y_COORD"),
#                 "전화번호": item.findtext("PHNE"),
#                 "팩스번호": item.findtext("FAX"),
#                 "홈페이지": item.findtext("HOMEPAGE"),
#                 "관람시간": item.findtext("OPENHOUR"),
#                 "관람료": item.findtext("ENTR_FEE"),
#                 "휴관일": item.findtext("CLOSEDAY"),
#                 "개관일자": item.findtext("OPEN_DAY"),
#                 "객석수": item.findtext("SEAT_CNT"),
#                 "대표이미지": item.findtext("MAIN_IMG"),
#                 "기타사항": item.findtext("ETC_DESC"),
#                 "시설소개": item.findtext("FAC_DESC"),
#                 "무료구분": item.findtext("ENTRFREE"),
#                 "지하철": item.findtext("SUBWAY"),
#                 "버스정거장": item.findtext("BUSSTOP"),
#                 "노란버스": item.findtext("YELLOW"),
#                 "초록버스": item.findtext("GREEN"),
#                 "파란버스": item.findtext("BLUE"),
#                 "빨간버스": item.findtext("RED"),
#                 "공항버스": item.findtext("AIRPORT")
#             }
#             rows.append(row_data)

#         if rows:
#             df = pd.DataFrame(rows)
#             st.dataframe(df)
#         else:
#             st.warning("데이터가 없습니다.")
#     else:
#         st.error(f"API 요청 실패. 상태 코드: {response.status_code}")

######### 이 위는 api로 조회하는거



######### 이 아래는 업데이트가 되서 새 데이터가 생기는지 보려고 하는거


# import streamlit as st
# import requests
# import xml.etree.ElementTree as ET
# import pandas as pd
# import os
# from datetime import date

# # 설정
# API_KEY = "616d73735a6c6b613338414d616d78"
# BASE_URL = f"http://openapi.seoul.go.kr:8088/{API_KEY}/xml/culturalSpaceInfo/1/1/"
# CSV_FILE = "total_count_log.csv"

# st.title("서울시 문화공간 정보 - 데이터 업데이트 체크 (CSV 저장)")

# # 오늘 날짜
# today = str(date.today())

# # API 호출
# response = requests.get(BASE_URL)

# if response.status_code == 200:
#     root = ET.fromstring(response.content)
#     total_count = root.findtext(".//list_total_count")
#     st.info(f"📦 오늘의 total_count: {total_count}")

#     # 기존 CSV 파일이 있다면 불러오기
#     if os.path.exists(CSV_FILE):
#         df_log = pd.read_csv(CSV_FILE)
#     else:
#         df_log = pd.DataFrame(columns=["date", "total_count"])

#     # 이전 값 확인
#     if not df_log.empty:
#         last_row = df_log.iloc[-1]
#         st.write(f"🕓 마지막 저장된 날짜: {last_row['date']}, total_count: {last_row['total_count']}")

#         if str(last_row["total_count"]) != total_count:
#             st.success("✅ 데이터가 변경되었습니다!")
#         else:
#             st.warning("ℹ️ total_count에는 변화가 없습니다.")
#     else:
#         st.info("처음 실행 중입니다.")

#     # 이미 오늘자 기록이 있으면 추가 저장은 하지 않음
#     if today not in df_log["date"].values:
#         df_log.loc[len(df_log)] = [today, total_count]
#         df_log.to_csv(CSV_FILE, index=False)
#         st.success("📄 오늘자 데이터가 CSV에 저장되었습니다.")
#     else:
#         st.info("오늘자 기록은 이미 저장되어 있습니다.")

#     st.dataframe(df_log)
# else:
#     st.error("API 요청 실패")

################




















# # CSV 파일 경로
# data_path = "hotel_fin_0331_1.csv"
# df = pd.read_csv(data_path, encoding='euc-kr')

# # 페이지 설정
# st.set_page_config(page_title="호텔 리뷰 감성 요약", layout="wide")
# st.title("🏠 STAY-VIEW💬")

# # 감성 항목
# aspect_columns = ['소음', '가격', '위치', '서비스', '청결', '편의시설']

# # ---------------- 지역 선택 ----------------
# regions = sorted(df['Location'].unique())
# selected_region = st.radio("📍 지역을 선택하세요", regions, horizontal=True)

# region_df = df[df['Location'] == selected_region]
# hotels = region_df['Hotel'].unique()
# selected_hotel = st.selectbox("🏠 호텔을 선택하세요", ["전체 보기"] + list(hotels))




# # ---------------- 사이드바: 정렬 기준 및 Top 5 ----------------
# st.sidebar.title("🔍 항목별 상위 호텔")
# aspect_to_sort = st.sidebar.selectbox("정렬 기준", aspect_columns)

# sorted_hotels = (
#     region_df.sort_values(by=aspect_to_sort, ascending=False)
#     .drop_duplicates(subset='Hotel')
# )

# top_hotels = sorted_hotels[['Hotel', aspect_to_sort]].head(5)
# st.sidebar.markdown("#### 🏅 정렬 기준 Top 5")
# for idx, row in enumerate(top_hotels.itertuples(), 1):
#     st.sidebar.write(f"👑**{idx}등!** {row.Hotel}")

# # ---------------- 구글 지도 생성 함수 ----------------

# def create_google_map(dataframe, zoom_start=12):
#     center_lat = dataframe['Latitude'].mean()
#     center_lon = dataframe['Longitude'].mean()
    
#     m = folium.Map(
#         location=[center_lat, center_lon], 
#         zoom_start=zoom_start, 
#         tiles="OpenStreetMap"
# #         Stamen Toner, Stamen Terrain, Stamen Watercolor 얘네는 attr 안적음
        
#         # tiles="https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}", 
#         # attr="Google"
#     )
    
#     if len(dataframe) > 1:
#         marker_cluster = MarkerCluster().add_to(m)
#         for idx, row in dataframe.iterrows():
#             hotel_name = row['Hotel']
#             lat = row['Latitude']
#             lon = row['Longitude']
#             tooltip = f"{hotel_name}"
            
#             # 구글 지도 링크들
#             google_maps_search_url = f"https://www.google.com/maps/search/?api=1&query={hotel_name}"
#             google_maps_directions_url = f"https://www.google.com/maps/dir/?api=1&origin=My+Location&destination={hotel_name}"
        
#             popup_html = f"""
#                 <b>{hotel_name}</b><br>
#                 <a href="{google_maps_search_url}" target="_blank">🌐 호텔 정보 보기</a><br>
#                 <a href="{google_maps_directions_url}" target="_blank">🧭 길찾기 (현재 위치 → 호텔)</a>
#             """
        
#             folium.Marker(
#                 location=[lat, lon],
#                 tooltip=tooltip,
#                 popup=folium.Popup(popup_html, max_width=300),
#                 icon=folium.Icon(color='blue', icon='hotel', prefix='fa')
#             ).add_to(marker_cluster)
#     else:
#         for idx, row in dataframe.iterrows():
#             hotel_name = row['Hotel']
#             lat = row['Latitude']
#             lon = row['Longitude']
#             tooltip = f"{hotel_name}"
            
#             # 구글 지도 링크들
#             google_maps_search_url = f"https://www.google.com/maps/search/?api=1&query={hotel_name}"
#             google_maps_directions_url = f"https://www.google.com/maps/dir/?api=1&origin=My+Location&destination={hotel_name}"
        
#             popup_html = f"""
#                 <b>{hotel_name}</b><br>
#                 <a href="{google_maps_search_url}" target="_blank">🌐 호텔 정보 보기</a><br>
#                 <a href="{google_maps_directions_url}" target="_blank">🧭 길찾기 (현재 위치 → 호텔)</a>
#             """
        
#             folium.Marker(
#                 location=[lat, lon],
#                 tooltip=tooltip,
#                 popup=folium.Popup(popup_html, max_width=300),
#                 icon=folium.Icon(color='red', icon='hotel', prefix='fa')
#             ).add_to(m)
    
#     return m



# # ---------------- 지도 출력 ----------------
# if selected_hotel == "전체 보기":
#     st.subheader(f"🗺️ {selected_region} 지역 호텔 지도")
#     map_df = region_df[['Hotel', 'Latitude', 'Longitude']].dropna()
#     if not map_df.empty:
#         m = create_google_map(map_df)
#         folium_static(m, width=800)
#     else:
#         st.warning("지도에 표시할 위치 정보가 없습니다.")
# else:
#     st.subheader(f"🗺️ '{selected_hotel}' 위치")
#     hotel_data = region_df[region_df['Hotel'] == selected_hotel].iloc[0]
#     hotel_map_df = pd.DataFrame({
#         'Hotel': [selected_hotel],
#         'Latitude': [hotel_data['Latitude']],
#         'Longitude': [hotel_data['Longitude']]
#     })
#     m = create_google_map(hotel_map_df, zoom_start=15)
#     folium_static(m, width=800)

#     # ---------------- 호텔 정보 ----------------
#     st.markdown("### ✨ 선택한 호텔 요약")
#     col1, col2 = st.columns(2)
#     with col1:
#         st.subheader("✅ 긍정 요약")
#         st.write(hotel_data['Refined_Positive'])
#     with col2:
#         st.subheader("🚫 부정 요약")
#         st.write(hotel_data['Refined_Negative'])

#     # ---------------- 항목별 점수 ----------------
#     st.markdown("---")
#     st.subheader("📊 항목별 평균 점수")

#     scores = hotel_data[aspect_columns]
#     score_df = pd.DataFrame({
#         "항목": aspect_columns,
#         "점수": scores.values
#     })

#     chart = alt.Chart(score_df).mark_bar().encode(
#         x=alt.X('항목', sort=None, axis=alt.Axis(labelAngle=0)),
#         y=alt.Y('점수', axis=alt.Axis(titleAngle=0)),
#         color=alt.condition(
#             alt.datum.점수 < 0,
#             alt.value('crimson'),
#             alt.value('steelblue')
#         )
#     ).properties(width=600, height=400)

#     st.altair_chart(chart, use_container_width=True)

# # ---------------- 원본 데이터 보기 ----------------
# with st.expander("📄 원본 데이터 보기"):
#     if selected_hotel == "전체 보기":
#         st.dataframe(region_df.reset_index(drop=True))
#     else:
#         st.dataframe(region_df[region_df['Hotel'] == selected_hotel].reset_index(drop=True))
