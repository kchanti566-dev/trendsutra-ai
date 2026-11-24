import hashlib
import os
import re
import time
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
    """<style>#MainMenu,footer,.stDeployButton,div[data-testid="stToolbarActions"]{display:none!important;}header[data-testid="stHeader"]{height:1.5rem!important;background:transparent!important;}.block-container{padding-top:0rem!important;margin-top:-2.2rem!important;}section[data-testid="stSidebar"]>div:first-child{padding-top:0rem!important;margin-top:-1.5rem!important;}div.stButton>button:first-child{background-color:#c92a2a;color:white;font-weight:bold;border-radius:6px;border:none;}div.stDownloadButton>button:first-child{background-color:#2b8a3e;color:white;font-weight:bold;border-radius:6px;border:none;}</style>""",
    unsafe_allow_html=True,
)

GEMINI_KEYS = [
    k
    for k in (
        st.secrets.get("GEMINI_API_KEY", ""),
        st.secrets.get("GEMINI_API_KEY_2", ""),
    )
    if k
]
YOUTUBE_KEY = st.secrets.get("YOUTUBE_API_KEY", "")
RAPIDAPI_KEY = st.secrets.get("RAPIDAPI_API_KEY", "")

GOOGLE_SHEET_API = "https://script.google.com/macros/s/AKfycbzEkkgxBP7aOKIXkEiOG7_rWc0quvnvTVqQDSWUAMk2zOPN7W8Ue_uOPwH7edmJJtEd/exec"
PAY_1_MONTH_LINK = "https://rzp.io/rzp/yop8jYS"
PAY_12_MONTHS_LINK = "https://rzp.io/rzp/sjonGmqw"


@st.cache_resource
def get_device_ledger():
    return {}


DEVICE_LEDGER = get_device_ledger()


def get_server_ip_signature():
    try:
        hdrs = st.context.headers
        ip = (
            hdrs.get("X-Forwarded-For", "")
            .split(",")[0]
            .strip()
            or hdrs.get("X-Real-Ip", "")
            or hdrs.get("Remote-Addr", "")
        )
        lang = hdrs.get("Accept-Language", "")[:15]
        if ip:
            return hashlib.sha256(f"{ip}|{lang}".encode()).hexdigest()[:24]
    except Exception:
        pass
    return ""


js_fp = streamlit_js_eval(
    js_expressions="""(async () => {
        try {
            const c = document.createElement('canvas');
            const gl = c.getContext('webgl') || c.getContext('experimental-webgl');
            let gpu = '';
            if (gl) {
                const dbg = gl.getExtension('WEBGL_debug_renderer_info');
                gpu = dbg ? gl.getParameter(dbg.UNMASKED_RENDERER_WEBGL) : '';
            }
            const raw = [
                screen.width + 'x' + screen.height,
                screen.colorDepth,
                navigator.hardwareConcurrency || '',
                navigator.deviceMemory || '',
                Intl.DateTimeFormat().resolvedOptions().timeZone || '',
                navigator.platform || '',
                gpu
            ].join('|');
            const buf = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(raw));
            const hwHash = Array.from(new Uint8Array(buf)).map(b => b.toString(16).padStart(2, '0')).join('').slice(0, 24);
            const lsVal = parseInt(localStorage.getItem('ts_device_free_v6') || '0', 10) || 0;
            const proVal = localStorage.getItem('ts_device_pro_v6') || '';
            const ckMatch = document.cookie.match(/ts_free_v6=(\d+)/);
            const ckVal = ckMatch ? parseInt(ckMatch[1], 10) : 0;
            return JSON.stringify({hw: hwHash, count: Math.max(lsVal, ckVal), pro: proVal});
        } catch (e) {
            return JSON.stringify({hw: '', count: 0, pro: ''});
        }
    })()""",
    key="ts_hw_sync_v6",
)

if "free_used_count" not in st.session_state:
    st.session_state.free_used_count = 0
if "is_pro_user" not in st.session_state:
    st.session_state.is_pro_user = False
if "device_keys" not in st.session_state:
    st.session_state.device_keys = []

ip_sig = get_server_ip_signature()
hw_sig = ""
browser_count = 0
browser_pro = ""

if js_fp and isinstance(js_fp, str) and js_fp.startswith("{"):
    import json
    try:
        parsed = json.loads(js_fp)
        hw_sig = parsed.get("hw", "")
        browser_count = int(parsed.get("count", 0))
        browser_pro = parsed.get("pro", "")
    except Exception:
        pass

keys_to_check = [k for k in (f"ip:{ip_sig}" if ip_sig else "", f"hw:{hw_sig}" if hw_sig else "") if k]
st.session_state.device_keys = keys_to_check

server_count = max([DEVICE_LEDGER.get(k, 0) for k in keys_to_check] + [0])
true_used = max(st.session_state.free_used_count, browser_count, server_count)

for k in keys_to_check:
    if true_used > DEVICE_LEDGER.get(k, 0):
        DEVICE_LEDGER[k] = true_used

if true_used > st.session_state.free_used_count:
    st.session_state.free_used_count = true_used
    st.rerun()

if browser_pro == "yes" and not st.session_state.is_pro_user:
    st.session_state.is_pro_user = True
    st.rerun()


def sync_device_usage(new_count):
    st.session_state.free_used_count = new_count
    for k in st.session_state.device_keys:
        DEVICE_LEDGER[k] = max(DEVICE_LEDGER.get(k, 0), new_count)
    streamlit_js_eval(
        js_expressions=f"""(() => {{
            localStorage.setItem('ts_device_free_v6', '{new_count}');
            document.cookie = 'ts_free_v6={new_count}; max-age=315360000; path=/; SameSite=Lax';
        }})()""",
        key=f"ls_sync_{int(time.time() * 1000)}",
    )


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
            f"• **1 Month:** **₹100/-** 👉 [Pay ₹100]({PAY_1_MONTH_LINK})  \n• **12"
            f" Months:** **₹1,000/-** 👉 [Pay ₹1,000]({PAY_12_MONTHS_LINK})"
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
                    js_expressions="localStorage.setItem('ts_device_pro_v6', 'yes')",
                    key=f"ls_pro_{int(time.time())}",
                )
                time.sleep(0.6)
                st.rerun()
            elif res_st == "ALREADY_USED":
                st.error(
                    "❌ ఈ Payment ID గరిష్టంగా 3 డివైజ్‌లలో వాడబడింది! admin@aiengtel.com"
                    " కి మెసేజ్ చేయండి."
                )
            else:
                st.error("❌ సరైన Payment ID ఇవ్వండి.")

if os.path.isfile("logo.png"):
    c1, c2 = st.columns((1, 5))
    with c1:
        st.image("logo.png", width=100)
    with c2:
        st.markdown("# TrendSutra AI")
        st.markdown(
            "**A to Z Growth Analyzer for YouTube, Instagram & TikTok | Powered by"
            " [AIENGTEL.com](https://aiengtel.com)**"
        )
else:
    st.markdown(
        "# 🚀 TrendSutra AI\n**A to Z Growth Analyzer for YouTube, Instagram &"
        " TikTok | Powered by [AIENGTEL.com](https://aiengtel.com)**"
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
    last_err = "API Key missing in Secrets"
    for key in GEMINI_KEYS:
        clean_k = key.strip()
        if not clean_k:
            continue
        client = genai.Client(api_key=clean_k)
        flash_models = []
        try:
            for mod in client.models.list():
                m_name = getattr(mod, "name", "").replace("models/", "")
                methods = getattr(mod, "supported_generation_methods", []) or []
                if "flash" in m_name.lower() and "lite" in m_name.lower() and "generateContent" in methods:
                    flash_models.insert(0, m_name)
                elif "flash" in m_name.lower() and "generateContent" in methods:
                    flash_models.append(m_name)
        except Exception:
            pass
        if not flash_models:
            flash_models = ["gemini-3.5-flash-lite", "gemini-3.5-flash", "gemini-2.5-flash-lite"]
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
            f"* **1 Month Unlimited (₹100):** 👉 [Pay ₹100]({PAY_1_MONTH_LINK})\n*"
            f" **12 Months Unlimited (₹1,000):** 👉 [Pay ₹1,000]({PAY_12_MONTHS_LINK})"
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
                        sync_device_usage(st.session_state.free_used_count + 1)
                        time.sleep(0.7)
                        st.rerun()
                else:
                    st.error(res_txt)

if st.session_state.generated_report:
    if isinstance(st.session_state.report_stats, dict):
        m1, m2, m3 = st.columns(3)
        m1.metric(
            "👀 Views", f"{int(st.session_state.report_stats.get('viewCount',0)):,}"
        )
        m2.metric(
            "👍 Likes", f"{int(st.session_state.report_stats.get('likeCount',0)):,}"
        )
        m3.metric(
            "💬 Comments",
            f"{int(st.session_state.report_stats.get('commentCount',0)):,}",
        )
    st.success("✅ Growth Audit Report సిద్ధమైంది!")
    st.download_button(
        "📥 Download Growth Report (.txt)",
        st.session_state.generated_report,
        "TrendSutra_Report.txt",
    )
    st.markdown(st.session_state.generated_report)
