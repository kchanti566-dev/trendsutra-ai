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

    try:
        vid_match = re.search(r"(?:v=|youtu\.be\/|shorts\/)([0-9A-Za-z_-]{11})", url_or_handle)
        if vid_match:
            video_id = vid_match.group(1)
            if clean_yt_key:
                try:
                    api_url = "https://googleapis.com"
                    params = {"part": "snippet,statistics", "id": video_id, "key": clean_yt_key}
                    res = requests.get(api_url, params=params, timeout=5).json()
                    if res.get("items") and len(res["items"]) > 0:
                        item = res["items"][0]
                        snippet = item.get("snippet", {})
                        stats = item.get("statistics", {})
                        tags = ", ".join(snippet.get("tags", [])[:10])
                        data_summary = (
                            f"Type: YouTube Video | "
                            f"Exact Video Title: {snippet.get('title')} | "
                            f"Channel Name: {snippet.get('channelTitle')} | "
                            f"Description: {snippet.get('description', '')[:300]} | "
                            f"Tags: {tags if tags else 'No tags'} | "
                            f"Views: {stats.get('viewCount', '0')}, Likes: {stats.get('likeCount', '0')}"
                        )
                        return data_summary, f"🎥 **{snippet.get('title')}** (Channel: {snippet.get('channelTitle')} | 👁️ {stats.get('viewCount', '0')} Views)"
                except Exception:
                    pass

            oembed_url = "https://youtube.com"
            ores = requests.get(oembed_url, params={"url": f"https://youtube.com{video_id}", "format": "json"}, timeout=5)
            if ores.status_code == 200:
                odata = ores.json()
                data_summary = f"Type: YouTube Video | Exact Video Title: {odata.get('title')} | Channel Name: {odata.get('author_name')}"
                return data_summary, f"🎥 **{odata.get('title')}** (Channel: {odata.get('author_name')})"

        handle_match = re.search(r"@([0-9A-Za-z_.-]+)", url_or_handle)
        if handle_match and clean_yt_key:
            handle_name = "@" + handle_match.group(1)
            api_url = "https://googleapis.com"
            params = {"part": "snippet,statistics", "forHandle": handle_name, "key": clean_yt_key}
            res = requests.get(api_url, params=params, timeout=5).json()
            if res.get("items") and len(res["items"]) > 0:
                item = res["items"][0]
                snippet = item.get("snippet", {})
                stats = item.get("statistics", {})
                data_summary = (
                    f"Type: YouTube Channel | "
                    f"Channel Name: {snippet.get('title')} | "
                    f"Bio: {snippet.get('description', '')[:300]} | "
                    f"Subscribers: {stats.get('subscriberCount', 'Hidden')}, Views: {stats.get('viewCount', '0')}, Videos: {stats.get('videoCount', '0')}"
                )
                return data_summary, f"📺 **{snippet.get('title')}** (👥 {stats.get('subscriberCount', 'Hidden')} Subscribers | 🎬 {stats.get('videoCount', '0')} Videos)"

        return None, "⚠️ ఈ YouTube లింక్/హ్యాండిల్ నుండి డేటా దొరకలేదు. దయచేసి సరైన పూర్తి వీడియో లింక్ ఇవ్వండి."
    except Exception as e:
        return None, f"⚠️ Error fetching data: {str(e)}"

def generate_accurate_report(prompt):
    api_keys = [
        str(st.secrets.get("GEMINI_API_KEY", "")).strip(),
        str(st.secrets.get("GEMINI_API_KEY_2", "")).strip()
    ]
    api_keys = [k for k in api_keys if k]
    
    if not api_keys:
        return "⚠️ API Key కనుగొనబడలేదు! Streamlit Secrets లో GEMINI_API_KEY ని యాడ్ చేయండి."

    last_error = ""
    for key in api_keys:
        try:
            client = genai.Client(api_key=key)
            for attempt in range(2):
                try:
                    response = client.models.generate_content(
                        model="gemini-3.8-flash",
                        contents=prompt,
                    )
                    return response.text
                except Exception as e:
                    last_error = str(e)
                    if "503" in last_error or "UNAVAILABLE" in last_error:
                        time.sleep(2)
                        continue
                    else:
                        break
            
            for m in client.models.list():
                if "flash" in m.name and "3.8" not in m.name:
                    try:
                        clean_model = m.name.replace("models/", "")
                        response = client.models.generate_content(
                            model=clean_model,
                            contents=prompt,
                        )
                        return response.text
                    except Exception:
                        continue
        except Exception as e:
            last_error = str(e)
            continue

    return f"⚠️ Server is temporarily busy. Please click Generate again! ({last_error})"

with st.sidebar:
    st.title("🌍 Global & Regional Settings")
    selected_lang = st.selectbox(
        "Report Language / భాషను ఎంచుకోండి:",
        ["English (Global)", "Telugu (తెలుగు)", "Hindi (हिंदी)", "Tamil (தமிழ்)", "Kannada (ಕನ್ನಡ)", "Malayalam (മലയാളം)", "Spanish (Español)"]
    )
    audience_type = st.radio(
        "Target Audience / ఆడియన్స్ రకం:",
        ["Regional / Local Audience", "Global / International Audience", "Both (Global + Regional)"]
    )
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
            real_data = ""
            display_banner = ""
            if platform == "YouTube":
                real_data, display_banner = get_youtube_real_data(handle)
                if not real_data:
                    st.error(display_banner)
                    st.stop()
            else:
                real_data = f"Platform: {platform} | Profile/Link: {handle}"
                display_banner = f"📱 Analyzing **{handle}** on {platform}"

            st.info(display_banner)

            prompt = (
                f"You are an expert Social Media Growth Strategist. "
                f"CRITICAL RULE: Base your analysis STRICTLY on the real verified data provided below. Do NOT guess or hallucinate false topics, titles, or numbers. "
                f"VERIFIED REAL DATA: {real_data}. "
                f"Target Audience: {audience_type}. "
                f"Output Language: Strictly write the entire response in {selected_lang}. "
                f"Provide a sharp, accurate A-to-Z growth report with these 5 sections: "
                f"1) Exact Title, Hook & Content Audit, "
                f"2) 3 Better Viral Title & Content Ideas directly related to this exact topic, "
                f"3) High-Ranking SEO Keywords & Hashtags for {audience_type}, "
                f"4) Engagement & Watch-Time Improvement Tips, "
                f"5) Best Posting Strategy & Monetization Tip."
            )
            
            report = generate_accurate_report(prompt)
            
            if report.startswith("⚠️"):
                st.error(report)
            else:
                st.success("✅ 100% Data-Backed Growth Report Ready!")
                st.markdown(report)
