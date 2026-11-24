import os
import re
import time
import hashlib
import requests
import streamlit as st
from google import genai
from googleapiclient.discovery import build
from streamlit_js_eval import streamlit_js_eval

st.set_page_config(
    page_title="TrendSutra AI - Growth Analyzer",
    page_icon="logo.png" if os.path.isfile("logo.png") else "🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    #MainMenu, footer, .stDeployButton, div[data-testid="stToolbarActions"] {display: none !important;}
    header[data-testid="stHeader"] {height: 1.5rem !important; background: transparent !important;}
    .block-container {padding-top: 0rem !important; margin-top: -2.2rem !important; padding-bottom: 1rem !important;}
    section[data-testid="stSidebar"] > div:first-child {padding-top: 0rem !important; margin-top: -1.5rem !important;}
    div[data-testid="stSidebarUserContent"] {padding-top: 0rem !important;}
    div.stButton > button:first-child {background-color: #c92a2a; color: white; font-weight: bold; border-radius: 6px; padding: 0.5rem 1.2rem; border: none;}
    div.stDownloadButton > button:first-child {background-color: #2b8a3e; color: white; font-weight: bold; border-radius: 6px; padding: 0.5rem 1.2rem; border: none;}
    </style>
    """,
    unsafe_allow_html=True,
)

GEMINI_KEYS = [
    k for k in (
        st.secrets.get("GEMINI_API_KEY", ""),
        st.secrets.get("GEMINI_API_KEY_2", ""),
    ) if str(k).strip()
]
YOUTUBE_KEY = st.secrets.get("YOUTUBE_API_KEY", "")
RAPIDAPI_KEY = st.secrets.get("RAPIDAPI_API_KEY", "")

GOOGLE_SHEET_API = "https://script.google.com/macros/s/AKfycbzEkkgxBP7aOKIXkEiOG7_rWc0quvnvTVqQDSWUAMk2zOPN7W8Ue_uOPwH7edmJJtEd/exec"
PAY_1_MONTH_LINK = "https://rzp.io/rzp/yop8jYS"
PAY_12_MONTHS_LINK = "https://rzp.io/rzp/sjonGmqw"

# Multi-layer persistent device lock (localStorage + IndexedDB + Cookie + Server-side IP/UA hash)
DEVICE_LOCK_JS = """
(async () => {
    const key = 'ts_perm_device_used_v9';
    let val = 0;
    try {
        const ls = localStorage.getItem(key);
        if (ls && !isNaN(ls)) val = Math.max(val, parseInt(ls));
    } catch(e) {}
    try {
        const match = document.cookie.match(new RegExp('(^| )' + key + '=([^;]+)'));
        if (match && !isNaN(match[2])) val = Math.max(val, parseInt(match[2]));
    } catch(e) {}
    try {
        const idbVal = await new Promise((resolve) => {
            const req = indexedDB.open('TrendSutraLockDB', 1);
            req.onupgradeneeded = () => req.result.createObjectStore('locks');
            req.onsuccess = () => {
                const tx = req.result.transaction('locks', 'readonly');
                const getReq = tx.objectStore('locks').get(key);
                getReq.onsuccess = () => resolve(getReq.result || 0);
                getReq.onerror = () => resolve(0);
            };
            req.onerror = () => resolve(0);
        });
        if (idbVal && !isNaN(idbVal)) val = Math.max(val, parseInt(idbVal));
    } catch(e) {}
    return String(val);
})()
"""

def set_permanent_device_lock(count_val, key_suffix):
    c = int(count_val)
    js_write = f"""
    (async () => {{
        const key = 'ts_perm_device_used_v9';
        const val = '{c}';
        try {{ localStorage.setItem(key, val); }} catch(e) {{}}
        try {{ document.cookie = key + '=' + val + '; max-age=315360000; path=/; SameSite=Lax'; }} catch(e) {{}}
        try {{
            const req = indexedDB.open('TrendSutraLockDB', 1);
            req.onupgradeneeded = () => req.result.createObjectStore('locks');
            req.onsuccess = () => {{
                const tx = req.result.transaction('locks', 'readwrite');
                tx.objectStore('locks').put(val, key);
            }};
        }} catch(e) {{}}
        return val;
    }})()
    """
    streamlit_js_eval(js_expressions=js_write, key=f"set_lock_{key_suffix}")

def get_device_fingerprint():
    try:
        headers = st.context.headers
        ip = headers.get("X-Forwarded-For", "").split(",")[0].strip()
        ua = headers.get("User-Agent", "")
        lang = headers.get("Accept-Language", "")
        raw = f"{ip}|{ua}|{lang}"
        if ip or ua:
            return hashlib.sha256(raw.encode()).hexdigest()[:24]
    except Exception:
        pass
    return ""

@st.cache_resource
def get_server_device_tracker():
    return {}

server_tracker = get_server_device_tracker()
dev_fp = get_device_fingerprint()

ls_free = streamlit_js_eval(js_expressions=DEVICE_LOCK_JS, key="ts_read_perm_lock")
ls_pro = streamlit_js_eval(js_expressions="localStorage.getItem('ts_perm_pro_v9')", key="ts_read_pro_lock")

if "free_used_count" not in st.session_state:
    st.session_state.free_used_count = 0
if "is_pro_user" not in st.session_state:
    st.session_state.is_pro_user = False

# Sync from server fingerprint tracker
if dev_fp and dev_fp in server_tracker:
    if server_tracker[dev_fp] > st.session_state.free_used_count:
        st.session_state.free_used_count = server_tracker[dev_fp]

# Sync from browser permanent storage (localStorage + IndexedDB + Cookie)
if ls_free is not None and str(ls_free).isdigit():
    browser_count = int(ls_free)
    if browser_count > st.session_state.free_used_count:
        st.session_state.free_used_count = browser_count
        if dev_fp:
            server_tracker[dev_fp] = max(server_tracker.get(dev_fp, 0), browser_count)
        st.rerun()
    elif st.session_state.free_used_count > browser_count:
        set_permanent_device_lock(st.session_state.free_used_count, f"sync_{st.session_state.free_used_count}")

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
            timeout=15,
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
            js_expressions="localStorage.setItem('ts_perm_pro_v9', 'yes')",
            key="ls_pro_url_v9",
        )
        st.toast("🎉 Payment Verified! Unlimited Pro Access Unlocked!")
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
        ("Regional / Local", "Global / International", "Both (Global + Local)"),
    )
    st.markdown("### 💎 Pro Plans (Unlimited)")
    if st.session_state.is_pro_user:
        st.success("✅ **PRO UNLIMITED ACTIVE!**\n\nఅన్‌లిమిటెడ్ రిపోర్ట్‌లు పొందవచ్చు.")
    else:
        remaining = max(0, 3 - st.session_state.free_used_count)
        if remaining == 0:
            st.error("🔒 **Free Trial: 0 ఉచిత రిపోర్ట్‌లు మిగిలి ఉన్నాయి!**\n\nఈ డివైజ్‌కు ఇచ్చిన 3 ఉచిత అవకాశాలు పూర్తయ్యాయి.")
        else:
            st.caption(f"🎁 **Free Trial:** మీకు **{remaining} ఉచిత రిపోర్ట్‌లు** మిగిలి ఉన్నాయి.")
        st.markdown(
            f"• **1 Month:** **₹100/-** 👉 [Pay ₹100]({PAY_1_MONTH_LINK})  \n"
            f"• **12 Months:** **₹1,000/-** 👉 [Pay ₹1,000]({PAY_12_MONTHS_LINK})"
        )
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
                    js_expressions="localStorage.setItem('ts_perm_pro_v9', 'yes')",
                    key=f"ls_pro_btn_{int(time.time())}",
                )
                time.sleep(0.6)
                st.rerun()
            elif res_st == "ALREADY_USED":
                st.error("❌ ఈ Payment ID గరిష్టంగా 3 డివైజ్‌లలో వాడబడింది! support@aiengtel.com కి మెసేజ్ చేయండి.")
            else:
                st.error("❌ సరైన Payment ID ఇవ్వండి.")

if os.path.isfile("logo.png"):
    c1, c2 = st.columns((1, 5))
    with c1:
        st.image("logo.png", width=100)
    with c2:
        st.markdown("# TrendSutra AI")
        st.markdown("**A to Z Growth Analyzer for YouTube, Instagram & TikTok | Powered by [AIENGTEL.com](https://aiengtel.com)**")
else:
    st.markdown("# 🚀 TrendSutra AI\n**A to Z Growth Analyzer for YouTube, Instagram & TikTok | Powered by [AIENGTEL.com](https://aiengtel.com)**")

col1, col2 = st.columns(2)
with col1:
    platform = st.selectbox("Select Platform:", ("YouTube", "Instagram Reels", "TikTok"))
with col2:
    video_url = st.text_input(
        "Channel / Profile / Video Link:",
        placeholder="https://youtu.be/... లేదా Reel / TikTok లింక్ పేస్ట్ చేయండి",
    )

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
        sn = items[0]["snippet"]
        st_obj = items[0]["statistics"]
        coms = []
        try:
            cr = yt.commentThreads().list(
                part="snippet",
                videoId=m.group(1),
                maxResults=30,
                order="relevance",
                textFormat="plainText",
            ).execute()
            coms = [
                c["snippet"]["topLevelComment"]["snippet"]["textDisplay"]
                for c in cr.get("items", [])
            ]
        except Exception:
            coms = ["కామెంట్లు ఆఫ్ చేసి ఉన్నాయి."]
        return (
            f"Title: {sn.get('title')}\n"
            f"Views: {st_obj.get('viewCount', '0')}, Likes: {st_obj.get('likeCount', '0')}\n"
            f"Desc: {sn.get('description', '')[:600]}\n"
            f"Tags: {sn.get('tags', [])}\n"
            f"Comments: {coms}",
            st_obj,
        )
    except Exception as e:
        return None, f"YouTube Error: {str(e)}"

def generate_growth_report(platform_name, raw_data, lang, audience):
    prompt = (
        f"Friendly {platform_name} Growth Advisor for TrendSutra AI. "
        f"Give a detailed 5-section A-to-Z Growth Report in {lang} for {audience}. "
        "Use exact Telugu spelling 'పని 1, పని 2, పని 3'.\n"
        "Sections:\n"
        "1. Audience Feedback & Sentiment\n"
        "2. 3 High-Retention Viral Video Ideas\n"
        "3. Earning & Monetization Ideas\n"
        "4. Optimized Title, Description & SEO Tags\n"
        "5. 30-Day Step-by-Step Action Plan\n"
        f"Data: {raw_data}"
    )
    last_err = "API Key missing in Secrets"
    for key in GEMINI_KEYS:
        clean_key = str(key).strip()
        if not clean_key:
            continue
        client = genai.Client(api_key=clean_key)
        flash_models = []
        try:
            for m_obj in client.models.list():
                m_name = getattr(m_obj, "name", "").replace("models/", "")
                if "flash" in m_name and "tts" not in m_name and "image" not in m_name and "audio" not in m_name:
                    flash_models.append(m_name)
        except Exception:
            pass
        if not flash_models:
            flash_models = ["gemini-2.5-flash", "gemini-2.5-flash-lite", "gemini-3.5-flash"]
        for m in flash_models[:4]:
            try:
                resp = client.models.generate_content(model=m, contents=prompt)
                if resp and resp.text:
                    return True, resp.text
            except Exception as e:
                last_err = str(e)
                time.sleep(1.5)
    return False, f"⚠️ AI సర్వర్ బిజీగా ఉంది: {last_err[:120]}"

if "generated_report" not in st.session_state:
    st.session_state.generated_report = ""
if "report_stats" not in st.session_state:
    st.session_state.report_stats = None

if st.button("Generate Accurate Growth Report 🔍"):
    if not st.session_state.is_pro_user and st.session_state.free_used_count >= 3:
        st.session_state.generated_report = ""
        st.error("🔒 **ఈ డివైజ్‌లో మీ 3 ఉచిత రిపోర్ట్‌లు పూర్తయ్యాయి! (0 Chances Left)**")
        st.markdown(
            f"* **1 Month Unlimited (₹100):** 👉 [Pay ₹100]({PAY_1_MONTH_LINK})\n"
            f"* **12 Months Unlimited (₹1,000):** 👉 [Pay ₹1,000]({PAY_12_MONTHS_LINK})"
        )
    elif not video_url.strip():
        st.warning("⚠️ ముందుగా వీడియో లింక్ పేస్ట్ చేయండి.")
    else:
        with st.spinner("రిపోర్ట్ తయారు చేస్తోంది..."):
            if platform == "YouTube":
                d_txt, st_obj = fetch_youtube_info(video_url.strip())
            else:
                d_txt, st_obj = f"{platform} URL: {video_url.strip()}", None
            if platform == "YouTube" and not d_txt:
                st.error(f"⚠️ {st_obj}")
            else:
                ok, res_txt = generate_growth_report(platform, d_txt, report_lang, target_audience)
                if ok:
                    st.session_state.generated_report = res_txt
                    st.session_state.report_stats = st_obj
                    if not st.session_state.is_pro_user:
                        new_count = st.session_state.free_used_count + 1
                        st.session_state.free_used_count = new_count
                        if dev_fp:
                            server_tracker[dev_fp] = max(server_tracker.get(dev_fp, 0), new_count)
                        set_permanent_device_lock(new_count, f"use_{new_count}_{int(time.time())}")
                        time.sleep(0.8)
                        st.rerun()
                else:
                    st.error(res_txt)

if st.session_state.generated_report:
    if isinstance(st.session_state.report_stats, dict):
        m1, m2, m3 = st.columns(3)
        m1.metric("👀 Views", f"{int(st.session_state.report_stats.get('viewCount', 0)):,}")
        m2.metric("👍 Likes", f"{int(st.session_state.report_stats.get('likeCount', 0)):,}")
        m3.metric("💬 Comments", f"{int(st.session_state.report_stats.get('commentCount', 0)):,}")
    st.success("✅ Growth Audit Report సిద్ధమైంది!")
    st.download_button(
        "📥 Download Growth Report (.txt)",
        st.session_state.generated_report,
        "TrendSutra_Report.txt",
    )
    st.markdown(st.session_state.generated_report)
