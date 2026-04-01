import streamlit as st
import requests
from PIL import Image, ImageDraw, ImageFont
import io
import urllib3
import datetime
import re

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- 날씨 및 데이터 가져오기 함수 ---

def get_current_weather():
    try:
        # m: 섭씨(metric), 1: 현재 날씨 한 줄만 가져오기
        # format=%C+%t: 날씨상태와 온도를 가져옴
        response = requests.get("https://wttr.in?format=%C+%t&m", timeout=5)
        if response.status_code == 200:
            weather_data = response.text.strip()
            
            # 깨질 수 있는 특수문자나 단위를 정제
            weather_data = weather_data.replace('+', '') # + 기호 제거
            
            # 영어 날씨 상태를 한국어로 간단히 매핑 (필요시 추가)
            weather_map = {
                "Clear": "맑음", "Sunny": "쾌청", "Partly cloudy": "구름 조금",
                "Cloudy": "흐림", "Overcast": "매우 흐림", "Mist": "안개",
                "Patchy rain possible": "가끔 비", "Rain": "비", "Snow": "눈"
            }
            
            for eng, kor in weather_map.items():
                if eng in weather_data:
                    weather_data = weather_data.replace(eng, kor)
                    break
            
            return weather_data
    except Exception:
        return "맑음 15°C"
    return "맑음 15°C"

@st.cache_data
def search_artists(query):
    url = f"https://itunes.apple.com/search?term={query}&entity=musicArtist&limit=5"
    try:
        response = requests.get(url, verify=False)
        if response.status_code == 200:
            return response.json().get('results', [])
    except Exception:
        return []
    return []

@st.cache_data
def get_albums(artist_id):
    url = f"https://itunes.apple.com/lookup?id={artist_id}&entity=album"
    try:
        response = requests.get(url, verify=False)
        if response.status_code == 200:
            results = response.json().get('results', [])
            return [r for r in results if r.get('wrapperType') == 'collection']
    except Exception:
        return []
    return []

@st.cache_data
def get_tracks(collection_id):
    url = f"https://itunes.apple.com/lookup?id={collection_id}&entity=song"
    try:
        response = requests.get(url, verify=False)
        if response.status_code == 200:
            results = response.json().get('results', [])
            return [r for r in results if r.get('wrapperType') == 'track']
    except Exception:
        return []
    return []

# --- 이미지 생성 함수 (동일) ---

def wrap_text(text, font, max_width, draw):
    lines = []
    if not text: return ""
    for paragraph in text.splitlines():
        current_line = ""
        for char in paragraph:
            test_line = current_line + char
            if draw.textbbox((0, 0), test_line, font=font)[2] <= max_width:
                current_line = test_line
            else:
                lines.append(current_line)
                current_line = char
        if current_line:
            lines.append(current_line)
    return '\n'.join(lines)

def create_music_card(album_url, title, artist, genre, rating, review, date_str, weather_str):
    img_res = requests.get(album_url.replace("100x100bb", "600x600bb"), verify=False)
    album_img = Image.open(io.BytesIO(img_res.content)).convert("RGB")
    
    card_w, card_h = 800, 1000
    card = Image.new('RGB', (card_w, card_h), color="#F9F6F0")
    draw = ImageDraw.Draw(card)
    
    try:
        font_path = "KoPub Dotum Medium.ttf"
        font_title = ImageFont.truetype(font_path, 46)
        font_artist = ImageFont.truetype(font_path, 30)
        font_star = ImageFont.truetype(font_path, 40)
        font_review = ImageFont.truetype(font_path, 32)
        font_date = ImageFont.truetype(font_path, 22)
    except:
        font_title = ImageFont.load_default()
        font_artist = ImageFont.load_default()
        font_star = ImageFont.load_default()
        font_review = ImageFont.load_default()
        font_date = ImageFont.load_default()

    album_size = 520
    album_x = (card_w - album_size) // 2
    
    # 우측 상단 날짜 및 날씨 배치
    date_weather_text = f"{date_str}  {weather_str}"
    dw_bbox = draw.textbbox((0, 0), date_weather_text, font=font_date)
    dw_w = dw_bbox[2] - dw_bbox[0]
    draw.text((album_x + album_size - dw_w, 40), date_weather_text, fill="#8B7355", font=font_date)
    
    y_pos = 80
    album_img = album_img.resize((album_size, album_size), Image.Resampling.LANCZOS)
    card.paste(album_img, (album_x, y_pos))
    
    y_pos += album_size + 40
    x_start = 40
    allowed_width = card_w - (x_start * 2)

    wrapped_title = wrap_text(title, font_title, allowed_width, draw)
    title_bbox = draw.multiline_textbbox((0, 0), wrapped_title, font=font_title, align="center")
    title_w = title_bbox[2] - title_bbox[0]
    draw.multiline_text(((card_w - title_w) // 2, y_pos), wrapped_title, fill="#3E3A39", font=font_title, align="center")
    
    y_pos += (title_bbox[3] - title_bbox[1]) + 30
    
    artist_line = f"{artist} · #{genre.replace(' ', '_')}"
    wrapped_artist = wrap_text(artist_line, font_artist, allowed_width, draw)
    artist_bbox = draw.multiline_textbbox((0, 0), wrapped_artist, font=font_artist, align="center")
    artist_w = artist_bbox[2] - artist_bbox[0]
    draw.multiline_text(((card_w - artist_w) // 2, y_pos), wrapped_artist, fill="#8B7355", font=font_artist, align="center")
    
    y_pos += (artist_bbox[3] - artist_bbox[1]) + 30
    
    stars = "★" * int(rating) + "☆" * (5 - int(rating))
    star_bbox = draw.textbbox((0, 0), stars, font=font_star)
    star_w = star_bbox[2] - star_bbox[0]
    draw.text(((card_w - star_w) // 2, y_pos), stars, fill="#3E3A39", font=font_star)
    
    y_pos += (star_bbox[3] - star_bbox[1]) + 35
    
    wrapped_review = wrap_text(review, font_review, allowed_width, draw)
    draw.multiline_text((x_start, y_pos), wrapped_review, fill="#4A4A4A", font=font_review, spacing=10)
    
    return card

# --- UI 설정 및 메인 로직 ---

st.set_page_config(page_title="뮤직 프레임 노트", layout="centered")

st.markdown("""
<style>
    @import url('https://webfontworld.github.io/kopub/KoPubDotum.css');
    * { font-family: 'KoPubDotum', sans-serif !important; font-weight: 500; }
    .stApp { background-color: #3B261D; }
    h1, h2, h3, p, label { color: #E8DECC !important; }
    .stTextInput>div>div>input, .stSelectbox>div>div>div {
        background-color: #2A1A12; color: #E8DECC !important; border: 1px solid #5C3D2E; border-radius: 4px;
    }
    .stButton>button, div[data-testid="stDownloadButton"]>button {
        background-color: #5C3D2E !important; color: #E8DECC !important;
        border: 1px solid #2A1A12 !important; border-radius: 8px !important;
    }
    .lp-container { display: flex; justify-content: center; margin: 20px 0; }
    .lp-container img {
        border-radius: 50%; border: 12px solid #111111; box-shadow: 5px 5px 20px rgba(0,0,0,0.6);
        width: 250px; height: 250px; object-fit: cover;
    }
    header {visibility: hidden;} footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

st.title("뮤직 프레임 노트")

if 'step' not in st.session_state: st.session_state.step = 'artist'
if 'selected_artist' not in st.session_state: st.session_state.selected_artist = None
if 'selected_album' not in st.session_state: st.session_state.selected_album = None

if st.session_state.step == 'artist':
    artist_query = st.text_input("아티스트 이름을 입력해줘.")
    if artist_query:
        artists = search_artists(artist_query)
        if artists:
            for artist in artists:
                if st.button(f"{artist['artistName']} ({artist.get('primaryGenreName', 'Genre')})", use_container_width=True):
                    st.session_state.selected_artist = artist
                    st.session_state.step = 'album'
                    st.rerun()
        else:
            st.warning("아티스트를 찾지 못했어.")

elif st.session_state.step == 'album':
    st.subheader(f"{st.session_state.selected_artist['artistName']}의 앨범들")
    if st.button("← 다시 검색하기"):
        st.session_state.step = 'artist'
        st.rerun()
    
    albums = get_albums(st.session_state.selected_artist['artistId'])
    if albums:
        cols = st.columns(3)
        for idx, album in enumerate(albums):
            with cols[idx % 3]:
                img_url = album['artworkUrl100'].replace("100x100bb", "300x300bb")
                st.image(img_url, use_container_width=True)
                if st.button("선택", key=f"album_{idx}", use_container_width=True):
                    st.session_state.selected_album = album
                    st.session_state.step = 'track'
                    st.rerun()
                st.write(f"<p style='font-size:0.8rem; text-align:center;'>{album['collectionName']}</p>", unsafe_allow_html=True)

elif st.session_state.step == 'track':
    album = st.session_state.selected_album
    st.subheader(f"'{album['collectionName']}' 수록곡")
    if st.button("← 앨범 다시 고르기"):
        st.session_state.step = 'album'
        st.rerun()
        
    tracks = get_tracks(album['collectionId'])
    if tracks:
        track_names = {f"{t['trackName']}": t for t in tracks}
        selected_track_name = st.selectbox("기록하고 싶은 곡을 골라줘.", list(track_names.keys()))
        selected_track = track_names[selected_track_name]
        
        lp_url = album['artworkUrl100'].replace("100x100bb", "400x400bb")
        st.markdown(f'<div class="lp-container"><img src="{lp_url}"></div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            rating = st.slider("이 곡은 어땠어.", 1, 5, 5)
        with col2:
            review = st.text_input("그때의 감정을 짧게 남겨줘.")
            
        if st.button("음악 카드 생성하기", use_container_width=True):
            now = datetime.datetime.now()
            date_str = now.strftime("%Y. %m. %d.")
            weather_str = get_current_weather()
            
            card = create_music_card(
                album['artworkUrl100'],
                selected_track['trackName'],
                selected_track['artistName'],
                album['primaryGenreName'],
                rating,
                review,
                date_str,
                weather_str
            )
            
            st.image(card, use_container_width=True)
            img_io = io.BytesIO()
            card.save(img_io, format='JPEG', quality=95)
            st.download_button("카드 저장하기", img_io.getvalue(), "music_log.jpg", "image/jpeg", use_container_width=True)
