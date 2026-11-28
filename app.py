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
from datetime import datetime

# --- 1. PAGE CONFIG ---
page_icon = "logo.png" if os.path.exists("logo.png") else "📊"
st.set_page_config(page_title="TrendSutra AI - 1 AI • 1 India", page_icon=page_icon, layout="wide")

# --- 2. LOAD SECRETS ---
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

# --- 3. A-TO-Z LANGUAGES & UI TRANSLATIONS ---
LANGUAGES_A_TO_Z = [
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

UI_STRINGS = {
    "Telugu": {
        "email_ph": "మీ Email ID ఎంటర్ చేయండి...",
        "send_otp": "OTP పంపండి 📩",
        "otp_sent": "కి 6-అంకెల OTP పంపబడింది! ఇన్‌బాక్స్ / Spam చెక్ చేయండి.",
        "otp_ph": "6-అంకెల OTP",
        "verify_btn": "OTP నిర్ధారించండి ✅",
        "otp_err": "❌ తప్పు OTP! దయచేసి మళ్ళీ చెక్ చేయండి.",
        "invalid_email": "❌ సరైన Email ID ఎంటర్ చేయండి.",
        "temp_email": "❌ తాత్కాలిక ఈమెయిల్ అనుమతించబడదు.",
        "free_left": "ఉచిత రిపోర్ట్‌లు మిగిలాయి",
        "free_done": "మీ 3 ఉచిత రిపోర్ట్‌లు పూర్తయ్యాయి!",
        "login_for_free": "లాగిన్ అయి 3 ఉచిత రిపోర్ట్‌లు పొందండి",
        "gen_yt": "గ్రోత్ రిపోర్ట్ తయారు చేయండి 🔍",
        "gen_ig": "Instagram రిపోర్ట్ తయారు చేయండి 🔍",
        "gen_tt": "TikTok రిపోర్ట్ తయారు చేయండి 🔍",
        "fetching": "🔄 వీడియో వివరాలు & కామెంట్లు సేకరిస్తోంది... ⏳",
        "generating": "⚡ రిపోర్ట్ తయారవుతోంది... ⏳",
        "done": "✅ గ్రోత్ ఆడిట్ రిపోర్ట్ సిద్ధమైంది!",
        "download": "📥 పూర్తి రిపోర్ట్ డౌన్‌లోడ్ చేయండి (.txt)",
        "paste_warn": "దయచేసి వీడియో లింక్ పేస్ట్ చేయండి.",
        "lock_err": "🔒 మీ 3 ఉచిత రిపోర్ట్‌లు పూర్తయ్యాయి! అన్‌లిమిటెడ్ కోసం ఎడమ వైపు Pro Plan తీసుకోండి.",
        "bad_link": "❌ సరైన వీడియో లింక్ ఇవ్వండి.",
        "no_data": "❌ వీడియో వివరాలు పొందలేకపోయాము. Public లో ఉందో లేదో చూడండి."
    },
    "Hindi": {
        "email_ph": "अपना Email ID दर्ज करें...",
        "send_otp": "OTP भेजें 📩",
        "otp_sent": "पर 6-अंकों का OTP भेजा गया है! इनबॉक्स / स्पैम देखें।",
        "otp_ph": "6-अंकों का OTP",
        "verify_btn": "OTP सत्यापित करें ✅",
        "otp_err": "❌ गलत OTP! कृपया पुनः जांचें।",
        "invalid_email": "❌ सही Email ID दर्ज करें।",
        "temp_email": "❌ अस्थायी ईमेल मान्य नहीं है।",
        "free_left": "मुफ्त रिपोर्ट शेष हैं",
        "free_done": "आपकी 3 मुफ्त रिपोर्ट पूरी हो गई हैं!",
        "login_for_free": "लॉगिन करें और 3 मुफ्त रिपोर्ट पाएं",
        "gen_yt": "ग्रोथ रिपोर्ट बनाएं 🔍",
        "gen_ig": "Instagram रिपोर्ट बनाएं 🔍",
        "gen_tt": "TikTok रिपोर्ट बनाएं 🔍",
        "fetching": "🔄 वीडियो विवरण और कमेंट्स लिए जा रहे हैं... ⏳",
        "generating": "⚡ रिपोर्ट तैयार हो रही है... ⏳",
        "done": "✅ ग्रोथ ऑडिट रिपोर्ट तैयार है!",
        "download": "📥 पूरी रिपोर्ट डाउनलोड करें (.txt)",
        "paste_warn": "कृपया वीडियो लिंक पेस्ट करें।",
        "lock_err": "🔒 आपकी 3 मुफ्त रिपोर्ट पूरी हो गई हैं! अनलिमिटेड के लिए Pro Plan लें।",
        "bad_link": "❌ सही वीडियो लिंक दर्ज करें।",
        "no_data": "❌ वीडियो डेटा नहीं मिल सका। जांचें कि वीडियो Public है।"
    },
    "Tamil": {
        "email_ph": "உங்கள் Email ID ஐ உள்ளிடவும்...",
        "send_otp": "OTP அனுப்பு 📩",
        "otp_sent": "க்கு 6-இலக்க OTP அனுப்பப்பட்டுள்ளது! Inbox / Spam பார்க்கவும்.",
        "otp_ph": "6-இலக்க OTP",
        "verify_btn": "OTP சரிபார் ✅",
        "otp_err": "❌ தவறான OTP! மீண்டும் சரிபார்க்கவும்.",
        "invalid_email": "❌ சரியான Email ID ஐ உள்ளிடவும்.",
        "temp_email": "❌ தற்காலிக மின்னஞ்சல் அனுமதிக்கப்படாது.",
        "free_left": "இலவச அறிக்கைகள் மீதமுள்ளன",
        "free_done": "உங்கள் 3 இலவச அறிக்கைகள் முடிந்துவிட்டன!",
        "login_for_free": "உள்நுழைந்து 3 இலவச அறிக்கைகளைப் பெறுங்கள்",
        "gen_yt": "வளர்ச்சி அறிக்கையை உருவாக்கு 🔍",
        "gen_ig": "Instagram அறிக்கையை உருவாக்கு 🔍",
        "gen_tt": "TikTok அறிக்கையை உருவாக்கு 🔍",
        "fetching": "🔄 வீடியோ விவரங்கள் சேகரிக்கப்படுகின்றன... ⏳",
        "generating": "⚡ அறிக்கை உருவாக்கப்படுகிறது... ⏳",
        "done": "✅ வளர்ச்சி அறிக்கை தயாராகிவிட்டது!",
        "download": "📥 முழு அறிக்கையைப் பதிவிறக்கவும் (.txt)",
        "paste_warn": "வீடியோ இணைப்பை ஒட்டவும்.",
        "lock_err": "🔒 உங்கள் 3 இலவச அறிக்கைகள் முடிந்துவிட்டன! Pro Plan பெறவும்.",
        "bad_link": "❌ சரியான வீடியோ இணைப்பை வழங்கவும்.",
        "no_data": "❌ வீடியோ விவரங்களைப் பெற முடியவில்லை."
    },
    "Kannada": {
        "email_ph": "ನಿಮ್ಮ Email ID ನಮೂದಿಸಿ...",
        "send_otp": "OTP ಕಳುಹಿಸಿ 📩",
        "otp_sent": "ಗೆ 6-ಅಂಕಿಯ OTP ಕಳುಹಿಸಲಾಗಿದೆ! ಇನ್‌ಬಾಕ್ಸ್ / ಸ್ಪ್ಯಾಮ್ ಪರಿಶೀಲಿಸಿ.",
        "otp_ph": "6-ಅಂಕಿಯ OTP",
        "verify_btn": "OTP ದೃಢೀಕರಿಸಿ ✅",
        "otp_err": "❌ ತಪ್ಪಾದ OTP! ದಯವಿಟ್ಟು ಮತ್ತೆ ಪರಿಶೀಲಿಸಿ.",
        "invalid_email": "❌ ಸರಿಯಾದ Email ID ನಮೂದಿಸಿ.",
        "temp_email": "❌ ತಾತ್ಕಾಲಿಕ ಇಮೇಲ್ ಅನುಮತಿಸಲಾಗುವುದಿಲ್ಲ.",
        "free_left": "ಉಚಿತ ವರದಿಗಳು ಉಳಿದಿವೆ",
        "free_done": "ನಿಮ್ಮ 3 ಉಚಿತ ವರದಿಗಳು ಪೂರ್ಣಗೊಂಡಿವೆ!",
        "login_for_free": "ಲಾಗಿನ್ ಮಾಡಿ 3 ಉಚಿತ ವರದಿಗಳನ್ನು ಪಡೆಯಿರಿ",
        "gen_yt": "ಗ್ರೋತ್ ವರದಿ ತಯಾರಿಸಿ 🔍",
        "gen_ig": "Instagram ವರದಿ ತಯಾರಿಸಿ 🔍",
        "gen_tt": "TikTok ವರದಿ ತಯಾರಿಸಿ 🔍",
        "fetching": "🔄 ವೀಡಿಯೊ ವಿವರಗಳನ್ನು ಸಂಗ್ರಹಿಸಲಾಗುತ್ತಿದೆ... ⏳",
        "generating": "⚡ ವರದಿ ಸಿದ್ಧವಾಗುತ್ತಿದೆ... ⏳",
        "done": "✅ ಗ್ರೋತ್ ವರದಿ ಸಿದ್ಧವಾಗಿದೆ!",
        "download": "📥 ಪೂರ್ಣ ವರದಿ ಡೌನ್‌ಲೋಡ್ ಮಾಡಿ (.txt)",
        "paste_warn": "ದಯವಿಟ್ಟು ವೀಡಿಯೊ ಲಿಂಕ್ ಅಂಟಿಸಿ.",
        "lock_err": "🔒 ನಿಮ್ಮ 3 ಉಚಿತ ವರದಿಗಳು ಮುಗಿದಿವೆ! Pro Plan ತೆಗೆದುಕೊಳ್ಳಿ.",
        "bad_link": "❌ ಸರಿಯಾದ ವೀಡಿಯೊ ಲಿಂಕ್ ನೀಡಿ.",
        "no_data": "❌ ವೀಡಿಯೊ ವಿವರಗಳನ್ನು ಪಡೆಯಲು ಸಾಧ್ಯವಾಗಲಿಲ್ಲ."
    },
    "Malayalam": {
        "email_ph": "നിങ്ങളുടെ Email ID നൽകുക...",
        "send_otp": "OTP അയയ്ക്കുക 📩",
        "otp_sent": "ലേക്ക് 6-അക്ക OTP അയച്ചിട്ടുണ്ട്! ഇൻബോക്സ് / സ്പാം പരിശോധിക്കുക.",
        "otp_ph": "6-അക്ക OTP",
        "verify_btn": "OTP സ്ഥിരീകരിക്കുക ✅",
        "otp_err": "❌ തെറ്റായ OTP! വീണ്ടും പരിശോധിക്കുക.",
        "invalid_email": "❌ ശരിയായ Email ID നൽകുക.",
        "temp_email": "❌ താൽക്കാലിക ഇമെയിൽ അനുവദനീയമല്ല.",
        "free_left": "സൗജന്യ റിപ്പോർട്ടുകൾ ബാക്കിയുണ്ട്",
        "free_done": "നിങ്ങളുടെ 3 സൗജന്യ റിപ്പോർട്ടുകൾ പൂർത്തിയായി!",
        "login_for_free": "ലോഗിൻ ചെയ്ത് 3 സൗജന്യ റിപ്പോർട്ടുകൾ നേടുക",
        "gen_yt": "ഗ്രോത്ത് റിപ്പോർട്ട് തയ്യാറാക്കുക 🔍",
        "gen_ig": "Instagram റിപ്പോർട്ട് തയ്യാറാക്കുക 🔍",
        "gen_tt": "TikTok റിപ്പോർട്ട് തയ്യാറാക്കുക 🔍",
        "fetching": "🔄 വീഡിയോ വിവരങ്ങൾ ശേഖരിക്കുന്നു... ⏳",
        "generating": "⚡ റിപ്പോർട്ട് തയ്യാറാകുന്നു... ⏳",
        "done": "✅ ഗ്രോത്ത് റിപ്പോർട്ട് തയ്യാറായി!",
        "download": "📥 പൂർണ്ണ റിപ്പോർട്ട് ഡൗൺലോഡ് ചെയ്യുക (.txt)",
        "paste_warn": "ദയവായി വീഡിയോ ലിങ്ക് പേസ്റ്റ് ചെയ്യുക.",
        "lock_err": "🔒 നിങ്ങളുടെ 3 സൗജന്യ റിപ്പോർട്ടുകൾ തീർന്നു! Pro Plan എടുക്കുക.",
        "bad_link": "❌ ശരിയായ വീഡിയോ ലിങ്ക് നൽകുക.",
        "no_data": "❌ വീഡിയോ വിവരങ്ങൾ ലഭ്യമായില്ല."
    },
    "Marathi": {
        "email_ph": "तुमचा Email ID टाका...",
        "send_otp": "OTP पाठवा 📩",
        "otp_sent": "वर 6-अंकी OTP पाठवला आहे! इनबॉक्स / स्पॅम तपासा.",
        "otp_ph": "6-अंकी OTP",
        "verify_btn": "OTP सत्यापित करा ✅",
        "otp_err": "❌ चुकीचा OTP! कृपया पुन्हा तपासा.",
        "invalid_email": "❌ योग्य Email ID टाका.",
        "temp_email": "❌ तात्पुरता ईमेल चालणार नाही.",
        "free_left": "मोफत रिपोर्ट शिल्लक आहेत",
        "free_done": "तुमचे 3 मोफत रिपोर्ट पूर्ण झाले आहेत!",
        "login_for_free": "लॉगिन करा आणि 3 मोफत रिपोर्ट मिळवा",
        "gen_yt": "ग्रोथ रिपोर्ट तयार करा 🔍",
        "gen_ig": "Instagram रिपोर्ट तयार करा 🔍",
        "gen_tt": "TikTok रिपोर्ट तयार करा 🔍",
        "fetching": "🔄 व्हिडिओ माहिती गोळा केली जात आहे... ⏳",
        "generating": "⚡ रिपोर्ट तयार होत आहे... ⏳",
        "done": "✅ ग्रोथ ऑडिट रिपोर्ट तयार आहे!",
        "download": "📥 संपूर्ण रिपोर्ट डाउनलोड करा (.txt)",
        "paste_warn": "कृपया व्हिडिओ लिंक पेस्ट करा.",
        "lock_err": "🔒 तुमचे 3 मोफत रिपोर्ट संपले आहेत! Pro Plan घ्या.",
        "bad_link": "❌ योग्य व्हिडिओ लिंक द्या.",
        "no_data": "❌ व्हिडिओ माहिती मिळू शकली नाही."
    },
    "Bengali": {
        "email_ph": "আপনার Email ID লিখুন...",
        "send_otp": "OTP পাঠান 📩",
        "otp_sent": "-এ ৬-অঙ্কের OTP পাঠানো হয়েছে! ইনবক্স / স্প্যাম দেখুন।",
        "otp_ph": "৬-অঙ্কের OTP",
        "verify_btn": "OTP যাচাই করুন ✅",
        "otp_err": "❌ ভুল OTP! অনুগ্রহ করে আবার দেখুন।",
        "invalid_email": "❌ সঠিক Email ID লিখুন।",
        "temp_email": "❌ অস্থায়ী ইমেল গ্রহণযোগ্য নয়।",
        "free_left": "বিনামূল্যে রিপোর্ট বাকি আছে",
        "free_done": "আপনার ৩টি বিনামূল্যে রিপোর্ট শেষ হয়েছে!",
        "login_for_free": "লগইন করে ৩টি বিনামূল্যে রিপোর্ট পান",
        "gen_yt": "গ্রোথ রিপোর্ট তৈরি করুন 🔍",
        "gen_ig": "Instagram রিপোর্ট তৈরি করুন 🔍",
        "gen_tt": "TikTok রিপোর্ট তৈরি করুন 🔍",
        "fetching": "🔄 ভিডিওর তথ্য সংগ্রহ করা হচ্ছে... ⏳",
        "generating": "⚡ রিপোর্ট তৈরি হচ্ছে... ⏳",
        "done": "✅ গ্রোথ অডিট রিপোর্ট তৈরি হয়েছে!",
        "download": "📥 সম্পূর্ণ রিপোর্ট ডাউনলোড করুন (.txt)",
        "paste_warn": "অনুগ্রহ করে ভিডিও লিংক পেস্ট করুন।",
        "lock_err": "🔒 আপনার ৩টি ফ্রি রিপোর্ট শেষ! আনলিমিটেডের জন্য Pro Plan নিন।",
        "bad_link": "❌ সঠিক ভিডিও লিংক দিন।",
        "no_data": "❌ ভিডিওর তথ্য পাওয়া যায়নি।"
    },
    "Gujarati": {
        "email_ph": "તમારું Email ID દાખલ કરો...",
        "send_otp": "OTP મોકલો 📩",
        "otp_sent": "પર 6-અંકનો OTP મોકલવામાં આવ્યો છે! ઇનબોક્સ / સ્પામ તપાસો.",
        "otp_ph": "6-અંકનો OTP",
        "verify_btn": "OTP ચકાસો ✅",
        "otp_err": "❌ ખોટો OTP! કૃપા કરીને ફરી તપાસો.",
        "invalid_email": "❌ સાચું Email ID દાખલ કરો.",
        "temp_email": "❌ કામચલાઉ ઇમેઇલ માન્ય નથી.",
        "free_left": "મફત રિપોર્ટ બાકી છે",
        "free_done": "તમારા 3 મફત રિપોર્ટ પૂરા થઈ ગયા છે!",
        "login_for_free": "લોગિન કરો અને 3 મફત રિપોર્ટ મેળવો",
        "gen_yt": "ગ્રોથ રિપોર્ટ બનાવો 🔍",
        "gen_ig": "Instagram રિપોર્ટ બનાવો 🔍",
        "gen_tt": "TikTok રિપોર્ટ બનાવો 🔍",
        "fetching": "🔄 વિડિયો વિગતો મેળવવામાં આવી રહી છે... ⏳",
        "generating": "⚡ રિપોર્ટ તૈયાર થઈ રહ્યો છે... ⏳",
        "done": "✅ ગ્રોથ ઓડિટ રિપોર્ટ તૈયાર છે!",
        "download": "📥 સંપૂર્ણ રિપોર્ટ ડાઉનલોડ કરો (.txt)",
        "paste_warn": "કૃપા કરીને વિડિયો લિંક પેસ્ટ કરો.",
        "lock_err": "🔒 તમારા 3 મફત રિપોર્ટ પૂરા થઈ ગયા છે! Pro Plan લો.",
        "bad_link": "❌ સાચી વિડિયો લિંક આપો.",
        "no_data": "❌ વિડિયો વિગતો મળી શકી નથી."
    },
    "Punjabi": {
        "email_ph": "ਆਪਣਾ Email ID ਦਰਜ ਕਰੋ...",
        "send_otp": "OTP ਭੇਜੋ 📩",
        "otp_sent": "ਤੇ 6-ਅੰਕਾਂ ਦਾ OTP ਭੇਜਿਆ ਗਿਆ ਹੈ! ਇਨਬਾਕਸ / ਸਪੈਮ ਚੈੱਕ ਕਰੋ।",
        "otp_ph": "6-ਅੰਕਾਂ ਦਾ OTP",
        "verify_btn": "OTP ਪੁਸ਼ਟੀ ਕਰੋ ✅",
        "otp_err": "❌ ਗਲਤ OTP! ਕਿਰਪਾ ਕਰਕੇ ਦੁਬਾਰਾ ਚੈੱਕ ਕਰੋ।",
        "invalid_email": "❌ ਸਹੀ Email ID ਦਰਜ ਕਰੋ।",
        "temp_email": "❌ ਅਸਥਾਈ ਈਮੇਲ ਮਨਜ਼ੂਰ ਨਹੀਂ ਹੈ।",
        "free_left": "ਮੁਫ਼ਤ ਰਿਪੋਰਟਾਂ ਬਾਕੀ ਹਨ",
        "free_done": "ਤੁਹਾਡੀਆਂ 3 ਮੁਫ਼ਤ ਰਿਪੋਰਟਾਂ ਪੂਰੀਆਂ ਹੋ ਗਈਆਂ ਹਨ!",
        "login_for_free": "ਲੌਗਇਨ ਕਰੋ ਅਤੇ 3 ਮੁਫ਼ਤ ਰਿਪੋਰਟਾਂ ਪਾਓ",
        "gen_yt": "ਗਰੋਥ ਰਿਪੋਰਟ ਤਿਆਰ ਕਰੋ 🔍",
        "gen_ig": "Instagram ਰਿਪੋਰਟ ਤਿਆਰ ਕਰੋ 🔍",
        "gen_tt": "TikTok ਰਿਪੋਰਟ ਤਿਆਰ ਕਰੋ 🔍",
        "fetching": "🔄 ਵੀਡੀਓ ਵੇਰਵੇ ਲਏ ਜਾ ਰਹੇ ਹਨ... ⏳",
        "generating": "⚡ ਰਿਪੋਰਟ ਤਿਆਰ ਹੋ ਰਹੀ ਹੈ... ⏳",
        "done": "✅ ਗਰੋਥ ਆਡਿਟ ਰਿਪੋਰਟ ਤਿਆਰ ਹੈ!",
        "download": "📥 ਪੂਰੀ ਰਿਪੋਰਟ ਡਾਊਨਲੋਡ ਕਰੋ (.txt)",
        "paste_warn": "ਕਿਰਪਾ ਕਰਕੇ ਵੀਡੀਓ ਲਿੰਕ ਪੇਸਟ ਕਰੋ।",
        "lock_err": "🔒 ਤੁਹਾਡੀਆਂ 3 ਮੁਫ਼ਤ ਰਿਪੋਰਟਾਂ ਖ਼ਤਮ ਹੋ ਗਈਆਂ ਹਨ! Pro Plan ਲਓ।",
        "bad_link": "❌ ਸਹੀ ਵੀਡੀਓ ਲਿੰਕ ਦਿਓ।",
        "no_data": "❌ ਵੀਡੀਓ ਡਾਟਾ ਨਹੀਂ ਮਿਲ ਸਕਿਆ।"
    },
    "Odia": {
        "email_ph": "ଆପଣଙ୍କ Email ID ଦିଅନ୍ତୁ...",
        "send_otp": "OTP ପଠାନ୍ତୁ 📩",
        "otp_sent": "କୁ 6-ଅଙ୍କ ବିଶିଷ୍ଟ OTP ପଠାଯାଇଛି! ଇନବକ୍ସ / ସ୍ପାମ୍ ଯାଞ୍ଚ କରନ୍ତୁ।",
        "otp_ph": "6-ଅଙ୍କ OTP",
        "verify_btn": "OTP ଯାଞ୍ଚ କରନ୍ତୁ ✅",
        "otp_err": "❌ ଭୁଲ୍ OTP! ଦୟାକରି ପୁଣି ଯାଞ୍ଚ କରନ୍ତୁ।",
        "invalid_email": "❌ ସଠିକ୍ Email ID ଦିଅନ୍ତୁ।",
        "temp_email": "❌ ଅସ୍ଥାୟୀ ଇମେଲ୍ ଗ୍ରହଣୀୟ ନୁହେଁ।",
        "free_left": "ମାଗଣା ରିପୋର୍ଟ ବାକି ଅଛି",
        "free_done": "ଆପଣଙ୍କର 3ଟି ମାଗଣା ରିପୋର୍ଟ ଶେଷ ହୋଇଛି!",
        "login_for_free": "ଲଗଇନ୍ କରି 3ଟି ମାଗଣା ରିପୋର୍ଟ ପାଆନ୍ତୁ",
        "gen_yt": "ଗ୍ରୋଥ୍ ରିପୋର୍ଟ ତିଆରି କରନ୍ତୁ 🔍",
        "gen_ig": "Instagram ରିପୋର୍ଟ ତିଆରି କରନ୍ତୁ 🔍",
        "gen_tt": "TikTok ରିପୋର୍ଟ ତିଆରି କରନ୍ତୁ 🔍",
        "fetching": "🔄 ଭିଡିଓ ତଥ୍ୟ ସଂଗ୍ରହ କରାଯାଉଛି... ⏳",
        "generating": "⚡ ରିପୋର୍ଟ ପ୍ରସ୍ତୁତ ହେଉଛି... ⏳",
        "done": "✅ ଗ୍ରୋଥ୍ ଅଡିଟ୍ ରିପୋର୍ଟ ପ୍ରସ୍ତୁତ!",
        "download": "📥 ସମ୍ପୂର୍ଣ୍ଣ ରିପୋର୍ଟ ଡାଉନଲୋଡ୍ କରନ୍ତୁ (.txt)",
        "paste_warn": "ଦୟାକରି ଭିଡିଓ ଲିଙ୍କ୍ ପେଷ୍ଟ କରନ୍ତୁ।",
        "lock_err": "🔒 ଆପଣଙ୍କର 3ଟି ମାଗଣା ରିପୋର୍ଟ ଶେଷ ହୋଇଛି! Pro Plan ନିଅନ୍ତୁ।",
        "bad_link": "❌ ସଠିକ୍ ଭିଡିଓ ଲିଙ୍କ୍ ଦିଅନ୍ତୁ।",
        "no_data": "❌ ଭିଡିଓ ତଥ୍ୟ ମିଳିପାରିଲା ନାହିଁ।"
    },
    "Assamese": {
        "email_ph": "আপোনাৰ Email ID লিখক...",
        "send_otp": "OTP পঠাওক 📩",
        "otp_sent": "লৈ ৬-অংকৰ OTP পঠোৱা হৈছে! ইনবক্স / স্পেম চাওক।",
        "otp_ph": "৬-অংকৰ OTP",
        "verify_btn": "OTP নিশ্চিত কৰক ✅",
        "otp_err": "❌ ভুল OTP! অনুগ্ৰহ কৰি পুনৰ চাওক।",
        "invalid_email": "❌ সঠিক Email ID লিখক।",
        "temp_email": "❌ অস্থায়ী ইমেইল গ্ৰহণযোগ্য নহয়।",
        "free_left": "বিনামূলীয়া ৰিপৰ্ট বাকী আছে",
        "free_done": "আপোনাৰ ৩টা বিনামূলীয়া ৰিপৰ্ট সম্পূৰ্ণ হৈছে!",
        "login_for_free": "লগইন কৰি ৩টা বিনামূলীয়া ৰিপৰ্ট পাওক",
        "gen_yt": "গ্ৰোথ ৰিপৰ্ট তৈয়াৰ কৰক 🔍",
        "gen_ig": "Instagram ৰিপৰ্ট তৈয়াৰ কৰক 🔍",
        "gen_tt": "TikTok ৰিপৰ্ট তৈয়াৰ কৰক 🔍",
        "fetching": "🔄 ভিডিঅ'ৰ তথ্য সংগ্ৰহ কৰা হৈছে... ⏳",
        "generating": "⚡ ৰিপৰ্ট তৈয়াৰ হৈ আছে... ⏳",
        "done": "✅ গ্ৰোথ অডিট ৰিপৰ্ট সাজু হৈছে!",
        "download": "📥 সম্পূৰ্ণ ৰিপৰ্ট ডাউনলোড কৰক (.txt)",
        "paste_warn": "অনুগ্ৰহ কৰি ভিডিঅ' লিংক পেষ্ট কৰক।",
        "lock_err": "🔒 আপোনাৰ ৩টা বিনামূলীয়া ৰিপৰ্ট শেষ হৈছে! Pro Plan লওক।",
        "bad_link": "❌ সঠিক ভিডিঅ' লিংক দিয়ক।",
        "no_data": "❌ ভিডিঅ'ৰ তথ্য পোৱা নগ'ল।"
    },
    "Urdu": {
        "email_ph": "اپنا Email ID درج کریں...",
        "send_otp": "OTP بھیجیں 📩",
        "otp_sent": "پر 6 ہندسوں کا OTP بھیج دیا گیا ہے! ان باکس / اسپام چیک کریں۔",
        "otp_ph": "6 ہندسوں کا OTP",
        "verify_btn": "OTP کی تصدیق کریں ✅",
        "otp_err": "❌ غلط OTP! براہ کرم دوبارہ چیک کریں۔",
        "invalid_email": "❌ درست Email ID درج کریں۔",
        "temp_email": "❌ عارضی ای میل قابل قبول نہیں ہے۔",
        "free_left": "مفت رپورٹس باقی ہیں",
        "free_done": "آپ کی 3 مفت رپورٹس مکمل ہو گئی ہیں!",
        "login_for_free": "لاگ ان کریں اور 3 مفت رپورٹس حاصل کریں",
        "gen_yt": "گروتھ رپورٹ بنائیں 🔍",
        "gen_ig": "Instagram رپورٹ بنائیں 🔍",
        "gen_tt": "TikTok رپورٹ بنائیں 🔍",
        "fetching": "🔄 ویڈیو کی تفصیلات حاصل کی جا رہی ہیں... ⏳",
        "generating": "⚡ رپورٹ تیار ہو رہی ہے... ⏳",
        "done": "✅ گروتھ آڈٹ رپورٹ تیار ہے!",
        "download": "📥 مکمل رپورٹ ڈاؤن لوڈ کریں (.txt)",
        "paste_warn": "براہ کرم ویڈیو لنک پیسٹ کریں۔",
        "lock_err": "🔒 آپ کی 3 مفت رپورٹس ختم ہو گئی ہیں! Pro Plan لیں۔",
        "bad_link": "❌ درست ویڈیو لنک دیں۔",
        "no_data": "❌ ویڈیو کا ڈیٹا نہیں مل سکا۔"
    },
    "Bhojpuri": {
        "email_ph": "आपन Email ID डालीं...",
        "send_otp": "OTP भेजीं 📩",
        "otp_sent": "पर 6-अंक के OTP भेज दिहल गइल बा! इनबॉक्स / स्पैम देखीं।",
        "otp_ph": "6-अंक के OTP",
        "verify_btn": "OTP सत्यापित करीं ✅",
        "otp_err": "❌ गलत OTP बा! फेर से जाँच करीं।",
        "invalid_email": "❌ सही Email ID डालीं।",
        "temp_email": "❌ टेम्प ईमेल मान्य नइखे।",
        "free_left": "फ्री रिपोर्ट बाचल बा",
        "free_done": "रउआ 3 गो फ्री रिपोर्ट पूरा हो गइल बा!",
        "login_for_free": "लॉगिन करीं आ 3 फ्री रिपोर्ट पाईं",
        "gen_yt": "ग्रोथ रिपोर्ट बनाईं 🔍",
        "gen_ig": "Instagram रिपोर्ट बनाईं 🔍",
        "gen_tt": "TikTok रिपोर्ट बनाईं 🔍",
        "fetching": "🔄 वीडियो के जानकारी आ कमेंट्स जुटावल जा रहल बा... ⏳",
        "generating": "⚡ रिपोर्ट तैयार हो रहल बा... ⏳",
        "done": "✅ ग्रोथ ऑडिट रिपोर्ट तैयार बा!",
        "download": "📥 पूरा रिपोर्ट डाउनलोड करीं (.txt)",
        "paste_warn": "कृपया वीडियो लिंक पेस्ट करीं।",
        "lock_err": "🔒 रउआ 3 गो फ्री रिपोर्ट खतम हो गइल बा! Pro Plan लीं।",
        "bad_link": "❌ सही वीडियो लिंक दीं।",
        "no_data": "❌ वीडियो के जानकारी ना मिल पावल।"
    },
    "Default": {
        "email_ph": "Login with Mail ID...",
        "send_otp": "Send OTP 📩",
        "otp_sent": "— 6-digit OTP sent! Check Inbox / Spam.",
        "otp_ph": "Enter 6-digit OTP",
        "verify_btn": "Verify OTP ✅",
        "otp_err": "❌ Invalid OTP! Please check again.",
        "invalid_email": "❌ Please enter a valid Email ID.",
        "temp_email": "❌ Temporary email is not allowed.",
        "free_left": "Free Reports Left",
        "free_done": "Your 3 Free Reports are used!",
        "login_for_free": "Login to get 3 Free Reports",
        "gen_yt": "Generate Growth Report 🔍",
        "gen_ig": "Generate Instagram Report 🔍",
        "gen_tt": "Generate TikTok Report 🔍",
        "fetching": "🔄 Fetching video details & comments... ⏳",
        "generating": "⚡ Generating report... ⏳",
        "done": "✅ Growth Audit Report Ready!",
        "download": "📥 Download Complete Report (.txt)",
        "paste_warn": "Please paste a video link first.",
        "lock_err": "🔒 Your 3 Free Reports are used! Upgrade to Pro on the left.",
        "bad_link": "❌ Please enter a valid video link.",
        "no_data": "❌ Could not fetch video details. Make sure it is Public."
    }
}

def get_ui(lang_choice):
    if "Telugu" in lang_choice or "Tenglish" in lang_choice:
        return UI_STRINGS["Telugu"]
    for key in ["Hindi", "Tamil", "Kannada", "Malayalam", "Marathi", "Bengali", "Gujarati", "Punjabi", "Odia", "Assamese", "Urdu", "Bhojpuri"]:
        if key in lang_choice:
            return UI_STRINGS[key]
    return UI_STRINGS["Default"]

# --- 4. CUSTOM COMPACT CSS ---
st.markdown("""
<style>
    [data-testid="stToolbarActions"], #MainMenu, footer, .stDeployButton { display: none !important; }
    header[data-testid="stHeader"] { background: transparent !important; }
    [data-testid="stSidebarCollapsedControl"] { display: flex !important; visibility: visible !important; z-index: 99999 !important; }

    .block-container { padding-top: 0.7rem !important; padding-bottom: 0.8rem !important; max-width: 1220px; }
    section[data-testid="stSidebar"] .block-container { padding-top: 0.6rem !important; padding-bottom: 0.4rem !important; }
    section[data-testid="stSidebar"] hr { margin: 0.45rem 0 !important; }
    section[data-testid="stSidebar"] .stMarkdown p { margin-bottom: 0.25rem !important; font-size: 0.88rem !important; }

    .center-banner {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        padding: 12px 18px;
        border-radius: 12px;
        border-bottom: 4px solid #10b981;
        margin-bottom: 10px;
        text-align: center;
        color: #ffffff;
    }
    .banner-title-row { display: inline-flex; align-items: center; justify-content: center; gap: 12px; }
    .banner-title-row h1 { margin: 0; font-size: 1.75rem; font-weight: 800; color: #ffffff; letter-spacing: 0.3px; }
    .banner-sub { margin: 4px 0 0 0; color: #cbd5e1; font-size: 0.92rem; }
    .india-badge {
        display: inline-block;
        background: rgba(16, 185, 129, 0.18);
        border: 1px solid #10b981;
        color: #6ee7b7;
        font-size: 0.76rem;
        font-weight: 700;
        padding: 2px 10px;
        border-radius: 999px;
        margin-top: 5px;
    }
    .or-pill { text-align: center; font-weight: 700; color: #94a3b8; padding-top: 7px; font-size: 0.85rem; }
    .loading-pill {
        background: #ecfdf5; border: 1.5px solid #10b981; color: #065f46;
        padding: 7px 14px; border-radius: 8px; font-weight: 600; font-size: 0.88rem;
        display: inline-flex; align-items: center; gap: 6px;
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
    ("yt_detected_lang", ""),
    ("ig_report", ""),
    ("tt_report", "")
]:
    if key not in st.session_state:
        st.session_state[key] = default

# --- 6. GOOGLE OAUTH CHECK ---
try:
    if hasattr(st, "user") and getattr(st.user, "is_logged_in", False):
        g_email = getattr(st.user, "email", "")
        if g_email:
            st.session_state.verified_email = g_email.strip().lower()
except Exception:
    pass

# --- 7. GOOGLE SHEET LIVE HELPERS (NO-CACHE) ---
def get_free_used_count(user_id):
    if not SHEET_API or not user_id:
        return 0
    try:
        r = requests.get(
            SHEET_API,
            params={"device": user_id, "_ts": str(datetime.utcnow().timestamp())},
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
                params={"device": user_id, "inc": "1", "_ts": str(datetime.utcnow().timestamp())},
                timeout=8,
                allow_redirects=True
            )
            if r.status_code == 200:
                return
        except Exception:
            pass

def log_usage_to_sheet(user_id, platform, url):
    if not SHEET_API:
        return
    try:
        requests.get(
            SHEET_API,
            params={"log": "1", "device": user_id, "platform": platform, "url": url},
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
            params={"pid": pid, "plan": plan, "_ts": str(datetime.utcnow().timestamp())},
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

# --- 8. AUTO-RETURN FROM RAZORPAY ---
qp_pid = st.query_params.get("razorpay_payment_id", "")
if qp_pid and not st.session_state.pro_unlocked:
    st_res = verify_payment_id(qp_pid, plan="1m")
    if st_res == "VALID":
        st.session_state.pro_unlocked = True
        st.session_state.pro_label = "PRO ACTIVE"

# --- 9. EMAIL OTP SENDER ---
def send_otp_email(to_email, code):
    if not SENDER_EMAIL or not SENDER_PASS:
        return False, "SMTP not configured"
    try:
        msg = MIMEText(
            f"Welcome to TrendSutra AI (1 AI • 1 India)!\n\nYour 6-digit verification code is: {code}\n\n"
            f"Enter this code on TrendSutra AI to unlock your 3 Free Growth Reports."
        )
        msg["Subject"] = f"{code} is your TrendSutra AI Code"
        msg["From"] = f"TrendSutra AI <{SENDER_EMAIL}>"
        msg["To"] = to_email
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=12) as server:
            server.login(SENDER_EMAIL, SENDER_PASS)
            server.sendmail(SENDER_EMAIL, [to_email], msg.as_string())
        return True, "SENT"
    except Exception as e:
        return False, str(e)

# --- 10. YOUTUBE DATA FETCHER ---
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
            "audio_lang": snip.get("defaultAudioLanguage", "") or snip.get("defaultLanguage", ""),
            "description": snip.get("description", "")[:1200],
            "tags": snip.get("tags", [])[:20],
            "views": int(stats.get("viewCount", 0)),
            "likes": int(stats.get("likeCount", 0)),
            "comment_count": int(stats.get("commentCount", 0)),
            "comments": comments
        }
    except Exception:
        return None

# --- 11. SINGLE-CALL UNIFIED GEMINI AI WITH 4-KEY SMART FAILOVER ---
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
            return ordered[:3]
    except Exception:
        pass
    return preferred

def clean_mentor_word(text):
    return text.replace("మెంటర్", "సలహాదారు").replace("స్ట్రాటజిస్ట్", "సలహాదారు")

def generate_report_stream(prompt):
    if not GEMINI_KEYS:
        raise RuntimeError("API Key missing in Secrets.")
    last_err = ""
    for api_key in GEMINI_KEYS:
        try:
            client = genai.Client(api_key=api_key)
            models = get_best_models(client)
            for model_name in models:
                try:
                    response = client.models.generate_content_stream(
                        model=model_name,
                        contents=prompt,
                        config=types.GenerateContentConfig(temperature=0.80, max_output_tokens=8192)
                    )
                    yielded = False
                    for chunk in response:
                        if chunk.text:
                            yielded = True
                            yield clean_mentor_word(chunk.text)
                    if yielded:
                        return
                except Exception as me:
                    last_err = str(me)
                    continue
        except Exception as ke:
            last_err = str(ke)
            continue
    raise RuntimeError(f"AI సర్వర్ రద్దీగా ఉంది. 5 సెకన్ల తర్వాత మళ్ళీ ప్రయత్నించండి. ({last_err})")

# --- 12. COMPACT NO-SCROLL SIDEBAR ---
with st.sidebar:
    st.markdown("### ⚙️ Settings")
    report_lang = st.selectbox(
        "🔍 Search Language (A–Z):",
        LANGUAGES_A_TO_Z,
        index=0,
        label_visibility="visible"
    )
    active_lang_for_ui = st.session_state.yt_detected_lang if ("Auto-Detect" in report_lang and st.session_state.yt_detected_lang) else report_lang
    ui = get_ui(active_lang_for_ui)
    audience_scope = st.radio("Audience:", ["Regional", "Global", "Both"], horizontal=True)

    st.divider()
    st.markdown("### 💎 Pro Plans")
    free_used = get_free_used_count(st.session_state.verified_email) if st.session_state.verified_email else 0
    free_left = max(0, 3 - free_used)

    if st.session_state.pro_unlocked:
        st.success(f"✅ {st.session_state.pro_label}")
    elif st.session_state.verified_email:
        if free_left > 0:
            st.info(f"🎁 **{free_left}/3** {ui['free_left']}")
        else:
            st.error(f"🔒 {ui['free_done']}")
    else:
        st.info(f"🎁 {ui['login_for_free']}")

    st.markdown(f"• **1 Month:** ₹100 👉 [Pay ₹100]({RAZORPAY_1M})\n• **12 Months:** ₹1,000 👉 [Pay ₹1,000]({RAZORPAY_12M})")
    plan_choice = st.radio("Plan:", ["1M (₹100)", "12M (₹1,000)"], horizontal=True, label_visibility="collapsed")
    pay_input = st.text_input("Payment ID:", placeholder="Paste Payment ID (pay_...)", label_visibility="collapsed")
    if st.button("Unlock Pro 🔓", use_container_width=True):
        if pay_input.strip():
            p_code = "12m" if "12" in plan_choice else "1m"
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
                st.error("⏰ Plan Expired! Please renew.")
            elif status == "ALREADY_USED":
                st.error("❌ Used on 3 devices already.")
            else:
                st.error("❌ Invalid Payment ID.")

    st.divider()
    st.caption("📩 support@aiengtel.com | aiengtel.com")

# --- 13. CENTERED HEADER WITH LOGO ---
logo_html = ""
if os.path.exists("logo.png"):
    with open("logo.png", "rb") as lf:
        b64_logo = base64.b64encode(lf.read()).decode()
    logo_html = f'<img src="data:image/png;base64,{b64_logo}" style="height:44px; width:44px; border-radius:10px; object-fit:contain;" />'

st.markdown(f"""
<div class="center-banner">
    <div class="banner-title-row">
        {logo_html}
        <h1>TrendSutra AI</h1>
    </div>
    <p class="banner-sub">A to Z Growth Analyzer for YouTube, Instagram & TikTok Creators</p>
    <span class="india-badge">🇮🇳 1 AI • 1 India — Supports All 22 Indian Official Languages + Bhojpuri</span>
</div>
""", unsafe_allow_html=True)

# --- 14. SINGLE-ROW COMPACT LOGIN BAR ---
if not st.session_state.verified_email and not st.session_state.pro_unlocked:
    lc1, lc2, lc3, lc4 = st.columns([2.1, 0.4, 2.3, 1.3])
    with lc1:
        if st.button("🔵 Continue with Gmail", type="primary", use_container_width=True):
            try:
                st.login("google")
            except Exception as e:
                st.error(f"Google Login error: {e}")
    with lc2:
        st.markdown('<div class="or-pill">OR</div>', unsafe_allow_html=True)
    with lc3:
        email_in = st.text_input("Mail", placeholder=ui["email_ph"], label_visibility="collapsed")
    with lc4:
        if st.button(ui["send_otp"], use_container_width=True):
            clean_em = email_in.strip().lower()
            if "@" not in clean_em or "." not in clean_em.split("@")[-1]:
                st.error(ui["invalid_email"])
            elif clean_em.split("@")[-1] in TEMP_DOMAINS:
                st.error(ui["temp_email"])
            else:
                code = str(random.randint(100000, 999999))
                ok, err_msg = send_otp_email(clean_em, code)
                if ok:
                    st.session_state.otp_code = code
                    st.session_state.otp_target = clean_em
                    st.success(f"✅ {clean_em} {ui['otp_sent']}")
                else:
                    st.error(f"OTP Error: {err_msg}")

    if st.session_state.otp_target:
        oc1, oc2 = st.columns([2, 1])
        with oc1:
            otp_in = st.text_input("OTP", placeholder=ui["otp_ph"], max_chars=6, label_visibility="collapsed")
        with oc2:
            if st.button(ui["verify_btn"], type="primary", use_container_width=True):
                if otp_in.strip() == st.session_state.otp_code:
                    st.session_state.verified_email = st.session_state.otp_target
                    st.session_state.otp_code = ""
                    st.rerun()
                else:
                    st.error(ui["otp_err"])
else:
    uc1, uc2 = st.columns([5, 1])
    with uc1:
        who = st.session_state.verified_email or st.session_state.pro_label
        st.caption(f"👤 Logged in as **{who}**  |  🎯 **{free_left}/3** {ui['free_left']}")
    with uc2:
        if st.session_state.verified_email and st.button("Logout", use_container_width=True):
            st.session_state.verified_email = ""
            st.session_state.pro_unlocked = False
            try:
                if hasattr(st, "logout"):
                    st.logout()
            except Exception:
                pass
            st.rerun()

# --- 15. MAIN WORKSPACE ---
tab_yt, tab_ig, tab_tt = st.tabs(["📺 YouTube Analyzer", "📸 Instagram Reels Analyzer", "🎵 TikTok Analyzer"])

with tab_yt:
    yc1, yc2, yc3 = st.columns([3.4, 1.8, 1.8])
    with yc1:
        yt_url = st.text_input("YouTube URL", placeholder="Paste YouTube Video or Shorts Link...", label_visibility="collapsed")
    with yc2:
        run_yt = st.button(ui["gen_yt"], key="btn_yt", type="primary", use_container_width=True)
    with yc3:
        yt_status_slot = st.empty()

    if run_yt:
        if not yt_url.strip():
            st.warning(ui["paste_warn"])
        elif not st.session_state.pro_unlocked and free_left <= 0:
            st.error(ui["lock_err"])
        else:
            vid_id = extract_youtube_id(yt_url.strip())
            if not vid_id:
                st.error(ui["bad_link"])
            else:
                yt_status_slot.markdown(f'<div class="loading-pill">{ui["fetching"]}</div>', unsafe_allow_html=True)
                data = fetch_youtube_details(vid_id)
                if not data:
                    yt_status_slot.empty()
                    st.error(ui["no_data"])
                else:
                    comments_block = "\n".join(data["comments"][:15]) if data["comments"] else "No public comments available."
                    lang_instruction = (
                        "First, automatically detect the primary spoken/written language of this video from its Title, Description, Audio Language tag, and Comments (e.g., Telugu, Hindi, Tamil, Kannada, Malayalam, Marathi, Bengali, Gujarati, Punjabi, Odia, Assamese, Urdu, Bhojpuri, English, etc.). Start the very first line with: **🌐 Detected Video Language: <Language Name>** and write the ENTIRE 6-section report in that exact detected language!"
                        if "Auto-Detect" in report_lang
                        else f"Start the very first line with: **🌐 Report Language: {report_lang}** and write the ENTIRE 6-section report in **{report_lang}**!"
                    )

                    prompt = f"""
You are a warm, encouraging, expert human social media growth advisor ("సలహాదారు" / advisor).
{lang_instruction}
Target Audience Scope: **{audience_scope}**.
Write a deeply detailed, crystal-clear, easy-to-understand growth audit report (1,100 to 1,500 words) using simple everyday spoken words (never use complex bookish words, and if writing in Telugu NEVER use the word 'మెంటర్'—use 'సలహాదారు' instead).

VIDEO DATA:
- Channel: {data['channel']}
- Title: {data['title']}
- Audio Tag: {data['audio_lang']}
- Views: {data['views']:,} | Likes: {data['likes']:,} | Comments: {data['comment_count']:,}
- Description: {data['description']}
- Tags: {', '.join(data['tags'])}
- Real Audience Comments:
{comments_block}

STRICTLY FOLLOW THIS 6-SECTION STRUCTURE (Translate headings into the target report language):
### 🎬 1. Video Story Recap & Creator Appreciation
- Warmly retell the core story/message of this video based on its title, description, and comments so the creator feels you truly understood their work.
- Genuinely praise the creator's effort, topic choice, and presentation strengths.

### 💬 2. Real Audience Comments & Translation
- Pick 4 to 5 real viewer comments from above, translate/present them naturally in the target report language with the viewer's name, explain audience sentiment, and give 3 ready-to-copy reply templates.

### 🔥 3. 3 Next Viral Video Ideas + 5-Second Opening Hooks
- Give 3 fresh follow-up video ideas tailored to this channel, each with a word-for-word **5-second opening Hook** and a **Thumbnail idea**.

### 🎯 4. Copy-Paste SEO Makeover (Titles, Description & 15 Tags)
- Provide 3 clickable high-CTR title options, a 3-line SEO description hook, and 15 searchable tags.

### 💰 5. Monetization & Earning Blueprint
- Explain 3 practical ways this channel can earn money (AdSense, Affiliate links, Brand deals).

### 📅 6. 30-Day Step-by-Step Action Plan
- Give a clear Week 1 to Week 4 checklist of simple actions to grow views and subscribers.
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
                        st.session_state.yt_vid_id = vid_id
                        m_lang = re.search(r"Detected Video Language:\s*([A-Za-z]+)", full_text)
                        if m_lang:
                            st.session_state.yt_detected_lang = m_lang.group(1)
                        if not st.session_state.pro_unlocked:
                            increment_free_used(st.session_state.verified_email)
                        log_usage_to_sheet(st.session_state.verified_email or "PRO", "YouTube", yt_url.strip())
                        st.rerun()
                    except Exception as e:
                        yt_status_slot.empty()
                        st.error(str(e))

    if st.session_state.yt_report:
        st.success(ui["done"])
        st.download_button(
            ui["download"],
            data=st.session_state.yt_report,
            file_name=f"TrendSutra_Report_{st.session_state.yt_vid_id or 'YouTube'}.txt",
            mime="text/plain",
            use_container_width=True
        )
        st.markdown(st.session_state.yt_report)

with tab_ig:
    ic1, ic2, ic3 = st.columns([3.4, 1.8, 1.8])
    with ic1:
        ig_url = st.text_input("IG URL", placeholder="Paste Instagram Reel Link...", label_visibility="collapsed")
    with ic2:
        run_ig = st.button(ui["gen_ig"], key="btn_ig", type="primary", use_container_width=True)
    with ic3:
        ig_status_slot = st.empty()

    if run_ig:
        if not ig_url.strip():
            st.warning(ui["paste_warn"])
        elif not st.session_state.pro_unlocked and free_left <= 0:
            st.error(ui["lock_err"])
        else:
            ig_status_slot.markdown(f'<div class="loading-pill">{ui["generating"]}</div>', unsafe_allow_html=True)
            target_l = "Hindi or English (or detected regional language from link context)" if "Auto-Detect" in report_lang else report_lang
            ig_prompt = f"""
You are a warm, encouraging human Instagram Reels growth advisor ("సలహాదారు" / advisor).
Write a detailed 6-section Instagram Reels growth audit (1,000+ words) in **{target_l}** for a **{audience_scope}** audience using simple spoken words.
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
                st.session_state.ig_report = full_text
                if not st.session_state.pro_unlocked:
                    increment_free_used(st.session_state.verified_email)
                log_usage_to_sheet(st.session_state.verified_email or "PRO", "Instagram", ig_url.strip())
                st.rerun()
            except Exception as e:
                ig_status_slot.empty()
                st.error(str(e))

    if st.session_state.ig_report:
        st.success(ui["done"])
        st.download_button(
            ui["download"],
            data=st.session_state.ig_report,
            file_name="TrendSutra_Instagram_Report.txt",
            mime="text/plain",
            use_container_width=True
        )
        st.markdown(st.session_state.ig_report)

with tab_tt:
    tc1, tc2, tc3 = st.columns([3.4, 1.8, 1.8])
    with tc1:
        tt_url = st.text_input("TT URL", placeholder="Paste TikTok Video Link...", label_visibility="collapsed")
    with tc2:
        run_tt = st.button(ui["gen_tt"], key="btn_tt", type="primary", use_container_width=True)
    with tc3:
        tt_status_slot = st.empty()

    if run_tt:
        if not tt_url.strip():
            st.warning(ui["paste_warn"])
        elif not st.session_state.pro_unlocked and free_left <= 0:
            st.error(ui["lock_err"])
        else:
            tt_status_slot.markdown(f'<div class="loading-pill">{ui["generating"]}</div>', unsafe_allow_html=True)
            target_l = "English (or detected regional language from link context)" if "Auto-Detect" in report_lang else report_lang
            tt_prompt = f"""
You are a warm, encouraging human TikTok growth advisor ("సలహాదారు" / advisor).
Write a detailed 6-section TikTok growth audit (1,000+ words) in **{target_l}** for a **{audience_scope}** audience using simple spoken words.
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
                st.session_state.tt_report = full_text
                if not st.session_state.pro_unlocked:
                    increment_free_used(st.session_state.verified_email)
                log_usage_to_sheet(st.session_state.verified_email or "PRO", "TikTok", tt_url.strip())
                st.rerun()
            except Exception as e:
                tt_status_slot.empty()
                st.error(str(e))

    if st.session_state.tt_report:
        st.success(ui["done"])
        st.download_button(
            ui["download"],
            data=st.session_state.tt_report,
            file_name="TrendSutra_TikTok_Report.txt",
            mime="text/plain",
            use_container_width=True
        )
        st.markdown(st.session_state.tt_report)
