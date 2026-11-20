%%writefile app.py
import streamlit as st
import requests
import re
from google import genai
from googleapiclient.discovery import build

# --- పేజీ సెట్టింగ్స్ ---
st.set_page_config(
    page_title="Link-to-Growth AI (A to Z Analyzer)",
    page_icon="🚀",
    layout="wide"
)

st.title("🚀 YouTube, Instagram Reels & TikTok Link-to-Growth AI")
st.markdown("కేవలం వీడియో లింక్ పేస్ట్ చేయండి — పూర్తి **A to Z గ్రోత్ & వైరల్ రిపోర్ట్** పొందండి!")

# --- సైడ్‌బార్: API కీస్ సెటప్ ---
with st.sidebar:
    st.header("🔑 API కీస్ సెట్టింగ్స్")
    gemini_api_key = st.text_input("Gemini API Key", type="password", help="Google AI Studio నుండి పొందిన కీ")
    youtube_api_key = st.text_input("YouTube Data API v3 Key", type="password", help="Google Cloud Console నుండి పొందిన కీ")
    rapidapi_key = st.text_input("RapidAPI Key (Insta & TikTok)", type="password", help="RapidAPI నుండి పొందిన కీ")
    
    st.divider()
    st.info("💡 **గమనిక:** అన్ని API కీలు ఎంటర్ చేసిన తర్వాతే అనాలిసిస్ ప్రారంభించండి.")

# --- హెల్పర్ ఫంక్షన్స్ ---

def extract_youtube_id(url):
    pattern = r"(?:v=|\/)([0-9A-Za-z_-]{11}).*"
    match = re.search(pattern, url)
    return match.group(1) if match else None

def get_youtube_data(video_id, api_key):
    youtube = build("youtube", "v3", developerKey=api_key)
    request = youtube.videos().list(part="snippet,statistics", id=video_id)
    response = request.execute()
    if not response["items"]:
        return None
    item = response["items"][0]
    snippet = item["snippet"]
    stats = item["statistics"]
    
    # టాప్ కామెంట్స్ తెచ్చుకోవడం
    comments = []
    try:
        comment_req = youtube.commentThreads().list(
            part="snippet", videoId=video_id, maxResults=15, order="relevance"
        )
        comment_res = comment_req.execute()
        for c in comment_res.get("items", []):
            comments.append(c["snippet"]["topLevelComment"]["snippet"]["textDisplay"])
    except Exception:
        comments.append("కామెంట్స్ ఆఫ్ చేయబడి ఉన్నాయి లేదా అందుబాటులో లేవు.")

    return {
        "title": snippet.get("title", ""),
        "description": snippet.get("description", "")[:1000],
        "tags": snippet.get("tags", []),
        "views": stats.get("viewCount", "N/A"),
        "likes": stats.get("likeCount", "N/A"),
        "comments_count": stats.get("commentCount", "N/A"),
        "top_comments": comments
    }

def get_instagram_data_rapidapi(reel_url, api_key):
    """
    గమనిక: మీరు RapidAPI లో సబ్‌స్క్రైబ్ చేసుకున్న Instagram API యొక్క 
    సరైన Host మరియు Endpoint URL ను క్రింద అప్‌డేట్ చేయండి.
    """
    url = "https://rapidapi.com" # ఉదాహరణ Endpoint
    querystring = {"code_or_id_or_url": reel_url}
    headers = {
        "x-rapidapi-key": api_key,
        "x-rapidapi-host": "://rapidapi.com" # మీ RapidAPI Host ఇక్కడ ఇవ్వండి
    }
    response = requests.get(url, headers=headers, params=querystring)
    if response.status_code == 200:
        data = response.json().get("data", {})
        caption_data = data.get("caption") or {}
        metrics = data.get("metrics") or {}
        return {
            "caption": caption_data.get("text", "క్యాప్షన్ లేదు"),
            "likes": metrics.get("like_count", "N/A"),
            "comments_count": metrics.get("comment_count", "N/A"),
            "plays": metrics.get("play_count", "N/A"),
            "raw_summary": str(data)[:1500]
        }
    else:
        raise Exception(f"RapidAPI Error ({response.status_code}): {response.text}")

def get_tiktok_data_rapidapi(tiktok_url, api_key):
    """
    గమనిక: మీరు RapidAPI లో సబ్‌స్క్రైబ్ చేసుకున్న TikTok API యొక్క 
    సరైన Host మరియు Endpoint URL ను క్రింద అప్‌డేట్ చేయండి.
    """
    url = "https://rapidapi.com" # ఉదాహరణ Endpoint
    querystring = {"url": tiktok_url, "hd": "1"}
    headers = {
        "x-rapidapi-key": api_key,
        "x-rapidapi-host": "://rapidapi.com" # మీ RapidAPI Host ఇక్కడ ఇవ్వండి
    }
    response = requests.get(url, headers=headers, params=querystring)
    if response.status_code == 200:
        data = response.json().get("data", {})
        return {
            "title": data.get("title", "క్యాప్షన్ లేదు"),
            "plays": data.get("play_count", "N/A"),
            "likes": data.get("digg_count", "N/A"),
            "comments_count": data.get("comment_count", "N/A"),
            "shares": data.get("share_count", "N/A"),
            "raw_summary": str(data)[:1500]
        }
    else:
        raise Exception(f"RapidAPI Error ({response.status_code}): {response.text}")

def generate_atoz_report(platform, video_data, api_key):
    client = genai.Client(api_key=api_key)
    
    prompt = f"""
    మీరు ఒక నిపుణుడైన సోషల్ మీడియా గ్రోత్ స్ట్రాటజిస్ట్ మరియు వైరల్ కంటెంట్ అనలిస్ట్.
    క్రింద ఇవ్వబడిన {platform} వీడియో డేటాను విశ్లేషించి, పూర్తి **A to Z గ్రోత్ రిపోర్ట్** ను స్పష్టమైన తెలుగులో అందించండి.

    వీడియో డేటా:
    {video_data}

    రిపోర్ట్‌లో తప్పనిసరిగా ఈ క్రింది అంశాలు ఉండాలి:
    1. **A - Audience & Hook Analysis (ఆడియన్స్ & హుక్ విశ్లేషణ):** మొదటి 3 సెకన్ల ఆకర్షణ మరియు టార్గెట్ ఆడియన్స్.
    2. **B - Benchmark & Metrics (గణాంకాల విశ్లేషణ):** వ్యూస్, లైక్స్ మరియు ఎంగేజ్‌మెంట్ రేట్ పనితీరు.
    3. **C - Content & Caption Breakdown (కంటెంట్ & క్యాప్షన్ లోపాలు/బలాలు):** ఏది బాగా పనిచేసింది? ఏది మెరుగుపరచాలి?
    4. **D - Discovery & SEO / Hashtags (సెర్చ్ & హ్యాష్‌ట్యాగ్ వ్యూహం):** మెరుగైన రీచ్ కోసం 10 హై-రీచ్ ట్యాగ్స్/కీవర్డ్స్.
    5. **E - Engagement Boosters (కామెంట్స్ & షేర్స్ పెంచే చిట్కాలు):** ఆడియన్స్‌తో మాట్లాడించే CTA (Call to Action) ఐడియాలు.
    6. **Z - Zero-to-Viral Next Action Plan (తదుపరి వీడియో ప్లాన్):** ఇదే టాపిక్‌పై దీనికంటే 10 రెట్లు వైరల్ అయ్యే 3 కొత్త వీడియో ఐడియాలు మరియు వాటికి సరిపోయే ఆకర్షణీయమైన టైటిల్స్/హుక్స్.
    """
    
    response = client.models.generate_content(
        model="gemini-3.8-flash",
        contents=prompt
    )
    return response.text

# --- ప్రధాన ట్యాబ్స్ ---
tab1, tab2, tab3 = st.tabs(["📺 YouTube", "📸 Instagram Reels", "🎵 TikTok"])

# 1. YOUTUBE TAB
with tab1:
    st.subheader("YouTube వీడియో & షార్ట్స్ అనలైజర్")
    yt_url = st.text_input("YouTube వీడియో లింక్ ఇక్కడ పేస్ట్ చేయండి:", key="yt_input", placeholder="https://youtube.com...")
    
    if st.button("YouTube A to Z రిపోర్ట్ పొందండి", key="yt_btn", type="primary"):
        if not gemini_api_key or not youtube_api_key:
            st.error("దయచేసి సైడ్‌బార్‌లో Gemini API Key మరియు YouTube API Key ఎంటర్ చేయండి!")
        elif not yt_url:
            st.warning("దయచేసి YouTube లింక్ ఇవ్వండి.")
        else:
            video_id = extract_youtube_id(yt_url)
            if not video_id:
                st.error("సరైన YouTube లింక్ ఇవ్వండి.")
            else:
                with st.spinner("YouTube డేటా సేకరిస్తోంది మరియు AI విశ్లేషిస్తోంది..."):
                    try:
                        yt_data = get_youtube_data(video_id, youtube_api_key)
                        if yt_data:
                            report = generate_atoz_report("YouTube", yt_data, gemini_api_key)
                            st.success("విశ్లేషణ పూర్తయింది!")
                            st.markdown(report)
                        else:
                            st.error("వీడియో వివరాలు దొరకలేదు.")
                    except Exception as e:
                        st.error(f"లోపం సంభవించింది: {e}")

# 2. INSTAGRAM REELS TAB (Optional బాక్స్ తొలగించబడింది)
with tab2:
    st.subheader("Instagram Reels అనలైజర్")
    ig_url = st.text_input("Instagram Reel లింక్ ఇక్కడ పేస్ట్ చేయండి:", key="ig_input", placeholder="https://instagram.com...")
    
    if st.button("Instagram A to Z రిపోర్ట్ పొందండి", key="ig_btn", type="primary"):
        if not gemini_api_key or not rapidapi_key:
            st.error("దయచేసి సైడ్‌బార్‌లో Gemini API Key మరియు RapidAPI Key ఎంటర్ చేయండి!")
        elif not ig_url:
            st.warning("దయచేసి Instagram Reel లింక్ ఇవ్వండి.")
        else:
            with st.spinner("RapidAPI ద్వారా Instagram డేటా సేకరిస్తోంది మరియు AI విశ్లేషిస్తోంది..."):
                try:
                    ig_data = get_instagram_data_rapidapi(ig_url, rapidapi_key)
                    report = generate_atoz_report("Instagram Reels", ig_data, gemini_api_key)
                    st.success("విశ్లేషణ పూర్తయింది!")
                    st.markdown(report)
                except Exception as e:
                    st.error(f"లోపం సంభవించింది: {e}")

# 3. TIKTOK TAB (Optional బాక్స్ తొలగించబడింది)
with tab3:
    st.subheader("TikTok వీడియో అనలైజర్")
    tt_url = st.text_input("TikTok వీడియో లింక్ ఇక్కడ పేస్ట్ చేయండి:", key="tt_input", placeholder="https://tiktok.com...")
    
    if st.button("TikTok A to Z రిపోర్ట్ పొందండి", key="tt_btn", type="primary"):
        if not gemini_api_key or not rapidapi_key:
            st.error("దయచేసి సైడ్‌బార్‌లో Gemini API Key మరియు RapidAPI Key ఎంటర్ చేయండి!")
        elif not tt_url:
            st.warning("దయచేసి TikTok లింక్ ఇవ్వండి.")
        else:
            with st.spinner("RapidAPI ద్వారా TikTok డేటా సేకరిస్తోంది మరియు AI విశ్లేషిస్తోంది..."):
                try:
                    tt_data = get_tiktok_data_rapidapi(tt_url, rapidapi_key)
                    report = generate_atoz_report("TikTok", tt_data, gemini_api_key)
                    st.success("విశ్లేషణ పూర్తయింది!")
                    st.markdown(report)
                except Exception as e:
                    st.error(f"లోపం సంభవించింది: {e}")
