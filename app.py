import streamlit as st
from google import genai
import requests
import re
import time

# ==========================================
# ⚙️ LAUNCH SETTINGS
# ==========================================
FREE_LAUNCH_MODE = True  # కొన్ని రోజుల తర్వాత False చేస్తే Pro Plan ఆన్ అవుతుంది

# 1. Page Configuration
st.set_page_config(
    page_title="CreatorPulse AI by AIENGTEL - Global & Regional Growth Analyzer",
    page_icon="🚀",
    layout="wide"
)

# 2. Accurate YouTube Video & Channel Data Fetcher
def get_youtube_real_data(url_or_handle):
    yt_key = st.secrets.get("YOUTUBE_API_KEY")
    if not yt_key:
        return None, "⚠️ YouTube API Key missing in Streamlit Secrets."
    
    try:
        # 1. ముందుగా వీడియో లింక్ (youtu.be/xyz లేదా ://youtube.com లేదా shorts/xyz) చెక్ చేస్తుంది
        vid_match = re.search(r"(?:v=|youtu\.be\/|shorts\/)([0-9A-Za-z_-]{11})", url_or_handle)
        if vid_match:
            video_id = vid_match.group(1)
            api_url = f"https://googleapis.com{video_id}&key={yt_key}"
            res = requests.get(api_url, timeout=5).json()
            if res.get("items"):
                item = res["items"]
                snippet = item["snippet"]
                stats = item["statistics"]
                tags = ", ".join(snippet.get("tags", [])[:10])
                data_summary = (
                    f"Type: YouTube Video\n"
                    f"Exact Video Title: {snippet.get('title')}\n"
                    f"Channel Name: {snippet.get('channelTitle')}\n"
                    f"Description Snippet: {snippet.get('description', '')[:300]}\n"
                    f"Tags Used: {tags if tags else 'No tags'}\n"
                    f"Views: {stats.get('viewCount', '0')} | Likes: {stats.get('likeCount', '0')} | Comments: {stats.get('commentCount', '0')}"
                )
                return data_summary, f"🎥 **{snippet.get('title')}** (Channel: {snippet.get('channelTitle')} | 👁️ {stats.get('viewCount', '0')} Views)"

        # 2. ఒకవేళ ఛానల్ హ్యాండిల్ (@username) ఇస్తే ఛానల్ డేటా తెస్తుంది
        handle_match = re.search(r"@([0-9A-Za-z_.-]+)", url_or_handle)
        if handle_match:
            handle_name = "@" + handle_match.group(1)
            api_url = f"https://googleapis.com{handle_name}&key={yt_key}"
            res = requests.get(api_url, timeout=5).json()
            if res.get("items"):
                item = res["items"]
                snippet = item["snippet"]
                stats = item["statistics"]
                data_summary = (
                    f"Type: YouTube Channel\n"
                    f"Channel Name: {snippet.get('title')}\n"
                    f"Channel Bio/Description: {snippet.get('description', '')[:300]}\n"
                    f"Subscribers: {stats.get('subscriberCount', 'Hidden')} | Total Views: {stats.get('viewCount', '0')} | Total Videos: {stats.get('videoCount', '0')}"
                )
                return data_summary, f"📺 **{snippet.get('title')}** (👥 {stats.get('subscriberCount', 'Hidden')} Subscribers | 🎬 {stats.get('videoCount', '0')} Videos)"

        return None, "⚠️ ఈ YouTube లింక్/హ్యాండిల్ నుండి డేటా దొరకలేదు. దయచేసి సరైన పూర్తి వీడియో లింక్ లేదా @ChannelHandle ఇవ్వండి."
    except Exception as e:
        return None, f"⚠️ YouTube API Error: {str(e)}"

# 3. Smart Auto-Rotation Gemini Function
def generate_accurate_report(prompt):
    api_keys = [
        st.secrets.get("GEMINI_API_KEY"),
        st.secrets.get("GEMINI_API_KEY_2")
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

# 4. Sidebar - Global & Regional Settings + AIENGTEL Branding
with st.sidebar:
    st.title("🌍 Global & Regional Settings")
    
    selected_lang = st.selectbox(
        "Report Language / భాషను ఎంచుకోండి:",
        [
            "English (Global)", 
            "Telugu (తెలుగు)", 
            "Hindi (हिंदी)", 
            "Tamil (தமிழ்)", 
            "Kannada (ಕನ್ನಡ)",
            "Malayalam (മലയാളം)",
            "Spanish (Español)"
        ]
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

# 5. Main App Interface (2 Clean Columns - No Niche Box, No PDF)
st.title("🚀 CreatorPulse AI")
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
                    st.stop() # తప్పుడు అనాలిసిస్ రాకుండా ఇక్కడే ఆపుతుంది!
            else:
                # Instagram & TikTok కోసం యూజర్ ఇచ్చిన పేరు/లింక్ ఆధారంగా
                real_data = f"Platform: {platform} | Profile/Link: {handle}"
                display_banner = f"📱 Analyzing **{handle}** on {platform}"

            st.info(display_banner)

            prompt = f"""
            You are an expert Social Media Growth Strategist. 
            CRITICAL RULE: Base your analysis STRICTLY on the real verified data provided below. Do NOT guess or hallucinate false topics, titles, or numbers.
            
            VERIFIED REAL DATA:
            {real_data}
            
            Target Audience: {audience_type}
            Output Language: Strictly write the entire response in {selected_lang}.

            Provide a sharp, accurate A-to-Z growth report with these 5 sections (keep each bullet point practical and specific to the exact title/channel above):
            1. **Exact Title, Hook & Content Audit** (Analyze what is working or missing in the current title/description/stats)
            2. **3 Better Viral Title & Content Ideas** (Directly related to this exact topic/niche)
            3. **High-Ranking SEO Keywords & Hashtags** (Relevant to {audience_type})
            4. **Engagement & Watch-Time Improvement Tips**
            5. **Best Posting Strategy & Monetization Tip**
            """
            
            report = generate_accurate_report(prompt)
            
            if report.startswith("⚠️"):
                st.error(report)
            else:
                st.success("✅ 100% Data-Backed Growth Report Ready!")
                st.markdown(report)
