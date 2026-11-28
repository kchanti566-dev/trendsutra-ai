import streamlit as st
from google import genai
from google.genai import types
from googleapiclient.discovery import build
import re
import requests
import random
import smtplib
from email.mime.text import MIMEText
import time

# --- 1. PAGE CONFIG ---
page_icon = "logo.png" if os.path.exists("logo.png") else "📊"
st.set_page_config(page_title="TrendSutra AI - 1 AI • 1 India", page_icon=page_icon, layout="wide")

# --- 2. SECRETS ---
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

# --- 3. A-Z LANGUAGES (22 OFFICIAL INDIAN LANGUAGES + BHOJPURI + AUTO) ---
LANGUAGES = [
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
    "Kashmiri (कॉशुर / كٲشُر)",
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

# --- 4. CUSTOM DARK UI & COMPACT NO-SCROLL SIDEBAR ---
st.markdown("""
<style>
    /* Hide right-side GitHub/Share/Star icons, keep Sidebar toggle visible */
    [data-testid="stToolbarActions"] { display: none !important; }
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }

    /* Compact padding so everything fits on one screen */
    .block-container {
        padding-top: 1.1rem !important;
        padding-bottom: 1rem !important;
        max-width: 1280px;
    }
    section[data-testid="stSidebar"] .block-container {
        padding-top: 0.8rem !important;
        padding-bottom: 0.5rem !important;
    }
    section[data-testid="stSidebar"] hr {
        margin: 0.45rem 0 !important;
    }

    /* Centered Header Card */
    .ts-header {
        background: linear-gradient(135deg, #0b132b 0%, #1c2541 100%);
        border: 1px solid #334155;
        border-radius: 14px;
        padding: 14px 20px;
        text-align: center;
        margin-bottom: 12px;
    }
    .ts-title-row {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        gap: 12px;
    }
    .ts-title {
        font-size: 1.85rem;
        font-weight: 800;
        color: #ffffff;
        margin: 0;
        letter-spacing: 0.3px;
    }
    .ts-badge {
        background: #064e3b;
        color: #34d399;
        border: 1px solid #10b981;
        padding: 3px 10px;
        border-radius: 999px;
        font-size: 0.78rem;
        font-weight: 700;
    }
    .ts-sub {
        color: #cbd5e1;
        font-size: 0.92rem;
        margin: 4px 0 0 0;
    }

    /* Compact Login Strip */
    .login-strip {
        background: #0f172a;
        border: 1px solid #334155;
        border-radius: 10px;
        padding: 10px 14px;
        margin-bottom: 10px;
    }
    .status-pill {
        background: #064e3b;
        border: 1px solid #10b981;
        color: #ecfdf5;
        padding: 8px 14px;
        border-radius: 8px;
        font-weight: 600;
        display: inline-block;
        margin: 6px 0;
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
    ("yt_metrics", None),
    ("ig_report", ""),
    ("tt_report", ""),
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

try:
    qp = st.query_params
    rzp_id = qp.get("razorpay_payment_id", "")
    if rzp_id and str(rzp_id).startswith("pay_") and not st.session_state.pro_unlocked:
        st.session_state.auto_pay_id = str(rzp_id).strip()
except Exception:
    pass

# --- 7. GOOGLE SHEET LIVE SYNC (NO CACHE) ---
def get_free_used_count(user_id):
    if not SHEET_API or not user_id:
        return 0
    try:
        r = requests.get(
            SHEET_API,
            params={"device": user_id, "_ts": str(time.time())},
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
                params={"device": user_id, "inc": "1", "_ts": str(time.time())},
                timeout=8,
                allow_redirects=True
            )
            if r.status_code == 200:
                break
        except Exception:
            time.sleep(0.5)

def log_usage_to_sheet(user_id, platform, url):
    if not SHEET_API:
        return
    try:
        requests.get(
            SHEET_API,
            params={"log": "1", "device": user_id, "platform": platform, "url": url, "_ts": str(time.time())},
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
            params={"pid": pid, "plan": plan, "_ts": str(time.time())},
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

if "auto_pay_id" in st.session_state and st.session_state.auto_pay_id and not st.session_state.pro_unlocked:
    st_auto = verify_payment_id(st.session_state.auto_pay_id, plan="1m")
    if st_auto == "VALID":
        st.session_state.pro_unlocked = True
        st.session_state.pro_label = "PRO UNLIMITED ACTIVE"
    st.session_state.auto_pay_id = ""

def send_otp_email(to_email, code):
    if not SENDER_EMAIL or not SENDER_PASS:
        return False, "SMTP settings missing in Secrets"
    try:
        msg = MIMEText(
            f"Welcome to TrendSutra AI!\n\nYour 6-digit verification code is: {code}\n\n"
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

# --- 9. 4-KEY SMART FAILOVER STREAMING ---
def get_models_for_client(client):
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
        raise RuntimeError("No GEMINI_API_KEY configured in Secrets.")
    last_err = ""
    for api_key in GEMINI_KEYS:
        try:
            client = genai.Client(api_key=api_key)
            models = get_models_for_client(client)
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
                    yielded = False
                    for chunk in response:
                        if chunk.text:
                            yielded = True
                            yield chunk.text.replace("మెంటర్", "సలహాదారు")
                    if yielded:
                        return
                except Exception as e:
                    last_err = str(e)
                    continue
        except Exception as e:
            last_err = str(e)
            continue
    raise RuntimeError(f"AI server is busy. Please try again in 5 seconds. ({last_err})")

# --- 10. SIDEBAR (COMPACT NO-SCROLL & ENGLISH DEFAULT) ---
with st.sidebar:
    st.markdown("### ⚙️ Settings")
    report_lang = st.selectbox(
        "🔍 Type to Search Language (A–Z):",
        LANGUAGES,
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
            st.info(f"🎁 Free Trial: **{free_left}/3** reports left")
        else:
            st.error("🔒 **0/3** Free Reports Left")
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
            p_code = "12m" if "12M" in plan_choice else "1m"
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
                st.error("⏰ Plan expired! Please renew.")
            elif status == "ALREADY_USED":
                st.error("❌ Payment ID already used on 3 devices.")
            else:
                st.error("❌ Invalid Payment ID.")

    st.divider()
    st.caption("📩 support@aiengtel.com | © aiengtel.com")

# --- 11. CENTERED HEADER WITH LOGO ---
import base64
logo_html = ""
if os.path.exists("logo.png"):
    with open("logo.png", "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    logo_html = f'<img src="data:image/png;base64,{b64}" style="height:36px; width:36px; border-radius:8px; object-fit:contain;" />'

st.markdown(f"""
<div class="ts-header">
    <div class="ts-title-row">
        {logo_html}
        <h1 class="ts-title">TrendSutra AI</h1>
        <span class="ts-badge">🇮🇳 1 AI • 1 India</span>
    </div>
    <p class="ts-sub">A to Z Growth Analyzer in All 22 Indian Languages + Bhojpuri for YouTube, Instagram & TikTok</p>
</div>
""", unsafe_allow_html=True)

# --- 12. SINGLE-LINE COMPACT LOGIN BAR (ENGLISH DEFAULT) ---
if not st.session_state.verified_email and not st.session_state.pro_unlocked:
    st.markdown('<div class="login-strip">', unsafe_allow_html=True)
    lc1, lc2, lc3, lc4 = st.columns([1.4, 0.3, 1.8, 1.0])
    with lc1:
        if st.button("🔵 Continue with Gmail", type="primary", use_container_width=True):
            try:
                st.login("google")
            except Exception as e:
                st.error(f"Google Login error: {e}")
    with lc2:
        st.markdown("<p style='text-align:center; padding-top:6px; color:#94a3b8; font-weight:700;'>OR</p>", unsafe_allow_html=True)
    with lc3:
        email_in = st.text_input("Login with Mail ID", placeholder="Login with Mail ID (creator@email.com)", label_visibility="collapsed")
    with lc4:
        send_otp_clicked = st.button("Send OTP 📩", use_container_width=True)

    if send_otp_clicked:
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
                st.success(f"✅ 6-digit OTP sent to {clean_em}! Check Inbox or Spam.")
            else:
                st.error(f"❌ Failed to send OTP: {err_msg}")

    if st.session_state.otp_target:
        oc1, oc2 = st.columns([2, 1])
        with oc1:
            otp_in = st.text_input("Enter 6-digit OTP", placeholder="Enter 6-digit OTP", max_chars=6, label_visibility="collapsed")
        with oc2:
            if st.button("Verify OTP ✅", type="primary", use_container_width=True):
                if otp_in.strip() == st.session_state.otp_code:
                    st.session_state.verified_email = st.session_state.otp_target
                    st.session_state.otp_code = ""
                    st.rerun()
                else:
                    st.error("❌ Incorrect OTP! Please try again.")
    st.markdown('</div>', unsafe_allow_html=True)
else:
    uc1, uc2 = st.columns([4, 1])
    with uc1:
        who = st.session_state.verified_email if st.session_state.verified_email else "PRO USER"
        badge_txt = f"💎 {st.session_state.pro_label}" if st.session_state.pro_unlocked else f"🎁 {free_left}/3 Free Reports Left"
        st.markdown(f"<p style='margin:4px 0; color:#cbd5e1;'>👤 Logged in as <b>{who}</b> &nbsp;|&nbsp; <b>{badge_txt}</b></p>", unsafe_allow_html=True)
    with uc2:
        if st.button("Logout 🚪", use_container_width=True):
            st.session_state.verified_email = ""
            st.session_state.pro_unlocked = False
            try:
                if hasattr(st, "logout"):
                    st.logout()
            except Exception:
                pass
            st.rerun()

# --- 13. MAIN ANALYZER TABS (ENGLISH DEFAULT UI, REPORT IN SELECTED/DETECTED LANGUAGE) ---
tab_yt, tab_ig, tab_tt = st.tabs(["📺 YouTube Analyzer", "📸 Instagram Reels Analyzer", "🎵 TikTok Analyzer"])

with tab_yt:
    yc1, yc2 = st.columns([3.2, 1.3])
    with yc1:
        yt_url = st.text_input("YouTube URL", placeholder="Paste YouTube Video or Shorts Link (https://youtu.be/...)", label_visibility="collapsed")
    with yc2:
        run_yt = st.button("Generate Growth Report 🔍", key="btn_yt", type="primary", use_container_width=True)

    yt_status = st.empty()

    if run_yt:
        if not st.session_state.verified_email and not st.session_state.pro_unlocked:
            st.warning("🔐 Please login above with Gmail or Email OTP to get 3 Free Reports.")
        elif not yt_url.strip():
            st.warning("⚠️ Please paste a valid YouTube link.")
        elif not st.session_state.pro_unlocked and free_left <= 0:
            st.error("🔒 Your 3 Free Reports are completed! Upgrade on the left sidebar for Unlimited access.")
        else:
            vid_id = extract_youtube_id(yt_url.strip())
            if not vid_id:
                st.error("❌ Invalid YouTube link. Please paste a valid Video or Shorts URL.")
            else:
                yt_status.markdown('<div class="status-pill">🔄 Fetching video details & audience comments... ⏳</div>', unsafe_allow_html=True)
                data = fetch_youtube_details(vid_id)
                if not data:
                    yt_status.empty()
                    st.error("❌ Could not fetch video details. Make sure the video is Public.")
                else:
                    st.session_state.yt_vid_id = vid_id
                    st.session_state.yt_metrics = {
                        "views": data["views"],
                        "likes": data["likes"],
                        "comments": data["comment_count"]
                    }
                    m1, m2, m3 = st.columns(3)
                    m1.metric("👀 Views", f"{data['views']:,}")
                    m2.metric("👍 Likes", f"{data['likes']:,}")
                    m3.metric("💬 Comments", f"{data['comment_count']:,}")

                    comments_block = "\n".join(data["comments"][:15]) if data["comments"] else "No public comments available."
                    lang_instruction = (
                        "First automatically detect the primary language of this video from its title, description, and comments. Write the ENTIRE report (including all 6 headings) in that detected language using its NATIVE SCRIPT (for example: Telugu in తెలుగు script, Tamil in தமிழ் script, Hindi in देवनागरी script, Urdu in اردو script, Kannada in ಕನ್ನಡ script, etc.)."
                        if report_lang.startswith("Auto-Detect")
                        else f"Write the ENTIRE report (including all 6 headings) strictly in **{report_lang}** using its NATIVE SCRIPT."
                    )

                    prompt = f"""
You are a warm, encouraging, expert human social media growth advisor.
{lang_instruction}
Target Audience Scope: **{audience_scope}**.
Write a deeply detailed, practical growth report (1,100 to 1,500 words) using simple everyday spoken words so any creator can easily understand and apply it. (If writing in Telugu, use 'సలహాదారు' and NEVER use 'మెంటర్').

VIDEO DATA:
- Channel: {data['channel']}
- Title: {data['title']}
- Views: {data['views']:,} | Likes: {data['likes']:,} | Comments: {data['comment_count']:,}
- Description: {data['description']}
- Tags: {', '.join(data['tags'])}
- Real Audience Comments:
{comments_block}

STRICTLY FOLLOW THIS STRUCTURE:
Start the very first line with:
**🌐 Detected Video Language:** <Language Name>

Then write these 6 detailed sections (translate the 6 section headings into the target report language in its native script):

### 🎬 1. Video Story Recap & Creator Appreciation
- First, warmly retell the core story/message of this video based on its title, description, and comments so the creator feels you truly understood their hard work.
- Then genuinely praise the creator's effort, topic choice, and strengths.

### 💬 2. What the Audience is Saying (Real Comments Translated)
- Pick 4 to 5 real viewer comments from the list above, translate them naturally into the target report language, quote them with the viewer's name, explain what viewers love or ask for, and provide 3 ready-to-copy reply templates.

### 🔥 3. 3 Next Viral Video Ideas + 5-Second Hooks
- Give 3 fresh follow-up video ideas tailored to this channel, each with an exact word-for-word **5-second opening Hook** and **Thumbnail visual idea**.

### 🎯 4. Copy-Paste SEO Makeover (Titles, Description & 15 Tags)
- Provide 3 high-CTR clickable title options, a 3-line SEO description hook, and 15 searchable tags.

### 💰 5. Monetization & Earning Blueprint
- Explain 3 practical ways this channel can earn money (AdSense, Affiliate links, Brand sponsorships).

### 📅 6. 30-Day Step-by-Step Action Plan
- Give a clear Week 1 to Week 4 checklist of simple actions to grow views and subscribers.
"""
                    yt_status.markdown('<div class="status-pill">⚡ Generating Growth Report... (Refresh page to stop) ⏳</div>', unsafe_allow_html=True)
                    report_box = st.empty()
                    full_text = ""
                    try:
                        for piece in generate_report_stream(prompt):
                            full_text += piece
                            report_box.markdown(full_text)
                        yt_status.empty()
                        st.session_state.yt_report = full_text
                        if not st.session_state.pro_unlocked:
                            increment_free_used(st.session_state.verified_email)
                        log_usage_to_sheet(st.session_state.verified_email or "PRO", "YouTube", yt_url.strip())
                        st.rerun()
                    except Exception as e:
                        yt_status.empty()
                        st.error(str(e))

    # Persistent display after rerun (prevents blank screen on download)
    if st.session_state.yt_report and not run_yt:
        if st.session_state.yt_metrics:
            m1, m2, m3 = st.columns(3)
            m1.metric("👀 Views", f"{st.session_state.yt_metrics['views']:,}")
            m2.metric("👍 Likes", f"{st.session_state.yt_metrics['likes']:,}")
            m3.metric("💬 Comments", f"{st.session_state.yt_metrics['comments']:,}")
        st.markdown(st.session_state.yt_report)
        st.download_button(
            "📥 Download Complete Growth Report (.txt)",
            data=st.session_state.yt_report,
            file_name=f"TrendSutra_YouTube_Report_{st.session_state.yt_vid_id or 'report'}.txt",
            mime="text/plain",
            use_container_width=True
        )

with tab_ig:
    ic1, ic2 = st.columns([3.2, 1.3])
    with ic1:
        ig_url = st.text_input("Instagram URL", placeholder="Paste Instagram Reel Link (https://www.instagram.com/reel/...)", label_visibility="collapsed")
    with ic2:
        run_ig = st.button("Generate Growth Report 🔍", key="btn_ig", type="primary", use_container_width=True)

    ig_status = st.empty()

    if run_ig:
        if not st.session_state.verified_email and not st.session_state.pro_unlocked:
            st.warning("🔐 Please login above with Gmail or Email OTP to get 3 Free Reports.")
        elif not ig_url.strip():
            st.warning("⚠️ Please paste an Instagram Reel link.")
        elif not st.session_state.pro_unlocked and free_left <= 0:
            st.error("🔒 Your 3 Free Reports are completed! Upgrade on the left sidebar for Unlimited access.")
        else:
            ig_status.markdown('<div class="status-pill">⚡ Generating Instagram Growth Report... ⏳</div>', unsafe_allow_html=True)
            target_l = "English or the language indicated by the Reel URL/context" if report_lang.startswith("Auto-Detect") else report_lang
            ig_prompt = f"""
You are a warm, encouraging human Instagram Reels growth advisor.
Write a detailed 6-section Instagram Reels growth audit (1,000+ words) strictly in **{target_l}** using its NATIVE SCRIPT for a **{audience_scope}** audience. (If writing in Telugu, use 'సలహాదారు' and NEVER 'మెంటర్').
Reel Link: {ig_url.strip()}
Include 6 translated headings:
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
                ig_status.empty()
                st.session_state.ig_report = full_text
                if not st.session_state.pro_unlocked:
                    increment_free_used(st.session_state.verified_email)
                log_usage_to_sheet(st.session_state.verified_email or "PRO", "Instagram", ig_url.strip())
                st.rerun()
            except Exception as e:
                ig_status.empty()
                st.error(str(e))

    if st.session_state.ig_report and not run_ig:
        st.markdown(st.session_state.ig_report)
        st.download_button(
            "📥 Download Instagram Growth Report (.txt)",
            data=st.session_state.ig_report,
            file_name="TrendSutra_Instagram_Report.txt",
            mime="text/plain",
            use_container_width=True
        )

with tab_tt:
    tc1, tc2 = st.columns([3.2, 1.3])
    with tc1:
        tt_url = st.text_input("TikTok URL", placeholder="Paste TikTok Video Link (https://www.tiktok.com/@user/video/...)", label_visibility="collapsed")
    with tc2:
        run_tt = st.button("Generate Growth Report 🔍", key="btn_tt", type="primary", use_container_width=True)

    tt_status = st.empty()

    if run_tt:
        if not st.session_state.verified_email and not st.session_state.pro_unlocked:
            st.warning("🔐 Please login above with Gmail or Email OTP to get 3 Free Reports.")
        elif not tt_url.strip():
            st.warning("⚠️ Please paste a TikTok video link.")
        elif not st.session_state.pro_unlocked and free_left <= 0:
            st.error("🔒 Your 3 Free Reports are completed! Upgrade on the left sidebar for Unlimited access.")
        else:
            tt_status.markdown('<div class="status-pill">⚡ Generating TikTok Growth Report... ⏳</div>', unsafe_allow_html=True)
            target_l = "English or the language indicated by the TikTok URL/context" if report_lang.startswith("Auto-Detect") else report_lang
            tt_prompt = f"""
You are a warm, encouraging human TikTok growth advisor.
Write a detailed 6-section TikTok growth audit (1,000+ words) strictly in **{target_l}** using its NATIVE SCRIPT for a **{audience_scope}** audience. (If writing in Telugu, use 'సలహాదారు' and NEVER 'మెంటర్').
TikTok Link: {tt_url.strip()}
Include 6 translated headings:
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
                tt_status.empty()
                st.session_state.tt_report = full_text
                if not st.session_state.pro_unlocked:
                    increment_free_used(st.session_state.verified_email)
                log_usage_to_sheet(st.session_state.verified_email or "PRO", "TikTok", tt_url.strip())
                st.rerun()
            except Exception as e:
                tt_status.empty()
                st.error(str(e))

    if st.session_state.tt_report and not run_tt:
        st.markdown(st.session_state.tt_report)
        st.download_button(
            "📥 Download TikTok Growth Report (.txt)",
            data=st.session_state.tt_report,
            file_name="TrendSutra_TikTok_Report.txt",
            mime="text/plain",
            use_container_width=True
        )
