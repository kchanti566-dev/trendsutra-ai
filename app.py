import streamlit as st
from google import genai
from google.genai import types
from googleapiclient.discovery import build
import os
import re
import time
import base64
import requests
import random
import smtplib
from email.mime.text import MIMEText

# --- 1. PAGE CONFIG ---
st.set_page_config(
    page_title="TrendSutra AI - 1 AI • 1 India",
    page_icon="logo.png" if os.path.exists("logo.png") else "IN",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. LOAD SECRETS (4-KEY SMART FAILOVER) ---
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

# --- 3. 22 INDIAN OFFICIAL LANGUAGES + BHOJPURI (A-Z) ---
LANGUAGES = [
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
    "Sindhi (सिंधी)",
    "Tamil (தமிழ்)",
    "Telugu (తెలుగు)",
    "Tenglish (Telugu + English)",
    "Urdu (اردو)"
]

# --- 4. DYNAMIC MULTILINGUAL UI STRINGS ---
UI_TEXT = {
    "English": {
        "free_left": "🎁 {n}/3 Free Reports Left",
        "free_done": "🔒 0/3 Free Reports Left",
        "gen_btn": "Generate Growth Report 🔍",
        "fetching": "🔄 Fetching video details & comments... ⏳",
        "generating": "⚡ Generating report... ⏳",
        "ready": "✅ Growth Audit Report Ready!",
        "dl_btn": "📥 Download Complete Report (.txt)",
        "otp_sent": "✅ 6-digit OTP sent to {em}! Check Inbox/Spam.",
        "send_otp": "Send OTP 📩",
        "verify_otp": "Verify OTP ✅",
        "wrong_otp": "❌ Wrong OTP! Please check and try again.",
        "limit_msg": "🔒 Your 3 Free Reports are used! Unlock Pro Plan from the left sidebar."
    },
    "Telugu": {
        "free_left": "🎁 {n}/3 ఉచిత రిపోర్ట్‌లు మిగిలాయి",
        "free_done": "🔒 0/3 ఉచిత రిపోర్ట్‌లు మిగిలాయి",
        "gen_btn": "గ్రోత్ రిపోర్ట్ తయారు చేయండి 🔍",
        "fetching": "🔄 వీడియో వివరాలు & కామెంట్లు సేకరిస్తోంది... ⏳",
        "generating": "⚡ రిపోర్ట్ తయారవుతోంది... ⏳",
        "ready": "✅ గ్రోత్ ఆడిట్ రిపోర్ట్ సిద్ధమైంది!",
        "dl_btn": "📥 పూర్తి రిపోర్ట్ డౌన్‌లోడ్ చేయండి (.txt)",
        "otp_sent": "✅ {em} కి 6-అంకెల OTP పంపబడింది! ఇన్‌బాక్స్/Spam చెక్ చేయండి.",
        "send_otp": "OTP పంపండి 📩",
        "verify_otp": "OTP నిర్ధారించండి ✅",
        "wrong_otp": "❌ తప్పు OTP! దయచేసి మళ్ళీ చెక్ చేయండి.",
        "limit_msg": "🔒 మీ 3 ఉచిత రిపోర్ట్‌లు పూర్తయ్యాయి! ఎడమ వైపు Pro Plan తీసుకోండి."
    },
    "Hindi": {
        "free_left": "🎁 {n}/3 मुफ्त रिपोर्ट बाकी हैं",
        "free_done": "🔒 0/3 मुफ्त रिपोर्ट बाकी हैं",
        "gen_btn": "ग्रोथ रिपोर्ट बनाएं 🔍",
        "fetching": "🔄 वीडियो विवरण और कमेंट्स लिए जा रहे हैं... ⏳",
        "generating": "⚡ रिपोर्ट तैयार हो रही है... ⏳",
        "ready": "✅ ग्रोथ ऑडिट रिपोर्ट तैयार है!",
        "dl_btn": "📥 पूरी रिपोर्ट डाउनलोड करें (.txt)",
        "otp_sent": "✅ {em} पर 6-अंकों का OTP भेजा गया! इनबॉक्स/स्पैम जांचें।",
        "send_otp": "OTP भेजें 📩",
        "verify_otp": "OTP सत्यापित करें ✅",
        "wrong_otp": "❌ गलत OTP! कृपया पुनः जांचें।",
        "limit_msg": "🔒 आपकी 3 मुफ्त रिपोर्ट पूरी हो गई हैं! बाईं ओर से Pro Plan लें।"
    },
    "Tamil": {
        "free_left": "🎁 {n}/3 இலவச அறிக்கைகள் உள்ளன",
        "free_done": "🔒 0/3 இலவச அறிக்கைகள் உள்ளன",
        "gen_btn": "வளர்ச்சி அறிக்கையை உருவாக்கு 🔍",
        "fetching": "🔄 வீடியோ விவரங்கள் சேகரிக்கப்படுகின்றன... ⏳",
        "generating": "⚡ அறிக்கை தயாராகிறது... ⏳",
        "ready": "✅ வளர்ச்சி தணிக்கை அறிக்கை தயார்!",
        "dl_btn": "📥 முழு அறிக்கையைப் பதிவிறக்கவும் (.txt)",
        "otp_sent": "✅ {em} க்கு 6-இலக்க OTP அனுப்பப்பட்டது!",
        "send_otp": "OTP அனுப்பு 📩",
        "verify_otp": "OTP சரிபார் ✅",
        "wrong_otp": "❌ தவறான OTP! மீண்டும் சரிபார்க்கவும்.",
        "limit_msg": "🔒 உங்கள் 3 இலவச அறிக்கைகள் முடிந்துவிட்டன! இடதுபுறம் Pro Plan பெறவும்."
    },
    "Kannada": {
        "free_left": "🎁 {n}/3 ಉಚಿತ ವರದಿಗಳು ಬಾಕಿ ಇವೆ",
        "free_done": "🔒 0/3 ಉಚಿತ ವರದಿಗಳು ಬಾಕಿ ಇವೆ",
        "gen_btn": "ಗ್ರೋತ್ ವರದಿ ರಚಿಸಿ 🔍",
        "fetching": "🔄 ವೀಡಿಯೊ ವಿವರಗಳನ್ನು ಪಡೆಯಲಾಗುತ್ತಿದೆ... ⏳",
        "generating": "⚡ ವರದಿ ಸಿದ್ಧವಾಗುತ್ತಿದೆ... ⏳",
        "ready": "✅ ಗ್ರೋತ್ ಆಡಿಟ್ ವರದಿ ಸಿದ್ಧವಾಗಿದೆ!",
        "dl_btn": "📥 ಪೂರ್ಣ ವರದಿ ಡೌನ್‌ಲೋಡ್ ಮಾಡಿ (.txt)",
        "otp_sent": "✅ {em} ಗೆ 6-ಅಂಕಿಯ OTP ಕಳುಹಿಸಲಾಗಿದೆ!",
        "send_otp": "OTP ಕಳುಹಿಸಿ 📩",
        "verify_otp": "OTP ಪರಿಶೀಲಿಸಿ ✅",
        "wrong_otp": "❌ ತಪ್ಪಾದ OTP! ದಯವಿಟ್ಟು ಮತ್ತೆ ಪರಿಶೀಲಿಸಿ.",
        "limit_msg": "🔒 ನಿಮ್ಮ 3 ಉಚಿತ ವರದಿಗಳು ಮುಗಿದಿವೆ! ಎಡಭಾಗದಿಂದ Pro Plan ಪಡೆಯಿರಿ."
    },
    "Malayalam": {
        "free_left": "🎁 {n}/3 സൗജന്യ റിപ്പോർട്ടുകൾ ബാക്കിയുണ്ട്",
        "free_done": "🔒 0/3 സൗജന്യ റിപ്പോർട്ടുകൾ ബാക്കിയുണ്ട്",
        "gen_btn": "ഗ്രോത്ത് റിപ്പോർട്ട് നിർമ്മിക്കുക 🔍",
        "fetching": "🔄 വീഡിയോ വിവരങ്ങൾ ശേഖരിക്കുന്നു... ⏳",
        "generating": "⚡ റിപ്പോർട്ട് തയ്യാറാകുന്നു... ⏳",
        "ready": "✅ ഗ്രോത്ത് ഓഡിറ്റ് റിപ്പോർട്ട് തയ്യാറായി!",
        "dl_btn": "📥 പൂർണ്ണ റിപ്പോർട്ട് ഡൗൺലോഡ് ചെയ്യുക (.txt)",
        "otp_sent": "✅ {em} ലേക്ക് 6-അക്ക OTP അയച്ചു!",
        "send_otp": "OTP അയയ്ക്കുക 📩",
        "verify_otp": "OTP സ്ഥിരീകരിക്കുക ✅",
        "wrong_otp": "❌ തെറ്റായ OTP! വീണ്ടും പരിശോധിക്കുക.",
        "limit_msg": "🔒 നിങ്ങളുടെ 3 സൗജന്യ റിപ്പോർട്ടുകൾ കഴിഞ്ഞു! ഇടതുവശത്ത് നിന്ന് Pro Plan എടുക്കുക."
    },
    "Marathi": {
        "free_left": "🎁 {n}/3 मोफत रिपोर्ट शिल्लक आहेत",
        "free_done": "🔒 0/3 मोफत रिपोर्ट शिल्लक आहेत",
        "gen_btn": "ग्रोथ रिपोर्ट तयार करा 🔍",
        "fetching": "🔄 व्हिडिओ माहिती गोळा करत आहे... ⏳",
        "generating": "⚡ रिपोर्ट तयार होत आहे... ⏳",
        "ready": "✅ ग्रोथ ऑडिट रिपोर्ट तयार आहे!",
        "dl_btn": "📥 पूर्ण रिपोर्ट डाउनलोड करा (.txt)",
        "otp_sent": "✅ {em} वर 6-अंकी OTP पाठवला आहे!",
        "send_otp": "OTP पाठवा 📩",
        "verify_otp": "OTP तपासा ✅",
        "wrong_otp": "❌ चुकीचा OTP! कृपया पुन्हा तपासा.",
        "limit_msg": "🔒 तुमचे 3 मोफत रिपोर्ट संपले आहेत! डाव्या बाजूला Pro Plan घ्या."
    },
    "Bengali": {
        "free_left": "🎁 {n}/3 ফ্রি রিপোর্ট বাকি আছে",
        "free_done": "🔒 0/3 ফ্রি রিপোর্ট বাকি আছে",
        "gen_btn": "গ্রোথ রিপোর্ট তৈরি করুন 🔍",
        "fetching": "🔄 ভিডিওর তথ্য সংগ্রহ করা হচ্ছে... ⏳",
        "generating": "⚡ রিপোর্ট তৈরি হচ্ছে... ⏳",
        "ready": "✅ গ্রোথ অডিট রিপোর্ট তৈরি!",
        "dl_btn": "📥 সম্পূর্ণ রিপোর্ট ডাউনলোড করুন (.txt)",
        "otp_sent": "✅ {em}-এ ৬-অঙ্কের OTP পাঠানো হয়েছে!",
        "send_otp": "OTP পাঠান 📩",
        "verify_otp": "OTP যাচাই করুন ✅",
        "wrong_otp": "❌ ভুল OTP! অনুগ্রহ করে আবার দেখুন।",
        "limit_msg": "🔒 আপনার ৩টি ফ্রি রিপোর্ট শেষ! বাম দিক থেকে Pro Plan নিন।"
    },
    "Gujarati": {
        "free_left": "🎁 {n}/3 મફત રિપોર્ટ બાકી છે",
        "free_done": "🔒 0/3 મફત રિપોર્ટ બાકી છે",
        "gen_btn": "ગ્રોથ રિપોર્ટ બનાવો 🔍",
        "fetching": "🔄 વિડિયો વિગતો મેળવી રહ્યા છીએ... ⏳",
        "generating": "⚡ રિપોર્ટ તૈયાર થઈ રહ્યો છે... ⏳",
        "ready": "✅ ગ્રોથ ઓડિટ રિપોર્ટ તૈયાર છે!",
        "dl_btn": "📥 સંપૂર્ણ રિપોર્ટ ડાઉનલોડ કરો (.txt)",
        "otp_sent": "✅ {em} પર 6-અંકનો OTP મોકલવામાં આવ્યો છે!",
        "send_otp": "OTP મોકલો 📩",
        "verify_otp": "OTP ચકાસો ✅",
        "wrong_otp": "❌ ખોટો OTP! કૃપા કરીને ફરી તપાસો.",
        "limit_msg": "🔒 તમારા 3 મફત રિપોર્ટ પૂરા થયા છે! ડાબી બાજુથી Pro Plan લો."
    },
    "Punjabi": {
        "free_left": "🎁 {n}/3 ਮੁਫ਼ਤ ਰਿਪੋਰਟਾਂ ਬਾਕੀ ਹਨ",
        "free_done": "🔒 0/3 ਮੁਫ਼ਤ ਰਿਪੋਰਟਾਂ ਬਾਕੀ ਹਨ",
        "gen_btn": "ਗ੍ਰੋਥ ਰਿਪੋਰਟ ਬਣਾਓ 🔍",
        "fetching": "🔄 ਵੀਡੀਓ ਵੇਰਵੇ ਲਏ ਜਾ ਰਹੇ ਹਨ... ⏳",
        "generating": "⚡ ਰਿਪੋਰਟ ਤਿਆਰ ਹੋ ਰਹੀ ਹੈ... ⏳",
        "ready": "✅ ਗ੍ਰੋਥ ਆਡਿਟ ਰਿਪੋਰਟ ਤਿਆਰ ਹੈ!",
        "dl_btn": "📥 ਪੂਰੀ ਰਿਪੋਰਟ ਡਾਊਨਲੋਡ ਕਰੋ (.txt)",
        "otp_sent": "✅ {em} 'ਤੇ 6-ਅੰਕਾਂ ਦਾ OTP ਭੇਜਿਆ ਗਿਆ ਹੈ!",
        "send_otp": "OTP ਭੇਜੋ 📩",
        "verify_otp": "OTP ਪੁਸ਼ਟੀ ਕਰੋ ✅",
        "wrong_otp": "❌ ਗਲਤ OTP! ਕਿਰਪਾ ਕਰਕੇ ਦੁਬਾਰਾ ਜਾਂਚੋ।",
        "limit_msg": "🔒 ਤੁਹਾਡੀਆਂ 3 ਮੁਫ਼ਤ ਰਿਪੋਰਟਾਂ ਪੂਰੀਆਂ ਹੋ ਗਈਆਂ ਹਨ! ਖੱਬੇ ਪਾਸਿਓਂ Pro Plan ਲਓ।"
    },
    "Odia": {
        "free_left": "🎁 {n}/3 ମାଗଣା ରିପୋର୍ଟ ବାକି ଅଛି",
        "free_done": "🔒 0/3 ମାଗଣା ରିପୋର୍ଟ ବାକି ଅଛି",
        "gen_btn": "ଗ୍ରୋଥ୍ ରିପୋର୍ଟ ତିଆରି କରନ୍ତୁ 🔍",
        "fetching": "🔄 ଭିଡିଓ ବିବରଣୀ ସଂଗ୍ରହ କରାଯାଉଛି... ⏳",
        "generating": "⚡ ରିପୋର୍ଟ ପ୍ରସ୍ତୁତ ହେଉଛି... ⏳",
        "ready": "✅ ଗ୍ରୋଥ୍ ଅଡିଟ୍ ରିପୋର୍ଟ ପ୍ରସ୍ତୁତ!",
        "dl_btn": "📥 ସମ୍ପୂର୍ଣ୍ଣ ରିପୋର୍ଟ ଡାଉନଲୋଡ୍ କରନ୍ତୁ (.txt)",
        "otp_sent": "✅ {em} କୁ 6-ଅଙ୍କ ବିଶିଷ୍ଟ OTP ପଠାଯାଇଛି!",
        "send_otp": "OTP ପଠାନ୍ତୁ 📩",
        "verify_otp": "OTP ଯାଞ୍ଚ କରନ୍ତୁ ✅",
        "wrong_otp": "❌ ଭୁଲ୍ OTP! ଦୟାକରି ପୁଣି ଯାଞ୍ଚ କରନ୍ତୁ।",
        "limit_msg": "🔒 ଆପଣଙ୍କର 3ଟି ମାଗଣା ରିପୋର୍ଟ ଶେଷ ହୋଇଯାଇଛି! ବାମ ପାର୍ଶ୍ୱରୁ Pro Plan ନିଅନ୍ତୁ।"
    },
    "Assamese": {
        "free_left": "🎁 {n}/3 বিনামূলীয়া ৰিপ'ৰ্ট বাকী আছে",
        "free_done": "🔒 0/3 বিনামূলীয়া ৰিপ'ৰ্ট বাকী আছে",
        "gen_btn": "গ্ৰোথ ৰিপ'ৰ্ট বনাওক 🔍",
        "fetching": "🔄 ভিডিঅ'ৰ বিৱৰণ সংগ্ৰহ কৰা হৈছে... ⏳",
        "generating": "⚡ ৰিপ'ৰ্ট প্ৰস্তুত হৈ আছে... ⏳",
        "ready": "✅ গ্ৰোথ অডিট ৰিপ'ৰ্ট সাজু!",
        "dl_btn": "📥 সম্পূৰ্ণ ৰিপ'ৰ্ট ডাউনলোড কৰক (.txt)",
        "otp_sent": "✅ {em} লৈ ৬-অংকৰ OTP পঠিওৱা হৈছে!",
        "send_otp": "OTP পঠিয়াওক 📩",
        "verify_otp": "OTP নিশ্চিত কৰক ✅",
        "wrong_otp": "❌ ভুল OTP! অনুগ্ৰহ কৰি আকৌ পৰীক্ষা কৰক।",
        "limit_msg": "🔒 আপোনাৰ ৩টা বিনামূলীয়া ৰিপ'ৰ্ট শেষ হৈছে! বাওঁফালৰ পৰা Pro Plan লওক।"
    },
    "Urdu": {
        "free_left": "🎁 مفت رپورٹس باقی ہیں {n}/3",
        "free_done": "🔒 مفت رپورٹس باقی ہیں 0/3",
        "gen_btn": "گروتھ رپورٹ بنائیں 🔍",
        "fetching": "🔄 ویڈیو کی تفصیلات حاصل کی جا رہی ہیں... ⏳",
        "generating": "⚡ رپورٹ تیار ہو رہی ہے... ⏳",
        "ready": "✅ گروتھ آڈٹ رپورٹ تیار ہے!",
        "dl_btn": "📥 مکمل رپورٹ ڈاؤن لوڈ کریں (.txt)",
        "otp_sent": "✅ {em} پر 6 ہندسوں کا OTP بھیج دیا گیا ہے!",
        "send_otp": "OTP بھیجیں 📩",
        "verify_otp": "OTP تصدیق کریں ✅",
        "wrong_otp": "❌ غلط OTP! براہ کرم دوبارہ چیک کریں۔",
        "limit_msg": "🔒 آپ کی 3 مفت رپورٹس مکمل ہو گئی ہیں! بائیں جانب سے Pro Plan لیں۔"
    },
    "Bhojpuri": {
        "free_left": "🎁 {n}/3 फ्री रिपोर्ट बाकी बा",
        "free_done": "🔒 0/3 फ्री रिपोर्ट बाकी बा",
        "gen_btn": "ग्रोथ रिपोर्ट बनाईं 🔍",
        "fetching": "🔄 वीडियो के जानकारी जुटावल जा रहल बा... ⏳",
        "generating": "⚡ रिपोर्ट तैयार हो रहल बा... ⏳",
        "ready": "✅ ग्रोथ ऑडिट रिपोर्ट तैयार बा!",
        "dl_btn": "📥 पूरा रिपोर्ट डाउनलोड करीं (.txt)",
        "otp_sent": "✅ {em} पर 6-अंक के OTP भेज दिहल गइल बा!",
        "send_otp": "OTP भेजीं 📩",
        "verify_otp": "OTP जांच करीं ✅",
        "wrong_otp": "❌ गलत OTP! कृपया फेर से जांचीं।",
        "limit_msg": "🔒 राउर 3 गो फ्री रिपोर्ट पूरा हो गइल बा! बायां तरफ से Pro Plan लीं।"
    }
}

def get_ui(lang_label):
    if not lang_label or "Auto-Detect" in lang_label:
        return UI_TEXT["English"]
    base = lang_label.split("(")[0].strip()
    if base in UI_TEXT:
        return UI_TEXT[base]
    return UI_TEXT["English"]

# --- 5. COMPACT SINGLE-SCREEN DARK CSS ---
st.markdown("""
<style>
    [data-testid="stToolbarActions"], [data-testid="stDecoration"], #MainMenu, footer {
        display: none !important;
    }
    [data-testid="stSidebarCollapsedControl"] {
        display: flex !important;
        visibility: visible !important;
        z-index: 99999 !important;
    }
    .block-container {
        padding-top: 0.75rem !important;
        padding-bottom: 1rem !important;
        max-width: 1200px !important;
    }
    section[data-testid="stSidebar"] .block-container {
        padding-top: 0.6rem !important;
        padding-bottom: 0.5rem !important;
    }
    section[data-testid="stSidebar"] hr {
        margin: 0.45rem 0 !important;
    }
    .hero-card {
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
        margin: 0;
        font-size: 1.85rem;
        font-weight: 800;
        color: #ffffff;
        letter-spacing: 0.3px;
    }
    .hero-sub {
        margin: 4px 0 6px 0;
        color: #cbd5e1;
        font-size: 0.92rem;
    }
    .india-badge {
        display: inline-block;
        background: rgba(16, 185, 129, 0.15);
        border: 1px solid #10b981;
        color: #6ee7b7;
        padding: 2px 12px;
        border-radius: 999px;
        font-size: 0.78rem;
        font-weight: 600;
    }
    .user-strip {
        background: #1e293b;
        border: 1px solid #334155;
        border-radius: 10px;
        padding: 7px 14px;
        color: #e2e8f0;
        font-size: 0.9rem;
        margin-bottom: 6px;
    }
    .loading-pill {
        background: rgba(16, 185, 129, 0.15);
        border: 1px solid #10b981;
        color: #6ee7b7;
        padding: 7px 12px;
        border-radius: 8px;
        font-weight: 600;
        font-size: 0.88rem;
        text-align: center;
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
    "yt_vid": "",
    "yt_stats": None,
    "ig_report": "",
    "tt_report": "",
    "detected_lang": "",
    "exhausted_keys": []
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
        r = requests.get(SHEET_API, params={"device": user_id, "_ts": int(time.time())}, allow_redirects=True, timeout=8)
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
            r = requests.get(SHEET_API, params={"device": user_id, "inc": "1", "_ts": int(time.time())}, allow_redirects=True, timeout=8)
            if r.status_code == 200:
                return
        except Exception:
            time.sleep(0.5)

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
        }, allow_redirects=True, timeout=6)
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
        r = requests.get(SHEET_API, params={"pid": pid, "plan": plan, "_ts": int(time.time())}, allow_redirects=True, timeout=10)
        if r.status_code == 200:
            res = r.text.strip().upper()
            if res in ["VALID", "ALREADY_USED", "EXPIRED", "INVALID"]:
                return res
    except Exception:
        pass
    return "ERROR"

if not st.session_state.pro_unlocked:
    qp = st.query_params
    auto_pid = qp.get("razorpay_payment_id", "") or qp.get("payment_id", "")
    if auto_pid and str(auto_pid).startswith("pay_"):
        st_res = verify_payment_id(str(auto_pid), plan="1m")
        if st_res == "VALID":
            st.session_state.pro_unlocked = True
            st.session_state.pro_label = "PRO ACTIVE (Auto-Verified)"

def send_otp_email(to_email, code):
    if not SENDER_EMAIL or not SENDER_PASS:
        return False, "SMTP not configured"
    try:
        msg = MIMEText(
            f"Welcome to TrendSutra AI (1 AI • 1 India)!\n\n"
            f"Your 6-digit verification code is: {code}\n\n"
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

# --- 10. FAST 4-KEY SMART FAILOVER + DYNAMIC MODEL DISCOVERY ---
def clean_mentor_word(text):
    return text.replace("మెంటర్", "సలహాదారు").replace("స్ట్రాటజిస్ట్", "సలహాదారు")

@st.cache_data(ttl=3600, show_spinner=False)
def discover_active_models(api_key):
    try:
        client = genai.Client(api_key=api_key)
        found = []
        for m in client.models.list():
            name = m.name.replace("models/", "")
            if "flash" in name and "image" not in name and "audio" not in name and "tts" not in name and "1.5" not in name and "2.0" not in name and "2.5" not in name:
                found.append(name)
        found.sort(key=lambda x: (0 if "lite" in x else 1, x), reverse=True)
        if found:
            return found[:4]
    except Exception:
        pass
    return ["gemini-3.8-flash", "gemini-3.8-flash-lite", "gemini-3.5-flash", "gemini-flash-latest"]

def generate_report_stream(prompt):
    if not GEMINI_KEYS:
        raise RuntimeError("No Gemini API keys configured in Secrets.")

    active_keys = [k for k in GEMINI_KEYS if k not in st.session_state.exhausted_keys]
    if not active_keys:
        active_keys = list(GEMINI_KEYS)

    last_err = ""
    for api_key in active_keys:
        client = genai.Client(api_key=api_key)
        models_to_try = discover_active_models(api_key)
        for model_name in models_to_try:
            try:
                response = client.models.generate_content_stream(
                    model=model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.82,
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
                err_str = str(e)
                last_err = err_str
                if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str or "quota" in err_str.lower():
                    if api_key not in st.session_state.exhausted_keys:
                        st.session_state.exhausted_keys.append(api_key)
                    break
                continue
    raise RuntimeError(f"AI server is busy. Please try again in 5 seconds. ({last_err})")

# --- 11. SIDEBAR (NO-SCROLL COMPACT) ---
with st.sidebar:
    st.markdown("### ⚙️ Settings")
    selected_lang = st.selectbox(
        "🔍 Search Language (A–Z):",
        LANGUAGES,
        index=0
    )
    audience_scope = st.radio("Audience:", ["Regional", "Global", "Both"], horizontal=True)

    active_ui_lang = selected_lang if "Auto-Detect" not in selected_lang else (st.session_state.detected_lang or "English")
    ui = get_ui(active_ui_lang)

    st.divider()
    st.markdown("### 💎 Pro Plans")

    free_used = get_free_used_count(st.session_state.verified_email) if st.session_state.verified_email else 0
    free_left = max(0, 3 - free_used)

    if st.session_state.pro_unlocked:
        st.success(f"✅ {st.session_state.pro_label}")
    elif st.session_state.verified_email:
        if free_left > 0:
            st.info(ui["free_left"].format(n=free_left))
        else:
            st.error(ui["free_done"])
    else:
        st.info("🎁 Login to get **3 Free Reports**")

    st.markdown(f"• **1 Month:** ₹100 👉 [Pay ₹100]({RAZORPAY_1M})  • **12 Months:** ₹1,000 👉 [Pay ₹1,000]({RAZORPAY_12M})")
    plan_choice = st.radio("Plan:", ["1M (₹100)", "12M (₹1,000)"], horizontal=True, label_visibility="collapsed")
    pay_input = st.text_input("Payment ID:", placeholder="Paste Payment ID (pay_...)", label_visibility="collapsed")
    if st.button("Unlock Pro 🔓", use_container_width=True):
        if pay_input.strip():
            p_code = "12m" if "12M" in plan_choice else "1m"
            res = verify_payment_id(pay_input, plan=p_code)
            if res == "OWNER":
                st.session_state.pro_unlocked = True
                st.session_state.pro_label = "OWNER UNLIMITED ACTIVE"
                st.rerun()
            elif res == "VALID":
                st.session_state.pro_unlocked = True
                st.session_state.pro_label = f"PRO ACTIVE ({plan_choice})"
                st.rerun()
            elif res == "EXPIRED":
                st.error("⏰ Plan expired! Please recharge.")
            elif res == "ALREADY_USED":
                st.error("❌ Already used on 3 devices.")
            else:
                st.error("❌ Invalid Payment ID.")

    st.divider()
    st.caption("📩 support@aiengtel.com | © 2026 TrendSutra AI")

# --- 12. CENTERED HERO HEADER WITH LOGO ---
logo_html = ""
if os.path.exists("logo.png"):
    with open("logo.png", "rb") as img_f:
        b64_logo = base64.b64encode(img_f.read()).decode()
    logo_html = f'<img src="data:image/png;base64,{b64_logo}" style="height:42px; width:42px; border-radius:8px; object-fit:contain;" />'

st.markdown(f"""
<div class="hero-card">
    <div class="hero-title-row">
        {logo_html}
        <h1>TrendSutra AI</h1>
    </div>
    <div class="hero-sub">A to Z Growth Analyzer for YouTube, Instagram & TikTok Creators</div>
    <div class="india-badge">🇮🇳 1 AI • 1 India — Supports All 22 Indian Official Languages + Bhojpuri</div>
</div>
""", unsafe_allow_html=True)

# --- 13. COMPACT INLINE LOGIN BAR OR USER STRIP ---
if not st.session_state.verified_email and not st.session_state.pro_unlocked:
    lc1, lc2, lc3, lc4 = st.columns([2.2, 0.4, 2.3, 1.3], vertical_alignment="center")
    with lc1:
        if st.button("🔵 Continue with Gmail", type="primary", use_container_width=True):
            try:
                st.login("google")
            except Exception as e:
                st.error(f"Google Login error: {e}")
    with lc2:
        st.markdown("<div style='text-align:center; color:#94a3b8; font-weight:700;'>OR</div>", unsafe_allow_html=True)
    with lc3:
        email_in = st.text_input("Mail ID", placeholder="Login with Mail ID (e.g. name@gmail.com)", label_visibility="collapsed")
    with lc4:
        send_otp_clicked = st.button(ui["send_otp"], use_container_width=True)

    if send_otp_clicked:
        clean_em = email_in.strip().lower()
        if "@" not in clean_em or "." not in clean_em.split("@")[-1]:
            st.error("❌ Enter a valid Mail ID.")
        elif clean_em.split("@")[-1] in TEMP_DOMAINS:
            st.error("❌ Temporary emails are not allowed.")
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
        oc1, oc2 = st.columns([2, 1], vertical_alignment="center")
        with oc1:
            otp_in = st.text_input("OTP", placeholder="Enter 6-digit OTP received in your Mail ID", max_chars=6, label_visibility="collapsed")
        with oc2:
            if st.button(ui["verify_otp"], type="primary", use_container_width=True):
                if otp_in.strip() == st.session_state.otp_code:
                    st.session_state.verified_email = st.session_state.otp_target
                    st.session_state.otp_code = ""
                    st.rerun()
                else:
                    st.error(ui["wrong_otp"])
else:
    u1, u2 = st.columns([5, 1], vertical_alignment="center")
    with u1:
        badge_txt = f"✅ {st.session_state.pro_label}" if st.session_state.pro_unlocked else (ui["free_left"].format(n=free_left) if free_left > 0 else ui["free_done"])
        st.markdown(f'<div class="user-strip">👤 Logged in as <b>{st.session_state.verified_email or "PRO Member"}</b> &nbsp;|&nbsp; {badge_txt}</div>', unsafe_allow_html=True)
    with u2:
        if st.button("Logout", use_container_width=True):
            st.session_state.verified_email = ""
            st.session_state.pro_unlocked = False
            st.session_state.detected_lang = ""
            try:
                if hasattr(st, "logout"):
                    st.logout()
            except Exception:
                pass
            st.rerun()

# --- 14. PROMPT BUILDER (SINGLE-PASS LANGUAGE DETECTION + NATIVE SCRIPT) ---
def build_lang_instruction(sel_lang):
    if "Auto-Detect" in sel_lang:
        return """
FIRST: Detect the primary spoken/written language of the video from its title, description, tags, and viewer comments.
Start your response with the exact first line:
🌐 **Detected Video Language: [Language Name]**
THEN write the ENTIRE 6-section report (including ALL 6 section headings and every bullet point) in that detected language's **native script** (e.g., Telugu in తెలుగు script, Urdu in اردو script, Tamil in தமிழ் script, Hindi in हिन्दी script, Kannada in ಕನ್ನಡ script, etc. Never use Romanized/English letters for an Indian language unless the video itself is in English).
"""
    else:
        return f"""
Write the ENTIRE 6-section report (including ALL 6 section headings and every bullet point) strictly in **{sel_lang}** using its **authentic native script** (do NOT write Indian languages in English/Roman letters).
"""

# --- 15. MAIN WORKSPACE TABS ---
tab_yt, tab_ig, tab_tt = st.tabs(["📺 YouTube Analyzer", "📸 Instagram Reels Analyzer", "🎵 TikTok Analyzer"])

with tab_yt:
    yc1, yc2, yc3 = st.columns([3.4, 1.5, 1.5], vertical_alignment="center")
    with yc1:
        yt_url = st.text_input("YT Link", placeholder="Paste YouTube Video or Shorts Link...", label_visibility="collapsed")
    with yc2:
        run_yt = st.button(ui["gen_btn"], key="btn_yt", type="primary", use_container_width=True)
    with yc3:
        yt_status = st.empty()

    if run_yt:
        if not st.session_state.verified_email and not st.session_state.pro_unlocked:
            st.warning("🔐 Please login with Gmail or Mail ID above to generate your free report.")
        elif not yt_url.strip():
            st.warning("Please paste a YouTube link.")
        elif not st.session_state.pro_unlocked and free_left <= 0:
            st.error(ui["limit_msg"])
        else:
            vid_id = extract_youtube_id(yt_url.strip())
            if not vid_id:
                st.error("❌ Invalid YouTube Video or Shorts link.")
            else:
                yt_status.markdown(f'<div class="loading-pill">{ui["fetching"]}</div>', unsafe_allow_html=True)
                data = fetch_youtube_details(vid_id)
                if not data:
                    yt_status.empty()
                    st.error("❌ Could not fetch video details. Make sure the video is Public.")
                else:
                    st.session_state.yt_stats = data
                    st.session_state.yt_vid = vid_id
                    comments_block = "\n".join(data["comments"][:15]) if data["comments"] else "No public comments."
                    lang_rule = build_lang_instruction(selected_lang)
                    prompt = f"""
You are a warm, encouraging human social media growth advisor ("సలహాదారు" / "सलाहकार").
Write a comprehensive, deeply practical 6-section creator growth report (1,000 to 1,300 words) for a **{audience_scope}** audience.
Use simple, natural everyday spoken words (never use complex bookish terms, and never use the word 'మెంటర్'—use 'సలహాదారు' in Telugu).

{lang_rule}

VIDEO DATA:
- Channel: {data['channel']}
- Title: {data['title']}
- Views: {data['views']:,} | Likes: {data['likes']:,} | Comments: {data['comment_count']:,}
- Description: {data['description']}
- Tags: {', '.join(data['tags'])}
- Viewer Comments:
{comments_block}

STRICTLY INCLUDE THESE 6 SECTIONS (translate all 6 headings into the target native script):
### 🎬 1. Video Story Recap & Creator Appreciation
- Warmly retell the core story/message of this video so the creator feels you truly watched it, then genuinely praise their effort, presentation, and topic choice.

### 💬 2. Real Audience Comments & Reply Templates
- Quote 4–5 real comments from above, translate/summarize them naturally in the report language, explain what viewers love or request, and provide 3 copy-paste reply templates.

### 🔥 3. 3 Next Viral Video Ideas + 5-Second Opening Hooks
- Give 3 fresh follow-up video ideas tailored to this channel with exact word-for-word 5-second hooks and thumbnail concepts.

### 🎯 4. Copy-Paste SEO Makeover (Titles, Description & 15 Tags)
- Give 3 high-CTR title options, a strong 3-line SEO description hook, and 15 searchable comma-separated tags.

### 💰 5. Monetization & Brand Earning Blueprint
- Explain 3 practical ways this channel can earn money (AdSense, Affiliates, Sponsorships).

### 📅 6. 30-Day Step-by-Step Growth Action Plan
- Provide a Week 1 to Week 4 checklist to double views and subscribers.
"""
                    yt_status.markdown(f'<div class="loading-pill">{ui["generating"]}</div>', unsafe_allow_html=True)
                    report_box = st.empty()
                    full_text = ""
                    try:
                        for piece in generate_report_stream(prompt):
                            full_text += piece
                            report_box.markdown(full_text)
                        yt_status.empty()
                        st.session_state.yt_report = full_text
                        m_lang = re.search(r"Detected Video Language:\s*([A-Za-z]+)", full_text)
                        if m_lang:
                            st.session_state.detected_lang = m_lang.group(1).strip()
                        if not st.session_state.pro_unlocked:
                            increment_free_used(st.session_state.verified_email)
                        log_usage_to_sheet(st.session_state.verified_email or "PRO", "YouTube", yt_url.strip())
                        st.rerun()
                    except Exception as e:
                        yt_status.empty()
                        st.error(str(e))

    if st.session_state.yt_report:
        if st.session_state.yt_stats:
            d = st.session_state.yt_stats
            m1, m2, m3 = st.columns(3)
            m1.metric("👀 Views", f"{d['views']:,}")
            m2.metric("👍 Likes", f"{d['likes']:,}")
            m3.metric("💬 Comments", f"{d['comment_count']:,}")
        st.success(ui["ready"])
        st.download_button(
            ui["dl_btn"],
            data=st.session_state.yt_report,
            file_name=f"TrendSutra_YouTube_{st.session_state.yt_vid or 'Report'}.txt",
            mime="text/plain",
            use_container_width=True
        )
        st.markdown(st.session_state.yt_report)

with tab_ig:
    ic1, ic2, ic3 = st.columns([3.4, 1.5, 1.5], vertical_alignment="center")
    with ic1:
        ig_url = st.text_input("IG Link", placeholder="Paste Instagram Reel Link...", label_visibility="collapsed")
    with ic2:
        run_ig = st.button(ui["gen_btn"], key="btn_ig", type="primary", use_container_width=True)
    with ic3:
        ig_status = st.empty()

    if run_ig:
        if not st.session_state.verified_email and not st.session_state.pro_unlocked:
            st.warning("🔐 Please login with Gmail or Mail ID above to generate your free report.")
        elif not ig_url.strip():
            st.warning("Please paste an Instagram Reel link.")
        elif not st.session_state.pro_unlocked and free_left <= 0:
            st.error(ui["limit_msg"])
        else:
            ig_status.markdown(f'<div class="loading-pill">{ui["generating"]}</div>', unsafe_allow_html=True)
            lang_rule = build_lang_instruction(selected_lang)
            ig_prompt = f"""
You are a warm, encouraging human Instagram Reels growth advisor ("సలహాదారు").
Write a detailed 6-section Instagram Reels growth audit (900+ words) for a **{audience_scope}** audience using simple everyday spoken words.
{lang_rule}
Instagram Reel Link: {ig_url.strip()}
Include all 6 sections in the target native script:
1. Creator Appreciation & Reel Hook Strategy
2. Watch-Time, Audio & Retention Breakdown
3. 3 Viral Follow-Up Reel Ideas + 3-Second Hooks
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
                m_lang = re.search(r"Detected Video Language:\s*([A-Za-z]+)", full_text)
                if m_lang:
                    st.session_state.detected_lang = m_lang.group(1).strip()
                if not st.session_state.pro_unlocked:
                    increment_free_used(st.session_state.verified_email)
                log_usage_to_sheet(st.session_state.verified_email or "PRO", "Instagram", ig_url.strip())
                st.rerun()
            except Exception as e:
                ig_status.empty()
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
    tc1, tc2, tc3 = st.columns([3.4, 1.5, 1.5], vertical_alignment="center")
    with tc1:
        tt_url = st.text_input("TT Link", placeholder="Paste TikTok Video Link...", label_visibility="collapsed")
    with tc2:
        run_tt = st.button(ui["gen_btn"], key="btn_tt", type="primary", use_container_width=True)
    with tc3:
        tt_status = st.empty()

    if run_tt:
        if not st.session_state.verified_email and not st.session_state.pro_unlocked:
            st.warning("🔐 Please login with Gmail or Mail ID above to generate your free report.")
        elif not tt_url.strip():
            st.warning("Please paste a TikTok video link.")
        elif not st.session_state.pro_unlocked and free_left <= 0:
            st.error(ui["limit_msg"])
        else:
            tt_status.markdown(f'<div class="loading-pill">{ui["generating"]}</div>', unsafe_allow_html=True)
            lang_rule = build_lang_instruction(selected_lang)
            tt_prompt = f"""
You are a warm, encouraging human TikTok growth advisor ("సలహాదారు").
Write a detailed 6-section TikTok growth audit (900+ words) for a **{audience_scope}** audience using simple everyday spoken words.
{lang_rule}
TikTok Video Link: {tt_url.strip()}
Include all 6 sections in the target native script:
1. Creator Appreciation & Viral Potential Overview
2. Completion Rate & Looping Hook Formula
3. 3 Viral Follow-Up Video Ideas + 3-Second Hooks
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
                m_lang = re.search(r"Detected Video Language:\s*([A-Za-z]+)", full_text)
                if m_lang:
                    st.session_state.detected_lang = m_lang.group(1).strip()
                if not st.session_state.pro_unlocked:
                    increment_free_used(st.session_state.verified_email)
                log_usage_to_sheet(st.session_state.verified_email or "PRO", "TikTok", tt_url.strip())
                st.rerun()
            except Exception as e:
                tt_status.empty()
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
