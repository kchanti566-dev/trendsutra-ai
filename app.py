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
#MainMenu, footer, .stDeployButton, div[data-testid="stToolbarActions"], div[data-testid="stDecoration"], div[data-testid="stStatusWidget"] {
    display: none !important;
}
header[data-testid="stHeader"] {
    height: 1.2rem !important;
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
    margin-bottom: 0.35rem !important;
}
section[data-testid="stSidebar"] div[data-testid="stRadio"] > div {
    flex-direction: row !important;
    gap: 0.5rem !important;
}
div.stButton > button:first-child {
    background-color: #c92a2a;
    color: white;
    font-weight: bold;
    border-radius: 6px;
    border: none;
}
div.stDownloadButton > button:first-child {
    background-color: #2b8a3e;
    color: white;
    font-weight: bold;
    border-radius: 6px;
    border: none;
    padding: 0.45rem 1.1rem;
}
.loading-pill {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    background-color: #1e293b;
    color: #38bdf8;
    border: 1px solid #38bdf8;
    padding: 6px 14px;
    border-radius: 20px;
    font-weight: 600;
    font-size: 0.9rem;
    margin-top: 2px;
}
.spin-icon {
    display: inline-block;
    animation: spin 1s linear infinite;
}
@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}
</style>
""", unsafe_allow_html=True)

GEMINI_KEYS = [
    k.strip() for k in (
        st.secrets.get("GEMINI_API_KEY", ""),
        st.secrets.get("GEMINI_API_KEY_2", ""),
    ) if k and k.strip()
]
YOUTUBE_KEY = st.secrets.get("YOUTUBE_API_KEY", "").strip()
GOOGLE_SHEET_API = "https://script.google.com/macros/s/AKfycbzEkkgxBP7aOKIXkEiOG7_rWc0quvnvTVqQDSWUAMk2zOPN7W8Ue_uOPwH7edmJJtEd/exec"
PAY_1_MONTH_LINK = "https://rzp.io/rzp/yop8jYS"
PAY_12_MONTHS_LINK = "https://rzp.io/rzp/sjonGmqw"

def get_stable_device_id():
    try:
        headers = st.context.headers
        xff = headers.get("X-Forwarded-For", "") or headers.get("X-Real-Ip", "")
        client_ip = xff.split(",")[0].strip() if xff else ""
        ua = headers.get("User-Agent", "")
        os_sig = "WIN" if "Windows" in ua else ("AND" if "Android" in ua else ("IPH" if "iPhone" in ua else ("MAC" if "Mac" in ua else "GEN")))
        raw = f"{client_ip}|{os_sig}" if client_ip else ua
    except Exception:
        raw = "fallback_device"
    return "DEV_" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16].upper()

DEVICE_ID = get_stable_device_id()

def fetch_sheet_device_used(dev_id):
    try:
        r = requests.get(
            f"{GOOGLE_SHEET_API}?device={dev_id}&t={int(time.time())}",
            headers={"User-Agent": "Mozilla/5.0"},
            allow_redirects=True,
            timeout=8,
        )
        txt = r.text.strip()
        if txt.isdigit():
            return min(3, int(txt))
    except Exception:
        pass
    return None

def increment_sheet_device(dev_id):
    try:
        r = requests.get(
            f"{GOOGLE_SHEET_API}?device={dev_id}&inc=1&t={int(time.time())}",
            headers={"User-Agent": "Mozilla/5.0"},
            allow_redirects=True,
            timeout=8,
        )
        txt = r.text.strip()
        if txt.isdigit():
            return min(3, int(txt))
    except Exception:
        pass
    return None

def log_usage_to_sheet(dev_id, platform_name, url):
    try:
        requests.get(
            GOOGLE_SHEET_API,
            params={"log": "1", "device": dev_id, "platform": platform_name, "url": url[:250]},
            headers={"User-Agent": "Mozilla/5.0"},
            allow_redirects=True,
            timeout=5,
        )
    except Exception:
        pass

if "is_pro_user" not in st.session_state:
    st.session_state.is_pro_user = False
if "free_used_count" not in st.session_state:
    st.session_state.free_used_count = 0

sheet_count = fetch_sheet_device_used(DEVICE_ID)
if sheet_count is not None:
    st.session_state.free_used_count = max(st.session_state.free_used_count, sheet_count)

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
    if verify_payment_id(url_pid) in ("VALID", "OWNER_VALID"):
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
        rem = max(0, 3 - st.session_state.free_used_count)
        if rem > 0:
            st.info(f"🎁 **Free Trial:** మీకు **{rem} ఉచిత రిపోర్ట్‌లు** మిగిలి ఉన్నాయి.")
        else:
            st.error("🔒 **Free Trial:** మీకు **0 ఉచిత రిపోర్ట్‌లు** మిగిలి ఉన్నాయి!")
        st.markdown(
            f"• **1 Month:** **₹100/-** 👉 [Pay ₹100]({PAY_1_MONTH_LINK})  \n"
            f"• **12 Months:** **₹1,000/-** 👉 [Pay ₹1,000]({PAY_12_MONTHS_LINK})"
        )
        st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
        manual_pid = st.text_input(
            "Payment ID",
            placeholder="pay_P9x82kLm01",
            label_visibility="collapsed",
        )
        if st.button("Unlock with Payment ID 🔓"):
            res_st = verify_payment_id(manual_pid)
            if res_st in ("OWNER_VALID", "VALID"):
                st.session_state.is_pro_user = True
                st.rerun()
            elif res_st == "ALREADY_USED":
                st.error("❌ ఈ Payment ID గరిష్టంగా 3 డివైజ్‌లలో వాడబడింది!")
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
    video_url = st.text_input(
        "Channel / Profile / Video Link:",
        placeholder="https://youtu.be/... లేదా Reel / TikTok లింక్ పేస్ట్ చేయండి",
    )

@st.cache_data(ttl=180, show_spinner=False)
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
                part="snippet",
                videoId=m.group(1),
                maxResults=25,
                order="relevance",
                textFormat="plainText",
            ).execute()
            for c in cr.get("items", []):
                top = c["snippet"]["topLevelComment"]["snippet"]
                author = top.get("authorDisplayName", "Viewer")
                txt = top.get("textDisplay", "").strip()
                if txt:
                    coms.append(f"{author}: {txt}")
        except Exception:
            coms = ["కామెంట్లు ఆఫ్ చేసి ఉన్నాయి."]
        raw_summary = (
            f"Channel: {sn.get('channelTitle','')}\n"
            f"Title: {sn.get('title','')}\n"
            f"Views: {st_obj.get('viewCount','0')}, Likes: {st_obj.get('likeCount','0')}, Comments: {st_obj.get('commentCount','0')}\n"
            f"Description: {sn.get('description','')[:1000]}\n"
            f"Tags: {sn.get('tags', [])[:15]}\n"
            f"Real Viewer Comments: {coms[:12]}"
        )
        return raw_summary, st_obj
    except Exception as e:
        return None, f"YouTube Error: {str(e)}"

@st.cache_resource(show_spinner=False)
def get_active_models(api_key):
    client = genai.Client(api_key=api_key)
    lite_models, flash_models = [], []
    try:
        for m in client.models.list():
            name = getattr(m, "name", "").replace("models/", "")
            methods = getattr(m, "supported_generation_methods", []) or []
            if "generateContent" in methods and "flash" in name and "tts" not in name and "image" not in name and "audio" not in name:
                if any(old in name for old in ("1.0", "1.5", "2.0", "2.5-flash-preview")):
                    continue
                if "lite" in name:
                    lite_models.append(name)
                else:
                    flash_models.append(name)
    except Exception:
        pass
    ordered = sorted(lite_models, reverse=True) + sorted(flash_models, reverse=True)
    for fallback in ("gemini-2.5-flash-lite", "gemini-3.5-flash-lite", "gemini-2.5-flash"):
        if fallback not in ordered:
            ordered.append(fallback)
    return ordered

def clean_advisor_text(txt):
    return (
        txt.replace("మెంటర్", "సలహాదారు")
        .replace("మెంటార్", "సలహాదారు")
        .replace("స్ట్రాటజిస్ట్", "సలహాదారు")
    )

def build_prompt(platform_name, raw_data, lang, audience):
    return f"""You are a warm, encouraging human {platform_name} Growth Advisor (సలహాదారు) for TrendSutra AI.
Write a complete, detailed, easy-to-understand 6-section Growth Audit Report (around 1,100 to 1,400 words) in {lang} tailored for {audience} audience.
Rules:
- Use simple, everyday spoken language so any creator understands 100% immediately.
- In Telugu, always refer to yourself as 'సలహాదారు' (never use 'మెంటర్' or 'స్ట్రాటజిస్ట్').
- Do NOT write '(6 విభాగాలు)' anywhere.
- Finish ALL 6 sections completely from start to finish without stopping early.

Follow this exact structure:
Start with a warm 3-line greeting praising the creator's effort, channel, and video achievement.

### 🎬 1. మీ వీడియో కథ & క్రియేటర్ అభినందన (Video Story Recap & Creator Praise)
- First, warmly praise the creator's hard work, topic choice, presentation, and talent.
- Then, clearly replay/summarize the story or main points of the video based on the title, description, and comments so the creator feels you truly watched and understood their video.
- Highlight 3 things working great in this video.

### 💬 2. ఆడియన్స్ ఏం అంటున్నారు? (Translated Real Viewer Comments & Replies)
- Pick 4 to 5 real viewer comments from the data, translate each comment cleanly into {lang}, and explain what the audience loves or wants next.
- Provide 3 ready-to-copy reply templates the creator can paste to boost engagement.

### 🔥 3. తర్వాత తీయాల్సిన 3 వైరల్ వీడియో ఐడియాలు (Next 3 Viral Video Ideas)
- Give 3 fresh follow-up video ideas based on this video's success.
- For each idea, provide: Title concept, Story/Concept in 2 simple lines, and an exact 5-second Opening Hook dialogue.

### 🎯 4. కాపీ-పేస్ట్ టైటిల్స్, డిస్క్రిప్షన్ & ట్యాగ్స్ (SEO Makeover)
- Provide 3 High-CTR clickable titles in {lang}.
- Provide a short, punchy 3-line SEO description opening.
- Provide 15 searchable tags separated by commas.

### 💰 5. ఆదాయ మార్గాలు (Earning & Monetization Ideas)
- Explain 3 practical ways this creator can earn more money from this content (AdSense optimization, Affiliate links, Brand sponsorships) in simple steps.

### 📅 6. 30 రోజుల కార్యాచరణ ప్రణాళిక (30-Day Step-by-Step Action Plan)
- Give a clear 4-week plan using 'పని 1', 'పని 2', 'పని 3', 'పని 4' (if Telugu) with exact daily/weekly steps to grow faster.

Video Data:
{raw_data}"""

def stream_report_with_fallback(platform_name, raw_data, lang, audience, placeholder):
    prompt = build_prompt(platform_name, raw_data, lang, audience)
    last_err = "API Key missing in Secrets"
    for key in GEMINI_KEYS:
        client = genai.Client(api_key=key)
        models_to_try = get_active_models(key)
        for m in models_to_try:
            full_text = ""
            try:
                resp_stream = client.models.generate_content_stream(
                    model=m,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.8,
                        max_output_tokens=8192,
                    ),
                )
                for chunk in resp_stream:
                    part = getattr(chunk, "text", "") or ""
                    if part:
                        full_text += clean_advisor_text(part)
                        placeholder.markdown(full_text + " ▌")
                if len(full_text.strip()) > 200:
                    placeholder.markdown(full_text)
                    return True, full_text
            except Exception as e:
                last_err = str(e)
                if len(full_text.strip()) > 250:
                    cont_prompt = (
                        f"Continue and complete the remaining sections of this {platform_name} Growth Report in {lang} "
                        f"right from where it stopped, without repeating what is already written:\n\n{full_text[-1500:]}"
                    )
                    for m2 in models_to_try:
                        if m2 == m:
                            continue
                        try:
                            rem_stream = client.models.generate_content_stream(
                                model=m2,
                                contents=cont_prompt,
                                config=types.GenerateContentConfig(
                                    temperature=0.8,
                                    max_output_tokens=6000,
                                ),
                            )
                            for c2 in rem_stream:
                                p2 = getattr(c2, "text", "") or ""
                                if p2:
                                    full_text += clean_advisor_text(p2)
                                    placeholder.markdown(full_text + " ▌")
                            placeholder.markdown(full_text)
                            return True, full_text
                        except Exception:
                            continue
                time.sleep(0.5)
    return False, f"⚠️ AI సర్వర్ ప్రస్తుతం రద్దీగా ఉంది. దయచేసి ఒక్కసారి మళ్ళీ బటన్ నొక్కండి. ({last_err[:80]})"

if "generated_report" not in st.session_state:
    st.session_state.generated_report = ""
if "report_stats" not in st.session_state:
    st.session_state.report_stats = None

btn_col, status_col = st.columns((1.35, 2.65))
with btn_col:
    run_clicked = st.button("Generate Accurate Growth Report 🔍")
status_slot = status_col.empty()

if run_clicked:
    latest_sheet_cnt = fetch_sheet_device_used(DEVICE_ID)
    if latest_sheet_cnt is not None:
        st.session_state.free_used_count = max(st.session_state.free_used_count, latest_sheet_cnt)

    if not st.session_state.is_pro_user and st.session_state.free_used_count >= 3:
        st.session_state.generated_report = ""
        st.error("🔒 **మీ 3 ఉచిత రిపోర్ట్‌లు పూర్తయ్యాయి!** అన్‌లిమిటెడ్ రిపోర్ట్‌ల కోసం ఎడమ వైపున ఉన్న Pro Plan ఎంచుకోండి.")
        st.markdown(
            f"* **1 Month Unlimited (₹100):** 👉 [Pay ₹100]({PAY_1_MONTH_LINK})\n"
            f"* **12 Months Unlimited (₹1,000):** 👉 [Pay ₹1,000]({PAY_12_MONTHS_LINK})"
        )
    elif not video_url.strip():
        st.warning("⚠️ ముందుగా వీడియో లింక్ పేస్ట్ చేయండి.")
    else:
        status_slot.markdown(
            '<div class="loading-pill"><span class="spin-icon">🔄</span> రిపోర్ట్ లోడ్ అవుతోంది... దయచేసి వేచి ఉండండి (ఆపడానికి Refresh చేయండి)</div>',
            unsafe_allow_html=True,
        )
        if platform == "YouTube":
            d_txt, st_obj = fetch_youtube_info(video_url.strip())
        else:
            d_txt, st_obj = f"{platform} URL: {video_url.strip()}", None

        if platform == "YouTube" and not d_txt:
            status_slot.empty()
            st.error(f"⚠️ {st_obj}")
        else:
            if isinstance(st_obj, dict):
                m1, m2, m3 = st.columns(3)
                m1.metric("👀 Views", f"{int(st_obj.get('viewCount', 0)):,}")
                m2.metric("👍 Likes", f"{int(st_obj.get('likeCount', 0)):,}")
                m3.metric("💬 Comments", f"{int(st_obj.get('commentCount', 0)):,}")

            live_box = st.empty()
            ok, res_txt = stream_report_with_fallback(platform, d_txt, report_lang, target_audience, live_box)
            status_slot.empty()

            if ok:
                st.session_state.generated_report = res_txt
                st.session_state.report_stats = st_obj
                log_usage_to_sheet(DEVICE_ID, platform, video_url.strip())
                if not st.session_state.is_pro_user:
                    new_cnt = increment_sheet_device(DEVICE_ID)
                    st.session_state.free_used_count = new_cnt if new_cnt is not None else min(3, st.session_state.free_used_count + 1)
                st.rerun()
            else:
                st.error(res_txt)

elif st.session_state.generated_report:
    if isinstance(st.session_state.report_stats, dict):
        m1, m2, m3 = st.columns(3)
        m1.metric("👀 Views", f"{int(st.session_state.report_stats.get('viewCount', 0)):,}")
        m2.metric("👍 Likes", f"{int(st.session_state.report_stats.get('likeCount', 0)):,}")
        m3.metric("💬 Comments", f"{int(st.session_state.report_stats.get('commentCount', 0)):,}")
    st.success("✅ Growth Audit Report సిద్ధమైంది!")
    st.download_button(
        "📥 Download Full Growth Report (.txt)",
        data=st.session_state.generated_report,
        file_name="TrendSutra_Growth_Report.txt",
        mime="text/plain",
    )
    st.markdown(st.session_state.generated_report)
