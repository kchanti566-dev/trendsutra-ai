import streamlit as st
import streamlit.components.v1 as components
import requests
import google.generativeai as genai

# --- STEP 1: PAGE CONFIG & SIDEBAR API KEYS ---
st.set_page_config(page_title="TrendSutra AI", page_icon="🔥", layout="wide")

with st.sidebar:
    st.header("⚙️ TrendSutra Settings")
    gemini_key = st.text_input("Gemini API Key (Required for AI)", type="password")
    yt_key = st.text_input("YouTube Data API Key (Optional)", type="password")
    rapid_key = st.text_input("RapidAPI Key - IG/TikTok (Optional)", type="password")
    st.divider()
    st.info("💡 API keys lekapoyina demo/fallback trends tho app test cheyavachu.")

# --- STEP 2: PAYMENT VERIFICATION & LOCALSTORAGE LOCK ---
def verify_payment_id(pay_id):
    valid_prefixes = ("pay_", "TREND-", "PRO2026")
    return bool(pay_id and pay_id.strip().startswith(valid_prefixes) and len(pay_id.strip()) >= 8)

if "unlocked" not in st.session_state:
    st.session_state.unlocked = False

# Browser localStorage check & sync
components.html(
    """
    <script>
    const saved = localStorage.getItem('trendsutra_pro');
    if (saved === 'true' && !window.location.search.includes('pro=1')) {
        window.parent.history.replaceState(null, '', '?pro=1');
    }
    </script>
    """,
    height=0,
)

if st.query_params.get("pro") == "1":
    st.session_state.unlocked = True

if not st.session_state.unlocked:
    st.warning("🔒 **Pro Access Locked**: Continue cheyadaniki mee Payment ID enter cheyandi (Demo: `TREND-2026`).")
    col_p1, col_p2 = st.columns([3, 1])
    with col_p1:
        pay_input = st.text_input("Payment / License ID", placeholder="pay_xxxxxxxx or TREND-2026", label_visibility="collapsed")
    with col_p2:
        if st.button("Unlock Now", use_container_width=True):
            if verify_payment_id(pay_input):
                st.session_state.unlocked = True
                st.query_params["pro"] = "1"
                components.html("<script>localStorage.setItem('trendsutra_pro', 'true');</script>", height=0)
                st.rerun()
            else:
                st.error("Invalid Payment ID!")
    st.stop()

# --- PART 3A: MAIN HEADER & DATA FETCH FUNCTIONS ---
st.title("🔥 TrendSutra AI — Viral Content & Trend Engine")
st.caption("YouTube, Instagram & TikTok real-time viral topic analyzer")

@st.cache_data(ttl=1800)
def fetch_youtube_trends(niche, api_key):
    if not api_key:
        return [f"How to master {niche} in 2026", f"{niche} mistakes beginners make", f"Top 5 {niche} tools"]
    url = f"https://googleapis.com{niche}&type=video&order=viewCount&maxResults=5&key={api_key}"
    res = requests.get(url, timeout=10).json()
    return [item["snippet"]["title"] for item in res.get("items", [])]

@st.cache_data(ttl=1800)
def fetch_instagram_trends(niche, rapid_key):
    if not rapid_key:
        return [f"#{niche.replace(' ', '')}Tips", f"#{niche.replace(' ', '')}Reels", "#ViralGrowth2026"]
    headers = {"X-RapidAPI-Key": rapid_key, "X-RapidAPI-Host": "://rapidapi.com"}
    res = requests.get("https://://rapidapi.com/v1/hashtag", headers=headers, params={"hashtag": niche.replace(" ", "")}, timeout=10).json()
    items = res.get("data", {}).get("items", [])[:5]
    return [i.get("caption", {}).get("text", "")[:70] for i in items if i.get("caption")]

@st.cache_data(ttl=1800)
def fetch_tiktok_trends(niche, rapid_key):
    if not rapid_key:
        return [f"{niche} hook challenge", f"POV: learning {niche}", f"{niche} aesthetic routine"]
    headers = {"X-RapidAPI-Key": rapid_key, "X-RapidAPI-Host": "://rapidapi.com"}
    res = requests.get("https://://rapidapi.com/feed/search", headers=headers, params={"keywords": niche, "count": 5}, timeout=10).json()
    videos = res.get("data", {}).get("videos", [])
    return [v.get("title", "")[:70] for v in videos if v.get("title")]

def fetch_all_platform_trends(niche, yt_key="", rapid_key=""):
    return {
        "YouTube": fetch_youtube_trends(niche, yt_key),
        "Instagram": fetch_instagram_trends(niche, rapid_key),
        "TikTok": fetch_tiktok_trends(niche, rapid_key)
    }

# --- PART 3B: AI VIRAL SCRIPT GENERATOR & UI ---
def generate_viral_scripts(niche, trends, language, api_key):
    if not api_key:
        return (
            f"### 🎬 Sample Viral Hook ({language})\n"
            f"**Hook:** Stop scrolling! {niche} lo 99% mandi ee okka tappu chestunnaru...\n\n"
            f"**Body:** Ee trends chudandi: {', '.join(trends['YouTube'][:2])}.\n\n"
            f"**CTA:** Full guide kosam Follow kottandi!"
        )
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.5-flash")
    prompt = (
        f"You are a viral social media strategist. Niche: '{niche}'. Output Language: {language}.\n"
        f"Current trending topics across platforms: {trends}\n"
        "Generate: 1) 3 scroll-stopping viral hooks, 2) One 45-second Reel/Short script (Hook, Value, CTA), "
        "and 3) 5 high-reach hashtags."
    )
    return model.generate_content(prompt).text

col1, col2 = st.columns([2, 1])
with col1:
    niche = st.text_input("🎯 Mee Niche / Topic Enter Cheyandi", placeholder="e.g., AI Tools, Fitness, Personal Finance, Telugu Tech")
with col2:
    lang = st.selectbox("🗣️ Script Language", ["Telugu + English (Tenglish)", "English", "Telugu", "Hindi"])

if st.button("🚀 Analyze Trends & Generate Viral Script", type="primary", use_container_width=True):
    if not niche.strip():
        st.error("Dayachesi mundu oka niche enter cheyandi!")
    else:
        with st.spinner("Platforms nundi trends fetch chestunnam..."):
            trends_data = fetch_all_platform_trends(niche.strip(), yt_key, rapid_key)
        
        c1, c2, c3 = st.columns(3)
        with c1:
            st.subheader("📺 YouTube Trends")
            for t in trends_data["YouTube"]:
                st.markdown(f"- {t}")
        with c2:
            st.subheader("📸 Instagram Trends")
            for t in trends_data["Instagram"]:
                st.markdown(f"- {t}")
        with c3:
            st.subheader("🎵 TikTok Trends")
            for t in trends_data["TikTok"]:
                st.markdown(f"- {t}")

        st.divider()
        st.subheader("✨ AI Generated Viral Content Blueprint")
        with st.spinner("Viral hooks & script ready avutunnayi..."):
            script_output = generate_viral_scripts(niche.strip(), trends_data, lang, gemini_key)
            st.markdown(script_output)
