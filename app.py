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
st.set_page_config(
    page_title="TrendSutra AI - 1 AI • 1 India",
    page_icon="logo.png" if os.path.exists("logo.png") else "📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. LOAD SECRETS (4-KEY SMART FAILOVER) ---
GEMINI_KEYS = [
    str(st.secrets.get("GEMINI_API_KEY_4", "")).strip(),
    str(st.secrets.get("GEMINI_API_KEY_3", "")).strip(),
    str(st.secrets.get("GEMINI_API_KEY_2", "")).strip(),
    str(st.secrets.get("GEMINI_API_KEY", "")).strip(),
]
GEMINI_KEYS = [k for k in GEMINI_KEYS if k]

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

# --- 3. ALL 22 OFFICIAL INDIAN LANGUAGES + BHOJPURI (STRICTLY A-Z) ---
INDIAN_LANGUAGES = [
    "Auto-Detect Video Language",
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
    "Kashmiri (कश्मीरी)",
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
    "Sindhi (سنڌي)",
    "Tamil (தமிழ்)",
    "Telugu (తెలుగు)",
    "Tenglish (Telugu + English)",
    "Urdu (اردو)"
]

# --- 4. CUSTOM DARK UI & CLEAN LAYOUT ---
st.markdown("""
<style>
    /* Hide right-top Share/Star/Edit/GitHub icons while keeping Sidebar Open/Close button */
    [data-testid="stToolbarActions"], .stDeployButton, #MainMenu, footer {
        display: none !important;
    }
    [data-testid="stSidebarCollapsedControl"] {
        display: flex !important;
        visibility: visible !important;
    }
    .block-container {
        padding-top: 1.1rem !important;
        padding-bottom: 1.5rem !important;
        max-width: 1180px !important;
    }
    /* Compact No-Scroll Sidebar */
    section[data-testid="stSidebar"] .block-container {
        padding-top: 0.7rem !important;
        padding-bottom: 0.5rem !important;
    }
    section[data-testid="stSidebar"] h2, section[data-testid="stSidebar"] h3 {
        margin-top: 0.25rem !important;
        margin-bottom: 0.25rem !important;
        font-size: 1.02rem !important;
    }
    section[data-testid="stSidebar"] hr {
        margin: 0.45rem 0 !important;
    }
    /* Center Logo Header */
    .center-header {
        background: linear-gradient(135deg, #0b1324 0%, #162238 100%);
        border: 1px solid #26354f;
        border-radius: 14px;
        padding: 14px 20px;
        text-align: center;
        margin-bottom: 12px;
        box-shadow: 0 4px 16px rgba(0,0,0,0.28);
    }
    .header-title-row {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 10px;
    }
    .header-title-row h1 {
        margin: 0;
        font-size: 1.65rem;
        font-weight: 800;
        color: #ffffff;
        letter-spacing: 0.3px;
    }
    .india-badge {
        background: rgba(16, 185, 129, 0.16);
        border: 1px solid #10b981;
        color: #34d399;
        padding: 2px 10px;
        border-radius: 999px;
        font-size: 0.76rem;
        font-weight: 700;
    }
    .center-header p {
        margin: 4px 0 0 0;
        color: #cbd5e1;
        font-size: 0.88rem;
    }
    .user-strip {
        background: #111827;
        border: 1px solid #1f2937;
        border-radius: 10px;
        padding: 8px 14px;
        color: #e2e8f0;
        font-size: 0.88rem;
        margin-bottom: 10px;
    }
    .loading-pill {
        background: rgba(16, 185, 129, 0.14);
        border: 1px solid #10b981;
        color: #34d399;
        padding: 7px 14px;
        border-radius: 8px;
        font-weight: 600;
        font-size: 0.88rem;
        display: inline-block;
        margin-bottom: 8px;
    }
</style>
""", unsafe_allow_html=True)

# --- 5. SESSION STATE ---
for key, default in [
    ("verified_email", ""),
    ("otp_code", ""),
    ("otp_target", ""),
    ("pro_unlocked", False),
    ("pro_label", ""),
    ("yt_report", ""),
    ("yt_vid_id", ""),
    ("ig_report", ""),
    ("tt_report", "")
]:
    if key not in st.session_state:
        st.session_state[key] = default

# --- 6. GOOGLE OAUTH & RAZORPAY AUTO-REDIRECT ---
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
            params={"device": user_id, "_ts": int(time.time() * 1000)},
            timeout=10,
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
                timeout=10,
                allow_redirects=True
            )
            if r.status_code == 200:
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
                "_ts": int(time.time() * 1000)
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

if not st.session_state.pro_unlocked:
    qp_pid = st.query_params.get("razorpay_payment_id", "")
    if qp_pid and str(qp_pid).startswith("pay_"):
        if verify_payment_id(str(qp_pid), "1m") == "VALID":
            st.session_state.pro_unlocked = True
            st.session_state.pro_label = "PRO UNLIMITED ACTIVE"

def send_otp_email(to_email, code):
    if not SENDER_EMAIL or not SENDER_PASS:
        return False, "SMTP credentials not configured in Secrets."
    try:
        msg = MIMEText(
            f"Welcome to TrendSutra AI!\n\n"
            f"Your 6-digit verification code is: {code}\n\n"
            f"Enter this code on TrendSutra AI to unlock your 3 Free Growth Reports.\n"
            f"Do not share this OTP with anyone."
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
            "description": snip.get("description", "")[:1200],
            "tags": snip.get("tags", [])[:20],
            "views": int(stats.get("viewCount", 0)),
            "likes": int(stats.get("likeCount", 0)),
            "comment_count": int(stats.get("commentCount", 0)),
            "comments": comments
        }
    except Exception:
        return None

# --- 9. 4-KEY SMART FAILOVER GEMINI STREAMING ---
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

def generate_report_stream(prompt):
    if not GEMINI_KEYS:
        raise RuntimeError("Gemini API Keys not configured in Secrets.")
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
                            temperature=0.8,
                            max_output_tokens=8192
                        )
                    )
                    yielded_any = False
                    for chunk in response:
                        if chunk.text:
                            yielded_any = True
                            yield chunk.text
                    if yielded_any:
                        return
                except Exception as e:
                    last_err = str(e)
                    continue
        except Exception as e:
            last_err = str(e)
            continue
    raise RuntimeError(f"AI servers are currently busy. Please try again in 5 seconds. ({last_err})")

# --- 10. CENTER HEADER WITH LOGO ---
logo_html = ""
if os.path.exists("logo.png"):
    try:
        with open("logo.png", "rb") as f:
            b64_logo = base64.b64encode(f.read()).decode()
        logo_html = f'<img src="data:image/png;base64,{b64_logo}" style="width:36px; height:36px; border-radius:8px; object-fit:contain;" />'
    except Exception:
        pass

st.markdown(f"""
<div class="center-header">
    <div class="header-title-row">
        {logo_html}
        <h1>TrendSutra AI</h1>
        <span class="india-badge">🇮🇳 1 AI • 1 India</span>
    </div>
    <p>A to Z Growth Analyzer in All 22 Indian Languages + Bhojpuri for YouTube, Instagram & TikTok</p>
</div>
""", unsafe_allow_html=True)

# --- 11. NO-SCROLL SIDEBAR (100% ENGLISH UI) ---
with st.sidebar:
    st.subheader("⚙️ Settings")
    report_lang = st.selectbox(
        "Type to Search Language (A–Z):",
        INDIAN_LANGUAGES,
        index=0
    )
    audience_scope = st.radio("Target Audience:", ["Regional", "Global", "Both"], horizontal=True, label_visibility="collapsed")

    st.divider()
    st.subheader("💎 Pro Plans")

    free_used = get_free_used_count(st.session_state.verified_email) if st.session_state.verified_email else 0
    free_left = max(0, 3 - free_used)

    if st.session_state.pro_unlocked:
        st.success(f"✅ {st.session_state.pro_label}")
    elif st.session_state.verified_email:
        if free_left > 0:
            st.info(f"🎁 Free Trial: **{free_left}/3 left**")
        else:
            st.error("🔒 Free Trial: **0/3 left**")
    else:
        st.info("🎁 Login to get **3 Free Reports**")

    st.markdown(f"• **1 Month:** ₹100 👉 [Pay ₹100]({RAZORPAY_1M})")
    st.markdown(f"• **12 Months:** ₹1,000 👉 [Pay ₹1,000]({RAZORPAY_12M})")

    plan_choice = st.radio("Plan:", ["1M (₹100)", "12M (₹1,000)"], horizontal=True, label_visibility="collapsed")
    pay_input = st.text_input("Payment ID:", placeholder="Paste Payment ID (pay_...)", label_visibility="collapsed")
    if st.button("Unlock Pro 🔓", use_container_width=True):
        if not pay_input.strip():
            st.warning("Please enter your Payment ID.")
        else:
            p_code = "12m" if "12" in plan_choice else "1m"
            status = verify_payment_id(pay_input, plan=p_code)
            if status == "OWNER":
                st.session_state.pro_unlocked = True
                st.session_state.pro_label = "OWNER UNLIMITED ACTIVE"
                st.rerun()
            elif status == "VALID":
                st.session_state.pro_unlocked = True
                st.session_state.pro_label = f"PRO ACTIVE ({plan_choice})"
                st.rerun()
            elif status == "EXPIRED":
                st.error("⏰ Plan expired! Please renew your subscription.")
            elif status == "ALREADY_USED":
                st.error("❌ This Payment ID has already been used on 3 devices.")
            else:
                st.error("❌ Invalid Payment ID (must start with pay_).")

    st.divider()
    st.caption("📩 support@aiengtel.com | aiengtel.com")

# --- 12. SINGLE-ROW LOGIN BAR OR ACTIVE USER STRIP (100% ENGLISH UI) ---
if not st.session_state.verified_email and not st.session_state.pro_unlocked:
    lc1, lc2, lc3, lc4 = st.columns([1.6, 0.35, 1.8, 1.1])
    with lc1:
        if st.button("🔵 Continue with Gmail", type="primary", use_container_width=True):
            try:
                st.login("google")
            except Exception as e:
                st.error(f"Google Login error: {e}")
    with lc2:
        st.markdown("<div style='text-align:center; padding-top:7px; color:#94a3b8; font-weight:700;'>OR</div>", unsafe_allow_html=True)
    with lc3:
        email_in = st.text_input("Mail ID", placeholder="Login with Mail ID (Enter Email)", label_visibility="collapsed")
    with lc4:
        if st.button("Send OTP 📩", use_container_width=True):
            clean_em = email_in.strip().lower()
            if "@" not in clean_em or "." not in clean_em.split("@")[-1]:
                st.error("❌ Please enter a valid Email ID.")
            elif clean_em.split("@")[-1] in TEMP_DOMAINS:
                st.error("❌ Temporary emails are not allowed.")
            else:
                code = str(random.randint(100000, 999999))
                ok, err_msg = send_otp_email(clean_em, code)
                if ok:
                    st.session_state.otp_code = code
                    st.session_state.otp_target = clean_em
                    st.success(f"✅ 6-digit OTP sent to {clean_em}! Please check Inbox/Spam.")
                else:
                    st.error(f"❌ Failed to send OTP: {err_msg}")

    if st.session_state.otp_target:
        oc1, oc2 = st.columns([2.2, 1.2])
        with oc1:
            otp_in = st.text_input("Enter OTP", placeholder=f"Enter 6-digit OTP sent to {st.session_state.otp_target}", max_chars=6, label_visibility="collapsed")
        with oc2:
            if st.button("Verify OTP ✅", type="primary", use_container_width=True):
                if otp_in.strip() == st.session_state.otp_code:
                    st.session_state.verified_email = st.session_state.otp_target
                    st.session_state.otp_code = ""
                    st.rerun()
                else:
                    st.error("❌ Incorrect OTP! Please check and try again.")
else:
    uc1, uc2 = st.columns([4, 1])
    with uc1:
        badge_txt = f"✅ {st.session_state.pro_label}" if st.session_state.pro_unlocked else f"🎁 {free_left}/3 Free Reports Left"
        who_txt = st.session_state.verified_email if st.session_state.verified_email else "Pro Member"
        st.markdown(f'<div class="user-strip">👤 Logged in as <b>{who_txt}</b> &nbsp;|&nbsp; {badge_txt}</div>', unsafe_allow_html=True)
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

# --- 13. MAIN ANALYZER TABS (100% ENGLISH UI + NATIVE SCRIPT REPORT) ---
is_auto_lang = report_lang.startswith("Auto-Detect")
lang_instruction = (
    "Automatically detect the primary language of the video from its title, description, tags, and comments. "
    "First output a single line at the very top: `🌐 Detected Video Language: <Language Name>` and then write the ENTIRE 6-section report (including all 6 headings) in that detected language's native script (for example, Telugu in తెలుగు, Tamil in தமிழ், Hindi in हिन्दी, Urdu in اردو, Kannada in ಕನ್ನಡ, etc.)."
    if is_auto_lang else
    f"Write the ENTIRE 6-section report (including all 6 section headings) strictly in **{report_lang}** using its native script."
)

tab_yt, tab_ig, tab_tt = st.tabs(["📺 YouTube Analyzer", "📸 Instagram Reels Analyzer", "🎵 TikTok Analyzer"])

with tab_yt:
    yc1, yc2 = st.columns([3.4, 1.3])
    with yc1:
        yt_url = st.text_input("YouTube URL", placeholder="Paste YouTube Video or Shorts Link (https://youtube.com/...)", label_visibility="collapsed")
    with yc2:
        run_yt = st.button("Generate Growth Report 🔍", key="btn_yt", type="primary", use_container_width=True)

    yt_status_slot = st.empty()

    if run_yt:
        if not st.session_state.verified_email and not st.session_state.pro_unlocked:
            st.warning("⚠️ Please login with Gmail or Email OTP above to generate your free report.")
        elif not yt_url.strip():
            st.warning("⚠️ Please paste a YouTube video or Shorts link.")
        elif not st.session_state.pro_unlocked and free_left <= 0:
            st.error("🔒 Your 3 Free Reports are finished! Please upgrade to a Pro Plan on the left sidebar.")
        else:
            vid_id = extract_youtube_id(yt_url.strip())
            if not vid_id:
                st.error("❌ Please enter a valid YouTube Video or Shorts link.")
            else:
                yt_status_slot.markdown('<div class="loading-pill">🔄 Fetching video details & audience comments... ⏳</div>', unsafe_allow_html=True)
                data = fetch_youtube_details(vid_id)
                if not data:
                    yt_status_slot.empty()
                    st.error("❌ Could not fetch video details. Please make sure the video is Public.")
                else:
                    m1, m2, m3 = st.columns(3)
                    m1.metric("👀 Views", f"{data['views']:,}")
                    m2.metric("👍 Likes", f"{data['likes']:,}")
                    m3.metric("💬 Comments", f"{data['comment_count']:,}")

                    comments_block = "\n".join(data["comments"][:15]) if data["comments"] else "No public comments available."
                    prompt = f"""
You are a warm, encouraging, expert human social media growth advisor.
{lang_instruction}
Target audience scope: **{audience_scope}**.
Write a deeply detailed, practical, easy-to-understand growth audit report (1,100 to 1,500 words) using simple everyday spoken words so any creator can easily apply it.

VIDEO DATA:
- Channel: {data['channel']}
- Title: {data['title']}
- Views: {data['views']:,} | Likes: {data['likes']:,} | Comments: {data['comment_count']:,}
- Description: {data['description']}
- Tags: {', '.join(data['tags'])}
- Real Audience Comments:
{comments_block}

STRICTLY FOLLOW THIS 6-SECTION STRUCTURE (translate all 6 headings into the target language's native script):
### 🎬 1. Video Story Recap & Creator Appreciation
- First, warmly retell the core story/message of this video based on its title, description, and comments so the creator feels you truly watched and understood their hard work.
- Then genuinely praise the creator's effort, topic choice, and presentation.

### 💬 2. Audience Comments Translated & Reply Guide
- Pick 4 to 5 real viewer comments from the list above, translate them naturally into the target language, quote them with the viewer's name, explain what viewers love or ask for, and provide 3 ready-to-copy reply templates.

### 🔥 3. 3 Next Viral Video Ideas + 5-Second Hooks
- Give 3 fresh follow-up video ideas tailored to this channel. For each idea, write an exact word-for-word **5-second opening Hook** and a **Thumbnail visual idea**.

### 🎯 4. Copy-Paste SEO Makeover (Titles, Description & 15 Tags)
- Provide 3 clickable high-CTR title options, a strong 3-line SEO description hook, and 15 searchable comma-separated tags.

### 💰 5. Monetization & Earning Blueprint
- Explain 3 practical ways this channel can earn money (AdSense, Affiliate links, Brand sponsorships).

### 📅 6. 30-Day Step-by-Step Action Plan
- Give a clear Week 1 to Week 4 checklist of simple daily/weekly actions to double views and subscribers.
"""
                    yt_status_slot.markdown('<div class="loading-pill">⚡ Generating Growth Report... ⏳</div>', unsafe_allow_html=True)
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
        st.success("✅ Growth Audit Report Ready!")
        st.download_button(
            "📥 Download Complete Growth Report (.txt)",
            data=st.session_state.yt_report,
            file_name=f"TrendSutra_YouTube_Report_{st.session_state.yt_vid_id or 'Report'}.txt",
            mime="text/plain",
            use_container_width=True
        )

with tab_ig:
    ic1, ic2 = st.columns([3.4, 1.3])
    with ic1:
        ig_url = st.text_input("Instagram URL", placeholder="Paste Instagram Reel Link (https://instagram.com/reel/...)", label_visibility="collapsed")
    with ic2:
        run_ig = st.button("Generate Growth Report 🔍", key="btn_ig", type="primary", use_container_width=True)

    ig_status_slot = st.empty()

    if run_ig:
        if not st.session_state.verified_email and not st.session_state.pro_unlocked:
            st.warning("⚠️ Please login with Gmail or Email OTP above to generate your free report.")
        elif not ig_url.strip():
            st.warning("⚠️ Please paste an Instagram Reel link.")
        elif not st.session_state.pro_unlocked and free_left <= 0:
            st.error("🔒 Your 3 Free Reports are finished! Please upgrade to a Pro Plan on the left sidebar.")
        else:
            ig_status_slot.markdown('<div class="loading-pill">⚡ Generating Instagram Growth Report... ⏳</div>', unsafe_allow_html=True)
            ig_prompt = f"""
You are a warm, encouraging human Instagram Reels growth advisor.
{lang_instruction}
Target audience scope: **{audience_scope}**.
Write a detailed 6-section Instagram Reels growth audit (1,000+ words) in simple spoken words.
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
        st.success("✅ Instagram Growth Report Ready!")
        st.download_button(
            "📥 Download Instagram Report (.txt)",
            data=st.session_state.ig_report,
            file_name="TrendSutra_Instagram_Report.txt",
            mime="text/plain",
            use_container_width=True
        )

with tab_tt:
    tc1, tc2 = st.columns([3.4, 1.3])
    with tc1:
        tt_url = st.text_input("TikTok URL", placeholder="Paste TikTok Video Link (https://tiktok.com/@user/video/...)", label_visibility="collapsed")
    with tc2:
        run_tt = st.button("Generate Growth Report 🔍", key="btn_tt", type="primary", use_container_width=True)

    tt_status_slot = st.empty()

    if run_tt:
        if not st.session_state.verified_email and not st.session_state.pro_unlocked:
            st.warning("⚠️ Please login with Gmail or Email OTP above to generate your free report.")
        elif not tt_url.strip():
            st.warning("⚠️ Please paste a TikTok video link.")
        elif not st.session_state.pro_unlocked and free_left <= 0:
            st.error("🔒 Your 3 Free Reports are finished! Please upgrade to a Pro Plan on the left sidebar.")
        else:
            tt_status_slot.markdown('<div class="loading-pill">⚡ Generating TikTok Growth Report... ⏳</div>', unsafe_allow_html=True)
            tt_prompt = f"""
You are a warm, encouraging human TikTok growth advisor.
{lang_instruction}
Target audience scope: **{audience_scope}**.
Write a detailed 6-section TikTok growth audit (1,000+ words) in simple spoken words.
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
        st.success("✅ TikTok Growth Report Ready!")
        st.download_button(
            "📥 Download TikTok Report (.txt)",
            data=st.session_state.tt_report,
            file_name="TrendSutra_TikTok_Report.txt",
            mime="text/plain",
            use_container_width=True
        )
