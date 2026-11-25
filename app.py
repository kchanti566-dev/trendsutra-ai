import os
import re
import time
import hashlib
import requests
import streamlit as st
from google import genai
from google.genai import types
from googleapiclient.discovery import build
from streamlit_js_eval import streamlit_js_eval

st.set_page_config(
    page_title="TrendSutra AI - Growth Analyzer",
    page_icon="logo.png" if os.path.isfile("logo.png") else "🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """<style>
    #MainMenu, footer, .stDeployButton, div[data-testid="stToolbarActions"], div[data-testid="stStatusWidget"], div[data-testid="stDecoration"], .viewerBadge_container__1QSob, .viewerBadge_link__1S137 {
        display: none !important;
        visibility: hidden !important;
    }
    header[data-testid="stHeader"] {
        height: 1.2rem !important;
        background: transparent !important;
    }
    .block-container {
        padding-top: 0rem !important;
        margin-top: -2.2rem !important;
    }
    section[data-testid="stSidebar"] > div:first-child {
        padding-top: 0.4rem !important;
        margin-top: -1.2rem !important;
    }
    section[data-testid="stSidebar"] .stMarkdown p {
        margin-bottom: 0.25rem !important;
        font-size: 0.92rem !important;
    }
    section[data-testid="stSidebar"] h3 {
        margin-top: 0.35rem !important;
        margin-bottom: 0.25rem !important;
        font-size: 1.05rem !important;
    }
    section[data-testid="stSidebar"] div[data-testid="stVerticalBlock"] {
        gap: 0.45rem !important;
    }
    div.stButton > button:first-child {
        background-color: #c92a2a;
        color: white;
        font-weight: bold;
        border-radius: 6px;
        border: none;
        width: 100%;
    }
    div.stDownloadButton > button:first-child {
        background-color: #2b8a3e;
        color: white;
        font-weight: bold;
        border-radius: 6px;
        border: none;
    }
    </style>""",
    unsafe_allow_html=True,
)

GEMINI_KEYS = [
    k.strip()
    for k in (
        st.secrets.get("GEMINI_API_KEY", ""),
        st.secrets.get("GEMINI_API_KEY_2", ""),
    )
    if k and str(k).strip()
]
YOUTUBE_KEY = str(st.secrets.get("YOUTUBE_API_KEY", "")).strip()
RAPIDAPI_KEY = str(st.secrets.get("RAPIDAPI_API_KEY", "")).strip()

GOOGLE_SHEET_API = "https://script.google.com/macros/s/AKfycbzEkkgxBP7aOKIXkEiOG7_rWc0quvnvTVqQDSWUAMk2zOPN7W8Ue_uOPwH7edmJJtEd/exec"
PAY_1_MONTH_LINK = "https://rzp.io/rzp/yop8jYS"
PAY_12_MONTHS_LINK = "https://rzp.io/rzp/sjonGmqw"

@st.cache_data(ttl=3600, show_spinner=False)
def get_public_ip():
    try:
        r = requests.get("https://api.ipify.org", timeout=3)
        if r.status_code == 200 and r.text.strip():
            return r.text.strip()
    except Exception:
        pass
    try:
        headers = st.context.headers
        xff = headers.get("X-Forwarded-For", "") or headers.get("X-Real-Ip", "")
        if xff:
            return xff.split(",")[0].strip()
    except Exception:
        pass
    return "unknown_ip"

def get_device_signature():
    ip_val = get_public_ip()
    ua_val = ""
    try:
        ua_val = st.context.headers.get("User-Agent", "")
    except Exception:
        pass
    raw = f"{ip_val}|{ua_val[:80]}"
    return "dev_" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:20]

DEVICE_ID = get_device_signature()

@st.cache_data(ttl=120, show_spinner=False)
def fetch_sheet_device_count(dev_id):
    try:
        res = requests.get(
            f"{GOOGLE_SHEET_API}?device={dev_id}",
            headers={"User-Agent": "Mozilla/5.0"},
            allow_redirects=True,
            timeout=6,
        )
        txt = res.text.strip()
        if txt.isdigit():
            return int(txt)
    except Exception:
        pass
    return 0

def increment_sheet_device_count(dev_id):
    fetch_sheet_device_count.clear()
    try:
        res = requests.get(
            f"{GOOGLE_SHEET_API}?device={dev_id}&inc=1",
            headers={"User-Agent": "Mozilla/5.0"},
            allow_redirects=True,
            timeout=6,
        )
        txt = res.text.strip()
        if txt.isdigit():
            return int(txt)
    except Exception:
        pass
    return None

def log_usage_to_sheet(dev_id, platform_name, target_url):
    try:
        requests.get(
            GOOGLE_SHEET_API,
            params={
                "log": "1",
                "device": dev_id,
                "platform": platform_name,
                "url": target_url[:250],
            },
            headers={"User-Agent": "Mozilla/5.0"},
            allow_redirects=True,
            timeout=5,
        )
    except Exception:
        pass

ls_free = streamlit_js_eval(
    js_expressions="localStorage.getItem('ts_device_free_v8')", key="ls_get_free"
)
ls_pro = streamlit_js_eval(
    js_expressions="localStorage.getItem('ts_device_pro_v8')", key="ls_get_pro"
)

if "free_used_count" not in st.session_state:
    st.session_state.free_used_count = fetch_sheet_device_count(DEVICE_ID)
if "is_pro_user" not in st.session_state:
    st.session_state.is_pro_user = False

sheet_cnt = fetch_sheet_device_count(DEVICE_ID)
if sheet_cnt > st.session_state.free_used_count:
    st.session_state.free_used_count = sheet_cnt

if ls_free and str(ls_free).isdigit() and int(ls_free) > st.session_state.free_used_count:
    st.session_state.free_used_count = int(ls_free)
    st.rerun()

if ls_pro == "yes" and not st.session_state.is_pro_user:
    st.session_state.is_pro_user = True
    st.rerun()

def verify_payment_id(pid):
    if not pid:
        return "INVALID"
    clean_pid = pid.strip()
    owner_key = str(st.secrets.get("OWNER_SECRET_CODE", "")).strip()
    if owner_key and clean_pid == owner_key:
        return "OWNER_VALID"
    if not clean_pid.startswith("pay_"):
        return "INVALID"
    try:
        res = requests.get(
            f"{GOOGLE_SHEET_API}?pid={clean_pid}",
            headers={"User-Agent": "Mozilla/5.0"},
            allow_redirects=True,
            timeout=10,
        )
        txt = res.text.strip()
        if "ALREADY_USED" in txt:
            return "ALREADY_USED"
        if "VALID" in txt:
            return "VALID"
        return "INVALID"
    except Exception:
        return "ERROR"

url_pid = st.query_params.get("razorpay_payment_id", "")
if url_pid and not st.session_state.is_pro_user:
    st_val = verify_payment_id(url_pid)
    if st_val == "VALID":
        st.session_state.is_pro_user = True
        streamlit_js_eval(
            js_expressions="localStorage.setItem('ts_device_pro_v8', 'yes')",
            key="ls_pro_url",
        )
    elif st_val == "ALREADY_USED":
        st.sidebar.error("⚠️ ఈ Payment ID గరిష్టంగా 3 డివైజ్‌లలో వాడబడింది!")

with st.sidebar:
    st.markdown("### 🌍 Settings")
    report_lang = st.selectbox(
        "Report Language / భాష:",
        ("English (Global)", "Telugu (తెలుగు)", "Tenglish"),
    )
    target_audience = st.radio(
        "Target Audience:",
        ("Regional", "Global", "Both"),
        horizontal=True,
    )
    st.markdown("### 💎 Pro Plans (Unlimited)")
    if st.session_state.is_pro_user:
        st.success("✅ **PRO UNLIMITED ACTIVE!**\n\nఅన్‌లిమిటెడ్ రిపోర్ట్‌లు పొందవచ్చు.")
    else:
        rem = max(0, 3 - st.session_state.free_used_count)
        if rem > 0:
            st.caption(f"🎁 **Free Trial:** మీకు **{rem} ఉచిత రిపోర్ట్‌లు** మిగిలి ఉన్నాయి.")
        else:
            st.caption("🔒 **Free Trial: 0 ఉచిత రిపోర్ట్‌లు మిగిలి ఉన్నాయి.**")
        st.markdown(
            f"• **1 Month:** **₹100/-** 👉 [Pay ₹100]({PAY_1_MONTH_LINK})  \n"
            f"• **12 Months:** **₹1,000/-** 👉 [Pay ₹1,000]({PAY_12_MONTHS_LINK})"
        )
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        manual_pid = st.text_input(
            "🔑 Payment ID:",
            placeholder="pay_P9x82kLm01",
            label_visibility="collapsed",
        )
        if st.button("Unlock with Payment ID 🔓"):
            res_st = verify_payment_id(manual_pid)
            if res_st == "OWNER_VALID":
                st.session_state.is_pro_user = True
                st.rerun()
            elif res_st == "VALID":
                st.session_state.is_pro_user = True
                streamlit_js_eval(
                    js_expressions="localStorage.setItem('ts_device_pro_v8', 'yes')",
                    key=f"ls_pro_{int(time.time())}",
                )
                time.sleep(0.4)
                st.rerun()
            elif res_st == "ALREADY_USED":
                st.error("❌ ఈ Payment ID గరిష్టంగా 3 డివైజ్‌లలో వాడబడింది! admin@aiengtel.com కి మెసేజ్ చేయండి.")
            else:
                st.error("❌ సరైన Payment ID ఇవ్వండి.")

if os.path.isfile("logo.png"):
    c1, c2 = st.columns((1, 5))
    with c1:
        st.image("logo.png", width=95)
    with c2:
        st.markdown("# TrendSutra AI")
        st.markdown(
            "**A to Z Growth Analyzer for YouTube, Instagram & TikTok | Powered by [AIENGTEL.com](https://aiengtel.com)**"
        )
else:
    st.markdown(
        "# 🚀 TrendSutra AI\n**A to Z Growth Analyzer for YouTube, Instagram & TikTok | Powered by [AIENGTEL.com](https://aiengtel.com)**"
    )

col1, col2 = st.columns(2)
with col1:
    platform = st.selectbox("Select Platform:", ("YouTube", "Instagram Reels", "TikTok"))
with col2:
    video_url = st.text_input(
        "Channel / Profile / Video Link:",
        placeholder="https://youtu.be/... లేదా Reel / TikTok లింక్ పేస్ట్ చేయండి",
    )

@st.cache_data(ttl=600, show_spinner=False)
def fetch_youtube_info(url):
    m = re.search(r"(?:v=|\/|live\/|shorts\/)([0-9A-Za-z_-]{11}).*", url)
    if not m:
        return None, "సరైన YouTube వీడియో లింక్ ఇవ్వండి."
    try:
        yt = build("youtube", "v3", developerKey=YOUTUBE_KEY)
        vr = yt.videos().list(part="snippet,statistics", id=m.group(1)).execute()
        items = vr.get("items", [])
        if not items:
            return None, "వీడియో వివరాలు దొరకలేదు."
        sn, st_obj = items[0]["snippet"], items[0]["statistics"]
        views = int(st_obj.get("viewCount", 0) or 0)
        likes = int(st_obj.get("likeCount", 0) or 0)
        comments_cnt = int(st_obj.get("commentCount", 0) or 0)
        like_rate = round((likes / views * 100), 2) if views > 0 else 0.0
        comm_rate = round((comments_cnt / views * 100), 2) if views > 0 else 0.0

        coms = []
        try:
            cr = (
                yt.commentThreads()
                .list(
                    part="snippet",
                    videoId=m.group(1),
                    maxResults=40,
                    order="relevance",
                    textFormat="plainText",
                )
                .execute()
            )
            coms = [
                c["snippet"]["topLevelComment"]["snippet"]["textDisplay"]
                for c in cr.get("items", [])
            ]
        except Exception:
            coms = ["కామెంట్లు ఆఫ్ చేసి ఉన్నాయి."]

        rich_data = (
            f"Video Title: {sn.get('title')}\n"
            f"Channel Title: {sn.get('channelTitle')}\n"
            f"Published At: {sn.get('publishedAt')}\n"
            f"Views: {views:,} | Likes: {likes:,} (Like-to-View Rate: {like_rate}%) | Comments: {comments_cnt:,} (Comment-to-View Rate: {comm_rate}%)\n"
            f"Description Snippet: {sn.get('description', '')[:800]}\n"
            f"Current Tags: {sn.get('tags', [])}\n"
            f"Top Audience Comments ({len(coms)}): {coms}"
        )
        return rich_data, st_obj
    except Exception as e:
        return None, f"YouTube Error: {str(e)}"

@st.cache_resource(show_spinner=False)
def get_client(api_key):
    return genai.Client(api_key=api_key)

@st.cache_data(ttl=3600, show_spinner=False)
def get_best_models(api_key):
    fallback = ["gemini-3.5-flash-lite", "gemini-3.5-flash", "gemini-2.5-flash-lite"]
    try:
        client = get_client(api_key)
        all_names = [m.name.replace("models/", "") for m in client.models.list()]
        lite = [
            n for n in all_names
            if "flash-lite" in n and "2.0" not in n and "1.5" not in n and "tts" not in n and "image" not in n
        ]
        flash = [
            n for n in all_names
            if "flash" in n and "lite" not in n and "2.5-flash" != n and "2.0" not in n and "1.5" not in n and "tts" not in n and "image" not in n and "audio" not in n
        ]
        picked = lite + flash
        return picked if picked else fallback
    except Exception:
        return fallback

def build_prompt(platform_name, raw_data, lang, audience):
    return (
        f"You are an experienced, warm, human {platform_name} Growth Mentor & Content Strategist at TrendSutra AI. "
        f"Speak directly to the creator like a real human advisor—encouraging, brutally honest, practical, and deeply insightful (never robotic). "
        f"Write a COMPLETE, UNABRIDGED, detailed A-to-Z Growth Audit Report in {lang} tailored for a {audience} audience. "
        f"CRITICAL RULE: You MUST write ALL 6 SECTIONS completely from start to finish without stopping early or truncating! "
        f"If writing in Telugu or Tenglish, ALWAYS write exact Telugu spelling 'పని 1, పని 2, పని 3' for action steps.\n\n"
        f"Include ALL 6 sections with rich, specific details based on the actual data below:\n"
        f"1. 📊 **Performance & Engagement Diagnosis**: Analyze actual Views, Likes, Like-to-View %, and Comment-to-View % against industry benchmarks and explain exactly why the algorithm is or isn't pushing this content.\n"
        f"2. 💬 **Real Audience Psychology & Comment Insights**: Decode what viewers truly loved, complained about, or requested in the comments, plus 2 ready-to-copy pinned comment / reply templates to spark more engagement.\n"
        f"3. 🔥 **3 Fresh Viral Follow-Up Video Ideas**: Give 3 specific sequel/follow-up concepts with exact **First 5-Second Hook**, **Thumbnail Visual Concept**, and **Why It Will Go Viral**.\n"
        f"4. 🎯 **Copy-Paste SEO Makeover**: Provide 3 high-CTR replacement Titles, a high-retention opening Description block, and 15 searchable Tags/Hashtags.\n"
        f"5. 💰 **Monetization & Brand Earning Blueprint**: Explain 3 realistic ways this exact channel/page can earn money right now (AdSense optimization, Affiliate products, Local/National Brand sponsorships).\n"
        f"6. 📅 **Step-by-Step 30-Day Action Plan**: Break down concrete tasks for Week 1, Week 2, Week 3, and Week 4 using 'పని 1, పని 2, పని 3' format so the creator knows what to do tomorrow morning.\n\n"
        f"Creator & Video Data:\n{raw_data}"
    )

def stream_growth_report(platform_name, raw_data, lang, audience, placeholder):
    prompt = build_prompt(platform_name, raw_data, lang, audience)
    last_err = "API Key missing in Secrets"
    config = types.GenerateContentConfig(
        temperature=0.85,
        max_output_tokens=8192,
    )
    for key in GEMINI_KEYS:
        client = get_client(key)
        models_to_try = get_best_models(key)
        for m in models_to_try:
            try:
                full_text = ""
                for chunk in client.models.generate_content_stream(
                    model=m, contents=prompt, config=config
                ):
                    if chunk.text:
                        full_text += chunk.text
                        placeholder.markdown(full_text + " ▌")
                if full_text.strip():
                    placeholder.markdown(full_text)
                    return True, full_text
            except Exception as e:
                err_str = str(e)
                last_err = err_str
                if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                    last_err = "ఈరోజు ఉచిత API కీ పరిమితి (Daily Quota) ముగిసింది. దయచేసి కొద్దిసేపటి తర్వాత ప్రయత్నించండి లేదా Google AI Studio లో Billing ఆన్ చేయండి."
                    break
                continue
    return False, f"⚠️ AI సర్వర్ తాత్కాలికంగా బిజీగా ఉంది: {last_err[:150]}"

if "generated_report" not in st.session_state:
    st.session_state.generated_report = ""
if "report_stats" not in st.session_state:
    st.session_state.report_stats = None

if st.button("Generate Accurate Growth Report 🔍"):
    if not st.session_state.is_pro_user and st.session_state.free_used_count >= 3:
        st.session_state.generated_report = ""
        st.error("🔒 **ఈ డివైజ్‌లో మీ 3 ఉచిత రిపోర్ట్‌లు పూర్తయ్యాయి!**")
        st.markdown(
            f"* **1 Month Unlimited (₹100):** 👉 [Pay ₹100]({PAY_1_MONTH_LINK})\n"
            f"* **12 Months Unlimited (₹1,000):** 👉 [Pay ₹1,000]({PAY_12_MONTHS_LINK})"
        )
    elif not video_url.strip():
        st.warning("⚠️ ముందుగా వీడియో లింక్ పేస్ట్ చేయండి.")
    else:
        if platform == "YouTube":
            with st.spinner("YouTube లైవ్ డేటా & కామెంట్స్ సేకరిస్తోంది..."):
                d_txt, st_obj = fetch_youtube_info(video_url.strip())
        else:
            d_txt, st_obj = (
                f"Platform: {platform}\nURL: {video_url.strip()}\nNote: Public URL analysis requested. Provide deep platform-specific growth, hook, retention, audio trend, hashtag SEO, monetization, and 30-day action blueprint.",
                None,
            )

        if platform == "YouTube" and not d_txt:
            st.session_state.generated_report = ""
            st.error(f"⚠️ {st_obj}")
        else:
            if isinstance(st_obj, dict):
                m1, m2, m3 = st.columns(3)
                m1.metric("👀 Views", f"{int(st_obj.get('viewCount', 0)):,}")
                m2.metric("👍 Likes", f"{int(st_obj.get('likeCount', 0)):,}")
                m3.metric("💬 Comments", f"{int(st_obj.get('commentCount', 0)):,}")

            st.info("⚡ AI గ్రోత్ మెంటర్ మీ పూర్తి 6-విభాగాల రిపోర్ట్ రాస్తోంది...")
            stream_box = st.empty()
            ok, res_txt = stream_growth_report(
                platform, d_txt, report_lang, target_audience, stream_box
            )
            if ok:
                st.session_state.generated_report = res_txt
                st.session_state.report_stats = st_obj
                log_usage_to_sheet(DEVICE_ID, platform, video_url.strip())
                if not st.session_state.is_pro_user:
                    new_cnt = increment_sheet_device_count(DEVICE_ID)
                    if new_cnt is not None:
                        st.session_state.free_used_count = new_cnt
                    else:
                        st.session_state.free_used_count += 1
                    streamlit_js_eval(
                        js_expressions=f"localStorage.setItem('ts_device_free_v8', '{st.session_state.free_used_count}')",
                        key=f"ls_f_{int(time.time())}",
                    )
                    time.sleep(0.4)
                    st.rerun()
            else:
                stream_box.empty()
                st.session_state.generated_report = ""
                st.error(res_txt)

if st.session_state.generated_report:
    if isinstance(st.session_state.report_stats, dict):
        m1, m2, m3 = st.columns(3)
        m1.metric("👀 Views", f"{int(st.session_state.report_stats.get('viewCount', 0)):,}")
        m2.metric("👍 Likes", f"{int(st.session_state.report_stats.get('likeCount', 0)):,}")
        m3.metric("💬 Comments", f"{int(st.session_state.report_stats.get('commentCount', 0)):,}")
    st.success("✅ పూర్తి Growth Audit Report (6 విభాగాలు) సిద్ధమైంది!")
    st.download_button(
        "📥 Download Full Growth Report (.txt)",
        st.session_state.generated_report,
        "TrendSutra_Growth_Report.txt",
    )
    st.markdown(st.session_state.generated_report)
