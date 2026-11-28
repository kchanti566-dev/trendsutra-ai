code = r'''import streamlit as st
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
from PIL import Image
from email.mime.text import MIMEText

# --- 1. PAGE CONFIG ---
page_icon = "logo.png" if os.path.exists("logo.png") else "📈"
st.set_page_config(page_title="TrendSutra AI - 1 AI • 1 India", page_icon=page_icon, layout="wide")

# --- 2. LOAD SECRETS (4-KEY SMART FAILOVER) ---
KEY_1 = str(st.secrets.get("GEMINI_API_KEY", "")).strip()
KEY_2 = str(st.secrets.get("GEMINI_API_KEY_2", "")).strip()
KEY_3 = str(st.secrets.get("GEMINI_API_KEY_3", "")).strip()
KEY_4 = str(st.secrets.get("GEMINI_API_KEY_4", "")).strip()

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

# --- 3. 22 INDIAN OFFICIAL LANGUAGES + BHOJPURI (A-Z) ---
ALL_INDIAN_LANGUAGES = [
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
    "Sindhi (सिंधी)",
    "Tamil (தமிழ்)",
    "Telugu (తెలుగు)",
    "Tenglish (Telugu + English)",
    "Urdu (اردو)"
]

# --- 4. DYNAMIC UI STRINGS ---
UI_STRINGS = {
    "English": {
        "login_gmail": "Continue with Gmail",
        "or": "OR",
        "email_ph": "Login with Mail ID (creator@gmail.com)",
        "send_otp": "Send OTP 📩",
        "otp_sent": "6-digit OTP sent to {email}! Check Inbox/Spam.",
        "otp_ph": "Enter 6-digit OTP",
        "verify_otp": "Verify OTP ✅",
        "wrong_otp": "❌ Invalid OTP! Please check again.",
        "invalid_email": "❌ Please enter a valid Email ID.",
        "temp_email": "❌ Temporary emails are not allowed.",
        "logged_in": "Logged in as",
        "free_left": "{n}/3 Free Reports Left",
        "free_over": "0/3 Free Reports Left — Upgrade to Pro!",
        "logout": "Logout",
        "gen_btn": "Generate Growth Report 🔍",
        "gen_script_btn": "Generate Viral Script ✍️",
        "gen_thumb_btn": "Check Thumbnail CTR 🖼️",
        "fetching": "🔄 Fetching video details & comments... ⏳",
        "generating": "⚡ Generating report... ⏳",
        "ready": "✅ Report Ready!",
        "download": "📥 Download Report (.txt)",
        "limit_err": "🔒 Your 3 Free Reports are used! Please upgrade to Pro on the left sidebar.",
        "paste_warn": "Please paste a valid video link first.",
        "detected_lang": "🌐 Detected Language:"
    },
    "Telugu": {
        "login_gmail": "Gmail తో కొనసాగండి",
        "or": "లేదా",
        "email_ph": "Mail ID తో లాగిన్ (creator@gmail.com)",
        "send_otp": "OTP పంపండి 📩",
        "otp_sent": "{email} కి 6-అంకెల OTP పంపబడింది! ఇన్‌బాక్స్/Spam చూడండి.",
        "otp_ph": "6-అంకెల OTP ఎంటర్ చేయండి",
        "verify_otp": "OTP నిర్ధారించండి ✅",
        "wrong_otp": "❌ తప్పు OTP! దయచేసి మళ్ళీ చెక్ చేయండి.",
        "invalid_email": "❌ సరైన Email ID ఎంటర్ చేయండి.",
        "temp_email": "❌ తాత్కాలిక ఈమెయిల్ అనుమతించబడదు.",
        "logged_in": "లాగిన్:",
        "free_left": "{n}/3 ఉచిత రిపోర్ట్‌లు మిగిలాయి",
        "free_over": "0/3 ఉచిత రిపోర్ట్‌లు మిగిలాయి — Pro తీసుకోండి!",
        "logout": "లాగౌట్",
        "gen_btn": "గ్రోత్ రిపోర్ట్ తయారు చేయండి 🔍",
        "gen_script_btn": "వైరల్ స్క్రిప్ట్ రాయండి ✍️",
        "gen_thumb_btn": "థంబ్‌నెయిల్ CTR చెక్ చేయండి 🖼️",
        "fetching": "🔄 వీడియో వివరాలు & కామెంట్లు సేకరిస్తోంది... ⏳",
        "generating": "⚡ రిపోర్ట్ తయారవుతోంది... ⏳",
        "ready": "✅ రిపోర్ట్ సిద్ధమైంది!",
        "download": "📥 రిపోర్ట్ డౌన్‌లోడ్ చేయండి (.txt)",
        "limit_err": "🔒 మీ 3 ఉచిత రిపోర్ట్‌లు పూర్తయ్యాయి! ఎడమ వైపు Pro Plan తీసుకోండి.",
        "paste_warn": "దయచేసి ముందుగా వీడియో లింక్ పేస్ట్ చేయండి.",
        "detected_lang": "🌐 గుర్తించిన భాష:"
    },
    "Hindi": {
        "login_gmail": "Gmail से जारी रखें",
        "or": "या",
        "email_ph": "Mail ID से लॉगिन करें (creator@gmail.com)",
        "send_otp": "OTP भेजें 📩",
        "otp_sent": "{email} पर 6-अंकों का OTP भेजा गया है! इनबॉक्स/स्पैम देखें।",
        "otp_ph": "6-अंकों का OTP दर्ज करें",
        "verify_otp": "OTP सत्यापित करें ✅",
        "wrong_otp": "❌ गलत OTP! कृपया पुनः जांचें।",
        "invalid_email": "❌ कृपया सही Email ID दर्ज करें।",
        "temp_email": "❌ अस्थायी ईमेल की अनुमति नहीं है।",
        "logged_in": "लॉगिन:",
        "free_left": "{n}/3 मुफ्त रिपोर्ट बाकी हैं",
        "free_over": "0/3 मुफ्त रिपोर्ट बाकी हैं — Pro लें!",
        "logout": "लॉगआउट",
        "gen_btn": "ग्रोथ रिपोर्ट बनाएं 🔍",
        "gen_script_btn": "वायरल स्क्रिप्ट लिखें ✍️",
        "gen_thumb_btn": "थंबनेल CTR जांचें 🖼️",
        "fetching": "🔄 वीडियो विवरण और कमेंट्स ला रहे हैं... ⏳",
        "generating": "⚡ रिपोर्ट तैयार हो रही है... ⏳",
        "ready": "✅ रिपोर्ट तैयार है!",
        "download": "📥 रिपोर्ट डाउनलोड करें (.txt)",
        "limit_err": "🔒 आपकी 3 मुफ्त रिपोर्ट पूरी हो गई हैं! बाईं ओर से Pro प्लान लें।",
        "paste_warn": "कृपया पहले वीडियो लिंक पेस्ट करें।",
        "detected_lang": "🌐 पहचानी गई भाषा:"
    },
    "Tamil": {
        "login_gmail": "Gmail மூலம் தொடரவும்",
        "or": "அல்லது",
        "email_ph": "Mail ID மூலம் உள்நுழையவும்",
        "send_otp": "OTP அனுப்பு 📩",
        "otp_sent": "{email} க்கு 6-இலக்க OTP அனுப்பப்பட்டுள்ளது!",
        "otp_ph": "6-இலக்க OTP ஐ உள்ளிடவும்",
        "verify_otp": "OTP சரிபார்க்கவும் ✅",
        "wrong_otp": "❌ தவறான OTP! மீண்டும் சரிபார்க்கவும்.",
        "invalid_email": "❌ சரியான Email ID ஐ உள்ளிடவும்.",
        "temp_email": "❌ தற்காலிக மின்னஞ்சல் அனுமதிக்கப்படாது.",
        "logged_in": "உள்நுழைவு:",
        "free_left": "{n}/3 இலவச அறிக்கைகள் உள்ளன",
        "free_over": "0/3 இலவச அறிக்கைகள் உள்ளன — Pro பெறவும்!",
        "logout": "வெளியேறு",
        "gen_btn": "வளர்ச்சி அறிக்கை உருவாக்கு 🔍",
        "gen_script_btn": "வைரல் ஸ்கிரிப்ட் உருவாக்கு ✍️",
        "gen_thumb_btn": "தம்ப்நெயில் CTR சரிபார் 🖼️",
        "fetching": "🔄 வீடியோ விவரங்கள் சேகரிக்கப்படுகின்றன... ⏳",
        "generating": "⚡ அறிக்கை தயாராகிறது... ⏳",
        "ready": "✅ அறிக்கை தயார்!",
        "download": "📥 அறிக்கையை பதிவிறக்கவும் (.txt)",
        "limit_err": "🔒 உங்கள் 3 இலவச அறிக்கைகள் முடிந்துவிட்டன! இடதுபுறம் Pro பெறவும்.",
        "paste_warn": "முதலில் வீடியோ இணைப்பை ஒட்டவும்.",
        "detected_lang": "🌐 கண்டறியப்பட்ட மொழி:"
    },
    "Kannada": {
        "login_gmail": "Gmail ಮೂಲಕ ಮುಂದುವರಿಸಿ",
        "or": "ಅಥವಾ",
        "email_ph": "Mail ID ಮೂಲಕ ಲಾಗಿನ್ ಮಾಡಿ",
        "send_otp": "OTP ಕಳುಹಿಸಿ 📩",
        "otp_sent": "{email} ಗೆ 6-ಅಂಕಿಯ OTP ಕಳುಹಿಸಲಾಗಿದೆ!",
        "otp_ph": "6-ಅಂಕಿಯ OTP ನಮೂದಿಸಿ",
        "verify_otp": "OTP ಪರಿಶೀಲಿಸಿ ✅",
        "wrong_otp": "❌ ತಪ್ಪಾದ OTP! ದಯವಿಟ್ಟು ಮತ್ತೆ ಪರಿಶೀಲಿಸಿ.",
        "invalid_email": "❌ ಸರಿಯಾದ Email ID ನಮೂದಿಸಿ.",
        "temp_email": "❌ ತಾತ್ಕಾಲಿಕ ಇಮೇಲ್ ಅನುಮತಿಸಲಾಗುವುದಿಲ್ಲ.",
        "logged_in": "ಲಾಗಿನ್:",
        "free_left": "{n}/3 ಉಚಿತ ವರದಿಗಳು ಬಾಕಿ ಇವೆ",
        "free_over": "0/3 ಉಚಿತ ವರದಿಗಳು ಬಾಕಿ ಇವೆ — Pro ಪಡೆಯಿರಿ!",
        "logout": "ಲಾಗ್ಔಟ್",
        "gen_btn": "ಗ್ರೋತ್ ವರದಿ ತಯಾರಿಸಿ 🔍",
        "gen_script_btn": "ವೈರಲ್ ಸ್ಕ್ರಿಪ್ಟ್ ಬರೆಯಿರಿ ✍️",
        "gen_thumb_btn": "ಥಂಬ್‌ನೇಲ್ CTR ಪರಿಶೀಲಿಸಿ 🖼️",
        "fetching": "🔄 ವೀಡಿಯೊ ವಿವರಗಳನ್ನು ಸಂಗ್ರಹಿಸಲಾಗುತ್ತಿದೆ... ⏳",
        "generating": "⚡ ವರದಿ ತಯಾರಾಗುತ್ತಿದೆ... ⏳",
        "ready": "✅ ವರದಿ ಸಿದ್ಧವಾಗಿದೆ!",
        "download": "📥 ವರದಿ ಡೌನ್‌ಲೋಡ್ ಮಾಡಿ (.txt)",
        "limit_err": "🔒 ನಿಮ್ಮ 3 ಉಚಿತ ವರದಿಗಳು ಮುಗಿದಿವೆ! ಎಡಭಾಗದಲ್ಲಿ Pro ಪಡೆಯಿರಿ.",
        "paste_warn": "ದಯವಿಟ್ಟು ಮೊದಲು ವೀಡಿಯೊ ಲಿಂಕ್ ಅಂಟಿಸಿ.",
        "detected_lang": "🌐 ಗುರುತಿಸಲಾದ ಭಾಷೆ:"
    },
    "Malayalam": {
        "login_gmail": "Gmail വഴി തുടരുക",
        "or": "അല്ലെങ്കിൽ",
        "email_ph": "Mail ID വഴി ലോഗിൻ ചെയ്യുക",
        "send_otp": "OTP അയയ്ക്കുക 📩",
        "otp_sent": "{email} എന്നതിലേക്ക് 6-അക്ക OTP അയച്ചു!",
        "otp_ph": "6-അക്ക OTP നൽകുക",
        "verify_otp": "OTP സ്ഥിരീകരിക്കുക ✅",
        "wrong_otp": "❌ തെറ്റായ OTP! വീണ്ടും പരിശോധിക്കുക.",
        "invalid_email": "❌ ശരിയായ Email ID നൽകുക.",
        "temp_email": "❌ താൽക്കാലിക ഇമെയിൽ അനുവദനീയമല്ല.",
        "logged_in": "ലോഗിൻ:",
        "free_left": "{n}/3 സൗജന്യ റിപ്പോർട്ടുകൾ ബാക്കിയുണ്ട്",
        "free_over": "0/3 സൗജന്യ റിപ്പോർട്ടുകൾ ബാക്കിയുണ്ട് — Pro എടുക്കുക!",
        "logout": "ലോഗൗട്ട്",
        "gen_btn": "ഗ്രോത്ത് റിപ്പോർട്ട് നിർമ്മിക്കുക 🔍",
        "gen_script_btn": "വൈറൽ സ്ക്രിപ്റ്റ് എഴുതുക ✍️",
        "gen_thumb_btn": "തംബ്നെയിൽ CTR പരിശോധിക്കുക 🖼️",
        "fetching": "🔄 വീഡിയോ വിവരങ്ങൾ ശേഖരിക്കുന്നു... ⏳",
        "generating": "⚡ റിപ്പോർട്ട് തയ്യാറാകുന്നു... ⏳",
        "ready": "✅ റിപ്പോർട്ട് തയ്യാറാണ്!",
        "download": "📥 റിപ്പോർട്ട് ഡൗൺലോഡ് ചെയ്യുക (.txt)",
        "limit_err": "🔒 നിങ്ങളുടെ 3 സൗജന്യ റിപ്പോർട്ടുകൾ കഴിഞ്ഞു! ഇടതുവശത്ത് Pro എടുക്കുക.",
        "paste_warn": "ദയവായി ആദ്യം വീഡിയോ ലിങ്ക് ഒട്ടിക്കുക.",
        "detected_lang": "🌐 തിരിച്ചറിഞ്ഞ ഭാഷ:"
    },
    "Urdu": {
        "login_gmail": "Gmail کے ساتھ جاری رکھیں",
        "or": "یا",
        "email_ph": "Mail ID سے لاگ ان کریں",
        "send_otp": "OTP بھیجیں 📩",
        "otp_sent": "{email} پر 6 ہندسوں کا OTP بھیج دیا گیا ہے!",
        "otp_ph": "6 ہندسوں کا OTP درج کریں",
        "verify_otp": "OTP کی تصدیق کریں ✅",
        "wrong_otp": "❌ غلط OTP! براہ کرم دوبارہ چیک کریں۔",
        "invalid_email": "❌ براہ کرم درست Email ID درج کریں۔",
        "temp_email": "❌ عارضی ای میل کی اجازت نہیں ہے۔",
        "logged_in": "لاگ ان:",
        "free_left": "{n}/3 مفت رپورٹس باقی ہیں",
        "free_over": "0/3 مفت رپورٹس باقی ہیں — Pro لیں!",
        "logout": "لاگ آؤٹ",
        "gen_btn": "گروتھ رپورٹ بنائیں 🔍",
        "gen_script_btn": "وائرل اسکرپٹ لکھیں ✍️",
        "gen_thumb_btn": "تھمب نیل CTR چیک کریں 🖼️",
        "fetching": "🔄 ویڈیو کی تفصیلات حاصل کی جا رہی ہیں... ⏳",
        "generating": "⚡ رپورٹ تیار ہو رہی ہے... ⏳",
        "ready": "✅ رپورٹ تیار ہے!",
        "download": "📥 رپورٹ ڈاؤن لوڈ کریں (.txt)",
        "limit_err": "🔒 آپ کی 3 مفت رپورٹس مکمل ہو گئی ہیں! بائیں جانب سے Pro پلان لیں۔",
        "paste_warn": "براہ کرم پہلے ویڈیو لنک پیسٹ کریں۔",
        "detected_lang": "🌐 شناخت شدہ زبان:"
    }
}

def get_ui_lang_key(selected_lang, detected_lang=""):
    target = detected_lang if (selected_lang == "Auto-Detect Video Language" and detected_lang) else selected_lang
    t_low = target.lower()
    if "tenglish" in t_low or "hinglish" in t_low or "auto-detect" in t_low:
        return "English"
    for k in UI_STRINGS.keys():
        if k.lower() in t_low:
            return k
    return "English"

def ui(key, selected_lang, detected_lang="", **kwargs):
    lk = get_ui_lang_key(selected_lang, detected_lang)
    txt = UI_STRINGS.get(lk, UI_STRINGS["English"]).get(key, UI_STRINGS["English"][key])
    return txt.format(**kwargs) if kwargs else txt

# --- 5. COMPACT NO-SCROLL STYLING & 4-SIDED HEADER BORDER ---
st.markdown("""
<style>
    [data-testid="stToolbarActions"] { display: none !important; }
    [data-testid="stDecoration"] { display: none !important; }
    [data-testid="stStatusWidget"] { display: none !important; }
    #MainMenu { visibility: hidden !important; }
    footer { visibility: hidden !important; }

    .block-container {
        padding-top: 2.3rem !important;
        padding-bottom: 1rem !important;
        max-width: 1180px;
    }

    section[data-testid="stSidebar"] > div {
        padding-top: 0.6rem !important;
        padding-bottom: 0.5rem !important;
    }
    section[data-testid="stSidebar"] .stMarkdown p {
        margin-bottom: 0.25rem !important;
        font-size: 0.88rem !important;
    }
    section[data-testid="stSidebar"] hr {
        margin: 0.45rem 0 !important;
    }

    .main-header {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        padding: 16px 22px;
        border-radius: 14px;
        border: 2px solid #10b981;
        margin-bottom: 12px;
        text-align: center;
    }
    .header-brand-row {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 12px;
        margin-bottom: 4px;
    }
    .main-header h1 {
        margin: 0 !important;
        padding: 0 !important;
        font-size: 1.85rem !important;
        color: #ffffff !important;
        line-height: 1.2 !important;
    }
    .main-header p {
        margin: 4px 0 0 0 !important;
        color: #cbd5e1 !important;
        font-size: 0.96rem !important;
    }
    .india-badge {
        display: inline-block;
        background: rgba(16, 185, 129, 0.16);
        border: 1px solid #10b981;
        color: #6ee7b7;
        padding: 2px 12px;
        border-radius: 20px;
        font-size: 0.78rem;
        font-weight: 600;
        margin-top: 6px;
    }
    .status-strip {
        background: #1e293b;
        border: 1px solid #334155;
        padding: 7px 14px;
        border-radius: 10px;
        color: #e2e8f0;
        font-size: 0.9rem;
    }
    .loading-pill {
        background: #064e3b;
        border: 1.5px solid #10b981;
        color: #ecfdf5;
        padding: 8px 14px;
        border-radius: 8px;
        font-weight: 600;
        font-size: 0.9rem;
        text-align: center;
    }
    div.stButton > button {
        height: 42px !important;
        padding-top: 0px !important;
        padding-bottom: 0px !important;
        font-weight: 600 !important;
    }
    div[data-testid="stTextInput"] input {
        height: 42px !important;
    }
</style>
""", unsafe_allow_html=True)

# --- 6. SESSION STATE ---
for k, v in {
    "verified_email": "",
    "otp_code": "",
    "otp_target": "",
    "pro_unlocked": False,
    "pro_label": "",
    "yt_report": "",
    "yt_vid_id": "",
    "yt_metrics": None,
    "yt_detected_lang": "",
    "ig_report": "",
    "ig_detected_lang": "",
    "tt_report": "",
    "tt_detected_lang": "",
    "script_report": "",
    "thumb_report": "",
    "exhausted_keys": set()
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# --- 7. CHECK GOOGLE OAUTH & RAZORPAY REDIRECT ---
try:
    if hasattr(st, "user") and getattr(st.user, "is_logged_in", False):
        g_email = getattr(st.user, "email", "")
        if g_email:
            st.session_state.verified_email = g_email.strip().lower()
except Exception:
    pass

# --- 8. GOOGLE SHEET HELPERS ---
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
        if r.status_code == 200:
            txt = r.text.strip()
            if txt.isdigit():
                return min(3, int(txt))
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
            if r.status_code == 200 and r.text.strip().isdigit():
                return
        except Exception:
            time.sleep(0.3)

def log_usage_to_sheet(user_id, platform, url):
    if not SHEET_API:
        return
    try:
        requests.get(
            SHEET_API,
            params={"log": "1", "device": user_id, "platform": platform, "url": url, "_ts": int(time.time() * 1000)},
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

q_pid = st.query_params.get("razorpay_payment_id", "")
if q_pid and not st.session_state.pro_unlocked:
    st_res = verify_payment_id(q_pid, plan="1m")
    if st_res in ["VALID", "OWNER"]:
        st.session_state.pro_unlocked = True
        st.session_state.pro_label = "PRO UNLIMITED ACTIVE"

def send_otp_email(to_email, code):
    if not SENDER_EMAIL or not SENDER_PASS:
        return False, "SMTP not configured"
    try:
        body_text = (
            "Welcome to TrendSutra AI (1 AI • 1 India)!\n\n"
            f"Your 6-digit verification code is: {code}\n\n"
            "Enter this code on TrendSutra AI to unlock your 3 Free Growth Reports."
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
            "default_audio_lang": snip.get("defaultAudioLanguage", ""),
            "description": snip.get("description", "")[:1200],
            "tags": snip.get("tags", [])[:20],
            "views": int(stats.get("viewCount", 0)),
            "likes": int(stats.get("likeCount", 0)),
            "comment_count": int(stats.get("commentCount", 0)),
            "comments": comments
        }
    except Exception:
        return None

# --- 10. 4-KEY SMART FAILOVER + FAST STREAMING ---
@st.cache_data(ttl=3600, show_spinner=False)
def discover_models_for_key(api_key):
    preferred = [
        "gemini-3.8-flash-lite",
        "gemini-3.8-flash",
        "gemini-2.5-flash-lite",
        "gemini-2.5-flash"
    ]
    try:
        client = genai.Client(api_key=api_key)
        avail = []
        for m in client.models.list():
            name = m.name.replace("models/", "")
            if "flash" in name and "1.5" not in name and "2.0" not in name and "8b" not in name:
                avail.append(name)
        ordered = [p for p in preferred if p in avail]
        for a in avail:
            if a not in ordered:
                ordered.append(a)
        if ordered:
            return ordered[:3]
    except Exception:
        pass
    return ["gemini-3.8-flash-lite", "gemini-3.8-flash"]

def clean_mentor_word(text):
    return text.replace("మెంటర్", "సలహాదారు").replace("స్ట్రాటజిస్ట్", "సలహాదారు")

def generate_report_stream(contents):
    raw_keys = [
        ("KEY_4", KEY_4),
        ("KEY_3", KEY_3),
        ("KEY_2", KEY_2),
        ("KEY_1_PAID", KEY_1)
    ]
    active_keys = []
    seen = set()
    for label, k in raw_keys:
        if k and k not in seen and label not in st.session_state.exhausted_keys:
            seen.add(k)
            active_keys.append((label, k))
    if not active_keys:
        st.session_state.exhausted_keys.clear()
        for label, k in raw_keys:
            if k and k not in seen:
                seen.add(k)
                active_keys.append((label, k))

    last_err = ""
    for label, api_key in active_keys:
        client = genai.Client(api_key=api_key)
        models = discover_models_for_key(api_key)
        for model_name in models:
            try:
                response = client.models.generate_content_stream(
                    model=model_name,
                    contents=contents,
                    config=types.GenerateContentConfig(temperature=0.82, max_output_tokens=8192)
                )
                yielded = False
                for chunk in response:
                    if chunk.text:
                        yielded = True
                        yield clean_mentor_word(chunk.text)
                if yielded:
                    return
            except Exception as e:
                last_err = str(e)
                err_low = last_err.lower()
                if "429" in err_low or "quota" in err_low or "resource_exhausted" in err_low:
                    if label != "KEY_1_PAID":
                        st.session_state.exhausted_keys.add(label)
                    break
                continue
    raise RuntimeError(f"AI సర్వర్ రద్దీగా ఉంది. 5 సెకన్ల తర్వాత మళ్ళీ ప్రయత్నించండి. ({last_err})")

# --- 11. SIDEBAR ---
with st.sidebar:
    st.markdown("### ⚙️ Settings")
    report_lang = st.selectbox(
        "🔍 Search Language (A–Z):",
        ALL_INDIAN_LANGUAGES,
        index=0
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
            st.info(f"🎁 {ui('free_left', report_lang, n=free_left)}")
        else:
            st.error(f"🔒 {ui('free_over', report_lang)}")
    else:
        st.info("🎁 Login for 3 Free Reports")

    st.markdown(f"• **1 Month:** ₹100 👉 [Pay ₹100]({RAZORPAY_1M})")
    st.markdown(f"• **12 Months:** ₹1,000 👉 [Pay ₹1,000]({RAZORPAY_12M})")
    plan_choice = st.radio("Plan:", ["1M (₹100)", "12M (₹1,000)"], horizontal=True, label_visibility="collapsed")
    pay_input = st.text_input("Payment ID:", placeholder="Paste Payment ID (pay_...)", label_visibility="collapsed")

    if st.button("Unlock Pro 🔓", use_container_width=True):
        if pay_input.strip():
            p_code = "12m" if "12" in plan_choice else "1m"
            status = verify_payment_id(pay_input, plan=p_code)
            if status in ["OWNER", "VALID"]:
                st.session_state.pro_unlocked = True
                st.session_state.pro_label = "OWNER UNLIMITED" if status == "OWNER" else f"PRO ({plan_choice})"
                st.rerun()
            elif status == "EXPIRED":
                st.error("⏰ Plan expired! Please renew.")
            elif status == "ALREADY_USED":
                st.error("❌ Used on 3 devices already.")
            else:
                st.error("❌ Invalid Payment ID.")

    st.divider()
    st.caption("📩 support@aiengtel.com | © 2026 TrendSutra AI")

# --- 12. CENTERED HEADER WITH LOGO & 4-SIDED BORDER ---
logo_html = ""
if os.path.exists("logo.png"):
    with open("logo.png", "rb") as lf:
        b64_logo = base64.b64encode(lf.read()).decode()
    logo_html = f'<img src="data:image/png;base64,{b64_logo}" style="width:42px; height:42px; border-radius:9px; object-fit:contain;" />'

st.markdown(f"""
<div class="main-header">
    <div class="header-brand-row">
        {logo_html}
        <h1>TrendSutra AI</h1>
    </div>
    <p>A to Z Growth Analyzer for YouTube, Instagram & TikTok Creators</p>
    <div class="india-badge">1 AI • 1 India — Supports All 22 Indian Official Languages + Bhojpuri</div>
</div>
""", unsafe_allow_html=True)

# --- 13. COMPACT LOGIN BAR / STATUS BAR ---
if not st.session_state.verified_email and not st.session_state.pro_unlocked:
    c_g, c_or, c_em, c_btn = st.columns([2.2, 0.45, 2.5, 1.4])
    with c_g:
        if st.button(f"🔵 {ui('login_gmail', report_lang)}", type="primary", use_container_width=True):
            try:
                st.login("google")
            except Exception as e:
                st.error(f"Google Login error: {e}")
    with c_or:
        st.markdown(f"<div style='text-align:center; padding-top:10px; color:#94a3b8; font-weight:700;'>{ui('or', report_lang)}</div>", unsafe_allow_html=True)
    with c_em:
        email_in = st.text_input("Mail", placeholder=ui("email_ph", report_lang), label_visibility="collapsed")
    with c_btn:
        if st.button(ui("send_otp", report_lang), use_container_width=True):
            clean_em = email_in.strip().lower()
            if "@" not in clean_em or "." not in clean_em.split("@")[-1]:
                st.error(ui("invalid_email", report_lang))
            elif clean_em.split("@")[-1] in TEMP_DOMAINS:
                st.error(ui("temp_email", report_lang))
            else:
                code = str(random.randint(100000, 999999))
                ok, err_msg = send_otp_email(clean_em, code)
                if ok:
                    st.session_state.otp_code = code
                    st.session_state.otp_target = clean_em
                    st.success(f"✅ {ui('otp_sent', report_lang, email=clean_em)}")
                else:
                    st.error(f"OTP Error: {err_msg}")

    if st.session_state.otp_target:
        oc1, oc2 = st.columns([3, 1.5])
        with oc1:
            otp_in = st.text_input("OTP", placeholder=ui("otp_ph", report_lang), max_chars=6, label_visibility="collapsed")
        with oc2:
            if st.button(ui("verify_otp", report_lang), type="primary", use_container_width=True):
                if otp_in.strip() == st.session_state.otp_code:
                    st.session_state.verified_email = st.session_state.otp_target
                    st.session_state.otp_code = ""
                    st.rerun()
                else:
                    st.error(ui("wrong_otp", report_lang))
    st.stop()
else:
    s1, s2 = st.columns([5, 1.2])
    with s1:
        badge = f"✅ {st.session_state.pro_label}" if st.session_state.pro_unlocked else f"🎁 {ui('free_left', report_lang, n=free_left)}"
        st.markdown(f"<div class='status-strip'>👤 {ui('logged_in', report_lang)} <b>{st.session_state.verified_email}</b> &nbsp;|&nbsp; {badge}</div>", unsafe_allow_html=True)
    with s2:
        if st.button(ui("logout", report_lang), use_container_width=True):
            st.session_state.verified_email = ""
            st.session_state.pro_unlocked = False
            st.session_state.yt_report = ""
            st.session_state.ig_report = ""
            st.session_state.tt_report = ""
            st.session_state.script_report = ""
            st.session_state.thumb_report = ""
            try:
                if hasattr(st, "logout"):
                    st.logout()
            except Exception:
                pass
            st.rerun()

# --- 14. SINGLE-PASS LANGUAGE + REPORT INSTRUCTION ---
def build_language_directive(selected_lang):
    if selected_lang == "Auto-Detect Video Language":
        return """
LANGUAGE & SCRIPT RULE (CRITICAL):
- Detect the primary spoken/written language of this video/content from its title, description, audio tag, and audience comments.
- First, output a single top line in exact format: `🌐 Detected Language: <Language Name>`
- Then write the ENTIRE report (all 6 headings and every paragraph) in that EXACT detected language using its **NATIVE SCRIPT** (e.g., Urdu in اردو script, Tamil in தமிழ் script, Telugu in తెలుగు script, Hindi in हिन्दी script, Kannada in ಕನ್ನಡ script, Malayalam in മലയാളം script, Bengali in বাংলা script, Marathi in मराठी script, etc. Never write Indian languages in Roman/English letters unless English is the video language).
"""
    else:
        return f"""
LANGUAGE & SCRIPT RULE (CRITICAL):
- Write the ENTIRE report (all 6 headings and every paragraph) in **{selected_lang}** using its **NATIVE SCRIPT** (never transliterate into English letters unless English/Hinglish/Tenglish was explicitly chosen).
"""

def parse_detected_lang(text):
    m = re.search(r"Detected Language:\s*([^\n\r*]+)", text)
    return m.group(1).strip() if m else ""

# --- 15. MAIN WORKSPACE (5 PRO TABS) ---
tab_yt, tab_ig, tab_tt, tab_sc, tab_th = st.tabs([
    "📺 YouTube Analyzer",
    "📸 Instagram Reels",
    "🎵 TikTok Analyzer",
    "✍️ Viral Script Generator",
    "🖼️ AI Thumbnail Checker"
])

# === TAB 1: YOUTUBE ANALYZER ===
with tab_yt:
    yc1, yc2, yc3 = st.columns([3.8, 1.8, 1.6])
    with yc1:
        yt_url = st.text_input("YT Link", placeholder="Paste YouTube Video or Shorts Link...", label_visibility="collapsed")
    with yc2:
        run_yt = st.button(ui("gen_btn", report_lang), key="btn_yt", type="primary", use_container_width=True)
    with yc3:
        yt_status_slot = st.empty()

    if run_yt:
        if not yt_url.strip():
            st.warning(ui("paste_warn", report_lang))
        elif not st.session_state.pro_unlocked and free_left <= 0:
            st.error(ui("limit_err", report_lang))
        else:
            vid_id = extract_youtube_id(yt_url.strip())
            if not vid_id:
                st.error("❌ Please enter a valid YouTube video or Shorts link.")
            else:
                yt_status_slot.markdown(f"<div class='loading-pill'>{ui('fetching', report_lang)}</div>", unsafe_allow_html=True)
                data = fetch_youtube_details(vid_id)
                if not data:
                    yt_status_slot.empty()
                    st.error("❌ Could not fetch video details. Make sure the video is Public.")
                else:
                    comments_block = "\n".join(data["comments"][:15]) if data["comments"] else "No public comments."
                    lang_rule = build_language_directive(report_lang)
                    prompt = f"""
You are a warm, encouraging, expert human social media growth advisor ("సలహాదారు").
{lang_rule}
Write a comprehensive, deeply detailed 6-section growth audit report (1,100 to 1,400 words) for a **{audience_scope}** audience using simple everyday spoken words (never use the word 'మెంటర్').

VIDEO DATA:
- Channel: {data['channel']} | Audio Tag: {data['default_audio_lang']}
- Title: {data['title']}
- Views: {data['views']:,} | Likes: {data['likes']:,} | Comments: {data['comment_count']:,}
- Description: {data['description']}
- Tags: {', '.join(data['tags'])}
- Real Audience Comments:
{comments_block}

STRICTLY INCLUDE THESE 6 SECTIONS (translate headings into the target native script):
### 🎬 1. Video Story Recap & Creator Appreciation
### 💬 2. Real Audience Comments & Reply Templates
### 🔥 3. 3 Next Viral Video Ideas + 5-Sec Hooks
### 🎯 4. Copy-Paste SEO Makeover (Titles, Description & 15 Tags)
### 💰 5. Monetization & Brand Earning Blueprint
### 📅 6. Step-by-Step 30-Day Growth Action Plan
"""
                    yt_status_slot.markdown(f"<div class='loading-pill'>{ui('generating', report_lang)}</div>", unsafe_allow_html=True)
                    report_box = st.empty()
                    full_text = ""
                    try:
                        for piece in generate_report_stream(prompt):
                            full_text += piece
                            report_box.markdown(full_text)
                        yt_status_slot.empty()
                        st.session_state.yt_report = full_text
                        st.session_state.yt_vid_id = vid_id
                        st.session_state.yt_metrics = (data["views"], data["likes"], data["comment_count"])
                        st.session_state.yt_detected_lang = parse_detected_lang(full_text)
                        if not st.session_state.pro_unlocked:
                            increment_free_used(st.session_state.verified_email)
                        log_usage_to_sheet(st.session_state.verified_email or "PRO", "YouTube", yt_url.strip())
                        st.rerun()
                    except Exception as e:
                        yt_status_slot.empty()
                        st.error(str(e))

    if st.session_state.yt_report:
        if st.session_state.yt_metrics:
            v, l, c = st.session_state.yt_metrics
            m1, m2, m3 = st.columns(3)
            m1.metric("👀 Views", f"{v:,}")
            m2.metric("👍 Likes", f"{l:,}")
            m3.metric("💬 Comments", f"{c:,}")
        st.success(ui("ready", report_lang, st.session_state.yt_detected_lang))
        st.markdown(st.session_state.yt_report)
        st.download_button(
            ui("download", report_lang, st.session_state.yt_detected_lang),
            data=st.session_state.yt_report,
            file_name=f"TrendSutra_YouTube_{st.session_state.yt_vid_id}.txt",
            mime="text/plain",
            key="dl_yt",
            use_container_width=True
        )

# === TAB 2: INSTAGRAM REELS ===
with tab_ig:
    ic1, ic2, ic3 = st.columns([3.8, 1.8, 1.6])
    with ic1:
        ig_url = st.text_input("IG Link", placeholder="Paste Instagram Reel Link...", label_visibility="collapsed")
    with ic2:
        run_ig = st.button(ui("gen_btn", report_lang), key="btn_ig", type="primary", use_container_width=True)
    with ic3:
        ig_status_slot = st.empty()

    if run_ig:
        if not ig_url.strip():
            st.warning(ui("paste_warn", report_lang))
        elif not st.session_state.pro_unlocked and free_left <= 0:
            st.error(ui("limit_err", report_lang))
        else:
            ig_status_slot.markdown(f"<div class='loading-pill'>{ui('generating', report_lang)}</div>", unsafe_allow_html=True)
            lang_rule = build_language_directive(report_lang)
            ig_prompt = f"""
You are a warm, encouraging human Instagram Reels growth advisor ("సలహాదారు").
{lang_rule}
Write a detailed 6-section Instagram Reels growth audit (1,000+ words) for a **{audience_scope}** audience using simple spoken words (never use 'మెంటర్').
Reel Link: {ig_url.strip()}
Sections (in target native script):
### 🎬 1. Reel Strategy & Creator Appreciation
### 👀 2. Watch-Time, Audio & 3-Second Retention Analysis
### 🔥 3. 3 Viral Follow-Up Reel Ideas + Word-for-Word Hooks
### 🎯 4. Copy-Paste Caption & 15 Trending Hashtags
### 💰 5. Brand Collaboration & Monetization Blueprint
### 📅 6. 30-Day Instagram Growth Action Plan
"""
            report_box = st.empty()
            full_text = ""
            try:
                for piece in generate_report_stream(ig_prompt):
                    full_text += piece
                    report_box.markdown(full_text)
                ig_status_slot.empty()
                st.session_state.ig_report = full_text
                st.session_state.ig_detected_lang = parse_detected_lang(full_text)
                if not st.session_state.pro_unlocked:
                    increment_free_used(st.session_state.verified_email)
                log_usage_to_sheet(st.session_state.verified_email or "PRO", "Instagram", ig_url.strip())
                st.rerun()
            except Exception as e:
                ig_status_slot.empty()
                st.error(str(e))

    if st.session_state.ig_report:
        st.success(ui("ready", report_lang, st.session_state.ig_detected_lang))
        st.markdown(st.session_state.ig_report)
        st.download_button(
            ui("download", report_lang, st.session_state.ig_detected_lang),
            data=st.session_state.ig_report,
            file_name="TrendSutra_Instagram_Report.txt",
            mime="text/plain",
            key="dl_ig",
            use_container_width=True
        )

# === TAB 3: TIKTOK ANALYZER ===
with tab_tt:
    tc1, tc2, tc3 = st.columns([3.8, 1.8, 1.6])
    with tc1:
        tt_url = st.text_input("TT Link", placeholder="Paste TikTok Video Link...", label_visibility="collapsed")
    with tc2:
        run_tt = st.button(ui("gen_btn", report_lang), key="btn_tt", type="primary", use_container_width=True)
    with tc3:
        tt_status_slot = st.empty()

    if run_tt:
        if not tt_url.strip():
            st.warning(ui("paste_warn", report_lang))
        elif not st.session_state.pro_unlocked and free_left <= 0:
            st.error(ui("limit_err", report_lang))
        else:
            tt_status_slot.markdown(f"<div class='loading-pill'>{ui('generating', report_lang)}</div>", unsafe_allow_html=True)
            lang_rule = build_language_directive(report_lang)
            tt_prompt = f"""
You are a warm, encouraging human TikTok growth advisor ("సలహాదారు").
{lang_rule}
Write a detailed 6-section TikTok growth audit (1,000+ words) for a **{audience_scope}** audience using simple spoken words (never use 'మెంటర్').
TikTok Link: {tt_url.strip()}
Sections (in target native script):
### 🎬 1. Video Potential & Creator Appreciation
### 🔄 2. Completion Rate & Looping Hook Formula
### 🔥 3. 3 Viral Follow-Up TikTok Ideas + Word-for-Word Hooks
### 🎯 4. Copy-Paste Caption & 15 FYP Hashtags
### 💰 5. Creator Rewards & Brand Monetization Plan
### 📅 6. 30-Day TikTok Growth Action Plan
"""
            report_box = st.empty()
            full_text = ""
            try:
                for piece in generate_report_stream(tt_prompt):
                    full_text += piece
                    report_box.markdown(full_text)
                tt_status_slot.empty()
                st.session_state.tt_report = full_text
                st.session_state.tt_detected_lang = parse_detected_lang(full_text)
                if not st.session_state.pro_unlocked:
                    increment_free_used(st.session_state.verified_email)
                log_usage_to_sheet(st.session_state.verified_email or "PRO", "TikTok", tt_url.strip())
                st.rerun()
            except Exception as e:
                tt_status_slot.empty()
                st.error(str(e))

    if st.session_state.tt_report:
        st.success(ui("ready", report_lang, st.session_state.tt_detected_lang))
        st.markdown(st.session_state.tt_report)
        st.download_button(
            ui("download", report_lang, st.session_state.tt_detected_lang),
            data=st.session_state.tt_report,
            file_name="TrendSutra_TikTok_Report.txt",
            mime="text/plain",
            key="dl_tt",
            use_container_width=True
        )

# === TAB 4: VIRAL SCRIPT GENERATOR ===
with tab_sc:
    sc1, sc2, sc3, sc4 = st.columns([2.8, 1.3, 1.3, 1.5])
    with sc1:
        script_topic = st.text_input("Topic", placeholder="Enter Video Topic (e.g., How to save mobile battery)...", label_visibility="collapsed")
    with sc2:
        script_len = st.selectbox("Duration", ["Shorts / Reel (60 Sec)", "Medium Video (3–5 Min)", "Long Video (8–10 Min)"], label_visibility="collapsed")
    with sc3:
        script_tone = st.selectbox("Tone", ["Engaging & Friendly", "High-Energy / Viral", "Emotional / Storytelling", "Educational / Clear"], label_visibility="collapsed")
    with sc4:
        run_sc = st.button(ui("gen_script_btn", report_lang), key="btn_sc", type="primary", use_container_width=True)

    sc_status_slot = st.empty()
    if run_sc:
        if not script_topic.strip():
            st.warning("Please enter a video topic first.")
        elif not st.session_state.pro_unlocked and free_left <= 0:
            st.error(ui("limit_err", report_lang))
        else:
            sc_status_slot.markdown(f"<div class='loading-pill'>{ui('generating', report_lang)}</div>", unsafe_allow_html=True)
            target_script_lang = "Telugu (తెలుగు)" if report_lang == "Auto-Detect Video Language" else report_lang
            sc_prompt = f"""
You are an expert viral video scriptwriter for Indian creators.
Write a ready-to-shoot, word-for-word spoken script in **{target_script_lang}** (using its **NATIVE SCRIPT**) for a **{audience_scope}** audience.
- Topic: {script_topic.strip()}
- Format / Duration: {script_len}
- Tone: {script_tone}

STRICTLY INCLUDE (in {target_script_lang} native script):
### 🎣 1. 3 High-Retention Opening Hooks (First 5 Seconds — Word-for-Word)
### 🎬 2. Complete Scene-by-Scene Spoken Script + Visual/B-Roll Cues
### 📢 3. High-Converting Call to Action (Subscribe / Comment Prompt)
### 🎯 4. 3 Clickable Titles, Thumbnail Text & 10 Viral Hashtags
"""
            report_box = st.empty()
            full_text = ""
            try:
                for piece in generate_report_stream(sc_prompt):
                    full_text += piece
                    report_box.markdown(full_text)
                sc_status_slot.empty()
                st.session_state.script_report = full_text
                if not st.session_state.pro_unlocked:
                    increment_free_used(st.session_state.verified_email)
                log_usage_to_sheet(st.session_state.verified_email or "PRO", "ScriptGenerator", script_topic.strip()[:80])
                st.rerun()
            except Exception as e:
                sc_status_slot.empty()
                st.error(str(e))

    if st.session_state.script_report:
        st.success(ui("ready", report_lang))
        st.markdown(st.session_state.script_report)
        st.download_button(
            ui("download", report_lang),
            data=st.session_state.script_report,
            file_name="TrendSutra_Viral_Script.txt",
            mime="text/plain",
            key="dl_sc",
            use_container_width=True
        )

# === TAB 5: AI THUMBNAIL CHECKER ===
with tab_th:
    th1, th2, th3 = st.columns([2.6, 2.2, 1.6])
    with th1:
        thumb_file = st.file_uploader("Upload Thumbnail", type=["jpg", "jpeg", "png", "webp"], label_visibility="collapsed")
    with th2:
        thumb_title = st.text_input("Video Title (Optional)", placeholder="Optional: Enter Video Title for context...", label_visibility="collapsed")
    with th3:
        run_th = st.button(ui("gen_thumb_btn", report_lang), key="btn_th", type="primary", use_container_width=True)

    th_status_slot = st.empty()
    if thumb_file is not None:
        st.image(thumb_file, width=320)

    if run_th:
        if thumb_file is None:
            st.warning("Please upload a Thumbnail image (JPG/PNG) first.")
        elif not st.session_state.pro_unlocked and free_left <= 0:
            st.error(ui("limit_err", report_lang))
        else:
            th_status_slot.markdown(f"<div class='loading-pill'>{ui('generating', report_lang)}</div>", unsafe_allow_html=True)
            pil_img = Image.open(thumb_file)
            target_th_lang = "Telugu (తెలుగు)" if report_lang == "Auto-Detect Video Language" else report_lang
            th_prompt = f"""
You are a YouTube & Social Media Thumbnail CTR Optimization Expert.
Analyze this uploaded thumbnail image carefully and write a practical, actionable audit in **{target_th_lang}** (using its **NATIVE SCRIPT**) for a **{audience_scope}** audience.
Video Title Context: {thumb_title.strip() if thumb_title.strip() else "Not provided"}

STRICTLY INCLUDE (in {target_th_lang} native script):
### 📊 1. Estimated CTR Score (Out of 10) & First-Impression Verdict
### 🔍 2. Mobile Readability, Face/Emotion & Color Contrast Check
### 🛠️ 3. Top 3 Exact Changes to Double Clicks (CTR)
### ✍️ 4. 3 Punchy Thumbnail Text Alternatives (Max 3–4 Words Each)
"""
            report_box = st.empty()
            full_text = ""
            try:
                for piece in generate_report_stream([th_prompt, pil_img]):
                    full_text += piece
                    report_box.markdown(full_text)
                th_status_slot.empty()
                st.session_state.thumb_report = full_text
                if not st.session_state.pro_unlocked:
                    increment_free_used(st.session_state.verified_email)
                log_usage_to_sheet(st.session_state.verified_email or "PRO", "ThumbnailChecker", thumb_file.name)
                st.rerun()
            except Exception as e:
                th_status_slot.empty()
                st.error(str(e))

    if st.session_state.thumb_report:
        st.success(ui("ready", report_lang))
        st.markdown(st.session_state.thumb_report)
        st.download_button(
            ui("download", report_lang),
            data=st.session_state.thumb_report,
            file_name="TrendSutra_Thumbnail_Audit.txt",
            mime="text/plain",
            key="dl_th",
            use_container_width=True
        )
'''

with open("app.py", "w", encoding="utf-8") as f:
    f.write(code)

import py_compile
py_compile.compile("app.py", doraise=True)
print("Verified OK! Lines:", len(code.splitlines()))
