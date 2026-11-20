import os
import re
import time
from google import genai
from googleapiclient.discovery import build
import requests
import streamlit as st

st.set_page_config(page_title="TrendSutra AI - Growth Analyzer", page_icon="logo.png", layout="wide")

GEMINI_KEYS = [st.secrets.get("GEMINI_API_KEY", ""), st.secrets.get("GEMINI_API_KEY_2", "")]
GEMINI_KEYS = [k for k in GEMINI_KEYS if k]
YOUTUBE_KEY = st.secrets.get("YOUTUBE_API_KEY", "")
RAPIDAPI_KEY = st.secrets.get("RAPIDAPI_API_KEY", "")

with st.sidebar:
    st.markdown("## 🌍 Global & Regional Settings")
    report_lang = st.selectbox("Report Language / భాషను ఎంచుకోండి:", ["English (Global)", "Telugu (తెలుగు)", "Tenglish"])
    target_audience = st.radio("Target Audience / ఆడియన్స్ రకం:", ["Regional / Local Audience", "Global / International Audience", "Both (Global + Regional)"])
    st.markdown("---")
    st.success("🎉 **FREE LAUNCH OFFER!**\n\nUnlimited Deep AI Audits are 100% FREE for a limited time!")

# --- సురక్షిత లోగో & టైటిల్ (FileNotFoundError రాకుండా) ---
if os.path.isfile("logo.png"):
    try:
        col_logo, col_title = st.columns([1, 6])
        with col_logo:
            st.image("logo.png", width=100)
        with col_title:
            st.markdown("# TrendSutra AI")
            st.markdown("**A to Z Growth Analyzer for YouTube, Instagram & TikTok | Powered by [AIENGTEL.com](https://aiengtel.com)**")
    except Exception:
        st.markdown("# 🚀 TrendSutra AI")
        st.markdown("**A to Z Growth Analyzer for YouTube, Instagram & TikTok | Powered by [AIENGTEL.com](https://aiengtel.com)**")
else:
    st.markdown("# 🚀 TrendSutra AI")
    st.markdown("**A to Z Growth Analyzer for YouTube, Instagram & TikTok | Powered by [AIENGTEL.com](https://aiengtel.com)**")

st.info("🎁 **Special Launch Access:** Enjoy unlimited real-data AI Growth Audits for free!")

col1, col2 = st.columns([1, 2])
with col1:
    platform = st.selectbox("Select Platform:", ["YouTube", "Instagram Reels", "TikTok"])
with col2:
    video_url = st.text_input("Channel / Profile / Video Link:", placeholder="https://youtu.be... లేదా Reel / TikTok లింక్ పేస్ట్ చేయండి")

def extract_youtube_id(url):
    pattern = r"(?:v=|\/|live\/|shorts\/)([0-9A-Za-z_-]{11}).*"
    match = re.search(pattern, url)
    return match.group(1) if match else None

def fetch_youtube_info(url):
    vid_id = extract_youtube_id(url)
    if not vid_id:
        return None, "సరైన YouTube వీడియో లింక్ ఇవ్వండి (ఉదా: https://youtu.be...)."
    try:
        youtube = build("youtube", "v3", developerKey=YOUTUBE_KEY)
        vid_res = youtube.videos().list(part="snippet,statistics", id=vid_id).execute()
        if not vid_res.get("items"):
            return None, "ఈ వీడియో వివరాలు దొరకలేదు (ప్రైవేట్ వీడియో కావచ్చు)."
        item = vid_res["items"][0]
        snippet = item["snippet"]
        stats = item.get("statistics", {})
        comments = []
        try:
            com_res = youtube.commentThreads().list(part="snippet", videoId=vid_id, maxResults=40, order="relevance", textFormat="plainText").execute()
            for c in com_res.get("items", []):
                comments.append(c["snippet"]["topLevelComment"]["snippet"]["textDisplay"])
        except Exception:
            comments.append("కామెంట్లు ఆఫ్ చేసి ఉన్నాయి.")
        summary = f"Title: {snippet.get('title')}\nViews: {stats.get('viewCount', '0')}, Likes: {stats.get('likeCount', '0')}, Comments: {stats.get('commentCount', '0')}\nDescription: {snippet.get('description', '')[:800]}\nTags: {snippet.get('tags', [])}\nTop Comments: {comments}"
        return summary, stats
    except Exception as e:
        return None, f"YouTube API లోపం: {str(e)}"

def fetch_rapidapi_safe(api_url, host, params, fallback_label):
    try:
        headers = {"x-rapidapi-key": RAPIDAPI_KEY, "x-rapidapi-host": host}
        res = requests.get(api_url, headers=headers, params=params, timeout=15)
        if res.status_code == 200 and res.text and res.text.strip():
            return f"{fallback_label} Data:\n{res.text[:3500]}"
        return f"{fallback_label} URL provided (API status {res.status_code}). Analyze based on URL structure & niche."
    except Exception as e:
        return f"{fallback_label} URL provided (Fetch note: {str(e)})."

def generate_growth_report(platform_name, raw_data, lang, audience):
    prompt = f"""
    You are a {platform_name} Growth Strategist for TrendSutra AI.
    Analyze the data and create an A-to-Z Growth Audit Report.
    - Output Language: {lang} (Write strictly in this language; if Telugu, use natural Telugu).
    - Target Audience: {audience}
    - Opening Rule: Do NOT say "As an elite strategist". Start with a 1-line intro mentioning "TrendSutra AI", then go straight to Section 1.
    Source Data: {raw_data}
    Structure into 5 sections:
    1. 📊 **Audience Pulse & Sentiment (ప్రేక్షకుల నాడి)**
    2. 🪝 **Viral Hook & Next 3 Video Ideas**
    3. 💰 **Monetization Blueprint (ఆదాయ మార్గాలు)**
    4. 🔍 **SEO, Caption & Hashtag Optimization**
    5. 🚀 **30-Day Growth Action Plan**
    """
    models_list = ["gemini-3.5-flash-lite", "gemini-3.8-flash", "gemini-2.5-flash"]
    for attempt in range(2):
        for key in GEMINI_KEYS:
            client = genai.Client(api_key=key)
            for model_name in models_list:
                try:
                    resp = client.models.generate_content(model=model_name, contents=prompt)
                    if resp and resp.text:
                        return True, resp.text
                except Exception:
                    time.sleep(1.5)
                    continue
    return False, "⚠️ AI సర్వర్ ప్రస్తుతం రద్దీగా ఉంది. దయచేసి 5 సెకన్ల తర్వాత మళ్ళీ క్లిక్ చేయండి."

st.markdown("""
<style>
div.stButton > button:first-child {background-color: #c92a2a; color: white; font-weight: bold; border-radius: 6px; padding: 0.5rem 1.2rem; border: none;}
div.stDownloadButton > button:first-child {background-color: #2b8a3e; color: white; font-weight: bold; border-radius: 6px; padding: 0.5rem 1.2rem; border: none;}
</style>
""", unsafe_allow_html=True)

if "generated_report" not in st.session_state:
    st.session_state.generated_report = ""
if "report_stats" not in st.session_state:
    st.session_state.report_stats = None
if "report_platform" not in st.session_state:
    st.session_state.report_platform = ""

if st.button("Generate Accurate Growth Report 🔍"):
    if not video_url.strip():
        st.warning("⚠️ దయచేసి ముందుగా వీడియో లేదా ప్రొఫైల్ లింక్ పేస్ట్ చేయండి.")
    else:
        data_text = ""
        stats_obj = None
        with st.spinner(f"{platform} నుండి డేటా సేకరిస్తోంది..."):
            if platform == "YouTube":
                data_text, stats_obj = fetch_youtube_info(video_url.strip())
            elif platform == "Instagram Reels":
                data_text = fetch_rapidapi_safe("https://rapidapi.com", "://rapidapi.com", {"reel_post_code_or_url": video_url.strip()}, f"Instagram Reel ({video_url.strip()})")
            elif platform == "TikTok":
                data_text = fetch_rapidapi_safe("https://rapidapi.com", "://rapidapi.com", {"url": video_url.strip()}, f"TikTok Video ({video_url.strip()})")
        if platform == "YouTube" and not data_text:
            st.error(f"⚠️ {stats_obj}")
        else:
            with st.spinner("TrendSutra AI లోతుగా విశ్లేషిస్తోంది..."):
                success, result_text = generate_growth_report(platform, data_text, report_lang, target_audience)
                if success:
                    st.session_state.generated_report = result_text
                    st.session_state.report_stats = stats_obj if platform == "YouTube" else None
                    st.session_state.report_platform = platform
                else:
                    st.session_state.generated_report = ""
                    st.error(result_text)

if st.session_state.generated_report:
    if isinstance(st.session_state.report_stats, dict):
        m1, m2, m3 = st.columns(3)
        m1.metric("👀 Views", f"{int(st.session_state.report_stats.get('viewCount', 0)):,}")
        m2.metric("👍 Likes", f"{int(st.session_state.report_stats.get('likeCount', 0)):,}")
        m3.metric("💬 Comments", f"{int(st.session_state.report_stats.get('commentCount', 0)):,}")
    st.success("✅ Growth Audit Report సిద్ధమైంది!")
    file_content = f"=== TrendSutra AI - {st.session_state.report_platform} Growth Audit Report ===\nPowered by AIENGTEL.com\n\n{st.session_state.generated_report}"
    st.download_button(label="📥 Download Growth Report (.txt)", data=file_content, file_name=f"TrendSutra_AI_{st.session_state.report_platform}_Report.txt", mime="text/plain")
    st.markdown("---")
    st.markdown(st.session_state.generated_report)
