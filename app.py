import os
import re
import time
import random
import base64
import smtplib
from email.mime.text import MIMEText
from datetime import datetime
import requests
import streamlit as st
from google import genai
from google.genai import types
from googleapiclient.discovery import build

# --- 1. PAGE CONFIG ---
st.set_page_config(
    page_title="TrendSutra AI - Growth Analyzer",
    page_icon="logo.png" if os.path.exists("logo.png") else None,
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. LOAD SECRETS ---
GEMINI_KEYS = []
for k_name in ["GEMINI_API_KEY_4", "GEMINI_API_KEY_3", "GEMINI_API_KEY_2", "GEMINI_API_KEY"]:
    val = str(st.secrets.get(k_name, "")).strip()
    if val and val not in GEMINI_KEYS:
        GEMINI_KEYS.append(val)

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

# --- 3. 22 OFFICIAL INDIAN LANGUAGES + BHOJPURI (A-Z) ---
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
    "Kashmiri (कॉशुर)",
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

UI_TEXT = {
    "English": {
        "free_left": "Free Reports Left",
        "free_over": "Your 3 Free Reports are used!",
        "gen_btn": "Generate Growth Report 🔍",
        "fetching": "Fetching video details & audience comments...",
        "generating": "Generating Growth Report...",
        "ready": "Growth Audit Report Ready!",
        "dl_btn": "📥 Download Complete Growth Report (.txt)",
        "otp_sent": "6-digit OTP sent to {email}! Check Inbox/Spam.",
        "send_otp": "Send OTP 📩",
        "verify_otp": "Verify OTP ✅"
    },
    "Telugu": {
        "free_left": "ఉచిత రిపోర్ట్‌లు మిగిలాయి",
        "free_over": "మీ 3 ఉచిత రిపోర్ట్‌లు పూర్తయ్యాయి!",
        "gen_btn": "గ్రోత్ రిపోర్ట్ తయారు చేయండి 🔍",
        "fetching": "వీడియో వివరాలు & కామెంట్లు సేకరిస్తోంది...",
        "generating": "రిపోర్ట్ తయారవుతోంది...",
        "ready": "గ్రోత్ ఆడిట్ రిపోర్ట్ సిద్ధమైంది!",
        "dl_btn": "📥 పూర్తి రిపోర్ట్ డౌన్‌లోడ్ చేయండి (.txt)",
        "otp_sent": "{email} కి 6-అంకెల OTP పంపబడింది! Inbox/Spam చూడండి.",
        "send_otp": "OTP పంపండి 📩",
        "verify_otp": "OTP నిర్ధారించండి ✅"
    },
    "Hindi": {
        "free_left": "मुफ्त रिपोर्ट बाकी हैं",
        "free_over": "आपकी 3 मुफ्त रिपोर्ट पूरी हो गई हैं!",
        "gen_btn": "ग्रोथ रिपोर्ट बनाएं 🔍",
        "fetching": "वीडियो विवरण और कमेंट लिए जा रहे हैं...",
        "generating": "ग्रोथ रिपोर्ट तैयार हो रही है...",
        "ready": "ग्रोथ ऑडिट रिपोर्ट तैयार है!",
        "dl_btn": "📥 पूरी रिपोर्ट डाउनलोड करें (.txt)",
        "otp_sent": "{email} पर 6-अंकों का OTP भेजा गया है!",
        "send_otp": "OTP भेजें 📩",
        "verify_otp": "OTP सत्यापित करें ✅"
    },
    "Tamil": {
        "free_left": "இலவச அறிக்கைகள் உள்ளன",
        "free_over": "உங்கள் 3 இலவச அறிக்கைகள் முடிந்துவிட்டன!",
        "gen_btn": "வளர்ச்சி அறிக்கையை உருவாக்கவும் 🔍",
        "fetching": "வீடியோ விவரங்கள் சேகரிக்கப்படுகின்றன...",
        "generating": "அறிக்கை உருவாக்கப்படுகிறது...",
        "ready": "வளர்ச்சி அறிக்கை தயாராக உள்ளது!",
        "dl_btn": "📥 முழு அறிக்கையைப் பதிவிறக்கவும் (.txt)",
        "otp_sent": "{email} க்கு 6-இலக்க OTP அனுப்பப்பட்டது!",
        "send_otp": "OTP அனுப்பு 📩",
        "verify_otp": "OTP சரிபார் ✅"
    },
    "Kannada": {
        "free_left": "ಉಚಿತ ವರದಿಗಳು ಉಳಿದಿವೆ",
        "free_over": "ನಿಮ್ಮ 3 ಉಚಿತ ವರದಿಗಳು ಮುಗಿದಿವೆ!",
        "gen_btn": "ಗ್ರೋತ್ ವರದಿ ರಚಿಸಿ 🔍",
        "fetching": "ವೀಡಿಯೊ ವಿವರಗಳನ್ನು ಪಡೆಯಲಾಗುತ್ತಿದೆ...",
        "generating": "ವರದಿ ಸಿದ್ಧವಾಗುತ್ತಿದೆ...",
        "ready": "ಗ್ರೋತ್ ವರದಿ ಸಿದ್ಧವಾಗಿದೆ!",
        "dl_btn": "📥 ಪೂರ್ಣ ವರದಿ ಡೌನ್‌ಲೋಡ್ ಮಾಡಿ (.txt)",
        "otp_sent": "{email} ಗೆ 6-ಅಂಕಿಯ OTP ಕಳುಹಿಸಲಾಗಿದೆ!",
        "send_otp": "OTP ಕಳುಹಿಸಿ 📩",
        "verify_otp": "OTP ಪರಿಶೀಲಿಸಿ ✅"
    },
    "Malayalam": {
        "free_left": "സൗജന്യ റിപ്പോർട്ടുകൾ ബാക്കിയുണ്ട്",
        "free_over": "നിങ്ങളുടെ 3 സൗജന്യ റിപ്പോർട്ടുകൾ കഴിഞ്ഞു!",
        "gen_btn": "ഗ്രോത്ത് റിപ്പോർട്ട് തയ്യാറാക്കുക 🔍",
        "fetching": "വീഡിയോ വിവരങ്ങൾ ശേഖരിക്കുന്നു...",
        "generating": "റിപ്പോർട്ട് തയ്യാറാകുന്നു...",
        "ready": "ഗ്രോത്ത് റിപ്പോർട്ട് തയ്യാറായി!",
        "dl_btn": "📥 പൂർണ്ണ റിപ്പോർട്ട് ഡൗൺലോഡ് ചെയ്യുക (.txt)",
        "otp_sent": "{email} ലേക്ക് 6-അക്ക OTP അയച്ചു!",
        "send_otp": "OTP അയയ്ക്കുക 📩",
        "verify_otp": "OTP സ്ഥിരീകരിക്കുക ✅"
    },
    "Marathi": {
        "free_left": "मोफत रिपोर्ट शिल्लक आहेत",
        "free_over": "तुमचे 3 मोफत रिपोर्ट संपले आहेत!",
        "gen_btn": "ग्रोथ रिपोर्ट तयार करा 🔍",
        "fetching": "व्हिडिओ माहिती गोळा करत आहे...",
        "generating": "रिपोर्ट तयार होत आहे...",
        "ready": "ग्रोथ ऑडिट रिपोर्ट तयार आहे!",
        "dl_btn": "📥 संपूर्ण रिपोर्ट डाउनलोड करा (.txt)",
        "otp_sent": "{email} वर 6-अंकी OTP पाठवला आहे!",
        "send_otp": "OTP पाठवा 📩",
        "verify_otp": "OTP सत्यापित करा ✅"
    },
    "Bengali": {
        "free_left": "ফ্রি রিপোর্ট বাকি আছে",
        "free_over": "আপনার ৩টি ফ্রি রিপোর্ট শেষ হয়ে গেছে!",
        "gen_btn": "গ্রোথ রিপোর্ট তৈরি করুন 🔍",
        "fetching": "ভিডিওর তথ্য সংগ্রহ করা হচ্ছে...",
        "generating": "রিপোর্ট তৈরি হচ্ছে...",
        "ready": "গ্রোথ অডিট রিপোর্ট প্রস্তুত!",
        "dl_btn": "📥 সম্পূর্ণ রিপোর্ট ডাউনলোড করুন (.txt)",
        "otp_sent": "{email}-এ ৬-সংখ্যার OTP পাঠানো হয়েছে!",
        "send_otp": "OTP পাঠান 📩",
        "verify_otp": "OTP যাচাই করুন ✅"
    },
    "Gujarati": {
        "free_left": "મફત રિપોર્ટ બાકી છે",
        "free_over": "તમારા 3 મફત રિપોર્ટ પૂરા થઈ ગયા છે!",
        "gen_btn": "ગ્રોથ રિપોર્ટ બનાવો 🔍",
        "fetching": "વિડિયોની વિગતો લેવામાં આવી રહી છે...",
        "generating": "રિપોર્ટ તૈયાર થઈ રહ્યો છે...",
        "ready": "ગ્રોથ ઓડિટ રિપોર્ટ તૈયાર છે!",
        "dl_btn": "📥 સંપૂર્ણ રિપોર્ટ ડાઉનલોડ કરો (.txt)",
        "otp_sent": "{email} પર 6-અંકનો OTP મોકલવામાં આવ્યો છે!",
        "send_otp": "OTP મોકલો 📩",
        "verify_otp": "OTP ચકાસો ✅"
    },
    "Punjabi": {
        "free_left": "ਮੁਫ਼ਤ ਰਿਪੋਰਟਾਂ ਬਾਕੀ ਹਨ",
        "free_over": "ਤੁਹਾਡੀਆਂ 3 ਮੁਫ਼ਤ ਰਿਪੋਰਟਾਂ ਪੂਰੀਆਂ ਹੋ ਗਈਆਂ ਹਨ!",
        "gen_btn": "ਗ੍ਰੋਥ ਰਿਪੋਰਟ ਬਣਾਓ 🔍",
        "fetching": "ਵੀਡੀਓ ਵੇਰਵੇ ਲਏ ਜਾ ਰਹੇ ਹਨ...",
        "generating": "ਰਿਪੋਰਟ ਤਿਆਰ ਹੋ ਰਹੀ ਹੈ...",
        "ready": "ਗ੍ਰੋਥ ਆਡਿਟ ਰਿਪੋਰਟ ਤਿਆਰ ਹੈ!",
        "dl_btn": "📥 ਪੂਰੀ ਰਿਪੋਰਟ ਡਾਊਨਲੋਡ ਕਰੋ (.txt)",
        "otp_sent": "{email} 'ਤੇ 6-ਅੰਕਾਂ ਦਾ OTP ਭੇਜਿਆ ਗਿਆ ਹੈ!",
        "send_otp": "OTP ਭੇਜੋ 📩",
        "verify_otp": "OTP ਪੁਸ਼ਟੀ ਕਰੋ ✅"
    },
    "Odia": {
        "free_left": "ମାଗଣା ରିପୋର୍ଟ ବାକି ଅଛି",
        "free_over": "ଆପଣଙ୍କର 3ଟି ମାଗଣା ରିପୋର୍ଟ ଶେଷ ହୋଇଛି!",
        "gen_btn": "ଗ୍ରୋଥ୍ ରିପୋର୍ଟ ତିଆରି କରନ୍ତୁ 🔍",
        "fetching": "ଭିଡିଓ ତଥ୍ୟ ସଂଗ୍ରହ କରାଯାଉଛି...",
        "generating": "ରିପୋର୍ଟ ପ୍ରସ୍ତୁତ ହେଉଛି...",
        "ready": "ଗ୍ରୋଥ୍ ଅଡିଟ୍ ରିପୋର୍ଟ ପ୍ରସ୍ତୁତ!",
        "dl_btn": "📥 ସମ୍ପୂର୍ଣ୍ଣ ରିପୋର୍ଟ ଡାଉନଲୋଡ୍ କରନ୍ତୁ (.txt)",
        "otp_sent": "{email} କୁ 6-ଅଙ୍କ ବିଶିଷ୍ଟ OTP ପଠାଯାଇଛି!",
        "send_otp": "OTP ପଠାନ୍ତୁ 📩",
        "verify_otp": "OTP ଯାଞ୍ଚ କରନ୍ତୁ ✅"
    },
    "Assamese": {
        "free_left": "বিনামূলীয়া ৰিপৰ্ট বাকী আছে",
        "free_over": "আপোনাৰ ৩টা বিনামূলীয়া ৰিপৰ্ট শেষ হৈছে!",
        "gen_btn": "গ্ৰোথ ৰিপৰ্ট তৈয়াৰ কৰক 🔍",
        "fetching": "ভিডিঅ'ৰ তথ্য সংগ্ৰহ কৰা হৈছে...",
        "generating": "ৰিপৰ্ট প্ৰস্তুত হৈ আছে...",
        "ready": "গ্ৰোথ অডিট ৰিপৰ্ট সাজু হৈছে!",
        "dl_btn": "📥 সম্পূৰ্ণ ৰিপৰ্ট ডাউনলোড কৰক (.txt)",
        "otp_sent": "{email} লৈ ৬-সংখ্যাৰ OTP পঠিওৱা হৈছে!",
        "send_otp": "OTP পঠিয়াওক 📩",
        "verify_otp": "OTP নিশ্চিত কৰক ✅"
    },
    "Urdu": {
        "free_left": "مفت رپورٹس باقی ہیں",
        "free_over": "آپ کی 3 مفت رپورٹس مکمل ہو گئی ہیں!",
        "gen_btn": "گروتھ رپورٹ بنائیں 🔍",
        "fetching": "ویڈیو کی تفصیلات حاصل کی جا رہی ہیں...",
        "generating": "رپورٹ تیار ہو رہی ہے...",
        "ready": "گروتھ آڈٹ رپورٹ تیار ہے!",
        "dl_btn": "📥 مکمل رپورٹ ڈاؤن لوڈ کریں (.txt)",
        "otp_sent": "{email} پر 6 ہندسوں کا OTP بھیج دیا گیا ہے!",
        "send_otp": "OTP بھیجیں 📩",
        "verify_otp": "OTP کی تصدیق کریں ✅"
    },
    "Bhojpuri": {
        "free_left": "फ्री रिपोर्ट बाचल बा",
        "free_over": "राउर 3 गो फ्री रिपोर्ट पूरा हो गइल बा!",
        "gen_btn": "ग्रोथ रिपोर्ट बनाईं 🔍",
        "fetching": "वीडियो के जानकारी जुटावल जा रहल बा...",
        "generating": "रिपोर्ट तैयार हो रहल बा...",
        "ready": "ग्रोथ ऑडिट रिपोर्ट तैयार बा!",
        "dl_btn": "📥 पूरा रिपोर्ट डाउनलोड करीं (.txt)",
        "otp_sent": "{email} पर 6-अंक के OTP भेज दिहल गइल बा!",
        "send_otp": "OTP भेजीं 📩",
        "verify_otp": "OTP जांच करीं ✅"
    }
}

def get_ui_lang_key(selected_lang):
    if not selected_lang or "Auto-Detect" in selected_lang:
        return "English"
    for k in UI_TEXT:
        if selected_lang.startswith(k):
            return k
    return "English"

def t_ui(key, selected_lang, **kwargs):
    lk = get_ui_lang_key(selected_lang)
    txt = UI_TEXT.get(lk, UI_TEXT["English"]).get(key, UI_TEXT["English"][key])
    return txt.format(**kwargs) if kwargs else txt

# --- 4. CUSTOM STYLING (4-SIDE BORDER & CLEAN ALIGNMENT) ---
st.markdown("""
<style>
    [data-testid="stToolbarActions"] { display: none !important; }
    [data-testid="stDecoration"] { display: none !important; }
    footer { visibility: hidden !important; }

    .block-container {
        padding-top: 2.3rem !important;
        padding-bottom: 1rem !important;
        max-width: 1220px !important;
    }

    section[data-testid="stSidebar"] .block-container {
        padding-top: 1.1rem !important;
        padding-bottom: 0.5rem !important;
    }
    section[data-testid="stSidebar"] hr {
        margin: 0.45rem 0 !important;
    }

    .center-header-box {
        background: linear-gradient(135deg, #0b1324 0%, #162238 100%);
        border: 2px solid #10b981;
        border-radius: 14px;
        padding: 14px 20px;
        text-align: center;
        margin-bottom: 12px;
        box-shadow: 0 4px 16px rgba(16, 185, 129, 0.14);
    }
    .header-title-row {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        gap: 12px;
        margin-bottom: 4px;
    }
    .header-title-row h1 {
        margin: 0 !important;
        padding: 0 !important;
        font-size: 1.85rem !important;
        font-weight: 800 !important;
        color: #ffffff !important;
        letter-spacing: 0.3px;
    }
    .header-sub {
        margin: 0;
        color: #cbd5e1;
        font-size: 0.95rem;
    }
    .india-badge {
        display: inline-block;
        margin-top: 6px;
        background: rgba(16, 185, 129, 0.14);
        border: 1px solid #10b981;
        color: #34d399;
        padding: 2px 12px;
        border-radius: 999px;
        font-size: 0.78rem;
        font-weight: 600;
    }

    .status-strip {
        background: #111827;
        border: 1.5px solid #334155;
        border-radius: 10px;
        padding: 8px 14px;
        color: #f8fafc;
        font-size: 0.92rem;
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 10px;
    }

    .loading-pill {
        background: #064e3b;
        border: 1.5px solid #10b981;
        color: #ecfdf5;
        padding: 8px 14px;
        border-radius: 10px;
        font-weight: 600;
        font-size: 0.9rem;
        display: inline-flex;
        align-items: center;
        gap: 8px;
    }

    .plan-row {
        font-size: 0.88rem;
        line-height: 1.65;
        margin: 3px 0;
        color: #e2e8f0;
        display: block;
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
    ("tt_report", ""),
    ("exhausted_keys", set())
]:
    if key not in st.session_state:
        st.session_state[key] = default

# --- 6. GOOGLE OAUTH ---
try:
    if hasattr(st, "user") and getattr(st.user, "is_logged_in", False):
        g_email = getattr(st.user, "email", "")
        if g_email:
            st.session_state.verified_email = g_email.strip().lower()
except Exception:
    pass

# --- 7. GOOGLE SHEET SYNC ---
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
            if r.status_code == 200 and r.text.strip().isdigit():
                return
        except Exception:
            time.sleep(0.4)

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

q_pid = st.query_params.get("razorpay_payment_id", "")
if q_pid and not st.session_state.pro_unlocked:
    st_res = verify_payment_id(q_pid, plan="1m")
    if st_res in ["VALID", "OWNER"]:
        st.session_state.pro_unlocked = True
        st.session_state.pro_label = "PRO UNLIMITED ACTIVE"

def send_otp_email(to_email, code):
    if not SENDER_EMAIL or not SENDER_PASS:
        return False, "SMTP not configured in Secrets"
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

# --- 8. YOUTUBE FETCHER ---
def extract_youtube_id(url):
    patterns = [
        r"(?:v=|\/)([0-9A-Za-z_-]{11}).*",
        r"youtu\.be\/([0-9A-Za-z_-]{11})",
        r"shorts\/([0-9A-Za-z_-]{11})",
        r"live\/([0-9A-Za-z_-]{11})"
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
        item = v_res["items"]
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
            "default_audio_lang": snip.get("defaultAudioLanguage", snip.get("defaultLanguage", "")),
            "description": snip.get("description", "")[:1200],
            "tags": snip.get("tags", [])[:20],
            "views": int(stats.get("viewCount", 0)),
            "likes": int(stats.get("likeCount", 0)),
            "comment_count": int(stats.get("commentCount", 0)),
            "comments": comments
        }
    except Exception:
        return None

# --- 9. SINGLE-PASS GEMINI STREAMING ---
def clean_mentor_word(text):
    return text.replace("మెంటర్", "సలహాదారు").replace("స్ట్రాటజిస్ట్", "సలహాదారు")

def get_models_for_client(client):
    preferred = [
        "gemini-3.8-flash-lite",
        "gemini-3.8-flash",
        "gemini-3.5-flash-lite",
        "gemini-3.5-flash"
    ]
    try:
        avail = []
        for m in client.models.list():
            name = m.name.replace("models/", "")
            if "flash" in name and "1.5" not in name and "2.0" not in name and "2.5" not in name and "8b" not in name:
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

def generate_report_stream(prompt):
    if not GEMINI_KEYS:
        raise RuntimeError("No GEMINI_API_KEY configured in Streamlit Secrets.")

    active_keys = [k for k in GEMINI_KEYS if k not in st.session_state.exhausted_keys]
    if not active_keys:
        st.session_state.exhausted_keys = set()
        active_keys = list(GEMINI_KEYS)

    last_err = ""
    for api_key in active_keys:
        client = genai.Client(api_key=api_key)
        models = get_models_for_client(client)
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
                if "429" in last_err or "RESOURCE_EXHAUSTED" in last_err or "quota" in last_err.lower():
                    if api_key != GEMINI_KEYS[-1]:
                        st.session_state.exhausted_keys.add(api_key)
                    break
                continue
    raise RuntimeError(f"AI server is busy. Please try again in 5 seconds. ({last_err})")

# --- 10. SIDEBAR (CLEAN ORDERED PLANS + A-Z SEARCHABLE LANGUAGES) ---
with st.sidebar:
    st.markdown("### ⚙️ Settings")
    selected_lang = st.selectbox(
        "🔍 Search Language (A–Z):",
        LANGUAGES_LIST,
        index=0,
        help="Type any Indian language name to search"
    )
    audience_scope = st.radio("Audience:", ["Regional", "Global", "Both"], horizontal=True)

    st.divider()
    st.markdown("### 💎 Pro Plans")

    free_used = get_free_used_count(st.session_state.verified_email) if st.session_state.verified_email else 0
    free_left = max(0, 3 - free_used)

    if st.session_state.pro_unlocked:
        st.success(f"✅ {st.session_state.pro_label}")
    elif st.session_state.verified_email:
        if free_left > 0:
            st.info(f"🎁 **{free_left}/3** {t_ui('free_left', selected_lang)}")
        else:
            st.error(f"🔒 {t_ui('free_over', selected_lang)}")
    else:
        st.info("🎁 Login to get **3 Free Reports**")

    st.markdown(f"""
    <div class="plan-row">• <b>1 Month:</b> ₹100 👉 <a href="{RAZORPAY_1M}" target="_blank">Pay ₹100</a></div>
    <div class="plan-row">• <b>12 Months:</b> ₹1,000 👉 <a href="{RAZORPAY_12M}" target="_blank">Pay ₹1,000</a></div>
    """, unsafe_allow_html=True)

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
                st.error("❌ Used on 3 devices.")
            else:
                st.error("❌ Invalid ID.")

    st.divider()
    st.caption("📩 support@aiengtel.com | aiengtel.com")

# --- 11. CENTERED HEADER WITH LOGO & 4-SIDE BORDER (NO FLAG EMOJI) ---
logo_html = ""
if os.path.exists("logo.png"):
    with open("logo.png", "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    logo_html = f'<img src="data:image/png;base64,{b64}" style="height:42px; width:42px; border-radius:8px; object-fit:contain;" />'

st.markdown(f"""
<div class="center-header-box">
    <div class="header-title-row">
        {logo_html}
        <h1>TrendSutra AI</h1>
    </div>
    <p class="header-sub">A to Z Growth Analyzer for YouTube, Instagram &amp; TikTok Creators</p>
    <div class="india-badge">1 AI • 1 India — Supports All 22 Indian Official Languages + Bhojpuri</div>
</div>
""", unsafe_allow_html=True)

# --- 12. COMPACT SINGLE-ROW LOGIN BAR ---
if not st.session_state.verified_email and not st.session_state.pro_unlocked:
    lc1, lc2, lc3, lc4 = st.columns([1.4, 0.25, 1.5, 0.9])
    with lc1:
        if st.button("Continue with Gmail", type="primary", use_container_width=True):
            try:
                st.login("google")
            except Exception as e:
                st.error(f"Google Login Error: {e}")
    with lc2:
        st.markdown("<div style='text-align:center; padding-top:8px; color:#94a3b8; font-weight:700;'>OR</div>", unsafe_allow_html=True)
    with lc3:
        email_in = st.text_input("Email", placeholder="Login with Mail ID (Enter Email)", label_visibility="collapsed")
    with lc4:
        if st.button(t_ui("send_otp", selected_lang), use_container_width=True):
            clean_em = email_in.strip().lower()
            if "@" not in clean_em or "." not in clean_em.split("@")[-1]:
                st.error("Enter valid Email ID.")
            elif clean_em.split("@")[-1] in TEMP_DOMAINS:
                st.error("Temporary emails not allowed.")
            else:
                code = str(random.randint(100000, 999999))
                ok, err_msg = send_otp_email(clean_em, code)
                if ok:
                    st.session_state.otp_code = code
                    st.session_state.otp_target = clean_em
                    st.success(t_ui("otp_sent", selected_lang, email=clean_em))
                else:
                    st.error(f"OTP Error: {err_msg}")

    if st.session_state.otp_target:
        oc1, oc2 = st.columns([2, 1])
        with oc1:
            otp_in = st.text_input("OTP", placeholder="Enter 6-digit OTP from Email", max_chars=6, label_visibility="collapsed")
        with oc2:
            if st.button(t_ui("verify_otp", selected_lang), type="primary", use_container_width=True):
                if otp_in.strip() == st.session_state.otp_code:
                    st.session_state.verified_email = st.session_state.otp_target
                    st.session_state.otp_code = ""
                    st.rerun()
                else:
                    st.error("Invalid OTP.")
    st.stop()

# --- 13. LOGGED-IN STATUS STRIP ---
sc1, sc2 = st.columns([4, 1])
with sc1:
    badge_txt = (
        f"✅ {st.session_state.pro_label}"
        if st.session_state.pro_unlocked
        else f"🎁 {free_left}/3 {t_ui('free_left', selected_lang)}"
    )
    user_disp = st.session_state.verified_email or "Pro Member"
    st.markdown(f'<div class="status-strip"><span>👤 Logged in as <b>{user_disp}</b> &nbsp;|&nbsp; {badge_txt}</span></div>', unsafe_allow_html=True)
with sc2:
    if st.button("Logout", use_container_width=True):
        st.session_state.verified_email = ""
        st.session_state.pro_unlocked = False
        try:
            if hasattr(st, "logout"):
                st.logout()
        except Exception:
            pass
        st.rerun()

# --- 14. UNIFIED LANGUAGE INSTRUCTION HELPER ---
def build_lang_instruction(sel_lang, audio_hint=""):
    if "Auto-Detect" in sel_lang:
        hint_txt = f" (YouTube audio/language hint: {audio_hint})" if audio_hint else ""
        return f"""
LANGUAGE RULE (1 AI • 1 India Auto-Detect):
- Automatically detect the primary language of this video from its Title, Description, Tags, Audio Hint{hint_txt}, and Viewer Comments.
- At the very top of your response, output this exact single line first:
  🌐 **Detected Video Language:** [Detected Language Name]
- Then write the ENTIRE 6-section report, all 6 section headings, and all translations in that SAME detected language using its NATIVE SCRIPT (for example: Telugu in తెలుగు లిపి, Tamil in தமிழ் எழுத்து, Hindi in देवनागरी, Urdu in اردو رسم الخط, Kannada in ಕನ್ನಡ, Malayalam in മലയാളം, Bengali in বাংলা, Marathi in देवनागरी, Gujarati in ગુજરાતી, Punjabi in ਗੁਰਮੁਖੀ, Odia in ଓଡ଼ିଆ, Assamese in অসমীয়া, Bhojpuri in देवनागरी).
- NEVER write an Indian language using English/Roman letters unless the video itself is in English/Hinglish/Tenglish.
"""
    else:
        return f"""
LANGUAGE RULE:
- Write the ENTIRE 6-section report and ALL 6 section headings strictly in **{sel_lang}** using its NATIVE SCRIPT (never use Romanized/English letters for Indian scripts unless Hinglish/Tenglish/English was selected).
"""

# --- 15. MAIN WORKSPACE TABS ---
tab_yt, tab_ig, tab_tt = st.tabs(["📺 YouTube Analyzer", "📸 Instagram Reels Analyzer", "🎵 TikTok Analyzer"])

with tab_yt:
    yc1, yc2 = st.columns([3, 1.2])
    with yc1:
        yt_url = st.text_input("YouTube URL", placeholder="Paste YouTube Video or Shorts Link (https://www.youtube.com/watch?v=...)", label_visibility="collapsed")
    with yc2:
        run_yt = st.button(t_ui("gen_btn", selected_lang), key="btn_yt", type="primary", use_container_width=True)

    yt_status = st.empty()

    if run_yt:
        if not yt_url.strip():
            st.warning("Please paste a YouTube link.")
        elif not st.session_state.pro_unlocked and free_left <= 0:
            st.error(f"🔒 {t_ui('free_over', selected_lang)}")
        else:
            vid_id = extract_youtube_id(yt_url.strip())
            if not vid_id:
                st.error("❌ Invalid YouTube link.")
            else:
                yt_status.markdown(f'<div class="loading-pill">🔄 {t_ui("fetching", selected_lang)} ⏳</div>', unsafe_allow_html=True)
                data = fetch_youtube_details(vid_id)
                if not data:
                    yt_status.empty()
                    st.error("❌ Could not fetch video data. Ensure video is Public.")
                else:
                    comments_block = "\n".join(data["comments"][:15]) if data["comments"] else "No public comments available."
                    lang_rule = build_lang_instruction(selected_lang, data.get("default_audio_lang", ""))
                    prompt = f"""
You are a warm, encouraging, expert human social media growth advisor ("సలహాదారు").
Write a comprehensive, deeply detailed, easy-to-understand growth audit report (1,100 to 1,400 words) for a **{audience_scope}** audience.
Use simple everyday spoken words (never use complex bookish words, and NEVER use the word 'మెంటర్'—use 'సలహాదారు' if in Telugu).

{lang_rule}

VIDEO DATA:
- Channel: {data['channel']}
- Title: {data['title']}
- Views: {data['views']:,} | Likes: {data['likes']:,} | Comments: {data['comment_count']:,}
- Description: {data['description']}
- Tags: {', '.join(data['tags'])}
- Real Audience Comments:
{comments_block}

STRICTLY FOLLOW THIS 6-SECTION STRUCTURE (Translate all 6 section titles into the target language's native script):
### 🎬 1. Video Story Recap & Creator Appreciation
- Warmly retell the core story/message of this video based on its title, description, and comments so the creator feels you truly watched and understood their hard work.
- Genuinely praise the creator's effort, topic choice, and presentation.

### 💬 2. Real Audience Comments & Reply Templates
- Pick 4 to 5 real viewer comments from the list above, translate them naturally into the target language's native script, quote them with the viewer's name, explain what the audience loves or asks for, and give 3 ready-to-copy reply templates.

### 🔥 3. 3 Next Viral Video Ideas + 5-Sec Hooks
- Give 3 fresh follow-up video ideas tailored to this channel, each with a word-for-word 5-second opening Hook and Thumbnail idea.

### 🎯 4. Copy-Paste SEO Makeover (Titles, Description & 15 Tags)
- Provide 3 clickable high-CTR title options, a 3-line SEO description hook, and 15 searchable comma-separated tags.

### 💰 5. Monetization & Brand Earning Blueprint
- Explain 3 practical ways this channel can earn money (AdSense, Affiliate links, Brand sponsorships).

### 📅 6. Step-by-Step 30-Day Action Plan
- Give a Week 1 to Week 4 checklist of simple actions to double views and subscribers.
"""
                    yt_status.markdown(f'<div class="loading-pill">⚡ {t_ui("generating", selected_lang)} ⏳</div>', unsafe_allow_html=True)
                    report_box = st.empty()
                    full_text = ""
                    try:
                        for piece in generate_report_stream(prompt):
                            full_text += piece
                            report_box.markdown(full_text)
                        yt_status.empty()
                        st.session_state.yt_report = full_text
                        st.session_state.yt_vid_id = vid_id
                        if not st.session_state.pro_unlocked:
                            increment_free_used(st.session_state.verified_email)
                        log_usage_to_sheet(st.session_state.verified_email or "PRO", "YouTube", yt_url.strip())
                        st.rerun()
                    except Exception as e:
                        yt_status.empty()
                        st.error(str(e))

    if st.session_state.yt_report:
        st.success(f"✅ {t_ui('ready', selected_lang)}")
        st.download_button(
            t_ui("dl_btn", selected_lang),
            data=st.session_state.yt_report,
            file_name=f"TrendSutra_YouTube_Report_{st.session_state.yt_vid_id or 'audit'}.txt",
            mime="text/plain",
            use_container_width=True
        )
        st.markdown(st.session_state.yt_report)

with tab_ig:
    ic1, ic2 = st.columns([3, 1.2])
    with ic1:
        ig_url = st.text_input("Instagram URL", placeholder="Paste Instagram Reel Link (https://www.instagram.com/reel/...)", label_visibility="collapsed")
    with ic2:
        run_ig = st.button(t_ui("gen_btn", selected_lang), key="btn_ig", type="primary", use_container_width=True)

    ig_status = st.empty()

    if run_ig:
        if not ig_url.strip():
            st.warning("Please paste an Instagram Reel link.")
        elif not st.session_state.pro_unlocked and free_left <= 0:
            st.error(f"🔒 {t_ui('free_over', selected_lang)}")
        else:
            ig_status.markdown(f'<div class="loading-pill">⚡ {t_ui("generating", selected_lang)} ⏳</div>', unsafe_allow_html=True)
            lang_rule = build_lang_instruction(selected_lang)
            ig_prompt = f"""
You are a warm, encouraging human Instagram Reels growth advisor ("సలహాదారు").
Write a detailed 6-section Instagram Reels growth audit (1,000+ words) for a **{audience_scope}** audience using simple spoken words.
{lang_rule}
Reel Link: {ig_url.strip()}
Include 6 sections (headings in target language native script):
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

    if st.session_state.ig_report:
        st.success(f"✅ {t_ui('ready', selected_lang)}")
        st.download_button(
            t_ui("dl_btn", selected_lang),
            data=st.session_state.ig_report,
            file_name="TrendSutra_Instagram_Report.txt",
            mime="text/plain",
            use_container_width=True
        )
        st.markdown(st.session_state.ig_report)

with tab_tt:
    tc1, tc2 = st.columns([3, 1.2])
    with tc1:
        tt_url = st.text_input("TikTok URL", placeholder="Paste TikTok Video Link (https://www.tiktok.com/@user/video/...)", label_visibility="collapsed")
    with tc2:
        run_tt = st.button(t_ui("gen_btn", selected_lang), key="btn_tt", type="primary", use_container_width=True)

    tt_status = st.empty()

    if run_tt:
        if not tt_url.strip():
            st.warning("Please paste a TikTok link.")
        elif not st.session_state.pro_unlocked and free_left <= 0:
            st.error(f"🔒 {t_ui('free_over', selected_lang)}")
        else:
            tt_status.markdown(f'<div class="loading-pill">⚡ {t_ui("generating", selected_lang)} ⏳</div>', unsafe_allow_html=True)
            lang_rule = build_lang_instruction(selected_lang)
            tt_prompt = f"""
You are a warm, encouraging human TikTok growth advisor ("సలహాదారు").
Write a detailed 6-section TikTok growth audit (1,000+ words) for a **{audience_scope}** audience using simple spoken words.
{lang_rule}
TikTok Link: {tt_url.strip()}
Include 6 sections (headings in target language native script):
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

    if st.session_state.tt_report:
        st.success(f"✅ {t_ui('ready', selected_lang)}")
        st.download_button(
            t_ui("dl_btn", selected_lang),
            data=st.session_state.tt_report,
            file_name="TrendSutra_TikTok_Report.txt",
            mime="text/plain",
            use_container_width=True
        )
        st.markdown(st.session_state.tt_report)
