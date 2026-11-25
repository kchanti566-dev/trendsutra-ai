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
    #MainMenu, footer, .stDeployButton, div[data-testid="stToolbarActions"], div[data-testid="stStatusWidget"], div[data-testid="stDecoration"], [class*="viewerBadge"] {
        display: none !important;
        visibility: hidden !important;
    }
    header[data-testid="stHeader"] {
        height: 0.5rem !important;
        background: transparent !important;
    }
    .block-container {
        padding-top: 0.2rem !important;
        margin-top: -1.5rem !important;
    }
    section[data-testid="stSidebar"] > div:first-child {
        padding-top: 0.2rem !important;
        margin-top: -1.2rem !important;
    }
    section[data-testid="stSidebar"] .stMarkdown p {
        margin-bottom: 0.3rem !important;
        line-height: 1.35 !important;
    }
    section[data-testid="stSidebar"] h3 {
        margin-top: 0.3rem !important;
        margin-bottom: 0.3rem !important;
        font-size: 1.05rem !important;
    }
    section[data-testid="stSidebar"] div[data-testid="stAlert"] {
        padding: 0.45rem 0.65rem !important;
        margin-bottom: 0.4rem !important;
    }
    section[data-testid="stSidebar"] div[data-testid="stTextInput"] {
        margin-top: 0.35rem !important;
        margin-bottom: 0.35rem !important;
    }
    div.stButton > button:first-child {
        background-color: #c92a2a;
        color: white;
        font-weight: bold;
        border-radius: 6px;
        border: none;
        padding: 0.45rem 0.9rem;
    }
    div.stDownloadButton > button:first-child {
        background-color: #2b8a3e;
        color: white;
        font-weight: bold;
        border-radius: 6px;
        border: none;
    }
    .loading-pill {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        background: #1c2536;
        border: 1px solid #3b82f6;
        color: #93c5fd;
        padding: 7px 14px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.92rem;
    }
    .spin-icon {
        display: inline-block;
        animation: spin 1s linear infinite;
    }
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
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


def get_client_device_id():
    try:
        headers = st.context.headers
        xff = headers.get("X-Forwarded-For", "")
        ip = xff.split(",")[0].strip() if xff else headers.get("Remote-Addr", "unknown_ip")
        ua = headers.get("User-Agent", "")
        os_sig = "win" if "Windows" in ua else ("mac" if "Mac" in ua else ("android" if "Android" in ua else ("ios" if "iPhone" in ua or "iPad" in ua else "other")))
        raw = f"{ip}_{os_sig}"
        return "dev_" + hashlib.sha256(raw.encode()).hexdigest()[:16]
    except Exception:
        return "dev_fallback_001"


DEVICE_ID = get_client_device_id()


def get_sheet_device_count(dev_id):
    try:
        r = requests.get(
            f"{GOOGLE_SHEET_API}?device={dev_id}",
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=6,
        )
        txt = r.text.strip()
        if txt.isdigit():
            return min(3, int(txt))
    except Exception:
        pass
    return 0


def increment_sheet_device_count(dev_id):
    try:
        r = requests.get(
            f"{GOOGLE_SHEET_API}?device={dev_id}&inc=1",
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=6,
        )
        txt = r.text.strip()
        if txt.isdigit():
            return min(3, int(txt))
    except Exception:
        pass
    return None


def log_usage_to_sheet(dev_id, plat, url):
    try:
        requests.get(
            GOOGLE_SHEET_API,
            params={"log": "1", "device": dev_id, "platform": plat, "url": url},
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=5,
        )
    except Exception:
        pass


ls_pro = streamlit_js_eval(
    js_expressions="localStorage.getItem('ts_device_pro_v7')", key="ls_get_pro"
)
ls_free = streamlit_js_eval(
    js_expressions="localStorage.getItem('ts_device_free_v7')", key="ls_get_free"
)

if "is_pro_user" not in st.session_state:
    st.session_state.is_pro_user = False

if "free_used_count" not in st.session_state:
    st.session_state.free_used_count = get_sheet_device_count(DEVICE_ID)

if ls_free and str(ls_free).isdigit():
    val = min(3, int(ls_free))
    if val > st.session_state.free_used_count:
        st.session_state.free_used_count = val

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
            timeout=12,
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
            js_expressions="localStorage.setItem('ts_device_pro_v7', 'yes')",
            key="ls_pro_url",
        )
    elif st_val == "ALREADY_USED":
        st.sidebar.error("⚠️ ఈ Payment ID గరిష్టంగా 3 డివైజ్‌లలో వాడబడింది!")

with st.sidebar:
    st.markdown("### 🟢 Settings")
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
        if rem > 0:
            st.info(f"🎁 **Free Trial:** మీకు **{rem} ఉచిత రిపోర్ట్‌లు** మిగిలి ఉన్నాయి.")
        else:
            st.error("🔒 **Free Trial: 0 ఉచిత రిపోర్ట్‌లు మిగిలి ఉన్నాయి!**")
        st.markdown(
            f"• **1 Month:** **₹100/-** 👉 [Pay ₹100]({PAY_1_MONTH_LINK})  \n"
            f"• **12 Months:** **₹1,000/-** 👉 [Pay ₹1,000]({PAY_12_MONTHS_LINK})"
        )
        st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
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
                    js_expressions="localStorage.setItem('ts_device_pro_v7', 'yes')",
                    key=f"ls_pro_{int(time.time())}",
                )
                time.sleep(0.4)
                st.rerun()
            elif res_st == "ALREADY_USED":
                st.error("❌ ఈ Payment ID 3 డివైజ్‌లలో వాడబడింది! admin@aiengtel.com కి మెసేజ్ చేయండి.")
            else:
                st.error("❌ సరైన Payment ID ఇవ్వండి.")


if os.path.isfile("logo.png"):
    c1, c2 = st.columns((1, 6))
    with c1:
        st.image("logo.png", width=85)
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


@st.cache_data(ttl=120, show_spinner=False)
def fetch_youtube_info(url):
    m = re.search(r"(?:v=|\/|live\/|shorts\/)([0-9A-Za-z_-]{11}).*", url)
    if not m:
        return None, "సరైన YouTube వీడియో లింక్ ఇవ్వండి.", []
    try:
        yt = build("youtube", "v3", developerKey=YOUTUBE_KEY)
        vr = yt.videos().list(part="snippet,statistics", id=m.group(1)).execute()
        items = vr.get("items", [])
        if not items:
            return None, "వీడియో వివరాలు దొరకలేదు.", []
        sn, st_obj = items[0]["snippet"], items[0]["statistics"]
        coms = []
        try:
            cr = yt.commentThreads().list(
                part="snippet",
                videoId=m.group(1),
                maxResults=20,
                order="relevance",
                textFormat="plainText",
            ).execute()
            for c in cr.get("items", []):
                top = c["snippet"]["topLevelComment"]["snippet"]
                author = top.get("authorDisplayName", "Viewer")
                text = top.get("textDisplay", "").replace("\n", " ").strip()
                if text:
                    coms.append(f"{author}: {text[:160]}")
        except Exception:
            coms = []
        views = int(st_obj.get("viewCount", 0) or 0)
        likes = int(st_obj.get("likeCount", 0) or 0)
        comments_cnt = int(st_obj.get("commentCount", 0) or 0)
        like_rate = round((likes / views) * 100, 2) if views > 0 else 0
        raw_summary = (
            f"Title: {sn.get('title')}\n"
            f"Channel: {sn.get('channelTitle')}\n"
            f"Views: {views:,}, Likes: {likes:,} (Like Rate: {like_rate}%), Total Comments: {comments_cnt:,}\n"
            f"Description: {sn.get('description', '')[:500]}\n"
            f"Tags: {sn.get('tags', [])[:15]}\n"
            f"Top Viewer Comments: {coms[:10]}"
        )
        return raw_summary, st_obj, coms[:5]
    except Exception as e:
        return None, f"YouTube Error: {str(e)}", []


@st.cache_resource(ttl=3600)
def get_best_models(api_key):
    lite_models = []
    flash_models = []
    try:
        client = genai.Client(api_key=api_key)
        for m in client.models.list():
            name = getattr(m, "name", "").replace("models/", "")
            methods = getattr(m, "supported_actions", None) or getattr(m, "supported_generation_methods", None) or []
            if "generateContent" in methods or not methods:
                if "flash-lite" in name and "1.5" not in name and "2.0" not in name:
                    lite_models.append(name)
                elif "flash" in name and "1.5" not in name and "2.0" not in name:
                    flash_models.append(name)
    except Exception:
        pass
    ordered = lite_models + flash_models
    for fb in ("gemini-2.5-flash-lite", "gemini-3.5-flash-lite", "gemini-2.5-flash"):
        if fb not in ordered:
            ordered.append(fb)
    return ordered[:4]


def clean_advisor_text(txt):
    return (
        txt.replace("మెంటర్", "సలహాదారు")
        .replace("స్ట్రాటజిస్ట్", "సలహాదారు")
        .replace("Mentor", "Advisor")
    )


def stream_growth_report(platform_name, raw_data, lang, audience, top_comments, placeholder):
    comments_block = "\n".join(top_comments) if top_comments else "No public comments available."
    prompt = (
        f"You are a warm, practical {platform_name} Growth Advisor (గ్రోత్ సలహాదారు) at TrendSutra AI. "
        f"Write a complete, detailed, easy-to-understand 6-section A-to-Z Growth Report in {lang} for a {audience} audience.\n"
        "CRITICAL RULES:\n"
        "- Use simple, everyday spoken language (వాడుక భాష) that any creator can immediately understand and apply.\n"
        "- In Telugu, ALWAYS refer to yourself as 'సలహాదారు' (NEVER use 'మెంటర్' or 'స్ట్రాటజిస్ట్').\n"
        "- Use exact Telugu spelling 'పని 1, పని 2, పని 3'.\n"
        f"- In Section 2 ('💬 2. ఆడియన్స్ ఏం అంటున్నారు?'), list the actual Top Viewer Comments below, TRANSLATE each comment naturally into {lang}, explain what viewers really want, and provide 3 copy-paste reply templates.\n"
        "- Write ALL 6 sections completely with rich, actionable examples without cutting off early:\n\n"
        "### 📊 1. వీడియో పనితీరు విశ్లేషణ (Performance Diagnosis)\n"
        "(Analyze Views, Likes, Like Rate %, and why viewers watch or drop off.)\n\n"
        "### 💬 2. ఆడియన్స్ ఏం అంటున్నారు? (Real Comments & Translation)\n"
        f"(Quote & translate these real comments into {lang}, analyze viewer mood, and give 3 ready-to-use replies):\n{comments_block}\n\n"
        "### 🔥 3. తదుపరి 3 వైరల్ వీడియో ఐడియాలు (3 Viral Follow-Up Ideas)\n"
        "(For each idea give: Topic, exact first 5-second Hook line, and Thumbnail text/visual idea.)\n\n"
        "### 🎯 4. కాపీ-పేస్ట్ SEO మెరుగుదల (Titles, Description & Tags)\n"
        "(Give 3 high-CTR Titles, a 3-line SEO Description hook, and 15 searchable Tags.)\n\n"
        "### 💰 5. సంపాదన మార్గాలు (Earning & Brand Blueprint)\n"
        "(Explain 3 practical ways to earn money from this specific topic.)\n\n"
        "### 📅 6. 30 రోజుల కార్యాచరణ ప్రణాళిక (30-Day Action Plan)\n"
        "(Give clear weekly steps using పని 1, పని 2, పని 3, పని 4.)\n\n"
        f"Video Data:\n{raw_data}"
    )

    last_err = "API Key missing in Secrets"
    for key in GEMINI_KEYS:
        client = genai.Client(api_key=key)
        models = get_best_models(key)
        for m in models:
            for retry in range(2):
                try:
                    full_text = ""
                    stream = client.models.generate_content_stream(
                        model=m,
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            temperature=0.8,
                            max_output_tokens=8192,
                        ),
                    )
                    for chunk in stream:
                        if chunk.text:
                            full_text += chunk.text
                            placeholder.markdown(clean_advisor_text(full_text) + " ▌")
                    if full_text.strip():
                        final_clean = clean_advisor_text(full_text)
                        placeholder.markdown(final_clean)
                        return True, final_clean
                except Exception as e:
                    last_err = str(e)
                    if "503" in last_err or "UNAVAILABLE" in last_err:
                        time.sleep(1.5)
                        continue
                    break
    if "429" in last_err or "RESOURCE_EXHAUSTED" in last_err:
        return False, "⚠️ ఉచిత API కీ రోజువారీ పరిమితి ముగిసింది. కొద్దిసేపటి తర్వాత మళ్ళీ ప్రయత్నించండి."
    if "503" in last_err or "UNAVAILABLE" in last_err:
        return False, "⚠️ Google AI సర్వర్ ప్రస్తుతం రద్దీగా ఉంది. దయచేసి 5 సెకన్ల తర్వాత మళ్ళీ బటన్ నొక్కండి."
    return False, f"⚠️ AI సర్వర్ బిజీగా ఉంది: {last_err[:120]}"


if "generated_report" not in st.session_state:
    st.session_state.generated_report = ""
if "report_stats" not in st.session_state:
    st.session_state.report_stats = None

btn_col, status_col = st.columns([2, 3])
with btn_col:
    generate_clicked = st.button("Generate Accurate Growth Report 🔍")
with status_col:
    top_status_box = st.empty()

if generate_clicked:
    if not st.session_state.is_pro_user and st.session_state.free_used_count >= 3:
        st.session_state.generated_report = ""
        st.error("🔒 **మీ 3 ఉచిత రిపోర్ట్‌లు పూర్తయ్యాయి!**")
        st.markdown(
            f"* **1 Month Unlimited (₹100):** 👉 [Pay ₹100]({PAY_1_MONTH_LINK})\n"
            f"* **12 Months Unlimited (₹1,000):** 👉 [Pay ₹1,000]({PAY_12_MONTHS_LINK})"
        )
    elif not video_url.strip():
        st.warning("⚠️ ముందుగా వీడియో లింక్ పేస్ట్ చేయండి.")
    else:
        top_status_box.markdown(
            '<div class="loading-pill"><span class="spin-icon">🔄</span> రిపోర్ట్ లోడ్ అవుతోంది... దయచేసి వేచి ఉండండి (ఆపడానికి పేజీ Refresh చేయండి)</div>',
            unsafe_allow_html=True,
        )
        if platform == "YouTube":
            d_txt, st_obj, top_coms = fetch_youtube_info(video_url.strip())
        else:
            d_txt, st_obj, top_coms = f"{platform} URL: {video_url.strip()}", None, []

        if platform == "YouTube" and not d_txt:
            top_status_box.empty()
            st.error(f"⚠️ {st_obj}")
        else:
            if isinstance(st_obj, dict):
                m1, m2, m3 = st.columns(3)
                m1.metric("👀 Views", f"{int(st_obj.get('viewCount', 0)):,}")
                m2.metric("👍 Likes", f"{int(st_obj.get('likeCount', 0)):,}")
                m3.metric("💬 Comments", f"{int(st_obj.get('commentCount', 0)):,}")

            live_box = st.empty()
            ok, res_txt = stream_growth_report(
                platform, d_txt, report_lang, target_audience, top_coms, live_box
            )
            top_status_box.empty()
            if ok:
                st.session_state.generated_report = res_txt
                st.session_state.report_stats = st_obj
                log_usage_to_sheet(DEVICE_ID, platform, video_url.strip())
                if not st.session_state.is_pro_user:
                    new_cnt = increment_sheet_device_count(DEVICE_ID)
                    if new_cnt is not None:
                        st.session_state.free_used_count = new_cnt
                    else:
                        st.session_state.free_used_count = min(3, st.session_state.free_used_count + 1)
                    streamlit_js_eval(
                        js_expressions=f"localStorage.setItem('ts_device_free_v7', '{st.session_state.free_used_count}')",
                        key=f"ls_f_{int(time.time())}",
                    )
                    time.sleep(0.4)
                    st.rerun()
            else:
                st.session_state.generated_report = ""
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
