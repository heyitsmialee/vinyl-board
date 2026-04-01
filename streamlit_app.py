import streamlit as st
import requests
from PIL import Image, ImageDraw, ImageFont
import io
import urllib3
import datetime

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


@st.cache_data
def search_music(query):
    url = f"https://itunes.apple.com/search?term={query}&entity=song&limit=200"
    try:
        response = requests.get(url, verify=False)
        if response.status_code == 200:
            return response.json().get('results', [])
    except Exception:
        return []
    return []


# 현재 날씨를 자동으로 가져오는 함수
def get_current_weather():
    try:
        # wttr.in 서비스를 이용해 현재 위치의 날씨와 온도를 가져옴
        response = requests.get("https://wttr.in?format=%C+%t", timeout=5)
        if response.status_code == 200:
            return response.text.strip()
    except Exception:
        return "맑음"  # 정보를 가져오지 못할 경우 기본값
    return "맑음"


def wrap_text(text, font, max_width, draw):
    lines = []
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
        font_title = ImageFont.truetype("KoPub Dotum Medium.ttf", 46)
        font_artist = ImageFont.truetype("KoPub Dotum Medium.ttf", 30)
        font_star = ImageFont.truetype("KoPub Dotum Medium.ttf", 40)
        font_review = ImageFont.truetype("KoPub Dotum Medium.ttf", 32)
        font_date = ImageFont.truetype("KoPub Dotum Medium.ttf", 22)
    except:
        font_title = ImageFont.load_default()
        font_artist = ImageFont.load_default()
        font_star = ImageFont.load_default()
        font_review = ImageFont.load_default()
        font_date = ImageFont.load_default()

    album_size = 520
    album_x = (card_w - album_size) // 2

    # 앨범 커버 우측 상단에 자동 생성된 날짜와 날씨 배치
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
    draw.multiline_text(((card_w - title_w) // 2, y_pos), wrapped_title, fill="#3E3A39", font=font_title,
                        align="center")
    y_pos += (title_bbox[3] - title_bbox[1]) + 30

    artist_line = f"{artist} · #{genre.replace(' ', '_')}"
    wrapped_artist = wrap_text(artist_line, font_artist, allowed_width, draw)
    artist_bbox = draw.multiline_textbbox((0, 0), wrapped_artist, font=font_artist, align="center")
    artist_w = artist_bbox[2] - artist_bbox[0]
    draw.multiline_text(((card_w - artist_w) // 2, y_pos), wrapped_artist, fill="#8B7355", font=font_artist,
                        align="center")
    y_pos += (artist_bbox[3] - artist_bbox[1]) + 30

    stars = "★" * int(rating) + "☆" * (5 - int(rating))
    star_bbox = draw.textbbox((0, 0), stars, font=font_star)
    star_w = star_bbox[2] - star_bbox[0]
    draw.text(((card_w - star_w) // 2, y_pos), stars, fill="#3E3A39", font=font_star)
    y_pos += (star_bbox[3] - star_bbox[1]) + 35

    wrapped_review = wrap_text(review, font_review, allowed_width, draw)
    draw.multiline_text((x_start, y_pos), wrapped_review, fill="#4A4A4A", font=font_review, spacing=10)

    return card


st.set_page_config(page_title="뮤직 프레임 노트", layout="centered")

st.markdown("""
<style>
    @import url('https://webfontworld.github.io/kopub/KoPubDotum.css');

    * {
        font-family: 'KoPubDotum', sans-serif !important;
        font-weight: 500;
    }

    .stApp {
        background-color: #3B261D;
    }
    h1, h2, h3, p, label {
        color: #E8DECC !important;
    }
    .stTextInput>div>div>input, .stTextArea>div>div>textarea, .stSelectbox>div>div>div {
        background-color: #2A1A12;
        color: #E8DECC !important;
        border: 1px solid #5C3D2E;
        border-radius: 4px;
    }
    ul[role="listbox"] {
        background-color: #F9F6F0 !important;
    }
    ul[role="listbox"] li, ul[role="listbox"] li span {
        color: #3B261D !important;
    }
    .stButton>button, div[data-testid="stDownloadButton"]>button {
        background-color: #5C3D2E !important;
        color: #E8DECC !important;
        border: 1px solid #2A1A12 !important;
        border-radius: 8px !important;
        transition: all 0.3s ease !important;
    }
    .stButton>button:hover, div[data-testid="stDownloadButton"]>button:hover {
        border-color: #E8DECC !important;
        color: #FFFFFF !important;
    }
    .lp-container {
        display: flex;
        justify-content: center;
        margin: 40px 0;
    }
    .lp-container img {
        border-radius: 50%;
        border: 16px solid #111111;
        box-shadow: 5px 5px 25px rgba(0,0,0,0.8);
        transition: transform 2s ease-out;
        width: 320px;
        height: 320px;
        object-fit: cover;
    }
    .lp-container img:hover {
        transform: rotate(180deg);
    }
    header {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

st.title("뮤직 프레임 노트")
st.markdown("오늘의 문장을 엘피와 함께 기록해봐.")

query = st.text_input("기록하고 싶은 노래나 아티스트를 검색해줘.")
if query:
    results = search_music(query)
    if results:
        selected = st.selectbox(
            "정확한 곡을 골라줘.",
            results,
            format_func=lambda r: f"{r.get('trackName', 'Unknown')} - {r.get('artistName', 'Unknown')}"
        )

        cover_url = selected['artworkUrl100'].replace("100x100bb", "400x400bb")
        st.markdown(f'<div class="lp-container"><img src="{cover_url}"></div>', unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            rating = st.slider("이 곡은 어땠어.", 1, 5, 5)
        with col2:
            review = st.text_input("그때의 감정을 짧게 남겨줘.")

        if st.button("음악 카드 생성하기", use_container_width=True):
            # 날짜와 날씨를 자동으로 생성
            now = datetime.datetime.now()
            date_str = now.strftime("%Y. %m. %d.")
            weather_str = get_current_weather()

            card = create_music_card(
                selected['artworkUrl100'],
                selected['trackName'],
                selected['artistName'],
                selected['primaryGenreName'],
                rating,
                review,
                date_str,
                weather_str
            )

            st.markdown("<br>인쇄용 카드 미리보기", unsafe_allow_html=True)
            st.image(card, use_container_width=True)

            img_io = io.BytesIO()
            card.save(img_io, format='JPEG', quality=95)
            st.download_button("카드 저장하기", img_io.getvalue(), "music_log.jpg", "image/jpeg", use_container_width=True)
    else:
        st.warning("검색 결과가 없어. 다른 키워드로 검색해볼까.")
