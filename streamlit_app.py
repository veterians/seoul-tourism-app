import streamlit as st
import pandas as pd
import json
import os
import time
import random
from datetime import datetime
from pathlib import Path
from geopy.distance import geodesic

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

# 추천 코스 데이터
RECOMMENDATION_COURSES = {
    "문화 코스": ["경복궁", "인사동", "창덕궁", "북촌한옥마을"],
    "쇼핑 코스": ["동대문 DDP", "명동", "광장시장", "남산서울타워"],
    "자연 코스": ["서울숲", "남산서울타워", "한강공원", "북한산"],
    "대중적 코스": ["경복궁", "명동", "남산서울타워", "63빌딩"]
}

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
        st.image("https://i.imgur.com/W3UVTgZ.png", width=100)  # 사용자 아이콘
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
        
    # Google Maps API 키
    if "google_maps_api_key" not in st.session_state:
        # secrets.toml에서 가져오기 시도
        try:
            st.session_state.google_maps_api_key = st.secrets["google_maps_api_key"]
        except:
            st.session_state.google_maps_api_key = ""
    
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
                return True
    except Exception as e:
        print(f"세션 데이터 로드 오류: {e}")
    return False

def save_session_data():
    """세션 데이터 저장"""
    try:
        # 데이터 폴더 생성
        os.makedirs(os.path.dirname(SESSION_DATA_FILE), exist_ok=True)
        
        data = {
            "users": st.session_state.users,
            "user_visits": st.session_state.user_visits,
            "user_xp": st.session_state.user_xp
        }
        
        with open(SESSION_DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"세션 데이터 저장 오류: {e}")
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

def load_excel_files(language="한국어"):
    """데이터 폴더에서 모든 Excel 파일 로드"""
    data_folder = Path("asset")
    all_markers = []
    
    if not data_folder.exists():
        st.warning("데이터 폴더가 존재하지 않습니다.")
        return []
        
    # 모든 Excel 파일 찾기
    excel_files = list(data_folder.glob("*.xlsx"))
    
    if not excel_files:
        st.warning("데이터 폴더에 Excel 파일이 없습니다.")
        return []
    
    for file_path in excel_files:
        try:
            # 파일 카테고리 결정
            file_category = "기타"
            file_name = file_path.name.lower()
            
            for category, keywords in FILE_CATEGORIES.items():
                if any(keyword.lower() in file_name for keyword in keywords):
                    file_category = category
                    break
            
            # 파일 로드
            df = pd.read_excel(file_path, engine='openpyxl')
            
            # 데이터 전처리 및 마커 변환
            markers = process_dataframe(df, file_category, language)
            all_markers.extend(markers)
            
            st.success(f"{file_path.name}: {len(markers)}개 마커 로드")
        
        except Exception as e:
            st.error(f"{file_path.name} 처리 오류: {str(e)}")
    
    return all_markers

def process_dataframe(df, category, language="한국어"):
    """데이터프레임을 Google Maps 마커 형식으로 변환"""
    markers = []
    
    # 필수 열 확인: X좌표, Y좌표
    if 'X좌표' not in df.columns or 'Y좌표' not in df.columns:
        # 중국어 데이터의 경우 열 이름이 다를 수 있음
        if 'X坐标' in df.columns and 'Y坐标' in df.columns:
            df['X좌표'] = df['X坐标']
            df['Y좌표'] = df['Y坐标']
        else:
            st.warning(f"'{category}' 데이터에 좌표 열이 없습니다.")
            return []
    
    # 언어별 열 이름 결정
    name_col = '명칭(한국어)'
    if language == "영어" and '명칭(영어)' in df.columns:
        name_col = '명칭(영어)'
    elif language == "중국어" and '명칭(중국어)' in df.columns:
        name_col = '명칭(중국어)'
    
    # 중국어 종로구 데이터 특별 처리
    if category == "종로구 관광지" and language == "중국어":
        if '名称' in df.columns:
            name_col = '名称'
    
    # 주소 열 결정
    address_col = None
    address_candidates = ['주소(한국어)', '주소', '소재지', '도로명주소', '지번주소']
    if language == "영어":
        address_candidates = ['주소(영어)'] + address_candidates
    elif language == "중국어":
        address_candidates = ['주소(중국어)', '地址'] + address_candidates
    
    for col in address_candidates:
        if col in df.columns:
            address_col = col
            break
    
    # 유효한 좌표 데이터만 사용
    df = df.dropna(subset=['X좌표', 'Y좌표'])
    valid_coords = (df['X좌표'] >= 124) & (df['X좌표'] <= 132) & (df['Y좌표'] >= 33) & (df['Y좌표'] <= 43)
    df = df[valid_coords]
    
    # 마커 색상 결정
    color = CATEGORY_COLORS.get(category, "gray")
    
    # 각 행을 마커로 변환
    for _, row in df.iterrows():
        try:
            # 기본 정보
            name = row[name_col] if name_col in row and pd.notna(row[name_col]) else "이름 없음"
            lat = float(row['Y좌표'])
            lng = float(row['X좌표'])
            
            # 주소 정보
            address = ""
            if address_col and address_col in row and pd.notna(row[address_col]):
                address = row[address_col]
            
            # 추가 정보 (있는 경우)
            info = ""
            if address:
                info += f"주소: {address}<br>"
            
            # 전화번호 (있는 경우)
            for tel_col in ['전화번호', 'TELNO', '연락처']:
                if tel_col in row and pd.notna(row[tel_col]):
                    info += f"전화: {row[tel_col]}<br>"
                    break
            
            # 마커 생성
            marker = {
                'lat': lat,
                'lng': lng,
                'title': name,
                'color': color,
                'category': category,
                'info': info
            }
            markers.append(marker)
            
        except Exception as e:
            print(f"마커 생성 오류: {e}")
            continue
    
    return markers

def create_google_maps_html(api_key, center_lat, center_lng, markers=None, zoom=13, language="ko"):
    """Google Maps HTML 생성"""
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
            legend_html_item = '<div class="legend-item"><img src="http://maps.google.com/mapfiles/ms/icons/'
            legend_html_item += color 
            legend_html_item += '-dot.png" alt="'
            legend_html_item += category 
            legend_html_item += '"> '
            legend_html_item += category
            legend_html_item += ' ('
            legend_html_item += str(count)
            legend_html_item += ')</div>'
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
        icon_url = "http://maps.google.com/mapfiles/ms/icons/" + color + "-dot.png"
        
        # 정보창 HTML 내용
        info_content = """
            <div style="padding: 10px; max-width: 300px;">
                <h3 style="margin-top: 0; color: #1976D2;">{0}</h3>
                <p><strong>분류:</strong> {1}</p>
                <div>{2}</div>
            </div>
        """.format(title, category, info).replace("'", "\\\\'").replace("\n", "")
        
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
                if (category === 'all' || markerCategories[i] === category) {
                    markers[i].setVisible(true);
                } else {
                    markers[i].setVisible(false);
                }
            }
            
            // 필터 버튼 활성화 상태 업데이트
            document.querySelectorAll('.filter-button').forEach(function(btn) {
                btn.classList.remove('active');
            });
            document.getElementById('filter-' + category).classList.add('active');
        }
    """
    
    # 마커 클러스터링 코드
    clustering_js = """
        // 마커 클러스터링
        var markerCluster = new MarkerClusterer(map, markers, {
            imagePath: 'https://developers.google.com/maps/documentation/javascript/examples/markerclusterer/m',
            maxZoom: 15,
            gridSize: 50
        });
    """
    
    # 필터 버튼 HTML 생성
    filter_buttons = '<button id="filter-all" class="filter-button active" onclick="filterMarkers(\'all\')">전체 보기</button>'
    for cat in categories.keys():
        filter_buttons += ' <button id="filter-' + cat + '" class="filter-button" onclick="filterMarkers(\'' + cat + '\')">' + cat + '</button>'
    
    # 전체 HTML 코드 생성 - 문자열 결합으로 f-string 대신 사용
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>서울 관광 지도</title>
        <meta charset="utf-8">
        <style>
            #map {
                height: 100%;
                width: 100%;
                margin: 0;
                padding: 0;
            }
            html, body {
                height: 100%;
                margin: 0;
                padding: 0;
                font-family: 'Noto Sans KR', Arial, sans-serif;
            }
            .map-controls {
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
            }
            .filter-button {
                margin: 5px;
                padding: 5px 10px;
                background-color: #f8f9fa;
                border: 1px solid #dadce0;
                border-radius: 4px;
                cursor: pointer;
            }
            .filter-button:hover {
                background-color: #e8eaed;
            }
            .filter-button.active {
                background-color: #1976D2;
                color: white;
            }
            #legend {
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
            }
            .legend-item {
                margin-bottom: 5px;
                display: flex;
                align-items: center;
            }
            .legend-item img {
                width: 20px;
                height: 20px;
                margin-right: 5px;
            }
            .custom-control {
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
            }
        </style>
        <script src="https://developers.google.com/maps/documentation/javascript/examples/markerclusterer/markerclusterer.js"></script>
    </head>
    <body>
        <div id="map"></div>
        
        <!-- 카테고리 필터 -->
        <div class="map-controls" id="category-filter">
            <div style="margin-bottom: 8px; font-weight: bold;">카테고리 필터</div>
            """ + filter_buttons + """
        </div>
        
        <!-- 지도 범례 -->
        <div id="legend">
            <div style="font-weight: bold; margin-bottom: 8px;">지도 범례</div>
            """ + legend_html + """
        </div>
        
        <script>
            // 지도 변수
            var map;
            var markers = [];
            var markerCategories = [];
            var infoWindows = [];
            var currentMarker = null;
            
            // 모든 정보창 닫기
            function closeAllInfoWindows() {
                for (var i = 0; i < infoWindows.length; i++) {
                    infoWindows[i].close();
                }
            }
            
            function initMap() {
                // 지도 생성
                map = new google.maps.Map(document.getElementById('map'), {
                    center: { lat: """ + str(center_lat) + """, lng: """ + str(center_lng) + """ },
                    zoom: """ + str(zoom) + """,
                    fullscreenControl: true,
                    mapTypeControl: true,
                    streetViewControl: true,
                    zoomControl: true,
                    mapTypeId: 'roadmap'
                });
                
                // 현재 위치 버튼 추가
                const locationButton = document.createElement("button");
                locationButton.textContent = "📍 내 위치";
                locationButton.classList.add("custom-control");
                locationButton.addEventListener("click", () => {
                    if (navigator.geolocation) {
                        navigator.geolocation.getCurrentPosition(
                            (position) => {
                                const pos = {
                                    lat: position.coords.latitude,
                                    lng: position.coords.longitude,
                                };
                                
                                // 부모 창에 현재 위치 전달
                                window.parent.postMessage({
                                    'type': 'current_location',
                                    'lat': pos.lat,
                                    'lng': pos.lng
                                }, '*');
                                
                                map.setCenter(pos);
                                map.setZoom(15);
                                
                                // 현재 위치 마커 추가
                                new google.maps.Marker({
                                    position: pos,
                                    map: map,
                                    title: '내 위치',
                                    icon: {
                                        path: google.maps.SymbolPath.CIRCLE,
                                        fillColor: '#4285F4',
                                        fillOpacity: 1,
                                        strokeColor: '#FFFFFF',
                                        strokeWeight: 2,
                                        scale: 8
                                    }
                                });
                            },
                            () => {
                                alert("위치 정보를 가져오는데 실패했습니다.");
                            }
                        );
                    } else {
                        alert("이 브라우저에서는 위치 정보 기능을 지원하지 않습니다.");
                    }
                });
                
                map.controls[google.maps.ControlPosition.TOP_RIGHT].push(locationButton);
                
                // 범례를 지도에 추가
                map.controls[google.maps.ControlPosition.RIGHT_BOTTOM].push(
                    document.getElementById('legend')
                );
                
                // 마커 추가
                """ + markers_js + """
                
                // 마커 클러스터링
                """ + clustering_js + """
                
                // 필터링 함수
                """ + filter_js + """
                
                // 지도 클릭 이벤트
                map.addListener('click', function(event) {
                    // 열린 정보창 닫기
                    closeAllInfoWindows();
                    
                    // 바운스 애니메이션 중지
                    if (currentMarker) currentMarker.setAnimation(null);
                    
                    // 클릭 이벤트 데이터 전달
                    window.parent.postMessage({
                        'type': 'map_click',
                        'lat': event.latLng.lat(),
                        'lng': event.latLng.lng()
                    }, '*');
                });
            }
        </script>
        <script src="https://maps.googleapis.com/maps/api/js?key=""" + api_key + """&callback=initMap&language=""" + language + """" async defer></script>
    </body>
    </html>
    """
    
    return html
    
def show_google_map(api_key, center_lat, center_lng, markers=None, zoom=13, height=600, language="한국어"):
    """Google Maps 컴포넌트 표시"""
    # 언어 코드 변환
    lang_code = LANGUAGE_CODES.get(language, "ko")
    
    # HTML 생성
    map_html = create_google_maps_html(
        api_key=api_key,
        center_lat=center_lat,
        center_lng=center_lng,
        markers=markers,
        zoom=zoom,
        language=lang_code
    )
    
    # HTML 컴포넌트로 표시
    st.components.v1.html(map_html, height=height, scrolling=False)

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
        
        # 메인 이미지
        main_image_path = Path("asset") / "SeoulTripView.png"
        st.image(main_image_path, width=300)
        
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


# def show_login_page():
#     """로그인 페이지 표시"""
#     col1, col2, col3 = st.columns([1, 2, 1])
    
#     with col2:
#         page_header("서울 관광앱")
# #       st.image("https://github.com/veterians/seoul-tourism-app/blob/main/asset/SeoulTripView.png", width=300)
#         main_image_path = Path("asset") / "SeoulTripView.png"
#         st.image(main_image_path, width=300)
        
#         tab1, tab2 = st.tabs(["Login", "Join"])

#         with tab1:
#             st.markdown("### Login")
#             username = st.text_input("ID", key="login_username")
#             password = st.text_input("PW", type="password", key="login_password")
#             col1, col2 = st.columns([1,1])
#             with col1:
#                 remember = st.checkbox("아이디 저장")
#             with col2:
#                 st.markdown("")  # 빈 공간
            
#             if st.button("Login", use_container_width=True):
#                 if authenticate_user(username, password):
#                     st.success("🎉 로그인 성공!")
#                     st.session_state.logged_in = True
#                     st.session_state.username = username
#                     change_page("menu")
#                     st.rerun()
#                 else:
#                     st.error("❌ 아이디 또는 비밀번호가 올바르지 않습니다.")

#         with tab2:
#             st.markdown("### Join")
#             new_user = st.text_input("새 아이디", key="register_username")
#             new_pw = st.text_input("새 비밀번호", type="password", key="register_password")
#             new_pw_confirm = st.text_input("비밀번호 확인", type="password", key="register_password_confirm")
            
#             if st.button("Join", use_container_width=True):
#                 if not new_user or not new_pw:
#                     st.error("아이디와 비밀번호를 입력해주세요.")
#                 elif new_pw != new_pw_confirm:
#                     st.error("비밀번호와 비밀번호 확인이 일치하지 않습니다.")
#                 elif register_user(new_user, new_pw):
#                     st.success("✅ 회원가입 완료!")
#                     st.session_state.logged_in = True
#                     st.session_state.username = new_user
#                     change_page("menu")
#                     st.rerun()
#                 else:
#                     st.warning("⚠️ 이미 존재하는 아이디입니다.")

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
    """지도 페이지 표시"""
    page_header("서울 관광 장소 지도")
    
    # 뒤로가기 버튼
    if st.button("← 메뉴로 돌아가기"):
        change_page("menu")
        st.rerun()
    
    # API 키 확인
    api_key = st.session_state.google_maps_api_key
    if not api_key:
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
    
    # 데이터 로드 컨트롤
    with st.sidebar:
        st.header("데이터 관리")
        
        # 데이터 로드 버튼
        if st.button("서울 관광 데이터 로드", use_container_width=True):
            with st.spinner("데이터를 로드하는 중..."):
                all_markers = load_excel_files(st.session_state.language)
                if all_markers:
                    st.session_state.all_markers = all_markers
                    st.session_state.markers_loaded = True
                    st.success(f"총 {len(all_markers)}개의 관광지 로드 완료!")
                else:
                    st.warning("데이터를 로드할 수 없습니다.")
        
        # 파일 업로드
        uploaded_files = st.file_uploader(
            "Excel 파일 업로드 (.xlsx)",
            type=["xlsx"],
            accept_multiple_files=True
        )
        
        if uploaded_files:
            if st.button("업로드한 파일 처리", use_container_width=True):
                with st.spinner("파일을 처리하는 중..."):
                    # 파일 처리 로직 (실제 구현 필요)
                    st.success("파일 업로드 완료!")
    
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
            if hasattr(st.session_state, 'all_markers') and st.session_state.all_markers:
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
            if search_term and hasattr(st.session_state, 'all_markers') and st.session_state.all_markers:
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
            if hasattr(st.session_state, 'all_markers') and st.session_state.all_markers:
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
                        st.session_state.transport_mode = "walk"
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
                        st.session_state.transport_mode = "car"
                        st.rerun()
                
                if st.button("← 지도로 돌아가기", use_container_width=True):
                    st.session_state.navigation_active = False
                    st.rerun()
            
            else:
                # 선택된 교통수단에 따른 내비게이션 표시
                transport_mode = st.session_state.transport_mode
                transport_icons = {
                    "walk": "🚶",
                    "transit": "🚍",
                    "car": "🚗"
                }
                transport_names = {
                    "walk": "도보",
                    "transit": "대중교통",
                    "car": "자동차"
                }
                
                st.markdown(f"### {transport_icons[transport_mode]} {transport_names[transport_mode]} 경로")
                
                # 경로 데이터 준비 (두 지점 연결)
                route = [
                    {"lat": user_lat, "lng": user_lng},  # 출발지
                    {"lat": dest_lat, "lng": dest_lng}   # 목적지
                ]
                
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
                    # 지도에 출발지-목적지 경로 표시
                    show_google_map(
                        api_key=api_key,
                        center_lat=(user_lat + dest_lat) / 2,  # 중간 지점
                        center_lng=(user_lng + dest_lng) / 2,
                        markers=markers,
                        zoom=14,
                        height=600,
                        language=st.session_state.language
                    )
                
                with info_col:
                    # 경로 정보 표시
                    st.markdown("### 경로 정보")
                    st.markdown(f"**{destination['name']}까지**")
                    st.markdown(f"- 거리: {distance:.0f}m")
                    
                    # 교통수단별 예상 시간
                    if transport_mode == "walk":
                        speed = 67  # m/min
                        transport_desc = "도보"
                    elif transport_mode == "transit":
                        speed = 200  # m/min
                        transport_desc = "대중교통"
                    else:  # car
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
                    other_modes = {"walk": "도보", "transit": "대중교통", "car": "자동차"}
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
    """관광 코스 추천 페이지 표시"""
    page_header("서울 관광 코스 짜주기")
    
    # 뒤로가기 버튼
    if st.button("← 메뉴로 돌아가기"):
        change_page("menu")
        st.rerun()
    
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
        st.rerun()
    
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
            st.rerun()

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
