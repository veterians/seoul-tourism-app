import streamlit as st
import pandas as pd
import json
import os
import time
import random
from datetime import datetime
from pathlib import Path
from geopy.distance import geodesic
import numpy as np

# --- (기존 상수 및 설정 값은 동일하게 유지) ---
# 페이지 설정
st.set_page_config(
    page_title="서울 관광앱",
    page_icon="🗼",
    layout="wide",
    initial_sidebar_state="collapsed"
)

#################################################
# 상수 및 설정 값
#################################################

# Google Maps 기본 중심 위치 (서울시청)
DEFAULT_LOCATION = [37.5665, 126.9780]

# 카테고리별 마커 색상
CATEGORY_COLORS = {
    "체육시설": "blue",
    "공연행사": "purple",
    "관광기념품": "green",
    "한국음식점": "orange",
    "미술관/전시": "pink",
    "종로구 관광지": "red",
    "기타": "gray",
    "현재 위치": "darkblue", # 현재 위치 마커 색상 추가
    "목적지": "darkred"   # 목적지 마커 색상 추가
}

# 파일명과 카테고리 매핑
FILE_CATEGORIES = {
    "체육시설": ["체육시설", "공연행사"],
    "관광기념품": ["관광기념품", "외국인전용"],
    "한국음식점": ["음식점", "한국음식"],
    "미술관/전시": ["미술관", "전시"],
    "종로구 관광지": ["종로구", "관광데이터"]
}

# 세션 데이터 저장 파일
SESSION_DATA_FILE = "data/session_data.json"

# 경험치 설정
XP_PER_LEVEL = 200
PLACE_XP = {
    "경복궁": 80,
    "남산서울타워": 65,
    "동대문 DDP": 35,
    "명동": 25,
    "인사동": 40,
    "창덕궁": 70,
    "북촌한옥마을": 50,
    "광장시장": 30,
    "서울숲": 20,
    "63빌딩": 45
}

# 언어 코드 매핑
LANGUAGE_CODES = {
    "한국어": "ko",
    "영어": "en",
    "중국어": "zh-CN"
}

# 추천 코스 데이터 (기본값, 실제 데이터가 없을 경우 사용)
RECOMMENDATION_COURSES = {
    "문화 코스": ["경복궁", "인사동", "창덕궁", "북촌한옥마을"],
    "쇼핑 코스": ["동대문 DDP", "명동", "광장시장", "남산서울타워"],
    "자연 코스": ["서울숲", "남산서울타워", "한강공원", "북한산"],
    "대중적 코스": ["경복궁", "명동", "남산서울타워", "63빌딩"]
}

# 여행 스타일별 카테고리 가중치
STYLE_CATEGORY_WEIGHTS = {
    "활동적인": {"체육시설": 1.5, "공연행사": 1.2, "종로구 관광지": 1.0},
    "휴양": {"미술관/전시": 1.3, "한국음식점": 1.2, "종로구 관광지": 1.0},
    "맛집": {"한국음식점": 2.0, "관광기념품": 1.0, "종로구 관광지": 0.8},
    "쇼핑": {"관광기념품": 2.0, "한국음식점": 1.0, "종로구 관광지": 0.8},
    "역사/문화": {"종로구 관광지": 1.5, "미술관/전시": 1.3, "공연행사": 1.2},
    "자연": {"종로구 관광지": 1.5, "체육시설": 1.0, "한국음식점": 0.8}
}

# 명시적으로 로드할 7개 파일 리스트
EXCEL_FILES = [
    "서울시 자랑스러운 한국음식점 정보 한국어영어중국어 1.xlsx",
    "서울시 종로구 관광데이터 정보 한국어영어 1.xlsx",
    "서울시 체육시설 공연행사 정보 한국어영어중국어 1.xlsx",
    "서울시 문화행사 공공서비스예약 정보한국어영어중국어 1.xlsx",
    "서울시 외국인전용 관광기념품 판매점 정보한국어영어중국어 1.xlsx",
    "서울시 종로구 관광데이터 정보 중국어 1.xlsx",
    "서울시립미술관 전시정보 한국어영어중국어 1.xlsx"
]

# --- (기존 유틸리티 함수들은 대부분 유지, 필요한 경우 일부 수정) ---
# 예: init_session_state에 tourism_data 초기화 확인
def init_session_state():
    """세션 상태 초기화"""
    # ... (기존 초기화 코드) ...
    if 'tourism_data' not in st.session_state:
        st.session_state.tourism_data = [] # 명시적 초기화
    # ... (기존 초기화 코드) ...

#################################################
# 데이터 로드 함수 - 수정됨
#################################################

def load_excel_files(language="한국어"): # language 파라미터 추가
    """데이터 폴더에서 지정된 Excel 파일 로드"""
    data_folder = Path("asset")
    all_markers = []

    if not data_folder.exists():
        st.warning(f"데이터 폴더({data_folder})가 존재하지 않습니다. 폴더를 생성합니다.")
        data_folder.mkdir(parents=True, exist_ok=True)
        return [] # 데이터 폴더 없으면 빈 리스트 반환

    files_exist_in_folder = any(f.is_file() for f in data_folder.iterdir() if f.name in EXCEL_FILES)

    if not files_exist_in_folder:
        st.error(f"지정된 Excel 파일({', '.join(EXCEL_FILES)})이 asset 폴더에 하나도 존재하지 않습니다. 파일을 추가해주세요.")
        # 예시 데이터나 안내 메시지 추가 가능
        # st.info("예시: '서울시 자랑스러운 한국음식점 정보 한국어영어중국어 1.xlsx' 파일을 asset 폴더에 넣어주세요.")
        return []

    loaded_files_count = 0
    for file_name in EXCEL_FILES:
        file_path = data_folder / file_name
        if not file_path.exists():
            st.warning(f"파일을 찾을 수 없습니다: {file_name}")
            continue

        try:
            st.info(f"파일 로드 시도: {file_name}")
            df = pd.read_excel(file_path, engine='openpyxl')
            st.info(f"'{file_name}' 로드 성공. 행: {len(df)}, 열: {list(df.columns)}")

            file_category = "기타" # 기본 카테고리
            file_name_lower = file_name.lower()
            for category_key, keywords in FILE_CATEGORIES.items():
                if any(keyword.lower() in file_name_lower for keyword in keywords):
                    file_category = category_key
                    break
            
            # process_dataframe 함수에 language 인자 전달
            markers_from_file = process_dataframe(df, file_category, language)
            if markers_from_file:
                all_markers.extend(markers_from_file)
                st.success(f"'{file_name}' 처리 완료: {len(markers_from_file)}개 마커 추가됨.")
                loaded_files_count +=1
            else:
                st.warning(f"'{file_name}'에서 유효한 마커를 추출하지 못했습니다.")

        except Exception as e:
            st.error(f"'{file_name}' 처리 중 오류 발생: {e}")
            import traceback
            st.error(traceback.format_exc()) # 상세 오류 출력

    if loaded_files_count > 0:
        st.success(f"총 {loaded_files_count}개 파일에서 {len(all_markers)}개의 마커를 성공적으로 로드했습니다.")
    else:
        st.warning("로드된 파일에서 유효한 마커 데이터를 찾지 못했습니다. Excel 파일 내용을 확인해주세요.")

    return all_markers

def find_coord_columns(df_columns):
    """데이터프레임 컬럼 목록에서 위도, 경도 컬럼명 추론"""
    lat_candidates = ['y좌표', 'y坐标', '위도', 'latitude', 'lat', 'y']
    lon_candidates = ['x좌표', 'x坐标', '경도', 'longitude', 'lon', 'x']
    
    lat_col, lon_col = None, None
    
    df_columns_lower = [str(col).lower() for col in df_columns] # 컬럼명을 문자열로 변환 후 소문자로
    
    for candidate in lat_candidates:
        if candidate in df_columns_lower:
            lat_col = df_columns[df_columns_lower.index(candidate)]
            break
            
    for candidate in lon_candidates:
        if candidate in df_columns_lower:
            lon_col = df_columns[df_columns_lower.index(candidate)]
            break
            
    return lat_col, lon_col

def process_dataframe(df, category, language="한국어"):
    """데이터프레임을 Google Maps 마커 형식으로 변환 - 수정됨"""
    markers = []
    
    # 좌표 컬럼 동적 탐색
    lat_col_name, lon_col_name = find_coord_columns(df.columns)

    if not lat_col_name or not lon_col_name:
        st.warning(f"'{category}' 데이터에서 좌표 컬럼을 찾을 수 없습니다. (탐색된 컬럼: 위도={lat_col_name}, 경도={lon_col_name}) 사용 가능한 컬럼: {list(df.columns)}")
        return []
    
    st.info(f"'{category}' 데이터 좌표 컬럼으로 '{lat_col_name}'(위도), '{lon_col_name}'(경도) 사용.")

    # 언어별 명칭 컬럼 결정 (기존 로직 유지 또는 개선)
    name_col_mapping = {
        "한국어": ['명칭(한국어)', '명칭', '업소명', '상호명', '이름', '시설명', '관광지명', '장소명', '제목'],
        "영어": ['명칭(영어)', '업소명(영어)', '상호명(영어)','PLACE', 'NAME', 'TITLE', 'ENGLISH_NAME'],
        "중국어": ['명칭(중국어)', '업소명(중국어)', '상호명(중국어)','名称', '中文名']
    }
    name_col = None
    for col_candidate in name_col_mapping.get(language, name_col_mapping["한국어"]): # 해당 언어 없으면 한국어 기준으로
        if col_candidate in df.columns:
            name_col = col_candidate
            break
    
    if category == "종로구 관광지" and language == "중국어" and '名称' in df.columns: # 특정 파일 예외 처리
        name_col = '名称'

    if not name_col:
        st.warning(f"'{category}' 데이터 ({language})에서 적절한 명칭 컬럼을 찾지 못했습니다. 사용 가능한 컬럼: {list(df.columns)}")
        # 명칭이 없으면 데이터 처리 중단 또는 기본값 사용 결정
        # 여기서는 일단 첫번째 문자열 컬럼을 사용하도록 시도 (주의: 원치 않는 결과 초래 가능)
        string_cols = [col for col in df.columns if df[col].dtype == 'object']
        if string_cols:
            name_col = string_cols[0]
            st.info(f"명칭 컬럼 대안으로 '{name_col}' 사용.")
        else:
            st.error(f"'{category}' 데이터에 사용할 명칭 컬럼이 없습니다.")
            return []


    # 주소 컬럼 결정 (기존 로직 유지 또는 개선)
    address_col_mapping = {
        "한국어": ['주소(한국어)', '주소', '소재지', '도로명주소', '지번주소', '위치'],
        "영어": ['주소(영어)', 'ADDRESS', 'LOCATION'],
        "중국어": ['주소(중국어)', '地址']
    }
    address_col = None
    for col_candidate in address_col_mapping.get(language, address_col_mapping["한국어"]):
        if col_candidate in df.columns:
            address_col = col_candidate
            break

    # 좌표 데이터 숫자 변환 및 유효성 검사
    df[lat_col_name] = pd.to_numeric(df[lat_col_name], errors='coerce')
    df[lon_col_name] = pd.to_numeric(df[lon_col_name], errors='coerce')
    df = df.dropna(subset=[lat_col_name, lon_col_name])

    # 대한민국 위경도 대략적 범위 (오차 감안하여 약간 넓게)
    # 실제 서비스라면 더 정확한 범위 설정 필요
    valid_coords = (df[lat_col_name] >= 33) & (df[lat_col_name] <= 39) & \
                     (df[lon_col_name] >= 124) & (df[lon_col_name] <= 132)
    
    invalid_coords_df = df[~valid_coords]
    if not invalid_coords_df.empty:
        st.warning(f"'{category}' 데이터에서 유효한 대한민국 좌표 범위를 벗어나는 {len(invalid_coords_df)}개의 데이터가 제외되었습니다.")
        # st.write("제외된 좌표 데이터 샘플:", invalid_coords_df[[name_col, lat_col_name, lon_col_name]].head())


    df = df[valid_coords]

    if df.empty:
        st.warning(f"'{category}' 데이터에 유효한 좌표가 없습니다. (좌표 컬럼: {lat_col_name}, {lon_col_name})")
        return []

    # 중요도 점수 계산 (기존 로직 유지)
    df['importance_score'] = 1.0
    # ... (중요도 점수 계산 로직) ...

    color = CATEGORY_COLORS.get(category, "gray")

    processed_count = 0
    for _, row in df.iterrows():
        try:
            if pd.isna(row[name_col]) or not str(row[name_col]).strip(): # 이름이 비어있거나 공백만 있으면 제외
                # st.write(f"이름 누락으로 건너뜀: {row}") # 디버깅용
                continue

            name_val = str(row[name_col])
            lat_val = float(row[lat_col_name])
            lon_val = float(row[lon_col_name])

            # 주소 및 추가 정보 (기존 로직 활용)
            address_val = str(row[address_col]) if address_col and pd.notna(row[address_col]) else "정보 없음"
            info_parts = []
            if address_val != "정보 없음":
                info_parts.append(f"주소: {address_val}")
            
            # 전화번호, 운영시간, 입장료 등 (더 많은 컬럼 후보군 추가 가능)
            tel_cols = ['전화번호', '연락처', 'TELNO', 'TEL']
            for tc in tel_cols:
                if tc in row and pd.notna(row[tc]):
                    info_parts.append(f"전화: {row[tc]}")
                    break
            # ... (다른 정보 컬럼 처리) ...

            info_html = "<br>".join(info_parts) if info_parts else "추가 정보 없음"
            
            marker = {
                'lat': lat_val,
                'lng': lon_val,
                'title': name_val,
                'color': color,
                'category': category,
                'info': info_html,
                'address': address_val, # 코스 추천 시 주소 정보 활용 가능
                'importance': row.get('importance_score', 1.0)
            }
            markers.append(marker)
            processed_count += 1
        except Exception as e:
            st.warning(f"마커 생성 중 오류 (데이터: {row.get(name_col, '이름 없음')}): {e}")
            continue
    
    if processed_count > 0:
        st.info(f"'{category}' ({language}) 데이터에서 {processed_count}개의 마커 생성 완료.")
    else:
        st.info(f"'{category}' ({language}) 데이터에서 유효한 마커를 생성하지 못했습니다.")
        
    return markers


# --- (create_Maps_html 함수는 기존 구조 유지, 필요시 마커 정보창 내용 수정) ---
def create_Maps_html(api_key, center_lat, center_lng, markers=None, zoom=13, language="ko"):
    if markers is None:
        markers = []
    
    # ... (기존 HTML 생성 로직) ...
    # 마커 정보창 내용 개선 (예시)
    # info_content = f"""
    #     <div style="padding: 10px; max-width: 300px; font-family: Arial, sans-serif;">
    #         <h4 style="margin-top: 0; color: #1976D2; font-size: 16px;">{title}</h4>
    #         <p style="font-size: 13px; margin-bottom: 5px;"><strong>분류:</strong> {category}</p>
    #         <div style="font-size: 12px; line-height: 1.4;">{info}</div>
    #         <button onclick="window.parent.postMessage({{type: 'navigate_to', title: '{title}', lat: {marker['lat']}, lng: {marker['lng']}}}, '*')">길찾기</button>
    #     </div>
    # """.replace("'", "\\\\'").replace("\n", "")
    # ... (기존 HTML 생성 로직) ...
    
    return html # html 변수가 정의되어 있다고 가정

# --- (show_google_map 함수는 기존 구조 유지) ---

#################################################
# 개선된 관광 코스 추천 함수 - 수정됨
#################################################
def recommend_courses(tourism_data, travel_styles, num_days, include_children=False):
    """
    사용자 취향과 일정에 따른 관광 코스 추천 기능 - 수정됨
    """
    if not tourism_data or not isinstance(tourism_data, list) or len(tourism_data) == 0:
        st.warning("코스 추천을 위한 관광지 데이터가 부족합니다. 기본 추천 코스를 표시합니다.")
        # 기본 코스 반환 (형식을 일관되게 맞춤)
        default_course_type = "대중적 코스"
        default_places = RECOMMENDATION_COURSES.get(default_course_type, [])
        
        # 기본 코스를 daily_courses 형식으로 변환
        daily_default_courses = []
        places_per_day = 3 # 하루 기본 3곳
        for day in range(num_days):
            day_course_places = []
            start_index = day * places_per_day
            end_index = start_index + places_per_day
            # 기본 코스 장소들을 딕셔너리 형태로 변환 (실제 데이터와 유사하게)
            for place_name in default_places[start_index:end_index]:
                # 실제 데이터가 없으므로, 일부 정보는 누락될 수 있음
                day_course_places.append({
                    'title': place_name,
                    'category': '기타', # 기본 카테고리
                    'lat': DEFAULT_LOCATION[0] + random.uniform(-0.1, 0.1), # 임의 좌표
                    'lng': DEFAULT_LOCATION[1] + random.uniform(-0.1, 0.1), # 임의 좌표
                    'importance': 1.0,
                    'info': '기본 추천 장소입니다.'
                })
            if day_course_places: # 장소가 있을 때만 추가
                 daily_default_courses.append(day_course_places)
            elif not daily_default_courses and day == 0 : # 첫날인데 장소가 없으면 비어있는채로라도 추가
                 daily_default_courses.append([])


        return [p['title'] for day_course in daily_default_courses for p in day_course], default_course_type, daily_default_courses

    # 장소별 점수 계산 (기존 로직 유지 또는 개선)
    # tourism_data의 각 아이템이 'importance', 'category', 'lat', 'lng', 'title' 키를 가지고 있다고 가정
    scored_places = []
    for place in tourism_data:
        if not all(k in place for k in ['importance', 'category', 'lat', 'lng', 'title']):
            # st.warning(f"필수 키가 없는 데이터 건너뜀: {place.get('title', '이름 없는 장소')}")
            continue # 필수 키가 없으면 코스 추천에서 제외

        score = float(place.get('importance', 1.0)) # importance가 문자열일 수 있으므로 float 변환

        for style in travel_styles:
            if style in STYLE_CATEGORY_WEIGHTS:
                category_weights = STYLE_CATEGORY_WEIGHTS[style]
                if place['category'] in category_weights:
                    score *= category_weights[place['category']]
        
        if include_children:
            if place['category'] in ["미술관/전시", "체육시설", "공원"]: # 공원 등 아이 친화적 카테고리 추가
                score *= 1.2
        
        scored_place = place.copy()
        scored_place['score'] = score
        scored_places.append(scored_place)

    if not scored_places:
        st.warning("점수를 계산할 수 있는 유효한 관광지가 없습니다. 기본 추천 코스를 사용합니다.")
        # 위 기본 코스 반환 로직 재사용
        default_course_type = "대중적 코스"
        default_places = RECOMMENDATION_COURSES.get(default_course_type, [])
        daily_default_courses = [] # 위에서 정의한대로 생성
        # ... (daily_default_courses 생성 로직 복사) ...
        return [p['title'] for day_course in daily_default_courses for p in day_course], default_course_type, daily_default_courses

    scored_places.sort(key=lambda x: x['score'], reverse=True)
    
    # --- (이하 동선 최적화 및 코스 생성 로직은 기존 구조를 따르되, 입력 데이터 형식 확인) ---
    # 예: seoul_city_hall 정의 확인, geodesic 사용 시 (lat, lng) 튜플 전달 확인
    
    places_per_day = 3 # 하루당 방문 장소 수 (조정 가능)
    # total_places_to_select = num_days * places_per_day * 2 # 더 많은 후보군 확보 (메모리 주의)
    # top_places = scored_places[:min(len(scored_places), total_places_to_select)]
    # 후보군이 너무 많으면 성능 저하, 적절히 조절
    candidate_pool_size = max(num_days * places_per_day * 3, 20) # 최소 20개 또는 필요 수량의 3배
    top_places = scored_places[:min(len(scored_places), candidate_pool_size)]


    if not top_places:
        st.warning("추천할 장소가 부족합니다. 여행 스타일이나 일정을 변경해보세요.")
        # 위 기본 코스 반환 로직 재사용
        # ...
        return [], "장소 부족", []


    # 동선 최적화: 그리디 알고리즘 (개선된 버전)
    seoul_city_hall = {"lat": DEFAULT_LOCATION[0], "lng": DEFAULT_LOCATION[1], "title": "시작점(서울시청)"}
    
    daily_courses = [] # 최종 일별 코스 (장소 딕셔너리 리스트의 리스트)
    
    # 전체 추천 기간 동안 중복 선택을 피하기 위한 집합
    selected_place_titles_overall = set()

    for day_num in range(num_days):
        daily_course_for_this_day = []
        # 매일 아침 시작 위치 (예: 숙소 또는 서울 중심)
        # 첫날은 서울시청, 다음날부터는 전날 마지막 장소에서 가장 가까운 (점수 높은) 곳으로 시작점 변경 가능 (고급 기능)
        current_location_for_day_planning = seoul_city_hall 

        # 현재 날짜에 선택 가능한 장소들 (아직 전체 코스에 포함되지 않은 장소들)
        available_places_for_day = [
            p for p in top_places 
            if p['title'] not in selected_place_titles_overall
        ]

        if not available_places_for_day:
            st.info(f"{day_num + 1}일차: 더 이상 추천할 새로운 장소가 없습니다.")
            break # 더 이상 추천할 장소가 없으면 종료

        for _ in range(places_per_day): # 하루에 places_per_day 만큼의 장소 선택
            if not available_places_for_day:
                break # 이 날짜에 더 이상 선택할 장소가 없으면 다음 장소 선택 중단

            # 현재 위치에서 가장 가깝고 점수 높은 장소 선택
            best_next_place = None
            highest_adjusted_score = -1

            for place_candidate in available_places_for_day:
                try:
                    distance_km = geodesic(
                        (current_location_for_day_planning['lat'], current_location_for_day_planning['lng']),
                        (place_candidate['lat'], place_candidate['lng'])
                    ).kilometers
                except Exception as e:
                    # st.warning(f"거리 계산 오류 ({place_candidate.get('title')}): {e}")
                    distance_km = float('inf') # 오류 시 매우 먼 것으로 간주

                # 거리 가중치 (0~1), 멀수록 낮은 값. 예: 10km 넘어가면 패널티 급증
                # distance_factor = 1 / (1 + (distance_km / 5)**2) # 거리가 5km일때 0.5, 10km일때 0.2
                # 또는 기존 방식:
                distance_factor = max(0.1, 1 - (distance_km / 15)) # 15km 이상이면 점수 10%만 반영


                # 최종 조정 점수: 장소 자체 점수 * 거리 가중치
                adjusted_score = place_candidate.get('score', 1.0) * distance_factor

                if adjusted_score > highest_adjusted_score:
                    highest_adjusted_score = adjusted_score
                    best_next_place = place_candidate
            
            if best_next_place:
                daily_course_for_this_day.append(best_next_place)
                selected_place_titles_overall.add(best_next_place['title']) # 전체 선택 목록에 추가
                current_location_for_day_planning = best_next_place # 다음 장소 탐색의 시작점으로 업데이트
                # 다음 선택을 위해 방금 선택한 장소는 available_places_for_day에서 제거
                available_places_for_day = [p for p in available_places_for_day if p['title'] != best_next_place['title']]
            else:
                # 더 이상 적합한 장소가 없을 경우 (모든 남은 장소의 adjusted_score가 매우 낮음)
                break 
        
        if daily_course_for_this_day: # 하루 코스가 생성되었으면 추가
            daily_courses.append(daily_course_for_this_day)

    # 코스 이름 결정 (기존 로직 유지)
    # ... (코스 이름 결정 로직) ...
    course_type = "맞춤 추천 코스" # 간단하게 통일 또는 기존 로직 사용
    if travel_styles:
        course_type = f"{', '.join(travel_styles)} 맞춤 코스"


    # 최종 추천된 모든 장소의 이름 리스트 (평탄화)
    recommended_place_names = [place['title'] for day_course in daily_courses for place in day_course]

    if not recommended_place_names:
         st.info("생성된 추천 코스가 없습니다. 조건을 변경해보세요.")
         # 이 경우에도 기본 코스 반환 또는 빈 리스트 반환
         # ... (기본 코스 반환 로직) ...

    return recommended_place_names, course_type, daily_courses


#################################################
# 페이지 함수 - show_map_page 수정
#################################################
def show_map_page():
    """지도 페이지 표시 - 수정됨"""
    page_header("서울 관광 장소 지도")

    if st.button("← 메뉴로 돌아가기"):
        change_page("menu")
        st.rerun()

    api_key = st.session_state.get("Maps_api_key", "") # .get으로 안전하게 접근
    if not api_key or api_key == "YOUR_Maps_API_KEY":
        st.error("Google Maps API 키가 설정되지 않았습니다.")
        # ... (API 키 입력 UI) ...
        return

    # 언어 선택 (기존 로직 유지)
    # ...

    user_location = get_location_position() # [lat, lng]

    # 데이터 로드 (st.session_state.all_markers 사용 일관성)
    # st.session_state.tourism_data 대신 st.session_state.all_markers를 주 데이터로 사용
    if not st.session_state.get('markers_loaded', False) or not st.session_state.get('all_markers'):
        with st.spinner("서울 관광 데이터를 로드하는 중..."):
            # load_excel_files 함수에 현재 선택된 언어 전달
            loaded_markers = load_excel_files(st.session_state.get('language', '한국어'))
            if loaded_markers:
                st.session_state.all_markers = loaded_markers
                st.session_state.markers_loaded = True
                # st.session_state.tourism_data = loaded_markers # 필요시 tourism_data도 동기화
                st.success(f"총 {len(st.session_state.all_markers)}개의 관광지 로드 완료!")
            else:
                st.session_state.all_markers = [] # 로드 실패 시 빈 리스트로 초기화
                st.session_state.markers_loaded = False # 실패 시 로드 안된 것으로
                st.warning("관광지 데이터를 로드할 수 없었습니다. Excel 파일을 확인하거나, asset 폴더에 파일이 올바르게 있는지 확인해주세요.")
                # 데이터가 없을 경우 지도 표시는 의미가 없을 수 있으므로, 여기서 중단하거나 빈 지도라도 표시할지 결정
                # return # 데이터 없으면 지도 표시 안함

    # 지도에 표시할 마커 준비
    map_display_markers = []
    
    # 1. 사용자 현재 위치 마커 (항상 추가)
    map_display_markers.append({
        'lat': user_location[0],
        'lng': user_location[1],
        'title': '내 위치',
        'color': CATEGORY_COLORS.get("현재 위치", "blue"), # 정의된 색상 사용
        'info': '현재 계신 곳입니다.',
        'category': '현재 위치',
        'importance': 2.0 # 중요도 높게 설정하여 항상 보이도록 (필요시)
    })

    # 2. 로드된 관광지 마커 추가
    if st.session_state.get('all_markers'):
        # st.write(f"all_markers 내용 일부: {st.session_state.all_markers[:2]}") # 디버깅용: 마커 데이터 확인
        map_display_markers.extend(st.session_state.all_markers)
        st.info(f"지도에 {len(st.session_state.all_markers)}개의 관광지를 포함하여 총 {len(map_display_markers)}개의 마커를 준비했습니다.")
    else:
        st.info("표시할 관광지 데이터가 없습니다. '내 위치'만 지도에 표시됩니다.")


    if not st.session_state.get('navigation_active', False):
        map_col, info_col = st.columns([2, 1])

        with map_col:
            if not map_display_markers: # 표시할 마커가 전혀 없을 경우
                st.warning("지도에 표시할 마커가 없습니다.")
            else:
                show_google_map(
                    api_key=api_key,
                    center_lat=user_location[0],
                    center_lng=user_location[1],
                    markers=map_display_markers, # 준비된 마커 리스트 전달
                    zoom=12, # 기본 줌 레벨
                    height=600,
                    language=st.session_state.get('language', '한국어')
                )
        
        with info_col:
            st.subheader("장소 정보 및 기능")
            # ... (검색, 카테고리 통계 등 기존 info_col 내용) ...
            # 검색 기능 수정: st.session_state.all_markers에서 검색
            search_term = st.text_input("장소 검색")
            if search_term and st.session_state.get('all_markers'):
                search_results = [
                    m for m in st.session_state.all_markers
                    if search_term.lower() in m.get('title', '').lower() # title이 없을 수도 있으므로 .get 사용
                ]
                # ... (검색 결과 표시 로직) ...
            elif search_term:
                st.info("검색할 관광지 데이터가 없습니다.")


            # 마커 클릭 시 정보 표시 (HTML에서 postMessage로 받은 데이터 처리 - 고급 기능)
            # 이 부분은 create_Maps_html 및 Streamlit 이벤트 처리와 연동 필요
            # if st.session_state.get('clicked_map_marker_info'):
            #     info = st.session_state.clicked_map_marker_info
            #     st.write(f"선택된 장소: {info['title']}")
            #     st.write(f"카테고리: {info['category']}")
            #     # 길찾기 버튼 등 추가

    else: # 내비게이션 모드
        # ... (기존 내비게이션 모드 UI) ...
        # 내비게이션 마커는 출발지, 목적지만 표시하도록 수정
        destination = st.session_state.navigation_destination
        if destination:
            navigation_markers = [
                 {
                    'lat': user_location[0], 
                    'lng': user_location[1], 
                    'title': '출발지 (내 위치)', 
                    'color': CATEGORY_COLORS.get("현재 위치", "blue"),
                    'info': '출발 지점입니다.',
                    'category': '내 위치'
                },
                {
                    'lat': destination['lat'], 
                    'lng': destination['lng'], 
                    'title': f"목적지: {destination['name']}", 
                    'color': CATEGORY_COLORS.get("목적지", "red"),
                    'info': f"도착 지점: {destination['name']}",
                    'category': '목적지'
                }
            ]
            # show_google_map에 navigation_markers 전달
            # ...

# --- (show_course_page 함수 수정) ---
def show_course_page():
    """개선된 관광 코스 추천 페이지 - 수정됨"""
    page_header("서울 관광 코스 짜주기")

    if st.button("← 메뉴로 돌아가기"):
        change_page("menu")
        st.rerun()

    # 데이터 로드 보장 (st.session_state.all_markers 사용)
    if not st.session_state.get('markers_loaded', False) or not st.session_state.get('all_markers'):
        with st.spinner("코스 추천을 위한 관광 데이터를 로드하는 중..."):
            # load_excel_files 함수에 현재 선택된 언어 전달
            loaded_markers = load_excel_files(st.session_state.get('language', '한국어'))
            if loaded_markers:
                st.session_state.all_markers = loaded_markers
                st.session_state.markers_loaded = True
                st.success(f"코스 추천용 데이터 로드 완료: {len(st.session_state.all_markers)}개 장소")
            else:
                st.session_state.all_markers = [] # 로드 실패 시 빈 리스트로 초기화
                st.session_state.markers_loaded = False
                st.error("코스 추천에 필요한 관광지 데이터를 로드할 수 없습니다. Excel 파일 및 설정을 확인해주세요.")
                # 데이터가 없으면 코스 추천 기능 사용 불가 메시지 표시 후 중단 가능
                st.info("데이터가 없어 코스 추천 기능을 사용할 수 없습니다.")
                return

    # ... (여행 정보 입력 UI는 기존과 유사하게 유지) ...
    # 여행 스타일 선택 (기존 로직 유지)
    
    if 'all_markers' not in st.session_state or not st.session_state.all_markers:
        st.warning("코스 추천을 위한 관광지 데이터가 없습니다. 먼저 지도 페이지에서 데이터를 로드하거나, Excel 파일을 확인해주세요.")
        # 이 경우 코스 생성 버튼을 비활성화 하거나, 메시지만 표시
        generate_course_disabled = True
    else:
        generate_course_disabled = False


    generate_course = st.button("코스 생성하기", type="primary", use_container_width=True, disabled=generate_course_disabled)

    if generate_course:
        if not selected_styles: # selected_styles 변수가 정의되어 있다고 가정
            st.warning("최소 하나 이상의 여행 스타일을 선택해주세요.")
        elif not st.session_state.get('all_markers'): # 다시 한번 데이터 확인
            st.error("코스 추천을 위한 관광 데이터가 없습니다. 앱을 새로고침하거나 관리자에게 문의하세요.")
        else:
            with st.spinner("최적의 관광 코스를 생성 중입니다..."):
                time.sleep(1) # AI가 생각하는 척
                # recommend_courses 함수에 st.session_state.all_markers 전달
                recommended_places, course_type, daily_courses = recommend_courses(
                    st.session_state.all_markers, # 여기가 중요!
                    selected_styles, # selected_styles 변수가 이전에 정의되어 있어야 함
                    delta, # delta (일수) 변수가 이전에 정의되어 있어야 함
                    include_children # include_children 변수가 이전에 정의되어 있어야 함
                )
                
                # st.write("추천된 daily_courses:", daily_courses) # 디버깅용

                if not recommended_places and not daily_courses:
                    st.error("선택하신 조건에 맞는 코스를 생성할 수 없었습니다. 다른 조건을 시도해보세요.")
                else:
                    st.success("코스 생성 완료!")
                    st.markdown("## 추천 코스")
                    st.markdown(f"**{course_type}** - {delta}일 일정")

                    if daily_courses: # daily_courses가 실제 장소 딕셔너리 리스트를 포함하고 있을 때
                        for day_idx, day_course_places in enumerate(daily_courses):
                            st.markdown(f"### Day {day_idx + 1}")
                            if not day_course_places:
                                st.info("이 날짜에는 추천 장소가 없습니다.")
                                continue
                            
                            # 시간대별 장소 표시 (기존 로직과 유사하게, place 딕셔너리 사용)
                            time_slots = ["오전 (09:00-12:00)", "점심 무렵 (12:00-14:00)", "오후 (14:00-17:00)", "저녁 이후 (17:00~)"]
                            
                            # 하루 장소 수에 맞춰 컬럼 동적 생성
                            num_places_this_day = len(day_course_places)
                            if num_places_this_day > 0:
                                timeline_cols = st.columns(num_places_this_day)
                                for i, place_details in enumerate(day_course_places):
                                    with timeline_cols[i]:
                                        # place_details는 {'title': ..., 'category': ..., 'lat': ..., 'lng': ..., 'info': ...} 형태여야 함
                                        current_time_slot = time_slots[i % len(time_slots)] # 시간대 순환
                                        st.markdown(f"**{current_time_slot}**")
                                        st.markdown(f"##### {place_details.get('title', '장소 이름 없음')}")
                                        st.caption(f"분류: {place_details.get('category', '미분류')}")
                                        # 추가 정보 표시 (주소 등)
                                        # if place_details.get('address') and place_details.get('address') != "정보 없음":
                                        #    st.caption(f"주소: {place_details.get('address')[:30]}...") # 너무 길면 잘라서 표시
                                        # else:
                                        #    st.caption(place_details.get('info', '세부 정보 없음')[:50])


                    else: # daily_courses가 비어있고 recommended_places (이름 리스트)만 있는 경우 (예: 기본 코스)
                        st.info("상세 일별 코스 정보가 없습니다. 주요 추천 장소 목록입니다.")
                        for place_name in recommended_places:
                            st.markdown(f"- {place_name}")
                    
                    # 지도에 코스 표시 (daily_courses 데이터 사용)
                    st.markdown("### 🗺️ 코스 지도")
                    api_key = st.session_state.get("Maps_api_key")
                    if not api_key or api_key == "YOUR_Maps_API_KEY":
                        st.error("Google Maps API 키가 필요합니다.")
                    elif daily_courses: # 상세 코스가 있을 때만 지도 표시
                        course_map_markers = []
                        # st.write("daily_courses for map:", daily_courses) # 디버깅
                        for day_idx, day_items in enumerate(daily_courses):
                            for place_idx, place_item in enumerate(day_items):
                                if not all(k in place_item for k in ['lat', 'lng', 'title']):
                                    # st.warning(f"지도 표시 위한 좌표/이름 누락: {place_item.get('title')}")
                                    continue
                                
                                # 일자별/순서별 색상 또는 아이콘 구분 가능
                                marker_colors_by_day = ['red', 'green', 'blue', 'purple', 'orange'] # 요일별 색상
                                color = marker_colors_by_day[day_idx % len(marker_colors_by_day)]

                                course_map_markers.append({
                                    'lat': place_item['lat'],
                                    'lng': place_item['lng'],
                                    'title': f"Day {day_idx+1}-{place_idx+1}: {place_item['title']}",
                                    'color': color,
                                    'category': place_item.get('category', '코스 장소'),
                                    'info': f"Day {day_idx+1}<br>{place_item.get('info', '')}",
                                    'importance': 1.5 # 코스 장소는 중요하게 표시
                                })
                        
                        if course_map_markers:
                            # 지도 중심 좌표 계산 (첫번째 장소 또는 모든 장소의 평균)
                            center_lat = course_map_markers[0]['lat']
                            center_lng = course_map_markers[0]['lng']
                            if len(course_map_markers) > 1:
                                center_lat = sum(m['lat'] for m in course_map_markers) / len(course_map_markers)
                                center_lng = sum(m['lng'] for m in course_map_markers) / len(course_map_markers)

                            show_google_map(
                                api_key=api_key,
                                center_lat=center_lat,
                                center_lng=center_lng,
                                markers=course_map_markers,
                                zoom=11, # 코스 전체를 볼 수 있도록 줌 아웃
                                height=500,
                                language=st.session_state.get('language', '한국어')
                            )
                        else:
                            st.info("코스 장소의 위치 정보가 없어 지도에 표시할 수 없습니다.")
                    
                    # 일정 저장 버튼 (기존 로직 유지)
                    # ...

# --- (show_history_page 함수는 큰 변경 없이 기존 구조 유지 가능) ---

# --- (메인 앱 로직 기존 구조 유지) ---
def main():
    # 로그인 상태에 따른 페이지 제어
    if not st.session_state.get("logged_in", False) and st.session_state.get("current_page", "login") != "login": # .get 사용
        st.session_state.current_page = "login"
    
    current_page = st.session_state.get("current_page", "login") # .get 사용

    if current_page == "login":
        show_login_page()
    elif current_page == "menu":
        show_menu_page()
    elif current_page == "map":
        show_map_page()
    elif current_page == "course":
        show_course_page()
    elif current_page == "history":
        show_history_page()
    else:
        st.session_state.current_page = "menu" # 알 수 없는 페이지면 메뉴로
        show_menu_page()

if __name__ == "__main__":
    # CSS 스타일 적용 및 세션 초기화는 main 함수 호출 전에 수행
    apply_custom_css() # 정의되어 있다고 가정
    init_session_state() # 정의되어 있다고 가정
    
    # 데이터 폴더 및 asset 폴더 생성 확인
    Path("data").mkdir(parents=True, exist_ok=True)
    Path("asset").mkdir(parents=True, exist_ok=True)

    main()
