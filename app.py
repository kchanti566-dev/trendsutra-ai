import os
import re
import time
import hashlib
import streamlit as st
import requests
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
    """<style>
    #MainMenu, footer, .stDeployButton, div[data-testid="stToolbarActions"],
    div[data-testid="stStatusWidget"], div[data-testid="stDecoration"],
    .viewerBadge_container__1QSob, .viewerBadge_link__1S137,
    div[class*="viewerBadge"], a[href*="streamlit.io"] {
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
        padding-top: 0rem !important;
        margin-top: -1.8rem !important;
    }
    section[data-testid="stSidebar"] .stMarkdown p {
        margin-bottom: 0.25rem !important;
        line-height: 1.3 !important;
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
        padding: 0.35rem 0.75rem !important;
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
    if k and k.strip()
]
YOUTUBE_KEY = st.secrets.get("YOUTUBE_API_KEY", "").strip()
RAPIDAPI_KEY = st.secrets.get("RAPIDAPI_API_KEY", "").strip()

GOOGLE_SHEET_API = "https://script.google.com/macros/s/AKfycbzEkkgxBP7aOKIXkEiOG7_rWc0quvnvTVqQDSWUAMk2zOPN7W8Ue_uOPwH7edmJJtEd/exec"
PAY_1_MONTH_LINK = "https://rzp.io/rzp/yop8jYS"
PAY_12_MONTHS_LINK = "https://rzp.io/rzp/sjonGmqw"


@st.cache_resource
def get_device_ledger():
    return {}


device_ledger = get_device_ledger()

def get_client_ip():
    try:
        headers = st.context.headers
        for h in ("X-Forwarded-For", "X-Real-Ip", "Cf-Connecting-Ip"):
            val = headers.get(h)
            if val:
                return val.split(",")[0].strip()
    except Exception:
        pass
    return "unknown_ip"


hw_sig = streamlit_js_eval(
    js_expressions="[navigator.platform, navigator.hardwareConcurrency, screen.width + 'x' + screen.height, Intl.DateTimeFormat().resolvedOptions().timeZone].join('|')",
    key="ts_hw_sig",
)

client_ip = get_client_ip()
raw_fp = f"{client_ip}|{hw_sig or 'base'}"
device_fp = hashlib.sha256(raw_fp.encode()).hexdigest()[:24]

ls_free = streamlit_js_eval(
    js_expressions="localStorage.getItem('ts_device_free_v6')", key="ls_get_free"
)
ls_pro = streamlit_js_eval(
    js_expressions="localStorage.getItem('ts_device_pro_v6')", key="ls_get_pro"
)

if "free_used_count" not in st.session_state:
    st.session_state.free_used_count = 0
if "is_pro_user" not in st.session_state:
    st.session_state.is_pro_user = False

server_count = device_ledger.get(device_fp, 0)
local_count = int(ls_free) if (ls_free and str(ls_free).isdigit()) else 0
max_used = max(st.session_state.free_used_count, server_count, local_count)

if max_used > st.session_state.free_used_count:
    st.session_state.free_used_count = max_used
    device_ledger[device_fp] = max_used
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
            js_expressions="localStorage.setItem('ts_device_pro_v6', 'yes')",
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
        ("Regional / Local", "Global / International", "Both (Global + Local)"),
        horizontal=True,
    )
    st.markdown("### 💎 Pro Plans (Unlimited)")
    if st.session_state.is_pro_user:
        st.success("✅ **PRO UNLIMITED ACTIVE!** అన్‌లిమిటెడ్ రిపోర్ట్‌లు పొందవచ్చు.")
    else:
        rem = max(0, 3 - st.session_state.free_used_count)
        if rem > 0:
            st.caption(f"🎁 **Free Trial:** మీకు **{rem} ఉచిత రిపోర్ట్‌లు** మిగిలి ఉన్నాయి.")
        else:
            st.error("🔒 **Free Trial: 0 అవకాశాలు మిగిలి ఉన్నాయి!**")
        st.markdown(
            f"• **1 Month:** **₹100/-** 👉 [Pay ₹100]({PAY_1_MONTH_LINK})  \n"
            f"• **12 Months:** **₹1,000/-** 👉 [Pay ₹1,000]({PAY_12_MONTHS_LINK})"
        )
        manual_pid = st.text_input(
            "🔑 Payment ID:",
            placeholder="pay_P9x82kLm01",
            label_visibility="collapsed",
        )
        if st.button("Unlock with Payment ID 🔓", use_container_width=True):
            res_st = verify_payment_id(manual_pid)
            if res_st == "OWNER_VALID":
                st.session_state.is_pro_user = True
                st.rerun()
            elif res_st == "VALID":
                st.session_state.is_pro_user = True
                streamlit_js_eval(
                    js_expressions="localStorage.setItem('ts_device_pro_v6', 'yes')",
                    key=f"ls_pro_{int(time.time())}",
                )
                time.sleep(0.5)
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


def fetch_youtube_info(url):
    m = re.search(r"(?:v=|\/|live\/|shorts\/)([0-9A-Za-z_-]{11}).*", url)
    if not m:
        return None, "సరైన YouTube వీడియో లింక్ ఇవ్వండి."
    try:
        yt = build("youtube", "v3", developerKey=YOUTUBE_KEY)
        vr = yt.videos().list(part="snippet,statistics", id=m.group(1)).execute()
        items = vr.get("items", ())
        if not items:
            return None, "వీడియో వివరాలు దొరకలేదు."
        sn, st_obj = items[0]["snippet"], items[0]["statistics"]
        coms = []
        try:
            cr = (
                yt.commentThreads()
                .list(
                    part="snippet",
                    videoId=m.group(1),
                    maxResults=30,
                    order="relevance",
                    textFormat="plainText",
                )
                .execute()
            )
            coms = [
                c["snippet"]["topLevelComment"]["snippet"]["textDisplay"]
                for c in cr.get("items", ())
            ]
        except Exception:
            coms = ["కామెంట్లు ఆఫ్ చేసి ఉన్నాయి."]
        return (
            f"Title: {sn.get('title')}\nViews: {st_obj.get('viewCount','0')},"
            f" Likes: {st_obj.get('likeCount','0')}\nDesc:"
            f" {sn.get('description','')[:600]}\nTags: {sn.get('tags',())}\nComments:"
            f" {coms}",
            st_obj,
        )
    except Exception as e:
        return None, f"YouTube Error: {str(e)}"


def generate_growth_report(platform_name, raw_data, lang, audience):
    prompt = (
        f"Friendly {platform_name} Growth Advisor for TrendSutra AI. Give a"
        f" 5-section A-to-Z Growth Report in {lang} for {audience}. Use exact"
        " Telugu spelling 'పని 1, పని 2, పని 3'.\nSections: 1. Audience Feedback"
        " 2. 3 Viral Video Ideas 3. Earning Ideas 4. Title/Description/Tags SEO 5."
        f" 30-Day Action Plan.\nData: {raw_data}"
    )
    last_err = "API Key missing"
    for key in GEMINI_KEYS:
        client = genai.Client(api_key=key)
        avail_models = []
        try:
            for mod in client.models.list():
                name = mod.name.replace("models/", "")
                if "flash" in name and "tts" not in name and "image" not in name:
                    avail_models.append(name)
        except Exception:
            pass
        if not avail_models:
            avail_models = ["gemini-2.5-flash", "gemini-2.5-flash-lite"]
        for m in avail_models[:3]:
            for _ in range(2):
                try:
                    resp = client.models.generate_content(model=m, contents=prompt)
                    if resp and resp.text:
                        return True, resp.text
                except Exception as e:
                    last_err = str(e)
                    time.sleep(1.5)
    return False, f"⚠️ AI సర్వర్ ప్రస్తుతం బిజీగా ఉంది: {last_err[:100]}"


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
                ok, res_txt = generate_growth_report(
                    platform, d_txt, report_lang, target_audience
                )
                if ok:
                    st.session_state.generated_report, st.session_state.report_stats = (
                        res_txt,
                        st_obj,
                    )
                    if not st.session_state.is_pro_user:
                        new_cnt = st.session_state.free_used_count + 1
                        st.session_state.free_used_count = new_cnt
                        device_ledger[device_fp] = new_cnt
                        streamlit_js_eval(
                            js_expressions=f"localStorage.setItem('ts_device_free_v6', '{new_cnt}')",
                            key=f"ls_f_{int(time.time())}",
                        )
                        time.sleep(0.5)
                        st.rerun()
                else:
                    st.error(res_txt)

if st.session_state.generated_report:
    if isinstance(st.session_state.report_stats, dict):
        m1, m2, m3 = st.columns(3)
        m1.metric("👀 Views", f"{int(st.session_state.report_stats.get('viewCount',0)):,}")
        m2.metric("👍 Likes", f"{int(st.session_state.report_stats.get('likeCount',0)):,}")
        m3.metric("💬 Comments", f"{int(st.session_state.report_stats.get('commentCount',0)):,}")
    st.success("✅ Growth Audit Report సిద్ధమైంది!")
    st.download_button(
        "📥 Download Growth Report (.txt)",
        st.session_state.generated_report,
        "TrendSutra_Report.txt",
    )
    st.markdown(st.session_state.generated_report)
