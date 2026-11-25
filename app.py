import os
import re
import time
import hashlib
import requests
import streamlit as st
from google import genai
from google.genai import types
from googleapiclient.discovery import build

st.set_page_config(
    page_title="TrendSutra AI - Growth Analyzer",
    page_icon="logo.png" if os.path.isfile("logo.png") else "🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""<style>
#MainMenu, footer, .stDeployButton, div[data-testid="stToolbarActions"], div[data-testid="stDecoration"], .viewerBadge_container__1QSob, .viewerBadge_link__1S137 {
    display: none !important;
}
header[data-testid="stHeader"] {
    height: 1.5rem !important;
    background: transparent !important;
}
.block-container {
    padding-top: 0.2rem !important;
    margin-top: -1.8rem !important;
}
section[data-testid="stSidebar"] > div:first-child {
    padding-top: 0.2rem !important;
    margin-top: -1.2rem !important;
}
section[data-testid="stSidebar"] .stMarkdown p {
    margin-bottom: 0.25rem !important;
    font-size: 0.92rem !important;
}
div.stButton > button:first-child {
    background-color: #c92a2a;
    color: white;
    font-weight: bold;
    border-radius: 6px;
    border: none;
    width: 100%;
    padding: 0.45rem 0.75rem;
}
div.stDownloadButton > button:first-child {
    background-color: #2b8a3e;
    color: white;
    font-weight: bold;
    border-radius: 6px;
    border: none;
}
.comment-card {
    background-color: rgba(43, 138, 62, 0.08);
    border-left: 4px solid #2b8a3e;
    padding: 8px 12px;
    margin-bottom: 6px;
    border-radius: 4px;
    font-size: 0.93rem;
}
</style>""", unsafe_allow_html=True)

GEMINI_KEYS = [
    k for k in (
        st.secrets.get("GEMINI_API_KEY", ""),
        st.secrets.get("GEMINI_API_KEY_2", ""),
    ) if k and str(k).strip()
]
YOUTUBE_KEY = st.secrets.get("YOUTUBE_API_KEY", "")

GOOGLE_SHEET_API = "https://script.google.com/macros/s/AKfycbzEkkgxBP7aOKIXkEiOG7_rWc0quvnvTVqQDSWUAMk2zOPN7W8Ue_uOPwH7edmJJtEd/exec"
PAY_1_MONTH_LINK = "https://rzp.io/rzp/yop8jYS"
PAY_12_MONTHS_LINK = "https://rzp.io/rzp/sjonGmqw"


def get_stable_device_id():
    try:
        headers = st.context.headers
        xff = headers.get("X-Forwarded-For", "")
        client_ip = xff.split(",")[0].strip() if xff else ""
        if not client_ip:
            client_ip = headers.get("X-Real-Ip", "")
        ua = headers.get("User-Agent", "")
        os_sig = "win" if "Windows" in ua else ("mac" if "Macintosh" in ua else ("and" if "Android" in ua else ("ios" if "iPhone" in ua or "iPad" in ua else "other")))
        raw = f"{client_ip}|{os_sig}" if client_ip else ua
        return "dev_" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]
    except Exception:
        return "dev_default_guest"


DEVICE_ID = get_stable_device_id()


def get_device_used_count(dev_id):
    try:
        r = requests.get(
            f"{GOOGLE_SHEET_API}?device={dev_id}",
            headers={"User-Agent": "Mozilla/5.0"},
            allow_redirects=True,
            timeout=8,
        )
        txt = r.text.strip()
        if txt.isdigit():
            return min(3, int(txt))
    except Exception:
        pass
    return 0


def increment_device_used_count(dev_id):
    try:
        r = requests.get(
            f"{GOOGLE_SHEET_API}?device={dev_id}&inc=1",
            headers={"User-Agent": "Mozilla/5.0"},
            allow_redirects=True,
            timeout=8,
        )
        txt = r.text.strip()
        if txt.isdigit():
            return min(3, int(txt))
    except Exception:
        pass
    return 3


def log_usage_to_sheet(dev_id, platform_name, url):
    try:
        requests.get(
            GOOGLE_SHEET_API,
            params={"log": "1", "device": dev_id, "platform": platform_name, "url": url},
            headers={"User-Agent": "Mozilla/5.0"},
            allow_redirects=True,
            timeout=6,
        )
    except Exception:
        pass


if "is_pro_user" not in st.session_state:
    st.session_state.is_pro_user = False

if "free_used_count" not in st.session_state:
    st.session_state.free_used_count = get_device_used_count(DEVICE_ID)


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
    if verify_payment_id(url_pid) == "VALID":
        st.session_state.is_pro_user = True

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
        rem = max(0, 3 - min(3, st.session_state.free_used_count))
        if rem > 0:
            st.info(f"🎁 **Free Trial:** మీకు **{rem} ఉచిత రిపోర్ట్‌లు** మిగిలి ఉన్నాయి.")
        else:
            st.error("🔒 **Free Trial: 0 ఉచిత రిపోర్ట్‌లు మిగిలి ఉన్నాయి!**")
        st.markdown(
            f"• **1 Month:** **₹100/-** 👉 [Pay ₹100]({PAY_1_MONTH_LINK})  \n"
            f"• **12 Months:** **₹1,000/-** 👉 [Pay ₹1,000]({PAY_12_MONTHS_LINK})"
        )
        st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
        manual_pid = st.text_input(
            "Payment ID:",
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
                st.rerun()
            elif res_st == "ALREADY_USED":
                st.error("❌ ఈ Payment ID గరిష్టంగా 3 డివైజ్‌లలో వాడబడింది! admin@aiengtel.com కి మెసేజ్ చేయండి.")
            else:
                st.error("❌ సరైన Payment ID ఇవ్వండి.")

if os.path.isfile("logo.png"):
    c1, c2 = st.columns((1, 6))
    with c1:
        st.image("logo.png", width=90)
    with c2:
        st.markdown("# TrendSutra AI")
        st.markdown("**A to Z Growth Analyzer for YouTube, Instagram & TikTok | Powered by [AIENGTEL.com](https://aiengtel.com)**")
else:
    st.markdown("# 🚀 TrendSutra AI\n**A to Z Growth Analyzer for YouTube, Instagram & TikTok | Powered by [AIENGTEL.com](https://aiengtel.com)**")

col1, col2 = st.columns(2)
with col1:
    platform = st.selectbox("Select Platform:", ("YouTube", "Instagram Reels", "TikTok"))
with col2:
    video_url = st.text_input("Channel / Profile / Video Link:", placeholder="https://youtu.be/... లేదా Reel / TikTok లింక్ పేస్ట్ చేయండి")


@st.cache_data(ttl=600, show_spinner=False)
def fetch_youtube_info(url):
    m = re.search(r"(?:v=|\/|live\/|shorts\/)([0-9A-Za-z_-]{11}).*", url)
    if not m:
        return None, "సరైన YouTube వీడియో లింక్ ఇవ్వండి.", []
    try:
        yt = build("youtube", "v3", developerKey=YOUTUBE_KEY)
        vr = yt.videos().list(part="snippet,statistics", id=m.group(1)).execute()
        items = vr.get("items", ())
        if not items:
            return None, "వీడియో వివరాలు దొరకలేదు.", []
        sn, st_obj = items[0]["snippet"], items[0]["statistics"]
        views = int(st_obj.get("viewCount", 0))
        likes = int(st_obj.get("likeCount", 0))
        comments_cnt = int(st_obj.get("commentCount", 0))
        like_pct = round((likes / views * 100), 2) if views > 0 else 0
        comm_pct = round((comments_cnt / views * 100), 3) if views > 0 else 0

        raw_coms = []
        display_coms = []
        try:
            cr = yt.commentThreads().list(
                part="snippet",
                videoId=m.group(1),
                maxResults=40,
                order="relevance",
                textFormat="plainText",
            ).execute()
            for c in cr.get("items", ()):
                top = c["snippet"]["topLevelComment"]["snippet"]
                author = top.get("authorDisplayName", "Viewer")
                text = top.get("textDisplay", "").strip().replace("\n", " ")
                if text:
                    raw_coms.append(f"{author}: {text}")
                    if len(display_coms) < 5:
                        display_coms.append((author, text))
        except Exception:
            raw_coms = ["కామెంట్లు ఆఫ్ చేసి ఉన్నాయి లేదా అందుబాటులో లేవు."]

        summary = (
            f"Title: {sn.get('title')}\n"
            f"Views: {views:,}, Likes: {likes:,} (Like Rate: {like_pct}%), Total Comments: {comments_cnt:,} (Comment Rate: {comm_pct}%)\n"
            f"Description: {sn.get('description', '')[:700]}\n"
            f"Tags: {sn.get('tags', ())}\n"
            f"Top Audience Comments: {raw_coms}"
        )
        return summary, st_obj, display_coms
    except Exception as e:
        return None, f"YouTube Error: {str(e)}", []


@st.cache_resource(show_spinner=False)
def get_best_models(api_key):
    lite_models = []
    flash_models = []
    try:
        client = genai.Client(api_key=api_key)
        for m in client.models.list():
            name = getattr(m, "name", "").replace("models/", "")
            methods = getattr(m, "supported_generation_methods", ()) or ()
            if "generateContent" in methods and "flash" in name and "tts" not in name and "image" not in name and "audio" not in name:
                if "2.0" in name or "1.5" in name or name == "gemini-2.5-flash":
                    continue
                if "lite" in name:
                    lite_models.append(name)
                else:
                    flash_models.append(name)
    except Exception:
        pass
    ordered = lite_models + flash_models
    return ordered if ordered else ["gemini-3.5-flash-lite", "gemini-2.5-flash-lite", "gemini-3.5-flash"]


def clean_advisor_words(text):
    text = text.replace("మెంటర్", "సలహాదారు").replace("స్ట్రాటజిస్ట్", "సలహాదారు")
    text = text.replace("Mentor", "Advisor").replace("Strategist", "Advisor")
    return text


def stream_growth_report(platform_name, raw_data, lang, audience, placeholder):
    prompt = (
        f"You are an experienced, friendly {platform_name} Growth Advisor (సలహాదారు) for TrendSutra AI. "
        f"Write a rich, easy-to-understand, deeply practical A-to-Z Growth Report in {lang} for a {audience} audience. "
        "CRITICAL RULES:\n"
        "- Use simple, everyday spoken words that any creator can immediately understand and apply.\n"
        "- In Telugu, ALWAYS use the exact word 'సలహాదారు' (never use 'మెంటర్' or 'స్ట్రాటజిస్ట్') and use 'పని 1, పని 2, పని 3'.\n"
        "- Do NOT write short 2-line summaries. Give thorough, detailed, actionable advice in every single section.\n"
        "- In Section 2, quote 5 REAL viewer comments from the data word-for-word (with commenter names) and explain what the audience loves or asks for.\n\n"
        "MUST INCLUDE ALL 6 SECTIONS COMPLETELY:\n"
        "### 📊 1. వీడియో పనితీరు & ఎంగేజ్‌మెంట్ విశ్లేషణ (Performance Diagnosis)\n"
        "- Explain Views, Likes %, and Comments % clearly, where viewers drop off, and 3 exact tricks to double engagement.\n"
        "### 💬 2. ఆడియన్స్ ఏం అంటున్నారు? (Real Comments & Replies)\n"
        "- Quote 5 actual comments from the video data with commenter names, explain audience mood, and provide 3 copy-paste reply templates.\n"
        "### 🔥 3. తర్వాత తీయాల్సిన 3 వైరల్ వీడియో ఐడియాలు (3 Viral Follow-Up Ideas)\n"
        "- Give 3 detailed next video ideas with exact 5-second opening Hook lines and Thumbnail text/visual ideas.\n"
        "### 🎯 4. కాపీ-పేస్ట్ SEO మేకోవర్ (Titles, Description & Tags)\n"
        "- Provide 3 high-CTR Titles, a ready-to-paste Description hook, and 15 searchable Tags.\n"
        "### 💰 5. ఆదాయం పెంచుకునే 3 మార్గాలు (Monetization & Brand Earning)\n"
        "- Give 3 practical earning methods suited to this channel's niche.\n"
        "### 📅 6. 30 రోజుల యాక్షన్ ప్లాన్ (Step-by-Step 30-Day Plan)\n"
        "- Break down Week 1, Week 2, Week 3, and Week 4 tasks clearly as పని 1, పని 2, పని 3, పని 4.\n\n"
        f"Video & Audience Data:\n{raw_data}"
    )
    last_err = "API Key missing in Secrets"
    for key in GEMINI_KEYS:
        clean_k = str(key).strip()
        if not clean_k:
            continue
        client = genai.Client(api_key=clean_k)
        models_to_try = get_best_models(clean_k)
        for m in models_to_try:
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
                        full_text += clean_advisor_words(chunk.text)
                        placeholder.markdown(full_text + " ▌")
                if full_text.strip():
                    placeholder.markdown(full_text)
                    return True, full_text
            except Exception as e:
                last_err = str(e)
                continue
    if "429" in last_err or "RESOURCE_EXHAUSTED" in last_err:
        return False, "⚠️ ఈరోజు ఉచిత API కోటా పరిమితి ముగిసింది (429 Quota). దయచేసి కొద్దిసేపటి తర్వాత మళ్ళీ ప్రయత్నించండి లేదా కొత్త API కీ జతచేయండి."
    return False, f"⚠️ AI సర్వర్ బిజీగా ఉంది: {last_err[:120]}"


if "generated_report" not in st.session_state:
    st.session_state.generated_report = ""
if "report_stats" not in st.session_state:
    st.session_state.report_stats = None
if "top_comments" not in st.session_state:
    st.session_state.top_comments = []

if st.button("Generate Accurate Growth Report 🔍"):
    current_used = get_device_used_count(DEVICE_ID)
    st.session_state.free_used_count = current_used

    if not st.session_state.is_pro_user and current_used >= 3:
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
        with st.spinner("వీడియో వివరాలు & కామెంట్లు సేకరిస్తోంది..."):
            if platform == "YouTube":
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
                st.markdown("### 💬 ఆడియన్స్ కామెంట్లు (Top 5 Viewer Comments)")
                for auth, c_txt in disp_coms:
                    st.markdown(f"<div class='comment-card'><b>@{auth}:</b> {c_txt}</div>", unsafe_allow_html=True)

            live_box = st.empty()
            ok, res_txt = stream_growth_report(platform, d_txt, report_lang, target_audience, live_box)
            if ok:
                st.session_state.generated_report = res_txt
                st.session_state.report_stats = st_obj
                st.session_state.top_comments = disp_coms
                log_usage_to_sheet(DEVICE_ID, platform, video_url.strip())
                if not st.session_state.is_pro_user:
                    new_cnt = increment_device_used_count(DEVICE_ID)
                    st.session_state.free_used_count = new_cnt
                st.rerun()
            else:
                live_box.empty()
                st.error(res_txt)

elif st.session_state.generated_report:
    if isinstance(st.session_state.report_stats, dict):
        stats_d = st.session_state.report_stats
        m1, m2, m3 = st.columns(3)
        m1.metric("👀 Views", f"{int(stats_d.get('viewCount', 0)):,}")
        m2.metric("👍 Likes", f"{int(stats_d.get('likeCount', 0)):,}")
        m3.metric("💬 Comments", f"{int(stats_d.get('commentCount', 0)):,}")
    if st.session_state.top_comments:
        st.markdown("### 💬 ఆడియన్స్ కామెంట్లు (Top 5 Viewer Comments)")
        for auth, c_txt in st.session_state.top_comments:
            st.markdown(f"<div class='comment-card'><b>@{auth}:</b> {c_txt}</div>", unsafe_allow_html=True)
    st.success("✅ Growth Audit Report సిద్ధమైంది!")
    st.download_button("📥 Download Growth Report (.txt)", st.session_state.generated_report, "TrendSutra_Report.txt")
    st.markdown(st.session_state.generated_report)
