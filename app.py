import streamlit as st
from google import genai
from google.genai import types
from googleapiclient.discovery import build
import os
import re
import requests
import random
import smtplib
import base64
from email.mime.text import MIMEText
from datetime import datetime

st.set_page_config(
    page_title="TrendSutra AI - 1 AI • 1 India",
    page_icon="logo.png" if os.path.exists("logo.png") else "IN",
    layout="wide"
)

GEMINI_PAID = str(st.secrets.get("GEMINI_API_KEY", "")).strip()
GEMINI_2 = str(st.secrets.get("GEMINI_API_KEY_2", "")).strip()
GEMINI_3 = str(st.secrets.get("GEMINI_API_KEY_3", "")).strip()
GEMINI_4 = str(st.secrets.get("GEMINI_API_KEY_4", "")).strip()

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

LANGUAGE_OPTIONS = [
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
    "Kashmiri (कश्मीरी / كٲشُر)",
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
    "Sindhi (सिंधी / سنڌي)",
    "Tamil (தமிழ்)",
    "Telugu (తెలుగు)",
    "Tenglish (Telugu + English)",
    "Urdu (اردو)"
]

UI_STRINGS = {
    "English": {
        "free_left": "{n}/3 Free Reports Left",
        "free_done": "0/3 Free Reports Left (Upgrade Required)",
        "login_prompt": "Sign in to get 3 Free Growth Reports",
        "send_otp": "Send OTP 📩",
        "otp_sent": "✅ 6-digit OTP sent to {em}! Check Inbox / Spam.",
        "verify_otp": "Verify OTP ✅",
        "gen_btn": "Generate Growth Report 🔍",
        "fetching": "🔄 Fetching video details & comments... ⏳",
        "generating": "⚡ Generating report... ⏳",
        "ready": "✅ Growth Audit Report Ready!",
        "dl_btn": "📥 Download Complete Report (.txt)",
        "limit_err": "🔒 Your 3 free reports are used! Upgrade to a Pro Plan on the left for unlimited reports."
    },
    "Telugu": {
        "free_left": "{n}/3 ఉచిత రిపోర్ట్‌లు మిగిలాయి",
        "free_done": "0/3 ఉచిత రిపోర్ట్‌లు మిగిలాయి (అప్‌గ్రేడ్ చేయండి)",
        "login_prompt": "3 ఉచిత రిపోర్ట్‌ల కోసం లాగిన్ అవ్వండి",
        "send_otp": "OTP పంపండి 📩",
        "otp_sent": "✅ {em} కి 6-అంకెల OTP పంపబడింది! ఇన్‌బాక్స్ చెక్ చేయండి.",
        "verify_otp": "OTP నిర్ధారించండి ✅",
        "gen_btn": "గ్రోత్ రిపోర్ట్ తయారు చేయండి 🔍",
        "fetching": "🔄 వీడియో వివరాలు & కామెంట్లు సేకరిస్తోంది... ⏳",
        "generating": "⚡ రిపోర్ట్ తయారవుతోంది... ⏳",
        "ready": "✅ గ్రోత్ ఆడిట్ రిపోర్ట్ సిద్ధమైంది!",
        "dl_btn": "📥 పూర్తి రిపోర్ట్ డౌన్‌లోడ్ చేయండి (.txt)",
        "limit_err": "🔒 మీ 3 ఉచిత రిపోర్ట్‌లు పూర్తయ్యాయి! అన్‌లిమిటెడ్ కోసం ఎడమ వైపు Pro Plan తీసుకోండి."
    },
    "Hindi": {
        "free_left": "{n}/3 मुफ्त रिपोर्ट बाकी हैं",
        "free_done": "0/3 मुफ्त रिपोर्ट बाकी हैं (अपग्रेड करें)",
        "login_prompt": "3 मुफ्त ग्रोथ रिपोर्ट के लिए लॉगिन करें",
        "send_otp": "OTP भेजें 📩",
        "otp_sent": "✅ {em} पर 6-अंकों का OTP भेजा गया है!",
        "verify_otp": "OTP सत्यापित करें ✅",
        "gen_btn": "ग्रोथ रिपोर्ट बनाएं 🔍",
        "fetching": "🔄 वीडियो विवरण और कमेंट्स लिए जा रहे हैं... ⏳",
        "generating": "⚡ रिपोर्ट तैयार हो रही है... ⏳",
        "ready": "✅ ग्रोथ ऑडिट रिपोर्ट तैयार है!",
        "dl_btn": "📥 पूरी रिपोर्ट डाउनलोड करें (.txt)",
        "limit_err": "🔒 आपकी 3 मुफ्त रिपोर्ट समाप्त हो गई हैं! अनलिमिटेड के लिए Pro प्लान लें।"
    },
    "Tamil": {
        "free_left": "{n}/3 இலவச அறிக்கைகள் உள்ளன",
        "free_done": "0/3 இலவச அறிக்கைகள் உள்ளன (மேம்படுத்தவும்)",
        "login_prompt": "3 இலவச அறிக்கைகளுக்கு உள்நுழையவும்",
        "send_otp": "OTP அனுப்பு 📩",
        "otp_sent": "✅ {em} க்கு 6-இலக்க OTP அனுப்பப்பட்டது!",
        "verify_otp": "OTP சரிபார் ✅",
        "gen_btn": "வளர்ச்சி அறிக்கையை உருவாக்கு 🔍",
        "fetching": "🔄 வீடியோ விவரங்கள் சேகரிக்கப்படுகின்றன... ⏳",
        "generating": "⚡ அறிக்கை தயாராகிறது... ⏳",
        "ready": "✅ வளர்ச்சி அறிக்கை தயாராக உள்ளது!",
        "dl_btn": "📥 முழு அறிக்கையைப் பதிவிறக்கவும் (.txt)",
        "limit_err": "🔒 உங்கள் 3 இலவச அறிக்கைகள் முடிந்துவிட்டன! Pro திட்டத்திற்கு மாறவும்."
    },
    "Kannada": {
        "free_left": "{n}/3 ಉಚಿತ ವರದಿಗಳು ಉಳಿದಿವೆ",
        "free_done": "0/3 ಉಚಿತ ವರದಿಗಳು ಉಳಿದಿವೆ",
        "login_prompt": "3 ಉಚಿತ ವರದಿಗಳಿಗಾಗಿ ಲಾಗಿನ್ ಮಾಡಿ",
        "send_otp": "OTP ಕಳುಹಿಸಿ 📩",
        "otp_sent": "✅ {em} ಗೆ 6-ಅಂಕಿಯ OTP ಕಳುಹಿಸಲಾಗಿದೆ!",
        "verify_otp": "OTP ಪರಿಶೀಲಿಸಿ ✅",
        "gen_btn": "ಗ್ರೋತ್ ವರದಿ ರಚಿಸಿ 🔍",
        "fetching": "🔄 ವೀಡಿಯೊ ವಿವರಗಳನ್ನು ಪಡೆಯಲಾಗುತ್ತಿದೆ... ⏳",
        "generating": "⚡ ವರದಿ ಸಿದ್ಧವಾಗುತ್ತಿದೆ... ⏳",
        "ready": "✅ ಗ್ರೋತ್ ಆಡಿಟ್ ವರದಿ ಸಿದ್ಧವಾಗಿದೆ!",
        "dl_btn": "📥 ಪೂರ್ಣ ವರದಿಯನ್ನು ಡೌನ್‌ಲೋಡ್ ಮಾಡಿ (.txt)",
        "limit_err": "🔒 ನಿಮ್ಮ 3 ಉಚಿತ ವರದಿಗಳು ಮುಗಿದಿವೆ! Pro ಪ್ಲಾನ್ ಆಯ್ಕೆಮಾಡಿ."
    },
    "Malayalam": {
        "free_left": "{n}/3 സൗജന്യ റിപ്പോർട്ടുകൾ ബാക്കിയുണ്ട്",
        "free_done": "0/3 സൗജന്യ റിപ്പോർട്ടുകൾ ബാക്കിയുണ്ട്",
        "login_prompt": "3 സൗജന്യ റിപ്പോർട്ടുകൾക്കായി ലോഗിൻ ചെയ്യുക",
        "send_otp": "OTP അയക്കുക 📩",
        "otp_sent": "✅ {em} എന്നതിലേക്ക് 6-അക്ക OTP അയച്ചു!",
        "verify_otp": "OTP പരിശോധിക്കുക ✅",
        "gen_btn": "ഗ്രോത്ത് റിപ്പോർട്ട് തയ്യാറാക്കുക 🔍",
        "fetching": "🔄 വീഡിയോ വിവരങ്ങൾ ശേഖരിക്കുന്നു... ⏳",
        "generating": "⚡ റിപ്പോർട്ട് തയ്യാറാകുന്നു... ⏳",
        "ready": "✅ ഗ്രോത്ത് ഓഡിറ്റ് റിപ്പോർട്ട് തയ്യാറായി!",
        "dl_btn": "📥 പൂർണ്ണ റിപ്പോർട്ട് ഡൗൺലോഡ് ചെയ്യുക (.txt)",
        "limit_err": "🔒 നിങ്ങളുടെ 3 സൗജന്യ റിപ്പോർട്ടുകൾ കഴിഞ്ഞു! Pro പ്ലാൻ എടുക്കുക."
    },
    "Marathi": {
        "free_left": "{n}/3 मोफत रिपोर्ट शिल्लक आहेत",
        "free_done": "0/3 मोफत रिपोर्ट शिल्लक आहेत",
        "login_prompt": "3 मोफत रिपोर्टसाठी लॉगिन करा",
        "send_otp": "OTP पाठवा 📩",
        "otp_sent": "✅ {em} वर 6-अंकी OTP पाठवला आहे!",
        "verify_otp": "OTP पडताळा ✅",
        "gen_btn": "ग्रोथ रिपोर्ट तयार करा 🔍",
        "fetching": "🔄 व्हिडिओ माहिती घेतली जात आहे... ⏳",
        "generating": "⚡ रिपोर्ट तयार होत आहे... ⏳",
        "ready": "✅ ग्रोथ ऑडिट रिपोर्ट तयार आहे!",
        "dl_btn": "📥 संपूर्ण रिपोर्ट डाउनलोड करा (.txt)",
        "limit_err": "🔒 तुमचे 3 मोफत रिपोर्ट संपले आहेत! Pro प्लॅन निवडा."
    },
    "Bengali": {
        "free_left": "{n}/3 বিনামূল্যে রিপোর্ট বাকি আছে",
        "free_done": "0/3 বিনামূল্যে রিপোর্ট বাকি আছে",
        "login_prompt": "3টি ফ্রি রিপোর্টের জন্য লগইন করুন",
        "send_otp": "OTP পাঠান 📩",
        "otp_sent": "✅ {em}-এ ৬-অঙ্কের OTP পাঠানো হয়েছে!",
        "verify_otp": "OTP যাচাই করুন ✅",
        "gen_btn": "গ্রোথ রিপোর্ট তৈরি করুন 🔍",
        "fetching": "🔄 ভিডিওর তথ্য সংগ্রহ করা হচ্ছে... ⏳",
        "generating": "⚡ রিপোর্ট তৈরি হচ্ছে... ⏳",
        "ready": "✅ গ্রোথ অডিট রিপোর্ট তৈরি!",
        "dl_btn": "📥 সম্পূর্ণ রিপোর্ট ডাউনলোড করুন (.txt)",
        "limit_err": "🔒 আপনার ৩টি ফ্রি রিপোর্ট শেষ হয়েছে! Pro প্ল্যান নিন।"
    },
    "Gujarati": {
        "free_left": "{n}/3 મફત રિપોર્ટ બાકી છે",
        "free_done": "0/3 મફત રિપોર્ટ બાકી છે",
        "login_prompt": "3 મફત રિપોર્ટ માટે લોગિન કરો",
        "send_otp": "OTP મોકલો 📩",
        "otp_sent": "✅ {em} પર 6-અંકનો OTP મોકલવામાં આવ્યો છે!",
        "verify_otp": "OTP ચકાસો ✅",
        "gen_btn": "ગ્રોથ રિપોર્ટ બનાવો 🔍",
        "fetching": "🔄 વીડિયો વિગતો મેળવવામાં આવી રહી છે... ⏳",
        "generating": "⚡ રિપોર્ટ તૈયાર થઈ રહ્યો છે... ⏳",
        "ready": "✅ ગ્રોથ ઓડિટ રિપોર્ટ તૈયાર છે!",
        "dl_btn": "📥 સંપૂર્ણ રિપોર્ટ ડાઉનલોડ કરો (.txt)",
        "limit_err": "🔒 તમારા 3 મફત રિપોર્ટ પૂરા થઈ ગયા છે! Pro પ્લાન લો."
    },
    "Punjabi": {
        "free_left": "{n}/3 ਮੁਫ਼ਤ ਰਿਪੋਰਟਾਂ ਬਾਕੀ ਹਨ",
        "free_done": "0/3 ਮੁਫ਼ਤ ਰਿਪੋਰਟਾਂ ਬਾਕੀ ਹਨ",
        "login_prompt": "3 ਮੁਫ਼ਤ ਰਿਪੋਰਟਾਂ ਲਈ ਲੌਗਇਨ ਕਰੋ",
        "send_otp": "OTP ਭੇਜੋ 📩",
        "otp_sent": "✅ {em} 'ਤੇ 6-ਅੰਕਾਂ ਦਾ OTP ਭੇਜਿਆ ਗਿਆ ਹੈ!",
        "verify_otp": "OTP ਪੁਸ਼ਟੀ ਕਰੋ ✅",
        "gen_btn": "ਗਰੋਥ ਰਿਪੋਰਟ ਬਣਾਓ 🔍",
        "fetching": "🔄 ਵੀਡੀਓ ਵੇਰਵੇ ਲਏ ਜਾ ਰਹੇ ਹਨ... ⏳",
        "generating": "⚡ ਰਿਪੋਰਟ ਤਿਆਰ ਹੋ ਰਹੀ ਹੈ... ⏳",
        "ready": "✅ ਗਰੋਥ ਆਡਿਟ ਰਿਪੋਰਟ ਤਿਆਰ ਹੈ!",
        "dl_btn": "📥 ਪੂਰੀ ਰਿਪੋਰਟ ਡਾਊਨਲੋਡ ਕਰੋ (.txt)",
        "limit_err": "🔒 ਤੁਹਾਡੀਆਂ 3 ਮੁਫ਼ਤ ਰਿਪੋਰਟਾਂ ਖਤਮ ਹੋ ਗਈਆਂ ਹਨ! Pro ਪਲਾਨ ਲਓ।"
    },
    "Urdu": {
        "free_left": "{n}/3 مفت رپورٹس باقی ہیں",
        "free_done": "0/3 مفت رپورٹس باقی ہیں",
        "login_prompt": "3 مفت رپورٹس کے لیے لاگ ان کریں",
        "send_otp": "OTP بھیجیں 📩",
        "otp_sent": "✅ {em} پر 6 ہندسوں کا OTP بھیج دیا گیا ہے!",
        "verify_otp": "OTP کی تصدیق کریں ✅",
        "gen_btn": "گروتھ رپورٹ بنائیں 🔍",
        "fetching": "🔄 ویڈیو کی تفصیلات حاصل کی جا رہی ہیں... ⏳",
        "generating": "⚡ رپورٹ تیار ہو رہی ہے... ⏳",
        "ready": "✅ گروتھ آڈٹ رپورٹ تیار ہے!",
        "dl_btn": "📥 مکمل رپورٹ ڈاؤن لوڈ کریں (.txt)",
        "limit_err": "🔒 آپ کی 3 مفت رپورٹس مکمل ہو گئی ہیں! Pro پلان منتخب کریں۔"
    }
}

def get_ui_lang(selected_label, detected_lang=""):
    target = detected_lang if ("Auto-Detect" in selected_label and detected_lang) else selected_label
    for k in UI_STRINGS:
        if k != "English" and k.lower() in target.lower():
            return UI_STRINGS[k]
    return UI_STRINGS["English"]

# --- CUSTOM CSS (FULL 4-SIDED HEADER BORDER + NO TOP CLIP + COMPACT) ---
st.markdown("""
<style>
    [data-testid="stToolbarActions"] { display: none !important; }
    [data-testid="stDecoration"] { display: none !important; }
    #MainMenu { visibility: hidden !important; }
    footer { visibility: hidden !important; }

    header[data-testid="stHeader"] {
        background: transparent !important;
        height: 2.2rem !important;
    }
    .block-container {
        padding-top: 2.3rem !important;
        padding-bottom: 0.6rem !important;
        padding-left: 1.5rem !important;
        padding-right: 1.5rem !important;
        max-width: 100% !important;
    }
    section[data-testid="stSidebar"] > div:first-child {
        padding-top: 0.4rem !important;
    }
    section[data-testid="stSidebar"] .block-container {
        padding-top: 0.3rem !important;
        padding-bottom: 0.3rem !important;
    }
    section[data-testid="stSidebar"] hr {
        margin: 0.45rem 0 !important;
    }
    .hero-box {
        background: linear-gradient(135deg, #0b132b 0%, #1c2541 100%);
        padding: 16px 22px;
        border-radius: 14px;
        border: 2px solid #10b981;
        box-shadow: 0 4px 16px rgba(16, 185, 129, 0.18);
        margin-top: 4px;
        margin-bottom: 12px;
        text-align: center;
    }
    .hero-title-row {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        gap: 12px;
        margin-bottom: 4px;
    }
    .hero-title-row h1 {
        margin: 0 !important;
        padding: 0 !important;
        font-size: 1.85rem !important;
        font-weight: 800 !important;
        color: #ffffff !important;
        line-height: 1.2 !important;
    }
    .hero-sub {
        margin: 0 !important;
        color: #cbd5e1 !important;
        font-size: 0.94rem !important;
    }
    .india-badge {
        display: inline-block;
        background: rgba(16, 185, 129, 0.16);
        border: 1px solid #10b981;
        color: #6ee7b7;
        font-size: 0.76rem;
        font-weight: 700;
        padding: 2px 11px;
        border-radius: 999px;
        margin-top: 6px;
    }
    .status-strip {
        background: #111827;
        border: 1px solid #374151;
        border-radius: 9px;
        padding: 7px 14px;
        color: #f3f4f6;
        font-size: 0.88rem;
        margin-bottom: 8px;
    }
    .loading-pill {
        background: #ecfdf5;
        border: 1.5px solid #10b981;
        color: #065f46;
        padding: 7px 14px;
        border-radius: 8px;
        font-weight: 600;
        font-size: 0.88rem;
        display: inline-block;
    }
    div.stButton > button {
        height: 40px !important;
        padding: 0 14px !important;
        font-weight: 600 !important;
        border-radius: 8px !important;
    }
    div[data-testid="stTextInput"] input {
        height: 40px !important;
    }
</style>
""", unsafe_allow_html=True)

# --- SESSION STATE ---
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
if "yt_metrics" not in st.session_state:
    st.session_state.yt_metrics = None
if "ig_report" not in st.session_state:
    st.session_state.ig_report = ""
if "tt_report" not in st.session_state:
    st.session_state.tt_report = ""
if "detected_lang" not in st.session_state:
    st.session_state.detected_lang = ""
if "exhausted_keys" not in st.session_state:
    st.session_state.exhausted_keys = set()

try:
    if hasattr(st, "user") and getattr(st.user, "is_logged_in", False):
        g_email = getattr(st.user, "email", "")
        if g_email:
            st.session_state.verified_email = g_email.strip().lower()
except Exception:
    pass

# --- GOOGLE SHEET HELPERS ---
def get_free_used_count(user_id):
    if not SHEET_API or not user_id:
        return 0
    try:
        r = requests.get(
            SHEET_API,
            params={"device": user_id, "_ts": int(datetime.now().timestamp() * 1000)},
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
                params={"device": user_id, "inc": "1", "_ts": int(datetime.now().timestamp() * 1000)},
                timeout=8,
                allow_redirects=True
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
                "device": user_id,
                "platform": platform,
                "url": url,
                "_ts": int(datetime.now().timestamp() * 1000)
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
            params={"pid": pid, "plan": plan, "_ts": int(datetime.now().timestamp() * 1000)},
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
            st.session_state.pro_label = "PRO ACTIVE (Auto-Unlocked)"

def send_otp_email(to_email, code):
    if not SENDER_EMAIL or not SENDER_PASS:
        return False, "SMTP not configured"
    try:
        msg = MIMEText(
            f"Welcome to TrendSutra AI!\n\nYour 6-digit verification code is: {code}\n\n"
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

# --- YOUTUBE DATA FETCHER ---
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
                    comments.append(f"{author}: {text[:200]}")
        except Exception:
            pass
        return {
            "title": snip.get("title", ""),
            "channel": snip.get("channelTitle", ""),
            "default_audio_lang": snip.get("defaultAudioLanguage", ""),
            "default_lang": snip.get("defaultLanguage", ""),
            "description": snip.get("description", "")[:1000],
            "tags": snip.get("tags", [])[:15],
            "views": int(stats.get("viewCount", 0)),
            "likes": int(stats.get("likeCount", 0)),
            "comment_count": int(stats.get("commentCount", 0)),
            "comments": comments
        }
    except Exception:
        return None

# --- SMART 4-KEY FAILOVER + FAST GEMINI 3.8 STREAMING ---
def get_ordered_api_keys():
    candidates = [
        ("Key_4_Free", GEMINI_4),
        ("Key_3_Free", GEMINI_3),
        ("Key_2_Free", GEMINI_2),
        ("Key_1_Paid", GEMINI_PAID),
    ]
    active = []
    for label, k in candidates:
        if k and k not in [x[1] for x in active]:
            if label != "Key_1_Paid" and label in st.session_state.exhausted_keys:
                continue
            active.append((label, k))
    if not active and GEMINI_PAID:
        active.append(("Key_1_Paid", GEMINI_PAID))
    return active

def clean_mentor_word(text):
    return text.replace("మెంటర్", "సలహాదారు").replace("స్ట్రాటజిస్ట్", "సలహాదారు")

def generate_report_stream(prompt):
    api_keys = get_ordered_api_keys()
    if not api_keys:
        raise RuntimeError("API Key missing in Streamlit Secrets.")

    last_err = ""
    for key_label, api_key in api_keys:
        try:
            client = genai.Client(api_key=api_key)
            models_to_try = ["gemini-3.8-flash-lite", "gemini-3.8-flash"]
            try:
                discovered = []
                for m in client.models.list():
                    mname = m.name.replace("models/", "")
                    if "flash" in mname and "2.5" not in mname and "2.0" not in mname and "1.5" not in mname and "8b" not in mname:
                        discovered.append(mname)
                if discovered:
                    lite_first = [x for x in discovered if "lite" in x]
                    others = [x for x in discovered if "lite" not in x]
                    models_to_try = (lite_first + others)[:2]
            except Exception:
                pass

            for model_name in models_to_try:
                try:
                    response = client.models.generate_content_stream(
                        model=model_name,
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            temperature=0.8,
                            max_output_tokens=6000
                        )
                    )
                    yielded_any = False
                    for chunk in response:
                        if chunk.text:
                            yielded_any = True
                            yield clean_mentor_word(chunk.text)
                    if yielded_any:
                        return
                except Exception as me:
                    last_err = str(me)
                    if "429" in last_err or "RESOURCE_EXHAUSTED" in last_err or "quota" in last_err.lower():
                        if key_label != "Key_1_Paid":
                            st.session_state.exhausted_keys.add(key_label)
                        break
                    continue
        except Exception as ke:
            last_err = str(ke)
            continue

    raise RuntimeError(f"AI server is busy. Please try again in 5 seconds. ({last_err})")

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("### ⚙️ Settings")
    report_lang = st.selectbox("🔍 Search Language (A–Z):", LANGUAGE_OPTIONS, index=0)
    audience_scope = st.radio("Audience:", ["Regional", "Global", "Both"], horizontal=True)

    st.divider()
    st.markdown("### 💎 Pro Plans")

    ui = get_ui_lang(report_lang, st.session_state.detected_lang)
    free_used = get_free_used_count(st.session_state.verified_email) if st.session_state.verified_email else 0
    free_left = max(0, 3 - free_used)

    if st.session_state.pro_unlocked:
        st.success(f"✅ {st.session_state.pro_label}")
    elif st.session_state.verified_email:
        if free_left > 0:
            st.info(f"🎁 {ui['free_left'].format(n=free_left)}")
        else:
            st.error(f"🔒 {ui['free_done']}")
    else:
        st.info(f"🎁 {ui['login_prompt']}")

    st.markdown(f"• **1 Month:** ₹100 👉 [Pay ₹100]({RAZORPAY_1M}) • **12 Months:** ₹1,000 👉 [Pay ₹1,000]({RAZORPAY_12M})")
    plan_choice = st.radio("Plan:", ["1M (₹100)", "12M (₹1,000)"], horizontal=True, label_visibility="collapsed")
    pay_input = st.text_input("Payment ID:", placeholder="Paste Payment ID (pay_...)", label_visibility="collapsed")
    if st.button("Unlock Pro 🔓", use_container_width=True):
        if not pay_input.strip():
            st.warning("Enter Payment ID.")
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

# --- CENTERED HEADER WITH FULL 4-SIDED BORDER ---
logo_html = ""
if os.path.exists("logo.png"):
    try:
        with open("logo.png", "rb") as img_f:
            b64_logo = base64.b64encode(img_f.read()).decode("utf-8")
        logo_html = f'<img src="data:image/png;base64,{b64_logo}" style="height:44px; width:auto; border-radius:8px;" />'
    except Exception:
        logo_html = ""

st.markdown(f"""
<div class="hero-box">
    <div class="hero-title-row">
        {logo_html}
        <h1>TrendSutra AI</h1>
    </div>
    <p class="hero-sub">A to Z Growth Analyzer for YouTube, Instagram & TikTok Creators</p>
    <div class="india-badge">🇮🇳 1 AI • 1 India — Supports All 22 Indian Official Languages + Bhojpuri</div>
</div>
""", unsafe_allow_html=True)

# --- COMPACT SINGLE-ROW LOGIN BAR ---
if not st.session_state.verified_email and not st.session_state.pro_unlocked:
    lc1, lc2, lc3, lc4 = st.columns([2.2, 0.4, 2.5, 1.5])
    with lc1:
        if st.button("🔵 Continue with Gmail", type="primary", use_container_width=True):
            try:
                st.login("google")
            except Exception as e:
                st.error(f"Google Login error: {e}")
    with lc2:
        st.markdown("<div style='text-align:center; padding-top:9px; color:#9ca3af; font-weight:700;'>OR</div>", unsafe_allow_html=True)
    with lc3:
        email_in = st.text_input("Mail ID", placeholder="Login with Mail ID (e.g. name@gmail.com)", label_visibility="collapsed")
    with lc4:
        if st.button(ui["send_otp"], use_container_width=True):
            clean_em = email_in.strip().lower()
            if "@" not in clean_em or "." not in clean_em.split("@")[-1]:
                st.error("Enter valid Mail ID.")
            elif clean_em.split("@")[-1] in TEMP_DOMAINS:
                st.error("Temporary email not allowed.")
            else:
                code = str(random.randint(100000, 999999))
                ok, err_msg = send_otp_email(clean_em, code)
                if ok:
                    st.session_state.otp_code = code
                    st.session_state.otp_target = clean_em
                    st.success(ui["otp_sent"].format(em=clean_em))
                else:
                    st.error(f"OTP Error: {err_msg}")

    if st.session_state.otp_target:
        oc1, oc2 = st.columns([3, 1.5])
        with oc1:
            otp_in = st.text_input("OTP", placeholder="Enter 6-digit OTP from email", max_chars=6, label_visibility="collapsed")
        with oc2:
            if st.button(ui["verify_otp"], type="primary", use_container_width=True):
                if otp_in.strip() == st.session_state.otp_code:
                    st.session_state.verified_email = st.session_state.otp_target
                    st.session_state.otp_code = ""
                    st.rerun()
                else:
                    st.error("Wrong OTP!")
else:
    sc1, sc2 = st.columns([5.2, 1])
    with sc1:
        who = st.session_state.verified_email if st.session_state.verified_email else "Pro Member"
        badge = f"💎 {st.session_state.pro_label}" if st.session_state.pro_unlocked else f"🎁 {ui['free_left'].format(n=free_left)}"
        st.markdown(f'<div class="status-strip">👤 Logged in as <b>{who}</b> &nbsp;|&nbsp; {badge}</div>', unsafe_allow_html=True)
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

# --- WORKSPACE TABS ---
tab_yt, tab_ig, tab_tt = st.tabs(["📺 YouTube Analyzer", "📸 Instagram Reels Analyzer", "🎵 TikTok Analyzer"])

def build_language_directive(selected_lang):
    if "Auto-Detect" in selected_lang:
        return (
            "LANGUAGE RULE (AUTO-DETECT): Detect the primary language of the video from its Title, Description, Audio Language tag, and Viewer Comments. "
            "Write the ENTIRE report AND all 6 section headings in that exact detected language using its NATIVE SCRIPT "
            "(for example: Telugu in తెలుగు script, Hindi in देवनागरी script, Tamil in தமிழ் script, Kannada in ಕನ್ನಡ script, "
            "Malayalam in മലയാളം script, Marathi in देवनागरी script, Bengali in বাংলা script, Gujarati in ગુજરાતી script, "
            "Punjabi in ਗੁਰਮੁਖੀ script, Odia in ଓଡ଼ିଆ script, Urdu in اردو script, English in English). "
            "At the very top of the report, include one line: '**🌐 Detected Video Language:** <Language Name>'."
        )
    else:
        return (
            f"LANGUAGE RULE: Write the ENTIRE report AND all 6 section headings in **{selected_lang}** using its NATIVE SCRIPT "
            "(for example: Urdu in اردو script, Tamil in தமிழ் script, Telugu in తెలుగు script, Hindi in देवनागरी script). "
            "Do NOT write Indian languages in English/Roman letters unless Hinglish or Tenglish was specifically chosen."
        )

with tab_yt:
    yc1, yc2, yc3 = st.columns([3.8, 1.8, 1.4])
    with yc1:
        yt_url = st.text_input("YT Link", placeholder="Paste YouTube Video or Shorts Link...", label_visibility="collapsed")
    with yc2:
        run_yt = st.button(ui["gen_btn"], key="btn_yt", type="primary", use_container_width=True)
    with yc3:
        yt_status_slot = st.empty()

    if run_yt:
        if not st.session_state.verified_email and not st.session_state.pro_unlocked:
            st.warning(f"👆 {ui['login_prompt']}")
        elif not yt_url.strip():
            st.warning("Paste a YouTube link.")
        elif not st.session_state.pro_unlocked and free_left <= 0:
            st.error(ui["limit_err"])
        else:
            vid_id = extract_youtube_id(yt_url.strip())
            if not vid_id:
                st.error("Invalid YouTube link.")
            else:
                yt_status_slot.markdown(f'<div class="loading-pill">{ui["fetching"]}</div>', unsafe_allow_html=True)
                data = fetch_youtube_details(vid_id)
                if not data:
                    yt_status_slot.empty()
                    st.error("Could not fetch video data. Ensure video is Public.")
                else:
                    st.session_state.yt_vid_id = vid_id
                    st.session_state.yt_metrics = (data["views"], data["likes"], data["comment_count"])
                    comments_block = "\n".join(data["comments"][:12]) if data["comments"] else "No public comments."
                    lang_rule = build_language_directive(report_lang)
                    prompt = f"""
You are a warm, encouraging human social media growth advisor ("సలహాదారు").
{lang_rule}
Target Audience Scope: **{audience_scope}**.
Write a clear, engaging growth audit report (900 to 1,200 words) using simple everyday spoken words (never use complex bookish words, and NEVER use the word 'మెంటర్'—use 'సలహాదారు' if needed).

VIDEO DATA:
- Channel: {data['channel']}
- Title: {data['title']}
- Audio/Video Language Tag: {data['default_audio_lang']} / {data['default_lang']}
- Views: {data['views']:,} | Likes: {data['likes']:,} | Comments: {data['comment_count']:,}
- Description: {data['description']}
- Tags: {', '.join(data['tags'])}
- Real Audience Comments:
{comments_block}

STRICTLY INCLUDE THESE 6 SECTIONS (Translate the headings into the target language's NATIVE SCRIPT):
### 🎬 1. Video Story Recap & Creator Appreciation
- Warmly retell the core story/message of this video so the creator feels you truly understood their work, then genuinely praise their effort and strengths.
### 💬 2. What the Audience Is Saying (Translated Comments + Reply Templates)
- Quote 3 to 4 real viewer comments translated into the target language's native script, explain what viewers love/ask, and give 2 ready-to-copy reply templates.
### 🔥 3. 3 Next Viral Video Ideas + 5-Second Hooks
- Give 3 fresh follow-up video ideas with exact word-for-word 5-second opening hooks and thumbnail concepts.
### 🎯 4. Copy-Paste SEO Makeover (3 High-CTR Titles, Description & 15 Tags)
### 💰 5. Monetization & Brand Earning Blueprint
### 📅 6. Step-by-Step 30-Day Growth Action Plan (Week 1 to Week 4)
"""
                    yt_status_slot.markdown(f'<div class="loading-pill">{ui["generating"]}</div>', unsafe_allow_html=True)
                    report_box = st.empty()
                    full_text = ""
                    try:
                        for piece in generate_report_stream(prompt):
                            full_text += piece
                            report_box.markdown(full_text)
                        yt_status_slot.empty()
                        st.session_state.yt_report = full_text
                        m_lang = re.search(r"Detected Video Language:\*?\*?\s*([A-Za-z]+)", full_text)
                        if m_lang:
                            st.session_state.detected_lang = m_lang.group(1)
                        if not st.session_state.pro_unlocked:
                            increment_free_used(st.session_state.verified_email)
                        log_usage_to_sheet(st.session_state.verified_email or "PRO", "YouTube", yt_url.strip())
                        st.rerun()
                    except Exception as e:
                        yt_status_slot.empty()
                        st.error(str(e))

    if st.session_state.yt_report:
        if st.session_state.yt_metrics:
            v_cnt, l_cnt, c_cnt = st.session_state.yt_metrics
            m1, m2, m3 = st.columns(3)
            m1.metric("👀 Views", f"{v_cnt:,}")
            m2.metric("👍 Likes", f"{l_cnt:,}")
            m3.metric("💬 Comments", f"{c_cnt:,}")
        st.success(ui["ready"])
        st.download_button(
            ui["dl_btn"],
            data=st.session_state.yt_report,
            file_name=f"TrendSutra_YouTube_{st.session_state.yt_vid_id or 'Report'}.txt",
            mime="text/plain",
            use_container_width=True
        )
        st.markdown(st.session_state.yt_report)

with tab_ig:
    ic1, ic2, ic3 = st.columns([3.8, 1.8, 1.4])
    with ic1:
        ig_url = st.text_input("IG Link", placeholder="Paste Instagram Reel Link...", label_visibility="collapsed")
    with ic2:
        run_ig = st.button(ui["gen_btn"], key="btn_ig", type="primary", use_container_width=True)
    with ic3:
        ig_status_slot = st.empty()

    if run_ig:
        if not st.session_state.verified_email and not st.session_state.pro_unlocked:
            st.warning(f"👆 {ui['login_prompt']}")
        elif not ig_url.strip():
            st.warning("Paste an Instagram Reel link.")
        elif not st.session_state.pro_unlocked and free_left <= 0:
            st.error(ui["limit_err"])
        else:
            ig_status_slot.markdown(f'<div class="loading-pill">{ui["generating"]}</div>', unsafe_allow_html=True)
            lang_rule = build_language_directive(report_lang)
            ig_prompt = f"""
You are a warm, encouraging human Instagram Reels growth advisor ("సలహాదారు").
{lang_rule}
Target Audience Scope: **{audience_scope}**.
Write a 6-section Instagram Reels growth audit (900+ words) using simple spoken words (use 'సలహాదారు', never 'మెంటర్').
Reel Link: {ig_url.strip()}
Include 6 sections (headings in target language's NATIVE SCRIPT):
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
        st.success(ui["ready"])
        st.download_button(
            ui["dl_btn"],
            data=st.session_state.ig_report,
            file_name="TrendSutra_Instagram_Report.txt",
            mime="text/plain",
            use_container_width=True
        )
        st.markdown(st.session_state.ig_report)

with tab_tt:
    tc1, tc2, tc3 = st.columns([3.8, 1.8, 1.4])
    with tc1:
        tt_url = st.text_input("TT Link", placeholder="Paste TikTok Video Link...", label_visibility="collapsed")
    with tc2:
        run_tt = st.button(ui["gen_btn"], key="btn_tt", type="primary", use_container_width=True)
    with tc3:
        tt_status_slot = st.empty()

    if run_tt:
        if not st.session_state.verified_email and not st.session_state.pro_unlocked:
            st.warning(f"👆 {ui['login_prompt']}")
        elif not tt_url.strip():
            st.warning("Paste a TikTok link.")
        elif not st.session_state.pro_unlocked and free_left <= 0:
            st.error(ui["limit_err"])
        else:
            tt_status_slot.markdown(f'<div class="loading-pill">{ui["generating"]}</div>', unsafe_allow_html=True)
            lang_rule = build_language_directive(report_lang)
            tt_prompt = f"""
You are a warm, encouraging human TikTok growth advisor ("సలహాదారు").
{lang_rule}
Target Audience Scope: **{audience_scope}**.
Write a 6-section TikTok growth audit (900+ words) using simple spoken words (use 'సలహాదారు', never 'మెంటర్').
TikTok Link: {tt_url.strip()}
Include 6 sections (headings in target language's NATIVE SCRIPT):
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
        st.success(ui["ready"])
        st.download_button(
            ui["dl_btn"],
            data=st.session_state.tt_report,
            file_name="TrendSutra_TikTok_Report.txt",
            mime="text/plain",
            use_container_width=True
        )
        st.markdown(st.session_state.tt_report)
