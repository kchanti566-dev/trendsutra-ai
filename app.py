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

# --- 1. PAGE CONFIG ---
page_icon_val = "logo.png" if os.path.exists("logo.png") else "🇮🇳"
st.set_page_config(page_title="TrendSutra AI - 1 AI • 1 India", page_icon=page_icon_val, layout="wide")

# --- 2. LOAD SECRETS (4 API KEYS SMART FAILOVER) ---
def get_gemini_keys():
    keys = []
    # Free tier keys first (Key 4 -> Key 3 -> Key 2), Paid key last (Key 1)
    for k_name in ["GEMINI_API_KEY_4", "GEMINI_API_KEY_3", "GEMINI_API_KEY_2", "GEMINI_API_KEY"]:
        val = str(st.secrets.get(k_name, "")).strip()
        if val and val not in keys:
            keys.append(val)
    return keys

GEMINI_KEYS = get_gemini_keys()
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

# --- ALL 22 INDIAN SCHEDULED LANGUAGES + BHOJPURI + GLOBAL (STRICT A TO Z ORDER) ---
LANGUAGES_A_TO_Z = [
    "Auto-Detect Video Language (ఆటోమేటిక్ భాష)",
    "Assamese (অসমীয়া)",
    "Bengali (বাংলা)",
    "Bhojpuri (भोजपुरी)",
    "Bodo (बड़ो)",
    "Dogri (डोगरी)",
    "English",
    "Gujarati (ગુજરાતી)",
    "Hindi (हिन्दी)",
    "Hinglish (Hindi + English)",
    "Kannada (ಕನ್ನಡ)",
    "Kashmiri (कॉशुर / کٲشُر)",
    "Konkani (कोंकणी)",
    "Maithili (मैथिली)",
    "Malayalam (മലയാളം)",
    "Manipuri (মৈতৈলোন্)",
    "Marathi (मराठी)",
    "Nepali (नेपाली)",
    "Odia (ଓଡ଼ିଆ)",
    "Punjabi (ਪੰਜਾਬੀ)",
    "Sanskrit (संस्कृतम्)",
    "Santali (ᱥᱟᱱᱛᱟᱲᱤ)",
    "Sindhi (सिन्धी / سنڌي)",
    "Tamil (தமிழ்)",
    "Telugu (తెలుగు)",
    "Tenglish (Telugu + English)",
    "Urdu (اردو)"
]

# --- 3. LOGO HELPER ---
def get_logo_base64():
    for fname in ["logo.png", "logo.jpg", "logo.jpeg", "logo.webp"]:
        if os.path.exists(fname):
            with open(fname, "rb") as f:
                return base64.b64encode(f.read()).decode()
    return ""

LOGO_B64 = get_logo_base64()

# --- 4. CUSTOM STYLING (CLEAN SINGLE-SCREEN + HIDE TOP RIGHT ICONS) ---
st.markdown("""
<style>
    /* Hide top-right Share, Star, Edit, GitHub icons while keeping sidebar expand button visible */
    [data-testid="stToolbarActions"],
    [data-testid="stDecoration"],
    #MainMenu,
    footer {
        display: none !important;
        visibility: hidden !important;
    }
    [data-testid="stSidebarCollapsedControl"] {
        display: flex !important;
        visibility: visible !important;
    }
    .block-container {
        padding-top: 0.7rem !important;
        padding-bottom: 0.8rem !important;
    }
    section[data-testid="stSidebar"] > div:first-child {
        padding-top: 0.6rem !important;
    }
    section[data-testid="stSidebar"] .stMarkdown p {
        margin-bottom: 0.25rem !important;
        font-size: 0.88rem !important;
    }
    section[data-testid="stSidebar"] hr {
        margin: 0.45rem 0 !important;
    }
    .center-header {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        padding: 12px 20px;
        border-radius: 12px;
        border-bottom: 3px solid #10b981;
        margin-bottom: 10px;
        text-align: center;
    }
    .center-title-row {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        gap: 10px;
    }
    .center-title-row img {
        height: 36px;
        width: 36px;
        border-radius: 8px;
        object-fit: cover;
    }
    .center-title-row h1 {
        margin: 0;
        font-size: 1.65rem;
        color: #ffffff;
        font-weight: 800;
        letter-spacing: 0.3px;
    }
    .center-subtitle {
        margin: 3px 0 0 0;
        color: #cbd5e1;
        font-size: 0.88rem;
    }
    .india-badge {
        display: inline-block;
        background: rgba(16, 185, 129, 0.18);
        border: 1px solid #10b981;
        color: #6ee7b7;
        padding: 1px 10px;
        border-radius: 20px;
        font-size: 0.76rem;
        font-weight: 600;
        margin-left: 6px;
    }
    .loading-pill {
        background: #064e3b;
        border: 1px solid #10b981;
        color: #ecfdf5;
        padding: 7px 14px;
        border-radius: 8px;
        font-weight: 600;
        font-size: 0.88rem;
        display: inline-flex;
        align-items: center;
        gap: 6px;
    }
</style>
""", unsafe_allow_html=True)

# --- 5. SESSION STATE ---
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
if "yt_vid_id" not in st.session_state:
    st.session_state.yt_vid_id = ""
if "ig_report" not in st.session_state:
    st.session_state.ig_report = ""
if "tt_report" not in st.session_state:
    st.session_state.tt_report = ""

# --- 6. CHECK GOOGLE OAUTH LOGIN ---
try:
    if hasattr(st, "user") and getattr(st.user, "is_logged_in", False):
        g_email = getattr(st.user, "email", "")
        if g_email:
            st.session_state.verified_email = g_email.strip().lower()
except Exception:
    pass

# --- 7. GOOGLE SHEET HELPERS (NO-CACHE LIVE SYNC) ---
def get_free_used_count(user_id):
    if not SHEET_API or not user_id:
        return 0
    try:
        r = requests.get(
            SHEET_API,
            params={"device": user_id.strip().lower(), "_ts": str(random.randint(10000, 99999))},
            allow_redirects=True,
            timeout=10
        )
        if r.status_code == 200 and r.text.strip().isdigit():
            return min(3, int(r.text.strip()))
    except Exception:
        pass
    return 0

def increment_free_used(user_id):
    if not SHEET_API or not user_id:
        return
    clean_id = user_id.strip().lower()
    for _ in range(2):
        try:
            r = requests.get(
                SHEET_API,
                params={"device": clean_id, "inc": "1", "_ts": str(random.randint(10000, 99999))},
                allow_redirects=True,
                timeout=10
            )
            if r.status_code == 200 and r.text.strip().isdigit():
                return
        except Exception:
            pass

def log_usage_to_sheet(user_id, platform, url):
    if not SHEET_API:
        return
    try:
        requests.get(
            SHEET_API,
            params={
                "log": "1",
                "device": (user_id or "PRO").strip().lower(),
                "platform": platform,
                "url": url,
                "_ts": str(random.randint(10000, 99999))
            },
            allow_redirects=True,
            timeout=8
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
            params={"pid": pid, "plan": plan, "_ts": str(random.randint(10000, 99999))},
            allow_redirects=True,
            timeout=10
        )
        if r.status_code == 200:
            res = r.text.strip().upper()
            if res in ["VALID", "ALREADY_USED", "EXPIRED", "INVALID"]:
                return res
    except Exception:
        pass
    return "ERROR"

# --- 8. AUTO-DETECT RAZORPAY REDIRECT ---
try:
    q_pid = st.query_params.get("razorpay_payment_id", "")
    if q_pid and not st.session_state.pro_unlocked:
        st_res = verify_payment_id(str(q_pid), plan="1m")
        if st_res == "VALID":
            st.session_state.pro_unlocked = True
            st.session_state.pro_label = "PRO UNLIMITED ACTIVE"
            st.query_params.clear()
            st.rerun()
except Exception:
    pass

def send_otp_email(to_email, code):
    if not SENDER_EMAIL or not SENDER_PASS:
        return False, "SMTP not configured"
    try:
        body_text = (
            "Welcome to TrendSutra AI (1 AI • 1 India)!\n\n"
            f"Your 6-digit verification code is: {code}\n\n"
            "Enter this code on TrendSutra AI to unlock your 3 Free Growth Reports.\n"
            "Do not share this OTP with anyone."
        )
        msg = MIMEText(body_text)
        msg["Subject"] = f"{code} is your TrendSutra AI Verification Code"
        msg["From"] = f"TrendSutra AI <{SENDER_EMAIL}>"
        msg["To"] = to_email

        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=12) as server:
            server.login(SENDER_EMAIL, SENDER_PASS)
            server.sendmail(SENDER_EMAIL, [to_email], msg.as_string())
        return True, "SENT"
    except Exception as e:
        return False, str(e)

# --- 9. YOUTUBE DATA FETCHER ---
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
            "title": snip.get("title", ""),
            "channel": snip.get("channelTitle", ""),
            "default_audio_lang": snip.get("defaultAudioLanguage", snip.get("defaultLanguage", "auto")),
            "description": snip.get("description", "")[:1200],
            "tags": snip.get("tags", [])[:20],
            "views": int(stats.get("viewCount", 0)),
            "likes": int(stats.get("likeCount", 0)),
            "comment_count": int(stats.get("commentCount", 0)),
            "comments": comments
        }
    except Exception:
        return None

# --- 10. GEMINI AI STREAMING (4-KEY FREE-TO-PAID SMART FAILOVER, SINGLE API CALL) ---
def clean_mentor_word(text):
    return text.replace("మెంటర్", "సలహాదారు").replace("స్ట్రాటజిస్ట్", "సలహాదారు")

def generate_report_stream(prompt):
    if not GEMINI_KEYS:
        raise RuntimeError("API కీ కన్ఫిగర్ చేయబడలేదు.")

    models = [
        "gemini-2.5-flash-lite",
        "gemini-2.5-flash",
        "gemini-3.5-flash-lite",
        "gemini-3.5-flash"
    ]
    last_err = ""
    # Try Free Keys first (Key 4 -> Key 3 -> Key 2), then Paid Key (Key 1)
    for api_key in GEMINI_KEYS:
        try:
            client = genai.Client(api_key=api_key)
        except Exception as e:
            last_err = str(e)
            continue

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

    raise RuntimeError(f"AI సర్వర్ రద్దీగా ఉంది. దయచేసి 5 సెకన్ల తర్వాత మళ్ళీ ప్రయత్నించండి. ({last_err})")

# --- 11. CENTERED HEADER WITH LOGO ---
logo_html = f'<img src="data:image/png;base64,{LOGO_B64}" alt="Logo">' if LOGO_B64 else ""
st.markdown(f"""
<div class="center-header">
    <div class="center-title-row">
        {logo_html}
        <h1>TrendSutra AI <span class="india-badge">🇮🇳 1 AI • 1 India</span></h1>
    </div>
    <p class="center-subtitle">A to Z Growth Analyzer in All 22 Indian Languages + Bhojpuri for YouTube, Instagram & TikTok</p>
</div>
""", unsafe_allow_html=True)

# --- 12. COMPACT NO-SCROLL SIDEBAR (A TO Z SEARCHABLE LANGUAGE BAR) ---
with st.sidebar:
    st.markdown("### ⚙️ Settings")
    report_lang = st.selectbox(
        "🔍 Type to Search Language (A–Z):",
        LANGUAGES_A_TO_Z,
        index=0,
        placeholder="Type language name (e.g. Telugu, Hindi, Tamil)..."
    )
    audience_scope = st.radio("Audience:", ["Regional", "Global", "Both"], horizontal=True, label_visibility="collapsed")

    st.divider()
    free_used = get_free_used_count(st.session_state.verified_email) if st.session_state.verified_email else 0
    free_left = max(0, 3 - free_used)

    st.markdown("### 💎 Pro Plans")
    if st.session_state.pro_unlocked:
        st.success(f"✅ {st.session_state.pro_label}")
    elif st.session_state.verified_email:
        if free_left > 0:
            st.info(f"🎁 Free Trial: **{free_left}/3** left")
        else:
            st.error("🔒 **0/3** Free Reports Left")
    else:
        st.info("🎁 Login for **3 Free Reports**")

    st.markdown(f"• **1 Month:** ₹100 👉 [Pay ₹100]({RAZORPAY_1M})")
    st.markdown(f"• **12 Months:** ₹1,000 👉 [Pay ₹1,000]({RAZORPAY_12M})")

    plan_choice = st.radio("Plan:", ["1M (₹100)", "12M (₹1,000)"], horizontal=True, label_visibility="collapsed")
    pay_input = st.text_input("Payment ID:", placeholder="Paste Payment ID (pay_...)", label_visibility="collapsed")
    if st.button("Unlock Pro 🔓", use_container_width=True):
        if not pay_input.strip():
            st.warning("Enter Payment ID")
        else:
            p_code = "12m" if "12M" in plan_choice else "1m"
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
                st.error("⏰ Plan Expired!")
            elif status == "ALREADY_USED":
                st.error("❌ Used on 3 devices")
            else:
                st.error("❌ Invalid Payment ID")

    st.divider()
    st.caption("📩 support@aiengtel.com | aiengtel.com")

# --- 13. INLINE LOGIN BAR (ALIGNED IN ONE ROW) ---
if not st.session_state.verified_email and not st.session_state.pro_unlocked:
    lc1, lc2, lc3, lc4 = st.columns([2.1, 0.35, 2.3, 1.35], vertical_alignment="bottom")
    with lc1:
        if st.button("🔵 Continue with Gmail", type="primary", use_container_width=True):
            try:
                st.login("google")
            except Exception as e:
                st.error(f"Google Login error: {e}")
    with lc2:
        st.markdown("<div style='text-align:center; padding-bottom:8px; font-weight:700; color:#94a3b8;'>OR</div>", unsafe_allow_html=True)
    with lc3:
        email_in = st.text_input("Login with Mail ID", placeholder="Login with Mail ID (name@email.com)", label_visibility="collapsed")
    with lc4:
        if st.button("Send OTP 📩", use_container_width=True):
            clean_em = email_in.strip().lower()
            if "@" not in clean_em or "." not in clean_em.split("@")[-1]:
                st.error("❌ సరైన Mail ID ఇవ్వండి")
            elif clean_em.split("@")[-1] in TEMP_DOMAINS:
                st.error("❌ Temp Mail అనుమతించబడదు")
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
        oc1, oc2 = st.columns([3, 1.5], vertical_alignment="bottom")
        with oc1:
            otp_in = st.text_input("Enter OTP", placeholder=f"Enter 6-digit OTP sent to {st.session_state.otp_target}", max_chars=6, label_visibility="collapsed")
        with oc2:
            if st.button("Verify OTP ✅", type="primary", use_container_width=True):
                if otp_in.strip() == st.session_state.otp_code:
                    st.session_state.verified_email = st.session_state.otp_target
                    st.session_state.otp_code = ""
                    st.rerun()
                else:
                    st.error("❌ తప్పు OTP!")
else:
    u_col1, u_col2 = st.columns([4.5, 1.2], vertical_alignment="center")
    with u_col1:
        who = st.session_state.verified_email if st.session_state.verified_email else st.session_state.pro_label
        badge = "UNLIMITED PRO" if st.session_state.pro_unlocked else f"{free_left}/3 ఉచిత రిపోర్ట్‌లు మిగిలాయి"
        st.caption(f"👤 Logged in as **{who}**  |  🎁 **{badge}**")
    with u_col2:
        if st.button("Logout 🚪", use_container_width=True):
            st.session_state.verified_email = ""
            st.session_state.pro_unlocked = False
            st.session_state.yt_report = ""
            st.session_state.ig_report = ""
            st.session_state.tt_report = ""
            try:
                if hasattr(st, "logout"):
                    st.logout()
            except Exception:
                pass
            st.rerun()

# --- 14. LANGUAGE INSTRUCTION HELPER (SINGLE API CALL) ---
def build_language_rule(selected_lang):
    if "Auto-Detect" in selected_lang:
        return (
            "AUTOMATIC LANGUAGE DETECTION & OUTPUT RULE:\n"
            "1. First, automatically detect the primary language of the video from its Title, Description, Audio Tag, and Audience Comments.\n"
            "2. At the very top of your response, display: `🌐 Detected Video Language: <Language Name>`.\n"
            "3. Write the ENTIRE report (all 6 sections + translated comments) in that EXACT detected language in simple, natural everyday spoken style.\n"
            "4. If the video is in Telugu, NEVER use the word 'మెంటర్'—use 'సలహాదారు'."
        )
    else:
        return (
            f"TARGET LANGUAGE RULE:\n"
            f"Write the ENTIRE report (all 6 sections + translated audience comments) in **{selected_lang}** using simple, natural everyday spoken words.\n"
            f"If writing in Telugu, NEVER use the word 'మెంటర్'—use 'సలహాదారు'."
        )

# --- 15. MAIN ANALYZER TABS ---
tab_yt, tab_ig, tab_tt = st.tabs(["📺 YouTube Analyzer", "📸 Instagram Reels Analyzer", "🎵 TikTok Analyzer"])

with tab_yt:
    yc1, yc2 = st.columns([3.6, 1.6], vertical_alignment="bottom")
    with yc1:
        yt_url = st.text_input("YouTube Link", placeholder="Paste YouTube Video or Shorts Link (https://youtube.com/...)", label_visibility="collapsed")
    with yc2:
        run_yt = st.button("Generate Growth Report 🔍", key="btn_yt", type="primary", use_container_width=True)
    yt_status_slot = st.empty()

    if run_yt:
        if not st.session_state.verified_email and not st.session_state.pro_unlocked:
            st.warning("⚠️ దయచేసి ముందుగా పైన Gmail లేదా Mail ID OTP తో లాగిన్ అవ్వండి.")
        elif not yt_url.strip():
            st.warning("⚠️ దయచేసి YouTube లింక్ పేస్ట్ చేయండి.")
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
                    m1, m2, m3 = st.columns(3)
                    m1.metric("👀 Views", f"{data['views']:,}")
                    m2.metric("👍 Likes", f"{data['likes']:,}")
                    m3.metric("💬 Comments", f"{data['comment_count']:,}")

                    comments_block = "\n".join(data["comments"][:15]) if data["comments"] else "No public comments available."
                    lang_rule = build_language_rule(report_lang)
                    prompt = f"""
You are a warm, encouraging, expert human social media growth advisor ("సలహాదారు").
Write a comprehensive, deeply detailed, easy-to-understand growth audit report (1,100 to 1,500 words) for a **{audience_scope}** audience.
{lang_rule}

VIDEO DATA:
- Channel: {data['channel']}
- Title: {data['title']}
- Audio Language Tag: {data['default_audio_lang']}
- Views: {data['views']:,} | Likes: {data['likes']:,} | Comments: {data['comment_count']:,}
- Description: {data['description']}
- Tags: {', '.join(data['tags'])}
- Real Audience Comments:
{comments_block}

STRICTLY FOLLOW THIS 6-SECTION STRUCTURE (Translate headings into the target/detected language):
### 🎬 1. Video Story Recap & Creator Appreciation
- Warmly retell the core story/message of this video based on its title, description, and comments so the creator feels you truly watched and understood their hard work.
- Genuinely praise the creator's effort, topic choice, and presentation.

### 💬 2. Real Audience Comments & Replies
- Pick 4 to 5 real viewer comments from the list above, translate them naturally into the target/detected language, quote them with the viewer's name, explain what viewers love or ask for, and give 3 ready-to-copy reply templates.

### 🔥 3. 3 Next Viral Video Ideas + 5-Sec Hooks
- Give 3 fresh follow-up video ideas tailored to this channel, each with an exact word-for-word **5-second opening Hook** and **Thumbnail visual idea**.

### 🎯 4. Copy-Paste SEO Makeover (Titles, Description & 15 Tags)
- Provide 3 clickable high-CTR titles, a 3-line SEO description hook, and 15 searchable comma-separated tags.

### 💰 5. Monetization & Brand Earning Blueprint
- Explain 3 practical ways this channel can earn money (AdSense, Affiliate links, Sponsorships).

### 📅 6. Step-by-Step 30-Day Action Plan
- Give a clear Week 1 to Week 4 checklist of simple actions to grow views and subscribers.
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
                        st.session_state.yt_vid_id = vid_id
                        if not st.session_state.pro_unlocked:
                            increment_free_used(st.session_state.verified_email)
                        log_usage_to_sheet(st.session_state.verified_email or "PRO", "YouTube", yt_url.strip())
                        st.rerun()
                    except Exception as e:
                        yt_status_slot.empty()
                        st.error(str(e))

    if st.session_state.yt_report:
        st.markdown(st.session_state.yt_report)
        st.download_button(
            "📥 Download Complete Growth Report (.txt)",
            data=st.session_state.yt_report,
            file_name=f"TrendSutra_YouTube_Report_{st.session_state.yt_vid_id or 'audit'}.txt",
            mime="text/plain",
            key="dl_yt_saved",
            use_container_width=True
        )

with tab_ig:
    ic1, ic2 = st.columns([3.6, 1.6], vertical_alignment="bottom")
    with ic1:
        ig_url = st.text_input("Instagram Link", placeholder="Paste Instagram Reel Link (https://instagram.com/reel/...)", label_visibility="collapsed")
    with ic2:
        run_ig = st.button("Generate Instagram Report 🔍", key="btn_ig", type="primary", use_container_width=True)
    ig_status_slot = st.empty()

    if run_ig:
        if not st.session_state.verified_email and not st.session_state.pro_unlocked:
            st.warning("⚠️ దయచేసి ముందుగా పైన లాగిన్ అవ్వండి.")
        elif not ig_url.strip():
            st.warning("⚠️ దయచేసి Instagram Reel లింక్ పేస్ట్ చేయండి.")
        elif not st.session_state.pro_unlocked and free_left <= 0:
            st.error("🔒 మీ 3 ఉచిత రిపోర్ట్‌లు పూర్తయ్యాయి! అన్‌లిమిటెడ్ రిపోర్ట్‌ల కోసం Pro Plan తీసుకోండి.")
        else:
            ig_status_slot.markdown('<div class="loading-pill">⚡ Instagram రిపోర్ట్ తయారవుతోంది... ⏳</div>', unsafe_allow_html=True)
            lang_rule = build_language_rule(report_lang)
            ig_prompt = f"""
You are a warm, encouraging human Instagram Reels growth advisor ("సలహాదారు").
Write a detailed 6-section Instagram Reels growth audit (1,000+ words) for a **{audience_scope}** audience.
{lang_rule}
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
        st.markdown(st.session_state.ig_report)
        st.download_button(
            "📥 Download Instagram Report (.txt)",
            data=st.session_state.ig_report,
            file_name="TrendSutra_Instagram_Report.txt",
            mime="text/plain",
            key="dl_ig_saved",
            use_container_width=True
        )

with tab_tt:
    tc1, tc2 = st.columns([3.6, 1.6], vertical_alignment="bottom")
    with tc1:
        tt_url = st.text_input("TikTok Link", placeholder="Paste TikTok Video Link (https://tiktok.com/...)", label_visibility="collapsed")
    with tc2:
        run_tt = st.button("Generate TikTok Report 🔍", key="btn_tt", type="primary", use_container_width=True)
    tt_status_slot = st.empty()

    if run_tt:
        if not st.session_state.verified_email and not st.session_state.pro_unlocked:
            st.warning("⚠️ దయచేసి ముందుగా పైన లాగిన్ అవ్వండి.")
        elif not tt_url.strip():
            st.warning("⚠️ దయచేసి TikTok లింక్ పేస్ట్ చేయండి.")
        elif not st.session_state.pro_unlocked and free_left <= 0:
            st.error("🔒 మీ 3 ఉచిత రిపోర్ట్‌లు పూర్తయ్యాయి! అన్‌లిమిటెడ్ రిపోర్ట్‌ల కోసం Pro Plan తీసుకోండి.")
        else:
            tt_status_slot.markdown('<div class="loading-pill">⚡ TikTok రిపోర్ట్ తయారవుతోంది... ⏳</div>', unsafe_allow_html=True)
            lang_rule = build_language_rule(report_lang)
            tt_prompt = f"""
You are a warm, encouraging human TikTok growth advisor ("సలహాదారు").
Write a detailed 6-section TikTok growth audit (1,000+ words) for a **{audience_scope}** audience.
{lang_rule}
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
        st.markdown(st.session_state.tt_report)
        st.download_button(
            "📥 Download TikTok Report (.txt)",
            data=st.session_state.tt_report,
            file_name="TrendSutra_TikTok_Report.txt",
            mime="text/plain",
            key="dl_tt_saved",
            use_container_width=True
        )
