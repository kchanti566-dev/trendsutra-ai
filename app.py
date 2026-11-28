import streamlit as st
from google import genai
from google.genai import types
from googleapiclient.discovery import build
import re
import requests
import random
import smtplib
import time
import os
import base64
from email.mime.text import MIMEText

# --- 1. PAGE CONFIG ---
LOGO_PATH = "logo.png" if os.path.exists("logo.png") else None
st.set_page_config(
    page_title="TrendSutra AI - 1 AI, 1 India Growth Analyzer",
    page_icon=LOGO_PATH if LOGO_PATH else "📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. LOAD SECRETS (4-KEY SMART FAILOVER) ---
PAID_KEY = str(st.secrets.get("GEMINI_API_KEY", "")).strip()
FREE_KEY_2 = str(st.secrets.get("GEMINI_API_KEY_2", "")).strip()
FREE_KEY_3 = str(st.secrets.get("GEMINI_API_KEY_3", "")).strip()
FREE_KEY_4 = str(st.secrets.get("GEMINI_API_KEY_4", "")).strip()

GEMINI_KEYS_ORDERED = []
for k in [FREE_KEY_4, FREE_KEY_3, FREE_KEY_2, PAID_KEY]:
    if k and k not in GEMINI_KEYS_ORDERED:
        GEMINI_KEYS_ORDERED.append(k)

YOUTUBE_KEY = str(st.secrets.get("YOUTUBE_API_KEY", "")).strip()
SHEET_API = str(st.secrets.get("GOOGLE_SHEET_API", "")).strip()
OWNER_CODE = str(st.secrets.get("OWNER_SECRET_CODE", "")).strip()
SENDER_EMAIL = str(st.secrets.get("SENDER_EMAIL", "")).strip()
SENDER_PASS = str(st.secrets.get("SENDER_APP_PASSWORD", "")).strip().replace(" ", "")

RAZORPAY_1M = "https://rzp.io/rzp/70Y3L0K"
RAZORPAY_12M = "https://rzp.io/rzp/77zX68U"

TEMP_DOMAINS = {
    "mailinator.com", "tempmail.com", "10minutemail.com", "guerrillamail.com",
    "yopmail.com", "throwawaymail.com", "fakeinbox.com", "trashmail.com",
    "getnada.com", "temp-mail.org", "dispostable.com", "maildrop.cc"
}

INDIAN_LANGUAGES = [
    "Auto-Detect Video Language (ఆటోమేటిక్ భాష)",
    "Telugu (తెలుగు)",
    "Hindi (हिन्दी)",
    "Tamil (தமிழ்)",
    "Kannada (ಕನ್ನಡ)",
    "Malayalam (മലയാളം)",
    "Marathi (मराठी)",
    "Bengali (বাংলা)",
    "Gujarati (ગુજરાતી)",
    "Punjabi (ਪੰਜਾਬੀ)",
    "Odia (ଓଡ଼ିଆ)",
    "Assamese (অসমীয়া)",
    "Urdu (اردو)",
    "English",
    "Hinglish (Hindi + English)",
    "Tenglish (Telugu + English)"
]

# --- 3. CUSTOM STYLING ---
st.markdown("""
<style>
    [data-testid="stToolbarActions"], .stAppDeployButton, #MainMenu, footer {
        display: none !important;
        visibility: hidden !important;
    }
    [data-testid="stSidebarCollapsedControl"] {
        display: flex !important;
        visibility: visible !important;
        z-index: 999999 !important;
    }
    .block-container {
        padding-top: 0.75rem !important;
        padding-bottom: 1rem !important;
        max-width: 100% !important;
    }
    [data-testid="stSidebar"] .block-container {
        padding-top: 0.5rem !important;
        padding-bottom: 0.4rem !important;
    }
    [data-testid="stSidebar"] hr {
        margin: 0.45rem 0 !important;
    }
    .center-banner {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        padding: 14px 20px;
        border-radius: 14px;
        border-bottom: 4px solid #10b981;
        text-align: center;
        margin-bottom: 10px;
        box-shadow: 0 4px 14px rgba(0,0,0,0.25);
    }
    .center-banner-title {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        gap: 12px;
        margin: 0;
        font-size: 1.95rem;
        font-weight: 800;
        color: #ffffff;
        letter-spacing: 0.4px;
    }
    .center-banner-sub {
        margin: 4px 0 0 0;
        color: #cbd5e1;
        font-size: 0.94rem;
    }
    .india-badge {
        display: inline-block;
        background: rgba(16, 185, 129, 0.16);
        border: 1px solid #10b981;
        color: #6ee7b7;
        padding: 2px 10px;
        border-radius: 999px;
        font-size: 0.78rem;
        font-weight: 700;
        margin-top: 5px;
    }
    .login-strip {
        background: #1e293b;
        border: 1px solid #334155;
        padding: 10px 14px;
        border-radius: 10px;
        margin-bottom: 10px;
        color: #f8fafc;
    }
    .loading-pill {
        background: #064e3b;
        border: 1.5px solid #10b981;
        color: #ecfdf5;
        padding: 8px 14px;
        border-radius: 8px;
        font-weight: 600;
        font-size: 0.9rem;
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
if "yt_vid" not in st.session_state:
    st.session_state.yt_vid = ""
if "ig_report" not in st.session_state:
    st.session_state.ig_report = ""
if "tt_report" not in st.session_state:
    st.session_state.tt_report = ""

# --- 5. CHECK GOOGLE OAUTH ---
try:
    if hasattr(st, "user") and getattr(st.user, "is_logged_in", False):
        g_email = getattr(st.user, "email", "")
        if g_email:
            st.session_state.verified_email = g_email.strip().lower()
except Exception:
    pass

# --- 6. GOOGLE SHEET HELPERS (NO-CACHE LIVE SYNC) ---
def get_free_used_count(user_id):
    if not SHEET_API or not user_id:
        return 0
    try:
        r = requests.get(
            SHEET_API,
            params={"device": user_id, "_ts": int(time.time() * 1000)},
            timeout=8,
            allow_redirects=True
        )
        if r.status_code == 200 and r.text.strip().isdigit():
            return min(3, int(r.text.strip()))
    except Exception:
        pass
    return 0

def increment_free_used(user_id):
    if not SHEET_API or not user_id:
        return
    for _ in range(2):
        try:
            r = requests.get(
                SHEET_API,
                params={"device": user_id, "inc": "1", "_ts": int(time.time() * 1000)},
                timeout=8,
                allow_redirects=True
            )
            if r.status_code == 200:
                return
        except Exception:
            time.sleep(0.3)

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
                "_ts": int(time.time() * 1000)
            },
            timeout=6,
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
            params={"pid": pid, "plan": plan, "_ts": int(time.time() * 1000)},
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

qp = st.query_params
if "razorpay_payment_id" in qp and not st.session_state.pro_unlocked:
    auto_pid = str(qp["razorpay_payment_id"]).strip()
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
        msg["Subject"] = f"{code} - TrendSutra AI Verification Code"
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
                part="snippet", videoId=video_id, maxResults=20, order="relevance", textFormat="plainText"
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
            "title": snip.get("title", ""),
            "channel": snip.get("channelTitle", ""),
            "channel_id": snip.get("channelId", ""),
            "default_audio_lang": snip.get("defaultAudioLanguage", "") or snip.get("defaultLanguage", ""),
            "description": snip.get("description", "")[:1200],
            "tags": snip.get("tags", [])[:20],
            "views": int(stats.get("viewCount", 0)),
            "likes": int(stats.get("likeCount", 0)),
            "comment_count": int(stats.get("commentCount", 0)),
            "comments": comments
        }
    except Exception:
        return None

# --- 8. SINGLE-CALL UNIFIED GEMINI AI STREAMING (ZERO EXTRA API CALLS!) ---
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
            return ordered[:3]
    except Exception:
        pass
    return preferred

def clean_mentor_word(text):
    return text.replace("మెంటర్", "సలహాదారు").replace("స్ట్రాటజిస్ట్", "సలహాదారు")

def generate_report_stream(prompt):
    if not GEMINI_KEYS_ORDERED:
        raise RuntimeError("Gemini API Key కనుగొనబడలేదు. Streamlit Secrets చెక్ చేయండి.")
    last_err = ""
    for api_key in GEMINI_KEYS_ORDERED:
        try:
            client = genai.Client(api_key=api_key)
            models = get_best_models(client)
            for model_name in models:
                try:
                    response = client.models.generate_content_stream(
                        model=model_name,
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            temperature=0.80,
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
        except Exception as e:
            last_err = str(e)
            continue
    raise RuntimeError(f"AI సర్వర్ రద్దీగా ఉంది. దయచేసి 5 సెకన్ల తర్వాత మళ్ళీ ప్రయత్నించండి. ({last_err})")

# --- 9. CENTERED HEADER WITH LOGO (NO ROCKET!) ---
logo_html = ""
if LOGO_PATH:
    try:
        with open(LOGO_PATH, "rb") as f:
            b64_logo = base64.b64encode(f.read()).decode()
        logo_html = f'<img src="data:image/png;base64,{b64_logo}" style="height:44px; width:44px; border-radius:10px; object-fit:contain; vertical-align:middle;" />'
    except Exception:
        logo_html = ""

st.markdown(f"""
<div class="center-banner">
    <div class="center-banner-title">{logo_html}<span>TrendSutra AI</span></div>
    <p class="center-banner-sub">A to Z Growth Analyzer for YouTube, Instagram & TikTok Creators</p>
    <div class="india-badge">🇮🇳 1 AI • 1 India — All Indian Regional Languages & Global Creators</div>
</div>
""", unsafe_allow_html=True)

# --- 10. COMPACT NO-SCROLL SIDEBAR ---
with st.sidebar:
    st.markdown("### ⚙️ Settings")
    report_lang = st.selectbox(
        "Report Language / భాష:",
        INDIAN_LANGUAGES,
        index=0
    )
    audience_scope = st.radio("Target Audience:", ["Regional (India)", "Global", "Both"], horizontal=True)

    st.divider()
    free_used = get_free_used_count(st.session_state.verified_email) if st.session_state.verified_email else 0
    free_left = max(0, 3 - free_used)

    if st.session_state.pro_unlocked:
        st.success(f"✅ {st.session_state.pro_label}")
    elif st.session_state.verified_email:
        if free_left > 0:
            st.info(f"🎁 Free Trials Left: **{free_left} / 3**")
        else:
            st.error("🔒 **0 / 3** ఉచిత రిపోర్ట్‌లు మిగిలాయి!")
    else:
        st.info("🎁 లాగిన్ అయి **3 ఉచిత రిపోర్ట్‌లు** పొందండి")

    st.markdown("### 💎 Pro Plans (Unlimited)")
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

# --- 11. SINGLE-ROW COMPACT LOGIN BAR ---
if not st.session_state.verified_email and not st.session_state.pro_unlocked:
    st.markdown('<div class="login-strip">🔐 <b>3 ఉచిత రిపోర్ట్‌ల కోసం లాగిన్ అవ్వండి:</b></div>', unsafe_allow_html=True)
    lc1, lc2, lc3, lc4 = st.columns([2.2, 0.5, 2.8, 1.5])
    with lc1:
        if st.button("🔵 Continue with Gmail", type="primary", use_container_width=True):
            try:
                st.login("google")
            except Exception as e:
                st.error(f"Google Login Error: {e}")
    with lc2:
        st.markdown("<div style='text-align:center; padding-top:8px; color:#94a3b8; font-weight:700;'>OR</div>", unsafe_allow_html=True)
    with lc3:
        email_in = st.text_input("Login with Mail ID", placeholder="Login with Mail ID (creator@gmail.com)", label_visibility="collapsed")
    with lc4:
        if st.button("Send OTP 📩", use_container_width=True):
            clean_em = email_in.strip().lower()
            if "@" not in clean_em or "." not in clean_em.split("@")[-1]:
                st.error("❌ సరైన Mail ID ఇవ్వండి.")
            elif clean_em.split("@")[-1] in TEMP_DOMAINS:
                st.error("❌ Temp Mail అనుమతించబడదు.")
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
            otp_in = st.text_input("Enter 6-digit OTP", placeholder="మీ మెయిల్ కి వచ్చిన 6-అంకెల OTP ఎంటర్ చేయండి", max_chars=6, label_visibility="collapsed")
        with oc2:
            if st.button("Verify & Start ✅", type="primary", use_container_width=True):
                if otp_in.strip() == st.session_state.otp_code:
                    st.session_state.verified_email = st.session_state.otp_target
                    st.session_state.otp_code = ""
                    st.rerun()
                else:
                    st.error("❌ తప్పు OTP!")
else:
    u_col1, u_col2 = st.columns([4, 1])
    with u_col1:
        who = st.session_state.verified_email if st.session_state.verified_email else "PRO Member"
        badge = "UNLIMITED PRO" if st.session_state.pro_unlocked else f"{free_left}/3 ఉచిత రిపోర్ట్‌లు మిగిలి ఉన్నాయి"
        st.caption(f"👤 Logged in as **{who}** | Status: **{badge}**")
    with u_col2:
        if st.session_state.verified_email:
            if st.button("Logout 🚪", use_container_width=True):
                st.session_state.verified_email = ""
                st.session_state.pro_unlocked = False
                try:
                    if hasattr(st, "logout"):
                        st.logout()
                except Exception:
                    pass
                st.rerun()

# --- 12. SINGLE-CALL UNIFIED LANGUAGE & CONTENT DIRECTIVE ---
def build_language_directive(selected_lang):
    if selected_lang.startswith("Auto-Detect"):
        return (
            "UNIFIED SINGLE-PASS LANGUAGE DETECTION & REPORT GENERATION: "
            "In this exact same response (without needing any extra step), identify the primary spoken/written language of this video "
            "from its title, description, audio language tag, and audience comments (Telugu, Hindi, Tamil, Kannada, Malayalam, Marathi, "
            "Bengali, Gujarati, Punjabi, Odia, Assamese, Urdu, or English). "
            "Start with one line: '🌐 Detected Video Language: <Language Name>' and write the ENTIRE growth report naturally in that EXACT language!"
        )
    return (
        f"Write the ENTIRE growth report naturally in **{selected_lang}** using simple, everyday spoken words "
        f"that any regional or global creator can easily understand."
    )

# --- 13. MAIN WORKSPACE TABS ---
tab_yt, tab_ig, tab_tt = st.tabs(["📺 YouTube Analyzer", "📸 Instagram Reels Analyzer", "🎵 TikTok Analyzer"])

with tab_yt:
    yc1, yc2, yc3 = st.columns([3.5, 1.5, 1.5])
    with yc1:
        yt_url = st.text_input("YouTube URL", placeholder="Paste YouTube Video or Shorts Link (https://...)", label_visibility="collapsed")
    with yc2:
        run_yt = st.button("Generate Growth Report 🔍", key="btn_yt", type="primary", use_container_width=True)
    with yc3:
        yt_status_slot = st.empty()

    if run_yt:
        if not st.session_state.verified_email and not st.session_state.pro_unlocked:
            st.warning("⚠️ దయచేసి పైన Gmail లేదా Mail ID తో లాగిన్ అవ్వండి.")
        elif not yt_url.strip():
            st.warning("దయచేసి YouTube లింక్ పేస్ట్ చేయండి.")
        elif not st.session_state.pro_unlocked and free_left <= 0:
            st.error("🔒 మీ 3 ఉచిత రిపోర్ట్‌లు పూర్తయ్యాయి! అన్‌లిమిటెడ్ రిపోర్ట్‌ల కోసం ఎడమ వైపు Pro Plan తీసుకోండి.")
        else:
            vid_id = extract_youtube_id(yt_url.strip())
            if not vid_id:
                st.error("❌ సరైన YouTube వీడియో లేదా Shorts లింక్ ఇవ్వండి.")
            else:
                yt_status_slot.markdown('<div class="loading-pill">🔄 డేటా సేకరిస్తోంది... ⏳</div>', unsafe_allow_html=True)
                data = fetch_youtube_details(vid_id)
                if not data:
                    yt_status_slot.empty()
                    st.error("❌ ఈ వీడియో డేటా పొందలేకపోయాము. వీడియో Public లో ఉందో లేదో చూడండి.")
                else:
                    lang_instruction = build_language_directive(report_lang)
                    comments_block = "\n".join(data["comments"][:15]) if data["comments"] else "No public comments available."
                    prompt = f"""
You are a warm, encouraging, expert human social media growth advisor ("సలహాదారు") for "1 AI, 1 India" (TrendSutra AI).
{lang_instruction}
Target Audience Scope: **{audience_scope}**.
Write a deeply helpful, easy-to-understand growth audit report (1,100 to 1,500 words). Use simple everyday spoken words (never use the word 'మెంటర్'—use 'సలహాదారు' in Telugu or equivalent friendly advisor word in the target language).

VIDEO DATA:
- Channel: {data['channel']}
- Title: {data['title']}
- Audio/Metadata Language Hint: {data['default_audio_lang'] or 'Auto-detect from title & comments'}
- Views: {data['views']:,} | Likes: {data['likes']:,} | Comments: {data['comment_count']:,}
- Description: {data['description']}
- Tags: {', '.join(data['tags'])}
- Real Audience Comments:
{comments_block}

STRICTLY FOLLOW THIS 6-SECTION STRUCTURE (Translate all headings into the report language):
### 🎬 1. Video Story Recap & Creator Appreciation
- Warmly retell the core story/message of this video based on its title, description, and comments so the creator feels you truly understood their hard work.
- Genuinely praise the creator's effort, topic choice, and presentation.

### 💬 2. Real Audience Comments & Sentiment
- Pick 4 to 5 real viewer comments from the list above, translate/present them naturally in the report language with the viewer's name, explain what viewers love or ask for, and give 3 ready-to-copy reply templates to boost engagement.

### 🔥 3. Next 3 Viral Video Ideas + 5-Sec Opening Hooks
- Give 3 fresh follow-up video ideas tailored to this Indian/global niche, each with an exact word-for-word **5-second opening Hook** and a **Thumbnail visual idea**.

### 🎯 4. Copy-Paste SEO Makeover (High-CTR Titles, Description & 15 Tags)
- Provide 3 clickable high-CTR title options, a strong 3-line SEO description hook, and 15 searchable comma-separated tags.

### 💰 5. Monetization & Brand Earning Blueprint
- Explain 3 practical ways this channel can earn money (AdSense, Affiliate links, Indian/Global Brand sponsorships).

### 📅 6. Step-by-Step 30-Day Action Plan
- Give a clear Week 1 to Week 4 checklist of simple actions to multiply views and subscribers.
"""
                    yt_status_slot.markdown('<div class="loading-pill">⚡ రిపోర్ట్ తయారవుతోంది... ⏳</div>', unsafe_allow_html=True)
                    report_box = st.empty()
                    full_text = ""
                    try:
                        for piece in generate_report_stream(prompt):
                            full_text += piece
                            report_box.markdown(full_text)
                        yt_status_slot.empty()
                        st.session_state.yt_report = full_text
                        st.session_state.yt_vid = vid_id
                        if not st.session_state.pro_unlocked:
                            increment_free_used(st.session_state.verified_email)
                        log_usage_to_sheet(st.session_state.verified_email or "PRO", "YouTube", yt_url.strip())
                        st.rerun()
                    except Exception as e:
                        yt_status_slot.empty()
                        st.error(str(e))

    if st.session_state.yt_report:
        st.success("✅ Growth Audit Report సిద్ధమైంది!")
        st.download_button(
            "📥 Download Complete Growth Report (.txt)",
            data=st.session_state.yt_report,
            file_name=f"TrendSutra_YouTube_Report_{st.session_state.yt_vid or 'audit'}.txt",
            mime="text/plain",
            use_container_width=True
        )
        st.markdown("---")
        st.markdown(st.session_state.yt_report)

with tab_ig:
    ic1, ic2, ic3 = st.columns([3.5, 1.5, 1.5])
    with ic1:
        ig_url = st.text_input("Instagram URL", placeholder="Paste Instagram Reel Link (https://www.instagram.com/reel/...)", label_visibility="collapsed")
    with ic2:
        run_ig = st.button("Generate Growth Report 🔍", key="btn_ig", type="primary", use_container_width=True)
    with ic3:
        ig_status_slot = st.empty()

    if run_ig:
        if not st.session_state.verified_email and not st.session_state.pro_unlocked:
            st.warning("⚠️ దయచేసి పైన Gmail లేదా Mail ID తో లాగిన్ అవ్వండి.")
        elif not ig_url.strip():
            st.warning("దయచేసి Instagram Reel లింక్ పేస్ట్ చేయండి.")
        elif not st.session_state.pro_unlocked and free_left <= 0:
            st.error("🔒 మీ 3 ఉచిత రిపోర్ట్‌లు పూర్తయ్యాయి! అన్‌లిమిటెడ్ రిపోర్ట్‌ల కోసం ఎడమ వైపు Pro Plan తీసుకోండి.")
        else:
            ig_status_slot.markdown('<div class="loading-pill">⚡ రిపోర్ట్ తయారవుతోంది... ⏳</div>', unsafe_allow_html=True)
            lang_instruction = build_language_directive(report_lang)
            ig_prompt = f"""
You are a warm, encouraging human Instagram Reels growth advisor ("సలహాదారు") for "1 AI, 1 India" (TrendSutra AI).
{lang_instruction}
Target Audience Scope: **{audience_scope}**.
Write a detailed 6-section Instagram Reels growth audit (1,000+ words) using simple spoken words (use 'సలహాదారు', never 'మెంటర్').
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
                if not st.session_state.pro_unlocked:
                    increment_free_used(st.session_state.verified_email)
                log_usage_to_sheet(st.session_state.verified_email or "PRO", "Instagram", ig_url.strip())
                st.rerun()
            except Exception as e:
                ig_status_slot.empty()
                st.error(str(e))

    if st.session_state.ig_report:
        st.success("✅ Instagram Growth Report సిద్ధమైంది!")
        st.download_button(
            "📥 Download Instagram Report (.txt)",
            data=st.session_state.ig_report,
            file_name="TrendSutra_Instagram_Report.txt",
            mime="text/plain",
            use_container_width=True
        )
        st.markdown("---")
        st.markdown(st.session_state.ig_report)

with tab_tt:
    tc1, tc2, tc3 = st.columns([3.5, 1.5, 1.5])
    with tc1:
        tt_url = st.text_input("TikTok URL", placeholder="Paste TikTok Video Link (https://www.tiktok.com/...)", label_visibility="collapsed")
    with tc2:
        run_tt = st.button("Generate Growth Report 🔍", key="btn_tt", type="primary", use_container_width=True)
    with tc3:
        tt_status_slot = st.empty()

    if run_tt:
        if not st.session_state.verified_email and not st.session_state.pro_unlocked:
            st.warning("⚠️ దయచేసి పైన Gmail లేదా Mail ID తో లాగిన్ అవ్వండి.")
        elif not tt_url.strip():
            st.warning("దయచేసి TikTok లింక్ పేస్ట్ చేయండి.")
        elif not st.session_state.pro_unlocked and free_left <= 0:
            st.error("🔒 మీ 3 ఉచిత రిపోర్ట్‌లు పూర్తయ్యాయి! అన్‌లిమిటెడ్ రిపోర్ట్‌ల కోసం ఎడమ వైపు Pro Plan తీసుకోండి.")
        else:
            tt_status_slot.markdown('<div class="loading-pill">⚡ రిపోర్ట్ తయారవుతోంది... ⏳</div>', unsafe_allow_html=True)
            lang_instruction = build_language_directive(report_lang)
            tt_prompt = f"""
You are a warm, encouraging human TikTok growth advisor ("సలహాదారు") for "1 AI, 1 India" (TrendSutra AI).
{lang_instruction}
Target Audience Scope: **{audience_scope}**.
Write a detailed 6-section TikTok growth audit (1,000+ words) using simple spoken words (use 'సలహాదారు', never 'మెంటర్').
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
                if not st.session_state.pro_unlocked:
                    increment_free_used(st.session_state.verified_email)
                log_usage_to_sheet(st.session_state.verified_email or "PRO", "TikTok", tt_url.strip())
                st.rerun()
            except Exception as e:
                tt_status_slot.empty()
                st.error(str(e))

    if st.session_state.tt_report:
        st.success("✅ TikTok Growth Report సిద్ధమైంది!")
        st.download_button(
            "📥 Download TikTok Report (.txt)",
            data=st.session_state.tt_report,
            file_name="TrendSutra_TikTok_Report.txt",
            mime="text/plain",
            use_container_width=True
        )
        st.markdown("---")
        st.markdown(st.session_state.tt_report)
