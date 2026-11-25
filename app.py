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

st.markdown("""<style>
#MainMenu,footer,.stDeployButton,div[data-testid="stToolbarActions"],div[data-testid="stDecoration"],div[data-testid="stStatusWidget"],.viewerBadge_container__1QSob,.styles_viewerBadge__CvC9N{display:none!important;}
header[data-testid="stHeader"]{height:1.2rem!important;background:transparent!important;}
.block-container{padding-top:0.4rem!important;margin-top:-1.5rem!important;}
section[data-testid="stSidebar"]>div:first-child{padding-top:0.2rem!important;margin-top:-1.2rem!important;}
section[data-testid="stSidebar"] .stMarkdown p{margin-bottom:0.2rem!important;font-size:0.9rem!important;}
section[data-testid="stSidebar"] hr{margin:0.35rem 0!important;}
section[data-testid="stSidebar"] div[data-testid="stRadio"]>div{gap:0.3rem!important;}
section[data-testid="stSidebar"] div[data-testid="stTextInput"]{margin-top:6px!important;margin-bottom:4px!important;}
div.stButton>button:first-child{background-color:#c92a2a;color:white;font-weight:bold;border-radius:6px;border:none;width:100%;}
div.stDownloadButton>button:first-child{background-color:#2b8a3e;color:white;font-weight:bold;border-radius:6px;border:none;}
</style>""", unsafe_allow_html=True)

GEMINI_KEYS = [k.strip() for k in (st.secrets.get("GEMINI_API_KEY", ""), st.secrets.get("GEMINI_API_KEY_2", "")) if k and k.strip()]
YOUTUBE_KEY = str(st.secrets.get("YOUTUBE_API_KEY", "")).strip()
RAPIDAPI_KEY = str(st.secrets.get("RAPIDAPI_API_KEY", "")).strip()

GOOGLE_SHEET_API = "https://script.google.com/macros/s/AKfycbzEkkgxBP7aOKIXkEiOG7_rWc0quvnvTVqQDSWUAMk2zOPN7W8Ue_uOPwH7edmJJtEd/exec"
PAY_1_MONTH_LINK = "https://rzp.io/rzp/yop8jYS"
PAY_12_MONTHS_LINK = "https://rzp.io/rzp/sjonGmqw"

def get_device_fingerprint():
    try:
        headers = st.context.headers if hasattr(st, "context") else {}
        fwd = headers.get("X-Forwarded-For", "") or headers.get("X-Real-Ip", "") or ""
        ip = fwd.split(",")[0].strip() if fwd else ""
        ua = headers.get("User-Agent", "")
        os_sig = "win" if "Windows" in ua else ("mac" if "Mac" in ua else ("and" if "Android" in ua else ("ios" if "iPhone" in ua or "iPad" in ua else "oth")))
        if ip:
            raw = f"{ip}_{os_sig}"
            return "dev_" + hashlib.sha256(raw.encode()).hexdigest()[:16]
    except Exception:
        pass
    return "dev_fallback_global"

DEVICE_ID = get_device_fingerprint()

def sheet_get_device_count(dev_id):
    try:
        r = requests.get(f"{GOOGLE_SHEET_API}?device={dev_id}", timeout=5)
        txt = r.text.strip()
        if txt.isdigit():
            return min(3, max(0, int(txt)))
    except Exception:
        pass
    return None

def sheet_inc_device_count(dev_id):
    try:
        r = requests.get(f"{GOOGLE_SHEET_API}?device={dev_id}&inc=1", timeout=5)
        txt = r.text.strip()
        if txt.isdigit():
            return min(3, max(0, int(txt)))
    except Exception:
        pass
    return None

def log_usage_to_sheet(dev_id, plat, url_str):
    try:
        requests.get(
            GOOGLE_SHEET_API,
            params={"log": "1", "device": dev_id, "platform": plat, "url": url_str},
            timeout=4,
        )
    except Exception:
        pass

ls_free = streamlit_js_eval(js_expressions="localStorage.getItem('ts_device_free_v8')", key="ls_get_free_v8")
ls_pro = streamlit_js_eval(js_expressions="localStorage.getItem('ts_device_pro_v8')", key="ls_get_pro_v8")

if "free_used_count" not in st.session_state:
    cloud_cnt = sheet_get_device_count(DEVICE_ID)
    st.session_state.free_used_count = cloud_cnt if cloud_cnt is not None else 0
else:
    if "last_sync_ts" not in st.session_state or (time.time() - st.session_state.last_sync_ts > 3):
        cloud_cnt = sheet_get_device_count(DEVICE_ID)
        st.session_state.last_sync_ts = time.time()
        if cloud_cnt is not None and cloud_cnt != st.session_state.free_used_count:
            st.session_state.free_used_count = cloud_cnt

if "is_pro_user" not in st.session_state:
    st.session_state.is_pro_user = False

if ls_free is not None and str(ls_free).isdigit():
    val = min(3, int(ls_free))
    if val > st.session_state.free_used_count:
        st.session_state.free_used_count = val
        st.rerun()

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
            timeout=10,
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
        streamlit_js_eval(js_expressions="localStorage.setItem('ts_device_pro_v8', 'yes')", key="ls_pro_url_v8")
    elif st_val == "ALREADY_USED":
        st.sidebar.error("⚠️ ఈ Payment ID గరిష్టంగా 3 డివైజ్‌లలో వాడబడింది!")

with st.sidebar:
    st.markdown("### ⚙️ Settings")
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
    st.markdown("---")
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
        st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
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
                streamlit_js_eval(js_expressions="localStorage.setItem('ts_device_pro_v8', 'yes')", key=f"ls_pro_{int(time.time())}")
                time.sleep(0.3)
                st.rerun()
            elif res_st == "ALREADY_USED":
                st.error("❌ ఈ Payment ID గరిష్టంగా 3 డివైజ్‌లలో వాడబడింది! admin@aiengtel.com కి మెసేజ్ చేయండి.")
            else:
                st.error("❌ సరైన Payment ID ఇవ్వండి.")

if os.path.isfile("logo.png"):
    c1, c2 = st.columns([1, 7])
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
    video_url = st.text_input("Channel / Profile / Video Link:", placeholder="https://youtu.be/... లేదా Reel / TikTok లింక్ పేస్ట్ చేయండి")

@st.cache_data(ttl=300, show_spinner=False)
def fetch_youtube_info(url, yt_key):
    m = re.search(r"(?:v=|\/|live\/|shorts\/)([0-9A-Za-z_-]{11}).*", url)
    if not m:
        return None, "సరైన YouTube వీడియో లింక్ ఇవ్వండి.", []
    if not yt_key:
        return None, "YouTube API Key Secrets లో లేదు.", []
    try:
        yt = build("youtube", "v3", developerKey=yt_key)
        vr = yt.videos().list(part="snippet,statistics", id=m.group(1)).execute()
        items = vr.get("items", [])
        if not items:
            return None, "వీడియో వివరాలు దొరకలేదు.", []
        sn, st_obj = items[0]["snippet"], items[0]["statistics"]
        raw_comments = []
        try:
            cr = yt.commentThreads().list(
                part="snippet",
                videoId=m.group(1),
                maxResults=25,
                order="relevance",
                textFormat="plainText",
            ).execute()
            for c in cr.get("items", []):
                top = c["snippet"]["topLevelComment"]["snippet"]
                author = top.get("authorDisplayName", "Viewer")
                text = top.get("textDisplay", "").replace("\n", " ").strip()
                if text:
                    raw_comments.append(f"{author}: {text[:180]}")
        except Exception:
            pass
        views = int(st_obj.get("viewCount", 0) or 0)
        likes = int(st_obj.get("likeCount", 0) or 0)
        comm_cnt = int(st_obj.get("commentCount", 0) or 0)
        like_rate = round((likes / views * 100), 2) if views > 0 else 0.0
        comm_rate = round((comm_cnt / views * 100), 3) if views > 0 else 0.0
        comments_block = "\n".join(raw_comments[:15]) if raw_comments else "No public comments found."
        summary = (
            f"Title: {sn.get('title')}\n"
            f"Channel: {sn.get('channelTitle')}\n"
            f"Views: {views:,} | Likes: {likes:,} (Like Rate: {like_rate}%) | Comments: {comm_cnt:,} (Comment Rate: {comm_rate}%)\n"
            f"Description: {sn.get('description', '')[:500]}\n"
            f"Tags: {sn.get('tags', [])[:15]}\n"
            f"Actual Viewer Comments:\n{comments_block}"
        )
        return summary, st_obj, raw_comments[:5]
    except Exception as e:
        return None, f"YouTube Error: {str(e)}", []

@st.cache_resource(show_spinner=False)
def get_working_models(api_key):
    client = genai.Client(api_key=api_key)
    lite_models = []
    flash_models = []
    try:
        for mod in client.models.list():
            name = mod.name.replace("models/", "")
            methods = getattr(mod, "supported_generation_methods", []) or []
            if "generateContent" in methods and "flash" in name.lower():
                if any(bad in name.lower() for bad in ("1.5", "2.0", "embedding", "audio", "image", "tts", "thinking")):
                    continue
                if "lite" in name.lower():
                    lite_models.append(name)
                else:
                    flash_models.append(name)
    except Exception:
        pass
    ordered = sorted(lite_models, reverse=True) + sorted(flash_models, reverse=True)
    for fallback in ("gemini-2.5-flash-lite", "gemini-2.5-flash"):
        if fallback not in ordered:
            ordered.append(fallback)
    return ordered

def clean_advisor_wording(text):
    text = text.replace("మెంటర్", "సలహాదారు").replace("mentor", "advisor").replace("Mentor", "Advisor")
    return text

def build_prompt(platform_name, raw_data, lang, audience):
    return f"""You are a friendly, practical human {platform_name} Growth Advisor (గ్రోత్ సలహాదారు) for TrendSutra AI.
Write a complete, easy-to-understand, deeply actionable 6-section A-to-Z Growth Audit Report in **{lang}** tailored for **{audience}** audience.

STRICT RULES:
1. Use simple, everyday spoken language (వాడుక భాష) that any creator can understand in seconds. Never use complex bookish words.
2. NEVER use the word "మెంటర్" or "Mentor"—always use "సలహాదారు" (Advisor).
3. In Section 2, pick up to 5 actual viewer comments from the data below, **TRANSLATE each comment naturally into {lang}**, show the translated comment with the commenter's name, explain what viewers really want, and provide 3 ready-to-copy replies in {lang}. (If no comments exist, say comments are turned off/empty and give 3 pinned comment ideas to spark discussion).
4. Write ALL 6 sections completely from start to finish without cutting short. Use exact Telugu numbering "పని 1, పని 2, పని 3" in Section 6.

STRUCTURE (Write all 6 sections in full):
### 📊 1. వీడియో పనితీరు విశ్లేషణ (Performance Diagnosis)
- Explain Views, Likes %, and Comments % in plain terms. What is working well and where viewers are dropping off.

### 💬 2. ఆడియన్స్ ఏం అంటున్నారు? (Translated Viewer Comments & Replies)
- List up to 5 real viewer comments **translated into {lang}** (with commenter name).
- Summarize the audience mood in 2 simple lines.
- Give 3 ready-to-copy reply templates in {lang} to boost algorithm engagement.

### 🔥 3. తదుపరి తీయాల్సిన 3 వైరల్ వీడియో ఐడియాలు (3 Viral Follow-Up Ideas)
- Give 3 specific follow-up video ideas based on this topic. For each idea, write: (a) Video Concept, (b) First 5-Second Hook line, (c) Thumbnail visual idea.

### 🎯 4. కాపీ-పేస్ట్ SEO మెరుగుదల (Copy-Paste Title, Description & Tags)
- 3 high-CTR catchy titles in {lang}.
- 3-line SEO description hook.
- 15 high-search tags separated by commas.

### 💰 5. ఆదాయం పెంచుకునే 3 మార్గాలు (Earning Blueprint)
- 3 practical ways to earn money from this exact niche (AdSense RPM tips, Affiliate products, Brand sponsorships).

### 📅 6. 30 రోజుల కార్యాచరణ ప్రణాళిక (30-Day Action Plan)
- పని 1 (Week 1): ...
- పని 2 (Week 2): ...
- పని 3 (Week 3): ...
- పని 4 (Week 4): ...

DATA TO ANALYZE:
{raw_data}"""

if "generated_report" not in st.session_state:
    st.session_state.generated_report = ""
if "report_stats" not in st.session_state:
    st.session_state.report_stats = None

btn_col, status_col = st.columns([1.4, 2.6])
with btn_col:
    run_clicked = st.button("Generate Accurate Growth Report 🔍")
with status_col:
    status_placeholder = st.empty()

if run_clicked:
    latest_cloud = sheet_get_device_count(DEVICE_ID)
    if latest_cloud is not None:
        st.session_state.free_used_count = latest_cloud

    if not st.session_state.is_pro_user and st.session_state.free_used_count >= 3:
        st.session_state.generated_report = ""
        st.session_state.report_stats = None
        st.error("🔒 **మీ 3 ఉచిత రిపోర్ట్‌లు పూర్తయ్యాయి!**")
        st.markdown(
            f"* **1 Month Unlimited (₹100):** 👉 [Pay ₹100]({PAY_1_MONTH_LINK})\n"
            f"* **12 Months Unlimited (₹1,000):** 👉 [Pay ₹1,000]({PAY_12_MONTHS_LINK})"
        )
    elif not video_url.strip():
        st.warning("⚠️ ముందుగా వీడియో లింక్ పేస్ట్ చేయండి.")
    else:
        status_placeholder.info("🔄 లోడ్ అవుతోంది... ⏳ (ఆపడానికి పేజీ రీఫ్రెష్ చేయండి)")
        if platform == "YouTube":
            d_txt, st_obj, _ = fetch_youtube_info(video_url.strip(), YOUTUBE_KEY)
        else:
            d_txt, st_obj = f"{platform} Link: {video_url.strip()}", None

        if platform == "YouTube" and not d_txt:
            status_placeholder.empty()
            st.error(f"⚠️ {st_obj}")
        else:
            st.session_state.report_stats = st_obj
            if isinstance(st_obj, dict):
                m1, m2, m3 = st.columns(3)
                m1.metric("👀 Views", f"{int(st_obj.get('viewCount', 0)):,}")
                m2.metric("👍 Likes", f"{int(st_obj.get('likeCount', 0)):,}")
                m3.metric("💬 Comments", f"{int(st_obj.get('commentCount', 0)):,}")

            prompt_text = build_prompt(platform, d_txt, report_lang, target_audience)
            stream_box = st.empty()
            full_text = ""
            success = False
            last_err = "API Key missing in Secrets"

            for key in GEMINI_KEYS:
                client = genai.Client(api_key=key)
                models_to_try = get_working_models(key)
                for m_name in models_to_try:
                    try:
                        full_text = ""
                        response_stream = client.models.generate_content_stream(
                            model=m_name,
                            contents=prompt_text,
                            config=types.GenerateContentConfig(
                                temperature=0.8,
                                max_output_tokens=8192,
                            ),
                        )
                        for chunk in response_stream:
                            if chunk.text:
                                full_text += clean_advisor_wording(chunk.text)
                                stream_box.markdown(full_text + " ▌")
                        if len(full_text.strip()) > 200:
                            stream_box.markdown(full_text)
                            success = True
                            break
                    except Exception as e:
                        last_err = str(e)
                        continue
                if success:
                    break

            status_placeholder.empty()
            if success:
                st.session_state.generated_report = full_text
                log_usage_to_sheet(DEVICE_ID, platform, video_url.strip())
                if not st.session_state.is_pro_user:
                    new_cnt = sheet_inc_device_count(DEVICE_ID)
                    if new_cnt is not None:
                        st.session_state.free_used_count = new_cnt
                    else:
                        st.session_state.free_used_count = min(3, st.session_state.free_used_count + 1)
                    streamlit_js_eval(
                        js_expressions=f"localStorage.setItem('ts_device_free_v8', '{st.session_state.free_used_count}')",
                        key=f"ls_f_{int(time.time())}",
                    )
                    time.sleep(0.3)
                    st.rerun()
            else:
                st.session_state.generated_report = ""
                if "429" in last_err or "RESOURCE_EXHAUSTED" in last_err:
                    st.error("⚠️ ఈరోజు ఉచిత AI API కోటా పూర్తయింది. దయచేసి కొద్దిసేపటి తర్వాత ప్రయత్నించండి లేదా Google AI Studio లో Billing ఆన్ చేయండి.")
                else:
                    st.error(f"⚠️ AI సర్వర్ బిజీగా ఉంది: {last_err[:120]}")

if st.session_state.generated_report and not run_clicked:
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
