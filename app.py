import os
import base64
import streamlit as st
from google import genai
from google.genai import types
from googleapiclient.discovery import build
import re
import requests
import random
import smtplib
import time
from email.mime.text import MIMEText

# --- 1. PAGE CONFIG ---
st.set_page_config(
    page_title='TrendSutra AI - 1 AI • 1 India',
    page_icon='logo.png' if os.path.exists('logo.png') else 'IN',
    layout='wide',
    initial_sidebar_state='expanded'
)

# --- 2. LOAD SECRETS ---
GEMINI_KEY_1 = str(st.secrets.get('GEMINI_API_KEY', '')).strip()
GEMINI_KEY_2 = str(st.secrets.get('GEMINI_API_KEY_2', '')).strip()
GEMINI_KEY_3 = str(st.secrets.get('GEMINI_API_KEY_3', '')).strip()
GEMINI_KEY_4 = str(st.secrets.get('GEMINI_API_KEY_4', '')).strip()

YOUTUBE_KEY = str(st.secrets.get('YOUTUBE_API_KEY', '')).strip()
SHEET_API = str(st.secrets.get('GOOGLE_SHEET_API', '')).strip()
OWNER_CODE = str(st.secrets.get('OWNER_SECRET_CODE', '')).strip()
SENDER_EMAIL = str(st.secrets.get('SENDER_EMAIL', '')).strip()
SENDER_PASS = str(st.secrets.get('SENDER_APP_PASSWORD', '')).strip().replace(' ', '')

RAZORPAY_1M = 'https://rzp.io/rzp/70Y3L0K'
RAZORPAY_12M = 'https://rzp.io/rzp/77zX68U'

TEMP_DOMAINS = {
    'mailinator.com', 'tempmail.com', '10minutemail.com', 'guerrillamail.com',
    'yopmail.com', 'throwawaymail.com', 'fakeinbox.com', 'trashmail.com',
    'getnada.com', 'temp-mail.org', 'dispostable.com', 'maildrop.cc'
}

# --- 3. 22 INDIAN OFFICIAL LANGUAGES + BHOJPURI (A-Z) ---
LANGUAGES = [
    'Auto-Detect Video Language',
    'Assamese (অসমীয়া)',
    'Bengali (বাংলা)',
    'Bhojpuri (भोजपुरी)',
    "Bodo (बर')",
    'Dogri (डोगरी)',
    'English',
    'Gujarati (ગુજરાતી)',
    'Hindi (हिन्दी)',
    'Hinglish (Hindi + English)',
    'Kannada (ಕನ್ನಡ)',
    'Kashmiri (कॉशुर / كٲشُر)',
    'Konkani (कोंकणी)',
    'Maithili (मैथिली)',
    'Malayalam (മലയാളം)',
    'Manipuri (মৈতৈলোন্)',
    'Marathi (मराठी)',
    'Nepali (नेपाली)',
    'Odia (ଓଡ଼ିଆ)',
    'Punjabi (ਪੰਜਾਬੀ)',
    'Sanskrit (संस्कृतम्)',
    'Santali (ᱥᱟᱱᱛᱟᱲᱤ)',
    'Sindhi (सिन्धी / سنڌي)',
    'Tamil (தமிழ்)',
    'Telugu (తెలుగు)',
    'Tenglish (Telugu + English)',
    'Urdu (اردو)'
]

# --- 4. DYNAMIC REGIONAL UI TRANSLATIONS ---
UI_TEXT = {
    'English': {
        'free_left': 'Free Reports Left',
        'free_done': 'Free Trial Ended!',
        'gen_btn': 'Generate Growth Report',
        'fetching': 'Fetching video details & audience comments...',
        'generating': 'Generating report...',
        'ready': 'Growth Audit Report Ready!',
        'download': 'Download Complete Report (.txt)',
        'otp_sent': '6-digit OTP sent! Check Inbox / Spam.',
        'send_otp': 'Send OTP',
        'verify_otp': 'Verify OTP'
    },
    'Telugu': {
        'free_left': 'ఉచిత రిపోర్ట్‌లు మిగిలాయి',
        'free_done': '3 ఉచిత రిపోర్ట్‌లు పూర్తయ్యాయి!',
        'gen_btn': 'గ్రోత్ రిపోర్ట్ తయారు చేయండి',
        'fetching': 'వీడియో వివరాలు & కామెంట్లు సేకరిస్తోంది...',
        'generating': 'రిపోర్ట్ తయారవుతోంది...',
        'ready': 'గ్రోత్ ఆడిట్ రిపోర్ట్ సిద్ధమైంది!',
        'download': 'పూర్తి రిపోర్ట్ డౌన్‌లోడ్ చేయండి (.txt)',
        'otp_sent': '6-అంకెల OTP పంపబడింది! ఇన్‌బాక్స్ చెక్ చేయండి.',
        'send_otp': 'OTP పంపండి',
        'verify_otp': 'OTP నిర్ధారించండి'
    },
    'Hindi': {
        'free_left': 'मुफ्त रिपोर्ट बाकी हैं',
        'free_done': '3 मुफ्त रिपोर्ट पूरी हो गई हैं!',
        'gen_btn': 'ग्रोथ रिपोर्ट बनाएं',
        'fetching': 'वीडियो विवरण और कमेंट्स लिए जा रहे हैं...',
        'generating': 'रिपोर्ट तैयार हो रही है...',
        'ready': 'ग्रोथ ऑडिट रिपोर्ट तैयार है!',
        'download': 'पूरी रिपोर्ट डाउनलोड करें (.txt)',
        'otp_sent': '6-अंकों का OTP भेजा गया! इनबॉक्स जांचें।',
        'send_otp': 'OTP भेजें',
        'verify_otp': 'OTP सत्यापित करें'
    },
    'Tamil': {
        'free_left': 'இலவச அறிக்கைகள் உள்ளன',
        'free_done': '3 இலவச அறிக்கைகள் முடிந்துவிட்டன!',
        'gen_btn': 'வளர்ச்சி அறிக்கையை உருவாக்கு',
        'fetching': 'வீடியோ விவரங்கள் சேகரிக்கப்படுகின்றன...',
        'generating': 'அறிக்கை தயாராகிறது...',
        'ready': 'வளர்ச்சி அறிக்கை தயாராக உள்ளது!',
        'download': 'முழு அறிக்கையை பதிவிறக்கவும் (.txt)',
        'otp_sent': '6-இலக்க OTP அனுப்பப்பட்டது!',
        'send_otp': 'OTP அனுப்பு',
        'verify_otp': 'OTP சரிபார்'
    },
    'Kannada': {
        'free_left': 'ಉಚಿತ ವರದಿಗಳು ಉಳಿದಿವೆ',
        'free_done': '3 ಉಚಿತ ವರದಿಗಳು ಪೂರ್ಣಗೊಂಡಿವೆ!',
        'gen_btn': 'ಗ್ರೋತ್ ವರದಿ ತಯಾರಿಸಿ',
        'fetching': 'ವೀಡಿಯೊ ವಿವರಗಳನ್ನು ಸಂಗ್ರಹಿಸಲಾಗುತ್ತಿದೆ...',
        'generating': 'ವರದಿ ಸಿದ್ಧವಾಗುತ್ತಿದೆ...',
        'ready': 'ಗ್ರೋತ್ ಆಡಿಟ್ ವರದಿ ಸಿದ್ಧವಾಗಿದೆ!',
        'download': 'ಪೂರ್ಣ ವರದಿ ಡೌನ್‌ಲೋಡ್ ಮಾಡಿ (.txt)',
        'otp_sent': '6-ಅಂಕಿಯ OTP ಕಳುಹಿಸಲಾಗಿದೆ!',
        'send_otp': 'OTP ಕಳುಹಿಸಿ',
        'verify_otp': 'OTP ದೃಢೀಕರಿಸಿ'
    },
    'Malayalam': {
        'free_left': 'സൗജന്യ റിപ്പോർട്ടുകൾ ബാക്കിയുണ്ട്',
        'free_done': '3 സൗജന്യ റിപ്പോർട്ടുകൾ പൂർത്തിയായി!',
        'gen_btn': 'ഗ്രോത്ത് റിപ്പോർട്ട് തയ്യാറാക്കുക',
        'fetching': 'വീഡിയോ വിവരങ്ങൾ ശേഖരിക്കുന്നു...',
        'generating': 'റിപ്പോർട്ട് തയ്യാറാകുന്നു...',
        'ready': 'ഗ്രോത്ത് ഓഡിറ്റ് റിപ്പോർട്ട് തയ്യാറായി!',
        'download': 'പൂർണ്ണ റിപ്പോർട്ട് ഡൗൺലോഡ് ചെയ്യുക (.txt)',
        'otp_sent': '6-അക്ക OTP അയച്ചു!',
        'send_otp': 'OTP അയക്കുക',
        'verify_otp': 'OTP സ്ഥിരീകരിക്കുക'
    },
    'Marathi': {
        'free_left': 'मोफत रिपोर्ट शिल्लक आहेत',
        'free_done': '3 मोफत रिपोर्ट पूर्ण झाले आहेत!',
        'gen_btn': 'ग्रोथ रिपोर्ट तयार करा',
        'fetching': 'व्हिडिओ माहिती गोळा करत आहे...',
        'generating': 'रिपोर्ट तयार होत आहे...',
        'ready': 'ग्रोथ ऑडिट रिपोर्ट तयार आहे!',
        'download': 'पूर्ण रिपोर्ट डाउनलोड करा (.txt)',
        'otp_sent': '6-अंकी OTP पाठवला आहे!',
        'send_otp': 'OTP पाठवा',
        'verify_otp': 'OTP तपासा'
    },
    'Bengali': {
        'free_left': 'ফ্রি রিপোর্ট বাকি আছে',
        'free_done': '৩টি ফ্রি রিপোর্ট শেষ হয়েছে!',
        'gen_btn': 'গ্রোথ রিপোর্ট তৈরি করুন',
        'fetching': 'ভিডিওর তথ্য সংগ্রহ করা হচ্ছে...',
        'generating': 'রিপোর্ট তৈরি হচ্ছে...',
        'ready': 'গ্রোথ অডিট রিপোর্ট প্রস্তুত!',
        'download': 'সম্পূর্ণ রিপোর্ট ডাউনলোড করুন (.txt)',
        'otp_sent': '৬-সংখ্যার OTP পাঠানো হয়েছে!',
        'send_otp': 'OTP পাঠান',
        'verify_otp': 'OTP যাচাই করুন'
    },
    'Gujarati': {
        'free_left': 'મફત રિપોર્ટ બાકી છે',
        'free_done': '3 મફત રિપોર્ટ પૂરા થઈ ગયા છે!',
        'gen_btn': 'ગ્રોથ રિપોર્ટ બનાવો',
        'fetching': 'વીડિયોની વિગતો લેવામાં આવી રહી છે...',
        'generating': 'રિપોર્ટ તૈયાર થઈ રહ્યો છે...',
        'ready': 'ગ્રોથ ઓડિટ રિપોર્ટ તૈયાર છે!',
        'download': 'સંપૂર્ણ રિપોર્ટ ડાઉનલોડ કરો (.txt)',
        'otp_sent': '6-અંકનો OTP મોકલવામાં આવ્યો છે!',
        'send_otp': 'OTP મોકલો',
        'verify_otp': 'OTP ચકાસો'
    },
    'Punjabi': {
        'free_left': 'ਮੁਫ਼ਤ ਰਿਪੋਰਟਾਂ ਬਾਕੀ ਹਨ',
        'free_done': '3 ਮੁਫ਼ਤ ਰਿਪੋਰਟਾਂ ਪੂਰੀਆਂ ਹੋ ਗਈਆਂ ਹਨ!',
        'gen_btn': 'ਗ੍ਰੋਥ ਰਿਪੋਰਟ ਬਣਾਓ',
        'fetching': 'ਵੀਡੀਓ ਵੇਰਵੇ ਇਕੱਠੇ ਕੀਤੇ ਜਾ ਰਹੇ ਹਨ...',
        'generating': 'ਰਿਪੋਰਟ ਤਿਆਰ ਹੋ ਰਹੀ ਹੈ...',
        'ready': 'ਗ੍ਰੋਥ ਆਡਿਟ ਰਿਪੋਰਟ ਤਿਆਰ ਹੈ!',
        'download': 'ਪੂਰੀ ਰਿਪੋਰਟ ਡਾਊਨਲੋਡ ਕਰੋ (.txt)',
        'otp_sent': '6-ਅੰਕਾਂ ਦਾ OTP ਭੇਜਿਆ ਗਿਆ ਹੈ!',
        'send_otp': 'OTP ਭੇਜੋ',
        'verify_otp': 'OTP ਪੁਸ਼ਟੀ ਕਰੋ'
    },
    'Odia': {
        'free_left': 'ମାଗଣା ରିପୋର୍ଟ ବାକି ଅଛି',
        'free_done': '୩ଟି ମାଗଣା ରିପୋର୍ଟ ଶେଷ ହୋଇଛି!',
        'gen_btn': 'ଗ୍ରୋଥ୍ ରିପୋର୍ଟ ତିଆରି କରନ୍ତୁ',
        'fetching': 'ଭିଡିଓ ତଥ୍ୟ ସଂଗ୍ରହ କରାଯାଉଛି...',
        'generating': 'ରିପୋର୍ଟ ପ୍ରସ୍ତୁତ ହେଉଛି...',
        'ready': 'ଗ୍ରୋଥ୍ ଅଡିଟ୍ ରିପୋର୍ଟ ପ୍ରସ୍ତୁତ!',
        'download': 'ସମ୍ପୂର୍ଣ୍ଣ ରିପୋର୍ଟ ଡାଉନଲୋଡ୍ କରନ୍ତୁ (.txt)',
        'otp_sent': '୬-ଅଙ୍କ ବିଶିଷ୍ଟ OTP ପଠାଯାଇଛି!',
        'send_otp': 'OTP ପଠାନ୍ତୁ',
        'verify_otp': 'OTP ଯାଞ୍ଚ କରନ୍ତୁ'
    },
    'Assamese': {
        'free_left': 'বিনামূলীয়া ৰিপৰ্ট বাকী আছে',
        'free_done': '৩টা বিনামূলীয়া ৰিপৰ্ট সম্পূৰ্ণ হৈছে!',
        'gen_btn': 'গ্ৰোথ ৰিপৰ্ট তৈয়াৰ কৰক',
        'fetching': 'ভিডিঅৰ তথ্য সংগ্ৰহ কৰা হৈছে...', 
        'generating': 'ৰিপৰ্ট প্ৰস্তুত হৈ আছে...',
        'ready': 'গ্ৰোথ অডিট ৰিপৰ্ট সাজু!',
        'download': 'সম্পূৰ্ণ ৰিপৰ্ট ডাউনলোড কৰক (.txt)',
        'otp_sent': '৬-সংখ্যাৰ OTP পঠিওৱা হৈছে!',
        'send_otp': 'OTP পঠিয়াওক',
        'verify_otp': 'OTP নিশ্চিত কৰক'
    },
    'Urdu': {
        'free_left': 'مفت رپورٹس باقی ہیں',
        'free_done': '3 مفت رپورٹس مکمل ہو گئی ہیں!',
        'gen_btn': 'گروتھ رپورٹ بنائیں',
        'fetching': 'ویڈیو کی تفصیلات حاصل کی جا رہی ہیں...',
        'generating': 'رپورٹ تیار ہو رہی ہے...',
        'ready': 'گروتھ آڈٹ رپورٹ تیار ہے!',
        'download': 'مکمل رپورٹ ڈاؤن لوڈ کریں (.txt)',
        'otp_sent': '6 ہندسوں کا OTP بھیج دیا گیا ہے!',
        'send_otp': 'OTP بھیجیں',
        'verify_otp': 'OTP کی تصدیق کریں'
    },
    'Bhojpuri': {
        'free_left': 'फ्री रिपोर्ट बाचल बा',
        'free_done': '3 गो फ्री रिपोर्ट पूरा हो गइल!',
        'gen_btn': 'ग्रोथ रिपोर्ट बनाईं',
        'fetching': 'वीडियो के जानकारी जुटावल जाता...',
        'generating': 'रिपोर्ट तैयार हो रहल बा...',
        'ready': 'ग्रोथ ऑडिट रिपोर्ट तैयार बा!',
        'download': 'पूरा रिपोर्ट डाउनलोड करीं (.txt)',
        'otp_sent': '6-अंक के OTP भेज दिहल गइल बा!',
        'send_otp': 'OTP भेजीं',
        'verify_otp': 'OTP सत्यापित करीं'
    }
}

def get_ui(selected_lang, detected_lang=''):
    target = detected_lang if (selected_lang.startswith('Auto-Detect') and detected_lang) else selected_lang
    for k in UI_TEXT:
        if k.lower() in target.lower():
            return UI_TEXT[k]
    return UI_TEXT['English']

# --- 5. CUSTOM CSS ---
st.markdown('''
<style>
    [data-testid='stToolbarActions'], #MainMenu, footer, .stDeployButton {
        display: none !important;
        visibility: hidden !important;
    }
    [data-testid='stSidebarCollapsedControl'] {
        display: flex !important;
        visibility: visible !important;
        z-index: 99999 !important;
    }
    .block-container {
        padding-top: 0.7rem !important;
        padding-bottom: 0.8rem !important;
        max-width: 1220px !important;
    }
    section[data-testid='stSidebar'] > div {
        padding-top: 0.6rem !important;
        padding-bottom: 0.4rem !important;
    }
    section[data-testid='stSidebar'] .stMarkdown p {
        margin-bottom: 0.25rem !important;
        font-size: 0.88rem !important;
    }
    section[data-testid='stSidebar'] hr {
        margin: 0.45rem 0 !important;
    }
    .center-hero {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        border: 1px solid #334155;
        border-bottom: 3px solid #10b981;
        border-radius: 14px;
        padding: 14px 20px;
        text-align: center;
        margin-bottom: 10px;
    }
    .hero-title-row {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        gap: 12px;
    }
    .hero-title-row h1 {
        margin: 0 !important;
        padding: 0 !important;
        font-size: 1.95rem !important;
        font-weight: 800 !important;
        color: #ffffff !important;
        letter-spacing: -0.5px;
    }
    .hero-sub {
        margin: 4px 0 0 0 !important;
        color: #cbd5e1 !important;
        font-size: 0.96rem !important;
    }
    .india-badge {
        display: inline-block;
        margin-top: 6px;
        background: rgba(16, 185, 129, 0.16);
        border: 1px solid #10b981;
        color: #6ee7b7;
        padding: 2px 12px;
        border-radius: 20px;
        font-size: 0.78rem;
        font-weight: 600;
    }
    .login-strip {
        background: #1e293b;
        border: 1px solid #334155;
        border-radius: 10px;
        padding: 10px 14px;
        margin-bottom: 10px;
    }
    .stTextInput > div > div > input {
        height: 42px !important;
    }
    .stButton > button {
        height: 42px !important;
        font-weight: 600 !important;
        border-radius: 8px !important;
    }
    .loading-pill {
        background: #ecfdf5;
        border: 1.5px solid #10b981;
        color: #065f46;
        height: 42px;
        padding: 0 14px;
        border-radius: 8px;
        font-weight: 600;
        font-size: 0.9rem;
        display: flex;
        align-items: center;
        justify-content: center;
    }
</style>
''', unsafe_allow_html=True)

# --- 6. SESSION STATE ---
if 'verified_email' not in st.session_state:
    st.session_state.verified_email = ''
if 'otp_code' not in st.session_state:
    st.session_state.otp_code = ''
if 'otp_target' not in st.session_state:
    st.session_state.otp_target = ''
if 'pro_unlocked' not in st.session_state:
    st.session_state.pro_unlocked = False
if 'pro_label' not in st.session_state:
    st.session_state.pro_label = ''
if 'yt_report' not in st.session_state:
    st.session_state.yt_report = ''
if 'yt_vid_id' not in st.session_state:
    st.session_state.yt_vid_id = ''
if 'yt_metrics' not in st.session_state:
    st.session_state.yt_metrics = None
if 'ig_report' not in st.session_state:
    st.session_state.ig_report = ''
if 'tt_report' not in st.session_state:
    st.session_state.tt_report = ''
if 'detected_lang' not in st.session_state:
    st.session_state.detected_lang = ''
if 'exhausted_keys' not in st.session_state:
    st.session_state.exhausted_keys = set()

# --- 7. CHECK GOOGLE OAUTH LOGIN ---
try:
    if hasattr(st, 'user') and getattr(st.user, 'is_logged_in', False):
        g_email = getattr(st.user, 'email', '')
        if g_email:
            st.session_state.verified_email = g_email.strip().lower()
except Exception:
    pass

# --- 8. GOOGLE SHEET HELPERS (LIVE NO-CACHE SYNC) ---
def get_free_used_count(user_id):
    if not SHEET_API or not user_id:
        return 0
    try:
        r = requests.get(
            SHEET_API,
            params={'device': user_id.strip().lower(), '_ts': str(time.time())},
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
        return False
    clean_id = user_id.strip().lower()
    for _ in range(2):
        try:
            r = requests.get(
                SHEET_API,
                params={'device': clean_id, 'inc': '1', '_ts': str(time.time())},
                timeout=10,
                allow_redirects=True
            )
            if r.status_code == 200 and r.text.strip().isdigit():
                return True
        except Exception:
            time.sleep(0.3)
    return False

def log_usage_to_sheet(user_id, platform, url):
    if not SHEET_API:
        return
    try:
        requests.get(
            SHEET_API,
            params={
                'log': '1',
                'device': (user_id or 'GUEST').strip().lower(),
                'platform': platform,
                'url': url,
                '_ts': str(time.time())
            },
            timeout=8,
            allow_redirects=True
        )
    except Exception:
        pass

def verify_payment_id(pid, plan='1m'):
    pid = pid.strip()
    if OWNER_CODE and pid == OWNER_CODE:
        return 'OWNER'
    if not pid.startswith('pay_') or len(pid) < 10:
        return 'INVALID'
    if not SHEET_API:
        return 'VALID'
    try:
        r = requests.get(
            SHEET_API,
            params={'pid': pid, 'plan': plan, '_ts': str(time.time())},
            timeout=10,
            allow_redirects=True
        )
        if r.status_code == 200:
            res = r.text.strip().upper()
            if res in ['VALID', 'ALREADY_USED', 'EXPIRED', 'INVALID']:
                return res
    except Exception:
        pass
    return 'ERROR'

# --- 9. AUTO-UNLOCK FROM RAZORPAY REDIRECT ---
qp = st.query_params
if 'razorpay_payment_id' in qp and not st.session_state.pro_unlocked:
    auto_pid = str(qp['razorpay_payment_id']).strip()
    if auto_pid.startswith('pay_'):
        st_res = verify_payment_id(auto_pid, plan='1m')
        if st_res == 'VALID':
            st.session_state.pro_unlocked = True
            st.session_state.pro_label = 'PRO UNLIMITED ACTIVE'
            st.query_params.clear()
            st.rerun()

def send_otp_email(to_email, code):
    if not SENDER_EMAIL or not SENDER_PASS:
        return False, 'SMTP not configured'
    try:
        body_txt = (
            f'Welcome to TrendSutra AI!\n\n'
            f'Your 6-digit verification code is: {code}\n\n'
            f'Enter this code on TrendSutra AI to unlock your 3 Free Growth Reports.'
        )
        msg = MIMEText(body_txt)
        msg['Subject'] = f'{code} is your TrendSutra AI Verification Code'
        msg['From'] = f'TrendSutra AI <{SENDER_EMAIL}>'
        msg['To'] = to_email
        with smtplib.SMTP_SSL('smtp.gmail.com', 465, timeout=12) as server:
            server.login(SENDER_EMAIL, SENDER_PASS)
            server.sendmail(SENDER_EMAIL, [to_email], msg.as_string())
        return True, 'SENT'
    except Exception as e:
        return False, str(e)

# --- 10. YOUTUBE DATA FETCHER ---
def extract_youtube_id(url):
    patterns = [
        r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
        r'youtu\.be\/([0-9A-Za-z_-]{11})',
        r'shorts\/([0-9A-Za-z_-]{11})'
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
        yt = build('youtube', 'v3', developerKey=YOUTUBE_KEY)
        v_res = yt.videos().list(part='snippet,statistics', id=video_id).execute()
        if not v_res.get('items'):
            return None
        item = v_res['items'][0]
        snip = item['snippet']
        stats = item.get('statistics', {})
        comments = []
        try:
            c_res = yt.commentThreads().list(
                part='snippet', videoId=video_id, maxResults=20, order='relevance', textFormat='plainText'
            ).execute()
            for c in c_res.get('items', []):
                top = c['snippet']['topLevelComment']['snippet']
                author = top.get('authorDisplayName', 'Viewer')
                text = top.get('textDisplay', '').strip().replace('\n', ' ')
                if text:
                    comments.append(f'{author}: {text[:200]}')
        except Exception:
            pass
        return {
            'title': snip.get('title', ''),
            'channel': snip.get('channelTitle', ''),
            'default_audio_lang': snip.get('defaultAudioLanguage', '') or snip.get('defaultLanguage', ''),
            'description': snip.get('description', '')[:1000],
            'tags': snip.get('tags', [])[:15],
            'views': int(stats.get('viewCount', 0)),
            'likes': int(stats.get('likeCount', 0)),
            'comment_count': int(stats.get('commentCount', 0)),
            'comments': comments
        }
    except Exception:
        return None

# --- 11. 4-KEY SMART FAILOVER + SESSION MEMORY (FAST FREE FIRST -> PAID) ---
def get_ordered_api_keys():
    candidates = [
        ('KEY_4', GEMINI_KEY_4),
        ('KEY_3', GEMINI_KEY_3),
        ('KEY_2', GEMINI_KEY_2),
        ('KEY_1_PAID', GEMINI_KEY_1)
    ]
    active = []
    paid_fallback = None
    for label, k in candidates:
        if k and len(k) > 10:
            if label == 'KEY_1_PAID':
                paid_fallback = (label, k)
            elif label not in st.session_state.exhausted_keys:
                active.append((label, k))
    if paid_fallback:
        active.append(paid_fallback)
    return active

def generate_report_stream(prompt):
    api_keys = get_ordered_api_keys()
    if not api_keys:
        raise RuntimeError('API Key missing in Streamlit Secrets.')

    fast_models = ['gemini-2.5-flash-lite', 'gemini-2.5-flash']
    last_err = ''

    for key_label, api_key in api_keys:
        try:
            client = genai.Client(api_key=api_key)
        except Exception:
            continue

        for model_name in fast_models:
            try:
                response = client.models.generate_content_stream(
                    model=model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.80,
                        max_output_tokens=7000
                    )
                )
                yielded_any = False
                for chunk in response:
                    if chunk.text:
                        yielded_any = True
                        clean_txt = chunk.text.replace('మెంటర్', 'సలహాదారు').replace('స్ట్రాటజిస్ట్', 'సలహాదారు')
                        yield clean_txt
                if yielded_any:
                    return
            except Exception as e:
                last_err = str(e)
                err_low = last_err.lower()
                if key_label != 'KEY_1_PAID' and ('429' in err_low or 'quota' in err_low or 'resource_exhausted' in err_low):
                    st.session_state.exhausted_keys.add(key_label)
                    break
                continue

    raise RuntimeError(f'AI server is busy. Please try again in 5 seconds. ({last_err})')

# --- 12. SIDEBAR ---
with st.sidebar:
    st.markdown('### ⚙️ Settings')
    report_lang = st.selectbox(
        '🔍 Search Language (A–Z):',
        LANGUAGES,
        index=0
    )
    audience_scope = st.radio('Audience:', ['Regional', 'Global', 'Both'], horizontal=True)

    st.divider()
    st.markdown('### 💎 Pro Plans')

    free_used = get_free_used_count(st.session_state.verified_email) if st.session_state.verified_email else 0
    free_left = max(0, 3 - free_used)
    ui = get_ui(report_lang, st.session_state.detected_lang)

    if st.session_state.pro_unlocked:
        st.success(f'✅ {st.session_state.pro_label}')
    elif st.session_state.verified_email:
        if free_left > 0:
            st.info(f"🎁 **{free_left}/3 {ui['free_left']}**")
        else:
            st.error(f"🔒 {ui['free_done']}")
    else:
        st.info('🎁 Login for **3 Free Reports**')

    st.markdown(f'• **1 Month:** ₹100 👉 [Pay ₹100]({RAZORPAY_1M}) • **12 Months:** ₹1,000 👉 [Pay ₹1,000]({RAZORPAY_12M})')

    plan_choice = st.radio('Plan:', ['1M (₹100)', '12M (₹1,000)'], horizontal=True, label_visibility='collapsed')
    pay_input = st.text_input('Payment ID:', placeholder='Paste Payment ID (pay_...)', label_visibility='collapsed')
    if st.button('Unlock Pro 🔓', use_container_width=True):
        if not pay_input.strip():
            st.warning('Enter Payment ID.')
        else:
            p_code = '12m' if '12' in plan_choice else '1m'
            status = verify_payment_id(pay_input, plan=p_code)
            if status == 'OWNER':
                st.session_state.pro_unlocked = True
                st.session_state.pro_label = 'OWNER UNLIMITED'
                st.rerun()
            elif status == 'VALID':
                st.session_state.pro_unlocked = True
                st.session_state.pro_label = f'PRO ({plan_choice})'
                st.rerun()
            elif status == 'EXPIRED':
                st.error('⏰ Plan Expired! Please renew.')
            elif status == 'ALREADY_USED':
                st.error('❌ Used on 3 devices already.')
            else:
                st.error('❌ Invalid Payment ID.')

    st.divider()
    st.caption('📩 support@aiengtel.com | © 2026 TrendSutra AI')

# --- 13. CENTERED HERO HEADER ---
logo_html = ''
if os.path.exists('logo.png'):
    with open('logo.png', 'rb') as f:
        b64_logo = base64.b64encode(f.read()).decode()
    logo_html = f'<img src="data:image/png;base64,{b64_logo}" style="height:44px; width:44px; border-radius:10px; object-fit:contain;" />'

st.markdown(f'''
<div class='center-hero'>
    <div class='hero-title-row'>
        {logo_html}
        <h1>TrendSutra AI</h1>
    </div>
    <p class='hero-sub'>A to Z Growth Analyzer for YouTube, Instagram & TikTok Creators</p>
    <span class='india-badge'>🇮🇳 1 AI • 1 India — Supports All 22 Indian Official Languages + Bhojpuri</span>
</div>
''', unsafe_allow_html=True)

# --- 14. SINGLE-ROW LOGIN BAR ---
if not st.session_state.verified_email and not st.session_state.pro_unlocked:
    st.markdown('<div class="login-strip">', unsafe_allow_html=True)
    lc1, lc2, lc3, lc4 = st.columns([2.2, 0.4, 2.3, 1.3], vertical_alignment='center')
    with lc1:
        if st.button('Continue with Gmail', type='primary', use_container_width=True):
            try:
                st.login('google')
            except Exception as e:
                st.error(f'Google Login error: {e}')
    with lc2:
        st.markdown("<div style='text-align:center; color:#94a3b8; font-weight:700;'>OR</div>", unsafe_allow_html=True)
    with lc3:
        email_in = st.text_input('Login with Mail ID', placeholder='Login with Mail ID (e.g. creator@gmail.com)', label_visibility='collapsed')
    with lc4:
        send_otp_clicked = st.button(f"{ui['send_otp']} 📩", use_container_width=True)

    if send_otp_clicked:
        clean_em = email_in.strip().lower()
        if '@' not in clean_em or '.' not in clean_em.split('@')[-1]:
            st.error('❌ Enter a valid Mail ID.')
        elif clean_em.split('@')[-1] in TEMP_DOMAINS:
            st.error('❌ Temporary emails are not allowed.')
        else:
            code = str(random.randint(100000, 999999))
            ok, err_msg = send_otp_email(clean_em, code)
            if ok:
                st.session_state.otp_code = code
                st.session_state.otp_target = clean_em
                st.success(f"✅ {clean_em} — {ui['otp_sent']}")
            else:
                st.error(f'OTP Error: {err_msg}')

    if st.session_state.otp_target:
        oc1, oc2 = st.columns([3, 1.5], vertical_alignment='center')
        with oc1:
            otp_in = st.text_input('Enter 6-digit OTP:', placeholder=f'Enter 6-digit OTP sent to {st.session_state.otp_target}', max_chars=6, label_visibility='collapsed')
        with oc2:
            if st.button(f"{ui['verify_otp']} ✅", type='primary', use_container_width=True):
                if otp_in.strip() == st.session_state.otp_code:
                    st.session_state.verified_email = st.session_state.otp_target
                    st.session_state.otp_code = ''
                    st.rerun()
                else:
                    st.error('❌ Wrong OTP!')
    st.markdown('</div>', unsafe_allow_html=True)
else:
    uc1, uc2 = st.columns([4.5, 1], vertical_alignment='center')
    with uc1:
        who = st.session_state.verified_email if st.session_state.verified_email else 'PRO Member'
        badge = f'✅ {st.session_state.pro_label}' if st.session_state.pro_unlocked else f"🎁 {free_left}/3 {ui['free_left']}"
        st.markdown(f"<div style='padding:6px 12px; background:#1e293b; border-radius:8px; border:1px solid #334155; font-size:0.9rem;'>👤 Logged in as <b>{who}</b> &nbsp;|&nbsp; {badge}</div>", unsafe_allow_html=True)
    with uc2:
        if st.button('Logout', use_container_width=True):
            st.session_state.verified_email = ''
            st.session_state.pro_unlocked = False
            st.session_state.yt_report = ''
            st.session_state.detected_lang = ''
            try:
                if hasattr(st, 'logout'):
                    st.logout()
            except Exception:
                pass
            st.rerun()

# --- 15. HELPER FOR LANGUAGE INSTRUCTION ---
def build_lang_instruction(selected_lang):
    if selected_lang.startswith('Auto-Detect'):
        return '''
LANGUAGE & NATIVE SCRIPT RULE (CRITICAL):
- Automatically detect the primary language of the video from its Title, Description, Audio Language tag, and Audience Comments.
- Start the very first line of your output with: **🌐 Detected Video Language: [Language Name]**
- Write the ENTIRE report (including all 6 section headings and all body text) in that detected language's **NATIVE SCRIPT** (e.g., Telugu in తెలుగు లిపి, Tamil in தமிழ் எழுத்து, Hindi in देवनागरी, Kannada in ಕನ್ನಡ, Malayalam in മലയാളം, Urdu in اردو رسم الخط, Bengali in বাংলা, Marathi in देवनागरी, Gujarati in ગુજરાતી, Punjabi in ਗੁਰਮੁਖੀ, Odia in ଓଡ଼ିଆ, Assamese in অসমীয়া, Bhojpuri in देवनागरी).
- Do NOT transliterate Indian languages into English/Roman letters unless the video itself is in English.
'''
    else:
        return f'''
LANGUAGE & NATIVE SCRIPT RULE (CRITICAL):
- Write the ENTIRE report (including all 6 section headings and all body text) in **{selected_lang}** using its authentic **NATIVE SCRIPT** (for example: Telugu in తెలుగు, Tamil in தமிழ், Hindi in हिन्दी, Urdu in اردو, Bengali in বাংলা, Kannada in ಕನ್ನಡ, Malayalam in മലയാളം, etc.).
- Do NOT write Indian languages in Roman/English letters (unless Hinglish or Tenglish was explicitly chosen).
'''

def extract_detected_lang_from_text(text):
    m = re.search(r'Detected Video Language:\s*([A-Za-z]+)', text)
    if m:
        return m.group(1).strip()
    return ''

# --- 16. MAIN WORKSPACE TABS ---
tab_yt, tab_ig, tab_tt = st.tabs(['📺 YouTube Analyzer', '📸 Instagram Reels Analyzer', '🎵 TikTok Analyzer'])

with tab_yt:
    yc1, yc2, yc3 = st.columns([3.3, 1.4, 1.3], vertical_alignment='center')
    with yc1:
        yt_url = st.text_input('YouTube URL', placeholder='Paste YouTube Video or Shorts Link...', label_visibility='collapsed')
    with yc2:
        run_yt = st.button(f"{ui['gen_btn']} 🔍", key='btn_yt', type='primary', use_container_width=True)
    with yc3:
        yt_status_slot = st.empty()

    if run_yt:
        if not st.session_state.verified_email and not st.session_state.pro_unlocked:
            st.warning('Please login above with Gmail or Mail ID to get your 3 Free Reports.')
        elif not yt_url.strip():
            st.warning('Please paste a YouTube video or Shorts link.')
        elif not st.session_state.pro_unlocked and free_left <= 0:
            st.error(f"🔒 {ui['free_done']}")
        else:
            vid_id = extract_youtube_id(yt_url.strip())
            if not vid_id:
                st.error('❌ Invalid YouTube link.')
            else:
                yt_status_slot.markdown(f"<div class='loading-pill'>🔄 {ui['fetching']} ⏳</div>", unsafe_allow_html=True)
                data = fetch_youtube_details(vid_id)
                if not data:
                    yt_status_slot.empty()
                    st.error('❌ Could not fetch video details. Make sure the video is Public.')
                else:
                    st.session_state.yt_vid_id = vid_id
                    st.session_state.yt_metrics = (data['views'], data['likes'], data['comment_count'])
                    comments_block = '\n'.join(data['comments'][:15]) if data['comments'] else 'No public comments available.'
                    lang_rule = build_lang_instruction(report_lang)
                    prompt = (
                        f'You are a warm, encouraging, expert human social media growth advisor ("సలహాదారు").\n'
                        f'Write a comprehensive, deeply detailed, easy-to-understand growth audit report (1,000 to 1,400 words) for a **{audience_scope}** audience.\n'
                        f'Use simple everyday spoken words (never use complex bookish words, and NEVER use the word మెంటర్—use సలహాదారు if Telugu).\n\n'
                        f'{lang_rule}\n\n'
                        f"VIDEO DATA:\n- Channel: {data['channel']}\n- Title: {data['title']}\n- Audio/Default Language Tag: {data['default_audio_lang']}\n"
                        f"- Views: {data['views']:,} | Likes: {data['likes']:,} | Comments: {data['comment_count']:,}\n"
                        f"- Description: {data['description']}\n- Tags: {', '.join(data['tags'])}\n- Real Audience Comments:\n{comments_block}\n\n"
                        'STRICTLY FOLLOW THIS 6-SECTION STRUCTURE (Translate all 6 section titles into the target language native script):\n'
                        '### 🎬 1. Video Story Recap & Creator Appreciation\n- Warmly retell the core story/message of this video based on its title, description, and comments so the creator feels you truly understood their hard work.\n- Genuinely praise the creator effort, topic choice, and presentation strengths.\n\n'
                        '### 💬 2. Real Audience Comments & Reply Templates\n- Pick 4 to 5 real viewer comments from the list above, translate them naturally into the target language native script, quote them with the viewer name, explain what viewers love or ask for, and give 3 ready-to-copy reply templates.\n\n'
                        '### 🔥 3. 3 Next Viral Video Ideas + 5-Second Hooks\n- Give 3 fresh, high-potential follow-up video ideas tailored to this channel. For each idea, write an exact word-for-word **5-second opening Hook** and a **Thumbnail visual idea**.\n\n'
                        '### 🎯 4. Copy-Paste SEO Makeover (Titles, Description & 15 Tags)\n- Provide 3 clickable high-CTR title options, a strong 3-line SEO description hook, and 15 searchable comma-separated tags.\n\n'
                        '### 💰 5. Monetization & Brand Earning Blueprint\n- Explain 3 practical ways this specific channel can earn money (AdSense, Affiliate links, Brand sponsorships) with realistic examples.\n\n'
                        '### 📅 6. Step-by-Step 30-Day Action Plan\n- Give a clear Week 1 to Week 4 checklist of simple daily/weekly actions to double views and subscribers.\n'
                    )
                    yt_status_slot.markdown(f"<div class='loading-pill'>⚡ {ui['generating']} ⏳</div>", unsafe_allow_html=True)
                    report_box = st.empty()
                    full_text = ''
                    try:
                        for piece in generate_report_stream(prompt):
                            full_text += piece
                            report_box.markdown(full_text)
                        yt_status_slot.empty()
                        st.session_state.yt_report = full_text
                        det = extract_detected_lang_from_text(full_text)
                        if det:
                            st.session_state.detected_lang = det
                        if not st.session_state.pro_unlocked:
                            increment_free_used(st.session_state.verified_email)
                        log_usage_to_sheet(st.session_state.verified_email or 'PRO', 'YouTube', yt_url.strip())
                        st.rerun()
                    except Exception as e:
                        yt_status_slot.empty()
                        st.error(str(e))

    if st.session_state.yt_report:
        if st.session_state.yt_metrics:
            v, l, c = st.session_state.yt_metrics
            m1, m2, m3 = st.columns(3)
            m1.metric('👀 Views', f'{v:,}')
            m2.metric('👍 Likes', f'{l:,}')
            m3.metric('💬 Comments', f'{c:,}')
        st.success(f"✅ {ui['ready']}")
        st.download_button(
            f"📥 {ui['download']}",
            data=st.session_state.yt_report,
            file_name=f"TrendSutra_YouTube_Report_{st.session_state.yt_vid_id or 'Audit'}.txt",
            mime='text/plain',
            use_container_width=True
        )
        st.markdown('---')
        st.markdown(st.session_state.yt_report)

with tab_ig:
    ic1, ic2, ic3 = st.columns([3.3, 1.4, 1.3], vertical_alignment='center')
    with ic1:
        ig_url = st.text_input('Instagram URL', placeholder='Paste Instagram Reel Link...', label_visibility='collapsed')
    with ic2:
        run_ig = st.button(f"{ui['gen_btn']} 🔍", key='btn_ig', type='primary', use_container_width=True)
    with ic3:
        ig_status_slot = st.empty()

    if run_ig:
        if not st.session_state.verified_email and not st.session_state.pro_unlocked:
            st.warning('Please login above with Gmail or Mail ID to get your 3 Free Reports.')
        elif not ig_url.strip():
            st.warning('Please paste an Instagram Reel link.')
        elif not st.session_state.pro_unlocked and free_left <= 0:
            st.error(f"🔒 {ui['free_done']}")
        else:
            ig_status_slot.markdown(f"<div class='loading-pill'>⚡ {ui['generating']} ⏳</div>", unsafe_allow_html=True)
            lang_rule = build_lang_instruction(report_lang)
            ig_prompt = (
                f'You are a warm, encouraging human Instagram Reels growth advisor ("సలహాదారు").\n'
                f'Write a detailed 6-section Instagram Reels growth audit (1,000+ words) for a **{audience_scope}** audience using simple spoken words.\n'
                f'{lang_rule}\nReel Link: {ig_url.strip()}\n'
                'Include 6 sections (headings translated into target native script):\n'
                '1. Creator Appreciation & Reel Strategy Overview\n2. Watch-Time, Audio & Retention Hook Analysis\n'
                '3. 3 Viral Follow-Up Reel Ideas with word-for-word 3-second Hooks\n4. Copy-Paste Caption & 15 Trending Hashtags\n'
                '5. Brand Collaboration & Monetization Plan\n6. 30-Day Instagram Growth Action Plan\n'
            )
            report_box = st.empty()
            full_text = ''
            try:
                for piece in generate_report_stream(ig_prompt):
                    full_text += piece
                    report_box.markdown(full_text)
                ig_status_slot.empty()
                st.session_state.ig_report = full_text
                if not st.session_state.pro_unlocked:
                    increment_free_used(st.session_state.verified_email)
                log_usage_to_sheet(st.session_state.verified_email or 'PRO', 'Instagram', ig_url.strip())
                st.rerun()
            except Exception as e:
                ig_status_slot.empty()
                st.error(str(e))

    if st.session_state.ig_report:
        st.success(f"✅ {ui['ready']}")
        st.download_button(
            f"📥 {ui['download']}",
            data=st.session_state.ig_report,
            file_name='TrendSutra_Instagram_Report.txt',
            mime='text/plain',
            use_container_width=True
        )
        st.markdown('---')
        st.markdown(st.session_state.ig_report)

with tab_tt:
    tc1, tc2, tc3 = st.columns([3.3, 1.4, 1.3], vertical_alignment='center')
    with tc1:
        tt_url = st.text_input('TikTok URL', placeholder='Paste TikTok Video Link...', label_visibility='collapsed')
    with tc2:
        run_tt = st.button(f"{ui['gen_btn']} 🔍", key='btn_tt', type='primary', use_container_width=True)
    with tc3:
        tt_status_slot = st.empty()

    if run_tt:
        if not st.session_state.verified_email and not st.session_state.pro_unlocked:
            st.warning('Please login above with Gmail or Mail ID to get your 3 Free Reports.')
        elif not tt_url.strip():
            st.warning('Please paste a TikTok video link.')
        elif not st.session_state.pro_unlocked and free_left <= 0:
            st.error(f"🔒 {ui['free_done']}")
        else:
            tt_status_slot.markdown(f"<div class='loading-pill'>⚡ {ui['generating']} ⏳</div>", unsafe_allow_html=True)
            lang_rule = build_lang_instruction(report_lang)
            tt_prompt = (
                f'You are a warm, encouraging human TikTok growth advisor ("సలహాదారు").\n'
                f'Write a detailed 6-section TikTok growth audit (1,000+ words) for a **{audience_scope}** audience using simple spoken words.\n'
                f'{lang_rule}\nTikTok Link: {tt_url.strip()}\n'
                'Include 6 sections (headings translated into target native script):\n'
                '1. Creator Appreciation & Viral Potential Overview\n2. Completion Rate & Looping Hook Formula\n'
                '3. 3 Viral Follow-Up TikTok Ideas with word-for-word 3-second Hooks\n4. Copy-Paste Caption & 15 FYP Hashtags\n'
                '5. Creator Rewards & Brand Monetization Plan\n6. 30-Day TikTok Growth Action Plan\n'
            )
            report_box = st.empty()
            full_text = ''
            try:
                for piece in generate_report_stream(tt_prompt):
                    full_text += piece
                    report_box.markdown(full_text)
                tt_status_slot.empty()
                st.session_state.tt_report = full_text
                if not st.session_state.pro_unlocked:
                    increment_free_used(st.session_state.verified_email)
                log_usage_to_sheet(st.session_state.verified_email or 'PRO', 'TikTok', tt_url.strip())
                st.rerun()
            except Exception as e:
                tt_status_slot.empty()
                st.error(str(e))

    if st.session_state.tt_report:
        st.success(f"✅ {ui['ready']}")
        st.download_button(
            f"📥 {ui['download']}",
            data=st.session_state.tt_report,
            file_name='TrendSutra_TikTok_Report.txt',
            mime='text/plain',
            use_container_width=True
        )
        st.markdown('---')
        st.markdown(st.session_state.tt_report)
