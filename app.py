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
    initial_sidebar_state="expanded"
)

st.markdown("""<style>
#MainMenu, footer, .stDeployButton, div[data-testid="stToolbarActions"], div[data-testid="stStatusWidget"], div[data-testid="stDecoration"], a[href*="streamlit.io"], div[class*="viewerBadge"] {display: none !important; visibility: hidden !important;}
header[data-testid="stHeader"] {height: 1.5rem !important; background: transparent !important;}
.block-container {padding-top: 0rem !important; margin-top: -2.2rem !important;}
section[data-testid="stSidebar"] > div:first-child {padding-top: 0rem !important; margin-top: -1.4rem !important;}
section[data-testid="stSidebar"] .stMarkdown {margin-bottom: -0.35rem !important;}
section[data-testid="stSidebar"] div[data-testid="stSelectbox"], section[data-testid="stSidebar"] div[data-testid="stRadio"] {margin-bottom: -0.45rem !important;}
section[data-testid="stSidebar"] div[data-testid="stTextInput"] {margin-top: 0.45rem !important; margin-bottom: -0.2rem !important;}
div.stButton > button:first-child {background-color: #c92a2a; color: white; font-weight: bold; border-radius: 6px; border: none; padding: 0.45rem 1.1rem;}
div.stDownloadButton > button:first-child {background-color: #2b8a3e; color: white; font-weight: bold; border-radius: 6px; border: none; padding: 0.45rem 1.1rem;}
.loading-pill {display: inline-flex; align-items: center; gap: 8px; background: #fff3bf; color: #5c3c00; border: 1px solid #fcc419; padding: 7px 14px; border-radius: 6px; font-weight: 600; font-size: 0.9rem; margin-top: 2px;}
.spin-icon {display: inline-block; animation: spin 1s linear infinite;}
@keyframes spin {100% {transform: rotate(360deg);}}
</style>""", unsafe_allow_html=True)

GEMINI_KEYS = [k.strip() for k in (st.secrets.get("GEMINI_API_KEY", ""), st.secrets.get("GEMINI_API_KEY_2", "")) if k and k.strip()]
YOUTUBE_KEY = str(st.secrets.get("YOUTUBE_API_KEY", "")).strip()
GOOGLE_SHEET_API = "https://script.google.com/macros/s/AKfycbzEkkgxBP7aOKIXkEiOG7_rWc0quvnvTVqQDSWUAMk2zOPN7W8Ue_uOPwH7edmJJtEd/exec"
PAY_1_MONTH_LINK = "https://rzp.io/rzp/yop8jYS"
PAY_12_MONTHS_LINK = "https://rzp.io/rzp/sjonGmqw"
MAX_FREE = 3

def get_stable_device_id():
    try:
        hdrs = dict(st.context.headers) if hasattr(st, "context") and hasattr(st.context, "headers") else {}
    except Exception:
        hdrs = {}
    fwd = hdrs.get("X-Forwarded-For", hdrs.get("x-forwarded-for", ""))
    client_ip = fwd.split(",")[0].strip() if fwd else hdrs.get("X-Real-Ip", hdrs.get("x-real-ip", "unknown_ip"))
    ua = hdrs.get("User-Agent", hdrs.get("user-agent", ""))
    clean_ua = re.sub(r"(Chrome|Edg|Safari|Firefox)/[0-9.]+", r"\1", ua)
    raw = f"{client_ip}|{clean_ua}"
    return "DEV_" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]

DEVICE_ID = get_stable_device_id()

def sheet_get_device_count(dev_id):
    try:
        r = requests.get(f"{GOOGLE_SHEET_API}?device={dev_id}&t={int(time.time())}", headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        txt = r.text.strip()
        if txt.isdigit():
            return min(MAX_FREE, int(txt))
    except Exception:
        pass
    return None

def sheet_inc_device_count(dev_id):
    try:
        r = requests.get(f"{GOOGLE_SHEET_API}?device={dev_id}&inc=1&t={int(time.time())}", headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        txt = r.text.strip()
        if txt.isdigit():
            return min(MAX_FREE, int(txt))
    except Exception:
        pass
    return None

def log_usage_to_sheet(dev_id, plat, url):
    try:
        requests.get(GOOGLE_SHEET_API, params={"log": "1", "device": dev_id, "platform": plat, "url": url[:250]}, headers={"User-Agent": "Mozilla/5.0"}, timeout=6)
    except Exception:
        pass

if "is_pro_user" not in st.session_state:
    st.session_state.is_pro_user = False
if "local_used" not in st.session_state:
    st.session_state.local_used = 0

live_sheet_used = sheet_get_device_count(DEVICE_ID)
if live_sheet_used is not None:
    st.session_state.local_used = max(st.session_state.local_used, live_sheet_used)
used_count = min(MAX_FREE, st.session_state.local_used)

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
        res = requests.get(f"{GOOGLE_SHEET_API}?pid={clean_pid}&t={int(time.time())}", headers={"User-Agent": "Mozilla/5.0"}, allow_redirects=True, timeout=12)
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
    if verify_payment_id(url_pid) in ("VALID", "OWNER_VALID"):
        st.session_state.is_pro_user = True

with st.sidebar:
    st.markdown("### 🌍 Settings")
    report_lang = st.selectbox("Report Language / భాష:", ("Telugu (తెలుగు)", "English (Global)", "Tenglish"))
    target_audience = st.radio("Target Audience:", ("Regional", "Global", "Both"), horizontal=True)
    st.markdown("---")
    st.markdown("### 💎 Pro Plans (Unlimited)")
    if st.session_state.is_pro_user:
        st.success("✅ **PRO UNLIMITED ACTIVE!**")
    else:
        rem = max(0, MAX_FREE - used_count)
        if rem > 0:
            st.info(f"🎁 **Free Trial:** మీకు **{rem} ఉచిత రిపోర్ట్‌లు** మిగిలి ఉన్నాయి.")
        else:
            st.error("🔒 **Free Trial:** మీకు **0 ఉచిత రిపోర్ట్‌లు** మిగిలి ఉన్నాయి.")
        st.markdown(f"• **1 Month:** **₹100/-** 👉 [Pay ₹100]({PAY_1_MONTH_LINK})  \n• **12 Months:** **₹1,000/-** 👉 [Pay ₹1,000]({PAY_12_MONTHS_LINK})")
        manual_pid = st.text_input("Payment ID", placeholder="pay_P9x82kLm01", label_visibility="collapsed")
        if st.button("Unlock with Payment ID 🔓"):
            res_st = verify_payment_id(manual_pid)
            if res_st in ("OWNER_VALID", "VALID"):
                st.session_state.is_pro_user = True
                st.rerun()
            elif res_st == "ALREADY_USED":
                st.error("❌ ఈ Payment ID 3 డివైజ్‌లలో వాడబడింది!")
            else:
                st.error("❌ సరైన Payment ID ఇవ్వండి.")

if os.path.isfile("logo.png"):
    c1, c2 = st.columns((1, 6))
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
    video_url = st.text_input("Channel / Profile / Video Link:", placeholder="https://youtu.be/... లేదా Reel / TikTok లింక్ పేస్ట్ చేయండి")

@st.cache_data(ttl=300, show_spinner=False)
def fetch_youtube_info(url):
    m = re.search(r"(?:v=|\/|live\/|shorts\/)([0-9A-Za-z_-]{11}).*", url)
    if not m:
        return None, None, "సరైన YouTube వీడియో లింక్ ఇవ్వండి."
    try:
        yt = build("youtube", "v3", developerKey=YOUTUBE_KEY)
        vr = yt.videos().list(part="snippet,statistics", id=m.group(1)).execute()
        items = vr.get("items", [])
        if not items:
            return None, None, "వీడియో వివరాలు దొరకలేదు."
        sn, st_obj = items[0]["snippet"], items[0]["statistics"]
        coms = []
        try:
            cr = yt.commentThreads().list(part="snippet", videoId=m.group(1), maxResults=25, order="relevance", textFormat="plainText").execute()
            for c in cr.get("items", []):
                top = c["snippet"]["topLevelComment"]["snippet"]
                author = top.get("authorDisplayName", "Viewer")
                txt = top.get("textDisplay", "").strip().replace("\n", " ")
                if txt:
                    coms.append(f"{author}: {txt[:220]}")
        except Exception:
            pass
        com_block = "\n".join(coms) if coms else "కామెంట్లు లేవు."
        summary = (
            f"Channel: {sn.get('channelTitle','')}\n"
            f"Title: {sn.get('title','')}\n"
            f"Views: {st_obj.get('viewCount','0')}, Likes: {st_obj.get('likeCount','0')}, CommentsCount: {st_obj.get('commentCount','0')}\n"
            f"Description: {sn.get('description','')[:1000]}\n"
            f"Tags: {sn.get('tags',[])[:20]}\n"
            f"Real Viewer Comments:\n{com_block}"
        )
        return summary, st_obj, None
    except Exception as e:
        return None, None, f"YouTube Error: {str(e)}"

@st.cache_resource(show_spinner=False)
def get_active_models(api_key):
    client = genai.Client(api_key=api_key)
    lite_models, std_models = [], []
    try:
        for m in client.models.list():
            name = getattr(m, "name", "").replace("models/", "")
            methods = getattr(m, "supported_generation_methods", []) or []
            if "generateContent" in methods and "gemini" in name and "flash" in name:
                if any(x in name for x in ("2.0", "1.5", "1.0", "vision", "audio", "image", "tts", "thinking")):
                    continue
                if "lite" in name:
                    lite_models.append(name)
                else:
                    std_models.append(name)
    except Exception:
        pass
    ordered = sorted(lite_models, reverse=True) + sorted(std_models, reverse=True)
    for fb in ("gemini-2.5-flash-lite", "gemini-3.5-flash-lite", "gemini-2.5-flash", "gemini-3.5-flash"):
        if fb not in ordered:
            ordered.append(fb)
    return ordered

def clean_advisor_terms(text):
    for bad in ("మెంటర్", "స్ట్రాటజిస్ట్", "mentor", "Mentor", "strategist", "Strategist"):
        text = text.replace(bad, "సలహాదారు")
    return text

def build_prompt(platform_name, raw_data, lang, audience):
    return f"""You are a warm, encouraging human growth advisor ('సలహాదారు' in Telugu) for TrendSutra AI.
Write a deeply detailed, friendly, easy-to-understand 6-section A-to-Z Growth Report in {lang} tailored for a {audience} audience.
STRICT RULES:
1. Never use the words 'మెంటర్', 'స్ట్రాటజిస్ట్', 'mentor', or 'strategist'. Always use 'సలహాదారు' (or 'advisor' in English).
2. Keep language simple, warm, and everyday—avoid stiff academic or complex English jargon so any creator understands 100% immediately.
3. Make the report rich and thorough (1,100 to 1,500 words) with clear bullet points, real examples, and ready-to-use scripts.
4. Translate all real viewer comments accurately into {lang} inside Section 2.
5. Use exact Telugu spelling 'పని 1, పని 2, పని 3' if writing in Telugu.
6. Do NOT stop early—complete ALL 6 sections thoroughly through the end of Section 6.

Include these exact 6 sections:
## 🎬 1. మీ వీడియో కథ & క్రియేటర్ అభినందన (Video Story Recap & Creator Praise)
- Start with heartfelt praise for the creator's effort, topic choice, presentation, and achievement.
- Retell the story or core message of this video clearly based on the title, description, and comments so the creator feels you truly watched and understood their work.
- Explain what is working well right now (views, likes, engagement ratio).

## 💬 2. ఆడియన్స్ ఏం అంటున్నారు? (Translated Real Viewer Comments & Replies)
- Pick 4 to 5 real comments from the provided data, translate each one naturally into {lang} with the commenter's name, and explain what the audience loves or asks for.
- Provide 3 warm, copy-paste reply templates the creator can pin or reply with today.

## 🔥 3. తర్వాత తీయాల్సిన 3 వైరల్ వీడియో ఐడియాలు (Next 3 Viral Video Ideas)
- Give 3 fresh follow-up video ideas inspired by this video's audience interest.
- For each idea, provide: Video Concept, exact 5-second Opening Hook dialogue, and Thumbnail visual idea.

## 🎯 4. కాపీ-పేస్ట్ SEO మేకోవర్ (Titles, Description & Tags)
- 3 High-CTR clickable titles in {lang}.
- A ready-to-paste first 3 lines of Description with strong call-to-action.
- 15 searchable YouTube/Social tags separated by commas.

## 💰 5. ఆదాయ మార్గాలు (Monetization & Brand Earning Ideas)
- 3 practical ways this channel can earn more money right now (AdSense optimization, Affiliate products, Local/National Brand sponsorships).

## 📅 6. 30 రోజుల కార్యాచరణ ప్రణాళిక (Step-by-Step 30-Day Action Plan)
- Clear week-by-week action steps (Week 1 to Week 4) with simple tasks (పని 1, పని 2, పని 3...) that anyone can follow easily.

Video & Audience Data:
{raw_data}"""

if "generated_report" not in st.session_state:
    st.session_state.generated_report = ""
if "report_stats" not in st.session_state:
    st.session_state.report_stats = None

btn_col, load_col = st.columns((1.6, 3.4))
with btn_col:
    run_clicked = st.button("Generate Accurate Growth Report 🔍")
with load_col:
    loader_box = st.empty()

if run_clicked:
    latest_used = sheet_get_device_count(DEVICE_ID)
    if latest_used is not None:
        st.session_state.local_used = max(st.session_state.local_used, latest_used)
    used_now = min(MAX_FREE, st.session_state.local_used)

    if not st.session_state.is_pro_user and used_now >= MAX_FREE:
        st.session_state.generated_report = ""
        st.error("🔒 **మీ 3 ఉచిత రిపోర్ట్‌లు పూర్తయ్యాయి!** అన్‌లిమిటెడ్ రిపోర్ట్‌ల కోసం క్రింది ప్లాన్‌ను ఎంచుకోండి:")
        st.markdown(f"• **1 Month Unlimited (₹100/-):** 👉 [Pay ₹100]({PAY_1_MONTH_LINK})  \n• **12 Months Unlimited (₹1,000/-):** 👉 [Pay ₹1,000]({PAY_12_MONTHS_LINK})")
    elif not video_url.strip():
        st.warning("⚠️ ముందుగా వీడియో లింక్ పేస్ట్ చేయండి.")
    else:
        loader_box.markdown('<div class="loading-pill"><span class="spin-icon">🔄</span> రిపోర్ట్ లోడ్ అవుతోంది... దయచేసి వేచి ఉండండి (ఆపడానికి పేజీ Refresh చేయండి)</div>', unsafe_allow_html=True)
        if platform == "YouTube":
            d_txt, st_obj, err_msg = fetch_youtube_info(video_url.strip())
        else:
            d_txt, st_obj, err_msg = f"Platform: {platform}\nURL: {video_url.strip()}", None, None

        if err_msg:
            loader_box.empty()
            st.error(f"⚠️ {err_msg}")
        else:
            st.session_state.report_stats = st_obj
            if isinstance(st_obj, dict):
                m1, m2, m3 = st.columns(3)
                m1.metric("👀 Views", f"{int(st_obj.get('viewCount', 0)):,}")
                m2.metric("👍 Likes", f"{int(st_obj.get('likeCount', 0)):,}")
                m3.metric("💬 Comments", f"{int(st_obj.get('commentCount', 0)):,}")

            prompt = build_prompt(platform, d_txt, report_lang, target_audience)
            stream_area = st.empty()
            full_text = ""
            success = False
            last_err = "API Key missing in Secrets"

            for api_key in GEMINI_KEYS:
                client = genai.Client(api_key=api_key)
                models_to_try = get_active_models(api_key)
                for m_name in models_to_try:
                    for retry in range(2):
                        try:
                            partial = ""
                            for chunk in client.models.generate_content_stream(
                                model=m_name,
                                contents=prompt,
                                config=types.GenerateContentConfig(temperature=0.82, max_output_tokens=8192)
                            ):
                                if chunk and chunk.text:
                                    partial += clean_advisor_terms(chunk.text)
                                    stream_area.markdown(partial + " ▌")
                            if len(partial.strip()) > 300:
                                full_text = partial.strip()
                                stream_area.markdown(full_text)
                                success = True
                                break
                        except Exception as e:
                            last_err = str(e)
                            if any(code in last_err for code in ("503", "429", "UNAVAILABLE", "overloaded", "RESOURCE_EXHAUSTED")):
                                time.sleep(1.5)
                                continue
                            break
                    if success:
                        break
                if success:
                    break

            loader_box.empty()
            if success:
                st.session_state.generated_report = full_text
                log_usage_to_sheet(DEVICE_ID, platform, video_url.strip())
                if not st.session_state.is_pro_user:
                    new_cnt = sheet_inc_device_count(DEVICE_ID)
                    st.session_state.local_used = new_cnt if new_cnt is not None else min(MAX_FREE, used_now + 1)
                st.success("✅ Growth Audit Report సిద్ధమైంది!")
                st.download_button("📥 Download Complete Growth Report (.txt)", full_text, file_name="TrendSutra_Growth_Report.txt", mime="text/plain")
            else:
                stream_area.empty()
                st.error("⚠️ AI సర్వర్ తాత్కాలికంగా రద్దీగా ఉంది. దయచేసి 5 సెకన్ల తర్వాత మళ్ళీ బటన్ నొక్కండి (మీ ఉచిత కౌంట్ తగ్గలేదు).")

elif st.session_state.generated_report:
    if isinstance(st.session_state.report_stats, dict):
        m1, m2, m3 = st.columns(3)
        m1.metric("👀 Views", f"{int(st.session_state.report_stats.get('viewCount', 0)):,}")
        m2.metric("👍 Likes", f"{int(st.session_state.report_stats.get('likeCount', 0)):,}")
        m3.metric("💬 Comments", f"{int(st.session_state.report_stats.get('commentCount', 0)):,}")
    st.success("✅ Growth Audit Report సిద్ధమైంది!")
    st.download_button("📥 Download Complete Growth Report (.txt)", st.session_state.generated_report, file_name="TrendSutra_Growth_Report.txt", mime="text/plain")
    st.markdown(st.session_state.generated_report)
