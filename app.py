import os
import re
import time
import hashlib
import json
from google import genai
from googleapiclient.discovery import build
import requests
import streamlit as st
from streamlit_js_eval import streamlit_js_eval

st.set_page_config(
    page_title="TrendSutra AI - Growth Analyzer",
    page_icon="logo.png" if os.path.isfile("logo.png") else "🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """<style>
    #MainMenu, footer, .stDeployButton, div[data-testid="stToolbarActions"], div[data-testid="stDecoration"], .viewerBadge_container__1QSob, .viewerBadge_link__1S137 {display:none!important;}
    header[data-testid="stHeader"] {height:1.2rem!important;background:transparent!important;}
    .block-container {padding-top:0rem!important;margin-top:-2.2rem!important;}
    section[data-testid="stSidebar"] > div:first-child {padding-top:0.4rem!important;margin-top:-1.2rem!important;}
    section[data-testid="stSidebar"] .stMarkdown p {margin-bottom:0.25rem!important;line-height:1.35!important;}
    section[data-testid="stSidebar"] div[data-testid="stVerticalBlock"] {gap:0.45rem!important;}
    div.stButton > button:first-child {background-color:#c92a2a;color:white;font-weight:bold;border-radius:6px;border:none;width:100%;}
    div.stDownloadButton > button:first-child {background-color:#2b8a3e;color:white;font-weight:bold;border-radius:6px;border:none;}
    </style>""",
    unsafe_allow_html=True,
)

GEMINI_KEYS = [
    k.strip()
    for k in (
        st.secrets.get("GEMINI_API_KEY", ""),
        st.secrets.get("GEMINI_API_KEY_2", ""),
        st.secrets.get("GEMINI_API_KEY_3", ""),
    )
    if k and k.strip()
]
YOUTUBE_KEY = st.secrets.get("YOUTUBE_API_KEY", "")
RAPIDAPI_KEY = st.secrets.get("RAPIDAPI_API_KEY", "")

GOOGLE_SHEET_API = "https://script.google.com/macros/s/AKfycbzEkkgxBP7aOKIXkEiOG7_rWc0quvnvTVqQDSWUAMk2zOPN7W8Ue_uOPwH7edmJJtEd/exec"
PAY_1_MONTH_LINK = "https://rzp.io/rzp/yop8jYS"
PAY_12_MONTHS_LINK = "https://rzp.io/rzp/sjonGmqw"

LEDGER_FILE = "/tmp/ts_device_ledger_v6.json"

def get_client_ip():
    try:
        r = requests.get("https://api.ipify.org?format=json", timeout=3)
        if r.status_code == 200:
            return r.json().get("ip", "")
    except Exception:
        pass
    try:
        hdrs = st.context.headers
        fwd = hdrs.get("X-Forwarded-For", "")
        if fwd:
            return fwd.split(",")[0].strip()
    except Exception:
        pass
    return "unknown_ip"

def load_ledger():
    if os.path.isfile(LEDGER_FILE):
        try:
            with open(LEDGER_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_ledger(data):
    try:
        with open(LEDGER_FILE, "w") as f:
            json.dump(data, f)
    except Exception:
        pass

hw_sig = streamlit_js_eval(
    js_expressions="navigator.platform + '|' + screen.width + 'x' + screen.height + '|' + (navigator.hardwareConcurrency || 0) + '|' + Intl.DateTimeFormat().resolvedOptions().timeZone",
    key="ls_hw_sig",
)
ls_free = streamlit_js_eval(
    js_expressions="localStorage.getItem('ts_device_free_v6')", key="ls_get_free"
)
ls_pro = streamlit_js_eval(
    js_expressions="localStorage.getItem('ts_device_pro_v6')", key="ls_get_pro"
)

if "client_ip" not in st.session_state:
    st.session_state.client_ip = get_client_ip()

device_raw = f"{st.session_state.client_ip}|{hw_sig or 'pending'}"
device_id = hashlib.sha256(device_raw.encode()).hexdigest()[:24]

ledger = load_ledger()
server_count = int(ledger.get(device_id, 0)) if hw_sig else 0
local_count = int(ls_free) if (ls_free and str(ls_free).isdigit()) else 0

if "free_used_count" not in st.session_state:
    st.session_state.free_used_count = max(server_count, local_count)
else:
    st.session_state.free_used_count = max(st.session_state.free_used_count, server_count, local_count)

if "is_pro_user" not in st.session_state:
    st.session_state.is_pro_user = False

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
    st.markdown("### 🟢 Settings")
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
        st.caption(f"🎁 **Free Trial:** మీకు **{rem} ఉచిత రిపోర్ట్‌లు** మిగిలి ఉన్నాయి.")
        st.markdown(
            f"• **1 Month:** **₹100/-** 👉 [Pay ₹100]({PAY_1_MONTH_LINK})  \n"
            f"• **12 Months:** **₹1,000/-** 👉 [Pay ₹1,000]({PAY_12_MONTHS_LINK})"
        )
        st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)
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
        st.image("logo.png", width=100)
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
    platform = st.selectbox(
        "Select Platform:", ("YouTube", "Instagram Reels", "TikTok")
    )
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
                    maxResults=15,
                    order="relevance",
                    textFormat="plainText",
                )
                .execute()
            )
            coms = [
                c["snippet"]["topLevelComment"]["snippet"]["textDisplay"][:150]
                for c in cr.get("items", ())
            ]
        except Exception:
            coms = ["కామెంట్లు ఆఫ్ చేసి ఉన్నాయి."]
        return (
            f"Title: {sn.get('title')}\nViews: {st_obj.get('viewCount','0')}, Likes: {st_obj.get('likeCount','0')}\n"
            f"Desc: {sn.get('description','')[:350]}\nTags: {sn.get('tags',())[:15]}\nComments: {coms}",
            st_obj,
        )
    except Exception as e:
        return None, f"YouTube Error: {str(e)}"

def get_prioritized_models(client):
    try:
        all_m = [
            m.name.replace("models/", "")
            for m in client.models.list()
            if "generateContent" in (m.supported_actions or [])
            and "flash" in m.name.lower()
            and "image" not in m.name.lower()
            and "audio" not in m.name.lower()
            and "tts" not in m.name.lower()
        ]
        lite = [x for x in all_m if "lite" in x.lower()]
        std = [x for x in all_m if "lite" not in x.lower()]
        ordered = lite + std
        if ordered:
            return ordered
    except Exception:
        pass
    return ["gemini-3.5-flash-lite", "gemini-3.5-flash", "gemini-2.5-flash-lite"]

def generate_growth_report(platform_name, raw_data, lang, audience):
    prompt = (
        f"Act as a {platform_name} Growth Advisor for TrendSutra AI. Give a crisp, high-impact "
        f"5-section A-to-Z Growth Report in {lang} for {audience} audience. Use exact Telugu spelling 'పని 1, పని 2, పని 3'.\n"
        f"Sections: 1. Audience Feedback 2. 3 Viral Video Ideas 3. Earning Ideas 4. Title/Description/Tags SEO 5. 30-Day Action Plan.\n"
        f"Data: {raw_data}"
    )
    last_err = "API Key missing in Secrets"
    for key in GEMINI_KEYS:
        client = genai.Client(api_key=key)
        models_to_try = get_prioritized_models(client)
        for m in models_to_try:
            for attempt in range(2):
                try:
                    resp = client.models.generate_content(model=m, contents=prompt)
                    if resp and resp.text:
                        return True, resp.text
                except Exception as e:
                    err_str = str(e)
                    last_err = err_str
                    if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                        time.sleep(3)
                    else:
                        break
    if "429" in last_err or "RESOURCE_EXHAUSTED" in last_err:
        return False, "⚠️ ఉచిత API కోటా (Free Tier Quota) తాత్కాలికంగా నిండింది! దయచేసి 1 నిమిషం ఆగి మళ్ళీ ప్రయత్నించండి లేదా Google AI Studio లో Billing ఆన్ చేయండి."
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
                        st.session_state.free_used_count += 1
                        if hw_sig:
                            ledger = load_ledger()
                            ledger[device_id] = st.session_state.free_used_count
                            save_ledger(ledger)
                        streamlit_js_eval(
                            js_expressions=f"localStorage.setItem('ts_device_free_v6', '{st.session_state.free_used_count}')",
                            key=f"ls_f_{int(time.time())}",
                        )
                        time.sleep(0.5)
                        st.rerun()
                else:
                    st.session_state.generated_report = ""
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
