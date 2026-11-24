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

# Hardware / Network / Cross-Browser Device Signature (works across Tabs, Profiles, Incognito & Browsers on same PC/Phone)
def get_hardware_device_id():
    hdrs = {}
    try:
        hdrs = dict(st.context.headers)
    except Exception:
        pass
    ip = hdrs.get("X-Forwarded-For", hdrs.get("X-Real-Ip", "")).split(",")[0].strip()
    plat = hdrs.get("Sec-Ch-Ua-Platform", "")
    mob = hdrs.get("Sec-Ch-Ua-Mobile", "")
    lang = hdrs.get("Accept-Language", "")[:15]
    raw_sig = f"{ip}|{plat}|{mob}|{lang}"
    return "DEV_" + hashlib.sha256(raw_sig.encode("utf-8")).hexdigest()[:20]

HW_DEVICE_ID = get_hardware_device_id()

@st.cache_resource
def get_server_device_ledger():
    return {"free_counts": {}, "pro_devices": set()}

LEDGER = get_server_device_ledger()

# Check Google Sheet backend + Server Ledger for hardware device usage
@st.cache_data(ttl=15, show_spinner=False)
def fetch_remote_device_free(dev_id):
    try:
        r = requests.get(
            f"{GOOGLE_SHEET_API}?dev={dev_id}&action=get",
            headers={"User-Agent": "Mozilla/5.0"},
            allow_redirects=True,
            timeout=6,
        )
        txt = r.text.strip()
        m = re.search(r"FREE_COUNT:(\d+)", txt)
        if m:
            return int(m.group(1))
    except Exception:
        pass
    return 0

def sync_device_free_count(dev_id, new_count):
    LEDGER["free_counts"][dev_id] = max(LEDGER["free_counts"].get(dev_id, 0), new_count)
    fetch_remote_device_free.clear()
    try:
        requests.get(
            f"{GOOGLE_SHEET_API}?dev={dev_id}&action=set&count={new_count}",
            headers={"User-Agent": "Mozilla/5.0"},
            allow_redirects=True,
            timeout=6,
        )
    except Exception:
        pass

# Browser-level 3-layer persistence (localStorage + Cookie + JS Canvas/Screen Hardware Hash)
js_read_expr = """
(function() {
    var f = parseInt(localStorage.getItem('ts_device_free_v6') || '0', 10);
    var m = document.cookie.match(/ts_device_free_v6=(\d+)/);
    if (m) f = Math.max(f, parseInt(m[1], 10));
    var p = (localStorage.getItem('ts_device_pro_v6') === 'yes' || document.cookie.indexOf('ts_device_pro_v6=yes') !== -1) ? 'yes' : 'no';
    var gpu = '';
    try {
        var c = document.createElement('canvas');
        var gl = c.getContext('webgl') || c.getContext('experimental-webgl');
        if (gl) {
            var dbg = gl.getExtension('WEBGL_debug_renderer_info');
            if (dbg) gpu = gl.getParameter(dbg.UNMASKED_RENDERER_WEBGL);
        }
    } catch(e) {}
    var hw = screen.width + 'x' + screen.height + '|' + (navigator.hardwareConcurrency || 0) + '|' + Intl.DateTimeFormat().resolvedOptions().timeZone + '|' + gpu;
    return JSON.stringify({free: f, pro: p, hw: hw});
})()
"""

client_state_raw = streamlit_js_eval(js_expressions=js_read_expr, key="ts_hw_sync_v6")

if "free_used_count" not in st.session_state:
    st.session_state.free_used_count = 0
if "is_pro_user" not in st.session_state:
    st.session_state.is_pro_user = False
if "full_hw_key" not in st.session_state:
    st.session_state.full_hw_key = HW_DEVICE_ID

# Combine Network/OS ID + Hardware GPU/Screen ID so even separate Chrome Profiles on same laptop match 100%!
combined_hw_id = HW_DEVICE_ID
js_free_val = 0
js_pro_val = "no"

if client_state_raw and isinstance(client_state_raw, str):
    import json
    try:
        parsed = json.loads(client_state_raw)
        js_free_val = int(parsed.get("free", 0))
        js_pro_val = parsed.get("pro", "no")
        hw_str = parsed.get("hw", "")
        if hw_str:
            combined_hw_id = "HW_" + hashlib.sha256(f"{HW_DEVICE_ID}|{hw_str}".encode("utf-8")).hexdigest()[:20]
            st.session_state.full_hw_key = combined_hw_id
    except Exception:
        pass

active_hw_id = st.session_state.full_hw_key
server_free_val = max(
    LEDGER["free_counts"].get(HW_DEVICE_ID, 0),
    LEDGER["free_counts"].get(active_hw_id, 0),
    fetch_remote_device_free(active_hw_id),
)

effective_free_used = max(st.session_state.free_used_count, js_free_val, server_free_val)
if effective_free_used > st.session_state.free_used_count:
    st.session_state.free_used_count = effective_free_used
    LEDGER["free_counts"][HW_DEVICE_ID] = effective_free_used
    LEDGER["free_counts"][active_hw_id] = effective_free_used

if js_pro_val == "yes" or HW_DEVICE_ID in LEDGER["pro_devices"] or active_hw_id in LEDGER["pro_devices"]:
    st.session_state.is_pro_user = True

def write_browser_lock(free_cnt, is_pro):
    pro_str = "yes" if is_pro else "no"
    js_write = f"""
    localStorage.setItem('ts_device_free_v6', '{free_cnt}');
    document.cookie = 'ts_device_free_v6={free_cnt}; path=/; max-age=315360000; SameSite=Lax';
    if ('{pro_str}' === 'yes') {{
        localStorage.setItem('ts_device_pro_v6', 'yes');
        document.cookie = 'ts_device_pro_v6=yes; path=/; max-age=315360000; SameSite=Lax';
    }}
    """
    streamlit_js_eval(js_expressions=js_write, key=f"ts_write_{int(time.time()*1000)}")

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
            f"{GOOGLE_SHEET_API}?pid={clean_pid}&dev={active_hw_id}",
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
        LEDGER["pro_devices"].add(HW_DEVICE_ID)
        LEDGER["pro_devices"].add(active_hw_id)
        write_browser_lock(st.session_state.free_used_count, True)
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
        rem = max(0, 3 - st.session_state.free_used_count)
        if rem == 0:
            st.error("🔒 **Free Trial: 0 ఉచిత రిపోర్ట్‌లు మిగిలి ఉన్నాయి!**\n\nఈ డివైజ్‌కు ఇచ్చిన 3 ఉచిత అవకాశాలు పూర్తయ్యాయి.")
        else:
            st.caption(f"🎁 **Free Trial:** మీకు **{rem} ఉచిత రిపోర్ట్‌లు** మిగిలి ఉన్నాయి.")
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
                LEDGER["pro_devices"].add(HW_DEVICE_ID)
                LEDGER["pro_devices"].add(active_hw_id)
                write_browser_lock(st.session_state.free_used_count, True)
                time.sleep(0.6)
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
        sn, st_obj = items[0]["snippet"], items[0]["statistics"]
        coms = []
        try:
            cr = yt.commentThreads().list(
                part="snippet", videoId=m.group(1), maxResults=30, order="relevance", textFormat="plainText"
            ).execute()
            coms = [c["snippet"]["topLevelComment"]["snippet"]["textDisplay"] for c in cr.get("items", [])]
        except Exception:
            coms = ["కామెంట్లు ఆఫ్ చేసి ఉన్నాయి."]
        return (
            f"Title: {sn.get('title')}\nViews: {st_obj.get('viewCount','0')}, Likes: {st_obj.get('likeCount','0')}\n"
            f"Desc: {sn.get('description','')[:600]}\nTags: {sn.get('tags',[])}\nComments: {coms}",
            st_obj,
        )
    except Exception as e:
        return None, f"YouTube Error: {str(e)}"

def get_available_flash_models(client):
    try:
        models = []
        for m in client.models.list():
            name = getattr(m, "name", "")
            methods = getattr(m, "supported_generation_methods", []) or []
            if "flash" in name.lower() and ("generateContent" in methods or not methods):
                clean = name.replace("models/", "")
                if "lite" in clean:
                    models.insert(0, clean)
                else:
                    models.append(clean)
        if models:
            return models[:3]
    except Exception:
        pass
    return ["gemini-2.5-flash-lite", "gemini-2.5-flash"]

def generate_growth_report(platform_name, raw_data, lang, audience):
    prompt = (
        f"Friendly {platform_name} Growth Advisor for TrendSutra AI. Give a 5-section A-to-Z Growth Report in {lang} for {audience}. "
        "Use exact Telugu spelling 'పని 1, పని 2, పని 3'.\n"
        "Sections: 1. Audience Feedback 2. 3 Viral Video Ideas 3. Earning Ideas 4. Title/Description/Tags SEO 5. 30-Day Action Plan.\n"
        f"Data: {raw_data}"
    )
    last_err = "API Key missing in Secrets"
    for attempt in range(2):
        for key in GEMINI_KEYS:
            try:
                client = genai.Client(api_key=key)
                m_list = get_available_flash_models(client)
                for m in m_list:
                    try:
                        resp = client.models.generate_content(model=m, contents=prompt)
                        if resp and resp.text:
                            return True, resp.text
                    except Exception as e:
                        last_err = str(e)
                        time.sleep(1.2)
            except Exception as e:
                last_err = str(e)
    return False, f"⚠️ AI సర్వర్ బిజీగా ఉంది: {last_err[:120]}"

if "generated_report" not in st.session_state:
    st.session_state.generated_report = ""
if "report_stats" not in st.session_state:
    st.session_state.report_stats = None

if st.button("Generate Accurate Growth Report 🔍"):
    # Re-verify hardware lock on click so two tabs open simultaneously cannot bypass the 3-report limit!
    latest_srv_count = max(
        st.session_state.free_used_count,
        LEDGER["free_counts"].get(HW_DEVICE_ID, 0),
        LEDGER["free_counts"].get(active_hw_id, 0),
        fetch_remote_device_free(active_hw_id),
    )
    st.session_state.free_used_count = latest_srv_count

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
                    st.session_state.generated_report, st.session_state.report_stats = res_txt, st_obj
                    if not st.session_state.is_pro_user:
                        new_cnt = st.session_state.free_used_count + 1
                        st.session_state.free_used_count = new_cnt
                        sync_device_free_count(HW_DEVICE_ID, new_cnt)
                        sync_device_free_count(active_hw_id, new_cnt)
                        write_browser_lock(new_cnt, False)
                        time.sleep(0.6)
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
