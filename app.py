import streamlit as st
from google import genai
from google.genai import types
from googleapiclient.discovery import build
import re
import os
import base64
import requests
import random
import smtplib
from email.mime.text import MIMEText
from datetime import datetime

# --- 1. PAGE CONFIG ---
page_icon = "logo.png" if os.path.exists("logo.png") else "📊"
st.set_page_config(page_title="TrendSutra AI - Growth Analyzer", page_icon=page_icon, layout="wide", initial_sidebar_state="expanded")

# --- 2. LOAD SECRETS ---
GEMINI_KEY = str(st.secrets.get("GEMINI_API_KEY", "")).strip()
YOUTUBE_KEY = str(st.secrets.get("YOUTUBE_API_KEY", "")).strip()
SHEET_API = str(st.secrets.get("GOOGLE_SHEET_API", "")).strip()
OWNER_CODE = str(st.secrets.get("OWNER_SECRET_CODE", "")).strip()
SENDER_EMAIL = str(st.secrets.get("SENDER_EMAIL", "")).strip()
SENDER_PASS = str(st.secrets.get("SENDER_APP_PASSWORD", "")).strip().replace(" ", "")

RAZORPAY_1M = "https://rzp.io/rzp/yop8jYS"
RAZORPAY_12M = "https://rzp.io/rzp/sjonGmqw"

TEMP_DOMAINS = {
    "mailinator.com", "tempmail.com", "10minutemail.com", "guerrillamail.com",
    "yopmail.com", "throwawaymail.com", "fakeinbox.com", "trashmail.com",
    "getnada.com", "temp-mail.org", "dispostable.com", "maildrop.cc"
}

# --- 3. CUSTOM STYLING (CENTERED LOGO HEADER + NO-SCROLL SIDEBAR) ---
st.markdown("""
<style>
    [data-testid="stToolbarActions"], .stDeployButton, #MainMenu, footer {
        display: none !important;
    }
    [data-testid="stSidebarCollapsedControl"] {
        display: flex !important;
        visibility: visible !important;
        z-index: 99999 !important;
    }
    header[data-testid="stHeader"] {
        background: transparent !important;
        height: 2.2rem !important;
    }
    .block-container {
        padding-top: 1.6rem !important;
        padding-bottom: 1rem !important;
        max-width: 1200px !important;
    }
    [data-testid="stSidebar"] > div:first-child {
        padding-top: 0.6rem !important;
        padding-bottom: 0.5rem !important;
    }
    [data-testid="stSidebar"] .stMarkdown p {
        margin-bottom: 0.25rem !important;
        font-size: 0.88rem !important;
    }
    [data-testid="stSidebar"] hr {
        margin: 0.45rem 0 !important;
    }
    .centered-banner {
        background: linear-gradient(135deg, #0b132b 0%, #1c2541 100%);
        padding: 18px 24px;
        border-radius: 14px;
        border-bottom: 4px solid #10b981;
        margin-bottom: 14px;
        text-align: center;
        box-shadow: 0 4px 16px rgba(0,0,0,0.25);
    }
    .banner-title-row {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        gap: 14px;
    }
    .banner-title-row h1 {
        margin: 0 !important;
        padding: 0 !important;
        font-size: 2.15rem !important;
        font-weight: 800 !important;
        color: #ffffff !important;
        letter-spacing: 0.3px;
    }
    .centered-banner p {
        margin: 6px 0 0 0 !important;
        color: #cbd5e1 !important;
        font-size: 1rem !important;
    }
    .status-strip {
        background: #0f172a;
        border: 1px solid #334155;
        padding: 8px 14px;
        border-radius: 10px;
        color: #f8fafc;
        font-size: 0.94rem;
        display: flex;
        align-items: center;
        height: 40px;
    }
    .loading-pill {
        background: #064e3b;
        border: 1.5px solid #10b981;
        color: #ecfdf5;
        padding: 8px 14px;
        border-radius: 10px;
        font-weight: 600;
        font-size: 0.92rem;
        display: inline-flex;
        align-items: center;
        gap: 8px;
    }
</style>
""", unsafe_allow_html=True)

# --- 4. SESSION STATE ---
if "verified_email" not in st.session_state:
    st.session_state.verified_email = ""
if "otp_code" not in st.session_state:
    st.session_state.otp_code = ""
if "otp_target" not in st.session_state:
    st.session_state.otp_target = ""
if "pro_unlocked" not in st.session_state:
    st.session_state.pro_unlocked = False
if "pro_label" not in st.session_state:
    st.session_state.pro_label = ""
if "yt_report" not in st.session_state:
    st.session_state.yt_report = ""
if "yt_meta" not in st.session_state:
    st.session_state.yt_meta = None
if "ig_report" not in st.session_state:
    st.session_state.ig_report = ""
if "tt_report" not in st.session_state:
    st.session_state.tt_report = ""
if "sheet_status" not in st.session_state:
    st.session_state.sheet_status = ""

# --- 5. CHECK GOOGLE OAUTH LOGIN ---
try:
    if hasattr(st, "user") and getattr(st.user, "is_logged_in", False):
        g_email = getattr(st.user, "email", "")
        if g_email:
            st.session_state.verified_email = g_email.strip().lower()
except Exception:
    pass

# --- 6. GOOGLE SHEET HELPERS ---
def get_free_used_count(user_id):
    if not SHEET_API or not user_id:
        return 0
    try:
        r = requests.get(
            SHEET_API,
            params={"device": user_id, "_ts": int(datetime.now().timestamp())},
            timeout=10,
            allow_redirects=True
        )
        txt = r.text.strip()
        if r.status_code == 200 and txt.isdigit():
            st.session_state.sheet_status = "OK"
            return min(3, int(txt))
        else:
            st.session_state.sheet_status = f"ERR:{txt[:40]}"
    except Exception as e:
        st.session_state.sheet_status = f"CONN_ERR:{str(e)[:30]}"
    return 0

def increment_free_used(user_id):
    if not SHEET_API or not user_id:
        return False
    for _ in range(2):
        try:
            r = requests.get(
                SHEET_API,
                params={"device": user_id, "inc": "1", "_ts": int(datetime.now().timestamp())},
                timeout=10,
                allow_redirects=True
            )
            if r.status_code == 200 and r.text.strip().isdigit():
                return True
        except Exception:
            pass
    return False

def log_usage_to_sheet(user_id, platform, url):
    if not SHEET_API:
        return
    try:
        requests.get(
            SHEET_API,
            params={
                "log": "1",
                "device": user_id,
                "platform": platform,
                "url": url,
                "_ts": int(datetime.now().timestamp())
            },
            timeout=8,
            allow_redirects=True
        )
    except Exception:
        pass

def verify_payment_id(pid, plan="1m"):
    pid = pid.strip()
    if OWNER_CODE and pid == OWNER_CODE:
        return "OWNER"
    if not pid.startswith("pay_") or len(pid) < 10:
        return "INVALID"
    if not SHEET_API:
        return "VALID"
    try:
        r = requests.get(
            SHEET_API,
            params={"pid": pid, "plan": plan},
            timeout=10,
            allow_redirects=True
        )
        if r.status_code == 200:
            res = r.text.strip().upper()
            if res in ["VALID", "ALREADY_USED", "EXPIRED", "INVALID"]:
                return res
    except Exception:
        pass
    return "ERROR"

if "razorpay_payment_id" in st.query_params and not st.session_state.pro_unlocked:
    auto_pid = str(st.query_params["razorpay_payment_id"]).strip()
    if auto_pid.startswith("pay_"):
        st_res = verify_payment_id(auto_pid, plan="1m")
        if st_res == "VALID":
            st.session_state.pro_unlocked = True
            st.session_state.pro_label = "PRO UNLIMITED ACTIVE"

def send_otp_email(to_email, code):
    if not SENDER_EMAIL or not SENDER_PASS:
        return False, "SMTP not configured"
    try:
        body = (
            f"Welcome to TrendSutra AI!\n\n"
            f"Your 6-digit verification code is: {code}\n\n"
            f"Enter this code on TrendSutra AI to unlock your 3 Free Growth Reports."
        )
        msg = MIMEText(body)
        msg["Subject"] = f"{code} is your TrendSutra AI Verification Code"
        msg["From"] = f"TrendSutra AI <{SENDER_EMAIL}>"
        msg["To"] = to_email
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=12) as server:
            server.login(SENDER_EMAIL, SENDER_PASS)
            server.sendmail(SENDER_EMAIL, [to_email], msg.as_string())
        return True, "SENT"
    except Exception as e:
        return False, str(e)

# --- 7. YOUTUBE DATA FETCHER ---
def extract_youtube_id(url):
    patterns = [
        r"(?:v=|\/)([0-9A-Za-z_-]{11}).*",
        r"youtu\.be\/([0-9A-Za-z_-]{11})",
        r"shorts\/([0-9A-Za-z_-]{11})"
    ]
    for p in patterns:
        m = re.search(p, url)
        if m:
            return m.group(1)
    return None

@st.cache_data(ttl=300, show_spinner=False)
def fetch_youtube_details(video_id):
    if not YOUTUBE_KEY:
        return None
    try:
        yt = build("youtube", "v3", developerKey=YOUTUBE_KEY)
        v_res = yt.videos().list(part="snippet,statistics", id=video_id).execute()
        if not v_res.get("items"):
            return None
        item = v_res["items"][0]
        snip = item["snippet"]
        stats = item.get("statistics", {})
        comments = []
        try:
            c_res = yt.commentThreads().list(
                part="snippet", videoId=video_id, maxResults=25, order="relevance", textFormat="plainText"
            ).execute()
            for c in c_res.get("items", []):
                top = c["snippet"]["topLevelComment"]["snippet"]
                author = top.get("authorDisplayName", "Viewer")
                text = top.get("textDisplay", "").strip().replace("\n", " ")
                if text:
                    comments.append(f"{author}: {text[:220]}")
        except Exception:
            pass
        return {
            "id": video_id,
            "title": snip.get("title", ""),
            "channel": snip.get("channelTitle", ""),
            "description": snip.get("description", "")[:1200],
            "tags": snip.get("tags", [])[:20],
            "views": int(stats.get("viewCount", 0)),
            "likes": int(stats.get("likeCount", 0)),
            "comment_count": int(stats.get("commentCount", 0)),
            "comments": comments
        }
    except Exception:
        return None

# --- 8. GEMINI AI STREAMING ---
@st.cache_resource
def get_gemini_client():
    return genai.Client(api_key=GEMINI_KEY)

def get_best_models(client):
    preferred = [
        "gemini-2.5-flash",
        "gemini-2.5-flash-lite",
        "gemini-3.5-flash",
        "gemini-3.5-flash-lite"
    ]
    try:
        avail = []
        for m in client.models.list():
            name = m.name.replace("models/", "")
            if "flash" in name and "2.0" not in name and "1.5" not in name and "8b" not in name:
                avail.append(name)
        ordered = [p for p in preferred if p in avail]
        for a in avail:
            if a not in ordered:
                ordered.append(a)
        if ordered:
            return ordered[:4]
    except Exception:
        pass
    return preferred

def clean_mentor_word(text):
    return text.replace("మెంటర్", "సలహాదారు").replace("స్ట్రాటజిస్ట్", "సలహాదారు")

def generate_report_stream(prompt):
    client = get_gemini_client()
    models = get_best_models(client)
    last_err = ""
    for model_name in models:
        try:
            response = client.models.generate_content_stream(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.82,
                    max_output_tokens=8192
                )
            )
            yielded_any = False
            for chunk in response:
                if chunk.text:
                    yielded_any = True
                    yield clean_mentor_word(chunk.text)
            if yielded_any:
                return
        except Exception as e:
            last_err = str(e)
            continue
    raise RuntimeError(f"AI సర్వర్ రద్దీగా ఉంది. దయచేసి 5 సెకన్ల తర్వాత మళ్ళీ ప్రయత్నించండి. ({last_err})")

# --- 9. LIVE QUOTA CHECK ---
free_used = get_free_used_count(st.session_state.verified_email) if st.session_state.verified_email else 0
free_left = max(0, 3 - free_used)

# --- 10. COMPACT NO-SCROLL SIDEBAR ---
with st.sidebar:
    st.markdown("**⚙️ Settings**")
    report_lang = st.selectbox(
        "Report Language:",
        ["Telugu (తెలుగు)", "English", "Tenglish (Telugu + English)"],
        label_visibility="collapsed"
    )
    audience_scope = st.radio("Audience:", ["Regional", "Global", "Both"], horizontal=True, label_visibility="collapsed")

    st.divider()
    st.markdown("**💎 Pro Plans (Unlimited)**")

    if st.session_state.pro_unlocked:
        st.success(f"✅ {st.session_state.pro_label}")
    elif st.session_state.verified_email:
        if free_left > 0:
            st.warning(f"🎁 Free Trial: **{free_left} / 3** రిపోర్ట్‌లు మిగిలాయి")
        else:
            st.error("🔒 **0** ఉచిత రిపోర్ట్‌లు మిగిలాయి!")
    else:
        st.info("🎁 లాగిన్ అయి **3 Free Reports** పొందండి")

    st.markdown(f"• **1 Month:** ₹100/- 👉 [Pay ₹100]({RAZORPAY_1M})")
    st.markdown(f"• **12 Months:** ₹1,000/- 👉 [Pay ₹1,000]({RAZORPAY_12M})")

    plan_choice = st.radio("Plan:", ["1 Month (₹100)", "12 Months (₹1,000)"], horizontal=True, label_visibility="collapsed")
    pay_input = st.text_input("Payment ID:", placeholder="Paste Payment ID (pay_...)", label_visibility="collapsed")
    if st.button("Unlock Pro 🔓", use_container_width=True):
        if not pay_input.strip():
            st.warning("Payment ID ఎంటర్ చేయండి.")
        else:
            p_code = "12m" if "12" in plan_choice else "1m"
            status = verify_payment_id(pay_input, plan=p_code)
            if status == "OWNER":
                st.session_state.pro_unlocked = True
                st.session_state.pro_label = "OWNER UNLIMITED"
                st.rerun()
            elif status == "VALID":
                st.session_state.pro_unlocked = True
                st.session_state.pro_label = f"PRO ({plan_choice})"
                st.rerun()
            elif status == "EXPIRED":
                st.error("⏰ ప్లాన్ గడువు ముగిసింది!")
            elif status == "ALREADY_USED":
                st.error("❌ ఇప్పటికే 3 డివైజ్‌లలో వాడబడింది.")
            else:
                st.error("❌ చెల్లని Payment ID.")

    st.divider()
    st.caption("📩 support@aiengtel.com | aiengtel.com")

# --- 11. CENTERED HEADER WITH LOGO ---
logo_html = ""
if os.path.exists("logo.png"):
    with open("logo.png", "rb") as img_f:
        b64_logo = base64.b64encode(img_f.read()).decode()
    logo_html = f'<img src="data:image/png;base64,{b64_logo}" style="width:46px; height:46px; border-radius:10px; object-fit:contain;" />'

st.markdown(f"""
<div class="centered-banner">
    <div class="banner-title-row">
        {logo_html}
        <h1>TrendSutra AI</h1>
    </div>
    <p>A to Z Growth Analyzer for YouTube, Instagram & TikTok Creators</p>
</div>
""", unsafe_allow_html=True)

# --- 12. SINGLE-LINE COMPACT LOGIN BAR ---
if not st.session_state.verified_email and not st.session_state.pro_unlocked:
    lc1, lc2, lc3, lc4 = st.columns([2.2, 0.4, 2.6, 1.5])
    with lc1:
        if st.button("🔵 Continue with Gmail", type="primary", use_container_width=True):
            try:
                st.login("google")
            except Exception as e:
                st.error(f"Google Login error: {e}")
    with lc2:
        st.markdown("<div style='text-align:center; padding-top:8px; color:#94a3b8; font-weight:700;'>OR</div>", unsafe_allow_html=True)
    with lc3:
        email_in = st.text_input("Mail ID", placeholder="Login with Mail ID (creator@gmail.com)", label_visibility="collapsed")
    with lc4:
        if st.button("Send OTP 📩", use_container_width=True):
            clean_em = email_in.strip().lower()
            if "@" not in clean_em or "." not in clean_em.split("@")[-1]:
                st.error("సరైన Mail ID ఇవ్వండి.")
            elif clean_em.split("@")[-1] in TEMP_DOMAINS:
                st.error("Temp mail అనుమతించబడదు.")
            else:
                code = str(random.randint(100000, 999999))
                ok, err_msg = send_otp_email(clean_em, code)
                if ok:
                    st.session_state.otp_code = code
                    st.session_state.otp_target = clean_em
                    st.success(f"✅ {clean_em} కి OTP పంపబడింది!")
                else:
                    st.error(f"OTP Error: {err_msg}")

    if st.session_state.otp_target:
        oc1, oc2 = st.columns([3, 1.5])
        with oc1:
            otp_in = st.text_input("OTP", placeholder=f"{st.session_state.otp_target} కి వచ్చిన 6-అంకెల OTP ఎంటర్ చేయండి", max_chars=6, label_visibility="collapsed")
        with oc2:
            if st.button("Verify & Unlock ✅", type="primary", use_container_width=True):
                if otp_in.strip() == st.session_state.otp_code:
                    st.session_state.verified_email = st.session_state.otp_target
                    st.session_state.otp_code = ""
                    st.rerun()
                else:
                    st.error("❌ తప్పు OTP!")
else:
    uc1, uc2 = st.columns([5.2, 1.2])
    with uc1:
        who = st.session_state.verified_email if st.session_state.verified_email else "PRO Member"
        badge = f"💎 <b>{st.session_state.pro_label}</b>" if st.session_state.pro_unlocked else f"🎁 <b>{free_left} / 3</b> ఉచిత రిపోర్ట్‌లు మిగిలి ఉన్నాయి"
        st.markdown(f'<div class="status-strip">✅ Logged in as <b>&nbsp;{who}&nbsp;</b> | {badge}</div>', unsafe_allow_html=True)
    with uc2:
        if st.button("Logout 🚪", use_container_width=True):
            st.session_state.verified_email = ""
            st.session_state.pro_unlocked = False
            st.session_state.yt_report = ""
            try:
                if hasattr(st, "logout"):
                    st.logout()
            except Exception:
                pass
            st.rerun()

# --- 13. MAIN TABS ---
tab_yt, tab_ig, tab_tt = st.tabs(["📺 YouTube Analyzer", "📸 Instagram Reels Analyzer", "🎵 TikTok Analyzer"])

with tab_yt:
    yc1, yc2 = st.columns([4.8, 1.6])
    with yc1:
        yt_url = st.text_input("YT Link", placeholder="Paste YouTube Video or Shorts Link (https://www.youtube.com/watch?v=...)", label_visibility="collapsed")
    with yc2:
        run_yt = st.button("Generate Growth Report 🔍", key="btn_yt", type="primary", use_container_width=True)

    yt_status_slot = st.empty()

    if run_yt:
        if not st.session_state.verified_email and not st.session_state.pro_unlocked:
            st.warning("⚠️ దయచేసి పైన **Continue with Gmail** లేదా **Login with Mail ID** ద్వారా లాగిన్ అవ్వండి.")
        elif not yt_url.strip():
            st.warning("దయచేసి YouTube లింక్ పేస్ట్ చేయండి.")
        elif not st.session_state.pro_unlocked and free_left <= 0:
            st.error("🔒 మీ 3 ఉచిత రిపోర్ట్‌లు పూర్తయ్యాయి! అన్‌లిమిటెడ్ రిపోర్ట్‌ల కోసం ఎడమ వైపు Pro Plan తీసుకోండి.")
        else:
            vid_id = extract_youtube_id(yt_url.strip())
            if not vid_id:
                st.error("❌ సరైన YouTube వీడియో లేదా Shorts లింక్ ఇవ్వండి.")
            else:
                yt_status_slot.markdown('<div class="loading-pill">🔄 వీడియో వివరాలు & కామెంట్లు సేకరిస్తోంది... ⏳</div>', unsafe_allow_html=True)
                data = fetch_youtube_details(vid_id)
                if not data:
                    yt_status_slot.empty()
                    st.error("❌ ఈ వీడియో డేటా పొందలేకపోయాము. వీడియో Public లో ఉందో లేదో చూడండి.")
                else:
                    st.session_state.yt_meta = data
                    comments_block = "\n".join(data["comments"][:15]) if data["comments"] else "No public comments available."
                    prompt = f"""
You are a warm, encouraging, expert human social media growth advisor ("సలహాదారు").
Write a comprehensive, deeply detailed, easy-to-understand growth audit report (1,100 to 1,500 words) in **{report_lang}** for a **{audience_scope}** audience.
Use simple everyday spoken words (never use complex bookish words, and NEVER use the word 'మెంటర్'—use 'సలహాదారు' if needed).

VIDEO DATA:
- Channel: {data['channel']}
- Title: {data['title']}
- Views: {data['views']:,} | Likes: {data['likes']:,} | Comments: {data['comment_count']:,}
- Description: {data['description']}
- Tags: {', '.join(data['tags'])}
- Real Audience Comments:
{comments_block}

STRICTLY FOLLOW THIS 6-SECTION STRUCTURE:
### 🎬 1. మీ వీడియో కథ & క్రియేటర్ అభినందన (Video Story Recap & Creator Appreciation)
- First, warmly retell the core story/message of this video based on its title, description, and comments so the creator feels you truly watched and understood their hard work.
- Then genuinely praise the creator's effort, topic choice, presentation, and strengths with encouraging words.

### 💬 2. ఆడియన్స్ ఏం అంటున్నారు? (Real Audience Comments Translated to {report_lang})
- Pick 4 to 5 real viewer comments from the list above, translate them naturally into **{report_lang}**, quote them with the viewer's name, explain what the audience loves or asks for, and give 3 ready-to-copy reply templates to boost algorithm engagement.

### 🔥 3. తదుపరి తీయాల్సిన 3 వైరల్ వీడియో ఐడియాలు (3 Next Viral Video Ideas + 5-Sec Hooks)
- Give 3 fresh, high-potential follow-up video ideas tailored to this channel. For each idea, write an exact word-for-word **5-second opening Hook** and a **Thumbnail visual idea**.

### 🎯 4. కాపీ-పేస్ట్ SEO మేకోవర్ (High-CTR Titles, Description & 15 Tags)
- Provide 3 clickable high-CTR title options, a strong 3-line SEO description hook, and 15 searchable comma-separated tags.

### 💰 5. ఆదాయ మార్గాలు (Monetization & Brand Earning Blueprint)
- Explain 3 practical ways this specific channel can earn money (AdSense, Affiliate links, Brand sponsorships) with realistic examples.

### 📅 6. 30 రోజుల కార్యాచరణ ప్రణాళిక (Step-by-Step 30-Day Action Plan)
- Give a clear Week 1 to Week 4 checklist of simple daily/weekly actions to double views and subscribers.
"""
                    yt_status_slot.markdown('<div class="loading-pill">⚡ రిపోర్ట్ తయారవుతోంది... (ఆపడానికి పేజీ Refresh చేయండి) ⏳</div>', unsafe_allow_html=True)
                    report_box = st.empty()
                    full_text = ""
                    try:
                        for piece in generate_report_stream(prompt):
                            full_text += piece
                            report_box.markdown(full_text)
                        yt_status_slot.empty()
                        st.session_state.yt_report = full_text
                        if not st.session_state.pro_unlocked and st.session_state.verified_email:
                            increment_free_used(st.session_state.verified_email)
                        log_usage_to_sheet(st.session_state.verified_email or "PRO", "YouTube", yt_url.strip())
                        st.rerun()
                    except Exception as e:
                        yt_status_slot.empty()
                        st.error(str(e))

    if st.session_state.yt_report:
        if st.session_state.yt_meta:
            d = st.session_state.yt_meta
            m1, m2, m3 = st.columns(3)
            m1.metric("👀 Views", f"{d['views']:,}")
            m2.metric("👍 Likes", f"{d['likes']:,}")
            m3.metric("💬 Comments", f"{d['comment_count']:,}")
        st.markdown(st.session_state.yt_report)
        st.download_button(
            "📥 Download Complete Growth Report (.txt)",
            data=st.session_state.yt_report,
            file_name="TrendSutra_YouTube_Growth_Report.txt",
            mime="text/plain",
            use_container_width=True
        )

with tab_ig:
    ic1, ic2 = st.columns([4.8, 1.6])
    with ic1:
        ig_url = st.text_input("IG Link", placeholder="Paste Instagram Reel Link (https://www.instagram.com/reel/...)", label_visibility="collapsed")
    with ic2:
        run_ig = st.button("Generate Growth Report 🔍", key="btn_ig", type="primary", use_container_width=True)

    ig_status_slot = st.empty()

    if run_ig:
        if not st.session_state.verified_email and not st.session_state.pro_unlocked:
            st.warning("⚠️ దయచేసి పైన **Continue with Gmail** లేదా **Login with Mail ID** ద్వారా లాగిన్ అవ్వండి.")
        elif not ig_url.strip():
            st.warning("దయచేసి Instagram Reel లింక్ పేస్ట్ చేయండి.")
        elif not st.session_state.pro_unlocked and free_left <= 0:
            st.error("🔒 మీ 3 ఉచిత రిపోర్ట్‌లు పూర్తయ్యాయి! అన్‌లిమిటెడ్ రిపోర్ట్‌ల కోసం ఎడమ వైపు Pro Plan తీసుకోండి.")
        else:
            ig_status_slot.markdown('<div class="loading-pill">⚡ Instagram రిపోర్ట్ తయారవుతోంది... ⏳</div>', unsafe_allow_html=True)
            ig_prompt = f"""
You are a warm, encouraging human Instagram Reels growth advisor ("సలహాదారు").
Write a detailed 6-section Instagram Reels growth audit (1,000+ words) in **{report_lang}** for a **{audience_scope}** audience using simple spoken words (use 'సలహాదారు', never 'మెంటర్').
Reel Link: {ig_url.strip()}
Include:
1. Creator Appreciation & Reel Strategy Overview
2. Watch-Time, Audio & Retention Hook Analysis
3. 3 Viral Follow-Up Reel Ideas with word-for-word 3-second Hooks
4. Copy-Paste Caption & 15 Trending Hashtags
5. Brand Collaboration & Monetization Plan
6. 30-Day Instagram Growth Action Plan
"""
            report_box = st.empty()
            full_text = ""
            try:
                for piece in generate_report_stream(ig_prompt):
                    full_text += piece
                    report_box.markdown(full_text)
                ig_status_slot.empty()
                st.session_state.ig_report = full_text
                if not st.session_state.pro_unlocked and st.session_state.verified_email:
                    increment_free_used(st.session_state.verified_email)
                log_usage_to_sheet(st.session_state.verified_email or "PRO", "Instagram", ig_url.strip())
                st.rerun()
            except Exception as e:
                ig_status_slot.empty()
                st.error(str(e))

    if st.session_state.ig_report:
        st.markdown(st.session_state.ig_report)
        st.download_button(
            "📥 Download Instagram Report (.txt)",
            data=st.session_state.ig_report,
            file_name="TrendSutra_Instagram_Report.txt",
            mime="text/plain",
            use_container_width=True
        )

with tab_tt:
    tc1, tc2 = st.columns([4.8, 1.6])
    with tc1:
        tt_url = st.text_input("TT Link", placeholder="Paste TikTok Video Link (https://www.tiktok.com/@user/video/...)", label_visibility="collapsed")
    with tc2:
        run_tt = st.button("Generate Growth Report 🔍", key="btn_tt", type="primary", use_container_width=True)

    tt_status_slot = st.empty()

    if run_tt:
        if not st.session_state.verified_email and not st.session_state.pro_unlocked:
            st.warning("⚠️ దయచేసి పైన **Continue with Gmail** లేదా **Login with Mail ID** ద్వారా లాగిన్ అవ్వండి.")
        elif not tt_url.strip():
            st.warning("దయచేసి TikTok లింక్ పేస్ట్ చేయండి.")
        elif not st.session_state.pro_unlocked and free_left <= 0:
            st.error("🔒 మీ 3 ఉచిత రిపోర్ట్‌లు పూర్తయ్యాయి! అన్‌లిమిటెడ్ రిపోర్ట్‌ల కోసం ఎడమ వైపు Pro Plan తీసుకోండి.")
        else:
            tt_status_slot.markdown('<div class="loading-pill">⚡ TikTok రిపోర్ట్ తయారవుతోంది... ⏳</div>', unsafe_allow_html=True)
            tt_prompt = f"""
You are a warm, encouraging human TikTok growth advisor ("సలహాదారు").
Write a detailed 6-section TikTok growth audit (1,000+ words) in **{report_lang}** for a **{audience_scope}** audience using simple spoken words (use 'సలహాదారు', never 'మెంటర్').
TikTok Link: {tt_url.strip()}
Include:
1. Creator Appreciation & Viral Potential Overview
2. Completion Rate & Looping Hook Formula
3. 3 Viral Follow-Up TikTok Ideas with word-for-word 3-second Hooks
4. Copy-Paste Caption & 15 FYP Hashtags
5. Creator Rewards & Brand Monetization Plan
6. 30-Day TikTok Growth Action Plan
"""
            report_box = st.empty()
            full_text = ""
            try:
                for piece in generate_report_stream(tt_prompt):
                    full_text += piece
                    report_box.markdown(full_text)
                tt_status_slot.empty()
                st.session_state.tt_report = full_text
                if not st.session_state.pro_unlocked and st.session_state.verified_email:
                    increment_free_used(st.session_state.verified_email)
                log_usage_to_sheet(st.session_state.verified_email or "PRO", "TikTok", tt_url.strip())
                st.rerun()
            except Exception as e:
                tt_status_slot.empty()
                st.error(str(e))

    if st.session_state.tt_report:
        st.markdown(st.session_state.tt_report)
        st.download_button(
            "📥 Download TikTok Report (.txt)",
            data=st.session_state.tt_report,
            file_name="TrendSutra_TikTok_Report.txt",
            mime="text/plain",
            use_container_width=True
        )
