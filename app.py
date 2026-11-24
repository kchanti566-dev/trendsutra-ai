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
    .viewerBadge_container__1QSob, .viewerBadge_link__1S137,
    a[href*="streamlit.io/cloud"] {
        display: none !important;
        visibility: hidden !important;
    }
    header[data-testid="stHeader"] {
        height: 1.5rem !important;
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
    }
    section[data-testid="stSidebar"] div[data-testid="stRadio"] > div {
        gap: 0.4rem !important;
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
    if str(k).strip()
]
YOUTUBE_KEY = str(st.secrets.get("YOUTUBE_API_KEY", "")).strip()
RAPIDAPI_KEY = str(st.secrets.get("RAPIDAPI_API_KEY", "")).strip()

GOOGLE_SHEET_API = "https://script.google.com/macros/s/AKfycbzEkkgxBP7aOKIXkEiOG7_rWc0quvnvTVqQDSWUAMk2zOPN7W8Ue_uOPwH7edmJJtEd/exec"
PAY_1_MONTH_LINK = "https://rzp.io/rzp/yop8jYS"
PAY_12_MONTHS_LINK = "https://rzp.io/rzp/sjonGmqw"

DEVICE_LEDGER_FILE = "/tmp/ts_device_ledger_v7.json"


def load_ledger():
    try:
        if os.path.exists(DEVICE_LEDGER_FILE):
            with open(DEVICE_LEDGER_FILE, "r") as f:
                return json.load(f)
    except Exception:
        pass
    return {}


def save_ledger(data):
    try:
        with open(DEVICE_LEDGER_FILE, "w") as f:
            json.dump(data, f)
    except Exception:
        pass


def get_server_client_ip():
    try:
        hdrs = st.context.headers
        for key in ("X-Forwarded-For", "X-Real-Ip", "CF-Connecting-IP", "True-Client-IP"):
            val = hdrs.get(key)
            if val:
                return val.split(",")[0].strip()
    except Exception:
        pass
    return ""


js_fp_expr = """(async () => {
    let pubIp = '';
    try {
        const r = await fetch('https://api.ipify.org?format=json');
        const j = await r.json();
        pubIp = j.ip || '';
    } catch(e) {}
    const hw = [
        navigator.platform || '',
        screen.width + 'x' + screen.height + 'x' + screen.colorDepth,
        navigator.hardwareConcurrency || '',
        Intl.DateTimeFormat().resolvedOptions().timeZone || ''
    ].join('|');
    let lsVal = 0;
    try { lsVal = parseInt(localStorage.getItem('ts_device_free_v7') || '0') || 0; } catch(e) {}
    let ckMatch = document.cookie.match(/ts_df_v7=(\d+)/);
    let ckVal = ckMatch ? parseInt(ckMatch[1]) : 0;
    let proFlag = 'no';
    try { if (localStorage.getItem('ts_device_pro_v7') === 'yes') proFlag = 'yes'; } catch(e) {}
    return JSON.stringify({ip: pubIp, hw: hw, ls: Math.max(lsVal, ckVal), pro: proFlag});
})()"""

client_info_raw = streamlit_js_eval(js_expressions=js_fp_expr, key="ts_fp_init_v7")

if "free_used_count" not in st.session_state:
    st.session_state.free_used_count = 0
if "is_pro_user" not in st.session_state:
    st.session_state.is_pro_user = False
if "device_keys" not in st.session_state:
    st.session_state.device_keys = []

srv_ip = get_server_client_ip()
client_ip = ""
hw_sig = ""
browser_count = 0
browser_pro = False

if client_info_raw and isinstance(client_info_raw, str):
    try:
        parsed = json.loads(client_info_raw)
        client_ip = str(parsed.get("ip", "")).strip()
        hw_sig = str(parsed.get("hw", "")).strip()
        browser_count = int(parsed.get("ls", 0))
        browser_pro = parsed.get("pro") == "yes"
    except Exception:
        pass

keys_to_track = []
if client_ip and hw_sig:
    keys_to_track.append("ip_hw_" + hashlib.sha256(f"{client_ip}|{hw_sig}".encode()).hexdigest()[:20])
if client_ip:
    keys_to_track.append("ip_" + hashlib.sha256(client_ip.encode()).hexdigest()[:20])
if srv_ip and hw_sig:
    keys_to_track.append("srv_hw_" + hashlib.sha256(f"{srv_ip}|{hw_sig}".encode()).hexdigest()[:20])
if hw_sig:
    keys_to_track.append("hw_" + hashlib.sha256(hw_sig.encode()).hexdigest()[:20])

if keys_to_track:
    st.session_state.device_keys = keys_to_track

ledger = load_ledger()
ledger_count = max([int(ledger.get(k, 0)) for k in st.session_state.device_keys] + [0])
effective_used = max(st.session_state.free_used_count, browser_count, ledger_count)

if effective_used > st.session_state.free_used_count:
    st.session_state.free_used_count = min(3, effective_used)
    for k in st.session_state.device_keys:
        ledger[k] = st.session_state.free_used_count
    save_ledger(ledger)
    st.rerun()

if browser_pro and not st.session_state.is_pro_user:
    st.session_state.is_pro_user = True
    st.rerun()


def record_device_usage(new_count):
    st.session_state.free_used_count = min(3, new_count)
    lg = load_ledger()
    for k in st.session_state.device_keys:
        lg[k] = st.session_state.free_used_count
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
        streamlit_js_eval(
            js_expressions="localStorage.setItem('ts_device_pro_v7', 'yes'); document.cookie='ts_pro_v7=yes;max-age=315360000;path=/';",
            key="ls_pro_url_v7",
        )
    elif st_val == "ALREADY_USED":
        st.sidebar.error("⚠️ ఈ Payment ID గరిష్టంగా 3 డివైజ్‌లలో వాడబడింది!")

with st.sidebar:
    st.markdown("### 🟢 Settings")
    report_lang = st.selectbox(
        "Report Language / భాష:",
        ("English (Global)", "Telugu (తెలుగు)", "Tenglish"),
        label_visibility="visible",
    )
    target_audience = st.radio(
        "Target Audience:",
        ("Regional", "Global", "Both"),
        horizontal=True,
    )
    st.markdown("---")
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
        st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
        manual_pid = st.text_input(
            "Payment ID",
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
                    js_expressions="localStorage.setItem('ts_device_pro_v7', 'yes'); document.cookie='ts_pro_v7=yes;max-age=315360000;path=/';",
                    key=f"ls_pro_{int(time.time())}",
                )
                time.sleep(0.5)
                st.rerun()
            elif res_st == "ALREADY_USED":
                st.error("❌ ఈ Payment ID గరిష్టంగా 3 డివైజ్‌లలో వాడబడింది! aiengtel@aiengtel.com కి మెసేజ్ చేయండి.")
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
        items = vr.get("items", [])
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
                    maxResults=25,
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
        return (
            f"Title: {sn.get('title')}\nViews: {st_obj.get('viewCount', '0')}, "
            f"Likes: {st_obj.get('likeCount', '0')}\nDesc: {sn.get('description', '')[:500]}\n"
            f"Tags: {sn.get('tags', [])}\nComments: {coms}",
            st_obj,
        )
    except Exception as e:
        return None, f"YouTube Error: {str(e)}"


def get_active_flash_models(client):
    lite_models = []
    flash_models = []
    try:
        for mod in client.models.list():
            m_name = getattr(mod, "name", "") or ""
            methods = getattr(mod, "supported_generation_methods", []) or []
            clean_m = m_name.replace("models/", "")
            if (
                (not methods or "generateContent" in methods)
                and "flash" in clean_m
                and "image" not in clean_m
                and "audio" not in clean_m
                and "tts" not in clean_m
            ):
                if "lite" in clean_m:
                    lite_models.append(clean_m)
                else:
                    flash_models.append(clean_m)
    except Exception:
        pass
    ordered = lite_models + flash_models
    return ordered if ordered else ["gemini-2.5-flash-lite", "gemini-2.5-flash"]


def generate_growth_report(platform_name, raw_data, lang, audience):
    prompt = (
        f"Friendly {platform_name} Growth Advisor for TrendSutra AI. Give a 5-section Growth Report "
        f"in {lang} for {audience} audience. Use exact Telugu spelling 'పని 1, పని 2, పని 3'.\n"
        f"Sections: 1. Audience Feedback 2. 3 Viral Video Ideas 3. Earning Ideas "
        f"4. Title/Description/Tags SEO 5. 30-Day Action Plan.\nData: {raw_data}"
    )
    last_err = "API Key missing in Secrets"
    for key in GEMINI_KEYS:
        client = genai.Client(api_key=key)
        models_to_try = get_active_flash_models(client)
        for m in models_to_try:
            try:
                resp = client.models.generate_content(model=m, contents=prompt)
                if resp and resp.text:
                    return True, resp.text
            except Exception as e:
                last_err = str(e)
                if "429" in last_err or "503" in last_err:
                    time.sleep(1.5)
                continue
    return False, f"⚠️ AI సర్వర్ బిజీగా ఉంది: {last_err[:120]}"


if "generated_report" not in st.session_state:
    st.session_state.generated_report = ""
if "report_stats" not in st.session_state:
    st.session_state.report_stats = None

if st.button("Generate Accurate Growth Report 🔍"):
    if not st.session_state.is_pro_user and st.session_state.free_used_count >= 3:
        st.session_state.generated_report = ""
        st.session_state.report_stats = None
        st.error("🔒 **ఈ డివైజ్‌లో మీ 3 ఉచిత రిపోర్ట్‌లు పూర్తయ్యాయి! (0 Free Reports Left)**")
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
                        new_cnt = st.session_state.free_used_count + 1
                        record_device_usage(new_cnt)
                        streamlit_js_eval(
                            js_expressions=(
                                f"localStorage.setItem('ts_device_free_v7', '{new_cnt}');"
                                f"document.cookie='ts_df_v7={new_cnt};max-age=315360000;path=/';"
                            ),
                            key=f"ls_f_{int(time.time())}",
                        )
                        time.sleep(0.5)
                        st.rerun()
                else:
                    st.session_state.generated_report = ""
                    st.session_state.report_stats = None
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
