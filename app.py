import streamlit as st
from google import genai
from google.genai import types
from googleapiclient.discovery import build
import re
import requests
import random
import smtplib
import time
import base64
import os
from email.mime.text import MIMEText

# --- 1. PAGE CONFIG ---
PAGE_ICON = "logo.png" if os.path.exists("logo.png") else "🇮🇳"
st.set_page_config(page_title="TrendSutra AI - 1 AI • 1 India", page_icon=PAGE_ICON, layout="wide")

# --- 2. LOAD SECRETS (4-KEY SMART FAILOVER: FREE KEYS FIRST -> PAID KEY LAST) ---
KEY_1_PAID = str(st.secrets.get("GEMINI_API_KEY", "")).strip()
KEY_2_FREE = str(st.secrets.get("GEMINI_API_KEY_2", "")).strip()
KEY_3_FREE = str(st.secrets.get("GEMINI_API_KEY_3", "")).strip()
KEY_4_FREE = str(st.secrets.get("GEMINI_API_KEY_4", "")).strip()

GEMINI_KEYS = [k for k in [KEY_4_FREE, KEY_3_FREE, KEY_2_FREE, KEY_1_PAID] if k]

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

# --- ALL 22 CONSTITUTIONAL INDIAN LANGUAGES + BHOJPURI + GLOBAL (STRICTLY A-Z SORTED) ---
LANGUAGES_LIST = [
    "Auto-Detect Video Language",
    "Assamese (অসমীয়া)",
    "Bengali (বাংলা)",
    "Bhojpuri (भोजपुरी)",
    "Bodo (बर')",
    "Dogri (डोगरी)",
    "English",
    "Gujarati (ગુજરાતી)",
    "Hindi (हिन्दी)",
    "Hinglish (Hindi + English)",
    "Kannada (ಕನ್ನಡ)",
    "Kashmiri (कॉशुर / كٲشُر)",
    "Konkani (कोंकणी)",
    "Maithili (मैथिली)",
    "Malayalam (മലയാളം)",
    "Manipuri / Meitei (ꯃꯩꯇꯩꯂꯣꯟ)",
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

# --- 3. CUSTOM STYLING (100% CLEAN ENGLISH UI, NO TOP RIGHT ICONS, COMPACT SIDEBAR) ---
st.markdown("""
<style>
    /* Hide right-side toolbar icons (Share, Star, Edit, GitHub) while keeping left sidebar toggle button */
    [data-testid="stToolbarActions"], .stAppDeployButton, #MainMenu, footer {
        visibility: hidden !important;
        display: none !important;
    }
    header[data-testid="stHeader"] {
        background: transparent !important;
        height: 2.2rem !important;
    }
    .block-container {
        padding-top: 0.6rem !important;
        padding-bottom: 0.8rem !important;
        max-width: 1220px !important;
    }
    /* Compact no-scroll sidebar */
    section[data-testid="stSidebar"] > div:first-child {
        padding-top: 0.6rem !important;
        padding-bottom: 0.4rem !important;
    }
    section[data-testid="stSidebar"] .stMarkdown p {
        margin-bottom: 0.25rem !important;
        font-size: 0.86rem !important;
    }
    section[data-testid="stSidebar"] hr {
        margin: 0.45rem 0 !important;
    }
    /* Centered Brand Header */
    .brand-banner {
        background: linear-gradient(135deg, #0b132b 0%, #1c2541 100%);
        border: 1px solid #334155;
        border-bottom: 3px solid #10b981;
        border-radius: 12px;
        padding: 12px 20px;
        margin-bottom: 10px;
        text-align: center;
    }
    .brand-title-row {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 12px;
    }
    .brand-title-row img {
        height: 40px;
        width: 40px;
        border-radius: 8px;
        object-fit: contain;
    }
    .brand-title-row h1 {
        margin: 0 !important;
        padding: 0 !important;
        font-size: 1.7rem !important;
        font-weight: 800 !important;
        color: #ffffff !important;
        letter-spacing: -0.3px;
    }
    .india-badge {
        background: rgba(16, 185, 129, 0.16);
        border: 1px solid #10b981;
        color: #34d399;
        padding: 2px 10px;
        border-radius: 20px;
        font-size: 0.78rem;
        font-weight: 700;
    }
    .brand-subtitle {
        margin: 4px 0 0 0 !important;
        color: #cbd5e1 !important;
        font-size: 0.9rem !important;
        text-align: center;
    }
    /* Compact Login & Status Strip */
    .status-strip {
        background: #111827;
        border: 1px solid #374151;
        border-radius: 10px;
        padding: 8px 14px;
        margin-bottom: 10px;
        color: #e5e7eb;
        font-size: 0.88rem;
    }
    .loading-pill {
        background: rgba(16, 185, 129, 0.15);
        border: 1px solid #10b981;
        color: #34d399;
        padding: 8px 14px;
        border-radius: 8px;
        font-weight: 600;
        font-size: 0.9rem;
        display: inline-block;
        margin-bottom: 8px;
    }
    /* Equal alignment for horizontal buttons & inputs */
    div[data-testid="stHorizontalBlock"] {
        align-items: flex-end !important;
    }
</style>
""", unsafe_allow_html=True)

# --- 4. SESSION STATE INITIALIZATION ---
defaults = {
    "verified_email": "",
    "otp_code": "",
    "otp_target": "",
    "pro_unlocked": False,
    "pro_label": "",
    "yt_report": "",
    "yt_vid_id": "",
    "yt_stats": None,
    "yt_lang_detected": "",
    "ig_report": "",
    "tt_report": "",
    "local_used_fallback": 0
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# --- 5. CHECK GOOGLE OAUTH LOGIN ---
try:
    if hasattr(st, "user") and getattr(st.user, "is_logged_in", False):
        g_email = getattr(st.user, "email", "")
        if g_email:
            st.session_state.verified_email = g_email.strip().lower()
except Exception:
    pass

# --- 6. GOOGLE SHEET HELPERS (NO-CACHE LIVE SYNC) ---
def get_free_used_count(user_id):
    if not user_id:
        return 0
    if not SHEET_API:
        return st.session_state.local_used_fallback
    try:
        r = requests.get(
            SHEET_API,
            params={"device": user_id, "_ts": str(int(time.time() * 1000))},
            timeout=10,
            allow_redirects=True
        )
        if r.status_code == 200:
            txt = r.text.strip()
            if txt.isdigit():
                val = min(3, int(txt))
                st.session_state.local_used_fallback = max(st.session_state.local_used_fallback, val)
                return st.session_state.local_used_fallback
    except Exception:
        pass
    return st.session_state.local_used_fallback

def increment_free_used(user_id):
    if not user_id:
        return
    st.session_state.local_used_fallback = min(3, st.session_state.local_used_fallback + 1)
    if not SHEET_API:
        return
    for _ in range(2):
        try:
            r = requests.get(
                SHEET_API,
                params={"device": user_id, "inc": "1", "_ts": str(int(time.time() * 1000))},
                timeout=10,
                allow_redirects=True
            )
            if r.status_code == 200 and r.text.strip().isdigit():
                st.session_state.local_used_fallback = min(3, int(r.text.strip()))
                break
        except Exception:
            time.sleep(0.4)

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
                "_ts": str(int(time.time() * 1000))
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
            params={"pid": pid, "plan": plan, "_ts": str(int(time.time() * 1000))},
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

# --- 7. AUTO-CHECK RAZORPAY REDIRECT URL PARAM ---
try:
    qp = st.query_params
    auto_pid = qp.get("razorpay_payment_id", "") or qp.get("payment_id", "")
    if auto_pid and not st.session_state.pro_unlocked:
        st_res = verify_payment_id(auto_pid, plan="1m")
        if st_res in ["VALID", "OWNER"]:
            st.session_state.pro_unlocked = True
            st.session_state.pro_label = "PRO UNLIMITED ACTIVE"
            st.query_params.clear()
except Exception:
    pass

def send_otp_email(to_email, code):
    if not SENDER_EMAIL or not SENDER_PASS:
        return False, "SMTP email credentials missing in Secrets."
    try:
        msg = MIMEText(
            f"Welcome to TrendSutra AI (1 AI • 1 India)!\n\n"
            f"Your 6-digit verification code is: {code}\n\n"
            f"Enter this code on TrendSutra AI to unlock your 3 Free Growth Reports."
        )
        msg["Subject"] = f"{code} is your TrendSutra AI Verification Code"
        msg["From"] = f"TrendSutra AI <{SENDER_EMAIL}>"
        msg["To"] = to_email

        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=12) as server:
            server.login(SENDER_EMAIL, SENDER_PASS)
            server.sendmail(SENDER_EMAIL, [to_email], msg.as_string())
        return True, "SENT"
    except Exception as e:
        return False, str(e)

# --- 8. YOUTUBE DATA FETCHER ---
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

# --- 9. GEMINI AI STREAMING (SINGLE-CALL UNIFIED LANGUAGE + REPORT + 4-KEY FAILOVER) ---
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
    return preferred[:3]

def clean_advisor_word(text):
    return text.replace("మెంటర్", "సలహాదారు").replace("స్ట్రాటజిస్ట్", "సలహాదారు")

def generate_report_stream(prompt):
    if not GEMINI_KEYS:
        raise RuntimeError("No Gemini API keys configured in Streamlit Secrets.")
    last_err = ""
    for api_key in GEMINI_KEYS:
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
                            yield clean_advisor_word(chunk.text)
                    if yielded_any:
                        return
                except Exception as e:
                    last_err = str(e)
                    continue
        except Exception as e:
            last_err = str(e)
            continue
    raise RuntimeError(f"AI servers are busy right now. Please try again in 5 seconds. ({last_err})")

# --- 10. CENTERED HEADER WITH LOGO ---
logo_html = ""
if os.path.exists("logo.png"):
    with open("logo.png", "rb") as f:
        b64_logo = base64.b64encode(f.read()).decode()
    logo_html = f'<img src="data:image/png;base64,{b64_logo}" alt="Logo">'

st.markdown(f"""
<div class="brand-banner">
    <div class="brand-title-row">
        {logo_html}
        <h1>TrendSutra AI</h1>
        <span class="india-badge">🇮🇳 1 AI • 1 India</span>
    </div>
    <p class="brand-subtitle">A to Z Growth Analyzer in All 22 Indian Languages + Bhojpuri for YouTube, Instagram & TikTok</p>
</div>
""", unsafe_allow_html=True)

# --- 11. COMPACT SIDEBAR (NO SCROLL, 100% ENGLISH UI) ---
with st.sidebar:
    st.markdown("### ⚙️ Settings")
    report_lang = st.selectbox(
        "🔍 Type to Search Language (A–Z):",
        LANGUAGES_LIST,
        index=0
    )
    audience_scope = st.radio("Target Audience:", ["Regional", "Global", "Both"], horizontal=True)

    st.divider()
    st.markdown("### 💎 Pro Plans")

    free_used = get_free_used_count(st.session_state.verified_email) if st.session_state.verified_email else 0
    free_left = max(0, 3 - free_used)

    if st.session_state.pro_unlocked:
        st.success(f"✅ {st.session_state.pro_label}")
    elif st.session_state.verified_email:
        if free_left > 0:
            st.info(f"🎁 Free Trial: **{free_left}/3 left**")
        else:
            st.error("🔒 0/3 Free Reports Left")
    else:
        st.info("🎁 Login for **3 Free Reports**")

    st.markdown(f"• **1 Month:** ₹100 👉 [Pay ₹100]({RAZORPAY_1M})")
    st.markdown(f"• **12 Months:** ₹1,000 👉 [Pay ₹1,000]({RAZORPAY_12M})")

    plan_choice = st.radio("Plan:", ["1M (₹100)", "12M (₹1,000)"], horizontal=True, label_visibility="collapsed")
    pay_input = st.text_input("Payment ID:", placeholder="Paste Payment ID (pay_...)", label_visibility="collapsed")
    if st.button("Unlock Pro 🔓", use_container_width=True):
        if not pay_input.strip():
            st.warning("Enter your Payment ID.")
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
                st.error("⏰ Plan expired! Please renew.")
            elif status == "ALREADY_USED":
                st.error("❌ Used on 3 devices already.")
            else:
                st.error("❌ Invalid Payment ID.")

    st.divider()
    st.caption("📩 support@aiengtel.com | aiengtel.com")

# --- 12. SINGLE-ROW COMPACT LOGIN BAR OR USER STATUS BAR ---
if not st.session_state.verified_email and not st.session_state.pro_unlocked:
    st.markdown('<div class="status-strip">🔐 <b>Sign in to get 3 Free Growth Reports</b> (Choose Google 1-Click or Email OTP):</div>', unsafe_allow_html=True)
    lc1, lc2, lc3, lc4 = st.columns([2.2, 0.5, 2.5, 1.5])
    with lc1:
        if st.button("🔵 Continue with Gmail", type="primary", use_container_width=True):
            try:
                st.login("google")
            except Exception as e:
                st.error(f"Google Login error: {e}")
    with lc2:
        st.markdown("<div style='text-align:center; padding-bottom:8px; color:#94a3b8; font-weight:700;'>OR</div>", unsafe_allow_html=True)
    with lc3:
        email_in = st.text_input("Email", placeholder="Login with Mail ID (e.g. name@gmail.com)", label_visibility="collapsed")
    with lc4:
        send_otp_btn = st.button("Send OTP 📩", use_container_width=True)

    if send_otp_btn:
        clean_em = email_in.strip().lower()
        if "@" not in clean_em or "." not in clean_em.split("@")[-1]:
            st.error("❌ Please enter a valid Email ID.")
        elif clean_em.split("@")[-1] in TEMP_DOMAINS:
            st.error("❌ Temporary email domains are not allowed.")
        else:
            code = str(random.randint(100000, 999999))
            ok, err_msg = send_otp_email(clean_em, code)
            if ok:
                st.session_state.otp_code = code
                st.session_state.otp_target = clean_em
                st.success(f"✅ 6-digit OTP sent to {clean_em}! Check your inbox or spam folder.")
            else:
                st.error(f"OTP Error: {err_msg}")

    if st.session_state.otp_target:
        oc1, oc2 = st.columns([3, 1.5])
        with oc1:
            otp_in = st.text_input("OTP", placeholder=f"Enter 6-digit OTP sent to {st.session_state.otp_target}", max_chars=6, label_visibility="collapsed")
        with oc2:
            if st.button("Verify OTP ✅", type="primary", use_container_width=True):
                if otp_in.strip() == st.session_state.otp_code:
                    st.session_state.verified_email = st.session_state.otp_target
                    st.session_state.otp_code = ""
                    st.rerun()
                else:
                    st.error("❌ Incorrect OTP. Please try again.")
    st.stop()
else:
    ub1, ub2 = st.columns([5, 1.2])
    with ub1:
        badge_txt = f"👑 {st.session_state.pro_label}" if st.session_state.pro_unlocked else f"🎁 {free_left}/3 Free Reports Left"
        st.markdown(f'<div class="status-strip">👤 Logged in as <b>{st.session_state.verified_email or "Pro User"}</b> &nbsp;|&nbsp; {badge_txt}</div>', unsafe_allow_html=True)
    with ub2:
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

# --- 13. HELPER FOR SINGLE-PASS UNIFIED LANGUAGE INSTRUCTION ---
def build_language_directive(selected_lang):
    if selected_lang.startswith("Auto-Detect"):
        return """
LANGUAGE RULE (SINGLE-PASS AUTO-DETECT & NATIVE SCRIPT):
1. First, automatically detect the primary language of the video from its title, audio language tag, description, and audience comments.
2. On the very first line of your output, write ONLY:
   🌐 **Detected Video Language:** <Language Name>
3. Then write the ENTIRE 6-section report (including all 6 section headings and every paragraph) in that detected language using its **authentic native script** (e.g. Telugu in తెలుగు script, Tamil in தமிழ் script, Hindi in हिन्दी Devanagari script, Urdu in اردو script, Kannada in ಕನ್ನಡ script, Malayalam in മലയാളം script, Bengali in বাংলা script, Marathi in मराठी script, Gujarati in ગુજરાતી script, Punjabi in ਪੰਜਾਬੀ script, etc. Do NOT write Indian languages in Roman/English letters unless Hinglish or Tenglish is detected).
"""
    else:
        return f"""
LANGUAGE RULE (NATIVE SCRIPT REQUIRED):
Write the ENTIRE 6-section report (including all 6 section headings and every paragraph) in **{selected_lang}** using its **authentic native script** (for example: Telugu in తెలుగు script, Tamil in தமிழ் script, Hindi in हिन्दी script, Urdu in اردو script, Kannada in ಕನ್ನಡ script, Malayalam in മലയാളം script, Bengali in বাংলা script, Marathi in मराठी script, Gujarati in ગુજરાતી script, Punjabi in ਪੰਜਾਬੀ script, Odia in ଓଡ଼ିଆ script, Assamese in অসমীয়া script, Bhojpuri in भोजपुरी script, etc.). Do NOT write in Roman/English letters unless English, Hinglish, or Tenglish is selected.
"""

# --- 14. MAIN WORKSPACE TABS ---
tab_yt, tab_ig, tab_tt = st.tabs(["📺 YouTube Analyzer", "📸 Instagram Reels Analyzer", "🎵 TikTok Analyzer"])

with tab_yt:
    yc1, yc2 = st.columns([4.2, 1.5])
    with yc1:
        yt_url = st.text_input("YT Link", placeholder="Paste YouTube Video or Shorts Link (https://youtube.com/...)", label_visibility="collapsed")
    with yc2:
        run_yt = st.button("Generate Growth Report 🔍", key="btn_yt", type="primary", use_container_width=True)

    yt_status_slot = st.empty()

    if run_yt:
        if not yt_url.strip():
            st.warning("Please paste a YouTube video or Shorts link.")
        elif not st.session_state.pro_unlocked and free_left <= 0:
            st.error("🔒 You have used all 3 Free Reports! Please upgrade to a Pro Plan on the left sidebar for unlimited access.")
        else:
            vid_id = extract_youtube_id(yt_url.strip())
            if not vid_id:
                st.error("❌ Invalid YouTube link. Please enter a valid Video or Shorts URL.")
            else:
                yt_status_slot.markdown('<div class="loading-pill">🔄 Fetching video details & audience comments... ⏳</div>', unsafe_allow_html=True)
                data = fetch_youtube_details(vid_id)
                if not data:
                    yt_status_slot.empty()
                    st.error("❌ Could not fetch video details. Make sure the video is Public.")
                else:
                    st.session_state.yt_stats = data
                    st.session_state.yt_vid_id = vid_id

                    comments_block = "\n".join(data["comments"][:15]) if data["comments"] else "No public comments available."
                    lang_rule = build_language_directive(report_lang)

                    prompt = f"""
You are a warm, encouraging, expert human social media growth advisor ("సలహాదారు" / "सलाहकार").
Write a deeply detailed, simple, easy-to-understand growth audit report (1,100 to 1,500 words) tailored for a **{audience_scope}** audience.
Use natural, everyday spoken words that any creator can easily understand. Never use complex academic words.
{lang_rule}

VIDEO DATA:
- Channel: {data['channel']}
- Title: {data['title']}
- Audio/Metadata Language Hint: {data['default_audio_lang']}
- Views: {data['views']:,} | Likes: {data['likes']:,} | Comments: {data['comment_count']:,}
- Description: {data['description']}
- Tags: {', '.join(data['tags'])}
- Real Audience Comments:
{comments_block}

STRICTLY FOLLOW THIS 6-SECTION STRUCTURE (Translate all 6 headings into the target native script):
### 🎬 1. Video Story Recap & Creator Appreciation
- First, warmly retell the core story/message of this video based on its title, description, and comments so the creator feels you truly watched and understood their hard work.
- Then genuinely praise the creator's effort, topic choice, and strengths with motivating words.

### 💬 2. What Your Audience Is Saying (Real Comments Translated & Reply Templates)
- Pick 4 to 5 real viewer comments from the list above, translate them naturally into the target language native script, quote them with the viewer's name, explain what viewers love or ask for, and give 3 ready-to-copy reply templates to boost engagement.

### 🔥 3. Next 3 Viral Video Ideas + Word-for-Word 5-Second Hooks
- Give 3 high-potential follow-up video ideas tailored to this channel. For each idea, write an exact word-for-word **5-second opening Hook** and a **Thumbnail visual idea**.

### 🎯 4. Copy-Paste SEO Makeover (High-CTR Titles, Description & 15 Tags)
- Provide 3 clickable high-CTR title options, a strong 3-line SEO description hook, and 15 searchable comma-separated tags.

### 💰 5. Monetization & Earning Blueprint
- Explain 3 practical ways this specific channel can earn money (AdSense, Affiliate marketing, Brand sponsorships) with realistic examples.

### 📅 6. 30-Day Step-by-Step Growth Action Plan
- Give a clear Week 1 to Week 4 checklist of simple daily/weekly actions to double views and subscribers.
"""
                    yt_status_slot.markdown('<div class="loading-pill">⚡ Generating Growth Report... ⏳</div>', unsafe_allow_html=True)
                    m1, m2, m3 = st.columns(3)
                    m1.metric("👀 Views", f"{data['views']:,}")
                    m2.metric("👍 Likes", f"{data['likes']:,}")
                    m3.metric("💬 Comments", f"{data['comment_count']:,}")

                    report_box = st.empty()
                    full_text = ""
                    try:
                        for piece in generate_report_stream(prompt):
                            full_text += piece
                            report_box.markdown(full_text)
                        yt_status_slot.empty()
                        st.session_state.yt_report = full_text
                        if not st.session_state.pro_unlocked:
                            increment_free_used(st.session_state.verified_email)
                        log_usage_to_sheet(st.session_state.verified_email or "PRO", "YouTube", yt_url.strip())
                        st.rerun()
                    except Exception as e:
                        yt_status_slot.empty()
                        st.error(str(e))

    # Persist YouTube report across reruns & downloads (never goes blank!)
    if st.session_state.yt_report and not run_yt:
        if st.session_state.yt_stats:
            d = st.session_state.yt_stats
            m1, m2, m3 = st.columns(3)
            m1.metric("👀 Views", f"{d['views']:,}")
            m2.metric("👍 Likes", f"{d['likes']:,}")
            m3.metric("💬 Comments", f"{d['comment_count']:,}")
        st.markdown(st.session_state.yt_report)
        st.success("✅ Growth Audit Report is ready!")
        st.download_button(
            "📥 Download Complete Growth Report (.txt)",
            data=st.session_state.yt_report,
            file_name=f"TrendSutra_YouTube_Report_{st.session_state.yt_vid_id or 'Audit'}.txt",
            mime="text/plain",
            use_container_width=True
        )

with tab_ig:
    ic1, ic2 = st.columns([4.2, 1.5])
    with ic1:
        ig_url = st.text_input("IG Link", placeholder="Paste Instagram Reel Link (https://www.instagram.com/reel/...)", label_visibility="collapsed")
    with ic2:
        run_ig = st.button("Generate Growth Report 🔍", key="btn_ig", type="primary", use_container_width=True)

    ig_status_slot = st.empty()

    if run_ig:
        if not ig_url.strip():
            st.warning("Please paste an Instagram Reel link.")
        elif not st.session_state.pro_unlocked and free_left <= 0:
            st.error("🔒 You have used all 3 Free Reports! Please upgrade to a Pro Plan on the left sidebar.")
        else:
            ig_status_slot.markdown('<div class="loading-pill">⚡ Generating Instagram Growth Report... ⏳</div>', unsafe_allow_html=True)
            lang_rule = build_language_directive(report_lang)
            ig_prompt = f"""
You are a warm, encouraging human Instagram Reels growth advisor.
Write a detailed 6-section Instagram Reels growth audit (1,000+ words) for a **{audience_scope}** audience using simple spoken words.
{lang_rule}
Reel Link: {ig_url.strip()}
Include (translate all 6 headings into the target native script):
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

    if st.session_state.ig_report and not run_ig:
        st.markdown(st.session_state.ig_report)
        st.success("✅ Instagram Growth Report is ready!")
        st.download_button(
            "📥 Download Instagram Report (.txt)",
            data=st.session_state.ig_report,
            file_name="TrendSutra_Instagram_Report.txt",
            mime="text/plain",
            use_container_width=True
        )

with tab_tt:
    tc1, tc2 = st.columns([4.2, 1.5])
    with tc1:
        tt_url = st.text_input("TT Link", placeholder="Paste TikTok Video Link (https://www.tiktok.com/@user/video/...)", label_visibility="collapsed")
    with tc2:
        run_tt = st.button("Generate Growth Report 🔍", key="btn_tt", type="primary", use_container_width=True)

    tt_status_slot = st.empty()

    if run_tt:
        if not tt_url.strip():
            st.warning("Please paste a TikTok video link.")
        elif not st.session_state.pro_unlocked and free_left <= 0:
            st.error("🔒 You have used all 3 Free Reports! Please upgrade to a Pro Plan on the left sidebar.")
        else:
            tt_status_slot.markdown('<div class="loading-pill">⚡ Generating TikTok Growth Report... ⏳</div>', unsafe_allow_html=True)
            lang_rule = build_language_directive(report_lang)
            tt_prompt = f"""
You are a warm, encouraging human TikTok growth advisor.
Write a detailed 6-section TikTok growth audit (1,000+ words) for a **{audience_scope}** audience using simple spoken words.
{lang_rule}
TikTok Link: {tt_url.strip()}
Include (translate all 6 headings into the target native script):
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

    if st.session_state.tt_report and not run_tt:
        st.markdown(st.session_state.tt_report)
        st.success("✅ TikTok Growth Report is ready!")
        st.download_button(
            "📥 Download TikTok Report (.txt)",
            data=st.session_state.tt_report,
            file_name="TrendSutra_TikTok_Report.txt",
            mime="text/plain",
            use_container_width=True
        )
