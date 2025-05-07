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
    "기타": "gray"
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

#################################################
# 유틸리티 함수
#################################################

def apply_custom_css():
    """앱 전체에 적용되는 커스텀 CSS"""
    st.markdown("""
    <style>
        .main-header {color:#1E88E5; font-size:30px; font-weight:bold; text-align:center;}
        .sub-header {color:#1976D2; font-size:24px; font-weight:bold; margin-top:20px;}
        .card {
            border-radius:10px; 
            padding:20px; 
            margin:10px 0px; 
            background-color:#f0f8ff; 
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            transition: transform 0.3s;
        }
        .card:hover {
            transform: translateY(-5px);
            box-shadow: 0 8px 16px rgba(0,0,0,0.2);
        }
        .blue-btn {
            background-color:#1976D2; 
            color:white; 
            padding:10px 20px; 
            border-radius:5px; 
            border:none;
            text-align:center;
            cursor:pointer;
            font-weight:bold;
        }
        .xp-text {
            color:#4CAF50; 
            font-weight:bold;
        }
        .stTabs [data-baseweb="tab-list"] {
            gap: 24px;
        }
        .stTabs [data-baseweb="tab"] {
            height: 50px;
            white-space: pre-wrap;
            border-radius: 4px 4px 0 0;
            gap: 1px;
            padding-top: 10px;
            padding-bottom: 10px;
        }
        div[data-testid="stHorizontalBlock"] > div:first-child {
            border: none !important;
        }
    </style>
    """, unsafe_allow_html=True)

def page_header(title):
    """페이지 헤더 표시"""
    st.markdown(f'<div class="main-header">{title}</div>', unsafe_allow_html=True)

def display_user_level_info():
    """사용자 레벨 및 경험치 정보 표시"""
    username = st.session_state.username
    user_xp = st.session_state.user_xp.get(username, 0)
    user_level = calculate_level(user_xp)
    xp_percentage = calculate_xp_percentage(user_xp)
    
    col1, col2 = st.columns([1, 4])
    with col1:
        main_image_path = Path("asset") / "SeoulTripView.png"
        if main_image_path.exists():
            st.image(main_image_path, use_container_width=True)
        else:
            st.info("이미지를 찾을 수 없습니다: asset/SeoulTripView.png")
    with col2:
        st.markdown(f"**레벨 {user_level}** ({user_xp} XP)")
        st.progress(xp_percentage / 100)
        st.caption(f"다음 레벨까지 {XP_PER_LEVEL - (user_xp % XP_PER_LEVEL)} XP 남음")

def change_page(page):
    """페이지 전환 함수"""
    st.session_state.current_page = page
    
    # 페이지 전환 시 일부 상태 초기화
    if page != "map":
        st.session_state.clicked_location = None
        st.session_state.navigation_active = False
        st.session_state.navigation_destination = None
        st.session_state.transport_mode = None

def authenticate_user(username, password):
    """사용자 인증 함수"""
    if "users" not in st.session_state:
        return False
    
    return username in st.session_state.users and st.session_state.users[username] == password

def register_user(username, password):
    """사용자 등록 함수"""
    if "users" not in st.session_state:
        st.session_state.users = {"admin": "admin"}
    
    if username in st.session_state.users:
        return False
    
    st.session_state.users[username] = password
    
    # 신규 사용자 데이터 초기화
    if "user_xp" not in st.session_state:
        st.session_state.user_xp = {}
    st.session_state.user_xp[username] = 0
    
    if "user_visits" not in st.session_state:
        st.session_state.user_visits = {}
    st.session_state.user_visits[username] = []
    
    save_session_data()
    return True

def logout_user():
    """로그아웃 함수"""
    st.session_state.logged_in = False
    st.session_state.username = ""
    change_page("login")

def init_session_state():
    """세션 상태 초기화"""
    # 로그인 관련 상태
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "username" not in st.session_state:
        st.session_state.username = ""
    if "current_page" not in st.session_state:
        st.session_state.current_page = "login"
        
    # 사용자 데이터
    if "users" not in st.session_state:
        st.session_state.users = {"admin": "admin"}  # 기본 관리자 계정
    if "user_xp" not in st.session_state:
        st.session_state.user_xp = {}
    if "user_visits" not in st.session_state:
        st.session_state.user_visits = {}
        
    # 지도 관련 상태
    if 'language' not in st.session_state:
        st.session_state.language = "한국어"
    if 'clicked_location' not in st.session_state:
        st.session_state.clicked_location = None
    if 'navigation_active' not in st.session_state:
        st.session_state.navigation_active = False
    if 'navigation_destination' not in st.session_state:
        st.session_state.navigation_destination = None
    if 'transport_mode' not in st.session_state:
        st.session_state.transport_mode = None
    
    # 관광 데이터 관련 상태
    if 'all_markers' not in st.session_state:
        st.session_state.all_markers = []
    if 'markers_loaded' not in st.session_state:
        st.session_state.markers_loaded = False
    if 'tourism_data' not in st.session_state:
        st.session_state.tourism_data = []
    if 'saved_courses' not in st.session_state:
        st.session_state.saved_courses = []
        
    # Google Maps API 키
    if "google_maps_api_key" not in st.session_state:
        # secrets.toml에서 가져오기 시도
        try:
            st.session_state.google_maps_api_key = st.secrets["google_maps_api_key"]
        except:
            # 기본값 설정 (실제 사용시 자신의 API 키로 변경 필요)
            st.session_state.google_maps_api_key = "YOUR_GOOGLE_MAPS_API_KEY"
    
    # 저장된 세션 데이터 로드
    load_session_data()

def load_session_data():
    """저장된 세션 데이터 로드"""
    try:
        if os.path.exists(SESSION_DATA_FILE):
            with open(SESSION_DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                # 데이터 복원
                st.session_state.users = data.get("users", {"admin": "admin"})
                st.session_state.user_visits = data.get("user_visits", {})
                st.session_state.user_xp = data.get("user_xp", {})
                st.session_state.saved_courses = data.get("saved_courses", [])
                return True
    except Exception as e:
        st.error(f"세션 데이터 로드 오류: {e}")
    return False

def save_session_data():
    """세션 데이터 저장"""
    try:
        # 데이터 폴더 생성
        os.makedirs(os.path.dirname(SESSION_DATA_FILE), exist_ok=True)
        
        data = {
            "users": st.session_state.users,
            "user_visits": st.session_state.user_visits,
            "user_xp": st.session_state.user_xp,
            "saved_courses": st.session_state.saved_courses
        }
        
        with open(SESSION_DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        st.error(f"세션 데이터 저장 오류: {e}")
        return False

def calculate_level(xp):
    """레벨 계산 함수"""
    return int(xp / XP_PER_LEVEL) + 1

def calculate_xp_percentage(xp):
    """경험치 비율 계산 (다음 레벨까지)"""
    current_level = calculate_level(xp)
    xp_for_current_level = (current_level - 1) * XP_PER_LEVEL
    xp_for_next_level = current_level * XP_PER_LEVEL
    
    xp_in_current_level = xp - xp_for_current_level
    xp_needed_for_next = xp_for_next_level - xp_for_current_level
    
    return int((xp_in_current_level / xp_needed_for_next) * 100)

def add_visit(username, place_name, lat, lng):
    """방문 기록 추가"""
    if username not in st.session_state.user_visits:
        st.session_state.user_visits[username] = []
    
    # XP 획득
    if username not in st.session_state.user_xp:
        st.session_state.user_xp[username] = 0
    
    xp_gained = PLACE_XP.get(place_name, 10)  # 기본 10XP, 장소별로 다른 XP
    st.session_state.user_xp[username] += xp_gained
    
    # 방문 데이터 생성
    visit_data = {
        "place_name": place_name,
        "latitude": lat,
        "longitude": lng,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "date": datetime.now().strftime("%Y-%m-%d"),
        "xp_gained": xp_gained,
        "rating": None
    }
    
    # 중복 방문 검사 (같은 날, 같은 장소)
    is_duplicate = False
    for visit in st.session_state.user_visits[username]:
        if (visit["place_name"] == place_name and 
            visit["date"] == visit_data["date"]):
            is_duplicate = True
            break
    
    if not is_duplicate:
        st.session_state.user_visits[username].append(visit_data)
        save_session_data()  # 방문 기록 저장
        return True, xp_gained
    return False, 0

def get_location_position():
    """사용자의 현재 위치를 반환"""
    try:
        from streamlit_js_eval import get_geolocation
        
        location = get_geolocation()
        if location and "coords" in location:
            return [location["coords"]["latitude"], location["coords"]["longitude"]]
    except Exception as e:
        st.warning(f"위치 정보를 가져올 수 없습니다: {e}")
        
    return DEFAULT_LOCATION  # 기본 위치 (서울시청)

#################################################
# 데이터 로드 함수
#################################################

def load_excel_files(language="한국어"):
    """데이터 폴더에서 Excel 파일 로드 - 개선된 버전"""
    data_folder = Path("asset")
    all_markers = []
    
    # 파일이 존재하는지 확인
    if not data_folder.exists():
        st.error(f"데이터 폴더({data_folder})가 존재하지 않습니다.")
        return []
    
    # 파일 목록 확인
    excel_files = list(data_folder.glob("*.xlsx"))
    
    if not excel_files:
        st.error("Excel 파일을 찾을 수 없습니다. GitHub 저장소의 파일을 확인해주세요.")
        st.info("확인할 경로: asset/*.xlsx")
        return []
    
    # 찾은 파일 목록 표시
    st.success(f"{len(excel_files)}개의 Excel 파일을 찾았습니다.")
    for file_path in excel_files:
        st.info(f"파일 발견: {file_path.name}")
    
    # 각 파일 처리
    for file_path in excel_files:
        try:
            # 파일 카테고리 결정
            file_category = "기타"
            file_name_lower = file_path.name.lower()
            
            for category, keywords in FILE_CATEGORIES.items():
                if any(keyword.lower() in file_name_lower for keyword in keywords):
                    file_category = category
                    break
            
            # 파일 로드
            st.info(f"'{file_path.name}' 파일을 '{file_category}' 카테고리로 로드 중...")
            df = pd.read_excel(file_path, engine='openpyxl')
            
            if df.empty:
                st.warning(f"'{file_path.name}' 파일에 데이터가 없습니다.")
                continue
            
            # 데이터프레임 기본 정보 출력
            st.success(f"'{file_path.name}' 파일 로드 완료: {len(df)}행, {len(df.columns)}열")
            
            # 데이터 전처리 및 마커 변환
            markers = process_dataframe(df, file_category, language)
            
            if markers:
                all_markers.extend(markers)
                st.success(f"'{file_path.name}'에서 {len(markers)}개 마커 추출 성공")
            else:
                st.warning(f"'{file_path.name}'에서 유효한 마커를 추출할 수 없습니다.")
            
        except Exception as e:
            st.error(f"'{file_path.name}' 파일 처리 오류: {str(e)}")
            import traceback
            st.error(traceback.format_exc())
    
    if not all_markers:
        st.error("모든 파일에서 유효한 마커를 찾을 수 없습니다.")
    else:
        st.success(f"총 {len(all_markers)}개의 마커를 성공적으로 로드했습니다.")
    
    return all_markers

def process_dataframe(df, category, language="한국어"):
    """데이터프레임을 Google Maps 마커 형식으로 변환 - X, Y 좌표 처리 개선"""
    markers = []
    
    # 1. X, Y 좌표 열 감지 (대소문자 및 다양한 이름 형식 지원)
    x_candidates = [col for col in df.columns if ('x' in col.lower() or 'X' in col) and '좌표' in col]
    y_candidates = [col for col in df.columns if ('y' in col.lower() or 'Y' in col) and '좌표' in col]
    
    # 중국어 좌표 열 처리
    if not x_candidates:
        x_candidates = [col for col in df.columns if 'X坐标' in col or 'x坐标' in col]
    if not y_candidates:
        y_candidates = [col for col in df.columns if 'Y坐标' in col or 'y坐标' in col]
    
    # 단순 X, Y 열 확인
    if not x_candidates:
        x_candidates = [col for col in df.columns if col.upper() == 'X' or col.lower() == 'x']
    if not y_candidates:
        y_candidates = [col for col in df.columns if col.upper() == 'Y' or col.lower() == 'y']
    
    # 경도/위도 열 확인
    if not x_candidates:
        x_candidates = [col for col in df.columns if '경도' in col or 'longitude' in col.lower() or 'lon' in col.lower()]
    if not y_candidates:
        y_candidates = [col for col in df.columns if '위도' in col or 'latitude' in col.lower() or 'lat' in col.lower()]
    
    # X, Y 좌표 열 선택
    x_col = x_candidates[0] if x_candidates else None
    y_col = y_candidates[0] if y_candidates else None
    
    # 2. X, Y 좌표 열이 없는 경우 숫자 열에서 자동 감지
    if not x_col or not y_col:
        st.warning(f"'{category}' 데이터에서 명시적인 X, Y 좌표 열을 찾을 수 없습니다. 숫자 열에서 자동 감지를 시도합니다.")
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        
        if len(numeric_cols) >= 2:
            # 각 열의 값 범위를 분석하여 위경도 추정
            for col in numeric_cols:
                if df[col].dropna().empty:
                    continue
                    
                # 열의 값 통계 확인
                col_mean = df[col].mean()
                col_min = df[col].min()
                col_max = df[col].max()
                
                # 경도(X) 범위 확인: 한국 경도는 대략 124-132
                if 120 <= col_mean <= 140:
                    x_col = col
                    st.info(f"X좌표(경도)로 '{col}' 열을 자동 감지했습니다. 범위: {col_min:.2f}~{col_max:.2f}")
                
                # 위도(Y) 범위 확인: 한국 위도는 대략 33-43
                elif 30 <= col_mean <= 45:
                    y_col = col
                    st.info(f"Y좌표(위도)로 '{col}' 열을 자동 감지했습니다. 범위: {col_min:.2f}~{col_max:.2f}")
    
    # 3. 좌표 열을 여전히 못 찾은 경우 마지막 시도: 단순히 마지막 두 개의 숫자 열 사용
    if not x_col or not y_col:
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        if len(numeric_cols) >= 2:
            x_col = numeric_cols[-2]  # 뒤에서 두 번째 숫자 열
            y_col = numeric_cols[-1]  # 마지막 숫자 열
            st.warning(f"좌표 추정: X좌표='{x_col}', Y좌표='{y_col}' (마지막 두 숫자 열)")
    
    # 4. 여전히 좌표 열을 찾지 못한 경우
    if not x_col or not y_col:
        st.error(f"'{category}' 데이터에서 X, Y 좌표 열을 찾을 수 없습니다.")
        st.error(f"사용 가능한 열: {', '.join(df.columns.tolist())}")
        return []
    
    # 5. 좌표 데이터 전처리
    st.success(f"좌표 열 감지 성공: X='{x_col}', Y='{y_col}'")
    
    # NaN 값 처리
    df = df.dropna(subset=[x_col, y_col])
    
    # 문자열을 숫자로 변환
    try:
        df[x_col] = pd.to_numeric(df[x_col], errors='coerce')
        df[y_col] = pd.to_numeric(df[y_col], errors='coerce')
        df = df.dropna(subset=[x_col, y_col])  # 변환 후 NaN이 된 값 제거
    except Exception as e:
        st.warning(f"좌표 변환 오류: {str(e)}")
    
    # 0 값 제거
    df = df[(df[x_col] != 0) & (df[y_col] != 0)]
    
    # 6. 좌표 유효성 검증 및 교정
    # 한국 영역 좌표 체크 (경도 124-132, 위도 33-43)
    valid_coords = (df[x_col] >= 124) & (df[x_col] <= 132) & (df[y_col] >= 33) & (df[y_col] <= 43)
    
    # X,Y가 바뀐 경우 체크 (Y가 경도, X가 위도인 경우)
    swapped_coords = (df[y_col] >= 124) & (df[y_col] <= 132) & (df[x_col] >= 33) & (df[x_col] <= 43)
    
    # X,Y가 바뀐 경우 자동 교정
    if swapped_coords.sum() > valid_coords.sum():
        st.warning(f"'{category}' 데이터의 X,Y 좌표가 바뀐 것으로 보입니다. 자동으로 교정합니다.")
        df['temp_x'] = df[x_col].copy()
        df[x_col] = df[y_col]
        df[y_col] = df['temp_x']
        df = df.drop('temp_x', axis=1)
        
        # 다시 유효성 검증
        valid_coords = (df[x_col] >= 124) & (df[x_col] <= 132) & (df[y_col] >= 33) & (df[y_col] <= 43)
    
    # 유효한 좌표만 필터링
    valid_df = df[valid_coords]
    
    if valid_df.empty:
        st.error(f"'{category}' 데이터에 유효한 한국 영역 좌표가 없습니다.")
        st.info(f"원본 좌표 범위: X({df[x_col].min():.2f}~{df[x_col].max():.2f}), Y({df[y_col].min():.2f}~{df[y_col].max():.2f})")
        
        # 좌표 값 10000으로 나누기 시도 (혹시 UTM 좌표계인 경우)
        if df[x_col].max() > 1000000 or df[y_col].max() > 1000000:
            st.warning("좌표값이 매우 큽니다. UTM 좌표계일 수 있어 10000으로 나누어 변환을 시도합니다.")
            df[x_col] = df[x_col] / 10000
            df[y_col] = df[y_col] / 10000
            
            # 다시 유효성 검증
            valid_coords = (df[x_col] >= 124) & (df[x_col] <= 132) & (df[y_col] >= 33) & (df[y_col] <= 43)
            valid_df = df[valid_coords]
            
            if not valid_df.empty:
                st.success(f"좌표 변환 성공! 유효한 좌표 {len(valid_df)}개 발견")
            else:
                st.error("좌표 변환 실패! 유효한 한국 영역 좌표를 찾을 수 없습니다.")
                return []
    
    # 7. 이름 열 결정
    name_col = get_name_column(df, category, language)
    
    # 8. 주소 열 결정
    address_col = get_address_column(df, language)
    
    # 9. 각 행을 마커로 변환
    success_count = 0
    for idx, row in valid_df.iterrows():
        try:
            # 기본 정보
            if name_col and pd.notna(row.get(name_col)):
                name = str(row[name_col])
            else:
                name = f"{category} #{idx+1}"
                
            # 좌표 추출
            lat = float(row[y_col])  # 위도 (Y좌표)
            lng = float(row[x_col])  # 경도 (X좌표)
            
            # 좌표값 유효성 최종 확인
            if not (33 <= lat <= 43 and 124 <= lng <= 132):
                continue  # 유효하지 않은 좌표 건너뛰기
            
            # 주소 정보
            address = ""
            if address_col and address_col in row and pd.notna(row[address_col]):
                address = row[address_col]
            
            # 정보창 HTML 구성
            info = build_info_html(row, name, address, category)
            
            # 마커 색상 결정
            color = CATEGORY_COLORS.get(category, "gray")
            
            # 마커 생성
            marker = {
                'lat': lat,
                'lng': lng,
                'title': name,
                'color': color,
                'category': category,
                'info': info,
                'address': address
            }
            markers.append(marker)
            success_count += 1
            
        except Exception as e:
            print(f"마커 생성 오류 (행 #{idx}): {e}")
            continue
    
    st.success(f"'{category}' 데이터에서 {success_count}개의 마커를 성공적으로 생성했습니다.")
    return markers

# 이름 열 결정 함수
def get_name_column(df, category, language):
    """카테고리와 언어에 따른 이름 열 결정"""
    name_candidates = []
    
    # 언어별 기본 후보
    if language == "한국어":
        name_candidates = ['명칭(한국어)', '명칭', '이름', '시설명', '관광지명', '장소명', '상호', '상호명']
    elif language == "영어":
        name_candidates = ['명칭(영어)', 'PLACE', 'NAME', 'TITLE', 'ENGLISH_NAME', 'name']
    elif language == "중국어":
        name_candidates = ['명칭(중국어)', '名称', '中文名', '名稱']
    
    # 카테고리별 특수 처리
    if category == "종로구 관광지" and language == "중국어":
        name_candidates = ['名称'] + name_candidates
    elif category == "한국음식점":
        if language == "한국어":
            name_candidates = ['상호명(한글)', '상호명', '업소명'] + name_candidates
        elif language == "영어":
            name_candidates = ['상호명(영문)', '영문명'] + name_candidates
        elif language == "중국어":
            name_candidates = ['상호명(중문)', '중문명'] + name_candidates
    
    # 후보 열 중 존재하는 첫 번째 열 사용
    for col in name_candidates:
        if col in df.columns:
            return col
    
    # 명칭 열이 없으면 첫 번째 문자열 열 사용
    string_cols = [col for col in df.columns if df[col].dtype == 'object']
    if string_cols:
        return string_cols[0]
    
    return None

# 주소 열 결정 함수
def get_address_column(df, language):
    """언어에 따른 주소 열 결정"""
    address_candidates = []
    
    if language == "한국어":
        address_candidates = ['주소(한국어)', '주소', '소재지', '도로명주소', '지번주소', '위치', 'ADDRESS']
    elif language == "영어":
        address_candidates = ['주소(영어)', 'ENGLISH_ADDRESS', 'address', 'location']
    elif language == "중국어":
        address_candidates = ['주소(중국어)', '地址', '位置', '中文地址']
    
    # 후보 열 중 존재하는 첫 번째 열 사용
    for col in address_candidates:
        if col in df.columns:
            return col
    
    return None

# 정보창 HTML 구성 함수
def build_info_html(row, name, address, category):
    """마커 정보창 HTML 구성"""
    info = f"<div style='padding: 10px; max-width: 300px;'>"
    info += f"<h3 style='margin-top: 0; color: #1976D2;'>{name}</h3>"
    info += f"<p><strong>분류:</strong> {category}</p>"
    
    if address:
        info += f"<p><strong>주소:</strong> {address}</p>"
    
    # 전화번호 정보
    for tel_col in ['전화번호', 'TELNO', '연락처', '전화', 'TEL', 'CONTACT']:
        if tel_col in row and pd.notna(row[tel_col]):
            info += f"<p><strong>전화:</strong> {row[tel_col]}</p>"
            break
    
    # 운영시간 정보
    for time_col in ['이용시간', '운영시간', 'OPENHOUR', 'HOUR', '영업시간', '개장시간']:
        if time_col in row and pd.notna(row[time_col]):
            info += f"<p><strong>운영시간:</strong> {row[time_col]}</p>"
            break
    
    # 입장료 정보
    for fee_col in ['입장료', '이용요금', 'FEE', '요금', '비용']:
        if fee_col in row and pd.notna(row[fee_col]):
            info += f"<p><strong>입장료:</strong> {row[fee_col]}</p>"
            break
    
    info += "</div>"
    return info
    
def create_google_maps_html(api_key, center_lat, center_lng, markers=None, zoom=13, language="ko", 
                           navigation_mode=False, start_location=None, end_location=None, transport_mode=None):
    """Google Maps HTML 생성 - 내비게이션 기능 추가 및 수정"""
    if markers is None:
        markers = []
    
    # 카테고리별 마커 그룹화
    categories = {}
    for marker in markers:
        category = marker.get('category', '기타')
        if category not in categories:
            categories[category] = []
        categories[category].append(marker)
    
    # 범례 HTML
    legend_items = []
    for category, color in CATEGORY_COLORS.items():
        # 해당 카테고리의 마커가 있는 경우만 표시
        if any(m.get('category') == category for m in markers):
            count = sum(1 for m in markers if m.get('category') == category)
            legend_html_item = f'<div class="legend-item"><img src="https://maps.google.com/mapfiles/ms/icons/{color}-dot.png" alt="{category}"> {category} ({count})</div>'
            legend_items.append(legend_html_item)
    
    legend_html = "".join(legend_items)
    
    # 마커 JavaScript 코드 생성
    markers_js = ""
    for i, marker in enumerate(markers):
        color = marker.get('color', 'red')
        title = marker.get('title', '').replace("'", "\\\'").replace('"', '\\\"')
        info = marker.get('info', '').replace("'", "\\\'").replace('"', '\\\"')
        category = marker.get('category', '').replace("'", "\\\'").replace('"', '\\\"')
        
        # 마커 아이콘 URL
        icon_url = f"https://maps.google.com/mapfiles/ms/icons/{color}-dot.png"
        
        # 정보창 HTML 내용
        info_content = f"""
            <div style="padding: 10px; max-width: 300px;">
                <h3 style="margin-top: 0; color: #1976D2;">{title}</h3>
                <p><strong>분류:</strong> {category}</p>
                <div>{info}</div>
            </div>
        """.replace("'", "\\\\'").replace("\n", "")
        
        # 마커 생성 코드
        marker_js_template = """
            var marker{0} = new google.maps.Marker({{
                position: {{ lat: {1}, lng: {2} }},
                map: map,
                title: '{3}',
                icon: '{4}',
                animation: google.maps.Animation.DROP
            }});
            
            markers.push(marker{0});
            markerCategories.push('{5}');
            
            var infowindow{0} = new google.maps.InfoWindow({{
                content: '{6}'
            }});
            
            marker{0}.addListener('click', function() {{
                closeAllInfoWindows();
                infowindow{0}.open(map, marker{0});
                
                // 마커 바운스 애니메이션
                if (currentMarker) currentMarker.setAnimation(null);
                marker{0}.setAnimation(google.maps.Animation.BOUNCE);
                currentMarker = marker{0};
                
                // 애니메이션 종료
                setTimeout(function() {{
                    marker{0}.setAnimation(null);
                }}, 1500);
                
                // 부모 창에 마커 클릭 이벤트 전달
                window.parent.postMessage({{
                    'type': 'marker_click',
                    'id': {0},
                    'title': '{3}',
                    'lat': {1},
                    'lng': {2},
                    'category': '{5}'
                }}, '*');
            }});
            
            infoWindows.push(infowindow{0});
        """
        
        # format 메서드로 동적 값 채우기
        curr_marker_js = marker_js_template.format(
            i, marker['lat'], marker['lng'], title, icon_url, category, info_content
        )
        
        markers_js += curr_marker_js
    
    # 필터링 함수
    filter_js = """
        function filterMarkers(category) {
            for (var i = 0; i < markers.length; i++) {
                var shouldShow = category === 'all' || markerCategories[i] === category;
                markers[i].setVisible(shouldShow);
            }
            
            // 필터 버튼 활성화 상태 업데이트
            document.querySelectorAll('.filter-button').forEach(function(btn) {
                btn.classList.remove('active');
            });
            
            // 카테고리 ID 안전하게 변환
            var safeCategory = category.replace(/[^a-zA-Z0-9]/g, '-').toLowerCase();
            var filterButtonId = 'filter-' + (category === 'all' ? 'all' : safeCategory);
            
            var filterButton = document.getElementById(filterButtonId);
            if (filterButton) {
                filterButton.classList.add('active');
            } else {
                document.getElementById('filter-all').classList.add('active');
            }
        }
    """
    
    # 마커 클러스터링 코드
    clustering_js = """
        // 마커 클러스터링
        if (typeof markerClusterer !== 'undefined' && markers.length > 0) {
            new markerClusterer.MarkerClusterer({
                map: map,
                markers: markers,
                algorithm: new markerClusterer.SuperClusterAlgorithm({
                    maxZoom: 15,
                    radius: 50
                })
            });
        }
    """
    
    # 필터 버튼 HTML 생성
    filter_buttons = '<button id="filter-all" class="filter-button active" onclick="filterMarkers(\'all\')">전체 보기</button>'
    for cat in categories.keys():
        safe_id = cat.replace(' ', '-').replace('/', '-').replace('(', '').replace(')', '')
        safe_id = ''.join(c for c in safe_id if c.isalnum() or c in '-_').lower()
        filter_buttons += f' <button id="filter-{safe_id}" class="filter-button" onclick="filterMarkers(\'{cat}\')">{cat}</button>'
    
    # 내비게이션 JavaScript 코드 - 수정됨
    directions_js = ""
    if navigation_mode and start_location and end_location and transport_mode:
        directions_js = f"""
        // 전역 변수 선언
        var directionsService;
        var directionsRenderer;
        
        // 내비게이션 초기화 함수
        function initDirections() {{
            console.log('내비게이션 초기화 중...');
            
            // Direction Service 생성
            directionsService = new google.maps.DirectionsService();
            
            // Direction Renderer 생성 및 설정
            directionsRenderer = new google.maps.DirectionsRenderer({{
                map: map,
                draggable: true,
                hideRouteList: false,
                suppressMarkers: false,
                preserveViewport: false,
                polylineOptions: {{
                    strokeColor: '#2196F3',
                    strokeOpacity: 0.8,
                    strokeWeight: 6
                }}
            }});
            
            // 렌더러를 지도에 명시적으로 연결
            directionsRenderer.setMap(map);
            
            // 지도가 완전히 로드된 후 경로 계산 실행
            setTimeout(calculateRoute, 500);
        }}
        
        // 경로 계산 및 표시 함수
        function calculateRoute() {{
            // 출발지와 목적지 설정
            var start = {{ lat: {start_location['lat']}, lng: {start_location['lng']} }};
            var end = {{ lat: {end_location['lat']}, lng: {end_location['lng']} }};
            
            // 이동 수단에 따른 travelMode 설정
            var travelMode;
            switch('{transport_mode.lower()}') {{
                case 'walking':
                    travelMode = google.maps.TravelMode.WALKING;
                    break;
                case 'transit':
                    travelMode = google.maps.TravelMode.TRANSIT;
                    break;
                case 'driving':
                default:
                    travelMode = google.maps.TravelMode.DRIVING;
                    break;
            }}
            
            // 경로 요청
            directionsService.route(
                {{
                    origin: start,
                    destination: end,
                    travelMode: travelMode,
                    optimizeWaypoints: true,
                    avoidHighways: false,
                    avoidTolls: false
                }},
                function(response, status) {{
                    if (status === 'OK') {{
                        // 경로 표시
                        directionsRenderer.setDirections(response);
                        
                        // 경로 정보 추출
                        var route = response.routes[0];
                        var leg = route.legs[0];
                        
                        // 경로 정보 패널 표시
                        var panel = document.getElementById('directions-panel');
                        if (panel) {{
                            panel.innerHTML = '<div style="font-weight:bold; margin-bottom:10px;">' +
                                '총 거리: ' + leg.distance.text + ', ' +
                                '소요 시간: ' + leg.duration.text + '</div>';
                            
                            // 상세 경로 안내 추가
                            for (var i = 0; i < leg.steps.length; i++) {{
                                var step = leg.steps[i];
                                var stepDiv = document.createElement('div');
                                stepDiv.className = 'direction-step';
                                stepDiv.innerHTML = (i+1) + '. ' + step.instructions;
                                panel.appendChild(stepDiv);
                            }}
                        }}
                        
                        // 경로 정보를 부모 창에 전달
                        window.parent.postMessage({{
                            'type': 'directions_success',
                            'distance': leg.distance.text,
                            'duration': leg.duration.text
                        }}, '*');
                    }} else {{
                        // 오류 처리
                        console.error('경로 계산 오류: ' + status);
                        var panel = document.getElementById('directions-panel');
                        if (panel) {{
                            panel.innerHTML = '<div style="color:red; padding:10px;">' +
                                '경로를 찾을 수 없습니다. (오류: ' + status + ')<br>' +
                                'Google Directions API가 활성화되어 있는지 확인하세요.</div>';
                        }}
                        
                        // 오류 정보를 부모 창에 전달
                        window.parent.postMessage({{
                            'type': 'directions_error',
                            'error': status
                        }}, '*');
                    }}
                }}
            );
        }}
        
        // 지도 로드 완료 이벤트에 내비게이션 초기화 연결
        google.maps.event.addListenerOnce(map, 'idle', function() {{
            initDirections();
        }});
        """
    
    # 전체 HTML 코드 생성
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>서울 관광 지도</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            #map {{
                height: 100%;
                width: 100%;
                margin: 0;
                padding: 0;
            }}
            html, body {{
                height: 100%;
                margin: 0;
                padding: 0;
                font-family: 'Noto Sans KR', Arial, sans-serif;
            }}
            .map-controls {{
                position: absolute;
                top: 10px;
                left: 10px;
                z-index: 5;
                background-color: white;
                padding: 10px;
                border-radius: 5px;
                box-shadow: 0 2px 6px rgba(0,0,0,.3);
                max-width: 90%;
                overflow-x: auto;
                white-space: nowrap;
            }}
            .filter-button {{
                margin: 5px;
                padding: 5px 10px;
                background-color: #f8f9fa;
                border: 1px solid #dadce0;
                border-radius: 4px;
                cursor: pointer;
            }}
            .filter-button:hover {{
                background-color: #e8eaed;
            }}
            .filter-button.active {{
                background-color: #1976D2;
                color: white;
            }}
            #legend {{
                font-family: 'Noto Sans KR', Arial, sans-serif;
                background-color: white;
                border: 1px solid #ccc;
                border-radius: 5px;
                bottom: 25px;
                box-shadow: 0 2px 6px rgba(0,0,0,.3);
                font-size: 12px;
                padding: 10px;
                position: absolute;
                right: 10px;
                z-index: 5;
            }}
            .legend-item {{
                margin-bottom: 5px;
                display: flex;
                align-items: center;
            }}
            .legend-item img {{
                width: 20px;
                height: 20px;
                margin-right: 5px;
            }}
            .custom-control {{
                background-color: #fff;
                border: 0;
                border-radius: 2px;
                box-shadow: 0 1px 4px -1px rgba(0, 0, 0, 0.3);
                margin: 10px;
                padding: 0 0.5em;
                font: 400 18px Roboto, Arial, sans-serif;
                overflow: hidden;
                height: 40px;
                cursor: pointer;
            }}
            /* 내비게이션 패널 스타일 */
            #directions-panel {{
                width: 300px;
                max-width: 90%;
                background-color: white;
                padding: 10px;
                border-radius: 5px;
                box-shadow: 0 2px 6px rgba(0,0,0,.3);
                position: absolute;
                top: 10px;
                right: 10px;
                z-index: 5;
                max-height: 400px;
                overflow-y: auto;
                font-size: 12px;
            }}
            .direction-step {{
                padding: 8px 5px;
                border-bottom: 1px solid #eee;
            }}
            .direction-step:last-child {{
                border-bottom: none;
            }}
        </style>
    </head>
    <body>
        <div id="map"></div>
        
        <!-- 카테고리 필터 -->
        <div class="map-controls" id="category-filter">
            <div style="margin-bottom: 8px; font-weight: bold;">카테고리 필터</div>
            {filter_buttons}
        </div>
        
        <!-- 지도 범례 -->
        <div id="legend">
            <div style="font-weight: bold; margin-bottom: 8px;">지도 범례</div>
            {legend_html}
        </div>
        
        <!-- 내비게이션 패널 -->
        {'''<div id="directions-panel"></div>''' if navigation_mode else ''}
        
        <script>
            // 디버깅용 로그 설정
            console.log = function() {{
                var args = Array.prototype.slice.call(arguments);
                var message = args.join(' ');
                window.parent.postMessage({{
                    'type': 'debug_log',
                    'message': message
                }}, '*');
                if (window.originalConsoleLog) window.originalConsoleLog.apply(console, arguments);
            }};
            if (!window.originalConsoleLog) window.originalConsoleLog = console.log;
        
            // 지도 및 마커 변수
            var map;
            var markers = [];
            var markerCategories = [];
            var infoWindows = [];
            var currentMarker = null;
            
            // 모든 정보창 닫기
            function closeAllInfoWindows() {{
                for (var i = 0; i < infoWindows.length; i++) {{
                    infoWindows[i].close();
                }}
            }}
            
            function initMap() {{
                // 지도 생성
                map = new google.maps.Map(document.getElementById('map'), {{
                    center: {{ lat: {center_lat}, lng: {center_lng} }},
                    zoom: {zoom},
                    fullscreenControl: true,
                    mapTypeControl: true,
                    streetViewControl: true,
                    zoomControl: true,
                    mapTypeId: 'roadmap',
                    gestureHandling: 'greedy'
                }});
                
                // 현재 위치 버튼 추가
                const locationButton = document.createElement("button");
                locationButton.textContent = "📍 내 위치";
                locationButton.classList.add("custom-control");
                locationButton.addEventListener("click", () => {{
                    if (navigator.geolocation) {{
                        navigator.geolocation.getCurrentPosition(
                            (position) => {{
                                const pos = {{
                                    lat: position.coords.latitude,
                                    lng: position.coords.longitude,
                                }};
                                
                                window.parent.postMessage({{
                                    'type': 'current_location',
                                    'lat': pos.lat,
                                    'lng': pos.lng
                                }}, '*');
                                
                                map.setCenter(pos);
                                map.setZoom(15);
                                
                                new google.maps.Marker({{
                                    position: pos,
                                    map: map,
                                    title: '내 위치',
                                    icon: {{
                                        path: google.maps.SymbolPath.CIRCLE,
                                        fillColor: '#4285F4',
                                        fillOpacity: 1,
                                        strokeColor: '#FFFFFF',
                                        strokeWeight: 2,
                                        scale: 8
                                    }}
                                }});
                            }},
                            () => {{ alert("위치 정보를 가져오는데 실패했습니다."); }}
                        );
                    }} else {{
                        alert("이 브라우저에서는 위치 정보 기능을 지원하지 않습니다.");
                    }}
                }});
                
                map.controls[google.maps.ControlPosition.TOP_RIGHT].push(locationButton);
                
                // 범례를 지도에 추가
                map.controls[google.maps.ControlPosition.RIGHT_BOTTOM].push(
                    document.getElementById('legend')
                );
                
                // 마커 추가
                {markers_js}
                
                // 마커 클러스터링
                {clustering_js}
                
                // 필터링 함수
                {filter_js}
                
                // 내비게이션 코드
                {directions_js}
                
                // 지도 클릭 이벤트
                map.addListener('click', function(event) {{
                    closeAllInfoWindows();
                    if (currentMarker) currentMarker.setAnimation(null);
                    
                    window.parent.postMessage({{
                        'type': 'map_click',
                        'lat': event.latLng.lat(),
                        'lng': event.latLng.lng()
                    }}, '*');
                }});
                
                console.log('지도 초기화 완료');
            }}
        </script>
        <script src="https://unpkg.com/@googlemaps/markerclusterer@2.0.9/dist/index.min.js"></script>
        <script src="https://maps.googleapis.com/maps/api/js?key={api_key}&callback=initMap&libraries=places,directions&v=weekly&language={language}" async defer></script>
    </body>
    </html>
    """
    
    return html
    
def show_google_map(api_key, center_lat, center_lng, markers=None, zoom=13, height=600, language="한국어", 
                   navigation_mode=False, start_location=None, end_location=None, transport_mode=None):
    """Google Maps 컴포넌트 표시 - 내비게이션 기능 추가"""
    # 언어 코드 변환
    lang_code = LANGUAGE_CODES.get(language, "ko")
    
    try:
        # 디버깅 정보
        if navigation_mode:
            st.info(f"내비게이션 모드: {transport_mode}, 출발: ({start_location['lat']:.4f}, {start_location['lng']:.4f}), 도착: ({end_location['lat']:.4f}, {end_location['lng']:.4f})")
        
        # HTML 생성
        map_html = create_google_maps_html(
            api_key=api_key,
            center_lat=center_lat,
            center_lng=center_lng,
            markers=markers,
            zoom=zoom,
            language=lang_code,
            navigation_mode=navigation_mode,
            start_location=start_location,
            end_location=end_location,
            transport_mode=transport_mode
        )
        
        # HTML 컴포넌트로 표시
        st.components.v1.html(map_html, height=height, scrolling=False)
        return True
        
    except Exception as e:
        st.error(f"지도 렌더링 오류: {str(e)}")
        st.error("지도 로딩에 실패했습니다. 아래 대체 옵션을 사용해보세요.")
        
        # 대체 지도 옵션: folium 사용
        try:
            import folium
            from streamlit_folium import folium_static
            
            st.info("대체 지도를 로드합니다...")
            m = folium.Map(location=[center_lat, center_lng], zoom_start=zoom)
            
            # 마커 추가
            if markers:
                for marker in markers:
                    folium.Marker(
                        [marker['lat'], marker['lng']], 
                        popup=marker.get('title', ''),
                        tooltip=marker.get('title', ''),
                        icon=folium.Icon(color=marker.get('color', 'red'))
                    ).add_to(m)
            
            # folium 지도 표시
            folium_static(m)
            return True
            
        except Exception as e2:
            st.error(f"대체 지도 로딩도 실패했습니다: {str(e2)}")
            
            # 비상용 텍스트 지도 표시
            st.warning("텍스트 기반 위치 정보:")
            if markers:
                for i, marker in enumerate(markers[:10]):  # 상위 10개만
                    st.text(f"{i+1}. {marker.get('title', '무제')} - 좌표: ({marker['lat']}, {marker['lng']})")
            return False

def display_visits(visits):
    """방문 기록 표시 함수"""
    if not visits:
        st.info("방문 기록이 없습니다.")
        return
    
    for i, visit in enumerate(visits):
        with st.container():
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                st.markdown(f"**{visit['place_name']}**")
                st.caption(f"방문일: {visit['date']}")
            
            with col2:
                st.markdown(f"+{visit.get('xp_gained', 0)} XP")
            
            with col3:
                # 리뷰 또는 평점이 있는 경우 표시
                if 'rating' in visit and visit['rating']:
                    st.markdown("⭐" * int(visit['rating']))
                else:
                    if st.button("평가", key=f"rate_{i}"):
                        # 평가 기능 구현 (실제로는 팝업이나 별도 UI가 필요)
                        st.session_state.rating_place = visit['place_name']
                        st.session_state.rating_index = i

#################################################
# 개선된 관광 코스 추천 함수
#################################################

def recommend_courses(data, travel_styles, num_days, include_children=False):
    """
    사용자 취향과 일정에 따른 관광 코스 추천 기능
    """
    if not data:
        st.warning("관광지 데이터가 없습니다. 기본 추천 코스를 사용합니다.")
        # 기본 코스 반환
        if "역사/문화" in travel_styles:
            course_type = "문화 코스"
        elif "쇼핑" in travel_styles:
            course_type = "쇼핑 코스"
        elif "자연" in travel_styles:
            course_type = "자연 코스"
        else:
            course_type = "대중적 코스"
            
        return RECOMMENDATION_COURSES.get(course_type, []), course_type, []
    
    # 장소별 점수 계산
    scored_places = []
    
    for place in data:
        # 기본 점수는 중요도
        score = place.get('importance', 1.0)
        
        # 여행 스타일에 따른 가중치 적용
        for style in travel_styles:
            if style in STYLE_CATEGORY_WEIGHTS:
                category_weights = STYLE_CATEGORY_WEIGHTS[style]
                if place['category'] in category_weights:
                    score *= category_weights[place['category']]
        
        # 아이 동반인 경우 가족 친화적인 장소 선호 (미술관/체육시설)
        if include_children:
            if place['category'] in ["미술관/전시", "체육시설"]:
                score *= 1.2
        
        # 최종 점수 저장
        scored_place = place.copy()
        scored_place['score'] = score
        scored_places.append(scored_place)
    
    # 점수별 정렬
    scored_places.sort(key=lambda x: x['score'], reverse=True)
    
    # 일수에 따른 장소 선택
    # 하루당 3곳 방문 가정 (아침, 점심, 저녁)
    places_per_day = 3
    total_places = num_days * places_per_day
    
    # 상위 N개 장소 선택 (N = total_places * 2 for more options)
    top_places = scored_places[:min(len(scored_places), total_places * 2)]
    
    # 동선 최적화: 그리디 알고리즘
    # 서울시청을 시작점으로 설정 (모든 날 아침에 숙소/시청에서 출발한다고 가정)
    seoul_city_hall = {"lat": 37.5665, "lng": 126.9780}
    
    daily_courses = []
    
    for day in range(num_days):
        daily_course = []
        current_position = seoul_city_hall
        
        # 이미 선택된 장소는 제외
        available_places = [p for p in top_places if not any(p['title'] == dp['title'] for dc in daily_courses for dp in dc)]
        
        if not available_places:
            break
        
        # 각 시간대별 최적 장소 선택
        for time_slot in range(places_per_day):
            if not available_places:
                break
                
            # 거리 가중치가 적용된 점수 계산
            for place in available_places:
                distance = geodesic(
                    (current_position['lat'], current_position['lng']), 
                    (place['lat'], place['lng'])
                ).kilometers
                
                # 거리에 따른 점수 감소 (너무 먼 곳은 피함)
                distance_factor = max(0.5, 1 - (distance / 10))  # 10km 이상이면 점수 절반으로
                place['adjusted_score'] = place.get('score', 1.0) * distance_factor
            
            # 조정된 점수로 재정렬
            available_places.sort(key=lambda x: x.get('adjusted_score', 0), reverse=True)
            
            # 최고 점수 장소 선택
            next_place = available_places[0]
            daily_course.append(next_place)
            
            # 선택된 장소 제거
            available_places.remove(next_place)
            
            # 현재 위치 업데이트
            current_position = {"lat": next_place['lat'], "lng": next_place['lng']}
        
        daily_courses.append(daily_course)
    
    # 코스 이름 결정
    if "역사/문화" in travel_styles:
        course_type = "서울 역사/문화 탐방 코스"
    elif "쇼핑" in travel_styles and "맛집" in travel_styles:
        course_type = "서울 쇼핑과 미식 코스"
    elif "쇼핑" in travel_styles:
        course_type = "서울 쇼핑 중심 코스"
    elif "맛집" in travel_styles:
        course_type = "서울 미식 여행 코스"
    elif "자연" in travel_styles:
        course_type = "서울의 자연 코스"
    elif "활동적인" in travel_styles:
        course_type = "액티브 서울 코스"
    else:
        course_type = "서울 필수 여행 코스"
    
    # 추천 장소 이름 목록 생성
    recommended_places = []
    for day_course in daily_courses:
        for place in day_course:
            recommended_places.append(place['title'])
    
    return recommended_places, course_type, daily_courses

#################################################
# 페이지 함수
#################################################

def show_login_page():
    """로그인 페이지 표시"""
    # 언어 설정 초기화
    if 'language' not in st.session_state:
        st.session_state.language = "한국어"
    
    # 언어별 텍스트 사전
    texts = {
        "한국어": {
            "app_title": "서울 관광앱",
            "login_tab": "로그인",
            "join_tab": "회원가입",
            "login_title": "로그인",
            "join_title": "회원가입",
            "id_label": "아이디",
            "pw_label": "비밀번호",
            "pw_confirm_label": "비밀번호 확인",
            "remember_id": "아이디 저장",
            "login_button": "로그인",
            "join_button": "가입하기",
            "login_success": "🎉 로그인 성공!",
            "login_failed": "❌ 아이디 또는 비밀번호가 올바르지 않습니다.",
            "input_required": "아이디와 비밀번호를 입력해주세요.",
            "pw_mismatch": "비밀번호와 비밀번호 확인이 일치하지 않습니다.",
            "join_success": "✅ 회원가입 완료!",
            "user_exists": "⚠️ 이미 존재하는 아이디입니다.",
            "new_id": "새 아이디",
            "new_pw": "새 비밀번호"
        },
        "영어": {
            "app_title": "Seoul Tourism App",
            "login_tab": "Login",
            "join_tab": "Join",
            "login_title": "Login",
            "join_title": "Join",
            "id_label": "ID",
            "pw_label": "Password",
            "pw_confirm_label": "Confirm Password",
            "remember_id": "Remember ID",
            "login_button": "Login",
            "join_button": "Join",
            "login_success": "🎉 Login successful!",
            "login_failed": "❌ ID or password is incorrect.",
            "input_required": "Please enter ID and password.",
            "pw_mismatch": "Passwords do not match.",
            "join_success": "✅ Registration completed!",
            "user_exists": "⚠️ ID already exists.",
            "new_id": "New ID",
            "new_pw": "New Password"
        },
        "중국어": {
            "app_title": "首尔观光应用",
            "login_tab": "登录",
            "join_tab": "注册",
            "login_title": "登录",
            "join_title": "注册",
            "id_label": "账号",
            "pw_label": "密码",
            "pw_confirm_label": "确认密码",
            "remember_id": "记住账号",
            "login_button": "登录",
            "join_button": "注册",
            "login_success": "🎉 登录成功！",
            "login_failed": "❌ 账号或密码不正确。",
            "input_required": "请输入账号和密码。",
            "pw_mismatch": "两次输入的密码不一致。",
            "join_success": "✅ 注册完成！",
            "user_exists": "⚠️ 此账号已存在。",
            "new_id": "新账号",
            "new_pw": "新密码"
        }
    }
    
    # 현재 선택된 언어에 따른 텍스트 가져오기
    current_lang_texts = texts[st.session_state.language]

    # 메인 이미지
    pic1, pic2, pic3, pic4, pic5 = st.columns([1, 1, 1, 1, 1])

    with pic3:
        main_image_path = Path("asset") / "SeoulTripView.png"
        if main_image_path.exists():
            st.image(main_image_path, use_container_width=True)
        else:
            st.info("이미지를 찾을 수 없습니다: asset/SeoulTripView.png")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        page_header(current_lang_texts["app_title"])

        # 언어 선택 드롭다운
        language_options = {
            "🇰🇷 한국어": "한국어",
            "🇺🇸 English": "영어",
            "🇨🇳 中文": "중국어"
        }
        selected_lang = st.selectbox(
            "Language / 언어 / 语言",
            options=list(language_options.keys()),
            index=list(language_options.values()).index(st.session_state.language),
            key="language_selector"
        )
        
        # 언어 변경 시 session_state 업데이트
        if language_options[selected_lang] != st.session_state.language:
            st.session_state.language = language_options[selected_lang]
            st.rerun()  # 언어 변경 후 페이지 새로고침
        
        # 로그인/회원가입 탭
        tab1, tab2 = st.tabs([current_lang_texts["login_tab"], current_lang_texts["join_tab"]])
        
        with tab1:
            st.markdown(f"### {current_lang_texts['login_title']}")
            username = st.text_input(current_lang_texts["id_label"], key="login_username")
            password = st.text_input(current_lang_texts["pw_label"], type="password", key="login_password")
            
            col1, col2 = st.columns([1,1])
            with col1:
                remember = st.checkbox(current_lang_texts["remember_id"])
            with col2:
                st.markdown("")  # 빈 공간
            
            if st.button(current_lang_texts["login_button"], use_container_width=True):
                if authenticate_user(username, password):
                    st.success(current_lang_texts["login_success"])
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    change_page("menu")
                    st.rerun()
                else:
                    st.error(current_lang_texts["login_failed"])
        
        with tab2:
            st.markdown(f"### {current_lang_texts['join_title']}")
            new_user = st.text_input(current_lang_texts["new_id"], key="register_username")
            new_pw = st.text_input(current_lang_texts["new_pw"], type="password", key="register_password")
            new_pw_confirm = st.text_input(current_lang_texts["pw_confirm_label"], type="password", key="register_password_confirm")
            
            if st.button(current_lang_texts["join_button"], use_container_width=True):
                if not new_user or not new_pw:
                    st.error(current_lang_texts["input_required"])
                elif new_pw != new_pw_confirm:
                    st.error(current_lang_texts["pw_mismatch"])
                elif register_user(new_user, new_pw):
                    st.success(current_lang_texts["join_success"])
                    st.session_state.logged_in = True
                    st.session_state.username = new_user
                    change_page("menu")
                    st.rerun()
                else:
                    st.warning(current_lang_texts["user_exists"])

def show_menu_page():
    """메인 메뉴 페이지 표시"""
    page_header("서울 관광앱")
    st.markdown(f"### 👋 {st.session_state.username}님, 환영합니다!")
    
    # 사용자 레벨 및 경험치 정보 표시
    display_user_level_info()
    
    st.markdown("---")
    st.markdown("### 메뉴를 선택해주세요")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="card">
            <h3>🗺️ 관광 장소 지도</h3>
            <p>서울의 주요 관광지를 지도에서 찾고 내비게이션으로 이동해보세요.</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("관광 장소 지도 보기", key="map_button", use_container_width=True):
            change_page("map")
            st.rerun()
    
    with col2:
        st.markdown("""
        <div class="card">
            <h3>🗓️ 서울 관광 코스 짜주기</h3>
            <p>AI가 당신의 취향에 맞는 최적의 관광 코스를 추천해드립니다.</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("관광 코스 짜기", key="course_button", use_container_width=True):
            change_page("course")
            st.rerun()
    
    st.markdown("")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="card">
            <h3>📝 나의 관광 이력</h3>
            <p>방문한 장소들의 기록과 획득한 경험치를 확인하세요.</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("관광 이력 보기", key="history_button", use_container_width=True):
            change_page("history")
            st.rerun()
            
    # 로그아웃 버튼
    st.markdown("---")
    if st.button("🔓 로그아웃", key="logout_button"):
        logout_user()
        st.rerun()

def show_map_page():
    """지도 페이지 표시 - 내비게이션 기능 개선"""
    page_header("서울 관광 장소 지도")
    
    # 뒤로가기 버튼
    if st.button("← 메뉴로 돌아가기"):
        change_page("menu")
        st.rerun()
    
    # API 키 확인
    api_key = st.session_state.google_maps_api_key
    if not api_key or api_key == "YOUR_GOOGLE_MAPS_API_KEY":
        st.error("Google Maps API 키가 설정되지 않았습니다.")
        api_key = st.text_input("Google Maps API 키를 입력하세요", type="password")
        if api_key:
            st.session_state.google_maps_api_key = api_key
            st.success("API 키가 설정되었습니다. 지도를 로드합니다.")
            st.rerun()
        else:
            st.info("Google Maps를 사용하려면 API 키가 필요합니다.")
            return
    
    # 언어 선택
    col1, col2 = st.columns([4, 1])
    with col2:
        selected_language = st.selectbox(
            "🌏 Language", 
            ["🇰🇷 한국어", "🇺🇸 English", "🇨🇳 中文"],
            index=0 if st.session_state.language == "한국어" else 1 if st.session_state.language == "영어" else 2
        )
        language_map = {
            "🇰🇷 한국어": "한국어",
            "🇺🇸 English": "영어",
            "🇨🇳 中文": "중국어"
        }
        st.session_state.language = language_map[selected_language]
    
    # 사용자 위치 가져오기
    user_location = get_location_position()
    
    # 자동으로 Excel 파일 로드 (아직 로드되지 않은 경우)
    if not st.session_state.markers_loaded or not st.session_state.all_markers:
        with st.spinner("서울 관광 데이터를 로드하는 중..."):
            all_markers = load_excel_files(st.session_state.language)
            if all_markers:
                st.session_state.all_markers = all_markers
                st.session_state.markers_loaded = True
                st.session_state.tourism_data = all_markers  # 코스 추천을 위해 저장
                st.success(f"총 {len(all_markers)}개의 관광지 로드 완료!")
            else:
                st.warning("관광지 데이터를 로드할 수 없습니다.")
    
    # 내비게이션 모드가 아닌 경우 기본 지도 표시
    if not st.session_state.navigation_active:
        map_col, info_col = st.columns([2, 1])
        
        with map_col:
            # 마커 데이터 준비
            markers = []
            
            # 사용자 현재 위치 마커
            markers.append({
                'lat': user_location[0],
                'lng': user_location[1],
                'title': '내 위치',
                'color': 'blue',
                'info': '현재 위치',
                'category': '현재 위치'
            })
            
            # 로드된 데이터 마커 추가
            if st.session_state.all_markers:
                markers.extend(st.session_state.all_markers)
                st.success(f"지도에 {len(st.session_state.all_markers)}개의 장소를 표시했습니다.")
            
            # Google Maps 표시
            show_google_map(
                api_key=api_key,
                center_lat=user_location[0],
                center_lng=user_location[1],
                markers=markers,
                zoom=12,
                height=600,
                language=st.session_state.language
            )
        
        with info_col:
            st.subheader("장소 정보")
            
            # 검색 기능
            search_term = st.text_input("장소 검색")
            if search_term and st.session_state.all_markers:
                search_results = [m for m in st.session_state.all_markers 
                                 if search_term.lower() in m['title'].lower()]
                
                if search_results:
                    st.markdown(f"### 🔍 검색 결과 ({len(search_results)}개)")
                    for i, marker in enumerate(search_results[:5]):  # 상위 5개만
                        with st.container():
                            st.markdown(f"**{marker['title']}**")
                            st.caption(f"분류: {marker.get('category', '기타')}")
                            
                            col1, col2 = st.columns([1,1])
                            with col1:
                                if st.button(f"길찾기", key=f"nav_{i}"):
                                    st.session_state.navigation_active = True
                                    st.session_state.navigation_destination = {
                                        "name": marker['title'],
                                        "lat": marker['lat'],
                                        "lng": marker['lng']
                                    }
                                    st.rerun()
                            
                            with col2:
                                if st.button(f"방문기록", key=f"visit_{i}"):
                                    success, xp = add_visit(
                                        st.session_state.username,
                                        marker['title'],
                                        marker['lat'],
                                        marker['lng']
                                    )
                                    if success:
                                        st.success(f"'{marker['title']}' 방문! +{xp} XP 획득!")
                                        time.sleep(1)
                                        st.rerun()
                                    else:
                                        st.info("이미 오늘 방문한 장소입니다.")
                else:
                    st.info(f"'{search_term}'에 대한 검색 결과가 없습니다.")
            
            # 카테고리별 통계
            if st.session_state.all_markers:
                st.subheader("카테고리별 장소")
                categories = {}
                for m in st.session_state.all_markers:
                    cat = m.get('category', '기타')
                    if cat not in categories:
                        categories[cat] = 0
                    categories[cat] += 1
                
                for cat, count in categories.items():
                    st.markdown(f"- **{cat}**: {count}개")
    else:
        # 내비게이션 모드 UI
        destination = st.session_state.navigation_destination
        if not destination:
            st.error("목적지 정보가 없습니다.")
            if st.button("지도로 돌아가기"):
                st.session_state.navigation_active = False
                st.rerun()
        else:
            st.subheader(f"🧭 {destination['name']}까지 내비게이션")
            
            # 목적지 정보 표시
            dest_lat, dest_lng = destination["lat"], destination["lng"]
            user_lat, user_lng = user_location
            
            # 직선 거리 계산
            distance = geodesic((user_lat, user_lng), (dest_lat, dest_lng)).meters
            
            if not st.session_state.transport_mode:
                st.markdown("### 이동 수단 선택")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    walk_time = distance / 67  # 도보 속도 약 4km/h (67m/분)
                    st.markdown("""
                    <div class="card">
                        <h3>🚶 도보</h3>
                        <p>예상 소요 시간: {:.0f}분</p>
                    </div>
                    """.format(walk_time), unsafe_allow_html=True)
                    
                    if st.button("도보 선택", use_container_width=True):
                        st.session_state.transport_mode = "walking"
                        st.rerun()
                
                with col2:
                    transit_time = distance / 200  # 대중교통 속도 약 12km/h (200m/분)
                    st.markdown("""
                    <div class="card">
                        <h3>🚍 대중교통</h3>
                        <p>예상 소요 시간: {:.0f}분</p>
                    </div>
                    """.format(transit_time), unsafe_allow_html=True)
                    
                    if st.button("대중교통 선택", use_container_width=True):
                        st.session_state.transport_mode = "transit"
                        st.rerun()
                
                with col3:
                    car_time = distance / 500  # 자동차 속도 약 30km/h (500m/분)
                    st.markdown("""
                    <div class="card">
                        <h3>🚗 자동차</h3>
                        <p>예상 소요 시간: {:.0f}분</p>
                    </div>
                    """.format(car_time), unsafe_allow_html=True)
                    
                    if st.button("자동차 선택", use_container_width=True):
                        st.session_state.transport_mode = "driving"
                        st.rerun()
                
                if st.button("← 지도로 돌아가기", use_container_width=True):
                    st.session_state.navigation_active = False
                    st.rerun()
            
            else:
                # 선택된 교통수단에 따른 내비게이션 표시
                transport_mode = st.session_state.transport_mode
                transport_icons = {
                    "walking": "🚶",
                    "transit": "🚍",
                    "driving": "🚗"
                }
                transport_names = {
                    "walking": "도보",
                    "transit": "대중교통", 
                    "driving": "자동차"
                }
                
                st.markdown(f"### {transport_icons[transport_mode]} {transport_names[transport_mode]} 경로")
                
                # 마커 데이터 준비
                markers = [
                    {
                        'lat': user_lat, 
                        'lng': user_lng, 
                        'title': '내 위치', 
                        'color': 'blue', 
                        'info': '출발 지점',
                        'category': '내 위치'
                    },
                    {
                        'lat': dest_lat, 
                        'lng': dest_lng, 
                        'title': destination["name"], 
                        'color': 'red', 
                        'info': f'목적지: {destination["name"]}',
                        'category': '목적지'
                    }
                ]
                
                # 내비게이션 UI
                nav_col, info_col = st.columns([2, 1])
                
                with nav_col:
                    # 내비게이션 모드일 때 지도 표시 부분 - 수정된 부분
                    show_google_map(
                        api_key=api_key,
                        center_lat=(user_lat + dest_lat) / 2,  # 중간 지점
                        center_lng=(user_lng + dest_lng) / 2,
                        markers=markers,
                        zoom=14,
                        height=600,
                        language=st.session_state.language,
                        navigation_mode=True,
                        start_location={"lat": user_lat, "lng": user_lng},
                        end_location={"lat": dest_lat, "lng": dest_lng},
                        transport_mode=transport_mode
                    )
                
                with info_col:
                    # 경로 정보 표시
                    st.markdown("### 경로 정보")
                    st.markdown(f"**{destination['name']}까지**")
                    st.markdown(f"- 거리: {distance:.0f}m")
                    
                    # 교통수단별 예상 시간
                    if transport_mode == "walking":
                        speed = 67  # m/min
                        transport_desc = "도보"
                    elif transport_mode == "transit":
                        speed = 200  # m/min
                        transport_desc = "대중교통"
                    else:  # driving
                        speed = 500  # m/min
                        transport_desc = "자동차"
                    
                    time_min = distance / speed
                    st.markdown(f"- 예상 소요 시간: {time_min:.0f}분")
                    st.markdown(f"- 이동 수단: {transport_desc}")
                    
                    # 턴바이턴 내비게이션 지시사항 (예시)
                    st.markdown("### 경로 안내")
                    directions = [
                        "현재 위치에서 출발합니다",
                        f"{distance*0.3:.0f}m 직진 후 오른쪽으로 턴",
                        f"{distance*0.2:.0f}m 직진 후 왼쪽으로 턴",
                        f"{distance*0.5:.0f}m 직진 후 목적지 도착"
                    ]
                    
                    for i, direction in enumerate(directions):
                        st.markdown(f"{i+1}. {direction}")
                    
                    # 다른 교통수단 선택 버튼
                    st.markdown("### 다른 이동 수단")
                    other_modes = {"walking": "도보", "transit": "대중교통", "driving": "자동차"}
                    other_modes.pop(transport_mode)  # 현재 모드 제거
                    
                    cols = st.columns(len(other_modes))
                    for i, (mode, name) in enumerate(other_modes.items()):
                        with cols[i]:
                            if st.button(name):
                                st.session_state.transport_mode = mode
                                st.rerun()
                    
                    if st.button("내비게이션 종료", use_container_width=True):
                        st.session_state.navigation_active = False
                        st.session_state.transport_mode = None
                        st.rerun()
                    
def show_course_page():
    """개선된 관광 코스 추천 페이지"""
    page_header("서울 관광 코스 짜주기")
    
    # 뒤로가기 버튼
    if st.button("← 메뉴로 돌아가기"):
        change_page("menu")
        st.rerun()
    
    # 자동으로 데이터 로드 (아직 로드되지 않은 경우)
    if not st.session_state.markers_loaded or not st.session_state.all_markers:
        with st.spinner("서울 관광 데이터를 로드하는 중..."):
            all_markers = load_excel_files(st.session_state.language)
            if all_markers:
                st.session_state.all_markers = all_markers
                st.session_state.markers_loaded = True
                st.session_state.tourism_data = all_markers
                st.success(f"총 {len(all_markers)}개의 관광지 로드 완료!")
            else:
                st.warning("관광지 데이터를 로드할 수 없습니다.")
    
    # AI 추천 아이콘 및 소개
    col1, col2 = st.columns([1, 5])
    with col1:
        main_image_path = Path("asset") / "SeoulTripView.png"
        if main_image_path.exists():
            st.image(main_image_path, use_container_width=True)
        else:
            st.info("이미지를 찾을 수 없습니다: asset/SeoulTripView.png")
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
                # 코스 추천 실행
                recommended_places, course_type, daily_courses = recommend_courses(
                    st.session_state.all_markers if hasattr(st.session_state, 'all_markers') else [],
                    selected_styles,
                    delta,
                    include_children
                )
                
                st.success("코스 생성 완료!")
                
                # 코스 표시
                st.markdown("## 추천 코스")
                st.markdown(f"**{course_type}** - {delta}일 일정")
                
                # 일별 코스 표시
                if daily_courses:
                    # 실제 데이터 기반 일별 코스 표시
                    for day_idx, day_course in enumerate(daily_courses):
                        st.markdown(f"### Day {day_idx + 1}")
                        
                        if not day_course:
                            st.info("추천 장소가 부족합니다.")
                            continue
                        
                        # 시간대별 장소 표시
                        time_slots = ["오전 (09:00-12:00)", "오후 (13:00-16:00)", "저녁 (16:00-19:00)"]
                        timeline = st.columns(len(day_course))
                        
                        for i, place in enumerate(day_course):
                            with timeline[i]:
                                time_idx = min(i, len(time_slots) - 1)
                                st.markdown(f"**{time_slots[time_idx]}**")
                                st.markdown(f"**{place['title']}**")
                                st.caption(f"분류: {place['category']}")
                                
                                # 간단한 설명 추가
                                info_text = ""
                                if 'address' in place and place['address']:
                                    info_text += f"위치: {place['address']}"
                                    if len(place['address']) > 20:
                                        info_text = info_text[:20] + "..."
                                st.caption(info_text)
                else:
                    # 기본 코스 데이터 표시
                    for day in range(1, min(delta+1, 4)):  # 최대 3일까지
                        st.markdown(f"### Day {day}")
                        
                        # 일별 방문 장소 선택
                        day_spots = []
                        if day == 1:
                            day_spots = recommended_places[:3]  # 첫날 3곳
                        elif day == 2:
                            day_spots = recommended_places[3:6] if len(recommended_places) > 3 else recommended_places[:3]
                        else:  # 3일차 이상
                            day_spots = recommended_places[6:9] if len(recommended_places) > 6 else recommended_places[:3]
                        
                        # 표시할 장소가 없으면 기본 추천
                        if not day_spots:
                            day_spots = ["경복궁", "남산서울타워", "명동"]
                        
                        timeline = st.columns(len(day_spots))
                        
                        for i, spot_name in enumerate(day_spots):
                            # 시간대 설정
                            time_slots = ["오전 (09:00-12:00)", "오후 (13:00-16:00)", "저녁 (16:00-19:00)"]
                            time_slot = time_slots[i % 3]
                            
                            with timeline[i]:
                                st.markdown(f"**{time_slot}**")
                                st.markdown(f"**{spot_name}**")
                                st.caption("관광지")
                
                # 지도에 코스 표시
                st.markdown("### 🗺️ 코스 지도")
                
                # API 키 확인
                api_key = st.session_state.google_maps_api_key
                if not api_key or api_key == "YOUR_GOOGLE_MAPS_API_KEY":
                    st.error("Google Maps API 키가 설정되지 않았습니다.")
                    api_key = st.text_input("Google Maps API 키를 입력하세요", type="password")
                    if api_key:
                        st.session_state.google_maps_api_key = api_key
                
                # 코스 마커 생성
                map_markers = []
                
                if daily_courses:
                    # 실제 데이터 기반 코스
                    for day_idx, day_course in enumerate(daily_courses):
                        for time_idx, place in enumerate(day_course):
                            # 시간대별 색상 구분
                            colors = ["blue", "green", "purple"]
                            color = colors[time_idx % len(colors)]
                            
                            marker = {
                                'lat': place['lat'],
                                'lng': place['lng'],
                                'title': f"Day {day_idx+1} - {place['title']}",
                                'info': f"Day {day_idx+1} {time_slots[time_idx]}<br>{place.get('info', '')}",
                                'category': place['category'],
                                'color': color
                            }
                            map_markers.append(marker)
                else:
                    # 기본 코스 - 좌표 데이터가 없어 지도 표시 불가
                    st.warning("코스 장소의 좌표 정보가 없어 지도에 표시할 수 없습니다.")
                
                # 지도 표시
                if map_markers:
                    # 지도 중심 좌표 계산 (마커들의 평균)
                    center_lat = sum(m['lat'] for m in map_markers) / len(map_markers)
                    center_lng = sum(m['lng'] for m in map_markers) / len(map_markers)
                    
                    # 지도 표시
                    show_google_map(
                        api_key=api_key,
                        center_lat=center_lat,
                        center_lng=center_lng,
                        markers=map_markers,
                        zoom=12,
                        height=500,
                        language=st.session_state.language
                    )
                
                # 일정 저장 버튼
                if st.button("이 코스 저장하기", use_container_width=True):
                    if 'saved_courses' not in st.session_state:
                        st.session_state.saved_courses = []
                    
                    # 코스 정보 저장
                    course_info = {
                        "type": course_type,
                        "days": delta,
                        "date": start_date.strftime("%Y-%m-%d"),
                        "styles": selected_styles
                    }
                    
                    if daily_courses:
                        # 실제 데이터 기반 코스
                        course_info["daily_places"] = []
                        for day in daily_courses:
                            day_places = [place['title'] for place in day]
                            course_info["daily_places"].append(day_places)
                    else:
                        # 기본 코스
                        course_info["places"] = recommended_places
                    
                    st.session_state.saved_courses.append(course_info)
                    save_session_data()  # 세션 데이터 저장
                    
                    st.success("코스가 저장되었습니다!")

def show_history_page():
    """관광 이력 페이지 표시"""
    page_header("나의 관광 이력")
    
    # 뒤로가기 버튼
    if st.button("← 메뉴로 돌아가기"):
        change_page("menu")
        st.rerun()
    
    username = st.session_state.username
    
    # 사용자 레벨과 경험치 표시
    user_xp = st.session_state.user_xp.get(username, 0)
    user_level = calculate_level(user_xp)
    xp_percentage = calculate_xp_percentage(user_xp)
    
    col1, col2, col3 = st.columns([1, 3, 1])
    
    with col1:
        main_image_path = Path("asset") / "SeoulTripView.png"
        if main_image_path.exists():
            st.image(main_image_path, use_container_width=True)
        else:
            st.info("이미지를 찾을 수 없습니다: asset/SeoulTripView.png")
    
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
        
        # API 키 확인
        api_key = st.session_state.google_maps_api_key
        if not api_key or api_key == "YOUR_GOOGLE_MAPS_API_KEY":
            st.error("Google Maps API 키가 설정되지 않았습니다.")
            api_key = st.text_input("Google Maps API 키를 입력하세요", type="password")
            if api_key:
                st.session_state.google_maps_api_key = api_key
                st.success("API 키가 설정되었습니다.")
            else:
                st.info("Google Maps를 사용하려면 API 키가 필요합니다.")
                return
        
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
            st.rerun()

#################################################
# 메인 앱 로직
#################################################

# 데이터 폴더 생성
data_folder = Path("data")
if not data_folder.exists():
    data_folder.mkdir(parents=True, exist_ok=True)

# asset 폴더 생성 (없는 경우)
asset_folder = Path("asset")
if not asset_folder.exists():
    asset_folder.mkdir(parents=True, exist_ok=True)

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
