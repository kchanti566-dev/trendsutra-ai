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
    #MainMenu, footer, .stDeployButton, div[data-testid="stToolbarActions"], div[data-testid="stDecoration"], div[data-testid="stStatusWidget"], .viewerBadge_container__1QSob, .styles_viewerBadge__1yB5_ {display:none!important;}
    header[data-testid="stHeader"] {height:1.2rem!important;background:transparent!important;}
    .block-container {padding-top:0.2rem!important;margin-top:-2.2rem!important;}
    section[data-testid="stSidebar"] > div:first-child {padding-top:0.2rem!important;margin-top:-1.8rem!important;}
    section[data-testid="stSidebar"] .block-container {padding-top:0.2rem!important;}
    section[data-testid="stSidebar"] h3 {margin-top:0.35rem!important;margin-bottom:0.2rem!important;font-size:1.05rem!important;}
    section[data-testid="stSidebar"] p, section[data-testid="stSidebar"] label {margin-bottom:0.15rem!important;font-size:0.88rem!important;}
    section[data-testid="stSidebar"] div[data-testid="stVerticalBlock"] > div {gap:0.35rem!important;}
    div.stButton > button:first-child {background-color:#c92a2a;color:white;font-weight:bold;border-radius:6px;border:none;width:100%;padding:0.4rem 0.75rem!important;}
    div.stDownloadButton > button:first-child {background-color:#2b8a3e;color:white;font-weight:bold;border-radius:6px;border:none;}
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

DEVICE_LEDGER = get_device_ledger()

fp_js = """
(async () => {
    let ip = '';
    try {
        const r = await fetch('https://api.ipify.org?format=json');
        const d = await r.json();
        ip = d.ip || '';
    } catch (e) {}
    const hw = [
        ip,
        navigator.platform || '',
        screen.width + 'x' + screen.height + 'x' + screen.colorDepth,
        navigator.hardwareConcurrency || '',
        navigator.deviceMemory || '',
        Intl.DateTimeFormat().resolvedOptions().timeZone || ''
    ].join('|');
    let ls_f = 0;
    let ls_p = 'no';
    try {
        ls_f = parseInt(localStorage.getItem('ts_device_free_v6') || '0', 10) || 0;
        ls_p = localStorage.getItem('ts_device_pro_v6') || 'no';
    } catch (e) {}
    return JSON.stringify({hw: hw, ls_f: ls_f, ls_p: ls_p});
})()
"""

client_info_raw = streamlit_js_eval(js_expressions=fp_js, key="ts_fp_eval_v6")

if "free_used_count" not in st.session_state:
    st.session_state.free_used_count = 0
if "is_pro_user" not in st.session_state:
    st.session_state.is_pro_user = False
if "device_id" not in st.session_state:
    st.session_state.device_id = ""

if client_info_raw and isinstance(client_info_raw, str):
    try:
        info = json.loads(client_info_raw)
        hw_str = info.get("hw", "")
        if hw_str:
            dev_hash = hashlib.sha256(hw_str.encode("utf-8")).hexdigest()[:24]
            st.session_state.device_id = dev_hash
            ledger_rec = DEVICE_LEDGER.get(dev_hash, {"free": 0, "pro": False})
            merged_free = max(
                st.session_state.free_used_count,
                int(info.get("ls_f", 0)),
                int(ledger_rec.get("free", 0)),
            )
            merged_pro = (
                st.session_state.is_pro_user
                or (info.get("ls_p") == "yes")
                or bool(ledger_rec.get("pro", False))
            )
            DEVICE_LEDGER[dev_hash] = {"free": merged_free, "pro": merged_pro}
            if merged_free != st.session_state.free_used_count or merged_pro != st.session_state.is_pro_user:
                st.session_state.free_used_count = merged_free
                st.session_state.is_pro_user = merged_pro
                st.rerun()
    except Exception:
        pass

def sync_device_state(new_free=None, new_pro=None):
    if new_free is not None:
        st.session_state.free_used_count = new_free
    if new_pro is not None:
        st.session_state.is_pro_user = new_pro
    dev_hash = st.session_state.get("device_id", "")
    if dev_hash:
        DEVICE_LEDGER[dev_hash] = {
            "free": st.session_state.free_used_count,
            "pro": st.session_state.is_pro_user,
        }
    try:
        streamlit_js_eval(
            js_expressions=f"try{{localStorage.setItem('ts_device_free_v6','{st.session_state.free_used_count}');localStorage.setItem('ts_device_pro_v6','{'yes' if st.session_state.is_pro_user else 'no'}');}}catch(e){{}}",
            key=f"sync_{int(time.time()*1000)}",
        )
    except Exception:
        pass

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
        sync_device_state(new_pro=True)
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
        ("Regional / Local", "Global / International", "Both"),
        horizontal=True,
    )
    st.markdown("### 💎 Pro Plans (Unlimited)")
    if st.session_state.is_pro_user:
        st.success("✅ **PRO UNLIMITED ACTIVE!**

అన్‌లిమిటెడ్ రిపోర్ట్‌లు పొందవచ్చు.")
    else:
        rem = max(0, 3 - st.session_state.free_used_count)
        if rem > 0:
            st.caption(f"🎁 **Free Trial:** మీకు **{rem} ఉచిత రిపోర్ట్‌లు** మిగిలి ఉన్నాయి.")
        else:
            st.error("🔒 **Free Trial: 0 ఉచిత రిపోర్ట్‌లు మిగిలి ఉన్నాయి!**

ఈ డివైజ్‌కు ఇచ్చిన 3 ఉచిత అవకాశాలు పూర్తయ్యాయి.")
        st.markdown(
            f"• **1 Month:** **₹100/-** 👉 [Pay ₹100]({PAY_1_MONTH_LINK})  
"
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
                sync_device_state(new_pro=True)
                st.rerun()
            elif res_st == "VALID":
                sync_device_state(new_pro=True)
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
        st.markdown("**A to Z Growth Analyzer for YouTube, Instagram & TikTok | Powered by [AIENGTEL.com](https://aiengtel.com)**")
else:
    st.markdown("# 🚀 TrendSutra AI
**A to Z Growth Analyzer for YouTube, Instagram & TikTok | Powered by [AIENGTEL.com](https://aiengtel.com)**")

col1, col2 = st.columns(2)
with col1:
    platform = st.selectbox("Select Platform:", ("YouTube", "Instagram Reels", "TikTok"))
with col2:
    video_url = st.text_input("Channel / Profile / Video Link:", placeholder="https://youtu.be/... లేదా Reel / TikTok లింక్ పేస్ట్ చేయండి")

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
            cr = yt.commentThreads().list(
                part="snippet",
                videoId=m.group(1),
                maxResults=30,
                order="relevance",
                textFormat="plainText",
            ).execute()
            coms = [c["snippet"]["topLevelComment"]["snippet"]["textDisplay"] for c in cr.get("items", ())]
        except Exception:
            coms = ["కామెంట్లు ఆఫ్ చేసి ఉన్నాయి."]
        return (
            f"Title: {sn.get('title')}\nViews: {st_obj.get('viewCount','0')}, Likes: {st_obj.get('likeCount','0')}\n"
            f"Desc: {sn.get('description','')[:600]}\nTags: {sn.get('tags',())}\nComments: {coms}",
            st_obj,
        )
    except Exception as e:
        return None, f"YouTube Error: {str(e)}"

def get_available_models(client):
    try:
        models = []
        for m in client.models.list():
            name = getattr(m, "name", "")
            methods = getattr(m, "supported_generation_methods", []) or []
            if "generateContent" in methods and "flash" in name.lower():
                clean = name.replace("models/", "")
                models.append(clean)
        if models:
            return models[:3]
    except Exception:
        pass
    return ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-3.5-flash-lite"]

def generate_growth_report(platform_name, raw_data, lang, audience):
    prompt = (
        f"Friendly {platform_name} Growth Advisor for TrendSutra AI. Give a 5-section A-to-Z Growth Report in {lang} for {audience}. "
        "Use exact Telugu spelling 'పని 1, పని 2, పని 3'.\n"
        "Sections: 1. Audience Feedback 2. 3 Viral Video Ideas 3. Earning Ideas 4. Title/Description/Tags SEO 5. 30-Day Action Plan.\n"
        f"Data: {raw_data}"
    )
    last_err = "API Key missing in Secrets"
    for key in GEMINI_KEYS:
        if not key:
            continue
        try:
            client = genai.Client(api_key=key)
            models_to_try = get_available_models(client)
            for m in models_to_try:
                try:
                    resp = client.models.generate_content(model=m, contents=prompt)
                    if resp and resp.text:
                        return True, resp.text
                except Exception as e:
                    last_err = str(e)
                    time.sleep(1.5)
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
                        sync_device_state(new_free=st.session_state.free_used_count + 1)
                        time.sleep(0.5)
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
