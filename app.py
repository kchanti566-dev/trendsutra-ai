import streamlit as st
from google import genai
from google.genai import types
from googleapiclient.discovery import build
import re
import os
import time
import base64
import requests
import random
import smtplib
from email.mime.text import MIMEText
from PIL import Image

st.set_page_config(page_title="TrendSutra AI - 1 AI • 1 India", page_icon="logo.png" if os.path.exists("logo.png") else "📈", layout="wide")

FREE_KEYS = []
for k in ["GEMINI_API_KEY_4", "GEMINI_API_KEY_3", "GEMINI_API_KEY_2"]:
    v = str(st.secrets.get(k, "")).strip()
    if v and v not in FREE_KEYS:
        FREE_KEYS.append(v)
PAID_KEY = str(st.secrets.get("GEMINI_API_KEY", "")).strip()
ALL_GEMINI_KEYS = FREE_KEYS + ([PAID_KEY] if PAID_KEY and PAID_KEY not in FREE_KEYS else [])

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

LANGUAGES_AZ = [
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
    "Kashmiri (کٲشُر)",
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

UI_STRINGS = {
    "English": {
        "free_left": "🎁 {n}/3 Free Reports Left",
        "free_over": "🔒 0/3 Free Reports Left (Upgrade to Pro)",
        "login_prompt": "🎁 Login to get 3 Free Growth Reports",
        "send_otp": "Send OTP 📩",
        "otp_sent": "✅ 6-digit OTP sent to {email}! Check Inbox / Spam.",
        "verify_otp": "Verify OTP ✅",
        "gen_btn": "Generate Growth Report 🔍",
        "fetching": "🔄 Fetching video details & comments... ⏳",
        "generating": "⚡ Generating report... ⏳",
        "ready": "✅ Growth Audit Report Ready!",
        "download": "📥 Download Complete Report (.txt)",
        "limit_err": "🔒 Your 3 free reports are completed! Please choose a Pro Plan on the left."
    },
    "Telugu": {
        "free_left": "🎁 {n}/3 ఉచిత రిపోర్ట్‌లు మిగిలాయి",
        "free_over": "🔒 0/3 ఉచిత రిపోర్ట్‌లు మిగిలాయి (Pro ప్లాన్ తీసుకోండి)",
        "login_prompt": "🎁 3 ఉచిత గ్రోత్ రిపోర్ట్‌ల కోసం లాగిన్ అవ్వండి",
        "send_otp": "OTP పంపండి 📩",
        "otp_sent": "✅ {email} కి 6-అంకెల OTP పంపబడింది! ఇన్‌బాక్స్ / Spam చూడండి.",
        "verify_otp": "OTP నిర్ధారించండి ✅",
        "gen_btn": "గ్రోత్ రిపోర్ట్ తయారు చేయండి 🔍",
        "fetching": "🔄 వీడియో వివరాలు & కామెంట్లు సేకరిస్తోంది... ⏳",
        "generating": "⚡ రిపోర్ట్ తయారవుతోంది... ⏳",
        "ready": "✅ గ్రోత్ ఆడిట్ రిపోర్ట్ సిద్ధమైంది!",
        "download": "📥 పూర్తి రిపోర్ట్ డౌన్‌లోడ్ చేయండి (.txt)",
        "limit_err": "🔒 మీ 3 ఉచిత రిపోర్ట్‌లు పూర్తయ్యాయి! అన్‌లిమిటెడ్ కోసం ఎడమ వైపు Pro Plan తీసుకోండి."
    },
    "Hindi": {
        "free_left": "🎁 {n}/3 मुफ्त रिपोर्ट बाकी हैं",
        "free_over": "🔒 0/3 मुफ्त रिपोर्ट बाकी हैं (Pro प्लान लें)",
        "login_prompt": "🎁 3 मुफ्त ग्रोथ रिपोर्ट के लिए लॉगिन करें",
        "send_otp": "OTP भेजें 📩",
        "otp_sent": "✅ {email} पर 6-अंकों का OTP भेजा गया है! Inbox / Spam देखें।",
        "verify_otp": "OTP सत्यापित करें ✅",
        "gen_btn": "ग्रोथ रिपोर्ट बनाएं 🔍",
        "fetching": "🔄 वीडियो विवरण और कमेंट्स लिए जा रहे हैं... ⏳",
        "generating": "⚡ रिपोर्ट तैयार हो रही है... ⏳",
        "ready": "✅ ग्रोथ ऑडिट रिपोर्ट तैयार है!",
        "download": "📥 पूरी रिपोर्ट डाउनलोड करें (.txt)",
        "limit_err": "🔒 आपकी 3 मुफ्त रिपोर्ट पूरी हो गई हैं! अनलिमिटेड के लिए बाईं ओर Pro Plan चुनें।"
    },
    "Tamil": {
        "free_left": "🎁 {n}/3 இலவச அறிக்கைகள் உள்ளன",
        "free_over": "🔒 0/3 இலவச அறிக்கைகள் உள்ளன (Pro திட்டம் பெறவும்)",
        "login_prompt": "🎁 3 இலவச வளர்ச்சி அறிக்கைகளுக்கு உள்நுழையவும்",
        "send_otp": "OTP அனுப்பு 📩",
        "otp_sent": "✅ {email} க்கு 6-இலக்க OTP அனுப்பப்பட்டது! Inbox / Spam பார்க்கவும்.",
        "verify_otp": "OTP சரிபார் ✅",
        "gen_btn": "வளர்ச்சி அறிக்கையை உருவாக்கு 🔍",
        "fetching": "🔄 வீடியோ விவரங்கள் சேகரிக்கப்படுகின்றன... ⏳",
        "generating": "⚡ அறிக்கை தயாராகிறது... ⏳",
        "ready": "✅ வளர்ச்சி அறிக்கை தயார்!",
        "download": "📥 முழு அறிக்கையைப் பதிவிறக்கவும் (.txt)",
        "limit_err": "🔒 உங்கள் 3 இலவச அறிக்கைகள் முடிந்துவிட்டன! இடதுபுறம் Pro Plan தேர்வு செய்யவும்."
    },
    "Kannada": {
        "free_left": "🎁 {n}/3 ಉಚಿತ ವರದಿಗಳು ಬಾಕಿ ಇವೆ",
        "free_over": "🔒 0/3 ಉಚಿತ ವರದಿಗಳು ಬಾಕಿ ಇವೆ (Pro ಪ್ಲಾನ್ ಪಡೆಯಿರಿ)",
        "login_prompt": "🎁 3 ಉಚಿತ ಬೆಳವಣಿಗೆ ವರದಿಗಳಿಗಾಗಿ ಲಾಗಿನ್ ಮಾಡಿ",
        "send_otp": "OTP ಕಳುಹಿಸಿ 📩",
        "otp_sent": "✅ {email} ಗೆ 6-ಅಂಕಿಯ OTP ಕಳುಹಿಸಲಾಗಿದೆ! Inbox / Spam ಪರಿಶೀಲಿಸಿ.",
        "verify_otp": "OTP ದೃಢೀಕರಿಸಿ ✅",
        "gen_btn": "ಬೆಳವಣಿಗೆ ವರದಿ ತಯಾರಿಸಿ 🔍",
        "fetching": "🔄 ವೀಡಿಯೊ ವಿವರಗಳನ್ನು ಸಂಗ್ರಹಿಸಲಾಗುತ್ತಿದೆ... ⏳",
        "generating": "⚡ ವರದಿ ತಯಾರಾಗುತ್ತಿದೆ... ⏳",
        "ready": "✅ ಬೆಳವಣಿಗೆ ವರದಿ ಸಿದ್ಧವಾಗಿದೆ!",
        "download": "📥 ಸಂಪೂರ್ಣ ವರದಿ ಡೌನ್‌ಲೋಡ್ ಮಾಡಿ (.txt)",
        "limit_err": "🔒 ನಿಮ್ಮ 3 ಉಚಿತ ವರದಿಗಳು ಪೂರ್ಣಗೊಂಡಿವೆ! ಎಡಭಾಗದಲ್ಲಿ Pro Plan ಆಯ್ಕೆಮಾಡಿ."
    },
    "Malayalam": {
        "free_left": "🎁 {n}/3 സൗജന്യ റിപ്പോർട്ടുകൾ ബാക്കിയുണ്ട്",
        "free_over": "🔒 0/3 സൗജന്യ റിപ്പോർട്ടുകൾ ബാക്കിയുണ്ട് (Pro പ്ലാൻ എടുക്കുക)",
        "login_prompt": "🎁 3 സൗജന്യ റിപ്പോർട്ടുകൾക്കായി ലോഗിൻ ചെയ്യുക",
        "send_otp": "OTP അയക്കുക 📩",
        "otp_sent": "✅ {email} ലേക്ക് 6-അക്ക OTP അയച്ചു! Inbox / Spam പരിശോധിക്കുക.",
        "verify_otp": "OTP സ്ഥിരീകരിക്കുക ✅",
        "gen_btn": "ഗ്രോത്ത് റിപ്പോർട്ട് തയ്യാറാക്കുക 🔍",
        "fetching": "🔄 വീഡിയോ വിവരങ്ങൾ ശേഖരിക്കുന്നു... ⏳",
        "generating": "⚡ റിപ്പോർട്ട് തയ്യാറാകുന്നു... ⏳",
        "ready": "✅ ഗ്രോത്ത് ഓഡിറ്റ് റിപ്പോർട്ട് തയ്യാറായി!",
        "download": "📥 പൂർണ്ണ റിപ്പോർട്ട് ഡൗൺലോഡ് ചെയ്യുക (.txt)",
        "limit_err": "🔒 നിങ്ങളുടെ 3 സൗജന്യ റിപ്പോർട്ടുകൾ പൂർത്തിയായി! ഇടതുവശത്ത് Pro Plan തിരഞ്ഞെടുക്കുക."
    },
    "Marathi": {
        "free_left": "🎁 {n}/3 मोफत रिपोर्ट शिल्लक आहेत",
        "free_over": "🔒 0/3 मोफत रिपोर्ट शिल्लक आहेत (Pro प्लॅन घ्या)",
        "login_prompt": "🎁 3 मोफत ग्रोथ रिपोर्टसाठी लॉगिन करा",
        "send_otp": "OTP पाठवा 📩",
        "otp_sent": "✅ {email} वर 6-अंकी OTP पाठवला आहे! Inbox / Spam तपासा.",
        "verify_otp": "OTP सत्यापित करा ✅",
        "gen_btn": "ग्रोथ रिपोर्ट तयार करा 🔍",
        "fetching": "🔄 व्हिडिओ माहिती गोळा करत आहे... ⏳",
        "generating": "⚡ रिपोर्ट तयार होत आहे... ⏳",
        "ready": "✅ ग्रोथ ऑडिट रिपोर्ट तयार आहे!",
        "download": "📥 संपूर्ण रिपोर्ट डाउनलोड करा (.txt)",
        "limit_err": "🔒 तुमचे 3 मोफत रिपोर्ट पूर्ण झाले आहेत! डावीकडे Pro Plan निवडा."
    },
    "Bengali": {
        "free_left": "🎁 {n}/3 বিনামূল্যে রিপোর্ট বাকি আছে",
        "free_over": "🔒 0/3 বিনামূল্যে রিপোর্ট বাকি আছে (Pro প্ল্যান নিন)",
        "login_prompt": "🎁 ৩টি বিনামূল্যে রিপোর্টের জন্য লগইন করুন",
        "send_otp": "OTP পাঠান 📩",
        "otp_sent": "✅ {email}-এ ৬-সংখ্যার OTP পাঠানো হয়েছে! Inbox / Spam দেখুন।",
        "verify_otp": "OTP যাচাই করুন ✅",
        "gen_btn": "গ্রোথ রিপোর্ট তৈরি করুন 🔍",
        "fetching": "🔄 ভিডিওর তথ্য সংগ্রহ করা হচ্ছে... ⏳",
        "generating": "⚡ রিপোর্ট তৈরি হচ্ছে... ⏳",
        "ready": "✅ গ্রোথ অডিট রিপোর্ট তৈরি!",
        "download": "📥 সম্পূর্ণ রিপোর্ট ডাউনলোড করুন (.txt)",
        "limit_err": "🔒 আপনার ৩টি বিনামূল্যে রিপোর্ট শেষ হয়েছে! বাম দিকে Pro Plan বেছে নিন।"
    },
    "Gujarati": {
        "free_left": "🎁 {n}/3 મફત રિપોર્ટ બાકી છે",
        "free_over": "🔒 0/3 મફત રિપોર્ટ બાકી છે (Pro પ્લાન લો)",
        "login_prompt": "🎁 3 મફત ગ્રોથ રિપોર્ટ માટે લોગિન કરો",
        "send_otp": "OTP મોકલો 📩",
        "otp_sent": "✅ {email} પર 6-અંકનો OTP મોકલવામાં આવ્યો છે! Inbox / Spam જુઓ.",
        "verify_otp": "OTP ચકાસો ✅",
        "gen_btn": "ગ્રોથ રિપોર્ટ બનાવો 🔍",
        "fetching": "🔄 વિડિયો વિગતો મેળવવામાં આવી રહી છે... ⏳",
        "generating": "⚡ રિપોર્ટ તૈયાર થઈ રહ્યો છે... ⏳",
        "ready": "✅ ગ્રોથ ઓડિટ રિપોર્ટ તૈયાર છે!",
        "download": "📥 સંપૂર્ણ રિપોર્ટ ડાઉનલોડ કરો (.txt)",
        "limit_err": "🔒 તમારા 3 મફત રિપોર્ટ પૂરા થઈ ગયા છે! ડાબી બાજુ Pro Plan પસંદ કરો."
    },
    "Punjabi": {
        "free_left": "🎁 {n}/3 ਮੁਫ਼ਤ ਰਿਪੋਰਟਾਂ ਬਾਕੀ ਹਨ",
        "free_over": "🔒 0/3 ਮੁਫ਼ਤ ਰਿਪੋਰਟਾਂ ਬਾਕੀ ਹਨ (Pro ਪਲਾਨ ਲਓ)",
        "login_prompt": "🎁 3 ਮੁਫ਼ਤ ਗ੍ਰੋਥ ਰਿਪੋਰਟਾਂ ਲਈ ਲੌਗਇਨ ਕਰੋ",
        "send_otp": "OTP ਭੇਜੋ 📩",
        "otp_sent": "✅ {email} 'ਤੇ 6-ਅੰਕਾਂ ਦਾ OTP ਭੇਜਿਆ ਗਿਆ ਹੈ! Inbox / Spam ਦੇਖੋ।",
        "verify_otp": "OTP ਪੁਸ਼ਟੀ ਕਰੋ ✅",
        "gen_btn": "ਗ੍ਰੋਥ ਰਿਪੋਰਟ ਬਣਾਓ 🔍",
        "fetching": "🔄 ਵੀਡੀਓ ਵੇਰਵੇ ਲਏ ਜਾ ਰਹੇ ਹਨ... ⏳",
        "generating": "⚡ ਰਿਪੋਰਟ ਤਿਆਰ ਹੋ ਰਹੀ ਹੈ... ⏳",
        "ready": "✅ ਗ੍ਰੋਥ ਆਡਿਟ ਰਿਪੋਰਟ ਤਿਆਰ ਹੈ!",
        "download": "📥 ਪੂਰੀ ਰਿਪੋਰਟ ਡਾਊਨਲੋਡ ਕਰੋ (.txt)",
        "limit_err": "🔒 ਤੁਹਾਡੀਆਂ 3 ਮੁਫ਼ਤ ਰਿਪੋਰਟਾਂ ਪੂਰੀਆਂ ਹੋ ਗਈਆਂ ਹਨ! ਖੱਬੇ ਪਾਸੇ Pro Plan ਚੁਣੋ।"
    },
    "Odia": {
        "free_left": "🎁 {n}/3 ମାଗଣା ରିପୋର୍ଟ ବାକି ଅଛି",
        "free_over": "🔒 0/3 ମାଗଣା ରିପୋର୍ଟ ବାକି ଅଛି (Pro ପ୍ଲାନ୍ ନିଅନ୍ତୁ)",
        "login_prompt": "🎁 ୩ଟି ମାଗଣା ରିପୋର୍ଟ ପାଇଁ ଲগଇନ୍ କରନ୍ତୁ",
        "send_otp": "OTP ପଠାନ୍ତୁ 📩",
        "otp_sent": "✅ {email} କୁ ୬-ଅଙ୍କ ବିଶିଷ୍ଟ OTP ପଠାଯାଇଛି! Inbox / Spam ଦେଖନ୍ତୁ।",
        "verify_otp": "OTP ଯାଞ୍ଚ କରନ୍ତୁ ✅",
        "gen_btn": "ଗ୍ରୋଥ୍ ରିପୋର୍ଟ ତିଆରି କରନ୍ତୁ 🔍",
        "fetching": "🔄 ଭିଡିଓ ତଥ୍ୟ ସଂଗ୍ରହ କରାଯାଉଛି... ⏳",
        "generating": "⚡ ରିପୋର୍ଟ ପ୍ରସ୍ତୁତ ହେଉଛି... ⏳",
        "ready": "✅ ଗ୍ରୋଥ୍ ଅଡିଟ୍ ରିପୋର୍ଟ ପ୍ରସ୍ତୁତ!",
        "download": "📥 ସମ୍ପୂର୍ଣ୍ଣ ରିପୋର୍ଟ ଡାଉନଲୋଡ୍ କରନ୍ତୁ (.txt)",
        "limit_err": "🔒 ଆପଣଙ୍କର ୩ଟି ମାଗଣା ରିପୋର୍ଟ ଶେଷ ହୋଇଛି! ବାମ ପଟେ Pro Plan ବାଛନ୍ତୁ।"
    },
    "Assamese": {
        "free_left": "🎁 {n}/3 বিনামূলীয়া ৰিপ'ৰ্ট বাকী আছে",
        "free_over": "🔒 0/3 বিনামূলীয়া ৰিপ'ৰ্ট বাকী আছে (Pro প্লেন লওক)",
        "login_prompt": "🎁 ৩টা বিনামূলীয়া ৰিপ'ৰ্টৰ বাবে লগইন কৰক",
        "send_otp": "OTP পঠিয়াওক 📩",
        "otp_sent": "✅ {email} লৈ ৬-সংখ্যাৰ OTP পঠিওৱা হৈছে! Inbox / Spam চাওক।",
        "verify_otp": "OTP নিশ্চিত কৰক ✅",
        "gen_btn": "গ্ৰোথ ৰিপ'ৰ্ট তৈয়াৰ কৰক 🔍",
        "fetching": "🔄 ভিডিঅ'ৰ তথ্য সংগ্ৰহ কৰা হৈছে... ⏳",
        "generating": "⚡ ৰিপ'ৰ্ট তৈয়াৰ হৈ আছে... ⏳",
        "ready": "✅ গ্ৰোথ অডিট ৰিপ'ৰ্ট সাজু!",
        "download": "📥 সম্পূৰ্ণ ৰিপ'ৰ্ট ডাউনলোড কৰক (.txt)",
        "limit_err": "🔒 আপোনাৰ ৩টা বিনামূলীয়া ৰিপ'ৰ্ট শেষ হৈছে! বাওঁফালে Pro Plan বাছনি কৰক।"
    },
    "Urdu": {
        "free_left": "🎁 {n}/3 مفت رپورٹس باقی ہیں",
        "free_over": "🔒 0/3 مفت رپورٹس باقی ہیں (Pro پلان لیں)",
        "login_prompt": "🎁 3 مفت گروتھ رپورٹس کے لیے لاگ ان کریں",
        "send_otp": "OTP بھیجیں 📩",
        "otp_sent": "✅ {email} پر 6 ہندسوں کا OTP بھیج دیا گیا ہے! Inbox / Spam چیک کریں۔",
        "verify_otp": "OTP کی تصدیق کریں ✅",
        "gen_btn": "گروتھ رپورٹ بنائیں 🔍",
        "fetching": "🔄 ویڈیو کی تفصیلات حاصل کی جا رہی ہیں... ⏳",
        "generating": "⚡ رپورٹ تیار ہو رہی ہے... ⏳",
        "ready": "✅ گروتھ آڈٹ رپورٹ تیار ہے!",
        "download": "📥 مکمل رپورٹ ڈاؤن لوڈ کریں (.txt)",
        "limit_err": "🔒 آپ کی 3 مفت رپورٹس مکمل ہو گئی ہیں! بائیں جانب Pro Plan منتخب کریں۔"
    },
    "Bhojpuri": {
        "free_left": "🎁 {n}/3 फ्री रिपोर्ट बाचल बा",
        "free_over": "🔒 0/3 फ्री रिपोर्ट बाचल बा (Pro प्लान लीं)",
        "login_prompt": "🎁 3 फ्री ग्रोथ रिपोर्ट खातिर लॉगिन करीं",
        "send_otp": "OTP भेजीं 📩",
        "otp_sent": "✅ {email} पर 6-अंक के OTP भेज दिहल गइल बा! Inbox / Spam देखीं।",
        "verify_otp": "OTP सत्यापित करीं ✅",
        "gen_btn": "ग्रोथ रिपोर्ट बनाईं 🔍",
        "fetching": "🔄 वीडियो के जानकारी जुटावल जा रहल बा... ⏳",
        "generating": "⚡ रिपोर्ट तैयार हो रहल बा... ⏳",
        "ready": "✅ ग्रोथ ऑडिट रिपोर्ट तैयार बा!",
        "download": "📥 पूरा रिपोर्ट डाउनलोड करीं (.txt)",
        "limit_err": "🔒 राउर 3 फ्री रिपोर्ट पूरा हो गइल बा! बाएं ओर Pro Plan चुनीं।"
    }
}

def get_ui_lang_key(selected_lang):
    if "Auto-Detect" in selected_lang:
        return "English"
    for k in UI_STRINGS.keys():
        if k.lower() in selected_lang.lower():
            return k
    return "English"

def get_logo_base64():
    for fname in ["logo.png", "logo.jpg", "logo.jpeg", "logo.webp"]:
        if os.path.exists(fname):
            with open(fname, "rb") as f:
                ext = fname.split(".")[-1]
                mime = "png" if ext == "png" else "jpeg"
                return f"data:image/{mime};base64,{base64.b64encode(f.read()).decode()}"
    return ""

st.markdown("""
<style>
    [data-testid="stToolbarActions"] { display: none !important; }
    [data-testid="stDecoration"] { display: none !important; }
    header[data-testid="stHeader"] { background: transparent !important; height: 2.5rem !important; }
    #MainMenu { visibility: hidden !important; }
    footer { visibility: hidden !important; }

    .block-container {
        padding-top: 3.6rem !important;
        padding-bottom: 1rem !important;
        max-width: 1180px;
    }

    section[data-testid="stSidebar"] > div:first-child {
        padding-top: 0.6rem !important;
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
        border: 2px solid #10b981 !important;
        box-shadow: 0 4px 16px rgba(16, 185, 129, 0.15);
        margin-bottom: 14px;
        text-align: center;
    }
    .header-title-row {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 12px;
    }
    .header-title-row img {
        height: 40px;
        width: 40px;
        border-radius: 8px;
        object-fit: contain;
    }
    .header-title-row h1 {
        margin: 0;
        font-size: 1.85rem;
        color: #ffffff;
        font-weight: 800;
    }
    .main-header p {
        margin: 4px 0 0 0;
        color: #cbd5e1;
        font-size: 0.95rem;
    }
    .india-badge {
        display: inline-block;
        margin-top: 6px;
        background: rgba(16, 185, 129, 0.16);
        border: 1px solid #10b981;
        color: #6ee7b7;
        padding: 2px 12px;
        border-radius: 999px;
        font-size: 0.8rem;
        font-weight: 600;
    }

    .status-strip {
        background: #1e293b;
        border: 1px solid #334155;
        padding: 9px 14px;
        border-radius: 10px;
        color: #f8fafc;
        font-size: 0.92rem;
    }
    .loading-pill {
        background: rgba(16, 185, 129, 0.15);
        border: 1px solid #10b981;
        color: #34d399;
        padding: 8px 14px;
        border-radius: 8px;
        font-weight: 600;
        font-size: 0.9rem;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

defaults = {
    "verified_email": "",
    "otp_code": "",
    "otp_target": "",
    "pro_unlocked": False,
    "pro_label": "",
    "yt_report": "",
    "yt_vid_id": "",
    "ig_report": "",
    "tt_report": "",
    "script_report": "",
    "thumb_report": "",
    "free_used_cache": None,
    "free_cache_user": "",
    "exhausted_keys": set()
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

try:
    if hasattr(st, "user") and getattr(st.user, "is_logged_in", False):
        g_email = getattr(st.user, "email", "")
        if g_email:
            em = g_email.strip().lower()
            if st.session_state.verified_email != em:
                st.session_state.verified_email = em
                st.session_state.free_used_cache = None
except Exception:
    pass

def fetch_sheet_count_live(user_id):
    if not SHEET_API or not user_id:
        return 0
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
                return min(3, int(txt))
    except Exception:
        pass
    return 0

def get_free_used_count(user_id):
    if not user_id:
        return 0
    if st.session_state.free_cache_user == user_id and st.session_state.free_used_cache is not None:
        return st.session_state.free_used_cache
    val = fetch_sheet_count_live(user_id)
    st.session_state.free_used_cache = val
    st.session_state.free_cache_user = user_id
    return val

def increment_free_used(user_id):
    if not user_id:
        return
    cur = get_free_used_count(user_id)
    new_val = min(3, cur + 1)
    st.session_state.free_used_cache = new_val
    st.session_state.free_cache_user = user_id
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
                st.session_state.free_used_cache = min(3, int(r.text.strip()))
                break
        except Exception:
            time.sleep(0.3)

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

try:
    qp = st.query_params
    auto_pid = str(qp.get("razorpay_payment_id", "")).strip()
    if auto_pid.startswith("pay_") and not st.session_state.pro_unlocked:
        st_res = verify_payment_id(auto_pid, plan="1m")
        if st_res in ["VALID", "OWNER"]:
            st.session_state.pro_unlocked = True
            st.session_state.pro_label = "PRO UNLIMITED ACTIVE"
except Exception:
    pass

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
            "audio_lang": snip.get("defaultAudioLanguage", "") or snip.get("defaultLanguage", ""),
            "description": snip.get("description", "")[:1100],
            "tags": snip.get("tags", [])[:15],
            "views": int(stats.get("viewCount", 0)),
            "likes": int(stats.get("likeCount", 0)),
            "comment_count": int(stats.get("commentCount", 0)),
            "comments": comments
        }
    except Exception:
        return None

@st.cache_data(ttl=3600, show_spinner=False)
def discover_models_for_key(api_key):
    preferred = [
        "gemini-3.8-flash-lite",
        "gemini-3.8-flash",
        "gemini-2.5-flash-lite",
        "gemini-2.5-flash"
    ]
    try:
        client = genai.Client(api_key=api_key, http_options={"timeout": 8000})
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
    return preferred

def clean_mentor_word(text):
    return text.replace("మెంటర్", "సలహాదారు").replace("స్ట్రాటజిస్ట్", "సలహాదారు")

def generate_report_stream(contents_payload):
    if not ALL_GEMINI_KEYS:
        raise RuntimeError("No Gemini API keys found in Streamlit Secrets.")
    active_keys = [k for k in ALL_GEMINI_KEYS if k not in st.session_state.exhausted_keys]
    if not active_keys:
        st.session_state.exhausted_keys = set()
        active_keys = list(ALL_GEMINI_KEYS)

    last_err = ""
    for api_key in active_keys:
        is_free = (api_key in FREE_KEYS)
        timeout_ms = 12000 if is_free else 45000
        client = genai.Client(api_key=api_key, http_options={"timeout": timeout_ms})
        models = discover_models_for_key(api_key)
        for model_name in models:
            try:
                response = client.models.generate_content_stream(
                    model=model_name,
                    contents=contents_payload,
                    config=types.GenerateContentConfig(temperature=0.8, max_output_tokens=6144)
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
                err_low = last_err.lower()
                if any(x in err_low for x in ["429", "quota", "resource_exhausted", "rate", "timeout", "timed out"]):
                    if is_free:
                        st.session_state.exhausted_keys.add(api_key)
                    break
                continue
    raise RuntimeError(f"AI Server busy. Please try again in 5 seconds. ({last_err})")

logo_b64 = get_logo_base64()
logo_html = f'<img src="{logo_b64}" alt="Logo">' if logo_b64 else ""
st.markdown(f"""
<div class="main-header">
    <div class="header-title-row">
        {logo_html}
        <h1>TrendSutra AI</h1>
    </div>
    <p>A to Z Growth Analyzer for YouTube, Instagram & TikTok Creators</p>
    <div class="india-badge">1 AI • 1 India — Supports All 22 Indian Official Languages + Bhojpuri</div>
</div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### ⚙️ Settings")
    report_lang = st.selectbox(
        "🔍 Search Language (A–Z):",
        LANGUAGES_AZ,
        index=0
    )
    audience_scope = st.radio("Audience:", ["Regional", "Global", "Both"], horizontal=True)

    ui_key = get_ui_lang_key(report_lang)
    T = UI_STRINGS[ui_key]

    st.divider()
    st.markdown("### 💎 Pro Plans")

    free_used = get_free_used_count(st.session_state.verified_email) if st.session_state.verified_email else 0
    free_left = max(0, 3 - free_used)

    if st.session_state.pro_unlocked:
        st.success(f"✅ {st.session_state.pro_label}")
    elif st.session_state.verified_email:
        if free_left > 0:
            st.info(T["free_left"].format(n=free_left))
        else:
            st.error(T["free_over"])
    else:
        st.info(T["login_prompt"])

    st.markdown(f"• **1 Month:** ₹100 👉 [Pay ₹100]({RAZORPAY_1M})\n• **12 Months:** ₹1,000 👉 [Pay ₹1,000]({RAZORPAY_12M})")

    plan_choice = st.radio("Plan:", ["1M (₹100)", "12M (₹1,000)"], horizontal=True, label_visibility="collapsed")
    pay_input = st.text_input("Payment ID:", placeholder="Paste Payment ID (pay_...)", label_visibility="collapsed")
    if st.button("Unlock Pro 🔓", use_container_width=True):
        if not pay_input.strip():
            st.warning("Enter Payment ID.")
        else:
            p_code = "12m" if "12" in plan_choice else "1m"
            status = verify_payment_id(pay_input, plan=p_code)
            if status == "OWNER":
                st.session_state.pro_unlocked = True
                st.session_state.pro_label = "OWNER UNLIMITED"
                st.rerun()
            elif status == "VALID":
                st.session_state.pro_unlocked = True
                st.session_state.pro_label = f"PRO ACTIVE ({plan_choice})"
                st.rerun()
            elif status == "EXPIRED":
                st.error("⏰ Plan Expired! Please renew.")
            elif status == "ALREADY_USED":
                st.error("❌ Used on 3 devices already.")
            else:
                st.error("❌ Invalid Payment ID.")

    st.divider()
    st.caption("📩 support@aiengtel.com | © 2026 TrendSutra AI")

if not st.session_state.verified_email and not st.session_state.pro_unlocked:
    c1, c2, c3, c4 = st.columns([2.2, 0.4, 2.5, 1.4])
    with c1:
        if st.button("Continue with Gmail", type="primary", use_container_width=True):
            try:
                st.login("google")
            except Exception as e:
                st.error(f"Google Login Error: {e}")
    with c2:
        st.markdown("<div style='text-align:center; padding-top:8px; color:#94a3b8; font-weight:700;'>OR</div>", unsafe_allow_html=True)
    with c3:
        email_in = st.text_input("Mail ID", placeholder="Login with Mail ID (creator@gmail.com)", label_visibility="collapsed")
    with c4:
        if st.button(T["send_otp"], use_container_width=True):
            clean_em = email_in.strip().lower()
            if "@" not in clean_em or "." not in clean_em.split("@")[-1]:
                st.error("❌ Invalid Email ID.")
            elif clean_em.split("@")[-1] in TEMP_DOMAINS:
                st.error("❌ Temp email not allowed.")
            else:
                code = str(random.randint(100000, 999999))
                ok, err_msg = send_otp_email(clean_em, code)
                if ok:
                    st.session_state.otp_code = code
                    st.session_state.otp_target = clean_em
                    st.success(T["otp_sent"].format(email=clean_em))
                else:
                    st.error(f"OTP Error: {err_msg}")

    if st.session_state.otp_target:
        oc1, oc2, oc3 = st.columns([2, 2, 1.5])
        with oc2:
            otp_in = st.text_input("OTP", placeholder="Enter 6-digit OTP", max_chars=6, label_visibility="collapsed")
        with oc3:
            if st.button(T["verify_otp"], type="primary", use_container_width=True):
                if otp_in.strip() == st.session_state.otp_code:
                    st.session_state.verified_email = st.session_state.otp_target
                    st.session_state.free_used_cache = None
                    st.session_state.otp_code = ""
                    st.rerun()
                else:
                    st.error("❌ Wrong OTP.")
    st.stop()
else:
    u1, u2 = st.columns([5, 1.2])
    with u1:
        badge_txt = f"✅ {st.session_state.pro_label}" if st.session_state.pro_unlocked else (T["free_left"].format(n=free_left) if free_left > 0 else T["free_over"])
        st.markdown(f'<div class="status-strip">👤 Logged in as <b>{st.session_state.verified_email or "PRO Member"}</b> &nbsp;|&nbsp; {badge_txt}</div>', unsafe_allow_html=True)
    with u2:
        if st.button("Logout", use_container_width=True):
            st.session_state.verified_email = ""
            st.session_state.pro_unlocked = False
            st.session_state.free_used_cache = None
            st.session_state.yt_report = ""
            try:
                if hasattr(st, "logout"):
                    st.logout()
            except Exception:
                pass
            st.rerun()

def build_language_instruction(selected_lang):
    if "Auto-Detect" in selected_lang:
        return (
            "CRITICAL LANGUAGE RULE: Automatically detect the primary language of the video from its Title, Description, Audio Language tag, and Viewer Comments. "
            "At the very top of your response, write a single line: '🌐 **Detected Video Language:** <Language Name>'. "
            "Then write the ENTIRE 6-section report (including ALL 6 section headings, story recap, comment translations, hooks, and action plan) in that exact detected language using its NATIVE SCRIPT (e.g., Urdu in اردو script, Tamil in தமிழ் script, Hindi in हिन्दी script, Telugu in తెలుగు script, etc.)! Never transliterate into English letters."
        )
    else:
        return (
            f"CRITICAL LANGUAGE RULE: Write the ENTIRE 6-section report (including ALL 6 section headings, story recap, comment translations, hooks, and action plan) strictly in **{selected_lang}** using its NATIVE SCRIPT! Never transliterate into English letters."
        )

tab_yt, tab_ig, tab_tt, tab_sc, tab_th = st.tabs([
    "📺 YouTube Analyzer",
    "📸 Instagram Reels",
    "🎵 TikTok Analyzer",
    "✍️ Viral Script Generator",
    "🖼️ AI Thumbnail Checker"
])

with tab_yt:
    yc1, yc2, yc3 = st.columns([4.2, 1.8, 1.6])
    with yc1:
        yt_url = st.text_input("YouTube Link", placeholder="Paste YouTube Video or Shorts Link...", label_visibility="collapsed")
    with yc2:
        run_yt = st.button(T["gen_btn"], key="btn_yt", type="primary", use_container_width=True)
    with yc3:
        yt_status = st.empty()

    if run_yt:
        if not yt_url.strip():
            st.warning("Please paste a YouTube link.")
        elif not st.session_state.pro_unlocked and free_left <= 0:
            st.error(T["limit_err"])
        else:
            vid_id = extract_youtube_id(yt_url.strip())
            if not vid_id:
                st.error("❌ Invalid YouTube link.")
            else:
                yt_status.markdown(f'<div class="loading-pill">{T["fetching"]}</div>', unsafe_allow_html=True)
                data = fetch_youtube_details(vid_id)
                if not data:
                    yt_status.empty()
                    st.error("❌ Could not fetch video data. Check if the video is Public.")
                else:
                    comments_block = "\n".join(data["comments"][:12]) if data["comments"] else "No public comments."
                    lang_rule = build_language_instruction(report_lang)
                    prompt = f"""
You are a warm, encouraging human social media growth advisor.
{lang_rule}
Write a deeply detailed, practical growth audit report (900 to 1,200 words) for a **{audience_scope}** audience using simple everyday spoken words.

VIDEO DATA:
- Channel: {data['channel']}
- Title: {data['title']}
- Audio Language Tag: {data['audio_lang']}
- Views: {data['views']:,} | Likes: {data['likes']:,} | Comments: {data['comment_count']:,}
- Description: {data['description']}
- Tags: {', '.join(data['tags'])}
- Real Audience Comments:
{comments_block}

STRICTLY INCLUDE THESE 6 SECTIONS (Translate every heading into the report's native script):
### 🎬 1. Video Story Recap & Creator Appreciation
- Warmly retell the core story/message of this video so the creator feels you truly understood their work, then genuinely praise their effort, topic choice, and strengths.

### 💬 2. What the Audience is Saying (Real Comments Translated)
- Quote 4 real viewer comments with their names, translate them naturally into the report language, explain audience sentiment, and give 3 copy-paste reply templates.

### 🔥 3. 3 Next Viral Video Ideas + 5-Second Opening Hooks
- Give 3 fresh follow-up video ideas tailored to this channel with an exact word-for-word 5-second Hook and Thumbnail idea for each.

### 🎯 4. Copy-Paste SEO Makeover (Titles, Description & 15 Tags)
- Provide 3 clickable high-CTR titles, a 3-line SEO description hook, and 15 comma-separated tags.

### 💰 5. Monetization & Brand Earning Blueprint
- Explain 3 practical ways this channel can earn money (AdSense, Affiliate, Brand deals).

### 📅 6. Step-by-Step 30-Day Action Plan
- Give a clear Week 1 to Week 4 checklist to double views and subscribers.
"""
                    yt_status.markdown(f'<div class="loading-pill">{T["generating"]}</div>', unsafe_allow_html=True)
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
        st.success(T["ready"])
        st.markdown(st.session_state.yt_report)
        st.download_button(
            T["download"],
            data=st.session_state.yt_report,
            file_name=f"TrendSutra_YouTube_{st.session_state.yt_vid_id or 'Report'}.txt",
            mime="text/plain",
            key="dl_yt_saved",
            use_container_width=True
        )

with tab_ig:
    ic1, ic2, ic3 = st.columns([4.2, 1.8, 1.6])
    with ic1:
        ig_url = st.text_input("Instagram Link", placeholder="Paste Instagram Reel Link...", label_visibility="collapsed")
    with ic2:
        run_ig = st.button(T["gen_btn"], key="btn_ig", type="primary", use_container_width=True)
    with ic3:
        ig_status = st.empty()

    if run_ig:
        if not ig_url.strip():
            st.warning("Please paste an Instagram Reel link.")
        elif not st.session_state.pro_unlocked and free_left <= 0:
            st.error(T["limit_err"])
        else:
            ig_status.markdown(f'<div class="loading-pill">{T["generating"]}</div>', unsafe_allow_html=True)
            lang_rule = build_language_instruction(report_lang)
            ig_prompt = f"""
You are a warm, encouraging human Instagram Reels growth advisor.
{lang_rule}
Write a detailed 6-section Instagram Reels growth audit (900+ words) for a **{audience_scope}** audience using simple spoken words.
Reel Link: {ig_url.strip()}
Translate all 6 headings into the report's native script:
1. Creator Appreciation & Reel Strategy Overview
2. Watch-Time, Audio & 3-Second Retention Hook Analysis
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
        st.success(T["ready"])
        st.markdown(st.session_state.ig_report)
        st.download_button(
            T["download"],
            data=st.session_state.ig_report,
            file_name="TrendSutra_Instagram_Report.txt",
            mime="text/plain",
            key="dl_ig_saved",
            use_container_width=True
        )

with tab_tt:
    tc1, tc2, tc3 = st.columns([4.2, 1.8, 1.6])
    with tc1:
        tt_url = st.text_input("TikTok Link", placeholder="Paste TikTok Video Link...", label_visibility="collapsed")
    with tc2:
        run_tt = st.button(T["gen_btn"], key="btn_tt", type="primary", use_container_width=True)
    with tc3:
        tt_status = st.empty()

    if run_tt:
        if not tt_url.strip():
            st.warning("Please paste a TikTok link.")
        elif not st.session_state.pro_unlocked and free_left <= 0:
            st.error(T["limit_err"])
        else:
            tt_status.markdown(f'<div class="loading-pill">{T["generating"]}</div>', unsafe_allow_html=True)
            lang_rule = build_language_instruction(report_lang)
            tt_prompt = f"""
You are a warm, encouraging human TikTok growth advisor.
{lang_rule}
Write a detailed 6-section TikTok growth audit (900+ words) for a **{audience_scope}** audience using simple spoken words.
TikTok Link: {tt_url.strip()}
Translate all 6 headings into the report's native script:
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
        st.success(T["ready"])
        st.markdown(st.session_state.tt_report)
        st.download_button(
            T["download"],
            data=st.session_state.tt_report,
            file_name="TrendSutra_TikTok_Report.txt",
            mime="text/plain",
            key="dl_tt_saved",
            use_container_width=True
        )

with tab_sc:
    sc1, sc2, sc3 = st.columns([3.5, 1.5, 1.5])
    with sc1:
        sc_topic = st.text_input("Video Topic", placeholder="Enter your video topic (e.g., How to save money on electricity bill)...", label_visibility="collapsed")
    with sc2:
        sc_len = st.selectbox("Duration", ["60 Sec (Shorts/Reels)", "3-5 Min Video", "8-10 Min Video"], label_visibility="collapsed")
    with sc3:
        sc_tone = st.selectbox("Tone", ["Engaging & Friendly", "Emotional & Story", "Funny & Energetic", "Educational & Clear"], label_visibility="collapsed")

    sb1, sb2 = st.columns([2.2, 4])
    with sb1:
        run_sc = st.button("Generate Viral Script ✍️", key="btn_sc", type="primary", use_container_width=True)
    with sb2:
        sc_status = st.empty()

    if run_sc:
        if not sc_topic.strip():
            st.warning("Please enter a video topic.")
        elif not st.session_state.pro_unlocked and free_left <= 0:
            st.error(T["limit_err"])
        else:
            sc_status.markdown(f'<div class="loading-pill">{T["generating"]}</div>', unsafe_allow_html=True)
            target_l = "English" if "Auto-Detect" in report_lang else report_lang
            sc_prompt = f"""
You are a master viral YouTube & Reels scriptwriter.
Write a complete, ready-to-speak video script in **{target_l}** (using its NATIVE SCRIPT, simple everyday spoken words) for a **{audience_scope}** audience.
Topic: {sc_topic.strip()}
Format/Length: {sc_len}
Tone: {sc_tone}

Include these 4 sections (translate headings into {target_l}'s native script):
### 🪝 1. 3 High-Retention Opening Hooks (First 5 Seconds)
- Write 3 scroll-stopping opening lines the creator can speak word-for-word.
### 📜 2. Complete Spoken Script + Visual / Camera Cues
- Write the full word-for-word dialogue broken into clear timestamps with [Visual / B-Roll / Text on Screen] cues.
### 📣 3. Natural Call-To-Action (Like, Comment & Subscribe)
- Write a friendly, non-pushy ending CTA that boosts comments.
### 🎯 4. 3 Viral Titles + Thumbnail Text Idea
- Give 3 high-CTR video titles and a 3-word bold thumbnail text idea.
"""
            report_box = st.empty()
            full_text = ""
            try:
                for piece in generate_report_stream(sc_prompt):
                    full_text += piece
                    report_box.markdown(full_text)
                sc_status.empty()
                st.session_state.script_report = full_text
                if not st.session_state.pro_unlocked:
                    increment_free_used(st.session_state.verified_email)
                log_usage_to_sheet(st.session_state.verified_email or "PRO", "ScriptGenerator", sc_topic.strip()[:80])
                st.rerun()
            except Exception as e:
                sc_status.empty()
                st.error(str(e))

    if st.session_state.script_report:
        st.success("✅ Viral Script Ready!")
        st.markdown(st.session_state.script_report)
        st.download_button(
            "📥 Download Script (.txt)",
            data=st.session_state.script_report,
            file_name="TrendSutra_Viral_Script.txt",
            mime="text/plain",
            key="dl_sc_saved",
            use_container_width=True
        )

with tab_th:
    th1, th2 = st.columns([3.5, 2.5])
    with th1:
        thumb_file = st.file_uploader("Upload Thumbnail Image (JPG / PNG / WEBP)", type=["jpg", "jpeg", "png", "webp"], label_visibility="collapsed")
    with th2:
        thumb_title = st.text_input("Video Title (Optional)", placeholder="Optional: Enter your video title for CTR check...", label_visibility="collapsed")
        run_th = st.button("Check Thumbnail CTR 🖼️", key="btn_th", type="primary", use_container_width=True)
        th_status = st.empty()

    if thumb_file is not None:
        st.image(thumb_file, width=320)

    if run_th:
        if thumb_file is None:
            st.warning("Please upload a thumbnail image first.")
        elif not st.session_state.pro_unlocked and free_left <= 0:
            st.error(T["limit_err"])
        else:
            th_status.markdown(f'<div class="loading-pill">{T["generating"]}</div>', unsafe_allow_html=True)
            img = Image.open(thumb_file)
            target_l = "English" if "Auto-Detect" in report_lang else report_lang
            th_prompt = f"""
You are an expert YouTube Thumbnail & CTR Designer.
Analyze this uploaded thumbnail image for a **{audience_scope}** audience.
Video Title: {thumb_title.strip() or 'Not provided'}
Write the entire review in **{target_l}** (using its NATIVE SCRIPT and simple spoken words).

Include these 4 sections (translate headings into {target_l}'s native script):
### 📊 1. Estimated CTR Score (Out of 10) & First Impression
- Give an honest score out of 10 and explain what a viewer notices in the first 0.5 seconds.
### 📱 2. Mobile Screen Readability & Text Check
- Check if the text, face expression, and contrast are clearly readable on a small phone screen.
### 🎨 3. Colors, Emotion & Curiosity Gap
- Evaluate background separation, color contrast, and emotional curiosity.
### 🚀 4. 3 Exact Fixes to Double Clicks (CTR)
- Give 3 specific, easy changes (better 3-word thumbnail text, color tweak, framing) to make this thumbnail go viral.
"""
            report_box = st.empty()
            full_text = ""
            try:
                for piece in generate_report_stream([th_prompt, img]):
                    full_text += piece
                    report_box.markdown(full_text)
                th_status.empty()
                st.session_state.thumb_report = full_text
                if not st.session_state.pro_unlocked:
                    increment_free_used(st.session_state.verified_email)
                log_usage_to_sheet(st.session_state.verified_email or "PRO", "ThumbnailChecker", thumb_file.name)
                st.rerun()
            except Exception as e:
                th_status.empty()
                st.error(str(e))

    if st.session_state.thumb_report:
        st.success("✅ Thumbnail CTR Audit Ready!")
        st.markdown(st.session_state.thumb_report)
        st.download_button(
            "📥 Download Thumbnail Audit (.txt)",
            data=st.session_state.thumb_report,
            file_name="TrendSutra_Thumbnail_Audit.txt",
            mime="text/plain",
            key="dl_th_saved",
            use_container_width=True
        )
