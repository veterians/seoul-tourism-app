import streamlit as st
import pandas as pd
import json
import os
import time
import random
from datetime import datetime, timedelta
from pathlib import Path
from geopy.distance import geodesic
import numpy as np
import traceback # 상세 오류 출력을 위해 추가

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
    "현재 위치": "darkblue",
    "목적지": "darkred"
}

# 파일명과 카테고리 매핑
FILE_CATEGORIES = {
    "체육시설": ["체육시설", "공연행사", "문화행사"],
    "관광기념품": ["관광기념품", "외국인전용"],
    "한국음식점": ["음식점", "한국음식"],
    "미술관/전시": ["미술관", "전시"],
    "종로구 관광지": ["종로구", "관광데이터"]
}

# 사용자 데이터 저장 파일 경로 (data 폴더 사용)
DATA_DIR = Path("data")
USER_CREDENTIALS_FILE = DATA_DIR / "user_credentials.json"
SAVED_COURSES_FILE = DATA_DIR / "saved_courses.json"
USER_XP_FILE = DATA_DIR / "user_xp.json"

# 경험치 설정
XP_PER_LEVEL = 200
PLACE_XP = {
    "경복궁": 80, "광화문": 75, "덕수궁": 60, "창경궁": 65, "창덕궁": 70,
    "N서울타워": 65, "롯데월드타워": 70, "63빌딩": 45,
    "코엑스": 40, "DDP": 35, "국립중앙박물관": 55, "리움미술관": 50,
    "명동": 25, "인사동": 40, "북촌한옥마을": 50, "남산골한옥마을": 45,
    "광장시장": 30, "남대문시장": 35, "동대문시장": 30,
    "서울숲": 20, "올림픽공원": 25, "한강공원": 15,
    "롯데월드": 60, "에버랜드": 0,
    "별마당도서관": 30,
}

# 언어 코드 매핑
LANGUAGE_CODES = {
    "한국어": "ko",
    "영어": "en",
    "중국어": "zh-CN"
}

# 추천 코스 데이터 (기본값)
RECOMMENDATION_COURSES = {
    "문화 코스": ["경복궁", "인사동", "창덕궁", "북촌한옥마을"],
    "쇼핑 코스": ["동대문 DDP", "명동", "광장시장", "N서울타워"],
    "자연 코스": ["서울숲", "N서울타워", "한강공원", "올림픽공원"],
    "대중적 코스": ["경복궁", "명동", "N서울타워", "63빌딩"]
}

# 여행 스타일별 카테고리 가중치
STYLE_CATEGORY_WEIGHTS = {
    "활동적인": {"체육시설": 1.5, "공연행사": 1.2, "종로구 관광지": 1.0},
    "휴양": {"미술관/전시": 1.3, "한국음식점": 1.2, "종로구 관광지": 1.0, "공원": 1.1},
    "맛집": {"한국음식점": 2.0, "관광기념품": 1.0, "종로구 관광지": 0.8},
    "쇼핑": {"관광기념품": 2.0, "한국음식점": 1.0, "종로구 관광지": 0.8},
    "역사/문화": {"종로구 관광지": 1.5, "미술관/전시": 1.3, "공연행사": 1.2},
    "자연": {"종로구 관광지": 1.2, "체육시설": 1.0, "한국음식점": 0.8, "공원": 1.5}
}

# Excel 데이터 파일이 위치한 폴더 (asset 폴더 사용)
ASSET_DIR = Path("asset")
EXCEL_FILES = [
    "서울시 자랑스러운 한국음식점 정보 한국어영어중국어 1.xlsx",
    "서울시 종로구 관광데이터 정보 한국어영어 1.xlsx",
    "서울시 체육시설 공연행사 정보 한국어영어중국어 1.xlsx",
    "서울시 문화행사 공공서비스예약 정보한국어영어중국어 1.xlsx",
    "서울시 외국인전용 관광기념품 판매점 정보한국어영어중국어 1.xlsx",
    "서울시 종로구 관광데이터 정보 중국어 1.xlsx",
    "서울시립미술관 전시정보 한국어영어중국어 1.xlsx"
]
#################################################
# 유틸리티 함수
#################################################
def apply_custom_css():
    """커스텀 CSS 적용"""
    st.markdown("""
    <style>
        body { font-family: 'Nanum Gothic', sans-serif; background-color: #f0f2f6; }
        .stApp > header { background-color: transparent; }
        .main .block-container { padding-top: 2rem; padding-bottom: 2rem; padding-left: 2rem; padding-right: 2rem; }
        .stButton>button { border-radius: 20px; border: 1px solid #4CAF50; background-color: #4CAF50; color: white; padding: 10px 24px; text-align: center; text-decoration: none; display: inline-block; font-size: 16px; margin: 4px 2px; transition-duration: 0.4s; cursor: pointer; }
        .stButton>button:hover { background-color: white; color: black; border: 1px solid #4CAF50; }
        .stButton>button[kind="primary"] { background-color: #007bff; border: 1px solid #007bff; }
        .stButton>button[kind="primary"]:hover { background-color: white; color: #007bff; border: 1px solid #007bff; }
        .stTextInput input, .stSelectbox select { border-radius: 8px; }
        .custom-card { background-color: white; padding: 20px; border-radius: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); margin-bottom: 15px; }
        h1, h2, h3, h4, h5, h6 { color: #333; }
    </style>
    """, unsafe_allow_html=True)

def load_user_xp():
    """사용자 경험치 데이터 로드"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if USER_XP_FILE.exists():
        try:
            with open(USER_XP_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {} # 파일 내용이 비었거나 JSON 형식이 아니면 빈 딕셔너리 반환
    return {}

def save_user_xp(user_xp_data):
    """사용자 경험치 데이터 저장"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(USER_XP_FILE, 'w', encoding='utf-8') as f:
        json.dump(user_xp_data, f, indent=4, ensure_ascii=False)


def init_session_state():
    """세션 상태 초기화"""
    if 'logged_in' not in st.session_state: st.session_state.logged_in = False
    if 'current_page' not in st.session_state: st.session_state.current_page = "login"
    if 'username' not in st.session_state: st.session_state.username = ""
    
    # Google API 키는 secrets에서 로드
    if 'Maps_api_key' not in st.session_state:
        try:
            st.session_state.Maps_api_key = st.secrets["Maps_api_key"]
        except (KeyError, FileNotFoundError): # secrets.toml 파일이 없거나 키가 없을 경우
            st.session_state.Maps_api_key = "YOUR_FALLBACK_API_KEY" # 대체 키 또는 빈 문자열
            # st.warning("Google Maps API 키를 Streamlit secrets에서 찾을 수 없습니다. 일부 기능이 제한될 수 있습니다.")

    if 'user_xp' not in st.session_state:
        st.session_state.user_xp = load_user_xp() # 파일에서 로드

    if 'user_level' not in st.session_state: st.session_state.user_level = {} # 레벨은 XP 기반으로 동적 계산
    if 'language' not in st.session_state: st.session_state.language = "한국어" # 기본 언어 설정
    if 'all_markers' not in st.session_state: st.session_state.all_markers = []
    if 'markers_loaded' not in st.session_state: st.session_state.markers_loaded = False
    if 'user_location' not in st.session_state: st.session_state.user_location = DEFAULT_LOCATION
    if 'navigation_active' not in st.session_state: st.session_state.navigation_active = False
    if 'navigation_destination' not in st.session_state: st.session_state.navigation_destination = None
    if 'saved_courses' not in st.session_state:
        st.session_state.saved_courses = load_saved_courses()

def page_header(title):
    """공통 페이지 헤더"""
    st.markdown(f"<h1 style='text-align: center; color: #4CAF50;'>{title} 🚀</h1>", unsafe_allow_html=True)
    st.markdown("---")

def change_page(page_name):
    """페이지 변경 함수"""
    st.session_state.current_page = page_name

def get_location_position():
    """현재 위치 가져오기 (JavaScript 사용)"""
    if 'get_location_once' not in st.session_state:
        st.session_state.get_location_once = True
    if st.session_state.get_location_once: # 한 번만 JS 실행 시도
        location_script = """
        <script>
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                function(position) {
                    const coords = {lat: position.coords.latitude, lng: position.coords.longitude};
                    window.parent.postMessage({type: 'streamlit:setComponentValue', value: coords, key: 'geolocation_data'}, '*');
                },
                function(error) {
                    console.error("Error Code = " + error.code + " - " + error.message);
                    const defaultCoords = {lat: %s, lng: %s, error: error.message}; // 기본 위치와 오류 메시지 전달
                    window.parent.postMessage({type: 'streamlit:setComponentValue', value: defaultCoords, key: 'geolocation_data'}, '*');
                }
            );
        } else {
            console.error("Geolocation is not supported by this browser.");
            const defaultCoords = {lat: %s, lng: %s, error: "Geolocation not supported"};
            window.parent.postMessage({type: 'streamlit:setComponentValue', value: defaultCoords, key: 'geolocation_data'}, '*');
        }
        </script>
        """ % (DEFAULT_LOCATION[0], DEFAULT_LOCATION[1], DEFAULT_LOCATION[0], DEFAULT_LOCATION[1])
        st.components.v1.html(location_script, height=0)
        st.session_state.get_location_once = False # 실행 후 플래그 변경
    return st.session_state.get('user_location', DEFAULT_LOCATION) # 세션에 저장된 값 반환

def load_user_credentials():
    """사용자 계정 정보 로드"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if USER_CREDENTIALS_FILE.exists():
        try:
            with open(USER_CREDENTIALS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}
    return {}

def save_user_credentials(credentials):
    """사용자 계정 정보 저장"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(USER_CREDENTIALS_FILE, 'w', encoding='utf-8') as f:
        json.dump(credentials, f, indent=4, ensure_ascii=False)

def load_saved_courses():
    """저장된 코스 로드"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if SAVED_COURSES_FILE.exists():
        try:
            with open(SAVED_COURSES_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError: return {}
    return {}

def save_user_course(username, course_name, course_details, daily_courses_for_save):
    """사용자 코스 저장"""
    all_saved_courses = load_saved_courses()
    if username not in all_saved_courses: all_saved_courses[username] = []
    is_duplicate = False
    if daily_courses_for_save and daily_courses_for_save[0] and daily_courses_for_save[0][0]: # 첫날 첫 장소까지 있는지 확인
        first_place_title = daily_courses_for_save[0][0].get('title', '')
        for existing_course in all_saved_courses[username]:
            if existing_course.get('course_name') == course_name and \
               existing_course.get('daily_courses') and \
               existing_course['daily_courses'][0] and \
               existing_course['daily_courses'][0][0].get('title') == first_place_title:
                is_duplicate = True; break
    if not is_duplicate:
        all_saved_courses[username].append({
            "course_name": course_name, "details": course_details,
            "saved_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "daily_courses": daily_courses_for_save
        })
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with open(SAVED_COURSES_FILE, 'w', encoding='utf-8') as f:
            json.dump(all_saved_courses, f, indent=4, ensure_ascii=False)
        st.success(f"'{course_name}' 코스가 저장되었습니다!")
    else: st.info(f"'{course_name}' 코스는 이미 저장되어 있습니다.")

def get_user_level(username):
    """사용자 레벨 및 진행도 계산"""
    xp = st.session_state.user_xp.get(str(username), 0) # username을 문자열로 확실히 변환
    level = xp // XP_PER_LEVEL
    progress = (xp % XP_PER_LEVEL) / XP_PER_LEVEL * 100
    return level, progress, xp

#################################################
# 데이터 로드 함수
#################################################
def load_excel_files(language="한국어"):
    """asset 폴더에서 지정된 Excel 파일 로드"""
    all_markers = []
    if not ASSET_DIR.exists():
        st.warning(f"데이터 파일 폴더({ASSET_DIR})가 존재하지 않습니다. 'asset' 폴더를 생성하고 Excel 파일을 넣어주세요.")
        return []

    files_in_folder = [f.name for f in ASSET_DIR.iterdir() if f.is_file() and f.name.endswith(('.xlsx', '.xls'))]
    files_to_load = [f_name for f_name in EXCEL_FILES if f_name in files_in_folder]
    missing_specific_files = [f_name for f_name in EXCEL_FILES if f_name not in files_in_folder]

    if not files_to_load:
        st.error(f"지정된 Excel 파일({', '.join(EXCEL_FILES)}) 중 어느 것도 '{ASSET_DIR}' 폴더에 없습니다.")
        if missing_specific_files: st.info(f"누락 파일: {', '.join(missing_specific_files)}")
        return []
    if missing_specific_files: st.warning(f"다음 지정 파일들이 '{ASSET_DIR}'에 없어 로드되지 않습니다: {', '.join(missing_specific_files)}")

    loaded_files_count = 0
    for file_name in files_to_load:
        file_path = ASSET_DIR / file_name
        try:
            df = pd.read_excel(file_path, engine='openpyxl')
            file_category = "기타"
            file_name_lower = file_name.lower()
            for category_key, keywords in FILE_CATEGORIES.items():
                if any(keyword.lower() in file_name_lower for keyword in keywords):
                    file_category = category_key; break
            markers_from_file = process_dataframe(df, file_category, language, file_name)
            if markers_from_file:
                all_markers.extend(markers_from_file); loaded_files_count +=1
        except Exception as e:
            st.error(f"'{file_name}' 처리 오류: {e}"); st.error(traceback.format_exc())
    if loaded_files_count > 0: st.success(f"총 {loaded_files_count}개 파일, {len(all_markers)}개 마커 로드 완료.")
    else: st.warning("유효 마커 데이터 없음. Excel 파일 확인 요망.")
    return all_markers

def find_coord_columns(df_columns):
    """DataFrame 컬럼 목록에서 위도, 경도 컬럼명 추론"""
    lat_candidates = ['y좌표', 'y 좌표', 'y좌표(wgs84)', 'y 좌표(wgs84)','y', '위도', 'latitude', 'lat']
    lon_candidates = ['x좌표', 'x 좌표', 'x좌표(wgs84)', 'x 좌표(wgs84)','x', '경도', 'longitude', 'lon']
    lat_col, lon_col = None, None
    df_columns_lower = [str(col).lower().strip() for col in df_columns]
    for candidate in lat_candidates:
        if candidate in df_columns_lower: lat_col = df_columns[df_columns_lower.index(candidate)]; break
    for candidate in lon_candidates:
        if candidate in df_columns_lower: lon_col = df_columns[df_columns_lower.index(candidate)]; break
    return lat_col, lon_col

def process_dataframe(df, category, language="한국어", filename=""):
    """DataFrame을 Google Maps 마커 형식으로 변환"""
    markers = []
    lat_col_name, lon_col_name = find_coord_columns(df.columns)
    if not lat_col_name or not lon_col_name: return []

    name_col_mapping = {
        "한국어": ['명칭', '업소명', '상호명', '시설명', '관광지명', '장소명', '제목', '명칭(국문)', '명칭(한글)', '점포명', '식당명', '가게명', '문화행사명', '전시명'],
        "영어": ['명칭(영어)', '업소명(영문)', '상호명(영문)', 'PLACE', 'NAME', 'TITLE', 'ENGLISH_NAME', 'EVENT_NAME(ENG)', 'EXHIBITION_NAME(ENG)'],
        "중국어": ['명칭(중국어)', '업소명(중문)', '상호명(중문)', '名称', '中文名', '活动名称(中文)', '展览名称(中文)']
    }
    name_col = None
    current_lang_candidates = name_col_mapping.get(language, [])
    fallback_lang_candidates = name_col_mapping.get("한국어", [])
    for col_candidate in current_lang_candidates + fallback_lang_candidates:
        if col_candidate in df.columns: name_col = col_candidate; break
    if category == "종로구 관광지" and language == "중국어" and '名称' in df.columns: name_col = '名称'
    if not name_col:
        string_cols = [col for col in df.columns if df[col].dtype == 'object']
        if string_cols: name_col = string_cols[0]
        else: return []

    address_col_mapping = {
        "한국어": ['주소', '소재지', '도로명주소', '지번주소', '위치', '장소', '주소(국문)', '소재지도로명주소'],
        "영어": ['주소(영어)', 'ADDRESS', 'LOCATION', 'ADDRESS(ENG)'],
        "중국어": ['주소(중국어)', '地址', 'ADDRESS(CHN)']
    }
    address_col = None
    current_addr_candidates = address_col_mapping.get(language, [])
    fallback_addr_candidates = address_col_mapping.get("한국어", [])
    for col_candidate in current_addr_candidates + fallback_addr_candidates:
        if col_candidate in df.columns: address_col = col_candidate; break

    df[lat_col_name] = pd.to_numeric(df[lat_col_name], errors='coerce')
    df[lon_col_name] = pd.to_numeric(df[lon_col_name], errors='coerce')
    df = df.dropna(subset=[lat_col_name, lon_col_name])
    valid_coords = (df[lat_col_name] >= 33) & (df[lat_col_name] <= 39) & \
                     (df[lon_col_name] >= 124) & (df[lon_col_name] <= 132)
    df = df[valid_coords]
    if df.empty: return []

    df['importance_score'] = 1.0
    for place_name_keyword, xp_value in PLACE_XP.items():
        if xp_value > 40:
            df.loc[df[name_col].astype(str).str.contains(place_name_keyword, case=False, na=False), 'importance_score'] *= 1.5
    if '평점' in df.columns:
        df['importance_score'] *= pd.to_numeric(df['평점'], errors='coerce').fillna(3.0) / 5.0 * 0.5 + 1.0
    
    color = CATEGORY_COLORS.get(category, "gray")
    for _, row in df.iterrows():
        try:
            if pd.isna(row[name_col]) or not str(row[name_col]).strip(): continue
            name_val = str(row[name_col]).strip()
            lat_val = float(row[lat_col_name]); lon_val = float(row[lon_col_name])
            address_val = str(row[address_col]).strip() if address_col and pd.notna(row[address_col]) else "정보 없음"
            info_parts = []
            if address_val != "정보 없음": info_parts.append(f"주소: {address_val}")
            tel_cols_candidates = {"한국어": ['전화번호', '연락처'], "영어": ['TEL', 'PHONE'], "중국어": ['电话']}
            tel_col_found = None
            for tc_lang in [language, "한국어", "영어", "중국어"]:
                 for tc in tel_cols_candidates.get(tc_lang, []):
                    if tc in row and pd.notna(row[tc]) and str(row[tc]).strip():
                        info_parts.append(f"전화: {row[tc]}"); tel_col_found = True; break
                 if tel_col_found: break
            extra_info_cols = {
                "운영시간": ['운영시간', '이용시간', '영업시간', 'HOURS', '营业时间'],
                "웹사이트": ['홈페이지', '웹사이트', '사이트', 'WEBSITE', '网站'],
                "정보": ['안내', '설명', '비고', 'INFO', '介绍', '기타정보'],
            }
            for info_key, col_candidates in extra_info_cols.items():
                col_found = None
                for c_lang in [language, "한국어", "영어", "중국어"]:
                    lang_specific_candidates = [cand for cand in col_candidates if f'({c_lang[:2].upper()})' in cand.upper() or language.lower() in cand.lower()]
                    general_candidates = [cand for cand in col_candidates if not any(x in cand.upper() for x in ['(EN)', '(영', '(중', '(CH'])]
                    for cand_list in [lang_specific_candidates, general_candidates]:
                        for cand_col in cand_list:
                            if cand_col in row and pd.notna(row[cand_col]) and str(row[cand_col]).strip():
                                info_text = str(row[cand_col])
                                info_parts.append(f"{info_key}: {info_text[:100]}{'...' if len(info_text) > 100 else ''}")
                                col_found = True; break
                        if col_found: break
                    if col_found: break
            info_html = "<br>".join(info_parts) if info_parts else "추가 정보 없음"
            marker = {'lat': lat_val, 'lng': lon_val, 'title': name_val, 'color': color, 'category': category, 'info': info_html, 'address': address_val, 'importance': row.get('importance_score', 1.0)}
            markers.append(marker)
        except Exception: continue
    return markers

def create_Maps_html(api_key, center_lat, center_lng, markers=None, zoom=13, height=500, language="ko", directions_options=None):
    """Google Maps를 포함하는 HTML 코드 생성 - JS 오류 처리 및 로그 추가"""
    if markers is None: markers = []
    marker_data_js_list = [] 
    for i, marker_info in enumerate(markers):
        title = str(marker_info.get('title', f'마커 {i+1}')).replace("'", "\\'") 
        info_content = str(marker_info.get('info', '세부 정보 없음')).replace("'", "\\\\'") 
        info_content = info_content.replace("\n", "<br>") 
        orig_title = str(marker_info.get('title', f'마커 {i+1}')).replace("'", "\\'") 
        orig_lat = marker_info.get('lat'); orig_lng = marker_info.get('lng')
        
        marker_js = f"""
        {{
            position: {{ lat: {marker_info.get('lat', 0)}, lng: {marker_info.get('lng', 0)} }},
            title: '{title}',
            icon: '{get_marker_icon_url(marker_info.get('color', 'red'))}', 
            info: '<div style="padding: 5px; max-width: 250px; font-family: Arial, sans-serif; font-size: 13px;">' +
                  '<h5 style="margin-top:0; margin-bottom:5px; color:#1976D2;">{title}</h5>' +
                  '<p style="font-size:11px; margin-bottom:3px;"><strong>카테고리:</strong> {marker_info.get('category', 'N/A')}</p>' +
                  '<div style="font-size:11px; line-height:1.3;">{info_content}</div>' +
                  '<button style="font-size:10px; padding:3px 8px; margin-top:5px;" onclick="handleNavigationRequest(\\'{orig_title}\\', {orig_lat}, {orig_lng})">길찾기</button>' +
                  '</div>',
            category: '{marker_info.get('category', '기타')}'
        }}
        """
        marker_data_js_list.append(marker_js)
    
    all_markers_js_str = "[" + ",\n".join(marker_data_js_list) + "]" 

    directions_service_js = ""; directions_renderer_js = ""; calculate_and_display_route_js = ""
    if directions_options and directions_options.get('origin') and directions_options.get('destination'):
        origin_lat = directions_options['origin']['lat']; origin_lng = directions_options['origin']['lng']
        dest_lat = directions_options['destination']['lat']; dest_lng = directions_options['destination']['lng']
        travel_mode = directions_options.get('travel_mode', 'DRIVING').upper() 
        directions_service_js = "const directionsService = new google.maps.DirectionsService();"
        directions_renderer_js = """
        const directionsRenderer = new google.maps.DirectionsRenderer({{
            suppressMarkers: true, polylineOptions: {{ strokeColor: '#FF0000', strokeOpacity: 0.8, strokeWeight: 5 }}
        }});
        directionsRenderer.setMap(map); 
        """
        calculate_and_display_route_js = f"""
        function calculateAndDisplayRoute(directionsService, directionsRenderer) {{
            directionsService.route({{ 
                origin: {{ lat: {origin_lat}, lng: {origin_lng} }},
                destination: {{ lat: {dest_lat}, lng: {dest_lng} }},
                travelMode: google.maps.TravelMode.{travel_mode} 
            }}, (response, status) => {{ 
                if (status === "OK") {{ 
                    directionsRenderer.setDirections(response); 
                    const route = response.routes[0].legs[0];
                    const routeInfo = {{ distance: route.distance.text, duration: route.duration.text }};
                    if (window.parent) window.parent.postMessage({{type: 'streamlit:setComponentValue', value: routeInfo, key: 'route_info'}}, '*');
                }} else {{ window.alert("경로 요청 실패: " + status); }}
            }});
        }}
        calculateAndDisplayRoute(directionsService, directionsRenderer); 
        """

    html_template = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Google Maps</title>
        <script async defer src="https://maps.googleapis.com/maps/api/js?key={api_key}&language={language}&callback=initMap&libraries=marker"></script> 
        <style> #map {{ height: {height}px; width: 100%; }} body {{ margin: 0; padding: 0; }} </style>
    </head>
    <body> <div id="map"></div>
        <script>
            let map; 
            let currentInfoWindow = null; 
            const allMapMarkerObjects = []; 
            const rawMarkersData = {all_markers_js_str}; 

            function initMap() {{ 
                console.log("initMap called"); 
                try {{
                    map = new google.maps.Map(document.getElementById('map'), {{ 
                        center: {{ lat: {center_lat}, lng: {center_lng} }}, 
                        zoom: {zoom}, mapTypeControl: false, streetViewControl: false
                    }});
                    console.log("Map initialized");

                    if (!rawMarkersData || rawMarkersData.length === 0) {{
                        console.log("No markers data to display.");
                    }}
                    
                    rawMarkersData.forEach((markerInfo, index) => {{
                        try {{
                            if (markerInfo.position && typeof markerInfo.position.lat === 'number' && typeof markerInfo.position.lng === 'number') {{
                                const marker = new google.maps.marker.AdvancedMarkerElement({{ 
                                    map: map,
                                    position: markerInfo.position,
                                    title: markerInfo.title || `마커 ${index + 1}`, 
                                    content: createMarkerIconElement(markerInfo.icon) 
                                }});
                                allMapMarkerObjects.push(marker); 
                                console.log("Marker created:", markerInfo.title);

                                if (markerInfo.info) {{ 
                                    const infoWindow = new google.maps.InfoWindow({{ content: markerInfo.info }});
                                    marker.addListener('click', () => {{ 
                                        if (currentInfoWindow) currentInfoWindow.close(); 
                                        infoWindow.open(map, marker); 
                                        currentInfoWindow = infoWindow;
                                    }});
                                }}
                            }} else {{ 
                                console.warn("Invalid position for marker:", markerInfo.title, markerInfo.position);
                            }}
                        }} catch (e) {{ 
                            console.error("Error creating individual marker:", markerInfo.title, e);
                        }}
                    }});
                    console.log("All markers processed. Total created: " + allMapMarkerObjects.length);

                    {directions_service_js} 
                    {directions_renderer_js} 
                    {calculate_and_display_route_js} 

                }} catch (e) {{ 
                    console.error("Error in initMap function:", e);
                }}
            }}

            function createMarkerIconElement(iconUrl) {{
                const img = document.createElement('img');
                img.src = iconUrl;
                img.style.width = '24px'; img.style.height = '24px';
                return img;
            }}
            
            function handleNavigationRequest(title, lat, lng) {{
                if (window.parent) window.parent.postMessage({{ type: 'navigate_to', title: title, lat: lat, lng: lng }}, '*');
            }}

            window.addEventListener('message', event => {{
                if (event.data && event.data.type) {{ 
                    if (event.data.type === 'filter_markers') {{ 
                        const categoryToShow = event.data.category;
                        allMapMarkerObjects.forEach((markerInstance, index) => {{
                            const originalMarkerData = rawMarkersData[index]; 
                            if (originalMarkerData) {{ 
                                if (categoryToShow === 'all' || originalMarkerData.category === categoryToShow) {{
                                    markerInstance.map = map; 
                                }} else {{
                                    markerInstance.map = null; 
                                }}
                            }}
                        }});
                    }} else if (event.data.type === 'set_map_center') {{ 
                        if (map && typeof event.data.lat === 'number' && typeof event.data.lng === 'number') {{
                            map.setCenter({{ lat: event.data.lat, lng: event.data.lng }});
                            if (typeof event.data.zoom === 'number') {{ 
                                map.setZoom(event.data.zoom);
                            }}
                        }}
                    }}
                }}
            }});
        </script>
    </body></html>
    """
    return html_template

def get_marker_icon_url(color_name):
    """색상 이름에 따른 마커 아이콘 URL 반환"""
    color_hex = {"red": "FE7569", "blue": "4285F4", "green": "34A853", "purple": "9C27B0", "orange": "FBBC05", "pink": "E91E63", "gray": "757575", "darkblue": "1A237E", "darkred": "B71C1C"}.get(color_name.lower(), "FE7569")
    return f"https://chart.googleapis.com/chart?chst=d_map_xpin_icon&chld=glyphish_dot|{color_hex}"

def show_google_map(api_key, center_lat, center_lng, markers=None, zoom=13, height=500, language="한국어", directions_options=None):
    """Streamlit에 Google Maps 표시"""
    if not api_key or api_key == "YOUR_FALLBACK_API_KEY" or not api_key.startswith("AIza"):
        st.error("Google Maps API 키가 유효하지 않거나 설정되지 않았습니다. Streamlit secrets를 확인해주세요."); return
    if not markers: markers = []
    map_html = create_Maps_html(api_key, center_lat, center_lng, markers, zoom, height, LANGUAGE_CODES.get(language, "ko"), directions_options)
    st.components.v1.html(map_html, height=height + 20, scrolling=False)

def recommend_courses(tourism_data, travel_styles, num_days, include_children=False, start_point=None, end_point=None):
    """사용자 취향과 일정에 따른 관광 코스 추천"""
    if not tourism_data or not isinstance(tourism_data, list) or len(tourism_data) == 0:
        st.warning("코스 추천용 관광지 데이터 부족. 기본 추천 코스 표시.")
        default_course_type = random.choice(list(RECOMMENDATION_COURSES.keys()))
        default_places_names = RECOMMENDATION_COURSES.get(default_course_type, [])
        daily_default_courses = []
        places_per_day = 3
        for day in range(num_days):
            day_course_places_details = []
            start_idx = day * places_per_day; end_idx = start_idx + places_per_day
            for place_name in default_places_names[start_idx:end_idx]:
                day_course_places_details.append({'title': place_name, 'category': '기타', 'lat': DEFAULT_LOCATION[0] + random.uniform(-0.05, 0.05), 'lng': DEFAULT_LOCATION[1] + random.uniform(-0.05, 0.05), 'importance': 1.0, 'info': f'{place_name} (기본 추천)', 'address': '정보 없음'})
            if day_course_places_details: daily_default_courses.append(day_course_places_details)
        if not daily_default_courses and num_days > 0: daily_default_courses.append([])
        return [p['title'] for day_course in daily_default_courses for p in day_course], default_course_type, daily_default_courses

    scored_places = []
    for place in tourism_data:
        if not all(k in place for k in ['importance', 'category', 'lat', 'lng', 'title']): continue
        score = float(place.get('importance', 1.0))
        for style in travel_styles:
            if style in STYLE_CATEGORY_WEIGHTS:
                category_weights = STYLE_CATEGORY_WEIGHTS[style]
                if place['category'] in category_weights: score *= category_weights[place['category']]
        if include_children:
            child_friendly_categories = ["체육시설", "공원", "미술관/전시"]
            if place['category'] in child_friendly_categories or "놀이" in place.get('title','').lower() or "어린이" in place.get('title','').lower(): score *= 1.3
        scored_place = place.copy(); scored_place['score'] = score; scored_places.append(scored_place)

    if not scored_places:
        st.warning("점수 계산 가능한 유효 관광지 없음. 기본 추천 코스 사용.")
        return [], "기본 코스", [[{'title': p, 'lat':DEFAULT_LOCATION[0], 'lng':DEFAULT_LOCATION[1]} for p in RECOMMENDATION_COURSES["대중적 코스"][:3]]]

    scored_places.sort(key=lambda x: x['score'], reverse=True)
    places_per_day = 3
    candidate_pool_size = max(num_days * places_per_day * 5, 30)
    top_places_pool = scored_places[:min(len(scored_places), candidate_pool_size)]
    if not top_places_pool:
        st.warning("추천 장소 부족. 여행 스타일/일정 변경 요망."); return [], "장소 부족", []

    daily_courses = []; selected_place_titles_overall = set()
    for day_num in range(num_days):
        daily_course_for_this_day = []
        if day_num == 0: current_location_for_day_planning = start_point if start_point else {"lat": DEFAULT_LOCATION[0], "lng": DEFAULT_LOCATION[1], "title": "시작점(기본)"}
        elif daily_courses and daily_courses[-1]: current_location_for_day_planning = daily_courses[-1][-1]
        else: current_location_for_day_planning = {"lat": DEFAULT_LOCATION[0], "lng": DEFAULT_LOCATION[1], "title": "시작점(기본)"}
        available_places_for_day = [p for p in top_places_pool if p['title'] not in selected_place_titles_overall]
        if not available_places_for_day:
            if not daily_course_for_this_day : daily_courses.append([]); continue
        for _ in range(places_per_day): # place_count_this_day 변수 사용 안 함
            if not available_places_for_day: break
            best_next_place = None; highest_adjusted_score = -1
            for place_candidate in available_places_for_day:
                try: distance_km = geodesic((current_location_for_day_planning['lat'], current_location_for_day_planning['lng']), (place_candidate['lat'], place_candidate['lng'])).kilometers
                except Exception: distance_km = float('inf')
                distance_factor = max(0, 1 - (distance_km / 20.0))
                adjusted_score = place_candidate.get('score', 1.0) * (0.6 + 0.4 * distance_factor)
                # 마지막 날, 마지막 장소는 지정된 종료 지점과의 거리도 고려 (선택적 고급 기능)
                # 이 부분은 num_days > 0 이고, places_per_day > 0 일때, 현재 선택하는 장소가 하루의 마지막 장소인지, 그리고 전체 일정의 마지막 날인지 확인해야 함
                # current_selection_is_last_of_day = len(daily_course_for_this_day) == places_per_day -1
                # current_day_is_last_day = day_num == num_days - 1
                # if current_day_is_last_day and current_selection_is_last_of_day and end_point:
                # 위 로직 대신, 단순히 마지막 날이면 종료점 고려
                if day_num == num_days - 1 and end_point: # 마지막 날이면 종료점과의 거리 고려
                    try:
                        dist_to_final_end = geodesic((place_candidate['lat'], place_candidate['lng']), (end_point['lat'], end_point['lng'])).km
                        adjusted_score *= (0.7 + 0.3 * max(0, 1 - (dist_to_final_end / 20.0))) # 종료 지점 가까우면 가산점
                    except: pass

                if adjusted_score > highest_adjusted_score: highest_adjusted_score = adjusted_score; best_next_place = place_candidate
            if best_next_place:
                daily_course_for_this_day.append(best_next_place)
                selected_place_titles_overall.add(best_next_place['title'])
                current_location_for_day_planning = best_next_place
                available_places_for_day = [p for p in available_places_for_day if p['title'] != best_next_place['title']]
            else: break
        daily_courses.append(daily_course_for_this_day)

    course_type_name = "맞춤 추천 코스"
    if travel_styles: course_type_name = f"{' & '.join(travel_styles)} 맞춤 코스"
    if include_children: course_type_name += " (아이와 함께)"
    recommended_place_names = [place['title'] for day_course in daily_courses for place in day_course if day_course]
    if not recommended_place_names and not any(day for day in daily_courses):
        default_course_type = random.choice(list(RECOMMENDATION_COURSES.keys()))
        # default_places_names = RECOMMENDATION_COURSES.get(default_course_type, []) # 이 변수는 사용되지 않음
        daily_default_courses = []
        return [], default_course_type, daily_default_courses
    return recommended_place_names, course_type_name, daily_courses

#################################################
# 페이지 함수
#################################################
def show_login_page():
    """로그인 및 회원가입 페이지"""
    page_header("서울 관광 앱에 오신 것을 환영합니다!")
    users = load_user_credentials()
    login_tab, signup_tab = st.tabs(["로그인", "회원가입"])
    with login_tab:
        st.subheader("로그인")
        with st.form("login_form"):
            username = st.text_input("사용자 이름", key="login_username_input") # 키 변경
            password = st.text_input("비밀번호", type="password", key="login_password_input") # 키 변경
            if st.form_submit_button("로그인"):
                if username in users and users[username] == password:
                    st.session_state.logged_in = True; st.session_state.username = username
                    user_xp_data = load_user_xp()
                    st.session_state.user_xp = user_xp_data
                    if username not in st.session_state.user_xp:
                        st.session_state.user_xp[username] = 0
                        save_user_xp(st.session_state.user_xp)
                    st.success(f"{username}님, 환영합니다!"); change_page("menu"); st.rerun()
                else: st.error("사용자 이름 또는 비밀번호가 잘못되었습니다.")
    with signup_tab:
        st.subheader("회원가입")
        with st.form("signup_form"):
            new_username = st.text_input("새 사용자 이름", key="signup_username_input") # 키 변경
            new_password = st.text_input("새 비밀번호", type="password", key="signup_password_input") # 키 변경
            confirm_password = st.text_input("비밀번호 확인", type="password", key="signup_confirm_password_input") # 키 변경
            if st.form_submit_button("가입하기"):
                if not new_username or not new_password: st.warning("사용자 이름과 비밀번호를 모두 입력해주세요.")
                elif new_password != confirm_password: st.error("비밀번호가 일치하지 않습니다.")
                elif new_username in users: st.error("이미 존재하는 사용자 이름입니다.")
                else:
                    users[new_username] = new_password; save_user_credentials(users)
                    current_xp_data = load_user_xp()
                    current_xp_data[new_username] = 0
                    save_user_xp(current_xp_data)
                    st.session_state.user_xp = current_xp_data
                    st.success("회원가입이 완료되었습니다. 로그인해주세요.")

def show_menu_page():
    """메인 메뉴 페이지"""
    page_header(f"{st.session_state.get('username','사용자')}님, 서울 여행을 계획해보세요!") # username 없을 경우 대비
    level, progress, current_xp = get_user_level(st.session_state.get('username'))
    st.markdown(f"**레벨: {level}** (XP: {current_xp}/{XP_PER_LEVEL * (level + 1)})"); st.progress(int(progress)); st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🗺️ 관광 지도 보기", use_container_width=True, type="primary"): change_page("map"); st.rerun()
        st.markdown("<p style='text-align: center; font-size: 0.9em;'>서울의 다양한 관광지를 지도로 확인하세요.</p>", unsafe_allow_html=True)
    with col2:
        if st.button("📅 맞춤 코스 짜기", use_container_width=True, type="primary"): change_page("course"); st.rerun()
        st.markdown("<p style='text-align: center; font-size: 0.9em;'>여행 스타일과 일정에 맞는 코스를 추천받으세요.</p>", unsafe_allow_html=True)
    st.markdown("---")
    if st.button("📜 저장된 내 코스 보기", use_container_width=True): change_page("history"); st.rerun()
    st.markdown("<p style='text-align: center; font-size: 0.9em;'>이전에 저장한 여행 코스를 확인하고 관리하세요.</p>", unsafe_allow_html=True)
    st.sidebar.title("설정")
    st.sidebar.selectbox("언어 (Language)", list(LANGUAGE_CODES.keys()), key="language", index=list(LANGUAGE_CODES.keys()).index(st.session_state.get("language", "한국어")), on_change=update_language_and_reload_data) # 기본값 설정
    st.sidebar.caption(f"Google Maps API 키가 secrets.toml을 통해 로드되었습니다.")
    if st.sidebar.button("로그아웃"): st.session_state.logged_in = False; st.session_state.username = ""; change_page("login"); st.rerun()

def update_language_and_reload_data():
    """언어 변경 시 데이터 다시 로드 트리거"""
    st.session_state.markers_loaded = False # 마커 로드 상태 초기화
    # 실제 데이터 로드는 각 페이지에서 필요시 수행됨
    st.info(f"{st.session_state.language}로 언어가 변경되었습니다. 관련 페이지에서 데이터가 다시 로드됩니다.")

def show_map_page():
    """지도 페이지 표시"""
    page_header("서울 관광 장소 지도")
    if st.button("← 메뉴로 돌아가기"): change_page("menu"); st.rerun()
    api_key = st.session_state.get("Maps_api_key", "")
    if not api_key or api_key == "YOUR_FALLBACK_API_KEY" or not (isinstance(api_key, str) and api_key.startswith("AIza")):
        st.error("Google Maps API 키가 올바르게 설정되지 않았습니다. 관리자에게 문의하거나 Streamlit secrets를 확인해주세요."); return

    if not st.session_state.get('markers_loaded', False) or not st.session_state.get('all_markers'):
        with st.spinner(f"{st.session_state.language} 관광 데이터를 로드 중... (시간이 다소 소요될 수 있습니다)"):
            loaded_markers = load_excel_files(st.session_state.language)
            if loaded_markers: st.session_state.all_markers = loaded_markers; st.session_state.markers_loaded = True
            else: st.session_state.all_markers = []; st.session_state.markers_loaded = False; st.warning("관광지 데이터를 로드할 수 없었습니다. Excel 파일 또는 설정을 확인해주세요.")
    
    # 사용자 위치 업데이트 로직 (st.text_input의 key를 통해 JS와 통신 시도)
    location_data_json = st.text_input("loc_data_map", key="geolocation_data", disabled=True, label_visibility="collapsed") # 키 다르게 설정
    if location_data_json:
        try:
            loc_data = json.loads(location_data_json)
            if isinstance(loc_data, dict) and 'lat' in loc_data and 'lng' in loc_data:
                if not loc_data.get('error'):
                    # 위치가 실제로 변경되었을 때만 세션 상태 업데이트 및 rerun
                    current_loc = st.session_state.get('user_location', DEFAULT_LOCATION)
                    new_loc = [loc_data['lat'], loc_data['lng']]
                    if geodesic(current_loc, new_loc).meters > 10: # 10미터 이상 변경 시에만 업데이트
                        st.session_state.user_location = new_loc
                        st.info(f"사용자 위치가 업데이트 되었습니다: 위도 {new_loc[0]:.4f}, 경도 {new_loc[1]:.4f}")
                        st.rerun()
        except json.JSONDecodeError: pass # 유효하지 않은 JSON은 조용히 무시
        except Exception as e: st.error(f"위치 데이터 처리 중 오류: {e}") # 그 외 예외는 로깅

    user_location = st.session_state.user_location
    map_display_markers = []; map_center_lat, map_center_lng = user_location[0], user_location[1]; current_zoom = 13
    directions_options = None

    if st.session_state.get('navigation_active', False) and st.session_state.get('navigation_destination'):
        dest = st.session_state.navigation_destination
        st.info(f"'{dest['name']}'(으)로 길찾기 중입니다...")
        map_display_markers.append({'lat': user_location[0], 'lng': user_location[1], 'title': '출발지 (내 위치)', 'color': CATEGORY_COLORS["현재 위치"], 'info': '현재 계신 곳입니다.', 'category': '현재 위치'})
        map_display_markers.append({'lat': dest['lat'], 'lng': dest['lng'], 'title': f"목적지: {dest['name']}", 'color': CATEGORY_COLORS["목적지"], 'info': f"도착 지점: {dest['name']}<br>{dest.get('address','주소 정보 없음')}", 'category': '목적지'})
        directions_options = {"origin": {"lat": user_location[0], "lng": user_location[1]}, "destination": {"lat": dest['lat'], "lng": dest['lng']}, "travel_mode": st.session_state.get("travel_mode", "DRIVING")}
        map_center_lat = (user_location[0] + dest['lat']) / 2; map_center_lng = (user_location[1] + dest['lng']) / 2; current_zoom = 11
        
        route_info_json = st.text_input("route_info_val_map", key="route_info",label_visibility="collapsed", disabled=True) # 키 다르게
        if route_info_json:
            try: route_details = json.loads(route_info_json); st.success(f"예상 경로: 거리 {route_details.get('distance', 'N/A')}, 소요 시간 {route_details.get('duration', 'N/A')}")
            except: pass
        if st.button("길찾기 종료", type="primary"):
            st.session_state.navigation_active = False; st.session_state.navigation_destination = None; st.rerun()
    else:
        map_display_markers.append({'lat': user_location[0], 'lng': user_location[1], 'title': '내 위치', 'color': CATEGORY_COLORS["현재 위치"], 'info': '현재 계신 곳입니다.', 'category': '현재 위치'})
        if st.session_state.get('all_markers'): map_display_markers.extend(st.session_state.all_markers)

    map_col, control_col = st.columns([3, 1])
    with map_col:
        if not map_display_markers and not directions_options: st.warning("지도에 표시할 마커가 없습니다.")
        get_location_position() # JS 위치 요청 함수 호출
        show_google_map(api_key=api_key, center_lat=map_center_lat, center_lng=map_center_lng, markers=map_display_markers, zoom=current_zoom, height=600, language=st.session_state.language, directions_options=directions_options)
    
    with control_col:
        st.subheader("지도 컨트롤")
        if not st.session_state.get('navigation_active', False):
            all_categories_from_data = list(set(m.get('category',"기타") for m in st.session_state.get('all_markers', [])))
            categories = ["all"] + sorted(all_categories_from_data)
            
            selected_category = st.selectbox("카테고리 필터:", categories, index=0, help="선택한 카테고리의 장소만 지도에 표시합니다.", key="map_category_filter")
            if st.button("필터 적용", use_container_width=True, key="map_filter_apply_btn"):
                filter_script = f"<script> if(window.parent) window.parent.postMessage({{type: 'filter_markers', category: '{selected_category}'}}, '*'); </script>"
                st.components.v1.html(filter_script, height=0)
                st.info(f"'{selected_category if selected_category != 'all' else '모든'}' 카테고리 필터가 적용되었습니다.")

            search_term = st.text_input("장소 검색:", placeholder="예: 경복궁, 남산타워", key="map_search_term")
            if search_term and st.session_state.get('all_markers'):
                search_results = [m for m in st.session_state.all_markers if search_term.lower() in m.get('title', '').lower()]
                if search_results:
                    st.write(f"**'{search_term}' 검색 결과:** ({len(search_results)}개)")
                    for i, res_marker in enumerate(search_results[:5]):
                        if st.button(f"{res_marker['title']} ( {res_marker['category']} )", key=f"search_result_btn_{i}_{res_marker['title']}"):
                            center_map_script = f"<script> if(window.parent) window.parent.postMessage({{type: 'set_map_center', lat: {res_marker['lat']}, lng: {res_marker['lng']}, zoom: 16}}, '*'); </script>"
                            st.components.v1.html(center_map_script, height=0)
                            st.info(f"'{res_marker['title']}'(으)로 지도 이동됨.")
                elif search_term: st.info(f"'{search_term}'에 대한 검색 결과가 없습니다.")
            elif search_term: st.info("검색할 관광지 데이터가 없습니다.")
        else:
            st.subheader("길찾기 옵션")
            travel_modes = {"DRIVING": "자동차", "WALKING": "도보", "BICYCLING": "자전거", "TRANSIT": "대중교통"}
            current_travel_mode = st.session_state.get("travel_mode", "DRIVING")
            selected_mode_key = st.radio("이동 수단:", list(travel_modes.keys()), index=list(travel_modes.keys()).index(current_travel_mode) ,format_func=lambda x: travel_modes[x], horizontal=True, key="map_travel_mode_radio")
            if current_travel_mode != selected_mode_key:
                st.session_state.travel_mode = selected_mode_key; st.rerun()

def show_course_page():
    """관광 코스 추천 페이지"""
    page_header("서울 관광 코스 짜주기")
    if st.button("← 메뉴로 돌아가기"): change_page("menu"); st.rerun()
    if not st.session_state.get('markers_loaded', False) or not st.session_state.get('all_markers'):
        with st.spinner(f"{st.session_state.language} 코스 추천용 관광 데이터를 로드 중..."):
            loaded_markers = load_excel_files(st.session_state.language)
            if loaded_markers: st.session_state.all_markers = loaded_markers; st.session_state.markers_loaded = True
            else: st.session_state.all_markers = []; st.session_state.markers_loaded = False; st.error("코스 추천에 필요한 관광지 데이터를 로드할 수 없습니다."); return
    st.markdown("###  여행 정보 입력")
    cols_info = st.columns([1,1,1])
    with cols_info[0]: start_date = st.date_input("여행 시작일", value=datetime.now().date(), min_value=datetime.now().date(), key="course_start_date")
    with cols_info[1]: num_days = st.number_input("여행 기간 (일)", min_value=1, max_value=7, value=3, key="course_num_days")
    with cols_info[2]: include_children = st.checkbox("아이와 함께하는 여행인가요?", value=False, key="course_include_children")
    st.markdown("### 여행 스타일 선택 (다중 선택 가능)")
    available_styles = list(STYLE_CATEGORY_WEIGHTS.keys())
    num_styles_half = (len(available_styles) + 1) // 2
    style_cols = st.columns(2); selected_styles = []
    for i, style in enumerate(available_styles):
        current_col = style_cols[0] if i < num_styles_half else style_cols[1]
        if current_col.checkbox(style, key=f"course_style_{style}"): selected_styles.append(style)
    if not selected_styles: st.info("선호하는 여행 스타일을 선택하시면 더 정확한 코스를 추천해 드립니다. (선택하지 않으면 일반적인 코스로 추천)")
    generate_course_disabled = not st.session_state.get('all_markers', False)
    if generate_course_disabled: st.warning("관광지 데이터가 로드되지 않아 코스를 생성할 수 없습니다.")
    
    if st.button("AI ✨ 코스 생성하기", type="primary", use_container_width=True, disabled=generate_course_disabled, key="course_generate_btn"):
        if not st.session_state.get('all_markers'): st.error("코스 추천을 위한 관광 데이터가 없습니다.")
        else:
            with st.spinner("AI가 최적의 관광 코스를 생성 중입니다... (최대 30초 소요)"):
                time.sleep(random.uniform(0.5, 1.5))
                recommended_places_names, course_type_name, daily_courses_details = recommend_courses(st.session_state.all_markers, selected_styles if selected_styles else ["대중적 코스"], num_days, include_children)
            if not recommended_places_names and not any(day for day in daily_courses_details): st.error("선택하신 조건에 맞는 코스를 생성할 수 없었습니다.")
            else:
                st.success("✨ 나만의 맞춤 코스가 생성되었습니다! ✨")
                st.session_state.generated_course_name = course_type_name
                st.session_state.generated_course_details_str = f"{num_days}일 일정, 시작일: {start_date.strftime('%Y-%m-%d')}"
                st.session_state.generated_daily_courses = daily_courses_details
                st.rerun() # 코스 생성 후 UI 업데이트 위해 rerun

    if 'generated_daily_courses' in st.session_state and st.session_state.generated_daily_courses:
        course_name_to_display = st.session_state.generated_course_name
        course_details_str_to_display = st.session_state.generated_course_details_str
        daily_courses_to_display = st.session_state.generated_daily_courses
        st.markdown(f"## 📌 {course_name_to_display}"); st.markdown(f"**{course_details_str_to_display}**"); st.markdown("---")
        
        tab_titles = [f"Day {i+1}" for i in range(len(daily_courses_to_display))] + ["🗺️ 전체 코스 지도"]
        course_tabs = st.tabs(tab_titles)

        for day_idx, day_course_places in enumerate(daily_courses_to_display):
            with course_tabs[day_idx]:
                st.subheader(f"Day {day_idx + 1} 일정")
                if not day_course_places: st.info("이 날짜에는 추천 장소가 없습니다."); continue
                time_slots_display = ["오전 (09:00-12:00)", "점심 및 이동 (12:00-14:00)", "오후 (14:00-17:00)", "저녁 이후 (17:00~)"]
                for i, place_details in enumerate(day_course_places):
                    current_time_slot_display = time_slots_display[i % len(time_slots_display)]
                    with st.container(border=True):
                        st.markdown(f"**🕙 {current_time_slot_display}: {place_details.get('title', '장소 이름 없음')}**")
                        st.caption(f"📍 분류: {place_details.get('category', '미분류')} | 🌟 예상 점수: {place_details.get('score', 0):.1f}")
                        expander_content = f"주소: {place_details.get('address', '정보 없음')}<br>추가 정보: {place_details.get('info', '세부 정보 없음')}"
                        with st.expander("상세 정보 보기/숨기기"): st.markdown(expander_content, unsafe_allow_html=True)
                        if st.button(f"'{place_details.get('title')}' 길찾기", key=f"course_nav_day{day_idx}_place{i}", help="지도로 이동하여 길찾기를 시작합니다."):
                            st.session_state.navigation_destination = {'name': place_details.get('title'), 'lat': place_details.get('lat'), 'lng': place_details.get('lng'), 'address': place_details.get('address')}
                            st.session_state.navigation_active = True; change_page("map"); st.rerun()
                    st.markdown("---")
        with course_tabs[-1]:
            st.subheader("🗺️ 전체 코스 지도에 표시"); api_key = st.session_state.get("Maps_api_key")
            if not api_key or api_key == "YOUR_FALLBACK_API_KEY" or not api_key.startswith("AIza"): st.error("Google Maps API 키가 유효하지 않습니다.")
            elif daily_courses_to_display and any(day for day in daily_courses_to_display):
                course_map_markers = []; all_lats, all_lngs = [], []
                for day_idx, day_items in enumerate(daily_courses_to_display):
                    if not day_items: continue
                    for place_idx, place_item in enumerate(day_items):
                        if not all(k in place_item for k in ['lat', 'lng', 'title']): continue
                        marker_colors_by_day = ['#FF5733', '#33FF57', '#3357FF', '#FF33A1', '#A133FF', '#33FFA1', '#FF8C33']
                        color = marker_colors_by_day[day_idx % len(marker_colors_by_day)]
                        all_lats.append(place_item['lat']); all_lngs.append(place_item['lng'])
                        course_map_markers.append({'lat': place_item['lat'], 'lng': place_item['lng'], 'title': f"D{day_idx+1}-{place_idx+1}: {place_item['title']}", 'color': color, 'category': place_item.get('category', '코스 장소'), 'info': f"<b>Day {day_idx+1}</b><br>{place_item.get('title')}<br><small>{place_item.get('address','주소 없음')}</small>", 'importance': 1.5})
                if course_map_markers:
                    center_lat = sum(all_lats) / len(all_lats) if all_lats else DEFAULT_LOCATION[0]
                    center_lng = sum(all_lngs) / len(all_lngs) if all_lngs else DEFAULT_LOCATION[1]
                    show_google_map(api_key=api_key, center_lat=center_lat, center_lng=center_lng, markers=course_map_markers, zoom=10, height=500, language=st.session_state.language)
                else: st.info("코스 장소의 위치 정보가 없어 지도에 표시할 수 없습니다.")
            else: st.info("표시할 코스가 없습니다.")
        if st.button("💾 이 코스 저장하기", use_container_width=True, key="course_save_btn"):
            if st.session_state.get("username"): # username 존재 확인
                daily_courses_for_saving = []
                for day_course in daily_courses_to_display:
                    saved_day = []
                    if day_course:
                        for place in day_course: saved_day.append({'title': place.get('title'), 'category': place.get('category'), 'lat': place.get('lat'), 'lng': place.get('lng'), 'address': place.get('address'), 'info': place.get('info')})
                    daily_courses_for_saving.append(saved_day)
                save_user_course(st.session_state.username, course_name_to_display, course_details_str_to_display, daily_courses_for_saving)
            else: st.warning("로그인해야 코스를 저장할 수 있습니다.")
        if st.button("🔄 다른 코스 생성하기", use_container_width=True, key="course_regenerate_btn"):
            if 'generated_daily_courses' in st.session_state: del st.session_state.generated_daily_courses
            if 'generated_course_name' in st.session_state: del st.session_state.generated_course_name
            if 'generated_course_details_str' in st.session_state: del st.session_state.generated_course_details_str
            st.rerun()

def show_history_page():
    """저장된 내 여행 코스 보기 페이지"""
    page_header("저장된 내 여행 코스")
    if st.button("← 메뉴로 돌아가기"): change_page("menu"); st.rerun()
    username = st.session_state.get("username")
    if not username: st.warning("로그인이 필요합니다."); return
    saved_courses_all_users = load_saved_courses()
    user_courses = saved_courses_all_users.get(username, [])
    if not user_courses: st.info("아직 저장된 코스가 없습니다."); return
    st.subheader(f"'{username}'님의 저장된 코스 목록 ({len(user_courses)}개)")
    user_courses.sort(key=lambda x: x.get("saved_at", "1970-01-01 00:00:00"), reverse=True)
    for idx, course_data in enumerate(user_courses):
        course_name = course_data.get("course_name", f"저장된 코스 {idx+1}")
        course_details_str = course_data.get("details", "상세 정보 없음")
        saved_at_str = course_data.get("saved_at", "날짜 정보 없음")
        daily_courses_data = course_data.get("daily_courses", [])
        with st.expander(f"**{course_name}** (저장일: {saved_at_str}) - {course_details_str}"):
            st.markdown(f"#### {course_name}")
            if not daily_courses_data or not any(day for day in daily_courses_data):
                st.write("이 코스에는 장소 정보가 없거나 비어있습니다.")
                if st.button("이 코스 삭제하기", key=f"history_delete_empty_course_{idx}", type="secondary"): # 키 변경
                    user_courses.pop(idx); saved_courses_all_users[username] = user_courses
                    DATA_DIR.mkdir(parents=True, exist_ok=True)
                    with open(SAVED_COURSES_FILE, 'w', encoding='utf-8') as f: json.dump(saved_courses_all_users, f, indent=4, ensure_ascii=False)
                    st.success(f"'{course_name}' 코스가 삭제되었습니다."); st.rerun()
                continue
            
            tab_titles_hist = [f"Day {i+1}" for i in range(len(daily_courses_data))] + ["🗺️ 전체 지도"]
            course_display_tabs = st.tabs(tab_titles_hist)

            for day_idx, day_places in enumerate(daily_courses_data):
                with course_display_tabs[day_idx]:
                    st.markdown(f"##### Day {day_idx + 1} 일정")
                    if not day_places: st.info("이 날짜에는 계획된 장소가 없습니다."); continue
                    for place_idx, place in enumerate(day_places):
                        st.markdown(f"**{place_idx+1}. {place.get('title', '이름 없는 장소')}**")
                        st.caption(f"분류: {place.get('category', '미분류')}")
                        if place.get('address') and place.get('address') != "정보 없음": st.caption(f"주소: {place.get('address')}")
                        if place.get('info') and place.get('info') != "추가 정보 없음":
                            with st.popover("추가 정보", use_container_width=True, key=f"hist_popover_day{day_idx}_place{place_idx}_{idx}"): # 키에 컨테이너 타입 명시
                                st.markdown(place.get('info'), unsafe_allow_html=True)
                        if st.button(f"'{place.get('title')}' 지도에서 보기/길찾기", key=f"hist_nav_btn_day{day_idx}_place{place_idx}_{idx}"): # 키에 버튼 명시
                            st.session_state.navigation_destination = {'name': place.get('title'), 'lat': place.get('lat'), 'lng': place.get('lng'), 'address': place.get('address')}
                            st.session_state.navigation_active = True; change_page("map"); st.rerun()
                        st.divider()
            with course_display_tabs[-1]:
                st.markdown("##### 전체 코스 지도"); api_key = st.session_state.get("Maps_api_key")
                if not api_key or api_key == "YOUR_FALLBACK_API_KEY" or not api_key.startswith("AIza"): st.error("Google Maps API 키가 유효하지 않습니다.")
                else:
                    hist_map_markers = []; hist_lats, hist_lngs = [], []
                    for day_i, day_p_list in enumerate(daily_courses_data):
                        if not day_p_list: continue
                        for place_i, p_item in enumerate(day_p_list):
                            if p_item and 'lat' in p_item and 'lng' in p_item:
                                hist_lats.append(p_item['lat']); hist_lngs.append(p_item['lng'])
                                marker_colors_by_day = ['#FF5733', '#33FF57', '#3357FF', '#FF33A1', '#A133FF']
                                hist_map_markers.append({'lat': p_item['lat'], 'lng': p_item['lng'], 'title': f"D{day_i+1}: {p_item.get('title', '')}", 'color': marker_colors_by_day[day_i % len(marker_colors_by_day)], 'info': f"<b>{p_item.get('title', '')}</b><br>{p_item.get('address','')}"})
                    if hist_map_markers:
                        center_lat_hist = sum(hist_lats) / len(hist_lats) if hist_lats else DEFAULT_LOCATION[0]
                        center_lng_hist = sum(hist_lngs) / len(hist_lngs) if hist_lngs else DEFAULT_LOCATION[1]
                        show_google_map(api_key, center_lat_hist, center_lng_hist, hist_map_markers, zoom=10, language=st.session_state.language)
                    else: st.info("표시할 장소의 위치 정보가 부족합니다.")
            if st.button("🗑️ 이 코스 삭제하기", key=f"history_delete_course_btn_{idx}", type="secondary"): # 키에 버튼 명시
                user_courses.pop(idx); saved_courses_all_users[username] = user_courses
                DATA_DIR.mkdir(parents=True, exist_ok=True)
                with open(SAVED_COURSES_FILE, 'w', encoding='utf-8') as f: json.dump(saved_courses_all_users, f, indent=4, ensure_ascii=False)
                st.success(f"'{course_name}' 코스가 삭제되었습니다."); st.rerun()

#################################################
# 메인 앱 로직
#################################################
def main():
    """메인 애플리케이션 실행 함수"""
    # 데이터 폴더 및 에셋 폴더 생성 (최초 실행 시)
    DATA_DIR.mkdir(parents=True, exist_ok=True) # 사용자 데이터 저장용
    ASSET_DIR.mkdir(parents=True, exist_ok=True) # Excel 등 정적 파일용

    # CSS 스타일 적용 및 세션 초기화는 앱 실행 시 한 번만
    if 'app_initialized' not in st.session_state:
        apply_custom_css()
        init_session_state()
        st.session_state.app_initialized = True

    # 로그인 상태에 따른 페이지 라우팅
    if not st.session_state.get("logged_in", False) and st.session_state.get("current_page", "login") != "login":
        st.session_state.current_page = "login" # 로그아웃 상태이고 현재 페이지가 로그인이 아니면 로그인 페이지로
    
    current_page = st.session_state.get("current_page", "login") # 현재 페이지 가져오기

    # 페이지에 따른 함수 호출
    if current_page == "login": show_login_page()
    elif current_page == "menu": show_menu_page()
    elif current_page == "map": show_map_page()
    elif current_page == "course": show_course_page()
    elif current_page == "history": show_history_page()
    else: # 알 수 없는 페이지면 기본 페이지로 (로그인 또는 메뉴)
        st.session_state.current_page = "login" if not st.session_state.get("logged_in") else "menu"
        st.rerun() # 페이지 상태 변경 후 새로고침

if __name__ == "__main__":
    main()
