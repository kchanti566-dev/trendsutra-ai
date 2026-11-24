import os
import re
import time
import json
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
    """<style>
    #MainMenu, footer, .stDeployButton, div[data-testid="stToolbarActions"],
    div[data-testid="stStatusWidget"], div[data-testid="stDecoration"],
    div[class*="viewerBadge"], a[href*="streamlit.io"] {
        display: none !important;
        visibility: hidden !important;
    }
    header[data-testid="stHeader"] {
        height: 0.5rem !important;
        background: transparent !important;
    }
    .block-container {
        padding-top: 0rem !important;
        margin-top: -1.8rem !important;
    }
    section[data-testid="stSidebar"] > div:first-child {
        padding-top: 0.4rem !important;
        margin-top: -1.2rem !important;
    }
    section[data-testid="stSidebar"] .stMarkdown p {
        margin-bottom: 0.25rem !important;
        font-size: 0.88rem !important;
    }
    section[data-testid="stSidebar"] h3 {
        margin-top: 0.4rem !important;
        margin-bottom: 0.25rem !important;
        font-size: 1.05rem !important;
    }
    section[data-testid="stSidebar"] div[data-baseweb="select"],
    section[data-testid="stSidebar"] div[role="radiogroup"] {
        margin-bottom: 0.15rem !important;
    }
    section[data-testid="stSidebar"] div[data-testid="stAlert"] {
        padding: 0.45rem 0.65rem !important;
        margin-bottom: 0.35rem !important;
    }
    section[data-testid="stSidebar"] div[data-testid="stTextInput"] {
        margin-top: -0.2rem !important;
        margin-bottom: -0.35rem !important;
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
    k for k in (
        st.secrets.get("GEMINI_API_KEY", ""),
        st.secrets.get("GEMINI_API_KEY_2", ""),
    ) if k
]
YOUTUBE_KEY = st.secrets.get("YOUTUBE_API_KEY", "")
RAPIDAPI_KEY = st.secrets.get("RAPIDAPI_API_KEY", "")

GOOGLE_SHEET_API = "https://script.google.com/macros/s/AKfycbzEkkgxBP7aOKIXkEiOG7_rWc0quvnvTVqQDSWUAMk2zOPN7W8Ue_uOPwH7edmJJtEd/exec"
PAY_1_MONTH_LINK = "https://rzp.io/rzp/yop8jYS"
PAY_12_MONTHS_LINK = "https://rzp.io/rzp/sjonGmqw"
LEDGER_FILE = "/tmp/trendsutra_device_ledger_v7.json"

def load_ledger():
    try:
        if os.path.exists(LEDGER_FILE):
            with open(LEDGER_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {"free": {}, "pro": {}}

def save_ledger(data):
    try:
        with open(LEDGER_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f)
    except Exception:
        pass

fp_js = """
(async () => {
  let ip = "unknown";
  try {
    const r = await fetch("https://api.ipify.org?format=json");
    const j = await r.json();
    if (j && j.ip) ip = j.ip;
  } catch(e) {}
  const hw = [
    navigator.platform || "",
    navigator.hardwareConcurrency || "",
    screen.width + "x" + screen.height,
    Intl.DateTimeFormat().resolvedOptions().timeZone || ""
  ].join("|");
  return ip + "::" + hw;
})()
"""
raw_fp = streamlit_js_eval(js_expressions=fp_js, key="ts_hw_ip_fp_v7")
ls_free = streamlit_js_eval(js_expressions="localStorage.getItem('ts_device_free_v7')", key="ls_get_free_v7")
ls_pro = streamlit_js_eval(js_expressions="localStorage.getItem('ts_device_pro_v7')", key="ls_get_pro_v7")

device_id = ""
if raw_fp and isinstance(raw_fp, str) and "::" in raw_fp:
    device_id = hashlib.sha256(raw_fp.encode("utf-8")).hexdigest()[:24]

if "free_used_count" not in st.session_state:
    st.session_state.free_used_count = 0
if "is_pro_user" not in st.session_state:
    st.session_state.is_pro_user = False

ledger = load_ledger()
srv_free = int(ledger.get("free", {}).get(device_id, 0)) if device_id else 0
srv_pro = bool(ledger.get("pro", {}).get(device_id, False)) if device_id else False
loc_free = int(ls_free) if (ls_free and str(ls_free).isdigit()) else 0
loc_pro = (ls_pro == "yes")

effective_free = max(st.session_state.free_used_count, srv_free, loc_free)
effective_pro = st.session_state.is_pro_user or srv_pro or loc_pro

if effective_free != st.session_state.free_used_count or effective_pro != st.session_state.is_pro_user:
    st.session_state.free_used_count = effective_free
    st.session_state.is_pro_user = effective_pro
    st.rerun()

def mark_device_pro(dev_id):
    if dev_id:
        lg = load_ledger()
        lg.setdefault("pro", {})[dev_id] = True
        save_ledger(lg)

def mark_device_free(dev_id, count_val):
    if dev_id:
        lg = load_ledger()
        curr = int(lg.get("free", {}).get(dev_id, 0))
        lg.setdefault("free", {})[dev_id] = max(curr, count_val)
        save_ledger(lg)

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
        mark_device_pro(device_id)
        streamlit_js_eval(js_expressions="localStorage.setItem('ts_device_pro_v7', 'yes')", key="ls_pro_url_v7")
    elif st_val == "ALREADY_USED":
        st.sidebar.error("⚠️ ఈ Payment ID గరిష్టంగా 3 డివైజ్‌లలో వాడబడింది!")

with st.sidebar:
    st.markdown("### 🌍 Settings")
    report_lang = st.selectbox(
        "Report Language:",
        ("English (Global)", "Telugu (తెలుగు)", "Tenglish"),
        label_visibility="collapsed",
    )
    target_audience = st.radio(
        "Audience:",
        ("Regional", "Global", "Both"),
        horizontal=True,
        label_visibility="collapsed",
    )
    st.markdown("### 💎 Pro Plans (Unlimited)")
    if st.session_state.is_pro_user:
        st.success("✅ **PRO UNLIMITED ACTIVE!** అన్‌లిమిటెడ్ రిపోర్ట్‌లు పొందవచ్చు.")
    else:
        rem = max(0, 3 - st.session_state.free_used_count)
        if rem > 0:
            st.info(f"🎁 **Free Trial:** **{rem} ఉచిత రిపోర్ట్‌లు** మిగిలి ఉన్నాయి.")
        else:
            st.error("🔒 **Free Trial: 0 ఉచిత రిపోర్ట్‌లు!** 3 అవకాశాలు పూర్తయ్యాయి.")
        st.markdown(
            f"• **1 Month:** **₹100/-** 👉 [Pay ₹100]({PAY_1_MONTH_LINK})  
"
            f"• **12 Months:** **₹1,000/-** 👉 [Pay ₹1,000]({PAY_12_MONTHS_LINK})"
        )
        manual_pid = st.text_input(
            "Payment ID",
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
                mark_device_pro(device_id)
                streamlit_js_eval(
                    js_expressions="localStorage.setItem('ts_device_pro_v7', 'yes')",
                    key=f"ls_pro_{int(time.time())}",
                )
                time.sleep(0.5)
                st.rerun()
            elif res_st == "ALREADY_USED":
                st.error("❌ ఈ Payment ID 3 డివైజ్‌లలో వాడబడింది! admin@aiengtel.com")
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
        "# 🚀 TrendSutra AI
**A to Z Growth Analyzer for YouTube, Instagram & TikTok | Powered by [AIENGTEL.com](https://aiengtel.com)**"
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
        items = vr.get("items", [])
        if not items:
            return None, "వీడియో వివరాలు దొరకలేదు."
        sn, st_obj = items[0]["snippet"], items[0]["statistics"]
        coms = []
        try:
            cr = yt.commentThreads().list(
                part="snippet",
                videoId=m.group(1),
                maxResults=30,
                order="relevance",
                textFormat="plainText",
            ).execute()
            coms = [c["snippet"]["topLevelComment"]["snippet"]["textDisplay"] for c in cr.get("items", [])]
        except Exception:
            coms = ["కామెంట్లు ఆఫ్ చేసి ఉన్నాయి."]
        return (
            f"Title: {sn.get('title')}
Views: {st_obj.get('viewCount','0')}, Likes: {st_obj.get('likeCount','0')}
"
            f"Desc: {sn.get('description','')[:600]}
Tags: {sn.get('tags',[])}
Comments: {coms}",
            st_obj,
        )
    except Exception as e:
        return None, f"YouTube Error: {str(e)}"

def get_working_flash_models(client):
    found = []
    try:
        for mdl in client.models.list():
            name = getattr(mdl, "name", "")
            methods = getattr(mdl, "supported_generation_methods", []) or []
            short_name = name.replace("models/", "")
            if "flash" in short_name.lower() and ("generateContent" in methods or not methods):
                found.append(short_name)
    except Exception:
        pass
    preferred = ["gemini-2.5-flash", "gemini-2.5-flash-lite", "gemini-3.5-flash-lite", "gemini-3.5-flash", "gemini-2.0-flash"]
    ordered = [p for p in preferred if p in found] + [f for f in found if f not in preferred]
    return ordered[:4] if ordered else preferred[:3]

def generate_growth_report(platform_name, raw_data, lang, audience):
    prompt = (
        f"Friendly {platform_name} Growth Advisor for TrendSutra AI. Give a 5-section A-to-Z Growth Report in {lang} "
        f"for {audience} audience. Use exact Telugu spelling 'పని 1, పని 2, పని 3'.
"
        f"Sections: 1. Audience Feedback 2. 3 Viral Video Ideas 3. Earning Ideas 4. Title/Description/Tags SEO 5. 30-Day Action Plan.
Data: {raw_data}"
    )
    last_err = "API Key missing in Secrets"
    for key in GEMINI_KEYS:
        clean_k = key.strip()
        if not clean_k:
            continue
        try:
            client = genai.Client(api_key=clean_k)
            models_to_try = get_working_flash_models(client)
            for m in models_to_try:
                try:
                    resp = client.models.generate_content(model=m, contents=prompt)
                    if resp and resp.text:
                        return True, resp.text
                except Exception as e:
                    last_err = str(e)
                    time.sleep(1)
        except Exception as e:
            last_err = str(e)
    return False, f"⚠️ AI సర్వర్ బిజీగా ఉంది: {last_err[:120]}"

if "generated_report" not in st.session_state:
    st.session_state.generated_report = ""
if "report_stats" not in st.session_state:
    st.session_state.report_stats = None

if st.button("Generate Accurate Growth Report 🔍"):
    if not st.session_state.is_pro_user and st.session_state.free_used_count >= 3:
        st.session_state.generated_report = ""
        st.error("🔒 **ఈ డివైజ్‌లో మీ 3 ఉచిత రిపోర్ట్‌లు పూర్తయ్యాయి!**")
        st.markdown(
            f"* **1 Month Unlimited (₹100):** 👉 [Pay ₹100]({PAY_1_MONTH_LINK})
"
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
                    st.session_state.generated_report, st.session_state.report_stats = res_txt, st_obj
                    if not st.session_state.is_pro_user:
                        st.session_state.free_used_count += 1
                        mark_device_free(device_id, st.session_state.free_used_count)
                        streamlit_js_eval(
                            js_expressions=f"localStorage.setItem('ts_device_free_v7', '{st.session_state.free_used_count}')",
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
