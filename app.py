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

st.markdown("""
<style>
#MainMenu, footer, .stDeployButton, div[data-testid="stToolbarActions"],
div[data-testid="stDecoration"], div[data-testid="stStatusWidget"],
[class*="viewerBadge_container"], [class*="viewerBadge_link"] {
    display: none !important;
    visibility: hidden !important;
}
header[data-testid="stHeader"] {
    height: 0.5rem !important;
    background: transparent !important;
}
.block-container {
    padding-top: 0.5rem !important;
    padding-bottom: 1rem !important;
    margin-top: -1.5rem !important;
}
section[data-testid="stSidebar"] > div:first-child {
    padding-top: 0.4rem !important;
    padding-bottom: 0.5rem !important;
    margin-top: -1rem !important;
}
section[data-testid="stSidebar"] .stMarkdown p {
    margin-bottom: 0.25rem !important;
    font-size: 0.9rem !important;
}
section[data-testid="stSidebar"] h3 {
    margin-top: 0.35rem !important;
    margin-bottom: 0.25rem !important;
    font-size: 1.05rem !important;
}
div.stButton > button:first-child {
    background-color: #c92a2a;
    color: white;
    font-weight: bold;
    border-radius: 6px;
    border: none;
    padding: 0.45rem 1rem;
}
div.stButton > button:first-child:hover {
    background-color: #a61e1e;
    color: white;
}
div.stDownloadButton > button:first-child {
    background-color: #2b8a3e;
    color: white;
    font-weight: bold;
    border-radius: 6px;
    border: none;
}
@keyframes ts-spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}
.ts-loading-pill {
    display: inline-flex;
    align-items: center;
    gap: 10px;
    background: #1c2536;
    border: 1px solid #3b82f6;
    color: #93c5fd;
    padding: 7px 14px;
    border-radius: 8px;
    font-size: 0.9rem;
    font-weight: 600;
    margin-top: 2px;
}
.ts-spinner {
    width: 16px;
    height: 16px;
    border: 2.5px solid #3b82f6;
    border-top: 2.5px solid #ffffff;
    border-radius: 50%;
    animation: ts-spin 0.8s linear infinite;
    display: inline-block;
}
</style>
""", unsafe_allow_html=True)

GEMINI_KEYS = [
    k.strip()
    for k in (
        st.secrets.get("GEMINI_API_KEY", ""),
        st.secrets.get("GEMINI_API_KEY_2", ""),
        st.secrets.get("GEMINI_API_KEY_3", ""),
    )
    if str(k).strip()
]
YOUTUBE_KEY = str(st.secrets.get("YOUTUBE_API_KEY", "")).strip()
RAPIDAPI_KEY = str(st.secrets.get("RAPIDAPI_API_KEY", "")).strip()

GOOGLE_SHEET_API = "https://script.google.com/macros/s/AKfycbzEkkgxBP7aOKIXkEiOG7_rWc0quvnvTVqQDSWUAMk2zOPN7W8Ue_uOPwH7edmJJtEd/exec"
PAY_1_MONTH_LINK = "https://rzp.io/rzp/yop8jYS"
PAY_12_MONTHS_LINK = "https://rzp.io/rzp/sjonGmqw"


def get_stable_device_id():
    try:
        headers = st.context.headers
        xff = headers.get("X-Forwarded-For", "") or headers.get("X-Real-Ip", "")
        client_ip = xff.split(",")[0].strip() if xff else ""
        ua = headers.get("User-Agent", "")
        lang = headers.get("Accept-Language", "")
        os_sig = "win" if "Windows" in ua else ("mac" if "Mac" in ua else ("and" if "Android" in ua else ("ios" if "iPhone" in ua or "iPad" in ua else "oth")))
        if client_ip and client_ip not in ("127.0.0.1", "::1", "localhost"):
            raw = f"{client_ip}|{os_sig}|{lang[:12]}"
        else:
            raw = f"local|{os_sig}|{ua[:40]}|{lang[:12]}"
        return "dev_" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]
    except Exception:
        return "dev_default_user"


DEVICE_ID = get_stable_device_id()


def sheet_get_device_count(dev_id):
    try:
        res = requests.get(
            f"{GOOGLE_SHEET_API}?device={dev_id}&t={int(time.time())}",
            headers={"User-Agent": "Mozilla/5.0"},
            allow_redirects=True,
            timeout=6,
        )
        txt = res.text.strip()
        if txt.isdigit():
            return min(3, int(txt))
    except Exception:
        pass
    return None


def sheet_inc_device_count(dev_id):
    try:
        res = requests.get(
            f"{GOOGLE_SHEET_API}?device={dev_id}&inc=1&t={int(time.time())}",
            headers={"User-Agent": "Mozilla/5.0"},
            allow_redirects=True,
            timeout=6,
        )
        txt = res.text.strip()
        if txt.isdigit():
            return min(3, int(txt))
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
            headers={"User-Agent": "Mozilla/5.0"},
            allow_redirects=True,
            timeout=4,
        )
    except Exception:
        pass


if "is_pro_user" not in st.session_state:
    st.session_state.is_pro_user = False

if "free_used_count" not in st.session_state:
    sheet_cnt = sheet_get_device_count(DEVICE_ID)
    st.session_state.free_used_count = sheet_cnt if sheet_cnt is not None else 0
else:
    if not st.session_state.is_pro_user:
        sheet_cnt = sheet_get_device_count(DEVICE_ID)
        if sheet_cnt is not None and sheet_cnt > st.session_state.free_used_count:
            st.session_state.free_used_count = sheet_cnt


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
    if st_val in ("VALID", "OWNER_VALID"):
        st.session_state.is_pro_user = True
    elif st_val == "ALREADY_USED":
        st.sidebar.error("⚠️ ఈ Payment ID గరిష్టంగా 3 డివైజ్‌లలో వాడబడింది!")

with st.sidebar:
    st.markdown("### 🌍 Settings")
    report_lang = st.selectbox(
        "Report Language / భాష:",
        ("Telugu (తెలుగు)", "English (Global)", "Tenglish"),
        label_visibility="visible",
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
        st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
        manual_pid = st.text_input(
            "🔑 Payment ID:",
            placeholder="pay_P9x82kLm01",
            label_visibility="collapsed",
        )
        if st.button("Unlock with Payment ID 🔓"):
            res_st = verify_payment_id(manual_pid)
            if res_st in ("OWNER_VALID", "VALID"):
                st.session_state.is_pro_user = True
                st.rerun()
            elif res_st == "ALREADY_USED":
                st.error("❌ ఈ Payment ID గరిష్టంగా 3 డివైజ్‌లలో వాడబడింది! admin@aiengtel.com కి మెసేజ్ చేయండి.")
            else:
                st.error("❌ సరైన Payment ID ఇవ్వండి.")


if os.path.isfile("logo.png"):
    c1, c2 = st.columns([1, 5])
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


@st.cache_data(ttl=600, show_spinner=False)
def fetch_youtube_info(url):
    m = re.search(r"(?:v=|\/|live\/|shorts\/)([0-9A-Za-z_-]{11}).*", url)
    if not m:
        return None, None, [], "సరైన YouTube వీడియో లింక్ ఇవ్వండి."
    try:
        yt = build("youtube", "v3", developerKey=YOUTUBE_KEY)
        vr = yt.videos().list(part="snippet,statistics", id=m.group(1)).execute()
        items = vr.get("items", [])
        if not items:
            return None, None, [], "వీడియో వివరాలు దొరకలేదు."
        sn = items[0]["snippet"]
        st_obj = items[0]["statistics"]
        views = int(st_obj.get("viewCount", 0))
        likes = int(st_obj.get("likeCount", 0))
        comments_cnt = int(st_obj.get("commentCount", 0))
        like_rate = round((likes / views) * 100, 2) if views > 0 else 0
        comment_rate = round((comments_cnt / views) * 100, 3) if views > 0 else 0

        raw_comments = []
        try:
            cr = yt.commentThreads().list(
                part="snippet",
                videoId=m.group(1),
                maxResults=25,
                order="relevance",
                textFormat="plainText",
            ).execute()
            for item in cr.get("items", []):
                top_c = item["snippet"]["topLevelComment"]["snippet"]
                author = top_c.get("authorDisplayName", "Viewer")
                text = top_c.get("textDisplay", "").strip().replace("\n", " ")
                if text:
                    raw_comments.append(f"{author}: {text[:220]}")
        except Exception:
            raw_comments = []

        comments_block = "\n".join([f"- {c}" for c in raw_comments[:15]]) if raw_comments else "కామెంట్లు ఆఫ్ చేసి ఉన్నాయి లేదా ఇంకా కామెంట్లు రాలేదు."
        summary_data = (
            f"Channel: {sn.get('channelTitle', '')}\n"
            f"Title: {sn.get('title', '')}\n"
            f"Views: {views:,} | Likes: {likes:,} (Like Rate: {like_rate}%) | Comments: {comments_cnt:,} (Comment Rate: {comment_rate}%)\n"
            f"Description: {sn.get('description', '')[:700]}\n"
            f"Tags: {sn.get('tags', [])[:15]}\n"
            f"Real Viewer Comments:\n{comments_block}"
        )
        return summary_data, st_obj, raw_comments[:6], None
    except Exception as e:
        return None, None, [], f"YouTube Error: {str(e)}"


@st.cache_resource(show_spinner=False)
def get_active_models(api_key):
    try:
        client = genai.Client(api_key=api_key)
        all_m = [
            m.name.replace("models/", "")
            for m in client.models.list()
            if "generateContent" in (m.supported_actions or [])
            and "flash" in m.name.lower()
            and "image" not in m.name.lower()
            and "audio" not in m.name.lower()
        ]
        lite_m = [m for m in all_m if "lite" in m.lower()]
        std_m = [m for m in all_m if "lite" not in m.lower()]
        ordered = lite_m + std_m
        if ordered:
            return ordered[:4]
    except Exception:
        pass
    return ["gemini-2.5-flash-lite", "gemini-2.5-flash", "gemini-3.5-flash-lite"]


def clean_advisor_terms(text):
    for bad in ("మెంటర్", "స్ట్రాటజిస్ట్", "కోచ్"):
        text = text.replace(bad, "సలహాదారు")
    return text


def build_rich_prompt(platform_name, raw_data, lang, audience):
    if "Telugu" in lang:
        lang_rule = (
            "Write the ENTIRE report in warm, encouraging, easy-to-understand everyday Telugu (సరళమైన వాడుక తెలుగు). "
            "CRITICAL: Translate all real viewer comments into natural Telugu inside Section 2 so the creator can easily read them in Telugu! "
            "Use exact spelling 'పని 1, పని 2, పని 3' in the action plan. Never use words like 'మెంటర్' or 'స్ట్రాటజిస్ట్'—always use 'సలహాదారు'."
        )
    elif "Tenglish" in lang:
        lang_rule = (
            "Write the ENTIRE report in friendly, motivating Tenglish (Telugu written in English letters). "
            "Translate any non-English viewer comments into easy Tenglish/English inside Section 2. "
            "Always act as a warm human 'Advisor / Salahadaru'."
        )
    else:
        lang_rule = (
            "Write the ENTIRE report in warm, encouraging, plain everyday English. "
            "Translate all real viewer comments into clear English inside Section 2. "
            "Always act as a supportive human Growth Advisor."
        )

    return f"""You are a warm, encouraging, experienced human {platform_name} Growth Advisor (సలహాదారు) for TrendSutra AI.
Your goal is to make the creator feel genuinely appreciated, confident, and excited while giving them a deeply detailed, practical, step-by-step A-to-Z Growth Report that feels worth every rupee.

TONE & PRAISE RULE (VERY IMPORTANT):
- Start the report with a warm, heartfelt appreciation paragraph praising the creator's effort, storytelling, presentation, and potential based on their real video title, topic, and engagement numbers! Make them feel proud of what they built before giving gentle, constructive improvements.
- Write in rich, thorough detail (around 1,000 to 1,400 words) so the user never feels the text is short or generic. Give real examples, exact scripts/hooks, and clear reasoning in every section.
- {lang_rule}
- Target Audience Focus: {audience}

MUST INCLUDE ALL 6 SECTIONS BELOW IN FULL DETAIL (DO NOT STOP EARLY):

### 🌟 1. క్రియేటర్ అభినందన & వీడియో పనితీరు విశ్లేషణ (Creator Appreciation & Deep Performance Diagnosis)
- Heartfelt, specific praise for what the creator did brilliantly in this video/content (topic choice, energy, presentation, audience connection).
- Honest, easy-to-understand breakdown of their Views, Likes (Like-to-View %), and Comments (Comment-to-View %), explaining what is working well and where small tweaks can double their reach.

### 💬 2. ఆడియన్స్ ఏం అంటున్నారు? (Real Audience Comments Translated & Reply Templates)
- List 4 to 5 real viewer comments from the data below, **translated into {lang}** (with original commenter name if available), and explain the emotion/demand behind each comment.
- Provide **3 ready-to-copy pinned/reply comment templates** the creator can paste right now to boost the algorithm.

### 🔥 3. తదుపరి 3 వైరల్ వీడియో ఐడియాలు (3 High-Potential Follow-Up Video Ideas)
- Give 3 specific follow-up video concepts tailored to this exact niche.
- For EACH of the 3 ideas, include:
  1. **Video Concept & Why It Will Go Viral**
  2. **Exact First 5-Second Opening Hook (మొదటి 5 సెకన్ల డైలాగ్)**
  3. **Eye-Catching Thumbnail Idea (థంబ్‌నెయిల్ డిజైన్ & టెక్స్ట్)**

### 🎯 4. కాపీ-పేస్ట్ SEO మేకోవర్ (High-CTR Titles, Description & Tags)
- **3 High-CTR Title Options** (curiosity + emotion driven, ready to copy-paste).
- **Optimized Video Description Hook** (first 3 lines written ready to paste).
- **15 Searchable Keywords / Tags** separated by commas.

### 💰 5. ఆదాయం & బ్రాండ్ డీల్స్ ప్లాన్ (Monetization & Earning Blueprint)
- Explain 3 realistic ways this creator can earn money from this exact content style (AdSense optimization, Affiliate products, Sponsored/Brand collaborations) with actionable steps.

### 📅 6. 30 రోజుల కార్యాచరణ ప్రణాళిక (Step-by-Step 30-Day Action Plan)
- Give a clear, motivating 4-week roadmap using `పని 1`, `పని 2`, `పని 3`, `పని 4` with specific daily/weekly habits so the creator knows exactly what to do starting tomorrow morning.

CONTENT DATA TO ANALYZE:
{raw_data}
"""


def stream_growth_report(platform_name, raw_data, lang, audience, placeholder):
    if not GEMINI_KEYS:
        return False, "⚠️ Streamlit Secrets లో GEMINI_API_KEY అందుబాటులో లేదు."

    prompt = build_rich_prompt(platform_name, raw_data, lang, audience)
    last_err = "AI సర్వర్ అందుబాటులో లేదు"

    for key in GEMINI_KEYS:
        client = genai.Client(api_key=key)
        models_to_try = get_active_models(key)
        for m in models_to_try:
            try:
                full_text = ""
                response_stream = client.models.generate_content_stream(
                    model=m,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.82,
                        max_output_tokens=8192,
                    ),
                )
                for chunk in response_stream:
                    if chunk and chunk.text:
                        full_text += clean_advisor_terms(chunk.text)
                        placeholder.markdown(full_text + " ▌")
                if full_text.strip():
                    placeholder.markdown(full_text)
                    return True, full_text
            except Exception as e:
                last_err = str(e)
                continue

    if "429" in last_err or "RESOURCE_EXHAUSTED" in last_err:
        return False, "⚠️ నేటి ఉచిత AI కోటా పూర్తయింది. దయచేసి కొద్దిసేపటి తర్వాత మళ్ళీ ప్రయత్నించండి."
    return False, f"⚠️ AI సర్వర్ ప్రస్తుతం బిజీగా ఉంది. దయచేసి మళ్ళీ ప్రయత్నించండి ({last_err[:80]})"


if "generated_report" not in st.session_state:
    st.session_state.generated_report = ""
if "report_stats" not in st.session_state:
    st.session_state.report_stats = None

btn_col, status_col = st.columns([1.3, 2.7])
with btn_col:
    generate_clicked = st.button("Generate Accurate Growth Report 🔍")
with status_col:
    loading_slot = st.empty()

if generate_clicked:
    if not st.session_state.is_pro_user:
        latest_cnt = sheet_get_device_count(DEVICE_ID)
        if latest_cnt is not None:
            st.session_state.free_used_count = latest_cnt

    if not st.session_state.is_pro_user and st.session_state.free_used_count >= 3:
        st.session_state.generated_report = ""
        st.error("🔒 **మీ 3 ఉచిత రిపోర్ట్‌లు పూర్తయ్యాయి!**")
        st.markdown(
            f"* **1 Month Unlimited (₹100):** 👉 [Pay ₹100]({PAY_1_MONTH_LINK})\n"
            f"* **12 Months Unlimited (₹1,000):** 👉 [Pay ₹1,000]({PAY_12_MONTHS_LINK})"
        )
    elif not video_url.strip():
        st.warning("⚠️ ముందుగా వీడియో లేదా ప్రొఫైల్ లింక్ పేస్ట్ చేయండి.")
    else:
        loading_slot.markdown(
            '<div class="ts-loading-pill"><span class="ts-spinner"></span>'
            '<span>రిపోర్ట్ లోడ్ అవుతోంది... దయచేసి వేచి ఉండండి (ఆపడానికి పేజీ Refresh చేయండి)</span></div>',
            unsafe_allow_html=True,
        )
        clean_url = video_url.strip()
        if platform == "YouTube":
            d_txt, st_obj, _, err_msg = fetch_youtube_info(clean_url)
        else:
            d_txt = (
                f"Platform: {platform}\nProfile / Video Link: {clean_url}\n"
                "Note: Analyze this creator's link niche, audience expectations, hook strategy, and growth potential in full detail."
            )
            st_obj, err_msg = None, None

        if platform == "YouTube" and err_msg:
            loading_slot.empty()
            st.error(f"⚠️ {err_msg}")
        else:
            if isinstance(st_obj, dict):
                m1, m2, m3 = st.columns(3)
                m1.metric("👀 Views", f"{int(st_obj.get('viewCount', 0)):,}")
                m2.metric("👍 Likes", f"{int(st_obj.get('likeCount', 0)):,}")
                m3.metric("💬 Comments", f"{int(st_obj.get('commentCount', 0)):,}")

            stream_box = st.empty()
            ok, res_txt = stream_growth_report(platform, d_txt, report_lang, target_audience, stream_box)
            loading_slot.empty()

            if ok:
                st.session_state.generated_report = res_txt
                st.session_state.report_stats = st_obj
                log_usage_to_sheet(DEVICE_ID, platform, clean_url)
                if not st.session_state.is_pro_user:
                    new_cnt = sheet_inc_device_count(DEVICE_ID)
                    if new_cnt is not None:
                        st.session_state.free_used_count = new_cnt
                    else:
                        st.session_state.free_used_count = min(3, st.session_state.free_used_count + 1)
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
