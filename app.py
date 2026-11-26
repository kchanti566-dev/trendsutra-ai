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
st.set_page_config(
    page_title="TrendSutra AI - Growth Analyzer",
    page_icon="logo.png" if os.path.exists("logo.png") else "📊",
    layout="wide"
)

# --- 2. LOAD SECRETS ---
GEMINI_KEY = str(st.secrets.get("GEMINI_API_KEY", "")).strip()
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

# --- 3. ULTRA-COMPACT SINGLE-SCREEN DARK UI STYLING ---
st.markdown("""
<style>
    [data-testid="stToolbar"], [data-testid="stDecoration"], [data-testid="stStatusWidget"], #MainMenu, header, footer {
        visibility: hidden !important;
        height: 0px !important;
        display: none !important;
    }
    .block-container {
        padding-top: 0.55rem !important;
        padding-bottom: 0.4rem !important;
        padding-left: 1.4rem !important;
        padding-right: 1.4rem !important;
    }
    section[data-testid="stSidebar"] > div {
        padding-top: 0.4rem !important;
        padding-bottom: 0.3rem !important;
    }
    section[data-testid="stSidebar"] .stMarkdown p {
        margin-bottom: 0.2rem !important;
        font-size: 0.85rem !important;
    }
    section[data-testid="stSidebar"] hr {
        margin: 0.35rem 0 !important;
    }
    section[data-testid="stSidebar"] [data-testid="stAlert"] {
        padding: 0.35rem 0.65rem !important;
    }
    .main-header {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        padding: 10px 18px;
        border-radius: 12px;
        border-left: 5px solid #10b981;
        margin-bottom: 8px;
        color: #ffffff;
        display: flex;
        align-items: center;
        gap: 14px;
    }
    .main-header img {
        width: 54px;
        height: 54px;
        object-fit: contain;
        border-radius: 10px;
        background: #0b1120;
        padding: 3px;
        border: 1px solid #334155;
    }
    .main-header h1 {
        margin: 0;
        font-size: 1.55rem;
        color: #ffffff;
        line-height: 1.15;
    }
    .main-header p {
        margin: 2px 0 0 0;
        color: #cbd5e1;
        font-size: 0.88rem;
    }
    .login-strip {
        background: #111827;
        border: 1px solid #374151;
        border-left: 4px solid #f59e0b;
        border-radius: 8px;
        padding: 6px 12px;
        margin-bottom: 6px;
        color: #f3f4f6;
        font-size: 0.88rem;
    }
    .loading-pill {
        background: #064e3b;
        border: 1px solid #10b981;
        color: #ecfdf5;
        padding: 7px 12px;
        border-radius: 8px;
        font-weight: 600;
        font-size: 0.86rem;
        display: inline-flex;
        align-items: center;
        gap: 6px;
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
if "last_report" not in st.session_state:
    st.session_state.last_report = ""

# --- 5. GOOGLE SHEET & PAYMENT HELPERS ---
def get_free_used_count(user_id):
    if not SHEET_API or not user_id:
        return 0
    try:
        r = requests.get(SHEET_API, params={"device": user_id}, timeout=8)
        if r.status_code == 200 and r.text.strip().isdigit():
            return min(3, int(r.text.strip()))
    except Exception:
        pass
    return 0

def increment_free_used(user_id):
    if not SHEET_API or not user_id:
        return
    try:
        requests.get(SHEET_API, params={"device": user_id, "inc": "1"}, timeout=8)
    except Exception:
        pass

def log_usage_to_sheet(user_id, platform, url):
    if not SHEET_API:
        return
    try:
        requests.get(SHEET_API, params={
            "log": "1",
            "device": user_id,
            "platform": platform,
            "url": url
        }, timeout=6)
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
        r = requests.get(SHEET_API, params={"pid": pid, "plan": plan}, timeout=10)
        if r.status_code == 200:
            res = r.text.strip().upper()
            if res in ["VALID", "ALREADY_USED", "EXPIRED", "INVALID"]:
                return res
    except Exception:
        pass
    return "ERROR"

def send_otp_email(to_email, code):
    if not SENDER_EMAIL or not SENDER_PASS:
        return False, "SMTP not configured"
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

# --- 6. CHECK GOOGLE OAUTH & RAZORPAY AUTO-REDIRECT ---
try:
    if hasattr(st, "user") and getattr(st.user, "is_logged_in", False):
        g_email = getattr(st.user, "email", "")
        if g_email:
            st.session_state.verified_email = g_email.strip().lower()
except Exception:
    pass

try:
    qp = st.query_params
    auto_pid = qp.get("razorpay_payment_id") or qp.get("pid")
    if auto_pid and not st.session_state.pro_unlocked:
        status = verify_payment_id(str(auto_pid), plan="1m")
        if status in ["VALID", "OWNER"]:
            st.session_state.pro_unlocked = True
            st.session_state.pro_label = "PRO UNLIMITED ACTIVE"
except Exception:
    pass

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

# --- 9. CLEAN HEADER WITH EMBEDDED LOGO (NO ROCKET, NO SIDEBAR LOGO) ---
logo_html = ""
if os.path.exists("logo.png"):
    try:
        with open("logo.png", "rb") as img_f:
            b64_logo = base64.b64encode(img_f.read()).decode("utf-8")
        logo_html = f'<img src="data:image/png;base64,{b64_logo}" alt="TrendSutra AI Logo">'
    except Exception:
        logo_html = ""

st.markdown(f"""
<div class="main-header">
    {logo_html}
    <div>
        <h1>TrendSutra AI</h1>
        <p>A to Z Growth Analyzer for YouTube, Instagram & TikTok Creators</p>
    </div>
</div>
""", unsafe_allow_html=True)

# --- 10. ULTRA-COMPACT SIDEBAR (NO LOGO, FITS WITHOUT SCROLL) ---
with st.sidebar:
    st.markdown("**⚙️ Settings**")
    report_lang = st.selectbox(
        "Report Language:",
        ["Telugu (తెలుగు)", "English", "Tenglish (Telugu + English)"],
        label_visibility="collapsed"
    )
    audience_scope = st.radio("Target Audience:", ["Regional", "Global", "Both"], horizontal=True)

    free_used = get_free_used_count(st.session_state.verified_email) if st.session_state.verified_email else 0
    free_left = max(0, 3 - free_used)

    if st.session_state.verified_email:
        st.success(f"👤 {st.session_state.verified_email}")
        if st.button("Logout 🚪", use_container_width=True):
            st.session_state.verified_email = ""
            st.session_state.pro_unlocked = False
            try:
                if hasattr(st, "logout"):
                    st.logout()
            except Exception:
                pass
            st.rerun()

    st.divider()
    st.markdown("**💎 Pro Plans (Unlimited)**")

    if st.session_state.pro_unlocked:
        st.success(f"✅ {st.session_state.pro_label}")
    elif st.session_state.verified_email:
        if free_left > 0:
            st.info(f"🎁 Free Trial: **{free_left} ఉచిత రిపోర్ట్‌లు** మిగిలి ఉన్నాయి.")
        else:
            st.error("🔒 మీ 3 ఉచిత రిపోర్ట్‌లు పూర్తయ్యాయి!")
    else:
        st.info("🎁 లాగిన్ అయి **3 ఉచిత రిపోర్ట్‌లు** పొందండి!")

    st.markdown(f"• **1 Month:** ₹100/- 👉 [Pay ₹100]({RAZORPAY_1M})  \n• **12 Months:** ₹1,000/- 👉 [Pay ₹1,000]({RAZORPAY_12M})")

    plan_choice = st.radio("Plan:", ["1 Month (₹100)", "12 Months (₹1,000)"], horizontal=True, label_visibility="collapsed")
    pay_input = st.text_input("Payment ID:", placeholder="Paste pay_... ID here", label_visibility="collapsed")
    if st.button("Unlock with Payment ID 🔓", use_container_width=True):
        if not pay_input.strip():
            st.warning("దయచేసి మీ Payment ID ఎంటర్ చేయండి.")
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
                st.error("⏰ ఈ ప్లాన్ గడువు ముగిసింది! దయచేసి మళ్ళీ రీఛార్జ్ చేసుకోండి.")
            elif status == "ALREADY_USED":
                st.error("❌ ఈ Payment ID ఇప్పటికే 3 డివైజ్‌లలో వాడబడింది.")
            else:
                st.error("❌ చెల్లని Payment ID (`pay_...` తో మొదలవ్వాలి).")

    st.caption("📩 support@aiengtel.com | © 2026 TrendSutra AI")

# --- 11. SINGLE-ROW ALIGNED LOGIN BAR ---
if not st.session_state.verified_email and not st.session_state.pro_unlocked:
    st.markdown("""
    <div class="login-strip">
        <b>🔐 3 ఉచిత రిపోర్ట్‌లు పొందడానికి లాగిన్ అవ్వండి:</b> Continue with Gmail లేదా Login with Mail ID ద్వారా ప్రారంభించండి.
    </div>
    """, unsafe_allow_html=True)

    col_g, col_or, col_em, col_btn = st.columns([2.5, 0.5, 3.6, 1.9], vertical_alignment="center")
    with col_g:
        if st.button("🔵 Continue with Gmail", type="primary", use_container_width=True):
            try:
                st.login("google")
            except Exception as e:
                st.error(f"Google Login సిద్ధంగా లేదు: {e}")
    with col_or:
        st.markdown("<div style='text-align:center; color:#9ca3af; font-weight:600;'>OR</div>", unsafe_allow_html=True)
    with col_em:
        email_in = st.text_input("Login with Mail ID", placeholder="Login with Mail ID", label_visibility="collapsed")
    with col_btn:
        send_otp_clicked = st.button("Send OTP 📩", use_container_width=True)

    if send_otp_clicked:
        clean_em = email_in.strip().lower()
        if "@" not in clean_em or "." not in clean_em.split("@")[-1]:
            st.error("❌ సరైన Mail ID ఎంటర్ చేయండి.")
        elif clean_em.split("@")[-1] in TEMP_DOMAINS:
            st.error("❌ తాత్కాలిక (Temp) మెయిల్ అనుమతించబడదు.")
        else:
            code = str(random.randint(100000, 999999))
            ok, err_msg = send_otp_email(clean_em, code)
            if ok:
                st.session_state.otp_code = code
                st.session_state.otp_target = clean_em
                st.success(f"✅ {clean_em} కి 6-అంకెల OTP పంపబడింది! ఇన్‌బాక్స్ / Spam చెక్ చేయండి.")
            else:
                st.error(f"OTP పంపడంలో సమస్య: {err_msg}")

    if st.session_state.otp_target:
        oc1, oc2 = st.columns([3.5, 2.0], vertical_alignment="center")
        with oc1:
            otp_in = st.text_input("OTP:", placeholder="మీ మెయిల్‌కు వచ్చిన 6-అంకెల OTP ఎంటర్ చేయండి", max_chars=6, label_visibility="collapsed")
        with oc2:
            if st.button("Verify OTP & Login ✅", type="primary", use_container_width=True):
                if otp_in.strip() == st.session_state.otp_code:
                    st.session_state.verified_email = st.session_state.otp_target
                    st.session_state.otp_code = ""
                    st.rerun()
                else:
                    st.error("❌ తప్పు OTP! దయచేసి మళ్ళీ చెక్ చేయండి.")

# --- 12. MAIN WORKSPACE (SAME ROW ALIGNED BUTTONS) ---
tab_yt, tab_ig, tab_tt = st.tabs(["📺 YouTube Analyzer", "📸 Instagram Reels Analyzer", "🎵 TikTok Analyzer"])

def check_can_run():
    if not st.session_state.verified_email and not st.session_state.pro_unlocked:
        st.warning("🔒 దయచేసి పైన **Continue with Gmail** లేదా **Login with Mail ID** ద్వారా లాగిన్ అవ్వండి (3 ఉచిత రిపోర్ట్‌లు లభిస్తాయి).")
        return False
    if not st.session_state.pro_unlocked and free_left <= 0:
        st.error("🔒 మీ 3 ఉచిత రిపోర్ట్‌లు పూర్తయ్యాయి! అన్‌లిమిటెడ్ రిపోర్ట్‌ల కోసం ఎడమ వైపు Pro Plan తీసుకోండి.")
        return False
    return True

with tab_yt:
    yt_c1, yt_c2, yt_c3 = st.columns([5.2, 2.6, 2.2], vertical_alignment="center")
    with yt_c1:
        yt_url = st.text_input("YouTube URL", placeholder="Paste YouTube Video or Shorts Link (https://www.youtube.com/watch?v=...)", label_visibility="collapsed")
    with yt_c2:
        run_yt = st.button("Generate Growth Report 🔍", key="btn_yt", type="primary", use_container_width=True)
    with yt_c3:
        yt_status_slot = st.empty()

    if run_yt:
        if check_can_run():
            if not yt_url.strip():
                st.warning("దయచేసి YouTube లింక్ పేస్ట్ చేయండి.")
            else:
                vid_id = extract_youtube_id(yt_url.strip())
                if not vid_id:
                    st.error("❌ సరైన YouTube వీడియో లేదా Shorts లింక్ ఇవ్వండి.")
                else:
                    yt_status_slot.markdown('<div class="loading-pill">🔄 లోడ్ అవుతోంది... ⏳</div>', unsafe_allow_html=True)
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
                        yt_status_slot.markdown('<div class="loading-pill">⚡ రిపోర్ట్ తయారవుతోంది... ⏳</div>', unsafe_allow_html=True)
                        report_box = st.empty()
                        full_text = ""
                        try:
                            for piece in generate_report_stream(prompt):
                                full_text += piece
                                report_box.markdown(full_text)
                            yt_status_slot.empty()
                            st.session_state.last_report = full_text
                            if not st.session_state.pro_unlocked:
                                increment_free_used(st.session_state.verified_email)
                            log_usage_to_sheet(st.session_state.verified_email or "PRO", "YouTube", yt_url.strip())
                            st.success("✅ Growth Audit Report సిద్ధమైంది!")
                            st.download_button(
                                "📥 Download Complete Growth Report (.txt)",
                                data=full_text,
                                file_name=f"TrendSutra_YouTube_Report_{vid_id}.txt",
                                mime="text/plain",
                                use_container_width=True
                            )
                        except Exception as e:
                            yt_status_slot.empty()
                            st.error(str(e))

with tab_ig:
    ig_c1, ig_c2, ig_c3 = st.columns([5.2, 2.6, 2.2], vertical_alignment="center")
    with ig_c1:
        ig_url = st.text_input("Instagram URL", placeholder="Paste Instagram Reel Link (https://www.instagram.com/reel/...)", label_visibility="collapsed")
    with ig_c2:
        run_ig = st.button("Generate Instagram Report 🔍", key="btn_ig", type="primary", use_container_width=True)
    with ig_c3:
        ig_status_slot = st.empty()

    if run_ig:
        if check_can_run():
            if not ig_url.strip():
                st.warning("దయచేసి Instagram Reel లింక్ పేస్ట్ చేయండి.")
            else:
                ig_status_slot.markdown('<div class="loading-pill">⚡ లోడ్ అవుతోంది... ⏳</div>', unsafe_allow_html=True)
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
                    if not st.session_state.pro_unlocked:
                        increment_free_used(st.session_state.verified_email)
                    log_usage_to_sheet(st.session_state.verified_email or "PRO", "Instagram", ig_url.strip())
                    st.success("✅ Instagram Growth Report సిద్ధమైంది!")
                    st.download_button(
                        "📥 Download Instagram Report (.txt)",
                        data=full_text,
                        file_name="TrendSutra_Instagram_Report.txt",
                        mime="text/plain",
                        use_container_width=True
                    )
                except Exception as e:
                    ig_status_slot.empty()
                    st.error(str(e))

with tab_tt:
    tt_c1, tt_c2, tt_c3 = st.columns([5.2, 2.6, 2.2], vertical_alignment="center")
    with tt_c1:
        tt_url = st.text_input("TikTok URL", placeholder="Paste TikTok Video Link (https://www.tiktok.com/@user/video/...)", label_visibility="collapsed")
    with tt_c2:
        run_tt = st.button("Generate TikTok Report 🔍", key="btn_tt", type="primary", use_container_width=True)
    with tt_c3:
        tt_status_slot = st.empty()

    if run_tt:
        if check_can_run():
            if not tt_url.strip():
                st.warning("దయచేసి TikTok లింక్ పేస్ట్ చేయండి.")
            else:
                tt_status_slot.markdown('<div class="loading-pill">⚡ లోడ్ అవుతోంది... ⏳</div>', unsafe_allow_html=True)
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
                    if not st.session_state.pro_unlocked:
                        increment_free_used(st.session_state.verified_email)
                    log_usage_to_sheet(st.session_state.verified_email or "PRO", "TikTok", tt_url.strip())
                    st.success("✅ TikTok Growth Report సిద్ధమైంది!")
                    st.download_button(
                        "📥 Download TikTok Report (.txt)",
                        data=full_text,
                        file_name="TrendSutra_TikTok_Report.txt",
                        mime="text/plain",
                        use_container_width=True
                    )
                except Exception as e:
                    tt_status_slot.empty()
                    st.error(str(e))
