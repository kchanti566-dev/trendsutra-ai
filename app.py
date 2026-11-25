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
    #MainMenu, footer, .stDeployButton, div[data-testid="stToolbarActions"],
    div[data-testid="stStatusWidget"], div[data-testid="stDecoration"],
    .viewerBadge_container__1QSob, .viewerBadge_link__1S137 { display: none !important; }
    header[data-testid="stHeader"] { height: 1.2rem !important; background: transparent !important; }
    .block-container { padding-top: 0rem !important; margin-top: -2.0rem !important; }
    section[data-testid="stSidebar"] > div:first-child { padding-top: 0.4rem !important; margin-top: -1.2rem !important; }
    section[data-testid="stSidebar"] .stMarkdown p { margin-bottom: 0.35rem !important; font-size: 0.92rem !important; }
    section[data-testid="stSidebar"] div[data-testid="stSelectbox"],
    section[data-testid="stSidebar"] div[data-testid="stRadio"] { margin-bottom: 0.35rem !important; }
    div.stButton > button:first-child {
        background-color: #c92a2a; color: white; font-weight: bold;
        border-radius: 6px; border: none; width: 100%;
    }
    div.stDownloadButton > button:first-child {
        background-color: #2b8a3e; color: white; font-weight: bold;
        border-radius: 6px; border: none;
    }
    .comment-box {
        background-color: #f8f9fa; border-left: 4px solid #c92a2a;
        padding: 10px 14px; border-radius: 6px; margin-bottom: 12px;
        color: #1f2937; font-size: 0.94rem;
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
YOUTUBE_KEY = st.secrets.get("YOUTUBE_API_KEY", "")
GOOGLE_SHEET_API = "https://script.google.com/macros/s/AKfycbzEkkgxBP7aOKIXkEiOG7_rWc0quvnvTVqQDSWUAMk2zOPN7W8Ue_uOPwH7edmJJtEd/exec"
PAY_1_MONTH_LINK = "https://rzp.io/rzp/yop8jYS"
PAY_12_MONTHS_LINK = "https://rzp.io/rzp/sjonGmqw"


def get_device_fingerprint():
    headers = st.context.headers if hasattr(st, "context") else {}
    xff = headers.get("X-Forwarded-For", "") or headers.get("X-Real-Ip", "")
    client_ip = xff.split(",")[0].strip() if xff else ""
    if not client_ip:
        try:
            client_ip = requests.get("https://api.ipify.org", timeout=4).text.strip()
        except Exception:
            client_ip = "unknown_ip"
    ua = headers.get("User-Agent", "")
    os_sig = "OtherOS"
    for tag in ("Windows NT 10.0", "Windows NT 11.0", "Macintosh", "Android", "iPhone", "iPad", "Linux"):
        if tag in ua:
            os_sig = tag
            break
    raw_sig = f"{client_ip}|{os_sig}"
    return "DEV_" + hashlib.sha256(raw_sig.encode()).hexdigest()[:14].upper()


DEVICE_ID = get_device_fingerprint()


def get_sheet_device_count(dev_id):
    try:
        r = requests.get(
            f"{GOOGLE_SHEET_API}?device={dev_id}",
            headers={"User-Agent": "Mozilla/5.0"},
            allow_redirects=True,
            timeout=8,
        )
        val = r.text.strip()
        if val.isdigit():
            return int(val)
    except Exception:
        pass
    return None


def inc_sheet_device_count(dev_id):
    try:
        r = requests.get(
            f"{GOOGLE_SHEET_API}?device={dev_id}&inc=1",
            headers={"User-Agent": "Mozilla/5.0"},
            allow_redirects=True,
            timeout=8,
        )
        val = r.text.strip()
        if val.isdigit():
            return int(val)
    except Exception:
        pass
    return None


def log_usage_to_sheet(dev_id, plat, link):
    try:
        requests.get(
            GOOGLE_SHEET_API,
            params={"log": "1", "device": dev_id, "platform": plat, "url": link},
            headers={"User-Agent": "Mozilla/5.0"},
            allow_redirects=True,
            timeout=6,
        )
    except Exception:
        pass


ls_free = streamlit_js_eval(js_expressions="localStorage.getItem('ts_dev_free_v9')", key="ls_f_v9")
ls_pro = streamlit_js_eval(js_expressions="localStorage.getItem('ts_dev_pro_v9')", key="ls_p_v9")

if "free_used_count" not in st.session_state:
    sheet_cnt = get_sheet_device_count(DEVICE_ID)
    st.session_state.free_used_count = sheet_cnt if sheet_cnt is not None else 0

if "is_pro_user" not in st.session_state:
    st.session_state.is_pro_user = False

if ls_free and str(ls_free).isdigit() and int(ls_free) > st.session_state.free_used_count:
    st.session_state.free_used_count = int(ls_free)

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
        streamlit_js_eval(js_expressions="localStorage.setItem('ts_dev_pro_v9', 'yes')", key="ls_p_url")
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
        st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
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
                    js_expressions="localStorage.setItem('ts_dev_pro_v9', 'yes')",
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


@st.cache_data(ttl=300, show_spinner=False)
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
        views = int(st_obj.get("viewCount", 0))
        likes = int(st_obj.get("likeCount", 0))
        comments_cnt = int(st_obj.get("commentCount", 0))
        like_rate = round((likes / views * 100), 2) if views > 0 else 0
        raw_comments = []
        display_comments = []
        try:
            cr = (
                yt.commentThreads()
                .list(
                    part="snippet",
                    videoId=m.group(1),
                    maxResults=40,
                    order="relevance",
                    textFormat="plainText",
                )
                .execute()
            )
            for idx, c in enumerate(cr.get("items", [])):
                top = c["snippet"]["topLevelComment"]["snippet"]
                author = top.get("authorDisplayName", "Viewer")
                txt = top.get("textDisplay", "").strip()
                if txt:
                    raw_comments.append(f"{author}: {txt}")
                    if len(display_comments) < 5:
                        display_comments.append(f"**{author}:** {txt[:220]}")
        except Exception:
            raw_comments = ["కామెంట్లు ఆఫ్ చేసి ఉన్నాయి."]

        summary = (
            f"Title: {sn.get('title')}\n"
            f"Channel: {sn.get('channelTitle')}\n"
            f"Views: {views:,}, Likes: {likes:,} (Like Rate: {like_rate}%), Comments: {comments_cnt:,}\n"
            f"Description: {sn.get('description', '')[:800]}\n"
            f"Tags: {sn.get('tags', [])[:20]}\n"
            f"Top Audience Comments ({len(raw_comments)}): {raw_comments[:25]}"
        )
        return summary, st_obj, display_comments
    except Exception as e:
        return None, f"YouTube Error: {str(e)}", []


@st.cache_resource(show_spinner=False)
def get_client(api_key):
    return genai.Client(api_key=api_key)


@st.cache_data(ttl=3600, show_spinner=False)
def get_active_models(api_key):
    preferred = []
    try:
        client = get_client(api_key)
        all_m = [
            m.name.replace("models/", "")
            for m in client.models.list()
            if "generateContent" in getattr(m, "supported_actions", [])
        ]
        for m in all_m:
            if "flash" in m and "2.5-flash" != m and "2.0" not in m and "1.5" not in m:
                preferred.append(m)
        preferred.sort(key=lambda x: (0 if "lite" in x else 1, x))
    except Exception:
        pass
    for fallback in ("gemini-3.5-flash-lite", "gemini-3.5-flash", "gemini-2.5-flash-lite"):
        if fallback not in preferred:
            preferred.append(fallback)
    return preferred


def clean_advisor_text(text):
    for bad in ("మెంటర్", "స్ట్రాటజిస్ట్", "Mentor", "Strategist"):
        rep = "సలహాదారు" if bad in ("మెంటర్", "స్ట్రాటజిస్ట్") else "Growth Advisor"
        text = text.replace(bad, rep)
    return text


def stream_growth_report(platform_name, raw_data, lang, audience, placeholder):
    prompt = f"""You are a friendly, experienced {platform_name} Growth Advisor (సలహాదారు) talking directly to a creator in simple, everyday {lang} for a {audience} audience.
Write a detailed, practical, high-value Growth Report covering ALL 6 sections below completely.
Rules:
- Use simple, easy-to-understand everyday words (no heavy formal words).
- Never use the word 'మెంటర్' or 'Mentor'; always address yourself as a friendly 'సలహాదారు' (Advisor).
- Quote 2 or 3 real viewer comments from the data and explain what the audience truly feels.
- Give deep, actionable examples, exact hook lines, and copy-paste templates so the creator feels this report is truly worth it.
- Use exact Telugu spelling 'పని 1, పని 2, పని 3' in the action plan.

Sections to write completely:
### 1. 📊 వీడియో పనితీరు విశ్లేషణ (Performance & Engagement Diagnosis)
### 2. 💬 ఆడియన్స్ మనసులో ఏముంది? (Real Viewer Comment Insights & Reply Templates)
### 3. 🔥 తదుపరి తీయాల్సిన 3 వైరల్ వీడియో ఐడియాలు (3 Viral Follow-Up Ideas with 5-Sec Hook & Thumbnail)
### 4. 🎯 కాపీ-పేస్ట్ SEO మెరుగుదల (3 High-CTR Titles, Description Hook & 15 Tags)
### 5. 💰 ఆదాయ మార్గాలు (Monetization & Brand Earning Blueprint)
### 6. 📅 30 రోజుల కార్యాచరణ ప్రణాళిక (Step-by-Step 30-Day Action Plan)

Video & Audience Data:
{raw_data}"""

    last_err = "API Key missing"
    for key in GEMINI_KEYS:
        client = get_client(key)
        models = get_active_models(key)
        for m in models:
            try:
                full_text = ""
                response_stream = client.models.generate_content_stream(
                    model=m,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.85,
                        max_output_tokens=8192,
                    ),
                )
                for chunk in response_stream:
                    if chunk.text:
                        full_text += clean_advisor_text(chunk.text)
                        placeholder.markdown(full_text + " ▌")
                if full_text.strip():
                    placeholder.markdown(full_text)
                    return True, full_text
            except Exception as e:
                last_err = str(e)
                continue
    if "429" in last_err or "RESOURCE_EXHAUSTED" in last_err:
        return False, "⚠️ ఉచిత AI పరిమితి (Quota) ప్రస్తుతానికి పూర్తయింది. దయచేసి 1 నిమిషం తర్వాత ప్రయత్నించండి."
    return False, f"⚠️ AI సర్వర్ బిజీగా ఉంది: {last_err[:120]}"


if "generated_report" not in st.session_state:
    st.session_state.generated_report = ""
if "report_stats" not in st.session_state:
    st.session_state.report_stats = None
if "top_comments" not in st.session_state:
    st.session_state.top_comments = []

if st.button("Generate Accurate Growth Report 🔍"):
    current_used = get_sheet_device_count(DEVICE_ID)
    if current_used is not None and current_used > st.session_state.free_used_count:
        st.session_state.free_used_count = current_used

    if not st.session_state.is_pro_user and st.session_state.free_used_count >= 3:
        st.session_state.generated_report = ""
        st.session_state.top_comments = []
        st.error("🔒 **ఈ డివైజ్‌లో మీ 3 ఉచిత రిపోర్ట్‌లు పూర్తయ్యాయి!**")
        st.markdown(
            f"* **1 Month Unlimited (₹100):** 👉 [Pay ₹100]({PAY_1_MONTH_LINK})\n"
            f"* **12 Months Unlimited (₹1,000):** 👉 [Pay ₹1,000]({PAY_12_MONTHS_LINK})"
        )
    elif not video_url.strip():
        st.warning("⚠️ ముందుగా వీడియో లింక్ పేస్ట్ చేయండి.")
    else:
        st.session_state.generated_report = ""
        st.session_state.top_comments = []
        if platform == "YouTube":
            with st.spinner("వీడియో వివరాలు & కామెంట్లు సేకరిస్తోంది..."):
                d_txt, st_obj, disp_coms = fetch_youtube_info(video_url.strip())
        else:
            d_txt, st_obj, disp_coms = f"{platform} URL: {video_url.strip()}", None, []

        if platform == "YouTube" and not d_txt:
            st.error(f"⚠️ {st_obj}")
        else:
            if isinstance(st_obj, dict):
                m1, m2, m3 = st.columns(3)
                m1.metric("👀 Views", f"{int(st_obj.get('viewCount', 0)):,}")
                m2.metric("👍 Likes", f"{int(st_obj.get('likeCount', 0)):,}")
                m3.metric("💬 Comments", f"{int(st_obj.get('commentCount', 0)):,}")
            if disp_coms:
                st.markdown("#### 💬 ఆడియన్స్ కామెంట్లు (Top Viewer Comments)")
                st.markdown(
                    "<div class='comment-box'>" + "<br>".join(disp_coms) + "</div>",
                    unsafe_allow_html=True,
                )
            live_box = st.empty()
            ok, res_txt = stream_growth_report(platform, d_txt, report_lang, target_audience, live_box)
            if ok:
                st.session_state.generated_report = res_txt
                st.session_state.report_stats = st_obj
                st.session_state.top_comments = disp_coms
                log_usage_to_sheet(DEVICE_ID, platform, video_url.strip())
                if not st.session_state.is_pro_user:
                    new_cnt = inc_sheet_device_count(DEVICE_ID)
                    st.session_state.free_used_count = new_cnt if new_cnt is not None else (st.session_state.free_used_count + 1)
                    streamlit_js_eval(
                        js_expressions=f"localStorage.setItem('ts_dev_free_v9', '{st.session_state.free_used_count}')",
                        key=f"ls_inc_{int(time.time())}",
                    )
                    time.sleep(0.4)
                    st.rerun()
            else:
                live_box.empty()
                st.error(res_txt)

elif st.session_state.generated_report:
    if isinstance(st.session_state.report_stats, dict):
        m1, m2, m3 = st.columns(3)
        m1.metric("👀 Views", f"{int(st.session_state.report_stats.get('viewCount', 0)):,}")
        m2.metric("👍 Likes", f"{int(st.session_state.report_stats.get('likeCount', 0)):,}")
        m3.metric("💬 Comments", f"{int(st.session_state.report_stats.get('commentCount', 0)):,}")
    if st.session_state.top_comments:
        st.markdown("#### 💬 ఆడియన్స్ కామెంట్లు (Top Viewer Comments)")
        st.markdown(
            "<div class='comment-box'>" + "<br>".join(st.session_state.top_comments) + "</div>",
            unsafe_allow_html=True,
        )
    st.success("✅ Growth Audit Report సిద్ధమైంది!")
    st.download_button(
        "📥 Download Growth Report (.txt)",
        st.session_state.generated_report,
        "TrendSutra_Report.txt",
    )
    st.markdown(st.session_state.generated_report)
