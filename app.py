import streamlit as st
import requests
from google import genai

st.set_page_config(
    page_title="TrendSutra AI | Growth Analyzer",
    page_icon="📈",
    layout="wide",
)

# --- Secrets Loader (Supports list or single key) ---
def get_gemini_keys():
    keys = []
    if "GEMINI_API_KEYS" in st.secrets:
        val = st.secrets["GEMINI_API_KEYS"]
        if isinstance(val, list):
            keys.extend([str(k).strip() for k in val if k and str(k).strip()])
        elif isinstance(val, str):
            keys.extend([k.strip() for k in val.split(",") if k.strip()])
    if "GEMINI_API_KEY" in st.secrets and st.secrets["GEMINI_API_KEY"]:
        single_key = str(st.secrets["GEMINI_API_KEY"]).strip()
        if single_key and single_key not in keys:
            keys.append(single_key)
    return keys

def generate_with_rotation(prompt: str) -> str:
    keys = get_gemini_keys()
    if not keys:
        return "❌ Streamlit Secrets లో Gemini API Key లేదు. దయచేసి యాడ్ చేయండి."

    if "gemini_key_idx" not in st.session_state:
        st.session_state.gemini_key_idx = 0

    models_to_try = ["gemini-3.8-flash", "gemini-2.5-flash"]
    total = len(keys)
    last_error = None

    for attempt in range(total):
        idx = (st.session_state.gemini_key_idx + attempt) % total
        api_key = keys[idx]
        for model_name in models_to_try:
            try:
                client = genai.Client(api_key=api_key)
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                )
                if response and getattr(response, "text", None):
                    st.session_state.gemini_key_idx = (idx + 1) % total
                    return response.text
            except Exception as e:
                last_error = f"[{model_name}] {str(e)}"
                continue

    return f"❌ అన్ని Gemini API Keys విఫలమయ్యాయి. చివరి లోపం: {last_error}"

# --- Platform Data Fetchers ---
def fetch_youtube_stats(channel_or_query: str) -> str:
    yt_key = st.secrets.get("YOUTUBE_API_KEY", "")
    if not yt_key:
        return "YouTube API Key missing in Secrets."
    try:
        search_url = "https://www.googleapis.com/youtube/v3/search"
        params = {
            "part": "snippet",
            "q": channel_or_query,
            "type": "channel",
            "maxResults": 1,
            "key": yt_key,
        }
        r = requests.get(search_url, params=params, timeout=15).json()
        items = r.get("items", [])
        if not items:
            return f"'{channel_or_query}' కోసం YouTube ఛానెల్ దొరకలేదు."

        ch = items[0]
        ch_id = ch["id"]["channelId"]
        title = ch["snippet"]["title"]
        desc = ch["snippet"].get("description", "")

        stats_url = "https://www.googleapis.com/youtube/v3/channels"
        s_params = {"part": "statistics", "id": ch_id, "key": yt_key}
        s_res = requests.get(stats_url, params=s_params, timeout=15).json()
        stats = s_res.get("items", [{}])[0].get("statistics", {})

        return (
            f"Channel: {title} (ID: {ch_id})\n"
            f"Subscribers: {stats.get('subscriberCount', 'Hidden/N/A')}\n"
            f"Total Views: {stats.get('viewCount', 'N/A')}\n"
            f"Total Videos: {stats.get('videoCount', 'N/A')}\n"
            f"Description: {desc[:300]}"
        )
    except Exception as e:
        return f"YouTube fetch error: {e}"

def fetch_rapidapi_info(platform: str, username: str) -> str:
    rapid_key = st.secrets.get("RAPIDAPI_API_KEY", "")
    if not rapid_key:
        return f"{platform} కోసం RapidAPI Key లేదు. యూజర్ ఇచ్చిన హ్యాండిల్ ఆధారంగా విశ్లేషించండి: @{username}"

    clean_user = username.lstrip("@").strip()
    try:
        if platform == "Instagram":
            url = "https://instagram-scraper-stable-api.p.rapidapi.com/ig_get_fb_profile_hover.php"
            headers = {
                "x-rapidapi-key": rapid_key,
                "x-rapidapi-host": "instagram-scraper-stable-api.p.rapidapi.com",
            }
            resp = requests.get(url, headers=headers, params={"username_or_url": clean_user}, timeout=15)
            return f"Instagram Raw Data (@{clean_user}): {resp.text[:1200]}"
        else:
            return f"TikTok Handle: @{clean_user} (AI Growth Analysis Mode)"
    except Exception as e:
        return f"{platform} API error: {e} | Handle: @{clean_user}"

# --- UI Header ---
st.title("📈 TrendSutra AI")
st.caption("YouTube, Instagram & TikTok A to Z Growth Analyzer • 100% Free Access")

with st.sidebar:
    st.header("⚙️ TrendSutra AI Controls")
    platform = st.selectbox("ప్లాట్‌ఫామ్ ఎంచుకోండి", ["YouTube", "Instagram", "TikTok"])
    target_input = st.text_input(
        "ఛానెల్ పేరు / @Username / Niche",
        placeholder="ఉదా: @creator లేదా Tech Telugu",
    )
    goal = st.selectbox(
        "ప్రధాన లక్ష్యం",
        [
            "A to Z Growth Audit",
            "Viral Hook & Content Ideas",
            "Algorithm & Retention Fix",
            "Monetization Roadmap",
        ],
    )
    keys_count = len(get_gemini_keys())
    st.success(f"🔑 Active Gemini Keys: {keys_count} (Auto-Rotation Ready)")

st.markdown("---")

if st.button("🚀 Analyze Now", type="primary"):
    if not target_input.strip():
        st.warning("దయచేసి ఛానెల్ పేరు / @Username లేదా Niche ఎంటర్ చేయండి.")
    else:
        with st.spinner("TrendSutra AI డేటా సేకరించి విశ్లేషిస్తోంది..."):
            if platform == "YouTube":
                raw_data = fetch_youtube_stats(target_input.strip())
            else:
                raw_data = fetch_rapidapi_info(platform, target_input.strip())

            prompt = f"""
You are **TrendSutra AI**, an expert growth strategist for YouTube, Instagram, and TikTok.
Respond clearly in simple, practical Telugu (with key English growth terms where helpful).

Platform: {platform}
Input: {target_input.strip()}
Goal: {goal}

Fetched Data:
{raw_data}

Provide a structured A to Z actionable report:
1. **Current Snapshot & Diagnosis** (ప్రస్తుత స్థితి & లోపాలు)
2. **Algorithm & Reach Boost Strategy** (రీచ్ పెంచే వ్యూహాలు)
3. **7 Ready-to-Shoot Content / Hook Ideas** (వైరల్ అయ్యే 7 ఐడియాలు)
4. **Next 7 Days Action Plan** (వచ్చే 7 రోజుల కార్యాచరణ)
"""
            report = generate_with_rotation(prompt)
            st.markdown("### 📊 TrendSutra AI Growth Report")
            st.markdown(report)
