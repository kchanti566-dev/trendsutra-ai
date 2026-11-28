import streamlit as st
from google import genai
from google.genai import types
from googleapiclient.discovery import build
import re
import requests
import random
import smtplib
import time
import os
from email.mime.text import MIMEText

# --- 1. PAGE CONFIG ---
page_icon = "logo.png" if os.path.exists("logo.png") else "📊"
st.set_page_config(page_title="TrendSutra AI - 1 AI • 1 India", page_icon=page_icon, layout="wide")

# --- 2. LOAD SECRETS (4-KEY FAILOVER) ---
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

# --- 3. ALL 22 INDIAN SCHEDULED LANGUAGES + BHOJPURI (A-Z) ---
LANGUAGES_LIST = [
    "Auto-Detect Video Language (ఆటోమేటిక్)",
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

# --- 4. DYNAMIC UI TRANSLATIONS (ZERO HARDCODED TELUGU) ---
UI_STRINGS = {
    "English": {
        "free_left": "{n}/3 Free Reports Left",
        "free_over": "0/3 Free Reports Left — Upgrade to Pro",
        "login_prompt": "Login with Gmail or Mail ID to get 3 Free Reports:",
        "otp_sent": "6-digit OTP sent to {email}! Check Inbox / Spam.",
        "otp_enter": "Enter 6-digit OTP:",
        "otp_btn": "Verify OTP ✅",
        "otp_err": "Invalid OTP! Please check and try again.",
        "send_otp": "Send OTP 📩",
        "gen_btn": "Generate Growth Report 🔍",
        "fetching": "🔄 Fetching video details & comments... ⏳",
        "generating": "⚡ Generating report... ⏳",
        "done": "✅ Growth Audit Report is ready!",
        "download": "📥 Download Complete Growth Report (.txt)",
        "locked": "🔒 Your 3 Free Reports are used! Upgrade to Pro Plan on the left for unlimited reports.",
        "paste_warn": "Please paste a valid video link."
    },
    "Telugu": {
        "free_left": "{n}/3 ఉచిత రిపోర్ట్‌లు మిగిలాయి",
        "free_over": "0/3 ఉచిత రిపోర్ట్‌లు పూర్తయ్యాయి — Pro తీసుకోండి",
        "login_prompt": "3 ఉచిత రిపోర్ట్‌ల కోసం Gmail లేదా Mail ID తో లాగిన్ అవ్వండి:",
        "otp_sent": "{email} కి 6-అంకెల OTP పంపబడింది! ఇన్‌బాక్స్ / Spam చెక్ చేయండి.",
        "otp_enter": "6-అంకెల OTP ఎంటర్ చేయండి:",
        "otp_btn": "OTP నిర్ధారించండి ✅",
        "otp_err": "❌ తప్పు OTP! మళ్ళీ చెక్ చేయండి.",
        "send_otp": "OTP పంపండి 📩",
        "gen_btn": "గ్రోత్ రిపోర్ట్ తయారు చేయండి 🔍",
        "fetching": "🔄 వీడియో వివరాలు & కామెంట్లు సేకరిస్తోంది... ⏳",
        "generating": "⚡ రిపోర్ట్ తయారవుతోంది... ⏳",
        "done": "✅ గ్రోత్ ఆడిట్ రిపోర్ట్ సిద్ధమైంది!",
        "download": "📥 పూర్తి రిపోర్ట్ డౌన్‌లోడ్ చేయండి (.txt)",
        "locked": "🔒 మీ 3 ఉచిత రిపోర్ట్‌లు పూర్తయ్యాయి! అన్‌లిమిటెడ్ రిపోర్ట్‌ల కోసం ఎడమ వైపు Pro Plan తీసుకోండి.",
        "paste_warn": "దయచేసి వీడియో లింక్ పేస్ట్ చేయండి."
    },
    "Hindi": {
        "free_left": "{n}/3 मुफ्त रिपोर्ट बाकी हैं",
        "free_over": "0/3 मुफ्त रिपोर्ट समाप्त — Pro लें",
        "login_prompt": "3 मुफ्त रिपोर्ट पाने के लिए Gmail या Mail ID से लॉगिन करें:",
        "otp_sent": "{email} पर 6-अंकों का OTP भेजा गया है! Inbox / Spam देखें।",
        "otp_enter": "6-अंकों का OTP दर्ज करें:",
        "otp_btn": "OTP सत्यापित करें ✅",
        "otp_err": "❌ गलत OTP! कृपया पुनः जांचें।",
        "send_otp": "OTP भेजें 📩",
        "gen_btn": "ग्रोथ रिपोर्ट बनाएं 🔍",
        "fetching": "🔄 वीडियो विवरण और कमेंट्स लिए जा रहे हैं... ⏳",
        "generating": "⚡ रिपोर्ट तैयार हो रही है... ⏳",
        "done": "✅ ग्रोथ ऑडिट रिपोर्ट तैयार है!",
        "download": "📥 पूरी रिपोर्ट डाउनलोड करें (.txt)",
        "locked": "🔒 आपकी 3 मुफ्त रिपोर्ट समाप्त हो गई हैं! अनलिमिटेड रिपोर्ट के लिए बाईं ओर Pro Plan लें।",
        "paste_warn": "कृपया वीडियो लिंक पेस्ट करें।"
    },
    "Tamil": {
        "free_left": "{n}/3 இலவச அறிக்கைகள் உள்ளன",
        "free_over": "0/3 இலவச அறிக்கைகள் முடிந்தன — Pro பெறவும்",
        "login_prompt": "3 இலவச அறிக்கைகளைப் பெற Gmail அல்லது Mail ID மூலம் உள்நுழையவும்:",
        "otp_sent": "{email} க்கு 6-இலக்க OTP அனுப்பப்பட்டது! Inbox / Spam பார்க்கவும்.",
        "otp_enter": "6-இலக்க OTP ஐ உள்ளிடவும்:",
        "otp_btn": "OTP சரிபார்க்கவும் ✅",
        "otp_err": "❌ தவறான OTP! மீண்டும் சரிபார்க்கவும்.",
        "send_otp": "OTP அனுப்பு 📩",
        "gen_btn": "வளர்ச்சி அறிக்கையை உருவாக்கவும் 🔍",
        "fetching": "🔄 வீடியோ விவரங்கள் சேகரிக்கப்படுகின்றன... ⏳",
        "generating": "⚡ அறிக்கை தயாராகிறது... ⏳",
        "done": "✅ வளர்ச்சி அறிக்கை தயாராகிவிட்டது!",
        "download": "📥 முழு அறிக்கையை பதிவிறக்கவும் (.txt)",
        "locked": "🔒 உங்கள் 3 இலவச அறிக்கைகள் முடிந்துவிட்டன! இடதுபுறம் உள்ள Pro Plan பெறவும்.",
        "paste_warn": "வீடியோ இணைப்பை ஒட்டவும்."
    },
    "Kannada": {
        "free_left": "{n}/3 ಉಚಿತ ವರದಿಗಳು ಬಾಕಿ ಇವೆ",
        "free_over": "0/3 ಉಚಿತ ವರದಿಗಳು ಮುಗಿದಿವೆ — Pro ಪಡೆಯಿರಿ",
        "login_prompt": "3 ಉಚಿತ ವರದಿಗಳಿಗಾಗಿ Gmail ಅಥವಾ Mail ID ಮೂಲಕ ಲಾಗಿನ್ ಆಗಿ:",
        "otp_sent": "{email} ಗೆ 6-ಅಂಕಿಯ OTP ಕಳುಹಿಸಲಾಗಿದೆ! Inbox / Spam ಪರಿಶೀಲಿಸಿ.",
        "otp_enter": "6-ಅಂಕಿಯ OTP ನಮೂದಿಸಿ:",
        "otp_btn": "OTP ಪರಿಶೀಲಿಸಿ ✅",
        "otp_err": "❌ ತಪ್ಪಾದ OTP! ಮತ್ತೆ ಪರಿಶೀಲಿಸಿ.",
        "send_otp": "OTP ಕಳುಹಿಸಿ 📩",
        "gen_btn": "ಗ್ರೋತ್ ವರದಿ ರಚಿಸಿ 🔍",
        "fetching": "🔄 ವೀಡಿಯೊ ವಿವರಗಳನ್ನು ಪಡೆಯಲಾಗುತ್ತಿದೆ... ⏳",
        "generating": "⚡ ವರದಿ ಸಿದ್ಧವಾಗುತ್ತಿದೆ... ⏳",
        "done": "✅ ಗ್ರೋತ್ ಆಡಿಟ್ ವರದಿ ಸಿದ್ಧವಾಗಿದೆ!",
        "download": "📥 ಪೂರ್ಣ ವರದಿಯನ್ನು ಡೌನ್‌ಲೋಡ್ ಮಾಡಿ (.txt)",
        "locked": "🔒 ನಿಮ್ಮ 3 ಉಚಿತ ವರದಿಗಳು ಮುಗಿದಿವೆ! ಎಡಭಾಗದಲ್ಲಿ Pro Plan ಪಡೆಯಿರಿ.",
        "paste_warn": "ದಯವಿಟ್ಟು ವೀಡಿಯೊ ಲಿಂಕ್ ಅಂಟಿಸಿ."
    },
    "Malayalam": {
        "free_left": "{n}/3 സൗജന്യ റിപ്പോർട്ടുകൾ ബാക്കിയുണ്ട്",
        "free_over": "0/3 സൗജന്യ റിപ്പോർട്ടുകൾ തീർന്നു — Pro എടുക്കുക",
        "login_prompt": "3 സൗജന്യ റിപ്പോർട്ടുകൾക്കായി Gmail അല്ലെങ്കിൽ Mail ID ഉപയോഗിച്ച് ലോഗിൻ ചെയ്യുക:",
        "otp_sent": "{email} എന്നതിലേക്ക് 6-അക്ക OTP അയച്ചിട്ടുണ്ട്! Inbox / Spam പരിശോധിക്കുക.",
        "otp_enter": "6-അക്ക OTP നൽകുക:",
        "otp_btn": "OTP സ്ഥിരീകരിക്കുക ✅",
        "otp_err": "❌ തെറ്റായ OTP! വീണ്ടും പരിശോധിക്കുക.",
        "send_otp": "OTP അയക്കുക 📩",
        "gen_btn": "ഗ്രോത്ത് റിപ്പോർട്ട് നിർമ്മിക്കുക 🔍",
        "fetching": "🔄 വീഡിയോ വിവരങ്ങൾ ശേഖരിക്കുന്നു... ⏳",
        "generating": "⚡ റിപ്പോർട്ട് തയ്യാറാകുന്നു... ⏳",
        "done": "✅ ഗ്രോത്ത് ഓഡിറ്റ് റിപ്പോർട്ട് തയ്യാറായി!",
        "download": "📥 പൂർണ്ണ റിപ്പോർട്ട് ഡൗൺലോഡ് ചെയ്യുക (.txt)",
        "locked": "🔒 നിങ്ങളുടെ 3 സൗജന്യ റിപ്പോർട്ടുകൾ തീർന്നു! ഇടതുവശത്ത് Pro Plan എടുക്കുക.",
        "paste_warn": "ദയവായി വീഡിയോ ലിങ്ക് പേസ്റ്റ് ചെയ്യുക."
    },
    "Marathi": {
        "free_left": "{n}/3 मोफत रिपोर्ट शिल्लक आहेत",
        "free_over": "0/3 मोफत रिपोर्ट संपले — Pro घ्या",
        "login_prompt": "3 मोफत रिपोर्ट मिळवण्यासाठी Gmail किंवा Mail ID ने लॉगिन करा:",
        "otp_sent": "{email} वर 6-अंकी OTP पाठवला आहे! Inbox / Spam तपासा.",
        "otp_enter": "6-अंकी OTP टाका:",
        "otp_btn": "OTP तपासा ✅",
        "otp_err": "❌ चुकीचा OTP! कृपया पुन्हा तपासा.",
        "send_otp": "OTP पाठवा 📩",
        "gen_btn": "ग्रोथ रिपोर्ट तयार करा 🔍",
        "fetching": "🔄 व्हिडिओ माहिती गोळा करत आहे... ⏳",
        "generating": "⚡ रिपोर्ट तयार होत आहे... ⏳",
        "done": "✅ ग्रोथ ऑडिट रिपोर्ट तयार आहे!",
        "download": "📥 पूर्ण रिपोर्ट डाउनलोड करा (.txt)",
        "locked": "🔒 तुमचे 3 मोफत रिपोर्ट संपले आहेत! डावीकडे Pro Plan घ्या.",
        "paste_warn": "कृपया व्हिडिओ लिंक पेस्ट करा."
    },
    "Bengali": {
        "free_left": "{n}/3 বিনামূল্যে রিপোর্ট বাকি আছে",
        "free_over": "0/3 বিনামূল্যে রিপোর্ট শেষ — Pro নিন",
        "login_prompt": "3টি বিনামূল্যে রিপোর্ট পেতে Gmail বা Mail ID দিয়ে লগইন করুন:",
        "otp_sent": "{email}-এ ৬-সংখ্যার OTP পাঠানো হয়েছে! Inbox / Spam চেক করুন।",
        "otp_enter": "৬-সংখ্যার OTP লিখুন:",
        "otp_btn": "OTP যাচাই করুন ✅",
        "otp_err": "❌ ভুল OTP! আবার চেষ্টা করুন।",
        "send_otp": "OTP পাঠান 📩",
        "gen_btn": "গ্রোথ রিপোর্ট তৈরি করুন 🔍",
        "fetching": "🔄 ভিডিওর তথ্য সংগ্রহ করা হচ্ছে... ⏳",
        "generating": "⚡ রিপোর্ট তৈরি হচ্ছে... ⏳",
        "done": "✅ গ্রোথ অডিট রিপোর্ট তৈরি!",
        "download": "📥 সম্পূর্ণ রিপোর্ট ডাউনলোড করুন (.txt)",
        "locked": "🔒 আপনার ৩টি বিনামূল্যে রিপোর্ট শেষ হয়েছে! বাম দিকে Pro Plan নিন।",
        "paste_warn": "অনুগ্রহ করে ভিডিও লিঙ্ক পেস্ট করুন।"
    },
    "Gujarati": {
        "free_left": "{n}/3 મફત રિપોર્ટ બાકી છે",
        "free_over": "0/3 મફત રિપોર્ટ પૂરા થયા — Pro લો",
        "login_prompt": "3 મફત રિપોર્ટ મેળવવા Gmail અથવા Mail ID થી લોગિન કરો:",
        "otp_sent": "{email} પર 6-અંકનો OTP મોકલવામાં આવ્યો છે! Inbox / Spam તપાસો.",
        "otp_enter": "6-અંકનો OTP દાખલ કરો:",
        "otp_btn": "OTP ચકાસો ✅",
        "otp_err": "❌ ખોટો OTP! ફરી પ્રયાસ કરો.",
        "send_otp": "OTP મોકલો 📩",
        "gen_btn": "ગ્રોથ રિપોર્ટ બનાવો 🔍",
        "fetching": "🔄 વિડિઓ વિગતો મેળવી રહ્યું છે... ⏳",
        "generating": "⚡ રિપોર્ટ તૈયાર થઈ રહ્યો છે... ⏳",
        "done": "✅ ગ્રોથ ઓડિટ રિપોર્ટ તૈયાર છે!",
        "download": "📥 સંપૂર્ણ રિપોર્ટ ડાઉનલોડ કરો (.txt)",
        "locked": "🔒 તમારા 3 મફત રિપોર્ટ પૂરા થઈ ગયા છે! ડાબી બાજુ Pro Plan લો.",
        "paste_warn": "કૃપા કરીને વિડિઓ લિંક પેસ્ટ કરો."
    },
    "Punjabi": {
        "free_left": "{n}/3 ਮੁਫ਼ਤ ਰਿਪੋਰਟਾਂ ਬਾਕੀ ਹਨ",
        "free_over": "0/3 ਮੁਫ਼ਤ ਰਿਪੋਰਟਾਂ ਖਤਮ — Pro ਲਓ",
        "login_prompt": "3 ਮੁਫ਼ਤ ਰਿਪੋਰਟਾਂ ਲੈਣ ਲਈ Gmail ਜਾਂ Mail ID ਨਾਲ ਲੌਗਇਨ ਕਰੋ:",
        "otp_sent": "{email} 'ਤੇ 6-ਅੰਕਾਂ ਦਾ OTP ਭੇਜਿਆ ਗਿਆ ਹੈ! Inbox / Spam ਚੈੱਕ ਕਰੋ।",
        "otp_enter": "6-ਅੰਕਾਂ ਦਾ OTP ਦਰਜ ਕਰੋ:",
        "otp_btn": "OTP ਪੁਸ਼ਟੀ ਕਰੋ ✅",
        "otp_err": "❌ ਗਲਤ OTP! ਦੁਬਾਰਾ ਜਾਂਚ ਕਰੋ।",
        "send_otp": "OTP ਭੇਜੋ 📩",
        "gen_btn": "ਗਰੋਥ ਰਿਪੋਰਟ ਬਣਾਓ 🔍",
        "fetching": "🔄 ਵੀਡੀਓ ਵੇਰਵੇ ਲਏ ਜਾ ਰਹੇ ਹਨ... ⏳",
        "generating": "⚡ ਰਿਪੋਰਟ ਤਿਆਰ ਹੋ ਰਹੀ ਹੈ... ⏳",
        "done": "✅ ਗਰੋਥ ਆਡਿਟ ਰਿਪੋਰਟ ਤਿਆਰ ਹੈ!",
        "download": "📥 ਪੂਰੀ ਰਿਪੋਰਟ ਡਾਊਨਲੋਡ ਕਰੋ (.txt)",
        "locked": "🔒 ਤੁਹਾਡੀਆਂ 3 ਮੁਫ਼ਤ ਰਿਪੋਰਟਾਂ ਖਤਮ ਹੋ ਗਈਆਂ ਹਨ! ਖੱਬੇ ਪਾਸੇ Pro Plan ਲਓ।",
        "paste_warn": "ਕਿਰਪਾ ਕਰਕੇ ਵੀਡੀਓ ਲਿੰક ਪੇસ્ટ ਕਰੋ।"
    },
    "Odia": {
        "free_left": "{n}/3 ମାଗଣା ରିପୋର୍ଟ ବାକି ଅଛି",
        "free_over": "0/3 ମାଗଣା ରିପୋର୍ଟ ଶେଷ — Pro ନିଅନ୍ତୁ",
        "login_prompt": "3ଟି ମାଗଣା ରିପୋର୍ଟ ପାଇବା ପାଇଁ Gmail କିମ୍ବା Mail ID ରେ ଲଗଇନ୍ କରନ୍ତୁ:",
        "otp_sent": "{email} କୁ 6-ଅଙ୍କ ବିଶିଷ୍ଟ OTP ପଠାଯାଇଛି! Inbox / Spam ଯାଞ୍ଚ କରନ୍ତୁ।",
        "otp_enter": "6-ଅଙ୍କ ବିଶିଷ୍ଟ OTP ଦିଅନ୍ତୁ:",
        "otp_btn": "OTP ଯାଞ୍ଚ କରନ୍ତୁ ✅",
        "otp_err": "❌ ଭୁଲ OTP! ପୁଣି ଯାଞ୍ଚ କରନ୍ତୁ।",
        "send_otp": "OTP ପଠାନ୍ତୁ 📩",
        "gen_btn": "ଗ୍ରୋଥ୍ ରିପୋର୍ଟ ତିଆରି କରନ୍ତୁ 🔍",
        "fetching": "🔄 ଭିଡିଓ ତଥ୍ୟ ସଂଗ୍ରହ ହେଉଛି... ⏳",
        "generating": "⚡ ରିପୋର୍ଟ ପ୍ରସ୍ତୁତ ହେଉଛି... ⏳",
        "done": "✅ ଗ୍ରୋଥ୍ ଅଡିଟ୍ ରିପୋର୍ଟ ପ୍ରସ୍ତୁତ!",
        "download": "📥 ସମ୍ପୂର୍ଣ୍ଣ ରିପୋର୍ଟ ଡାଉନଲୋଡ୍ କରନ୍ତୁ (.txt)",
        "locked": "🔒 ଆପଣଙ୍କର 3ଟି ମାଗଣା ରିପୋର୍ଟ ଶେଷ ହୋଇଯାଇଛି! ବାମ ପଟେ Pro Plan ନିଅନ୍ତୁ।",
        "paste_warn": "ଦୟାକରି ଭିଡିଓ ଲିଙ୍କ୍ ପେଷ୍ଟ କରନ୍ତୁ।"
    },
    "Assamese": {
        "free_left": "{n}/3 বিনামূলীয়া ৰিপৰ্ট বাকী আছে",
        "free_over": "0/3 বিনামূলীয়া ৰিপৰ্ট শেষ — Pro লওক",
        "login_prompt": "3টা বিনামূলীয়া ৰিপৰ্ট পাবলৈ Gmail বা Mail ID ৰে লগইন কৰক:",
        "otp_sent": "{email} লৈ ৬-টা সংখ্যাৰ OTP পঠিওৱা হৈছে! Inbox / Spam চাওক।",
        "otp_enter": "৬-টা সংখ্যাৰ OTP লিখক:",
        "otp_btn": "OTP নিশ্চিত কৰক ✅",
        "otp_err": "❌ ভুল OTP! পুনৰ চাওক।",
        "send_otp": "OTP পঠিয়াওক 📩",
        "gen_btn": "গ্ৰোথ ৰিপৰ্ট বনাওক 🔍",
        "fetching": "🔄 ভিডিঅ'ৰ তথ্য সংগ্ৰহ কৰা হৈছে... ⏳",
        "generating": "⚡ ৰিপৰ্ট প্ৰস্তুত হৈ আছে... ⏳",
        "done": "✅ গ্ৰোথ অডিট ৰিপৰ্ট সাজু হৈছে!",
        "download": "📥 সম্পূৰ্ণ ৰিপৰ্ট ডাউনলোড কৰক (.txt)",
        "locked": "🔒 আপোনাৰ ৩টা বিনামূলীয়া ৰিপৰ্ট শেষ হৈছে! বাঁওফালে Pro Plan লওক।",
        "paste_warn": "অনুগ্ৰহ কৰি ভিডিঅ' লিংক পেষ্ট কৰক।"
    },
    "Urdu": {
        "free_left": "{n}/3 مفت رپورٹس باقی ہیں",
        "free_over": "0/3 مفت رپورٹس ختم — Pro لیں",
        "login_prompt": "3 مفت رپورٹس حاصل کرنے کے لیے Gmail یا Mail ID سے لاگ ان کریں:",
        "otp_sent": "{email} پر 6 ہندسوں کا OTP بھیج دیا گیا ہے! Inbox / Spam چیک کریں۔",
        "otp_enter": "6 ہندسوں کا OTP درج کریں:",
        "otp_btn": "OTP کی تصدیق کریں ✅",
        "otp_err": "❌ غلط OTP! دوبارہ چیک کریں۔",
        "send_otp": "OTP بھیجیں 📩",
        "gen_btn": "گروتھ رپورٹ بنائیں 🔍",
        "fetching": "🔄 ویڈیو کی تفصیلات حاصل کی جا رہی ہیں... ⏳",
        "generating": "⚡ رپورٹ تیار ہو رہی ہے... ⏳",
        "done": "✅ گروتھ آڈٹ رپورٹ تیار ہے!",
        "download": "📥 مکمل رپورٹ ڈاؤن لوڈ کریں (.txt)",
        "locked": "🔒 آپ کی 3 مفت رپورٹس ختم ہو گئی ہیں! بائیں جانب Pro Plan لیں۔",
        "paste_warn": "براہ کرم ویڈیو لنک پیسٹ کریں۔"
    },
    "Bhojpuri": {
        "free_left": "{n}/3 मुफ्त रिपोर्ट बाचल बा",
        "free_over": "0/3 मुफ्त रिपोर्ट खतम — Pro लीं",
        "login_prompt": "3 मुफ्त रिपोर्ट खातिर Gmail या Mail ID से लॉगिन करीं:",
        "otp_sent": "{email} पर 6-अंक के OTP भेज दिहल गइल बा! Inbox / Spam देखीं।",
        "otp_enter": "6-अंक के OTP डालीं:",
        "otp_btn": "OTP सत्यापित करीं ✅",
        "otp_err": "❌ गलत OTP! फिर से जांचीं।",
        "send_otp": "OTP भेजीं 📩",
        "gen_btn": "ग्रोथ रिपोर्ट बनाईं 🔍",
        "fetching": "🔄 वीडियो के जानकारी लिहल जा रहल बा... ⏳",
        "generating": "⚡ रिपोर्ट तैयार हो रहल बा... ⏳",
        "done": "✅ ग्रोथ ऑडिट रिपोर्ट तैयार बा!",
        "download": "📥 पूरा रिपोर्ट डाउनलोड करीं (.txt)",
        "locked": "🔒 रउआ 3 मुफ्त रिपोर्ट खतम हो गइल बा! बायां तरफ Pro Plan लीं।",
        "paste_warn": "कृपया वीडियो लिंक पेस्ट करीं।"
    }
}

def get_ui_lang_key(selected_label, detected_lang=""):
    # If Auto-Detect is selected and we haven't detected a video language yet, default to English (never Telugu!)
    if "Auto-Detect" in selected_label:
        if not detected_lang:
            return "English"
        target = detected_lang
    else:
        target = selected_label

    t_low = target.lower()
    if "telugu" in t_low or "tenglish" in t_low:
        return "Telugu"
    if "hindi" in t_low or "hinglish" in t_low:
        return "Hindi"
    if "tamil" in t_low:
        return "Tamil"
    if "kannada" in t_low:
        return "Kannada"
    if "malayalam" in t_low:
        return "Malayalam"
    if "marathi" in t_low:
        return "Marathi"
    if "bengali" in t_low:
        return "Bengali"
    if "gujarati" in t_low:
        return "Gujarati"
    if "punjabi" in t_low:
        return "Punjabi"
    if "odia" in t_low:
        return "Odia"
    if "assamese" in t_low:
        return "Assamese"
    if "urdu" in t_low:
        return "Urdu"
    if "bhojpuri" in t_low:
        return "Bhojpuri"
    return "English"

def t(key, selected_label, detected_lang="", **kwargs):
    lk = get_ui_lang_key(selected_label, detected_lang)
    pack = UI_STRINGS.get(lk, UI_STRINGS["English"])
    txt = pack.get(key, UI_STRINGS["English"].get(key, ""))
    return txt.format(**kwargs) if kwargs else txt

# --- 5. COMPACT NO-SCROLL CSS & HIDE TOP-RIGHT TOOLBAR ---
st.markdown("""
<style>
    [data-testid="stToolbarActions"], [data-testid="stDecoration"], #MainMenu, footer {
        display: none !important;
        visibility: hidden !important;
    }
    [data-testid="stSidebarCollapsedControl"] {
        display: flex !important;
        visibility: visible !important;
        z-index: 99999 !important;
    }
    .block-container {
        padding-top: 0.7rem !important;
        padding-bottom: 0.5rem !important;
        max-width: 100% !important;
    }
    section[data-testid="stSidebar"] > div {
        padding-top: 0.6rem !important;
        padding-bottom: 0.4rem !important;
    }
    section[data-testid="stSidebar"] .stMarkdown p {
        margin-bottom: 0.25rem !important;
        font-size: 0.88rem !important;
    }
    section[data-testid="stSidebar"] hr {
        margin: 0.45rem 0 !important;
    }
    .center-banner {
        background: linear-gradient(135deg, #0b1324 0%, #162238 100%);
        border: 1px solid #26354d;
        border-radius: 12px;
        padding: 12px 18px;
        text-align: center;
        margin-bottom: 10px;
    }
    .brand-row {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        gap: 10px;
    }
    .brand-title {
        font-size: 1.65rem;
        font-weight: 800;
        color: #ffffff;
        margin: 0;
    }
    .india-badge {
        background: rgba(16, 185, 129, 0.16);
        border: 1px solid #10b981;
        color: #34d399;
        font-size: 0.78rem;
        font-weight: 700;
        padding: 3px 10px;
        border-radius: 20px;
    }
    .brand-sub {
        color: #94a3b8;
        font-size: 0.88rem;
        margin: 4px 0 0 0;
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
        background: #064e3b;
        border: 1px solid #10b981;
        color: #ecfdf5;
        padding: 8px 14px;
        border-radius: 8px;
        font-weight: 600;
        font-size: 0.9rem;
        display: inline-block;
    }
    div.stButton > button {
        height: 40px !important;
        padding-top: 0 !important;
        padding-bottom: 0 !important;
        font-weight: 600 !important;
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
    "ig_report": "",
    "tt_report": "",
    "detected_lang": ""
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# --- 7. CHECK GOOGLE OAUTH LOGIN ---
try:
    if hasattr(st, "user") and getattr(st.user, "is_logged_in", False):
        g_email = getattr(st.user, "email", "")
        if g_email:
            st.session_state.verified_email = g_email.strip().lower()
except Exception:
    pass

# --- 8. GOOGLE SHEET HELPERS (NO-CACHE LIVE SYNC) ---
def get_free_used_count(user_id):
    if not SHEET_API or not user_id:
        return 0
    try:
        r = requests.get(
            SHEET_API,
            params={"device": user_id, "_ts": int(time.time() * 1000)},
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
                params={"device": user_id, "inc": "1", "_ts": int(time.time() * 1000)},
                timeout=8,
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

qp_pid = st.query_params.get("razorpay_payment_id", "")
if qp_pid and not st.session_state.pro_unlocked:
    st_res = verify_payment_id(qp_pid, plan="1m")
    if st_res == "VALID":
        st.session_state.pro_unlocked = True
        st.session_state.pro_label = "PRO UNLIMITED ACTIVE"

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
        item = v_res["items"]
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
            "description": snip.get("description", "")[:1200],
            "tags": snip.get("tags", [])[:20],
            "views": int(stats.get("viewCount", 0)),
            "likes": int(stats.get("likeCount", 0)),
            "comment_count": int(stats.get("commentCount", 0)),
            "comments": comments
        }
    except Exception:
        return None

# --- 10. GEMINI 4-KEY SMART FAILOVER STREAMING ---
def clean_advisor_word(text):
    return text.replace("మెంటర్", "సలహాదారు").replace("స్ట్రాటజిస్ట్", "సలహాదారు")

def generate_report_stream(prompt):
    if not GEMINI_KEYS:
        raise RuntimeError("API Key missing in Secrets.")
    models_to_try = ["gemini-2.5-flash", "gemini-2.5-flash-lite"]
    last_err = ""
    for api_key in GEMINI_KEYS:
        try:
            client = genai.Client(api_key=api_key)
            for model_name in models_to_try:
                try:
                    response = client.models.generate_content_stream(
                        model=model_name,
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            temperature=0.80,
                            max_output_tokens=8192
                        )
                    )
                    yielded = False
                    for chunk in response:
                        if chunk.text:
                            yielded = True
                            yield clean_advisor_word(chunk.text)
                    if yielded:
                        return
                except Exception as me:
                    last_err = str(me)
                    continue
        except Exception as ke:
            last_err = str(ke)
            continue
    raise RuntimeError(f"AI server busy. Please retry in 5 seconds. ({last_err})")

# --- 11. SIDEBAR (COMPACT NO-SCROLL) ---
with st.sidebar:
    st.markdown("### ⚙️ Settings")
    report_lang = st.selectbox(
        "🔍 Type to Search Language (A–Z):",
        LANGUAGES_LIST,
        index=0
    )
    audience_scope = st.radio("Audience:", ["Regional", "Global", "Both"], horizontal=True, label_visibility="collapsed")

    st.divider()
    st.markdown("### 💎 Pro Plans")

    free_used = get_free_used_count(st.session_state.verified_email) if st.session_state.verified_email else 0
    free_left = max(0, 3 - free_used)

    if st.session_state.pro_unlocked:
        st.success(f"✅ {st.session_state.pro_label}")
    elif st.session_state.verified_email:
        if free_left > 0:
            st.info(f"🎁 {t('free_left', report_lang, st.session_state.detected_lang, n=free_left)}")
        else:
            st.error(f"🔒 {t('free_over', report_lang, st.session_state.detected_lang)}")
    else:
        st.info("🎁 Login for 3 Free Reports")

    st.markdown(f"• **1 Month:** ₹100 👉 [Pay ₹100]({RAZORPAY_1M})")
    st.markdown(f"• **12 Months:** ₹1,000 👉 [Pay ₹1,000]({RAZORPAY_12M})")

    plan_choice = st.radio("Plan:", ["1M (₹100)", "12M (₹1,000)"], horizontal=True, label_visibility="collapsed")
    pay_input = st.text_input("Payment ID:", placeholder="Paste Payment ID (pay_...)", label_visibility="collapsed")
    if st.button("Unlock Pro 🔓", use_container_width=True):
        if pay_input.strip():
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

    st.divider()
    st.caption("📩 support@aiengtel.com | © 2026 TrendSutra AI")

# --- 12. CENTERED LOGO HEADER ---
logo_html = ""
if os.path.exists("logo.png"):
    import base64
    with open("logo.png", "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    logo_html = f'<img src="data:image/png;base64,{b64}" width="36" height="36" style="border-radius:8px; vertical-align:middle;" />'

st.markdown(f"""
<div class="center-banner">
    <div class="brand-row">
        {logo_html}
        <span class="brand-title">TrendSutra AI</span>
        <span class="india-badge">🇮🇳 1 AI • 1 India</span>
    </div>
    <p class="brand-sub">A to Z Growth Analyzer in All 22 Indian Languages + Bhojpuri for YouTube, Instagram & TikTok</p>
</div>
""", unsafe_allow_html=True)

# --- 13. COMPACT SINGLE-ROW LOGIN BAR (ALIGNED & TRANSLATED) ---
if not st.session_state.verified_email and not st.session_state.pro_unlocked:
    st.caption(f"🔐 {t('login_prompt', report_lang)}")
    lc1, lc2, lc3, lc4 = st.columns([2.2, 0.4, 2.5, 1.5])
    with lc1:
        if st.button("🔵 Continue with Gmail", type="primary", use_container_width=True):
            try:
                st.login("google")
            except Exception as e:
                st.error(f"Google Login error: {e}")
    with lc2:
        st.markdown("<div style='text-align:center; padding-top:8px; color:#94a3b8; font-weight:700;'>OR</div>", unsafe_allow_html=True)
    with lc3:
        email_in = st.text_input("Mail ID", placeholder="Login with Mail ID (creator@gmail.com)", label_visibility="collapsed")
    with lc4:
        if st.button(t("send_otp", report_lang), use_container_width=True):
            clean_em = email_in.strip().lower()
            if "@" not in clean_em or "." not in clean_em.split("@")[-1]:
                st.error("❌ Invalid Email ID")
            elif clean_em.split("@")[-1] in TEMP_DOMAINS:
                st.error("❌ Temp email not allowed")
            else:
                code = str(random.randint(100000, 999999))
                ok, err_msg = send_otp_email(clean_em, code)
                if ok:
                    st.session_state.otp_code = code
                    st.session_state.otp_target = clean_em
                    st.success(f"✅ {t('otp_sent', report_lang, email=clean_em)}")
                else:
                    st.error(f"OTP Error: {err_msg}")

    if st.session_state.otp_target:
        oc1, oc2 = st.columns([3, 1.5])
        with oc1:
            otp_in = st.text_input("OTP", placeholder=t("otp_enter", report_lang), max_chars=6, label_visibility="collapsed")
        with oc2:
            if st.button(t("otp_btn", report_lang), type="primary", use_container_width=True):
                if otp_in.strip() == st.session_state.otp_code:
                    st.session_state.verified_email = st.session_state.otp_target
                    st.session_state.otp_code = ""
                    st.rerun()
                else:
                    st.error(t("otp_err", report_lang))
else:
    u_col1, u_col2 = st.columns([5, 1.2])
    with u_col1:
        if st.session_state.pro_unlocked:
            badge_txt = st.session_state.pro_label
        elif free_left > 0:
            badge_txt = t("free_left", report_lang, st.session_state.detected_lang, n=free_left)
        else:
            badge_txt = t("free_over", report_lang, st.session_state.detected_lang)
        st.markdown(f'<div class="status-strip">👤 Logged in as <b>{st.session_state.verified_email or "PRO User"}</b> &nbsp;|&nbsp; 🎁 <b>{badge_txt}</b></div>', unsafe_allow_html=True)
    with u_col2:
        if st.button("Logout 🚪", use_container_width=True):
            st.session_state.verified_email = ""
            st.session_state.pro_unlocked = False
            st.session_state.yt_report = ""
            st.session_state.detected_lang = ""
            try:
                if hasattr(st, "logout"):
                    st.logout()
            except Exception:
                pass
            st.rerun()

# --- 14. MAIN TABS ---
tab_yt, tab_ig, tab_tt = st.tabs(["📺 YouTube Analyzer", "📸 Instagram Reels Analyzer", "🎵 TikTok Analyzer"])

def build_language_instruction(selected_lang):
    if "Auto-Detect" in selected_lang:
        return (
            "1. First detect the exact spoken/written language of the video from its title, description, and comments.\n"
            "2. On the very first line of your output, write: 🌐 Detected Language: <Language Name in English>\n"
            "3. Write the ENTIRE report (including ALL 6 section headings and all content) in that detected language's NATIVE SCRIPT "
            "(for example: Telugu in తెలుగు script, Hindi in हिन्दी Devanagari script, Tamil in தமிழ் script, Urdu in اردو Nastaliq script, Kannada in ಕನ್ನಡ script, etc.). NEVER write Indian languages in Roman/English letters unless Hinglish or Tenglish is selected."
        )
    else:
        return (
            f"1. On the very first line of your output, write: 🌐 Selected Language: {selected_lang}\n"
            f"2. Write the ENTIRE report (including ALL 6 section headings and all content) strictly in **{selected_lang}** using its NATIVE SCRIPT "
            f"(for example: Tamil in தமிழ் script, Telugu in తెలుగు script, Hindi in हिन्दी Devanagari script, Urdu in اردو Nastaliq script, etc.). NEVER write headings in English when a regional language is selected."
        )

with tab_yt:
    yc1, yc2 = st.columns([4.2, 1.5])
    with yc1:
        yt_url = st.text_input("YT URL", placeholder="Paste YouTube Video or Shorts Link (https://youtu.be/...)", label_visibility="collapsed")
    with yc2:
        run_yt = st.button(t("gen_btn", report_lang, st.session_state.detected_lang), key="btn_yt", type="primary", use_container_width=True)

    yt_status = st.empty()

    if run_yt:
        if not st.session_state.verified_email and not st.session_state.pro_unlocked:
            st.warning(f"🔐 {t('login_prompt', report_lang)}")
        elif not yt_url.strip():
            st.warning(t("paste_warn", report_lang, st.session_state.detected_lang))
        elif not st.session_state.pro_unlocked and free_left <= 0:
            st.error(t("locked", report_lang, st.session_state.detected_lang))
        else:
            vid_id = extract_youtube_id(yt_url.strip())
            if not vid_id:
                st.error("❌ Invalid YouTube URL.")
            else:
                yt_status.markdown(f'<div class="loading-pill">{t("fetching", report_lang, st.session_state.detected_lang)}</div>', unsafe_allow_html=True)
                data = fetch_youtube_details(vid_id)
                if not data:
                    yt_status.empty()
                    st.error("❌ Could not fetch video details. Make sure video is Public.")
                else:
                    m1, m2, m3 = st.columns(3)
                    m1.metric("👀 Views", f"{data['views']:,}")
                    m2.metric("👍 Likes", f"{data['likes']:,}")
                    m3.metric("💬 Comments", f"{data['comment_count']:,}")

                    comments_block = "\n".join(data["comments"][:15]) if data["comments"] else "No public comments."
                    lang_rules = build_language_instruction(report_lang)
                    prompt = f"""
You are a warm, encouraging human social media growth advisor ("సలహాదారు").
Write a comprehensive, easy-to-understand 6-section growth audit report (1,100 to 1,400 words) for a **{audience_scope}** audience using simple spoken words.

LANGUAGE & SCRIPT RULES (CRITICAL):
{lang_rules}

VIDEO DATA:
- Channel: {data['channel']}
- Title: {data['title']}
- Views: {data['views']:,} | Likes: {data['likes']:,} | Comments: {data['comment_count']:,}
- Description: {data['description']}
- Tags: {', '.join(data['tags'])}
- Real Audience Comments:
{comments_block}

SECTIONS TO INCLUDE (TRANSLATE ALL 6 HEADINGS INTO THE TARGET LANGUAGE NATIVE SCRIPT):
### 🎬 1. Video Story Recap & Creator Appreciation
- Warmly retell the core story/message of this video so the creator feels you truly understood their work, then praise their strengths.
### 💬 2. Real Audience Comments Translated & Reply Strategy
- Quote 4 to 5 real viewer comments translated naturally into the target language, explain audience sentiment, and give 3 ready-to-copy reply templates.
### 🔥 3. 3 Next Viral Video Ideas + 5-Second Opening Hooks
- Give 3 fresh follow-up video ideas with exact word-for-word 5-second opening hooks and thumbnail concepts.
### 🎯 4. Copy-Paste SEO Makeover (3 High-CTR Titles, Description & 15 Tags)
### 💰 5. Monetization & Brand Earning Blueprint
### 📅 6. Step-by-Step 30-Day Growth Action Plan
"""
                    yt_status.markdown(f'<div class="loading-pill">{t("generating", report_lang, st.session_state.detected_lang)}</div>', unsafe_allow_html=True)
                    report_box = st.empty()
                    full_text = ""
                    try:
                        for piece in generate_report_stream(prompt):
                            full_text += piece
                            report_box.markdown(full_text)
                            if not st.session_state.detected_lang and "\n" in full_text:
                                first_line = full_text.split("\n")
                                if "Detected Language:" in first_line:
                                    st.session_state.detected_lang = first_line.split(":", 1)[1].strip()
                                    yt_status.markdown(f'<div class="loading-pill">{t("generating", report_lang, st.session_state.detected_lang)}</div>', unsafe_allow_html=True)
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
        st.success(t("done", report_lang, st.session_state.detected_lang))
        st.markdown(st.session_state.yt_report)
        st.download_button(
            t("download", report_lang, st.session_state.detected_lang),
            data=st.session_state.yt_report,
            file_name=f"TrendSutra_YT_{st.session_state.yt_vid_id or 'Report'}.txt",
            mime="text/plain",
            use_container_width=True
        )

with tab_ig:
    ic1, ic2 = st.columns([4.2, 1.5])
    with ic1:
        ig_url = st.text_input("IG URL", placeholder="Paste Instagram Reel Link (https://www.instagram.com/reel/...)", label_visibility="collapsed")
    with ic2:
        run_ig = st.button(t("gen_btn", report_lang, st.session_state.detected_lang), key="btn_ig", type="primary", use_container_width=True)

    ig_status = st.empty()
    if run_ig:
        if not st.session_state.verified_email and not st.session_state.pro_unlocked:
            st.warning(f"🔐 {t('login_prompt', report_lang)}")
        elif not ig_url.strip():
            st.warning(t("paste_warn", report_lang, st.session_state.detected_lang))
        elif not st.session_state.pro_unlocked and free_left <= 0:
            st.error(t("locked", report_lang, st.session_state.detected_lang))
        else:
            ig_status.markdown(f'<div class="loading-pill">{t("generating", report_lang, st.session_state.detected_lang)}</div>', unsafe_allow_html=True)
            lang_rules = build_language_instruction(report_lang)
            ig_prompt = f"""
You are a warm, encouraging human Instagram Reels growth advisor.
Write a 6-section Instagram Reels growth audit (1,000+ words) for a **{audience_scope}** audience.
{lang_rules}
Reel Link: {ig_url.strip()}
Include 6 sections (headings in target language native script): 1. Creator Appreciation & Reel Strategy, 2. Watch-Time & Retention Hook, 3. 3 Viral Follow-Up Ideas + 3-Sec Hooks, 4. Copy-Paste Caption & 15 Hashtags, 5. Brand Monetization, 6. 30-Day Growth Plan.
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
        st.success(t("done", report_lang, st.session_state.detected_lang))
        st.markdown(st.session_state.ig_report)
        st.download_button(
            t("download", report_lang, st.session_state.detected_lang),
            data=st.session_state.ig_report,
            file_name="TrendSutra_Instagram_Report.txt",
            mime="text/plain",
            use_container_width=True
        )

with tab_tt:
    tc1, tc2 = st.columns([4.2, 1.5])
    with tc1:
        tt_url = st.text_input("TT URL", placeholder="Paste TikTok Video Link (https://www.tiktok.com/...)", label_visibility="collapsed")
    with tc2:
        run_tt = st.button(t("gen_btn", report_lang, st.session_state.detected_lang), key="btn_tt", type="primary", use_container_width=True)

    tt_status = st.empty()
    if run_tt:
        if not st.session_state.verified_email and not st.session_state.pro_unlocked:
            st.warning(f"🔐 {t('login_prompt', report_lang)}")
        elif not tt_url.strip():
            st.warning(t("paste_warn", report_lang, st.session_state.detected_lang))
        elif not st.session_state.pro_unlocked and free_left <= 0:
            st.error(t("locked", report_lang, st.session_state.detected_lang))
        else:
            tt_status.markdown(f'<div class="loading-pill">{t("generating", report_lang, st.session_state.detected_lang)}</div>', unsafe_allow_html=True)
            lang_rules = build_language_instruction(report_lang)
            tt_prompt = f"""
You are a warm, encouraging human TikTok growth advisor.
Write a 6-section TikTok growth audit (1,000+ words) for a **{audience_scope}** audience.
{lang_rules}
TikTok Link: {tt_url.strip()}
Include 6 sections (headings in target language native script): 1. Creator Appreciation & Viral Potential, 2. Completion Rate & Loop Hook, 3. 3 Viral Follow-Up Ideas + 3-Sec Hooks, 4. Copy-Paste Caption & 15 Hashtags, 5. Creator Rewards & Monetization, 6. 30-Day Growth Plan.
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
        st.success(t("done", report_lang, st.session_state.detected_lang))
        st.markdown(st.session_state.tt_report)
        st.download_button(
            t("download", report_lang, st.session_state.detected_lang),
            data=st.session_state.tt_report,
            file_name="TrendSutra_TikTok_Report.txt",
            mime="text/plain",
            use_container_width=True
        )
