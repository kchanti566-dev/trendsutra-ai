import os
import re
import time
import hashlib
import requests
import streamlit as st
from streamlit_js_eval import streamlit_js_eval
from google import genai
from google.genai import types
from googleapiclient.discovery import build

st.set_page_config(
    page_title="TrendSutra AI - Growth Analyzer",
    page_icon="logo.png" if os.path.isfile("logo.png") else "🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """<style>
    #MainMenu, footer, .stDeployButton, div[data-testid="stToolbarActions"], div[data-testid="stDecoration"] {display: none !important;}
    header[data-testid="stHeader"] {height: 1.2rem !important; background: transparent !important;}
    .block-container {padding-top: 0.4rem !important; margin-top: -1.8rem !important; padding-bottom: 1rem !important;}
    section[data-testid="stSidebar"] > div:first-child {padding-top: 0.4rem !important; margin-top: -1.4rem !important;}
    section[data-testid="stSidebar"] .stMarkdown p {margin-bottom: 0.25rem !important; line-height: 1.3 !important;}
    section[data-testid="stSidebar"] h3 {margin-top: 0.35rem !important; margin-bottom: 0.25rem !important; font-size: 1.05rem !important;}
    section[data-testid="stSidebar"] div[data-testid="stSelectbox"], section[data-testid="stSidebar"] div[data-testid="stRadio"] {margin-bottom: 0.2rem !important;}
    div.stButton > button:first-child {background-color: #c92a2a; color: white; font-weight: bold; border-radius: 6px; border: none; width: 100%;}
    div.stDownloadButton > button:first-child {background-color: #2b8a3e; color: white; font-weight: bold; border-radius: 6px; border: none;}
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

hw_sig = streamlit_js_eval(
    js_expressions="navigator.platform + '|' + screen.width + 'x' + screen.height + '|' + (navigator.hardwareConcurrency||4)",
    key="ts_hw_sig_v1",
)
ls_free = streamlit_js_eval(
    js_expressions="localStorage.getItem('ts_device_free_v8')",
    key="ts_ls_free_v8",
)
ls_pro = streamlit_js_eval(
    js_expressions="localStorage.getItem('ts_device_pro_v8')",
    key="ts_ls_pro_v8",
)


@st.cache_data(ttl=3600, show_spinner=False)
def get_public_ip():
    try:
        r = requests.get("https://api.ipify.org", timeout=1.2)
        if r.status_code == 200 and r.text.strip():
            return r.text.strip()
    except Exception:
        pass
    return "local_net"


def get_device_id():
    ip_val = get_public_ip()
    hw_val = str(hw_sig) if hw_sig and str(hw_sig) != "None" else "default_hw"
    raw = f"{ip_val}::{hw_val}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


@st.cache_data(ttl=120, show_spinner=False)
def fetch_sheet_device_count(dev_id):
    try:
        r = requests.get(f"{GOOGLE_SHEET_API}?device={dev_id}", timeout=2.5)
        txt = r.text.strip()
        if txt.isdigit():
            return int(txt)
    except Exception:
        pass
    return 0


def increment_sheet_device_count(dev_id):
    try:
        r = requests.get(f"{GOOGLE_SHEET_API}?device={dev_id}&inc=1", timeout=3.5)
        fetch_sheet_device_count.clear()
        txt = r.text.strip()
        if txt.isdigit():
            return int(txt)
    except Exception:
        pass
    return None


def log_usage_to_sheet(dev_id, platform_name, url_str):
    try:
        requests.get(
            GOOGLE_SHEET_API,
            params={
                "log": "1",
                "device": dev_id,
                "platform": platform_name,
                "url": url_str[:250],
            },
            timeout=2.0,
        )
    except Exception:
        pass


device_id = get_device_id()

if "free_used_count" not in st.session_state:
    st.session_state.free_used_count = 0
if "is_pro_user" not in st.session_state:
    st.session_state.is_pro_user = False
if "sheet_checked_dev" not in st.session_state:
    st.session_state.sheet_checked_dev = ""

local_c = int(ls_free) if (ls_free and str(ls_free).isdigit()) else 0
if st.session_state.sheet_checked_dev != device_id:
    sheet_c = fetch_sheet_device_count(device_id)
    st.session_state.sheet_checked_dev = device_id
    best_c = max(st.session_state.free_used_count, local_c, sheet_c)
    if best_c != st.session_state.free_used_count:
        st.session_state.free_used_count = best_c
elif local_c > st.session_state.free_used_count:
    st.session_state.free_used_count = local_c

if ls_pro == "yes" and not st.session_state.is_pro_user:
    st.session_state.is_pro_user = True


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
            timeout=7,
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
            key="ls_pro_url_v8",
        )
    elif st_val == "ALREADY_USED":
        st.sidebar.error("⚠️ ఈ Payment ID గరిష్టంగా 3 డివైజ్‌లలో వాడబడింది!")

with st.sidebar:
    st.markdown("### 🌍 Settings")
    report_lang = st.selectbox(
        "Report Language / భాష:",
        ("Telugu (తెలుగు)", "English (Global)", "Tenglish"),
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
        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
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
                time.sleep(0.2)
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


@st.cache_data(ttl=300, show_spinner=False)
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
        like_rate = round((likes / views * 100), 2) if views > 0 else 0
        comm_rate = round((comments_cnt / views * 100), 2) if views > 0 else 0
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
                c["snippet"]["topLevelComment"]["snippet"]["textDisplay"][:160]
                for c in cr.get("items", [])
            ]
        except Exception:
            coms = ["కామెంట్లు ఆఫ్ చేసి ఉన్నాయి."]
        summary = (
            f"Title: {sn.get('title')}\n"
            f"Channel: {sn.get('channelTitle')}\n"
            f"Views: {views:,} | Likes: {likes:,} ({like_rate}% Like Rate) | Comments: {comments_cnt:,} ({comm_rate}% Comment Rate)\n"
            f"Description: {sn.get('description', '')[:500]}\n"
            f"Tags: {sn.get('tags', [])[:15]}\n"
            f"Audience Comments: {coms}"
        )
        return summary, st_obj
    except Exception as e:
        return None, f"YouTube Error: {str(e)}"


@st.cache_resource(show_spinner=False)
def get_fast_models(api_key):
    client = genai.Client(api_key=api_key)
    lite_models = []
    flash_models = []
    try:
        for mod in client.models.list():
            name = getattr(mod, "name", "").replace("models/", "")
            methods = getattr(mod, "supported_generation_methods", []) or []
            if "generateContent" not in methods:
                continue
            if any(bad in name for bad in ("2.5-flash", "2.0", "1.5", "1.0", "pro", "vision", "embedding")):
                if "2.5-flash-lite" not in name:
                    continue
            if "flash-lite" in name:
                lite_models.append(name)
            elif "flash" in name:
                flash_models.append(name)
    except Exception:
        pass
    ordered = list(dict.fromkeys(lite_models + flash_models + ["gemini-3.5-flash-lite", "gemini-2.5-flash-lite", "gemini-3.5-flash"]))
    return ordered[:4]


def generate_growth_report_stream(platform_name, raw_data, lang, audience, placeholder):
    prompt = (
        f"You are an experienced, warm, practical human {platform_name} Growth Mentor speaking directly to a creator on TrendSutra AI. "
        f"Write a rich, deeply detailed, practical A-to-Z Growth Audit Report in {lang} tailored for a {audience} audience. "
        "Avoid robotic filler; talk like a real human strategist giving honest, actionable advice based on the exact numbers and comments below. "
        "Whenever you number action steps in Telugu, strictly write 'పని 1', 'పని 2', 'పని 3' (never write 'చర్య').\n\n"
        "Structure the report clearly into these 6 detailed sections:\n"
        "1. 📊 **Performance & Engagement Diagnosis (లోతైన విశ్లేషణ):** Analyze the exact Views, Like-to-View %, and Comment-to-View %, and explain honestly what is working and what is holding this video back.\n"
        "2. 💬 **Real Audience Psychology & Comment Strategy (ఆడియన్స్ మనస్తత్వం):** Summarize what viewers loved or asked in the comments, and give 2 ready-to-paste pinned/reply comment templates to boost algorithm engagement.\n"
        "3. 🔥 **3 Fresh Viral Follow-Up Video Ideas (తదుపరి 3 వైరల్ వీడియో ఐడియాలు):** Give 3 distinct next-video concepts with exact first-5-second Hooks and Thumbnail text/visual ideas.\n"
        "4. 🎯 **Copy-Paste SEO Makeover (టైటిల్, డిస్క్రిప్షన్ & ట్యాగ్స్):** Provide 3 high-CTR clickable titles, a strong first-2-lines SEO description, and 15 high-search tags.\n"
        "5. 💰 **Monetization & Brand Earning Blueprint (సంపాదన మార్గాలు):** Suggest 3 realistic ways this creator can earn money from this niche (AdSense, Affiliate, Brand Sponsorships).\n"
        "6. 📅 **Step-by-Step 30-Day Action Plan (30 రోజుల కార్యాచరణ ప్రణాళిక):** Clear weekly milestones using 'పని 1, పని 2, పని 3' format.\n\n"
        f"Live Creator Data:\n{raw_data}"
    )
    last_err = "API Key missing in Secrets"
    for key in GEMINI_KEYS:
        client = genai.Client(api_key=key)
        models_to_try = get_fast_models(key)
        for m in models_to_try:
            try:
                full_text = ""
                response_stream = client.models.generate_content_stream(
                    model=m,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.85,
                        max_output_tokens=2000,
                    ),
                )
                for chunk in response_stream:
                    if chunk.text:
                        full_text += chunk.text
                        placeholder.markdown(full_text + " ▌")
                if full_text.strip():
                    placeholder.markdown(full_text)
                    return True, full_text
            except Exception as e:
                last_err = str(e)
                continue
    if "429" in last_err or "RESOURCE_EXHAUSTED" in last_err:
        return False, "⚠️ మీ ప్రస్తుత ఉచిత Gemini API కీ రోజువారీ పరిమితి (Quota) ముగిసింది. దయచేసి కొత్త API కీ లేదా Billing ఆన్ చేయండి."
    if "503" in last_err or "UNAVAILABLE" in last_err:
        return False, "⚠️ Google AI సర్వర్‌పై తాత్కాలిక రద్దీ ఉంది — దయచేసి 5 సెకన్ల తర్వాత మళ్ళీ బటన్ నొక్కండి."
    return False, f"⚠️ AI సర్వర్ తాత్కాలికంగా బిజీగా ఉంది: {last_err[:120]}"


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
        st.session_state.generated_report = ""
        if platform == "YouTube":
            d_txt, st_obj = fetch_youtube_info(video_url.strip())
        else:
            d_txt, st_obj = f"{platform} URL: {video_url.strip()}", None

        if platform == "YouTube" and not d_txt:
            st.error(f"⚠️ {st_obj}")
        else:
            if isinstance(st_obj, dict):
                m1, m2, m3 = st.columns(3)
                m1.metric("👀 Views", f"{int(st_obj.get('viewCount', 0)):,}")
                m2.metric("👍 Likes", f"{int(st_obj.get('likeCount', 0)):,}")
                m3.metric("💬 Comments", f"{int(st_obj.get('commentCount', 0)):,}")
            stream_box = st.empty()
            stream_box.info("⚡ రిపోర్ట్ ప్రత్యక్షంగా టైప్ అవుతోంది...")
            ok, res_txt = generate_growth_report_stream(
                platform, d_txt, report_lang, target_audience, stream_box
            )
            if ok:
                st.session_state.generated_report = res_txt
                st.session_state.report_stats = st_obj
                log_usage_to_sheet(device_id, platform, video_url.strip())
                if not st.session_state.is_pro_user:
                    new_val = increment_sheet_device_count(device_id)
                    st.session_state.free_used_count = (
                        new_val if new_val is not None else (st.session_state.free_used_count + 1)
                    )
                    streamlit_js_eval(
                        js_expressions=f"localStorage.setItem('ts_device_free_v8', '{st.session_state.free_used_count}')",
                        key=f"ls_f_{int(time.time())}",
                    )
                    time.sleep(0.2)
                    st.rerun()
            else:
                stream_box.empty()
                st.error(res_txt)

elif st.session_state.generated_report:
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
