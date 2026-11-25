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
    """<style>
    #MainMenu, footer, .stDeployButton, div[data-testid="stToolbarActions"], div[data-testid="stDecoration"], div[data-testid="stStatusWidget"], .viewerBadge_container__1QSob, .viewerBadge_link__1S137 {display:none!important;}
    header[data-testid="stHeader"] {height:1.2rem!important; background:transparent!important;}
    .block-container {padding-top:0.5rem!important; margin-top:-1.8rem!important; padding-bottom:2rem!important;}
    section[data-testid="stSidebar"] > div:first-child {padding-top:0.4rem!important; margin-top:-1.2rem!important;}
    section[data-testid="stSidebar"] .stMarkdown p {margin-bottom:0.35rem!important; line-height:1.35!important;}
    div[data-testid="stRadio"] > div {gap:0.4rem!important;}
    div.stButton > button:first-child {background-color:#c92a2a; color:white; font-weight:bold; border-radius:6px; border:none; width:100%;}
    div.stDownloadButton > button:first-child {background-color:#2b8a3e; color:white; font-weight:bold; border-radius:6px; border:none;}
    </style>""",
    unsafe_allow_html=True,
)

GEMINI_KEYS = [
    k.strip()
    for k in (
        st.secrets.get("GEMINI_API_KEY", ""),
        st.secrets.get("GEMINI_API_KEY_2", ""),
    )
    if k and str(k).strip()
]
YOUTUBE_KEY = str(st.secrets.get("YOUTUBE_API_KEY", "")).strip()
RAPIDAPI_KEY = str(st.secrets.get("RAPIDAPI_API_KEY", "")).strip()

GOOGLE_SHEET_API = "https://script.google.com/macros/s/AKfycbzEkkgxBP7aOKIXkEiOG7_rWc0quvnvTVqQDSWUAMk2zOPN7W8Ue_uOPwH7edmJJtEd/exec"
PAY_1_MONTH_LINK = "https://rzp.io/rzp/yop8jYS"
PAY_12_MONTHS_LINK = "https://rzp.io/rzp/sjonGmqw"

fp_raw = streamlit_js_eval(
    js_expressions="navigator.userAgent + '|' + screen.width + 'x' + screen.height + '|' + navigator.language + '|' + (navigator.hardwareConcurrency || '')",
    key="hw_fp_v9",
)
ls_free = streamlit_js_eval(
    js_expressions="localStorage.getItem('ts_device_free_v9')",
    key="ls_get_free_v9",
)
ls_pro = streamlit_js_eval(
    js_expressions="localStorage.getItem('ts_device_pro_v9')",
    key="ls_get_pro_v9",
)

@st.cache_data(ttl=3600)
def get_public_ip():
    try:
        return requests.get("https://api.ipify.org", timeout=5).text.strip()
    except Exception:
        return "unknown_ip"

def get_device_id():
    ip_addr = get_public_ip()
    raw = f"{ip_addr}|{fp_raw or 'browser'}"
    return "DEV_" + hashlib.sha256(raw.encode()).hexdigest()[:16]

def sync_device_sheet(dev_id, inc=False):
    try:
        url = f"{GOOGLE_SHEET_API}?device={dev_id}" + ("&inc=1" if inc else "")
        res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, allow_redirects=True, timeout=10)
        txt = res.text.strip()
        if txt.isdigit():
            return int(txt)
    except Exception:
        pass
    return None

def log_usage_to_sheet(dev_id, platform_name, link_url):
    try:
        requests.get(
            GOOGLE_SHEET_API,
            params={"log": "1", "device": dev_id, "platform": platform_name, "url": link_url[:150]},
            headers={"User-Agent": "Mozilla/5.0"},
            allow_redirects=True,
            timeout=8,
        )
    except Exception:
        pass

device_id = get_device_id()

if "free_used_count" not in st.session_state:
    st.session_state.free_used_count = 0
if "is_pro_user" not in st.session_state:
    st.session_state.is_pro_user = False
if "sheet_checked" not in st.session_state:
    st.session_state.sheet_checked = False

if ls_free and str(ls_free).isdigit() and int(ls_free) > st.session_state.free_used_count:
    st.session_state.free_used_count = int(ls_free)

if not st.session_state.sheet_checked and fp_raw:
    sc = sync_device_sheet(device_id, inc=False)
    if sc is not None and sc > st.session_state.free_used_count:
        st.session_state.free_used_count = sc
    st.session_state.sheet_checked = True

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
            js_expressions="localStorage.setItem('ts_device_pro_v9', 'yes')",
            key="ls_pro_url_v9",
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
        ("Regional", "Global", "Both"),
        horizontal=True,
    )
    st.markdown("### 💎 Pro Plans (Unlimited)")
    if st.session_state.is_pro_user:
        st.success("✅ PRO UNLIMITED ACTIVE! అన్‌లిమిటెడ్ రిపోర్ట్‌లు పొందవచ్చు.")
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
                    js_expressions="localStorage.setItem('ts_device_pro_v9', 'yes')",
                    key=f"ls_pro_{int(time.time())}",
                )
                time.sleep(0.5)
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

def fetch_youtube_info(url):
    m = re.search(r"(?:v=|\/|live\/|shorts\/)([0-9A-Za-z_-]{11}).*", url)
    if not m:
        return None, "సరైన YouTube వీడియో లింక్ ఇవ్వండి (ఉదా: https://youtu.be/...)."
    try:
        yt = build("youtube", "v3", developerKey=YOUTUBE_KEY)
        vr = yt.videos().list(part="snippet,statistics,contentDetails", id=m.group(1)).execute()
        items = vr.get("items", [])
        if not items:
            return None, "వీడియో వివరాలు దొరకలేదు. వీడియో Public లో ఉందో లేదో చూడండి."
        sn = items[0]["snippet"]
        st_obj = items[0]["statistics"]
        dur = items[0].get("contentDetails", {}).get("duration", "")
        coms = []
        try:
            cr = yt.commentThreads().list(
                part="snippet",
                videoId=m.group(1),
                maxResults=40,
                order="relevance",
                textFormat="plainText",
            ).execute()
            coms = [c["snippet"]["topLevelComment"]["snippet"]["textDisplay"] for c in cr.get("items", [])]
        except Exception:
            coms = ["కామెంట్లు ఆఫ్ చేసి ఉన్నాయి."]
        info_text = (
            f"Channel: {sn.get('channelTitle')}\n"
            f"Published At: {sn.get('publishedAt')}\n"
            f"Title: {sn.get('title')}\n"
            f"Duration: {dur}\n"
            f"Views: {st_obj.get('viewCount', '0')}, Likes: {st_obj.get('likeCount', '0')}, Comments: {st_obj.get('commentCount', '0')}\n"
            f"Description: {sn.get('description', '')[:900]}\n"
            f"Tags: {sn.get('tags', [])}\n"
            f"Top Audience Comments: {coms}"
        )
        return info_text, st_obj
    except Exception as e:
        return None, f"YouTube Data Error: {str(e)}"

def get_best_models(client):
    try:
        all_m = [
            m.name.replace("models/", "")
            for m in client.models.list()
            if "generateContent" in (getattr(m, "supported_actions", None) or getattr(m, "supported_generation_methods", None) or [])
        ]
        valid = [
            x for x in all_m
            if "gemini" in x
            and "1.5" not in x
            and "2.0" not in x
            and x != "gemini-2.5-flash"
            and "pro" not in x
            and "image" not in x
            and "tts" not in x
            and "robotics" not in x
        ]
        lite = [x for x in valid if "lite" in x]
        flash = [x for x in valid if "flash" in x and "lite" not in x]
        ordered = lite + flash
        if ordered:
            return ordered[:4]
    except Exception:
        pass
    return ["gemini-3.5-flash-lite", "gemini-3.5-flash", "gemini-2.5-flash-lite"]

def generate_growth_report(platform_name, raw_data, lang, audience):
    prompt = (
        f"You are an elite, deeply empathetic human YouTube & Social Media Growth Mentor working for TrendSutra AI. "
        f"Speak directly to the creator like a warm, experienced human coach—never sound robotic or generic. "
        f"Analyze the real metrics, comments, title, tags, and timing below and deliver a comprehensive, crystal-clear, actionable A-to-Z Growth Audit Report in {lang} tailored for a {audience} audience. "
        f"If writing in Telugu, always use the exact spelling 'పని 1, పని 2, పని 3' for tasks.\n\n"
        f"Structure the report into 6 detailed, high-value sections:\n"
        f"1. 📊 **Deep Performance & Engagement Diagnosis**: Calculate the real Like-to-View % and Comment-to-View % from the numbers, explain what is working right now, and pinpoint the exact bottleneck holding this video/profile back.\n"
        f"2. 💬 **Real Audience Psychology & Comment Insights**: Decode what viewers truly loved, what confused them, and what questions they are asking in the comments—plus exact reply templates to boost algorithm engagement.\n"
        f"3. 🔥 **3 Fresh, High-CTR Viral Follow-Up Video Ideas**: Give 3 specific next video concepts based on this video's momentum, complete with a scroll-stopping Hook (first 5 seconds) and Thumbnail visual concept for each.\n"
        f"4. 🎯 **Copy-Paste SEO Makeover (Titles, Description & Tags)**: Provide 3 high-converting clickable Titles, an optimized first-3-lines Description hook, and 15 high-volume searchable Tags/Hashtags.\n"
        f"5. 💰 **Monetization & Brand Earning Blueprint**: Show 3 realistic ways this exact niche can earn money right now (AdSense optimization, Affiliate products, Local/Global brand sponsorships) with estimated earning angles.\n"
        f"6. 📅 **Step-by-Step 30-Day Creator Action Plan**: Break down clear weekly milestones (పని 1, పని 2, పని 3...) so the creator knows exactly what to do tomorrow morning.\n\n"
        f"Creator Data:\n{raw_data}"
    )
    last_err = "API Key missing in Secrets"
    for key in GEMINI_KEYS:
        client = genai.Client(api_key=key)
        models_to_try = get_best_models(client)
        for m in models_to_try:
            for attempt in range(2):
                try:
                    resp = client.models.generate_content(
                        model=m,
                        contents=prompt,
                        config={"temperature": 0.85},
                    )
                    if resp and resp.text:
                        return True, resp.text
                except Exception as e:
                    err_s = str(e)
                    last_err = err_s
                    if "404" in err_s or "no longer available" in err_s:
                        break
                    time.sleep(1.5)
    if "429" in last_err or "RESOURCE_EXHAUSTED" in last_err:
        return False, "⚠️ ప్రస్తుతం ఎక్కువ మంది యూజర్లు రిపోర్ట్‌లు జనరేట్ చేస్తున్నారు (API Quota Limit). దయచేసి 1 నిమిషం ఆగి మళ్ళీ ప్రయత్నించండి."
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
            f"అన్‌లిమిటెడ్ రిపోర్ట్‌ల కోసం ప్రో ప్లాన్ ఎంచుకోండి:\n"
            f"* **1 Month Unlimited (₹100/-):** 👉 [Pay ₹100]({PAY_1_MONTH_LINK})\n"
            f"* **12 Months Unlimited (₹1,000/-):** 👉 [Pay ₹1,000]({PAY_12_MONTHS_LINK})"
        )
    elif not video_url.strip():
        st.warning("⚠️ ముందుగా వీడియో లేదా ఛానల్ లింక్ పేస్ట్ చేయండి.")
    else:
        with st.spinner("మీ కంటెంట్ డేటాను లోతుగా విశ్లేషించి పూర్తి గ్రోత్ రిపోర్ట్ తయారు చేస్తోంది..."):
            if platform == "YouTube":
                d_txt, st_obj = fetch_youtube_info(video_url.strip())
            else:
                d_txt, st_obj = f"Platform: {platform}\nProfile/Reel Link: {video_url.strip()}\nAnalyze hook, retention, audio trend, caption SEO, and monetization strategy for this link.", None

            if platform == "YouTube" and not d_txt:
                st.error(f"⚠️ {st_obj}")
            else:
                ok, res_txt = generate_growth_report(platform, d_txt, report_lang, target_audience)
                if ok:
                    st.session_state.generated_report = res_txt
                    st.session_state.report_stats = st_obj
                    log_usage_to_sheet(device_id, platform, video_url.strip())
                    if not st.session_state.is_pro_user:
                        new_c = sync_device_sheet(device_id, inc=True)
                        if new_c is not None:
                            st.session_state.free_used_count = new_c
                        else:
                            st.session_state.free_used_count += 1
                        streamlit_js_eval(
                            js_expressions=f"localStorage.setItem('ts_device_free_v9', '{st.session_state.free_used_count}')",
                            key=f"ls_f_{int(time.time())}",
                        )
                        time.sleep(0.5)
                        st.rerun()
                else:
                    st.session_state.generated_report = ""
                    st.error(res_txt)

if st.session_state.generated_report:
    if isinstance(st.session_state.report_stats, dict):
        m1, m2, m3 = st.columns(3)
        m1.metric("👀 Views", f"{int(st.session_state.report_stats.get('viewCount', 0)):,}")
        m2.metric("👍 Likes", f"{int(st.session_state.report_stats.get('likeCount', 0)):,}")
        m3.metric("💬 Comments", f"{int(st.session_state.report_stats.get('commentCount', 0)):,}")
    st.success("✅ మీ పూర్తి A-to-Z Growth Audit Report సిద్ధమైంది!")
    st.download_button(
        "📥 Download Growth Report (.txt)",
        st.session_state.generated_report,
        "TrendSutra_Growth_Report.txt",
    )
    st.markdown(st.session_state.generated_report)
