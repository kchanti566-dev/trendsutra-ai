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
from email.mime.text import MIMEText

# --- 1. PAGE CONFIG ---
st.set_page_config(
    page_title="TrendSutra AI - 1 AI • 1 India",
    page_icon="logo.png" if os.path.exists("logo.png") else "🇮🇳",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. LOAD SECRETS (FREE KEYS FIRST -> PAID KEY LAST) ---
KEY_PAID = str(st.secrets.get("GEMINI_API_KEY", "")).strip()
KEY_2 = str(st.secrets.get("GEMINI_API_KEY_2", "")).strip()
KEY_3 = str(st.secrets.get("GEMINI_API_KEY_3", "")).strip()
KEY_4 = str(st.secrets.get("GEMINI_API_KEY_4", "")).strip()

ORDERED_KEYS = []
for label, val in [("FREE_4", KEY_4), ("FREE_3", KEY_3), ("FREE_2", KEY_2), ("PAID_1", KEY_PAID)]:
    if val and val not in [v for _, v in ORDERED_KEYS]:
        ORDERED_KEYS.append((label, val))

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

# --- 3. ALL 22 INDIAN OFFICIAL LANGUAGES + BHOJPURI (A-Z) ---
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
    "Sindhi (सिन्धी)",
    "Tamil (தமிழ்)",
    "Telugu (తెలుగు)",
    "Tenglish (Telugu + English)",
    "Urdu (اردو)"
]

# --- 4. DYNAMIC MULTI-LANGUAGE UI DICTIONARY ---
UI_TEXT = {
    "English": {
        "free_left": "Free Reports Left",
        "free_done": "0/3 Free Reports Left",
        "gen_btn": "Generate Growth Report 🔍",
        "fetching": "Fetching video details...",
        "generating": "Generating report...",
        "ready": "Growth Audit Report Ready!",
        "download": "Download Complete Report (.txt) 📥",
        "send_otp": "Send OTP 📩",
        "otp_sent": "6-digit OTP sent to",
        "verify_otp": "Verify OTP ✅",
        "wrong_otp": "Invalid OTP! Please check again.",
        "limit_msg": "Your 3 free reports are finished! Upgrade to Pro on the left."
    },
    "Telugu": {
        "free_left": "ఉచిత రిపోర్ట్‌లు మిగిలాయి",
        "free_done": "0/3 ఉచిత రిపోర్ట్‌లు మిగిలాయి",
        "gen_btn": "గ్రోత్ రిపోర్ట్ తయారు చేయండి 🔍",
        "fetching": "వీడియో వివరాలు సేకరిస్తోంది...",
        "generating": "రిపోర్ట్ తయారవుతోంది...",
        "ready": "గ్రోత్ ఆడిట్ రిపోర్ట్ సిద్ధమైంది!",
        "download": "పూర్తి రిపోర్ట్ డౌన్‌లోడ్ చేయండి (.txt) 📥",
        "send_otp": "OTP పంపండి 📩",
        "otp_sent": "కి 6-అంకెల OTP పంపబడింది!",
        "verify_otp": "OTP నిర్ధారించండి ✅",
        "wrong_otp": "తప్పు OTP! దయచేసి మళ్ళీ చెక్ చేయండి.",
        "limit_msg": "మీ 3 ఉచిత రిపోర్ట్‌లు పూర్తయ్యాయి! ఎడమ వైపు Pro ప్లాన్ తీసుకోండి."
    },
    "Hindi": {
        "free_left": "मुफ्त रिपोर्ट बाकी हैं",
        "free_done": "0/3 मुफ्त रिपोर्ट बाकी हैं",
        "gen_btn": "ग्रोथ रिपोर्ट बनाएं 🔍",
        "fetching": "वीडियो विवरण प्राप्त हो रहा है...",
        "generating": "रिपोर्ट तैयार हो रही है...",
        "ready": "ग्रोथ ऑडिट रिपोर्ट तैयार है!",
        "download": "पूरी रिपोर्ट डाउनलोड करें (.txt) 📥",
        "send_otp": "OTP भेजें 📩",
        "otp_sent": "पर 6-अंकों का OTP भेजा गया है!",
        "verify_otp": "OTP सत्यापित करें ✅",
        "wrong_otp": "गलत OTP! कृपया पुनः जांचें।",
        "limit_msg": "आपकी 3 मुफ्त रिपोर्ट पूरी हो गई हैं! बाईं ओर Pro प्लान चुनें।"
    },
    "Tamil": {
        "free_left": "இலவச அறிக்கைகள் உள்ளன",
        "free_done": "0/3 இலவச அறிக்கைகள் உள்ளன",
        "gen_btn": "வளர்ச்சி அறிக்கையை உருவாக்கு 🔍",
        "fetching": "வீடியோ விவரங்கள் சேகரிக்கப்படுகின்றன...",
        "generating": "அறிக்கை தயாராகிறது...",
        "ready": "வளர்ச்சி தணிக்கை அறிக்கை தயார்!",
        "download": "முழு அறிக்கையைப் பதிவிறக்கவும் (.txt) 📥",
        "send_otp": "OTP அனுப்பு 📩",
        "otp_sent": "க்கு 6-இலக்க OTP அனுப்பப்பட்டது!",
        "verify_otp": "OTP சரிபார் ✅",
        "wrong_otp": "தவறான OTP! மீண்டும் சரிபார்க்கவும்.",
        "limit_msg": "உங்கள் 3 இலவச அறிக்கைகள் முடிந்துவிட்டன! இடதுபுறம் Pro திட்டத்தைப் பெறவும்."
    },
    "Kannada": {
        "free_left": "ಉಚಿತ ವರದಿಗಳು ಬಾಕಿ ಇವೆ",
        "free_done": "0/3 ಉಚಿತ ವರದಿಗಳು ಬಾಕಿ ಇವೆ",
        "gen_btn": "ಗ್ರೋತ್ ವರದಿ ರಚಿಸಿ 🔍",
        "fetching": "ವೀಡಿಯೊ ವಿವರಗಳನ್ನು ಪಡೆಯಲಾಗುತ್ತಿದೆ...",
        "generating": "ವರದಿ ಸಿದ್ಧವಾಗುತ್ತಿದೆ...",
        "ready": "ಗ್ರೋತ್ ಆಡಿಟ್ ವರದಿ ಸಿದ್ಧವಾಗಿದೆ!",
        "download": "ಪೂರ್ಣ ವರದಿಯನ್ನು ಡೌನ್‌ಲೋಡ್ ಮಾಡಿ (.txt) 📥",
        "send_otp": "OTP ಕಳುಹಿಸಿ 📩",
        "otp_sent": "ಗೆ 6-ಅಂಕಿಯ OTP ಕಳುಹಿಸಲಾಗಿದೆ!",
        "verify_otp": "OTP ಪರಿಶೀಲಿಸಿ ✅",
        "wrong_otp": "ತಪ್ಪಾದ OTP! ದಯವಿಟ್ಟು ಮತ್ತೆ ಪರಿಶೀಲಿಸಿ.",
        "limit_msg": "ನಿಮ್ಮ 3 ಉಚಿತ ವರದಿಗಳು ಮುಗಿದಿವೆ! ಎಡಭಾಗದಲ್ಲಿ Pro ಪ್ಲಾನ್ ಆಯ್ಕೆಮಾಡಿ."
    },
    "Malayalam": {
        "free_left": "സൗജന്യ റിപ്പോർട്ടുകൾ ബാക്കിയുണ്ട്",
        "free_done": "0/3 സൗജന്യ റിപ്പോർട്ടുകൾ ബാക്കിയുണ്ട്",
        "gen_btn": "ഗ്രോത്ത് റിപ്പോർട്ട് തയ്യാറാക്കുക 🔍",
        "fetching": "വീഡിയോ വിവരങ്ങൾ ശേഖരിക്കുന്നു...",
        "generating": "റിപ്പോർട്ട് തയ്യാറാകുന്നു...",
        "ready": "ഗ്രോത്ത് ഓഡിറ്റ് റിപ്പോർട്ട് തയ്യാറായി!",
        "download": "പൂർണ്ണ റിപ്പോർട്ട് ഡൗൺലോഡ് ചെയ്യുക (.txt) 📥",
        "send_otp": "OTP അയക്കുക 📩",
        "otp_sent": "ലേക്ക് 6-അക്ക OTP അയച്ചിരിക്കുന്നു!",
        "verify_otp": "OTP പരിശോധിക്കുക ✅",
        "wrong_otp": "തെറ്റായ OTP! ദയവായി വീണ്ടും പരിശോധിക്കുക.",
        "limit_msg": "നിങ്ങളുടെ 3 സൗജന്യ റിപ്പോർട്ടുകൾ തീർന്നു! ഇടതുവശത്ത് Pro പ്ലാൻ എടുക്കുക."
    },
    "Marathi": {
        "free_left": "मोफत रिपोर्ट शिल्लक आहेत",
        "free_done": "0/3 मोफत रिपोर्ट शिल्लक आहेत",
        "gen_btn": "ग्रोथ रिपोर्ट तयार करा 🔍",
        "fetching": "व्हिडिओ माहिती मिळवत आहे...",
        "generating": "रिपोर्ट तयार होत आहे...",
        "ready": "ग्रोथ ऑडिट रिपोर्ट तयार आहे!",
        "download": "संपूर्ण रिपोर्ट डाउनलोड करा (.txt) 📥",
        "send_otp": "OTP पाठवा 📩",
        "otp_sent": "वर 6-अंकी OTP पाठवला आहे!",
        "verify_otp": "OTP तपासा ✅",
        "wrong_otp": "चुकीचा OTP! कृपया पुन्हा तपासा.",
        "limit_msg": "तुमचे 3 मोफत रिपोर्ट संपले आहेत! डावीकडे Pro प्लॅन घ्या."
    },
    "Bengali": {
        "free_left": "বিনামূল্যে রিপোর্ট বাকি আছে",
        "free_done": "0/3 বিনামূল্যে রিপোর্ট বাকি আছে",
        "gen_btn": "গ্রোথ রিপোর্ট তৈরি করুন 🔍",
        "fetching": "ভিডিওর তথ্য সংগ্রহ করা হচ্ছে...",
        "generating": "রিপোর্ট তৈরি হচ্ছে...",
        "ready": "গ্রোথ অডিট রিপোর্ট তৈরি!",
        "download": "সম্পূর্ণ রিপোর্ট ডাউনলোড করুন (.txt) 📥",
        "send_otp": "OTP পাঠান 📩",
        "otp_sent": "এ ৬-সংখ্যার OTP পাঠানো হয়েছে!",
        "verify_otp": "OTP যাচাই করুন ✅",
        "wrong_otp": "ভুল OTP! অনুগ্রহ করে আবার দেখুন।",
        "limit_msg": "আপনার ৩টি ফ্রি রিপোর্ট শেষ! বাম দিকে Pro প্ল্যান নিন।"
    },
    "Gujarati": {
        "free_left": "મફત રિપોર્ટ બાકી છે",
        "free_done": "0/3 મફત રિપોર્ટ બાકી છે",
        "gen_btn": "ગ્રોથ રિપોર્ટ બનાવો 🔍",
        "fetching": "વીડિયોની વિગતો મેળવી રહ્યા છીએ...",
        "generating": "રિપોર્ટ તૈયાર થઈ રહ્યો છે...",
        "ready": "ગ્રોથ ઓડિટ રિપોર્ટ તૈયાર છે!",
        "download": "સંપૂર્ણ રિપોર્ટ ડાઉનલોડ કરો (.txt) 📥",
        "send_otp": "OTP મોકલો 📩",
        "otp_sent": "પર 6-અંકનો OTP મોકલવામાં આવ્યો છે!",
        "verify_otp": "OTP ચકાસો ✅",
        "wrong_otp": "ખોટો OTP! કૃપા કરીને ફરી તપાસો.",
        "limit_msg": "તમારા 3 મફત રિપોર્ટ પૂરા થઈ ગયા છે! ડાબી બાજુ Pro પ્લાન લો."
    },
    "Punjabi": {
        "free_left": "ਮੁਫ਼ਤ ਰਿਪੋਰਟਾਂ ਬਾਕੀ ਹਨ",
        "free_done": "0/3 ਮੁਫ਼ਤ ਰਿਪੋਰਟਾਂ ਬਾਕੀ ਹਨ",
        "gen_btn": "ਗਰੋਥ ਰਿਪੋਰਟ ਬਣਾਓ 🔍",
        "fetching": "ਵੀਡੀਓ ਵੇਰਵੇ ਲਏ ਜਾ ਰਹੇ ਹਨ...",
        "generating": "ਰਿਪੋਰਟ ਤਿਆਰ ਹੋ ਰਹੀ ਹੈ...",
        "ready": "ਗਰੋਥ ਆਡਿਟ ਰਿਪੋਰਟ ਤਿਆਰ ਹੈ!",
        "download": "ਪੂਰੀ ਰਿਪੋਰਟ ਡਾਊਨਲੋਡ ਕਰੋ (.txt) 📥",
        "send_otp": "OTP ਭੇਜੋ 📩",
        "otp_sent": "ਤੇ 6-ਅੰਕਾਂ ਦਾ OTP ਭੇਜਿਆ ਗਿਆ ਹੈ!",
        "verify_otp": "OTP ਪੁਸ਼ਟੀ ਕਰੋ ✅",
        "wrong_otp": "ਗਲਤ OTP! ਕਿਰਪਾ ਕਰਕੇ ਦੁਬਾਰਾ ਜਾਂਚ ਕਰੋ।",
        "limit_msg": "ਤੁਹਾਡੀਆਂ 3 ਮੁਫ਼ਤ ਰਿਪੋਰਟਾਂ ਖ਼ਤਮ ਹੋ ਗਈਆਂ ਹਨ! ਖੱਬੇ ਪਾਸੇ Pro ਪਲਾਨ ਲਓ।"
    },
    "Odia": {
        "free_left": "ମାଗଣା ରିପୋର୍ଟ ବାକି ଅଛି",
        "free_done": "0/3 ମାଗଣା ରିପୋର୍ଟ ବାକି ଅଛି",
        "gen_btn": "ଗ୍ରୋଥ୍ ରିପୋର୍ଟ ତିଆରି କରନ୍ତୁ 🔍",
        "fetching": "ଭିଡିଓ ତଥ୍ୟ ସଂଗ୍ରହ ହେଉଛି...",
        "generating": "ରିପୋର୍ଟ ପ୍ରସ୍ତୁତ ହେଉଛି...",
        "ready": "ଗ୍ରୋଥ୍ ଅଡିଟ୍ ରିପୋର୍ଟ ପ୍ରସ୍ତୁତ!",
        "download": "ସମ୍ପୂର୍ଣ୍ଣ ରିପୋର୍ଟ ଡାଉନଲୋଡ୍ କରନ୍ତୁ (.txt) 📥",
        "send_otp": "OTP ପଠାନ୍ତୁ 📩",
        "otp_sent": "କୁ 6-ଅଙ୍କ ବିଶିଷ୍ଟ OTP ପଠାଯାଇଛି!",
        "verify_otp": "OTP ଯାଞ୍ଚ କରନ୍ତୁ ✅",
        "wrong_otp": "ଭୁଲ୍ OTP! ଦୟାକରି ପୁଣି ଯାଞ୍ଚ କରନ୍ତୁ।",
        "limit_msg": "ଆପଣଙ୍କର 3ଟି ମାଗଣା ରିପୋର୍ଟ ଶେଷ ହୋଇଯାଇଛି! ବାମ ପାର୍ଶ୍ୱରେ Pro ପ୍ଲାନ୍ ନିଅନ୍ତୁ।"
    },
    "Assamese": {
        "free_left": "বিনামূলীয়া ৰিপৰ্ট বাকী আছে",
        "free_done": "0/3 বিনামূলীয়া ৰিপৰ্ট বাকী আছে",
        "gen_btn": "গ্ৰোথ ৰিপৰ্ট তৈয়াৰ কৰক 🔍",
        "fetching": "ভিডিঅ'ৰ তথ্য সংগ্ৰহ কৰা হৈছে...",
        "generating": "ৰিপৰ্ট প্ৰস্তুত হৈ আছে...",
        "ready": "গ্ৰোথ অডিট ৰিপৰ্ট সাজু!",
        "download": "সম্পূৰ্ণ ৰিপৰ্ট ডাউনলোড কৰক (.txt) 📥",
        "send_otp": "OTP পঠিয়াওক 📩",
        "otp_sent": "লৈ ৬-সংখ্যাৰ OTP পঠিওৱা হৈছে!",
        "verify_otp": "OTP পৰীক্ষা কৰক ✅",
        "wrong_otp": "ভুল OTP! অনুগ্ৰহ কৰি পুনৰ চাওক।",
        "limit_msg": "আপোনাৰ ৩টা বিনামূলীয়া ৰিপৰ্ট শেষ হৈছে! বাওঁফালে Pro প্লেন লওক।"
    },
    "Urdu": {
        "free_left": "مفت رپورٹس باقی ہیں",
        "free_done": "0/3 مفت رپورٹس باقی ہیں",
        "gen_btn": "گروتھ رپورٹ بنائیں 🔍",
        "fetching": "ویڈیو کی تفصیلات حاصل کی جا رہی ہیں...",
        "generating": "رپورٹ تیار ہو رہی ہے...",
        "ready": "گروتھ آڈٹ رپورٹ تیار ہے!",
        "download": "مکمل رپورٹ ڈاؤن لوڈ کریں (.txt) 📥",
        "send_otp": "OTP بھیجیں 📩",
        "otp_sent": "پر 6 ہندسوں کا OTP بھیج دیا گیا ہے!",
        "verify_otp": "OTP کی تصدیق کریں ✅",
        "wrong_otp": "غلط OTP! براہ کرم دوبارہ چیک کریں۔",
        "limit_msg": "آپ کی 3 مفت رپورٹس ختم ہو گئی ہیں! بائیں جانب Pro پلان لیں۔"
    },
    "Bhojpuri": {
        "free_left": "फ्री रिपोर्ट बाचल बा",
        "free_done": "0/3 फ्री रिपोर्ट बाचल बा",
        "gen_btn": "ग्रोथ रिपोर्ट बनाईं 🔍",
        "fetching": "वीडियो के जानकारी मिल रहल बा...",
        "generating": "रिपोर्ट तैयार हो रहल बा...",
        "ready": "ग्रोथ ऑडिट रिपोर्ट तैयार बा!",
        "download": "पूरा रिपोर्ट डाउनलोड करीं (.txt) 📥",
        "send_otp": "OTP भेजीं 📩",
        "otp_sent": "पर 6 अंक के OTP भेज दिहल गइल बा!",
        "verify_otp": "OTP जांच करीं ✅",
        "wrong_otp": "गलत OTP! कृपया फिर से देखीं।",
        "limit_msg": "रउआ 3 फ्री रिपोर्ट खतम हो गइल बा! बाएं ओर Pro प्लान लीं।"
    }
}

def get_ui_lang_key(selected_lang, detected_lang=""):
    target = detected_lang if (selected_lang == "Auto-Detect Video Language" and detected_lang) else selected_lang
    for k in UI_TEXT.keys():
        if k != "English" and k.lower() in target.lower():
            return k
    return "English"

def t_ui(key, selected_lang, detected_lang=""):
    lk = get_ui_lang_key(selected_lang, detected_lang)
    return UI_TEXT.get(lk, UI_TEXT["English"]).get(key, UI_TEXT["English"][key])

# --- 5. COMPACT NO-SCROLL DARK STYLING ---
st.markdown("""
<style>
    [data-testid="stToolbarActions"] { display: none !important; }
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }

    .block-container {
        padding-top: 0.75rem !important;
        padding-bottom: 0.5rem !important;
        max-width: 1220px !important;
    }

    section[data-testid="stSidebar"] > div {
        padding-top: 0.5rem !important;
        padding-bottom: 0.3rem !important;
    }
    section[data-testid="stSidebar"] .stMarkdown p {
        margin-bottom: 0.25rem !important;
        font-size: 0.85rem !important;
    }
    section[data-testid="stSidebar"] hr {
        margin: 0.45rem 0 !important;
    }

    .center-banner {
        background: linear-gradient(135deg, #0b132b 0%, #1c2541 100%);
        border: 1.5px solid #2b3a67;
        border-radius: 12px;
        padding: 12px 18px;
        text-align: center;
        margin-bottom: 10px;
    }
    .banner-title-row {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 12px;
    }
    .banner-title-row h1 {
        margin: 0;
        font-size: 1.85rem;
        font-weight: 800;
        color: #ffffff;
        letter-spacing: 0.3px;
    }
    .india-badge {
        background: rgba(16, 185, 129, 0.16);
        border: 1px solid #10b981;
        color: #6ee7b7;
        padding: 2px 10px;
        border-radius: 20px;
        font-size: 0.78rem;
        font-weight: 700;
    }
    .banner-sub {
        margin: 4px 0 0 0;
        color: #cbd5e1;
        font-size: 0.90rem;
    }

    .status-strip {
        background: #111827;
        border: 1px solid #374151;
        border-radius: 8px;
        padding: 7px 14px;
        color: #e5e7eb;
        font-size: 0.88rem;
        margin-bottom: 8px;
    }

    .loading-pill {
        background: #ecfdf5;
        border: 1.5px solid #10b981;
        color: #065f46;
        padding: 8px 12px;
        border-radius: 8px;
        font-weight: 700;
        font-size: 0.86rem;
        text-align: center;
    }
    .lang-detected-pill {
        background: #1e293b;
        border: 1px solid #38bdf8;
        color: #7dd3fc;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.82rem;
        font-weight: 600;
        display: inline-block;
        margin-bottom: 8px;
    }
</style>
""", unsafe_allow_html=True)

# --- 6. SESSION STATE ---
for k, default_v in [
    ("verified_email", ""),
    ("otp_code", ""),
    ("otp_target", ""),
    ("pro_unlocked", False),
    ("pro_label", ""),
    ("yt_report", ""),
    ("yt_vid_id", ""),
    ("yt_detected_lang", ""),
    ("yt_stats", None),
    ("ig_report", ""),
    ("tt_report", ""),
    ("exhausted_keys", set())
]:
    if k not in st.session_state:
        st.session_state[k] = default_v

# --- 7. CHECK GOOGLE OAUTH & RAZORPAY AUTO-REDIRECT ---
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
        r = requests.get(SHEET_API, params={"device": user_id, "_ts": int(time.time())}, timeout=7, allow_redirects=True)
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
            r = requests.get(SHEET_API, params={"device": user_id, "inc": "1", "_ts": int(time.time())}, timeout=7, allow_redirects=True)
            if r.status_code == 200 and r.text.strip().isdigit():
                return
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
            "url": url,
            "_ts": int(time.time())
        }, timeout=5, allow_redirects=True)
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
        r = requests.get(SHEET_API, params={"pid": pid, "plan": plan, "_ts": int(time.time())}, timeout=9, allow_redirects=True)
        if r.status_code == 200:
            res = r.text.strip().upper()
            if res in ["VALID", "ALREADY_USED", "EXPIRED", "INVALID"]:
                return res
    except Exception:
        pass
    return "ERROR"

qp = st.query_params
auto_pay_id = qp.get("razorpay_payment_id", "")
if auto_pay_id and not st.session_state.pro_unlocked:
    st_res = verify_payment_id(auto_pay_id, plan="1m")
    if st_res in ["VALID", "OWNER"]:
        st.session_state.pro_unlocked = True
        st.session_state.pro_label = "PRO UNLIMITED ACTIVE"

def send_otp_email(to_email, code):
    if not SENDER_EMAIL or not SENDER_PASS:
        return False, "SMTP not configured"
    try:
        body = (
            f"Welcome to TrendSutra AI (1 AI • 1 India)!\n\n"
            f"Your 6-digit verification code is: {code}\n\n"
            f"Enter this code on TrendSutra AI to unlock your 3 Free Growth Reports."
        )
        msg = MIMEText(body)
        msg["Subject"] = f"{code} is your TrendSutra AI Verification Code"
        msg["From"] = f"TrendSutra AI <{SENDER_EMAIL}>"
        msg["To"] = to_email
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=10) as server:
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
                part="snippet", videoId=video_id, maxResults=18, order="relevance", textFormat="plainText"
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
            "description": snip.get("description", "")[:1000],
            "tags": snip.get("tags", [])[:15],
            "default_audio_lang": snip.get("defaultAudioLanguage", ""),
            "views": int(stats.get("viewCount", 0)),
            "likes": int(stats.get("likeCount", 0)),
            "comment_count": int(stats.get("commentCount", 0)),
            "comments": comments
        }
    except Exception:
        return None

# --- 10. FAST SMART SESSION-MEMORY MULTI-KEY GEMINI STREAMING ---
@st.cache_resource
def get_gemini_client_for_key(api_key):
    return genai.Client(api_key=api_key)

def clean_mentor_word(text):
    return text.replace("మెంటర్", "సలహాదారు").replace("స్ట్రాటజిస్ట్", "సలహాదారు")

def generate_report_stream(prompt):
    if not ORDERED_KEYS:
        raise RuntimeError("No Gemini API keys configured in Secrets.")

    fast_models = [
        "gemini-2.5-flash-lite",
        "gemini-2.5-flash",
        "gemini-3.5-flash-lite",
        "gemini-3.5-flash"
    ]

    active_keys = [
        (lbl, kv) for (lbl, kv) in ORDERED_KEYS
        if lbl == "PAID_1" or lbl not in st.session_state.exhausted_keys
    ]
    if not active_keys:
        active_keys = ORDERED_KEYS

    last_err = ""
    for key_label, api_key in active_keys:
        client = get_gemini_client_for_key(api_key)
        for model_name in fast_models:
            try:
                response = client.models.generate_content_stream(
                    model=model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.80,
                        max_output_tokens=6144
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
                err_s = str(e)
                last_err = err_s
                if "429" in err_s or "RESOURCE_EXHAUSTED" in err_s or "403" in err_s or "API_KEY_INVALID" in err_s:
                    if key_label != "PAID_1":
                        st.session_state.exhausted_keys.add(key_label)
                    break
                continue

    raise RuntimeError(f"AI servers are temporarily busy. Please try again in 5 seconds. ({last_err})")

# --- 11. SIDEBAR (NO SCROLL) ---
with st.sidebar:
    st.markdown("### ⚙️ Settings")
    report_lang = st.selectbox(
        "🔍 Search Language (A–Z):",
        LANGUAGES_LIST,
        index=0
    )
    audience_scope = st.radio("Audience:", ["Regional", "Global", "Both"], horizontal=True)

    st.divider()
    st.markdown("### 💎 Pro Plans")

    free_used = get_free_used_count(st.session_state.verified_email) if st.session_state.verified_email else 0
    free_left = max(0, 3 - free_used)
    det_lang = st.session_state.yt_detected_lang

    if st.session_state.pro_unlocked:
        st.success(f"✅ {st.session_state.pro_label}")
    elif st.session_state.verified_email:
        if free_left > 0:
            st.info(f"🎁 {free_left}/3 {t_ui('free_left', report_lang, det_lang)}")
        else:
            st.error(f"🔒 {t_ui('free_done', report_lang, det_lang)}")
    else:
        st.info("🎁 Login for **3 Free Reports**")

    st.markdown(f"• **1 Month:** ₹100 👉 [Pay ₹100]({RAZORPAY_1M}) • **12 Months:** ₹1,000 👉 [Pay ₹1,000]({RAZORPAY_12M})")

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
                st.error("❌ Invalid Payment ID.")

    st.caption("📩 support@aiengtel.com | aiengtel.com")

# --- 12. CENTERED HEADER WITH LOGO ---
logo_html = ""
if os.path.exists("logo.png"):
    with open("logo.png", "rb") as lf:
        b64_logo = base64.b64encode(lf.read()).decode()
    logo_html = f'<img src="data:image/png;base64,{b64_logo}" style="height:42px; width:42px; border-radius:8px; object-fit:contain;" />'

st.markdown(f"""
<div class="center-banner">
    <div class="banner-title-row">
        {logo_html}
        <h1>TrendSutra AI</h1>
        <span class="india-badge">🇮🇳 1 AI • 1 India</span>
    </div>
    <p class="banner-sub">A to Z Growth Analyzer in All 22 Indian Official Languages + Bhojpuri for YouTube, Instagram & TikTok</p>
</div>
""", unsafe_allow_html=True)

# --- 13. COMPACT SINGLE-ROW LOGIN BAR ---
if not st.session_state.verified_email and not st.session_state.pro_unlocked:
    lc1, lc2, lc3, lc4 = st.columns([2.2, 0.4, 2.6, 1.5])
    with lc1:
        if st.button("Continue with Gmail", type="primary", use_container_width=True):
            try:
                st.login("google")
            except Exception as e:
                st.error(f"Google Login Error: {e}")
    with lc2:
        st.markdown("<div style='text-align:center; padding-top:7px; color:#94a3b8; font-weight:700;'>OR</div>", unsafe_allow_html=True)
    with lc3:
        email_in = st.text_input("Mail ID", placeholder="Login with Mail ID (creator@gmail.com)", label_visibility="collapsed")
    with lc4:
        if st.button(t_ui("send_otp", report_lang), use_container_width=True):
            clean_em = email_in.strip().lower()
            if "@" not in clean_em or "." not in clean_em.split("@")[-1]:
                st.error("❌ Invalid Email ID")
            elif clean_em.split("@")[-1] in TEMP_DOMAINS:
                st.error("❌ Temp Email not allowed")
            else:
                code = str(random.randint(100000, 999999))
                ok, err_msg = send_otp_email(clean_em, code)
                if ok:
                    st.session_state.otp_code = code
                    st.session_state.otp_target = clean_em
                    st.success(f"✅ {st.session_state.otp_target} {t_ui('otp_sent', report_lang)}")
                else:
                    st.error(f"OTP Error: {err_msg}")

    if st.session_state.otp_target:
        oc1, oc2 = st.columns([3, 1.5])
        with oc1:
            otp_in = st.text_input("OTP", placeholder="Enter 6-digit OTP from Inbox/Spam", max_chars=6, label_visibility="collapsed")
        with oc2:
            if st.button(t_ui("verify_otp", report_lang), type="primary", use_container_width=True):
                if otp_in.strip() == st.session_state.otp_code:
                    st.session_state.verified_email = st.session_state.otp_target
                    st.session_state.otp_code = ""
                    st.rerun()
                else:
                    st.error(f"❌ {t_ui('wrong_otp', report_lang)}")
else:
    sc1, sc2 = st.columns([5.2, 1.2])
    with sc1:
        who = st.session_state.verified_email if st.session_state.verified_email else "PRO User"
        badge = f"✅ {st.session_state.pro_label}" if st.session_state.pro_unlocked else f"🎁 {free_left}/3 {t_ui('free_left', report_lang, det_lang)}"
        st.markdown(f"<div class='status-strip'>👤 Logged in as <b>{who}</b> &nbsp;|&nbsp; {badge}</div>", unsafe_allow_html=True)
    with sc2:
        if st.button("Logout 🚪", use_container_width=True):
            st.session_state.verified_email = ""
            st.session_state.pro_unlocked = False
            st.session_state.yt_report = ""
            st.session_state.yt_detected_lang = ""
            try:
                if hasattr(st, "logout"):
                    st.logout()
            except Exception:
                pass
            st.rerun()

# --- 14. TABS ---
tab_yt, tab_ig, tab_tt = st.tabs(["📺 YouTube Analyzer", "📸 Instagram Reels Analyzer", "🎵 TikTok Analyzer"])

with tab_yt:
    ic1, ic2, ic3 = st.columns([4.2, 1.7, 1.4])
    with ic1:
        yt_url = st.text_input("YT Link", placeholder="Paste YouTube Video or Shorts Link (https://www.youtube.com/watch?v=...)", label_visibility="collapsed")
    with ic2:
        run_yt = st.button(t_ui("gen_btn", report_lang, det_lang), key="btn_yt", type="primary", use_container_width=True)
    with ic3:
        yt_status_slot = st.empty()

    if run_yt:
        if not st.session_state.verified_email and not st.session_state.pro_unlocked:
            st.warning("🔒 Please login with Gmail or Mail ID above to get your 3 Free Reports.")
        elif not yt_url.strip():
            st.warning("Please paste a YouTube link.")
        elif not st.session_state.pro_unlocked and free_left <= 0:
            st.error(f"🔒 {t_ui('limit_msg', report_lang, det_lang)}")
        else:
            vid_id = extract_youtube_id(yt_url.strip())
            if not vid_id:
                st.error("❌ Please enter a valid YouTube video or Shorts link.")
            else:
                yt_status_slot.markdown(f"<div class='loading-pill'>🔄 {t_ui('fetching', report_lang, det_lang)} ⏳</div>", unsafe_allow_html=True)
                data = fetch_youtube_details(vid_id)
                if not data:
                    yt_status_slot.empty()
                    st.error("❌ Could not fetch video details. Make sure the video is Public.")
                else:
                    st.session_state.yt_stats = data
                    st.session_state.yt_vid_id = vid_id
                    comments_block = "\n".join(data["comments"][:12]) if data["comments"] else "No public comments."

                    if report_lang == "Auto-Detect Video Language":
                        lang_instruction = (
                            "STEP 1 (FIRST LINE ONLY): Detect the primary spoken/written language of this video from its title, audio tag, description, and comments. "
                            "Output ONLY on the very first line: `DETECTED_LANG: <Language Name in English, e.g. Telugu, Hindi, Tamil, Kannada, Malayalam, Marathi, Bengali, Gujarati, Punjabi, Odia, Assamese, Urdu, Bhojpuri, English>`\n"
                            "STEP 2: Write the ENTIRE 6-section report (including ALL 6 section headings!) in that exact detected language using its NATIVE SCRIPT (e.g., Telugu script for Telugu, Tamil script for Tamil, Devanagari for Hindi/Marathi/Bhojpuri, Urdu script for Urdu)."
                        )
                    else:
                        lang_instruction = (
                            f"Write the ENTIRE 6-section report (including ALL 6 section headings!) strictly in **{report_lang}** using its NATIVE SCRIPT."
                        )

                    prompt = f"""
You are a warm, encouraging human social media growth advisor ("సలహాదారు").
{lang_instruction}
Target Audience: **{audience_scope}**.
Use simple everyday spoken words (never use complex bookish words, and NEVER use the word 'మెంటర్').

VIDEO DATA:
- Channel: {data['channel']}
- Title: {data['title']}
- Audio Tag: {data['default_audio_lang']}
- Views: {data['views']:,} | Likes: {data['likes']:,} | Comments: {data['comment_count']:,}
- Description: {data['description']}
- Tags: {', '.join(data['tags'])}
- Real Audience Comments:
{comments_block}

STRICTLY FOLLOW THIS 6-SECTION STRUCTURE (Translate all 6 headings into the target language's native script):
### 🎬 1. Video Story Recap & Creator Appreciation
- Warmly retell the core story/message of this video based on its title, description, and comments, and genuinely praise the creator's effort and strengths.

### 💬 2. Real Audience Comments & Replies
- Pick 4 real viewer comments above, translate them naturally into the target language, quote them with the viewer's name, and give 3 ready-to-copy reply templates.

### 🔥 3. 3 Next Viral Video Ideas + 5-Sec Hooks
- Give 3 fresh follow-up video ideas tailored to this channel with a word-for-word 5-second opening Hook and Thumbnail idea for each.

### 🎯 4. Copy-Paste SEO Makeover
- Provide 3 clickable high-CTR titles, a 3-line SEO description hook, and 15 searchable comma-separated tags.

### 💰 5. Monetization & Brand Earning Blueprint
- Explain 3 practical ways this channel can earn money (AdSense, Affiliate, Brand deals).

### 📅 6. Step-by-Step 30-Day Action Plan
- Give a clear Week 1 to Week 4 checklist to double views and subscribers.
"""
                    yt_status_slot.markdown(f"<div class='loading-pill'>⚡ {t_ui('generating', report_lang, det_lang)} ⏳</div>", unsafe_allow_html=True)
                    m1, m2, m3 = st.columns(3)
                    m1.metric("👀 Views", f"{data['views']:,}")
                    m2.metric("👍 Likes", f"{data['likes']:,}")
                    m3.metric("💬 Comments", f"{data['comment_count']:,}")

                    lang_badge_slot = st.empty()
                    report_box = st.empty()
                    raw_stream = ""
                    clean_report = ""
                    detected_lang_name = report_lang if report_lang != "Auto-Detect Video Language" else ""

                    try:
                        for piece in generate_report_stream(prompt):
                            raw_stream += piece
                            if report_lang == "Auto-Detect Video Language" and "\n" in raw_stream:
                                first_line, rest = raw_stream.split("\n", 1)
                                if "DETECTED_LANG:" in first_line:
                                    detected_lang_name = first_line.split("DETECTED_LANG:")[-1].strip().strip("*`")
                                    st.session_state.yt_detected_lang = detected_lang_name
                                    lang_badge_slot.markdown(
                                        f"<div class='lang-detected-pill'>🌐 Detected Video Language: <b>{detected_lang_name}</b></div>",
                                        unsafe_allow_html=True
                                    )
                                    yt_status_slot.markdown(
                                        f"<div class='loading-pill'>⚡ {t_ui('generating', report_lang, detected_lang_name)} ⏳</div>",
                                        unsafe_allow_html=True
                                    )
                                    clean_report = rest.lstrip()
                                else:
                                    clean_report = raw_stream
                            else:
                                clean_report = raw_stream
                            if clean_report:
                                report_box.markdown(clean_report)

                        yt_status_slot.empty()
                        st.session_state.yt_report = clean_report
                        if not st.session_state.pro_unlocked:
                            increment_free_used(st.session_state.verified_email)
                        log_usage_to_sheet(st.session_state.verified_email or "PRO", f"YouTube ({detected_lang_name})", yt_url.strip())
                        st.rerun()
                    except Exception as e:
                        yt_status_slot.empty()
                        st.error(str(e))

    if st.session_state.yt_report and not run_yt:
        if st.session_state.yt_stats:
            d = st.session_state.yt_stats
            m1, m2, m3 = st.columns(3)
            m1.metric("👀 Views", f"{d['views']:,}")
            m2.metric("👍 Likes", f"{d['likes']:,}")
            m3.metric("💬 Comments", f"{d['comment_count']:,}")
        dl = st.session_state.yt_detected_lang
        st.success(f"✅ {t_ui('ready', report_lang, dl)}")
        st.download_button(
            t_ui("download", report_lang, dl),
            data=st.session_state.yt_report,
            file_name=f"TrendSutra_Report_{st.session_state.yt_vid_id or 'YouTube'}.txt",
            mime="text/plain",
            use_container_width=True
        )
        if dl:
            st.markdown(f"<div class='lang-detected-pill'>🌐 Detected Video Language: <b>{dl}</b></div>", unsafe_allow_html=True)
        st.markdown(st.session_state.yt_report)

with tab_ig:
    ig_c1, ig_c2, ig_c3 = st.columns([4.2, 1.7, 1.4])
    with ig_c1:
        ig_url = st.text_input("IG Link", placeholder="Paste Instagram Reel Link (https://www.instagram.com/reel/...)", label_visibility="collapsed")
    with ig_c2:
        run_ig = st.button(t_ui("gen_btn", report_lang), key="btn_ig", type="primary", use_container_width=True)
    with ig_c3:
        ig_status_slot = st.empty()

    if run_ig:
        if not st.session_state.verified_email and not st.session_state.pro_unlocked:
            st.warning("🔒 Please login above to get your 3 Free Reports.")
        elif not ig_url.strip():
            st.warning("Please paste an Instagram Reel link.")
        elif not st.session_state.pro_unlocked and free_left <= 0:
            st.error(f"🔒 {t_ui('limit_msg', report_lang)}")
        else:
            ig_status_slot.markdown(f"<div class='loading-pill'>⚡ {t_ui('generating', report_lang)} ⏳</div>", unsafe_allow_html=True)
            target_l = "English" if report_lang == "Auto-Detect Video Language" else report_lang
            ig_prompt = f"""
You are a warm human Instagram Reels growth advisor.
Write a detailed 6-section Instagram Reels growth audit (including all 6 headings) strictly in **{target_l}** using its NATIVE SCRIPT for a **{audience_scope}** audience.
Reel Link: {ig_url.strip()}
Sections: 1. Creator Appreciation & Reel Strategy, 2. Watch-Time & Retention Hook Analysis, 3. 3 Viral Follow-Up Reel Ideas with 3-Sec Hooks, 4. Copy-Paste Caption & 15 Hashtags, 5. Brand Collaboration Blueprint, 6. 30-Day Growth Action Plan.
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
        st.success(f"✅ {t_ui('ready', report_lang)}")
        st.download_button(
            t_ui("download", report_lang),
            data=st.session_state.ig_report,
            file_name="TrendSutra_Instagram_Report.txt",
            mime="text/plain",
            use_container_width=True
        )
        st.markdown(st.session_state.ig_report)

with tab_tt:
    tt_c1, tt_c2, tt_c3 = st.columns([4.2, 1.7, 1.4])
    with tt_c1:
        tt_url = st.text_input("TT Link", placeholder="Paste TikTok Video Link (https://www.tiktok.com/@user/video/...)", label_visibility="collapsed")
    with tt_c2:
        run_tt = st.button(t_ui("gen_btn", report_lang), key="btn_tt", type="primary", use_container_width=True)
    with tt_c3:
        tt_status_slot = st.empty()

    if run_tt:
        if not st.session_state.verified_email and not st.session_state.pro_unlocked:
            st.warning("🔒 Please login above to get your 3 Free Reports.")
        elif not tt_url.strip():
            st.warning("Please paste a TikTok link.")
        elif not st.session_state.pro_unlocked and free_left <= 0:
            st.error(f"🔒 {t_ui('limit_msg', report_lang)}")
        else:
            tt_status_slot.markdown(f"<div class='loading-pill'>⚡ {t_ui('generating', report_lang)} ⏳</div>", unsafe_allow_html=True)
            target_l = "English" if report_lang == "Auto-Detect Video Language" else report_lang
            tt_prompt = f"""
You are a warm human TikTok growth advisor.
Write a detailed 6-section TikTok growth audit (including all 6 headings) strictly in **{target_l}** using its NATIVE SCRIPT for a **{audience_scope}** audience.
TikTok Link: {tt_url.strip()}
Sections: 1. Creator Appreciation & Viral Potential, 2. Completion Rate & Looping Hook Formula, 3. 3 Viral Follow-Up TikTok Ideas with 3-Sec Hooks, 4. Copy-Paste Caption & 15 Hashtags, 5. Creator Rewards & Brand Monetization, 6. 30-Day Growth Action Plan.
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
        st.success(f"✅ {t_ui('ready', report_lang)}")
        st.download_button(
            t_ui("download", report_lang),
            data=st.session_state.tt_report,
            file_name="TrendSutra_TikTok_Report.txt",
            mime="text/plain",
            use_container_width=True
        )
        st.markdown(st.session_state.tt_report)
