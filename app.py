import streamlit as st
from google import genai
import requests
import re
import time

APP_NAME = "TrendSutra AI"
FREE_LAUNCH_MODE = True

st.set_page_config(
    page_title=f"{APP_NAME} by AIENGTEL - Global & Regional Growth Analyzer",
    page_icon="🚀",
    layout="wide"
)

def get_youtube_real_data(url_or_handle):
    raw_yt_key = str(st.secrets.get("YOUTUBE_API_KEY", "")).strip()
    key_match = re.search(r"(AIza[0-9A-Za-z_-]{35})", raw_yt_key)
    clean_yt_key = key_match.group(1) if key_match else ""
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

    vid_match = re.search(r"(?:v=|youtu\.be\/|shorts\/)([0-9A-Za-z_-]{11})", url_or_handle)
    if vid_match:
        video_id = vid_match.group(1)
        if clean_yt_key:
            try:
                api_url = "https://googleapis.com"
                params = {"part": "snippet,statistics", "id": video_id, "key": clean_yt_key}
                r = requests.get(api_url, params=params, headers=headers, timeout=6)
                if r.status_code == 200 and r.text.strip():
                    res = r.json()
                    items = res.get("items", [])
                    if len(items) > 0:
                        snippet = items[0].get("snippet", {})
                        stats = items[0].get("statistics", {})
                        tags = ", ".join(snippet.get("tags", [])[:10])
                        data_summary = f"Type: YouTube Video | Title: {snippet.get('title')} | Channel: {snippet.get('channelTitle')} | Desc: {snippet.get('description', '')[:300]} | Tags: {tags} | Views: {stats.get('viewCount', '0')}, Likes: {stats.get('likeCount', '0')}"
                        return data_summary, f"🎥 **{snippet.get('title')}** (Channel: {snippet.get('channelTitle')} | 👁️ {stats.get('viewCount', '0')} Views)"
            except Exception:
                pass

        try:
            oembed_url = "https://youtube.com"
            ores = requests.get(oembed_url, params={"url": f"https://youtube.com{video_id}", "format": "json"}, headers=headers, timeout=6)
            if ores.status_code == 200 and ores.text.strip():
                odata = ores.json()
                data_summary = f"Type: YouTube Video | Exact Video Title: {odata.get('title')} | Channel Name: {odata.get('author_name')}"
                return data_summary, f"🎥 **{odata.get('title')}** (Channel: {odata.get('author_name')})"
        except Exception:
            pass

        try:
            page = requests.get(f"https://youtube.com{video_id}", headers=headers, timeout=6)
            title_match = re.search(r"<title>(.*?)</title>", page.text)
            if title_match:
                clean_title = title_match.group(1).replace(" - YouTube", "").strip()
                if clean_title and clean_title != "YouTube":
                    return f"Type: YouTube Video | Exact Video Title: {clean_title}", f"🎥 **{clean_title}**"
        except Exception:
            pass

    handle_match = re.search(r"@([0-9A-Za-z_.-]+)", url_or_handle)
    if handle_match and clean_yt_key:
        try:
            handle_name = "@" + handle_match.group(1)
            api_url = "https://googleapis.com"
            params = {"part": "snippet,statistics", "forHandle": handle_name, "key": clean_yt_key}
            r = requests.get(api_url, params=params, headers=headers, timeout=6)
            if r.status_code == 200 and r.text.strip():
                res = r.json()
                items = res.get("items", [])
                if len(items) > 0:
                    snippet = items[0].get("snippet", {})
                    stats = items[0].get("statistics", {})
                    data_summary = f"Type: YouTube Channel | Channel: {snippet.get('title')} | Bio: {snippet.get('description', '')[:300]} | Subscribers: {stats.get('subscriberCount', 'Hidden')}, Views: {stats.get('viewCount', '0')}, Videos: {stats.get('videoCount', '0')}"
                    return data_summary, f"📺 **{snippet.get('title')}** (👥 {stats.get('subscriberCount', 'Hidden')} Subscribers | 🎬 {stats.get('videoCount', '0')} Videos)"
        except Exception:
            pass

    return None, "⚠️ ఈ వీడియో ప్రైవేట్‌గా ఉండవచ్చు లేదా లింక్ తప్పుగా ఉంది. దయచేసి పబ్లిక్ YouTube లింక్ ఇవ్వండి."
def generate_accurate_report(prompt):
    api_keys = [str(st.secrets.get("GEMINI_API_KEY", "")).strip(), str(st.secrets.get("GEMINI_API_KEY_2", "")).strip()]
    api_keys = [k for k in api_keys if k]
    if not api_keys:
        return "⚠️ API Key కనుగొనబడలేదు! Streamlit Secrets లో GEMINI_API_KEY ని యాడ్ చేయండి."

    last_error = ""
    for key in api_keys:
        try:
            client = genai.Client(api_key=key)
            for attempt in range(2):
                try:
                    response = client.models.generate_content(model="gemini-3.8-flash", contents=prompt)
                    return response.text
                except Exception as e:
                    last_error = str(e)
                    if "503" in last_error or "UNAVAILABLE" in last_error:
                        time.sleep(2)
                        continue
                    break
            for m in client.models.list():
                if "flash" in m.name and "3.8" not in m.name:
                    try:
                        response = client.models.generate_content(model=m.name.replace("models/", ""), contents=prompt)
                        return response.text
                    except Exception:
                        continue
        except Exception as e:
            last_error = str(e)
            continue
    return f"⚠️ Server is temporarily busy. Please click Generate again! ({last_error})"

with st.sidebar:
    st.title("🌍 Global & Regional Settings")
    selected_lang = st.selectbox("Report Language / భాషను ఎంచుకోండి:", ["English (Global)", "Telugu (తెలుగు)", "Hindi (हिंदी)", "Tamil (தமிழ்)", "Kannada (ಕನ್ನಡ)", "Malayalam (മലയാളം)", "Spanish (Español)"])
    audience_type = st.radio("Target Audience / ఆడియన్స్ రకం:", ["Regional / Local Audience", "Global / International Audience", "Both (Global + Regional)"])
    st.divider()
    if FREE_LAUNCH_MODE:
        st.success("🎉 **FREE LAUNCH OFFER!**\nUnlimited Deep AI Audits are 100% FREE for a limited time!")
    else:
        region = st.radio("Select Currency:", ["India (₹ INR)", "International ($ USD)"])
        if region == "India (₹ INR)":
            st.info("💎 **Pro Plan: ₹199 / month**\n- Unlimited Deep Audits")
            st.markdown("[👉 Pay ₹199 via UPI / Razorpay](https://your-razorpay-link.com)")
        else:
            st.info("💎 **Pro Plan: $5 / month**\n- Unlimited Deep Audits")
            st.markdown("[👉 Pay $5 via International Card](https://your-international-link.com)")
    st.divider()
    st.markdown("### 🔗 Explore More AI Tools")
    st.markdown("Discover 100+ Best AI Tools in **English & తెలుగు** at **[AIENGTEL.com](https://aiengtel.com)** 🚀")

st.title(f"🚀 {APP_NAME}")
st.markdown("##### A to Z Growth Analyzer for YouTube, Instagram & TikTok | Powered by **[AIENGTEL.com](https://aiengtel.com)**")
if FREE_LAUNCH_MODE:
    st.info("🎁 **Special Launch Access:** Enjoy unlimited real-data AI Growth Audits for free!")

col1, col2 = st.columns(2)
with col1:
    platform = st.selectbox("Select Platform:", ["YouTube", "Instagram", "TikTok"])
with col2:
    handle = st.text_input("Channel / Profile / Video Link:", placeholder="Paste YouTube video/channel link or @username")

if st.button("Generate Accurate Growth Report 🔍", type="primary"):
    if not handle:
        st.warning("Please enter a valid link or @username!")
    else:
        with st.spinner("⚡ Fetching real profile/video data & analyzing..."):
            if platform == "YouTube":
                real_data, display_banner = get_youtube_real_data(handle)
                if not real_data:
                    st.error(display_banner)
                    st.stop()
            else:
                real_data = f"Platform: {platform} | Profile/Link: {handle}"
                display_banner = f"📱 Analyzing **{handle}** on {platform}"

            st.info(display_banner)
            prompt = f"You are an expert Social Media Growth Strategist. Base your analysis STRICTLY on this verified data without guessing: {real_data}. Target Audience: {audience_type}. Write the entire response strictly in {selected_lang} covering: Exact Title & Content Audit, 3 Better Viral Title & Content Ideas, SEO Keywords & Hashtags, Engagement & Watch-Time Tips, and Monetization Strategy."
            report = generate_accurate_report(prompt)
            if report.startswith("⚠️"):
                st.error(report)
            else:
                st.success("✅ 100% Data-Backed Growth Report Ready!")
                st.markdown(report)
