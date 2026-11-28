import streamlit as st
from google import genai
from google.genai import types
from googleapiclient.discovery import build
from PIL import Image
import re
import requests
import random
import smtplib
import time
import os
import base64
from email.mime.text import MIMEText

# --- 1. PAGE CONFIG ---
PAGE_ICON = "logo.png" if os.path.exists("logo.png") else "📈"
st.set_page_config(page_title="TrendSutra AI - 1 AI • 1 India", page_icon=PAGE_ICON, layout="wide")

# --- 2. LOAD SECRETS (4-KEY FAILOVER: FREE 4 -> 3 -> 2 -> PAID 1) ---
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

# --- 3. ALL 22 INDIAN OFFICIAL LANGUAGES + BHOJPURI (A TO Z) ---
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
    "Sindhi (सिंधी / سنڌي)",
    "Tamil (தமிழ்)",
    "Telugu (తెలుగు)",
    "Tenglish (Telugu + English)",
    "Urdu (اردو)"
]

# --- 4. DYNAMIC LOCALIZED UI STRINGS ---
UI_STRINGS = {
    "English": {
        "free_left": "Free Reports Left",
        "free_done": "Your 3 Free Reports are used!",
        "login_prompt": "Login to get 3 Free Growth Reports",
        "gen_btn": "Generate Growth Report 🔍",
        "script_btn": "Generate Viral Script ✍️",
        "thumb_btn": "Analyze Thumbnail CTR 🖼️",
        "fetching": "🔄 Fetching video details... ⏳",
        "generating": "⚡ Generating report... ⏳",
        "ready": "✅ Growth Audit Report Ready!",
        "download": "📥 Download Report (.txt)",
        "otp_sent": "6-digit OTP sent to",
        "otp_check": "Please check Inbox / Spam.",
        "otp_verify": "Verify OTP ✅",
        "otp_wrong": "❌ Invalid OTP! Please check again."
    },
    "Telugu": {
        "free_left": "ఉచిత రిపోర్ట్‌లు మిగిలాయి",
        "free_done": "మీ 3 ఉచిత రిపోర్ట్‌లు పూర్తయ్యాయి!",
        "login_prompt": "3 ఉచిత రిపోర్ట్‌ల కోసం లాగిన్ అవ్వండి",
        "gen_btn": "గ్రోత్ రిపోర్ట్ తయారు చేయండి 🔍",
        "script_btn": "వైరల్ స్క్రిప్ట్ రాయండి ✍️",
        "thumb_btn": "థంబ్‌నెయిల్ చెక్ చేయండి 🖼️",
        "fetching": "🔄 వీడియో వివరాలు సేకరిస్తోంది... ⏳",
        "generating": "⚡ రిపోర్ట్ తయారవుతోంది... ⏳",
        "ready": "✅ గ్రోత్ రిపోర్ట్ సిద్ధమైంది!",
        "download": "📥 రిపోర్ట్ డౌన్‌లోడ్ (.txt)",
        "otp_sent": "కి 6-అంకెల OTP పంపబడింది!",
        "otp_check": "ఇన్‌బాక్స్ / Spam చెక్ చేయండి.",
        "otp_verify": "OTP నిర్ధారించండి ✅",
        "otp_wrong": "❌ తప్పు OTP! మళ్ళీ చెక్ చేయండి."
    },
    "Hindi": {
        "free_left": "मुफ्त रिपोर्ट बाकी हैं",
        "free_done": "आपकी 3 मुफ्त रिपोर्ट पूरी हो गई हैं!",
        "login_prompt": "3 मुफ्त रिपोर्ट के लिए लॉगिन करें",
        "gen_btn": "ग्रोथ रिपोर्ट बनाएं 🔍",
        "script_btn": "वायरल स्क्रिप्ट बनाएं ✍️",
        "thumb_btn": "थंबनेल चेक करें 🖼️",
        "fetching": "🔄 वीडियो जानकारी ली जा रही है... ⏳",
        "generating": "⚡ रिपोर्ट तैयार हो रही है... ⏳",
        "ready": "✅ ग्रोथ रिपोर्ट तैयार है!",
        "download": "📥 रिपोर्ट डाउनलोड करें (.txt)",
        "otp_sent": "पर 6-अंकों का OTP भेजा गया!",
        "otp_check": "कृपया Inbox / Spam चेक करें।",
        "otp_verify": "OTP सत्यापित करें ✅",
        "otp_wrong": "❌ गलत OTP! कृपया पुनः जांचें।"
    },
    "Tamil": {
        "free_left": "இலவச அறிக்கைகள் உள்ளன",
        "free_done": "உங்கள் 3 இலவச அறிக்கைகள் முடிந்துவிட்டன!",
        "login_prompt": "3 இலவச அறிக்கைகளுக்கு உள்நுழையவும்",
        "gen_btn": "வளர்ச்சி அறிக்கை உருவாக்கு 🔍",
        "script_btn": "வைரல் ஸ்கிரிப்ட் உருவாக்கு ✍️",
        "thumb_btn": "தம்ப்நெயில் சரிபார் 🖼️",
        "fetching": "🔄 வீடியோ விவரங்கள் பெறப்படுகின்றன... ⏳",
        "generating": "⚡ அறிக்கை தயாராகிறது... ⏳",
        "ready": "✅ வளர்ச்சி அறிக்கை தயார்!",
        "download": "📥 அறிக்கையை பதிவிறக்கவும் (.txt)",
        "otp_sent": "க்கு 6-இலக்க OTP அனுப்பப்பட்டது!",
        "otp_check": "Inbox / Spam சரிபார்க்கவும்.",
        "otp_verify": "OTP சரிபார்க்கவும் ✅",
        "otp_wrong": "❌ தவறான OTP! மீண்டும் சரிபார்க்கவும்."
    },
    "Kannada": {
        "free_left": "ಉಚಿತ ವರದಿಗಳು ಬಾಕಿ ಇವೆ",
        "free_done": "ನಿಮ್ಮ 3 ಉಚಿತ ವರದಿಗಳು ಮುಗಿದಿವೆ!",
        "login_prompt": "3 ಉಚಿತ ವರದಿಗಳಿಗಾಗಿ ಲಾಗಿನ್ ಮಾಡಿ",
        "gen_btn": "ಗ್ರೋತ್ ವರದಿ ತಯಾರಿಸಿ 🔍",
        "script_btn": "ವೈರಲ್ ಸ್ಕ್ರಿಪ್ಟ್ ಬರೆಯಿರಿ ✍️",
        "thumb_btn": "ಥಂಬ್‌ನೇಲ್ ಪರಿಶೀಲಿಸಿ 🖼️",
        "fetching": "🔄 ವೀಡಿಯೊ ವಿವರಗಳನ್ನು ಪಡೆಯಲಾಗುತ್ತಿದೆ... ⏳",
        "generating": "⚡ ವರದಿ ಸಿದ್ಧವಾಗುತ್ತಿದೆ... ⏳",
        "ready": "✅ ಗ್ರೋತ್ ವರದಿ ಸಿದ್ಧವಾಗಿದೆ!",
        "download": "📥 ವರದಿ ಡೌನ್‌ಲೋಡ್ ಮಾಡಿ (.txt)",
        "otp_sent": "ಗೆ 6-ಅಂಕಿಯ OTP ಕಳುಹಿಸಲಾಗಿದೆ!",
        "otp_check": "Inbox / Spam ಪರಿಶೀಲಿಸಿ.",
        "otp_verify": "OTP ಪರಿಶೀಲಿಸಿ ✅",
        "otp_wrong": "❌ ತಪ್ಪಾದ OTP! ಮತ್ತೆ ಪರಿಶೀಲಿಸಿ."
    },
    "Malayalam": {
        "free_left": "സൗജന്യ റിപ്പോർട്ടുകൾ ബാക്കിയുണ്ട്",
        "free_done": "നിങ്ങളുടെ 3 സൗജന്യ റിപ്പോർട്ടുകൾ കഴിഞ്ഞു!",
        "login_prompt": "3 സൗജന്യ റിപ്പോർട്ടുകൾക്കായി ലോഗിൻ ചെയ്യുക",
        "gen_btn": "ഗ്രോത്ത് റിപ്പോർട്ട് തയ്യാറാക്കുക 🔍",
        "script_btn": "വൈറൽ സ്ക്രിപ്റ്റ് തയ്യാറാക്കുക ✍️",
        "thumb_btn": "തംബ്നെയിൽ പരിശോധിക്കുക 🖼️",
        "fetching": "🔄 വീഡിയോ വിവരങ്ങൾ ശേഖരിക്കുന്നു... ⏳",
        "generating": "⚡ റിപ്പോർട്ട് തയ്യാറാകുന്നു... ⏳",
        "ready": "✅ ഗ്രോത്ത് റിപ്പോർട്ട് തയ്യാറായി!",
        "download": "📥 റിപ്പോർട്ട് ഡൗൺലോഡ് (.txt)",
        "otp_sent": "ലേക്ക് 6-അക്ക OTP അയച്ചു!",
        "otp_check": "Inbox / Spam പരിശോധിക്കുക.",
        "otp_verify": "OTP സ്ഥിരീകരിക്കുക ✅",
        "otp_wrong": "❌ തെറ്റായ OTP! വീണ്ടും പരിശോധിക്കുക."
    },
    "Marathi": {
        "free_left": "मोफत रिपोर्ट शिल्लक आहेत",
        "free_done": "तुमचे 3 मोफत रिपोर्ट संपले आहेत!",
        "login_prompt": "3 मोफत रिपोर्टसाठी लॉगिन करा",
        "gen_btn": "ग्रोथ रिपोर्ट तयार करा 🔍",
        "script_btn": "व्हायरल स्क्रिप्ट तयार करा ✍️",
        "thumb_btn": "थंबनेल तपासा 🖼️",
        "fetching": "🔄 व्हिडिओ माहिती घेतली जात आहे... ⏳",
        "generating": "⚡ रिपोर्ट तयार होत आहे... ⏳",
        "ready": "✅ ग्रोथ रिपोर्ट तयार आहे!",
        "download": "📥 रिपोर्ट डाउनलोड करा (.txt)",
        "otp_sent": "वर 6-अंकी OTP पाठवला आहे!",
        "otp_check": "कृपया Inbox / Spam तपासा.",
        "otp_verify": "OTP पडताळा ✅",
        "otp_wrong": "❌ चुकीचा OTP! पुन्हा तपासा."
    },
    "Bengali": {
        "free_left": "ফ্রি রিপোর্ট বাকি আছে",
        "free_done": "আপনার ৩টি ফ্রি রিপোর্ট শেষ হয়ে গেছে!",
        "login_prompt": "৩টি ফ্রি রিপোর্টের জন্য লগইন করুন",
        "gen_btn": "গ্রোথ রিপোর্ট তৈরি করুন 🔍",
        "script_btn": "ভাইরাল স্ক্রিপ্ট তৈরি করুন ✍️",
        "thumb_btn": "থাম্বনেইল যাচাই করুন 🖼️",
        "fetching": "🔄 ভিডিওর তথ্য সংগ্রহ করা হচ্ছে... ⏳",
        "generating": "⚡ রিপোর্ট তৈরি হচ্ছে... ⏳",
        "ready": "✅ গ্রোথ রিপোর্ট তৈরি!",
        "download": "📥 রিপোর্ট ডাউনলোড করুন (.txt)",
        "otp_sent": "এ ৬-সংখ্যার OTP পাঠানো হয়েছে!",
        "otp_check": "Inbox / Spam চেক করুন।",
        "otp_verify": "OTP যাচাই করুন ✅",
        "otp_wrong": "❌ ভুল OTP! আবার চেষ্টা করুন।"
    },
    "Gujarati": {
        "free_left": "મફત રિપોર્ટ બાકી છે",
        "free_done": "તમારા 3 મફત રિપોર્ટ પૂરા થઈ ગયા છે!",
        "login_prompt": "3 મફત રિપોર્ટ માટે લોગિન કરો",
        "gen_btn": "ગ્રોથ રિપોર્ટ બનાવો 🔍",
        "script_btn": "વાયરલ સ્ક્રિપ્ટ બનાવો ✍️",
        "thumb_btn": "થંબનેલ તપાસો 🖼️",
        "fetching": "🔄 વિડિયોની માહિતી લેવામાં આવી રહી છે... ⏳",
        "generating": "⚡ રિપોર્ટ તૈયાર થઈ રહ્યો છે... ⏳",
        "ready": "✅ ગ્રોથ રિપોર્ટ તૈયાર છે!",
        "download": "📥 રિપોર્ટ ડાઉનલોડ કરો (.txt)",
        "otp_sent": "પર 6-અંકનો OTP મોકલવામાં આવ્યો છે!",
        "otp_check": "Inbox / Spam તપાસો.",
        "otp_verify": "OTP ચકાસો ✅",
        "otp_wrong": "❌ ખોટો OTP! ફરીથી તપાસો."
    },
    "Punjabi": {
        "free_left": "ਮੁਫ਼ਤ ਰਿਪੋਰਟਾਂ ਬਾਕੀ ਹਨ",
        "free_done": "ਤੁਹਾਡੀਆਂ 3 ਮੁਫ਼ਤ ਰਿਪੋਰਟਾਂ ਪੂਰੀਆਂ ਹੋ ਗਈਆਂ ਹਨ!",
        "login_prompt": "3 ਮੁਫ਼ਤ ਰਿਪੋਰਟਾਂ ਲਈ ਲੌਗਇਨ ਕਰੋ",
        "gen_btn": "ਗ੍ਰੋਥ ਰਿਪੋਰਟ ਬਣਾਓ 🔍",
        "script_btn": "ਵਾਇਰਲ ਸਕ੍ਰਿਪਟ ਬਣਾਓ ✍️",
        "thumb_btn": "ਥੰਬਨੇਲ ਚੈੱਕ ਕਰੋ 🖼️",
        "fetching": "🔄 ਵੀਡੀਓ ਜਾਣਕਾਰੀ ਲਈ ਜਾ ਰਹੀ ਹੈ... ⏳",
        "generating": "⚡ ਰਿਪੋਰਟ ਤਿਆਰ ਹੋ ਰਹੀ ਹੈ... ⏳",
        "ready": "✅ ਗ੍ਰੋਥ ਰਿਪੋਰਟ ਤਿਆਰ ਹੈ!",
        "download": "📥 ਰਿਪੋਰਟ ਡਾਊਨਲੋਡ ਕਰੋ (.txt)",
        "otp_sent": "ਤੇ 6-ਅੰਕਾਂ ਦਾ OTP ਭੇਜਿਆ ਗਿਆ ਹੈ!",
        "otp_check": "Inbox / Spam ਚੈੱਕ ਕਰੋ।",
        "otp_verify": "OTP ਪੁਸ਼ਟੀ ਕਰੋ ✅",
        "otp_wrong": "❌ ਗਲਤ OTP! ਦੁਬਾਰਾ ਜਾਂਚ ਕਰੋ।"
    },
    "Odia": {
        "free_left": "ମାଗଣା ରିପୋର୍ଟ ବାକି ଅଛି",
        "free_done": "ଆପଣଙ୍କର ୩ଟି ମାଗଣା ରିପୋର୍ଟ ଶେଷ ହୋଇଯାଇଛି!",
        "login_prompt": "୩ଟି ମାଗଣା ରିପୋର୍ଟ ପାଇଁ ଲଗଇନ୍ କରନ୍ତୁ",
        "gen_btn": "ଗ୍ରୋଥ୍ ରିପୋର୍ଟ ତିଆରି କରନ୍ତୁ 🔍",
        "script_btn": "ଭାଇରାଲ୍ ସ୍କ୍ରିପ୍ଟ ଲେଖନ୍ତୁ ✍️",
        "thumb_btn": "ଥମ୍ବନେଲ୍ ଯାଞ୍ଚ କରନ୍ତୁ 🖼️",
        "fetching": "🔄 ଭିଡିଓ ତଥ୍ୟ ସଂଗ୍ରହ କରାଯାଉଛି... ⏳",
        "generating": "⚡ ରିପୋର୍ଟ ପ୍ରସ୍ତୁତ ହେଉଛି... ⏳",
        "ready": "✅ ଗ୍ରୋଥ୍ ରିପୋର୍ଟ ପ୍ରସ୍ତୁତ!",
        "download": "📥 ରିପୋର୍ଟ ଡାଉନଲୋଡ୍ କରନ୍ତୁ (.txt)",
        "otp_sent": "କୁ 6-ଅଙ୍କ ବିଶିଷ୍ଟ OTP ପଠାଯାଇଛି!",
        "otp_check": "Inbox / Spam ଯାଞ୍ଚ କରନ୍ତୁ।",
        "otp_verify": "OTP ଯାଞ୍ଚ କରନ୍ତୁ ✅",
        "otp_wrong": "❌ ଭୁଲ୍ OTP! ପୁଣି ଯାଞ୍ଚ କରନ୍ତୁ।"
    },
    "Assamese": {
        "free_left": "বিনামূলীয়া ৰিপৰ্ট বাকী আছে",
        "free_done": "আপোনাৰ ৩টা বিনামূলীয়া ৰিপৰ্ট শেষ হৈছে!",
        "login_prompt": "৩টা বিনামূলীয়া ৰিপৰ্টৰ বাবে লগইন কৰক",
        "gen_btn": "গ্ৰোথ ৰিপৰ্ট তৈয়াৰ কৰক 🔍",
        "script_btn": "ভাইৰেল স্ক্ৰিপ্ট লিখক ✍️",
        "thumb_btn": "থাম্বনেইল পৰীক্ষা কৰক 🖼️",
        "fetching": "🔄 ভিডিঅ'ৰ তথ্য সংগ্ৰহ কৰা হৈছে... ⏳",
        "generating": "⚡ ৰিপৰ্ট প্ৰস্তুত হৈ আছে... ⏳",
        "ready": "✅ গ্ৰোথ ৰিপৰ্ট সাজু!",
        "download": "📥 ৰিপৰ্ট ডাউনলোড কৰক (.txt)",
        "otp_sent": "লৈ ৬-অংকৰ OTP পঠিওৱা হৈছে!",
        "otp_check": "Inbox / Spam পৰীক্ষা কৰক।",
        "otp_verify": "OTP নিশ্চিত কৰক ✅",
        "otp_wrong": "❌ ভুল OTP! পুনৰ পৰীক্ষা কৰক।"
    },
    "Urdu": {
        "free_left": "مفت رپورٹس باقی ہیں",
        "free_done": "آپ کی 3 مفت رپورٹس مکمل ہو گئی ہیں!",
        "login_prompt": "3 مفت رپورٹس کے لیے لاگ ان کریں",
        "gen_btn": "گروتھ رپورٹ بنائیں 🔍",
        "script_btn": "وائرل اسکرپٹ لکھیں ✍️",
        "thumb_btn": "تھمب نیل چیک کریں 🖼️",
        "fetching": "🔄 ویڈیو کی تفصیلات حاصل کی جا رہی ہیں... ⏳",
        "generating": "⚡ رپورٹ تیار ہو رہی ہے... ⏳",
        "ready": "✅ گروتھ رپورٹ تیار ہے!",
        "download": "📥 رپورٹ ڈاؤن لوڈ کریں (.txt)",
        "otp_sent": "پر 6 ہندسوں کا OTP بھیج دیا گیا ہے!",
        "otp_check": "براہ کرم Inbox / Spam چیک کریں۔",
        "otp_verify": "OTP کی تصدیق کریں ✅",
        "otp_wrong": "❌ غلط OTP! دوبارہ چیک کریں۔"
    },
    "Bhojpuri": {
        "free_left": "मुफ्त रिपोर्ट बाकी बा",
        "free_done": "राउर 3 मुफ्त रिपोर्ट पूरा हो गइल बा!",
        "login_prompt": "3 मुफ्त रिपोर्ट खातिर लॉगिन करीं",
        "gen_btn": "ग्रोथ रिपोर्ट बनाईं 🔍",
        "script_btn": "वायरल स्क्रिप्ट लिखीं ✍️",
        "thumb_btn": "थंबनेल जांच करीं 🖼️",
        "fetching": "🔄 वीडियो के जानकारी लिहल जा रहल बा... ⏳",
        "generating": "⚡ रिपोर्ट तैयार हो रहल बा... ⏳",
        "ready": "✅ ग्रोथ रिपोर्ट तैयार बा!",
        "download": "📥 रिपोर्ट डाउनलोड करीं (.txt)",
        "otp_sent": "पर 6-अंक के OTP भेजल गइल बा!",
        "otp_check": "Inbox / Spam जांच करीं।",
        "otp_verify": "OTP सत्यापित करीं ✅",
        "otp_wrong": "❌ गलत OTP! फिर से जांचीं।"
    }
}

def get_ui_lang_key(selected_label, detected_lang=""):
    target = detected_lang if (selected_label.startswith("Auto-Detect") and detected_lang) else selected_label
    for lang_key in UI_STRINGS.keys():
        if lang_key != "English" and lang_key.lower() in target.lower():
            return lang_key
    if "tenglish" in target.lower():
        return "Telugu"
    if "hinglish" in target.lower():
        return "Hindi"
    return "English"

def get_ui_text(selected_label, detected_lang=""):
    key = get_ui_lang_key(selected_label, detected_lang)
    return UI_STRINGS.get(key, UI_STRINGS["English"])

# --- 5. CUSTOM CSS (4-SIDE BORDER & NO TOP TOOLBAR ICONS) ---
st.markdown("""
<style>
    [data-testid="stToolbarActions"],
    .stAppDeployButton,
    #MainMenu,
    footer {
        display: none !important;
        visibility: hidden !important;
    }
    header[data-testid="stHeader"] {
        background: transparent !important;
    }
    [data-testid="stSidebarCollapsedControl"] {
        display: flex !important;
        visibility: visible !important;
        z-index: 999999 !important;
    }
    .block-container {
        padding-top: 3.6rem !important;
        padding-bottom: 1rem !important;
        max-width: 1180px;
    }
    section[data-testid="stSidebar"] > div {
        padding-top: 1.2rem !important;
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
        padding: 18px 22px;
        border-radius: 14px;
        border: 2px solid #10b981 !important;
        box-shadow: 0 4px 18px rgba(16, 185, 129, 0.18);
        margin-bottom: 12px;
        text-align: center;
    }
    .india-badge {
        display: inline-block;
        background: rgba(16, 185, 129, 0.16);
        border: 1px solid #10b981;
        color: #6ee7b7;
        padding: 3px 14px;
        border-radius: 999px;
        font-size: 0.82rem;
        font-weight: 600;
        margin-top: 6px;
    }
    .status-strip {
        background: #1e293b;
        border: 1px solid #334155;
        border-radius: 10px;
        padding: 9px 14px;
        color: #f8fafc;
        font-size: 0.93rem;
        margin-bottom: 10px;
    }
    .loading-pill {
        background: #064e3b;
        border: 1px solid #10b981;
        color: #ecfdf5;
        padding: 8px 14px;
        border-radius: 8px;
        font-weight: 600;
        font-size: 0.9rem;
        text-align: center;
    }
    div.stButton > button {
        height: 42px !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
    }
    div[data-testid="stTextInput"] input {
        height: 42px !important;
        border-radius: 8px !important;
    }
</style>
""", unsafe_allow_html=True)

# --- 6. SESSION STATE ---
for key, default in [
    ("verified_email", ""),
    ("otp_code", ""),
    ("otp_target", ""),
    ("pro_unlocked", False),
    ("pro_label", ""),
    ("yt_report", ""),
    ("yt_vid_id", ""),
    ("yt_metrics", None),
    ("ig_report", ""),
    ("tt_report", ""),
    ("script_report", ""),
    ("thumb_report", ""),
    ("detected_lang_name", ""),
    ("exhausted_keys", [])
]:
    if key not in st.session_state:
        st.session_state[key] = default

# --- 7. CHECK GOOGLE LOGIN & RAZORPAY AUTO-RETURN ---
try:
    if hasattr(st, "user") and getattr(st.user, "is_logged_in", False):
        g_email = getattr(st.user, "email", "")
        if g_email:
            st.session_state.verified_email = g_email.strip().lower()
except Exception:
    pass

q_params = st.query_params
auto_pid = q_params.get("razorpay_payment_id", "") or q_params.get("payment_id", "")
if auto_pid and str(auto_pid).startswith("pay_") and not st.session_state.pro_unlocked:
    st.session_state.pro_unlocked = True
    st.session_state.pro_label = f"PRO ACTIVE ({auto_pid})"

# --- 8. LIVE GOOGLE SHEET FUNCTIONS (NO CACHE) ---
def get_free_used_count(user_id):
    if not SHEET_API or not user_id:
        return 0
    try:
        r = requests.get(
            SHEET_API,
            params={"device": user_id, "_ts": str(time.time())},
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
                params={"device": user_id, "inc": "1", "_ts": str(time.time())},
                timeout=10,
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
            params={"log": "1", "device": user_id, "platform": platform, "url": url, "_ts": str(time.time())},
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
            "audio_lang": snip.get("defaultAudioLanguage", snip.get("defaultLanguage", "")),
            "description": snip.get("description", "")[:1000],
            "tags": snip.get("tags", [])[:15],
            "views": int(stats.get("viewCount", 0)),
            "likes": int(stats.get("likeCount", 0)),
            "comment_count": int(stats.get("commentCount", 0)),
            "comments": comments
        }
    except Exception:
        return None

# --- 10. FAST GEMINI STREAMING (NO 2.5-FLASH, ONLY 3.8+ MODELS) ---
@st.cache_data(ttl=3600, show_spinner=False)
def discover_models_for_key(api_key):
    fallback = ["gemini-3.8-flash-lite", "gemini-3.8-flash"]
    try:
        client = genai.Client(api_key=api_key, http_options=types.HttpOptions(timeout=8000))
        avail = []
        for m in client.models.list():
            name = m.name.replace("models/", "")
            if "flash" in name and not any(old in name for old in ["2.5", "2.0", "1.5", "8b"]):
                avail.append(name)
        ordered = [p for p in fallback if p in avail]
        for a in avail:
            if a not in ordered:
                ordered.append(a)
        if ordered:
            return ordered[:2]
    except Exception:
        pass
    return fallback

def clean_text(text):
    return text.replace("మెంటర్", "సలహాదారు").replace("స్ట్రాటజిస్ట్", "సలహాదారు")

def generate_report_stream(contents_payload):
    if not GEMINI_KEYS:
        raise RuntimeError("API Key missing in Secrets.")

    active_keys = [k for k in GEMINI_KEYS if k not in st.session_state.exhausted_keys]
    if not active_keys:
        st.session_state.exhausted_keys = []
        active_keys = GEMINI_KEYS

    last_err = ""
    for idx, api_key in enumerate(active_keys):
        is_last_key = (idx == len(active_keys) - 1)
        try:
            client = genai.Client(api_key=api_key, http_options=types.HttpOptions(timeout=14000))
            models = discover_models_for_key(api_key)
            for model_name in models:
                try:
                    response = client.models.generate_content_stream(
                        model=model_name,
                        contents=contents_payload,
                        config=types.GenerateContentConfig(temperature=0.82, max_output_tokens=8192)
                    )
                    yielded = False
                    for chunk in response:
                        if chunk.text:
                            yielded = True
                            yield clean_text(chunk.text)
                    if yielded:
                        return
                except Exception as m_err:
                    last_err = str(m_err)
                    if any(code in last_err for code in ["429", "RESOURCE_EXHAUSTED", "quota", "403"]):
                        if not is_last_key and api_key not in st.session_state.exhausted_keys:
                            st.session_state.exhausted_keys.append(api_key)
                        break
                    continue
        except Exception as k_err:
            last_err = str(k_err)
            if not is_last_key and api_key not in st.session_state.exhausted_keys:
                st.session_state.exhausted_keys.append(api_key)
            continue

    raise RuntimeError(f"AI servers are busy right now. Please try again in 5 seconds. ({last_err})")

# --- 11. SIDEBAR (NO LOGO, 1M & 12M IN CLEAN ORDER) ---
with st.sidebar:
    st.markdown("### ⚙️ Settings")
    report_lang = st.selectbox(
        "🔍 Search Language (A–Z):",
        LANGUAGE_OPTIONS,
        index=0
    )
    audience_scope = st.radio("Audience:", ["Regional", "Global", "Both"], horizontal=True)

    st.divider()
    st.markdown("### 💎 Pro Plans")

    free_used = get_free_used_count(st.session_state.verified_email) if st.session_state.verified_email else 0
    free_left = max(0, 3 - free_used)
    ui = get_ui_text(report_lang, st.session_state.detected_lang_name)

    if st.session_state.pro_unlocked:
        st.success(f"✅ {st.session_state.pro_label}")
    elif st.session_state.verified_email:
        if free_left > 0:
            st.info(f"🎁 **{free_left}/3** {ui['free_left']}")
        else:
            st.error(f"🔒 {ui['free_done']}")
    else:
        st.info(f"🎁 {ui['login_prompt']}")

    st.markdown(f"• **1 Month:** ₹100 👉 [Pay ₹100]({RAZORPAY_1M})")
    st.markdown(f"• **12 Months:** ₹1,000 👉 [Pay ₹1,000]({RAZORPAY_12M})")

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
                st.session_state.pro_label = f"PRO ({plan_choice})"
                st.rerun()
            elif status == "EXPIRED":
                st.error("⏰ Plan Expired!")
            elif status == "ALREADY_USED":
                st.error("❌ Used on 3 devices.")
            else:
                st.error("❌ Invalid Payment ID.")

    st.caption("📩 support@aiengtel.com | aiengtel.com")

# --- 12. CENTERED HEADER WITH 4-SIDE BORDER & NO FLAG ---
logo_html = ""
if os.path.exists("logo.png"):
    with open("logo.png", "rb") as img_f:
        b64_logo = base64.b64encode(img_f.read()).decode()
    logo_html = f'<img src="data:image/png;base64,{b64_logo}" style="height:44px; width:44px; border-radius:10px; object-fit:contain; vertical-align:middle; margin-right:12px;">'

st.markdown(f"""
<div class="main-header">
    <div style="display:flex; align-items:center; justify-content:center;">
        {logo_html}
        <span style="font-size:1.95rem; font-weight:800; color:#ffffff; letter-spacing:0.4px;">TrendSutra AI</span>
    </div>
    <p style="margin:6px 0 0 0; color:#cbd5e1; font-size:0.96rem;">A to Z Growth Analyzer for YouTube, Instagram & TikTok Creators</p>
    <div class="india-badge">1 AI • 1 India — Supports All 22 Indian Official Languages + Bhojpuri</div>
</div>
""", unsafe_allow_html=True)

# --- 13. COMPACT SINGLE-ROW LOGIN BAR ---
if not st.session_state.verified_email and not st.session_state.pro_unlocked:
    lc1, lc2, lc3, lc4 = st.columns([2.2, 0.4, 2.3, 1.4])
    with lc1:
        if st.button("🔵 Continue with Gmail", type="primary", use_container_width=True):
            try:
                st.login("google")
            except Exception as e:
                st.error(f"Google Login error: {e}")
    with lc2:
        st.markdown("<div style='text-align:center; padding-top:10px; color:#94a3b8; font-weight:700;'>OR</div>", unsafe_allow_html=True)
    with lc3:
        email_in = st.text_input("Mail", placeholder="Login with Mail ID (example@gmail.com)", label_visibility="collapsed")
    with lc4:
        if st.button("Send OTP 📩", use_container_width=True):
            clean_em = email_in.strip().lower()
            if "@" not in clean_em or "." not in clean_em.split("@")[-1]:
                st.error("❌ Enter valid Mail ID.")
            elif clean_em.split("@")[-1] in TEMP_DOMAINS:
                st.error("❌ Temp email not allowed.")
            else:
                code = str(random.randint(100000, 999999))
                ok, err_msg = send_otp_email(clean_em, code)
                if ok:
                    st.session_state.otp_code = code
                    st.session_state.otp_target = clean_em
                    st.success(f"✅ {st.session_state.otp_target} {ui['otp_sent']} {ui['otp_check']}")
                else:
                    st.error(f"OTP error: {err_msg}")

    if st.session_state.otp_target:
        oc1, oc2 = st.columns([3, 1.5])
        with oc1:
            otp_in = st.text_input("OTP", placeholder="Enter 6-digit OTP from Mail", max_chars=6, label_visibility="collapsed")
        with oc2:
            if st.button(ui["otp_verify"], type="primary", use_container_width=True):
                if otp_in.strip() == st.session_state.otp_code:
                    st.session_state.verified_email = st.session_state.otp_target
                    st.session_state.otp_code = ""
                    st.rerun()
                else:
                    st.error(ui["otp_wrong"])
else:
    uc1, uc2 = st.columns([5, 1])
    with uc1:
        badge_txt = f"💎 {st.session_state.pro_label}" if st.session_state.pro_unlocked else f"🎁 {free_left}/3 {ui['free_left']}"
        lang_tag = f" | 🌐 {st.session_state.detected_lang_name}" if (report_lang.startswith("Auto-Detect") and st.session_state.detected_lang_name) else ""
        st.markdown(f'<div class="status-strip">👤 Logged in as <b>{st.session_state.verified_email or "Pro User"}</b> &nbsp;|&nbsp; {badge_txt}{lang_tag}</div>', unsafe_allow_html=True)
    with uc2:
        if st.button("Logout", use_container_width=True):
            st.session_state.verified_email = ""
            st.session_state.pro_unlocked = False
            st.session_state.yt_report = ""
            st.session_state.detected_lang_name = ""
            try:
                if hasattr(st, "logout"):
                    st.logout()
            except Exception:
                pass
            st.rerun()

# --- 14. LANGUAGE INSTRUCTION HELPER ---
def build_lang_instruction(selected_lang):
    if selected_lang.startswith("Auto-Detect"):
        return """
LANGUAGE RULE (1 AI • 1 INDIA):
1. First detect the PRIMARY spoken/written language of the video/topic from the title, description, tags, and audience comments (e.g., Telugu, Hindi, Tamil, Kannada, Malayalam, Marathi, Bengali, Gujarati, Punjabi, Odia, Assamese, Urdu, Bhojpuri, English, etc.).
2. At the very top of your response, write a single line: `🌐 **Detected Video Language:** <Language Name>`
3. Write the ENTIRE report (including all 6 section headings and full explanations) in that exact detected language using its NATIVE SCRIPT (for example: Telugu in తెలుగు, Tamil in தமிழ், Hindi in हिन्दी, Urdu in اردو, Kannada in ಕನ್ನಡ, Malayalam in മലയാളം, Bengali in বাংলা, Gujarati in ગુજરાતી, Marathi in मराठी, Punjabi in ਪੰਜਾਬੀ, Odia in ଓଡ଼ିଆ). Never write Indian languages in Roman/English letters unless Hinglish or Tenglish is detected.
"""
    else:
        return f"""
LANGUAGE RULE (1 AI • 1 INDIA):
Write the ENTIRE report (including all 6 section headings and full explanations) strictly in **{selected_lang}** using its NATIVE SCRIPT (e.g., Telugu in తెలుగు, Tamil in தமிழ், Hindi in हिन्दी, Urdu in اردو, Kannada in ಕನ್ನಡ, Malayalam in മലയാളം, Bengali in বাংলা, Gujarati in ગુજરાતી, Marathi in मराठी, Punjabi in ਪੰਜਾਬੀ, Odia in ଓଡ଼ିଆ). Never write Indian languages in Roman/English letters unless Hinglish or Tenglish is explicitly selected.
"""

# --- 15. MAIN WORKSPACE (5 PRO TABS) ---
tab_yt, tab_ig, tab_tt, tab_script, tab_thumb = st.tabs([
    "📺 YouTube Analyzer",
    "📸 Instagram Reels",
    "🎵 TikTok Analyzer",
    "✍️ Viral Script Generator",
    "🖼️ AI Thumbnail Checker"
])

with tab_yt:
    ic1, ic2, ic3 = st.columns([4.2, 1.8, 2.0])
    with ic1:
        yt_url = st.text_input("YT", placeholder="Paste YouTube Video or Shorts Link...", label_visibility="collapsed")
    with ic2:
        run_yt = st.button(ui["gen_btn"], key="btn_yt", type="primary", use_container_width=True)
    with ic3:
        yt_status_slot = st.empty()

    if run_yt:
        if not st.session_state.verified_email and not st.session_state.pro_unlocked:
            st.warning(f"⚠️ {ui['login_prompt']}")
        elif not yt_url.strip():
            st.warning("⚠️ Paste a YouTube link first.")
        elif not st.session_state.pro_unlocked and free_left <= 0:
            st.error(f"🔒 {ui['free_done']}")
        else:
            vid_id = extract_youtube_id(yt_url.strip())
            if not vid_id:
                st.error("❌ Invalid YouTube link.")
            else:
                yt_status_slot.markdown(f'<div class="loading-pill">{ui["fetching"]}</div>', unsafe_allow_html=True)
                data = fetch_youtube_details(vid_id)
                if not data:
                    yt_status_slot.empty()
                    st.error("❌ Could not fetch video data. Check if the video is Public.")
                else:
                    st.session_state.yt_metrics = data
                    st.session_state.yt_vid_id = vid_id
                    comments_block = "\n".join(data["comments"][:12]) if data["comments"] else "No public comments."
                    lang_rule = build_lang_instruction(report_lang)
                    prompt = f"""
You are a warm, encouraging, expert human social media growth advisor ("సలహాదారు").
Write a comprehensive, deeply detailed growth audit report (1,100 to 1,400 words) for a **{audience_scope}** audience using simple everyday spoken words (never use the word 'మెంటర్').
{lang_rule}

VIDEO DATA:
- Channel: {data['channel']}
- Title: {data['title']}
- Audio Language Tag: {data['audio_lang']}
- Views: {data['views']:,} | Likes: {data['likes']:,} | Comments: {data['comment_count']:,}
- Description: {data['description']}
- Tags: {', '.join(data['tags'])}
- Real Audience Comments:
{comments_block}

STRICTLY FOLLOW THIS 6-SECTION STRUCTURE (Translate all 6 headings into the target language's native script):
### 🎬 1. Video Story Recap & Creator Appreciation
- Warmly retell the core story/message of this video based on its title, description, and comments, then genuinely praise the creator's effort and strengths.

### 💬 2. Real Audience Comments & Reply Templates
- Pick 4 to 5 real viewer comments above, translate them naturally into the target language, quote them with the viewer's name, explain what viewers love/ask, and provide 3 ready-to-copy reply templates.

### 🔥 3. 3 Next Viral Video Ideas + 5-Sec Hooks
- Give 3 fresh follow-up video ideas tailored to this channel with an exact word-for-word 5-second opening Hook and Thumbnail idea for each.

### 🎯 4. Copy-Paste SEO Makeover (Titles, Description & 15 Tags)
- Provide 3 high-CTR title options, a 3-line SEO description hook, and 15 searchable tags.

### 💰 5. Monetization & Brand Earning Blueprint
- Explain 3 practical ways this channel can earn money (AdSense, Affiliate links, Brand sponsorships).

### 📅 6. Step-by-Step 30-Day Action Plan
- Give a clear Week 1 to Week 4 checklist to double views and subscribers.
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
                            st.session_state.detected_lang_name = m_lang.group(1).strip()
                        if not st.session_state.pro_unlocked:
                            increment_free_used(st.session_state.verified_email)
                        log_usage_to_sheet(st.session_state.verified_email or "PRO", "YouTube", yt_url.strip())
                        st.rerun()
                    except Exception as e:
                        yt_status_slot.empty()
                        st.error(str(e))

    if st.session_state.yt_report:
        if st.session_state.yt_metrics:
            d = st.session_state.yt_metrics
            m1, m2, m3 = st.columns(3)
            m1.metric("👀 Views", f"{d['views']:,}")
            m2.metric("👍 Likes", f"{d['likes']:,}")
            m3.metric("💬 Comments", f"{d['comment_count']:,}")
        st.success(ui["ready"])
        st.download_button(
            ui["download"],
            data=st.session_state.yt_report,
            file_name=f"TrendSutra_YouTube_Report_{st.session_state.yt_vid_id or 'audit'}.txt",
            mime="text/plain",
            key="dl_yt_persist"
        )
        st.markdown(st.session_state.yt_report)

with tab_ig:
    ic1, ic2, ic3 = st.columns([4.2, 1.8, 2.0])
    with ic1:
        ig_url = st.text_input("IG", placeholder="Paste Instagram Reel Link...", label_visibility="collapsed")
    with ic2:
        run_ig = st.button(ui["gen_btn"], key="btn_ig", type="primary", use_container_width=True)
    with ic3:
        ig_status_slot = st.empty()

    if run_ig:
        if not st.session_state.verified_email and not st.session_state.pro_unlocked:
            st.warning(f"⚠️ {ui['login_prompt']}")
        elif not ig_url.strip():
            st.warning("⚠️ Paste an Instagram Reel link first.")
        elif not st.session_state.pro_unlocked and free_left <= 0:
            st.error(f"🔒 {ui['free_done']}")
        else:
            ig_status_slot.markdown(f'<div class="loading-pill">{ui["generating"]}</div>', unsafe_allow_html=True)
            lang_rule = build_lang_instruction(report_lang)
            ig_prompt = f"""
You are a warm, encouraging human Instagram Reels growth advisor ("సలహాదారు").
Write a detailed 6-section Instagram Reels growth audit (1,000+ words) for a **{audience_scope}** audience using simple spoken words (never use 'మెంటర్').
{lang_rule}
Reel Link: {ig_url.strip()}
Include 6 sections (with headings translated into the target language's native script):
1. Creator Appreciation & Reel Strategy Overview
2. Watch-Time, Audio & Retention Hook Analysis
3. 3 Viral Follow-Up Reel Ideas with 3-second Hooks
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
            ui["download"],
            data=st.session_state.ig_report,
            file_name="TrendSutra_Instagram_Report.txt",
            mime="text/plain",
            key="dl_ig_persist"
        )
        st.markdown(st.session_state.ig_report)

with tab_tt:
    tc1, tc2, tc3 = st.columns([4.2, 1.8, 2.0])
    with tc1:
        tt_url = st.text_input("TT", placeholder="Paste TikTok Video Link...", label_visibility="collapsed")
    with tc2:
        run_tt = st.button(ui["gen_btn"], key="btn_tt", type="primary", use_container_width=True)
    with tc3:
        tt_status_slot = st.empty()

    if run_tt:
        if not st.session_state.verified_email and not st.session_state.pro_unlocked:
            st.warning(f"⚠️ {ui['login_prompt']}")
        elif not tt_url.strip():
            st.warning("⚠️ Paste a TikTok video link first.")
        elif not st.session_state.pro_unlocked and free_left <= 0:
            st.error(f"🔒 {ui['free_done']}")
        else:
            tt_status_slot.markdown(f'<div class="loading-pill">{ui["generating"]}</div>', unsafe_allow_html=True)
            lang_rule = build_lang_instruction(report_lang)
            tt_prompt = f"""
You are a warm, encouraging human TikTok growth advisor ("సలహాదారు").
Write a detailed 6-section TikTok growth audit (1,000+ words) for a **{audience_scope}** audience using simple spoken words (never use 'మెంటర్').
{lang_rule}
TikTok Link: {tt_url.strip()}
Include 6 sections (with headings translated into the target language's native script):
1. Creator Appreciation & Viral Potential Overview
2. Completion Rate & Looping Hook Formula
3. 3 Viral Follow-Up TikTok Ideas with 3-second Hooks
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
            ui["download"],
            data=st.session_state.tt_report,
            file_name="TrendSutra_TikTok_Report.txt",
            mime="text/plain",
            key="dl_tt_persist"
        )
        st.markdown(st.session_state.tt_report)

# --- TAB 4: VIRAL SCRIPT GENERATOR ---
with tab_script:
    sc1, sc2, sc3 = st.columns([3.4, 1.4, 1.4])
    with sc1:
        script_topic = st.text_input("Topic", placeholder="Enter your video topic (e.g., How to grow on YouTube in 2026)...", label_visibility="collapsed")
    with sc2:
        script_len = st.selectbox("Length", ["Shorts / Reel (60 Sec)", "Medium Video (3–5 Min)", "Long Video (8–10 Min)"], label_visibility="collapsed")
    with sc3:
        script_tone = st.selectbox("Tone", ["Energetic & Viral", "Emotional & Story", "Educational & Clear", "Funny & Entertaining"], label_visibility="collapsed")

    sb1, sb2 = st.columns([2.2, 5.8])
    with sb1:
        run_script = st.button(ui["script_btn"], key="btn_script", type="primary", use_container_width=True)
    with sb2:
        script_status_slot = st.empty()

    if run_script:
        if not st.session_state.verified_email and not st.session_state.pro_unlocked:
            st.warning(f"⚠️ {ui['login_prompt']}")
        elif not script_topic.strip():
            st.warning("⚠️ Enter a video topic first.")
        elif not st.session_state.pro_unlocked and free_left <= 0:
            st.error(f"🔒 {ui['free_done']}")
        else:
            script_status_slot.markdown(f'<div class="loading-pill">{ui["generating"]}</div>', unsafe_allow_html=True)
            lang_rule = build_lang_instruction(report_lang)
            script_prompt = f"""
You are a top viral YouTube & Reels scriptwriter ("సలహాదారు").
Write a complete, word-for-word, ready-to-shoot viral video script for a **{audience_scope}** audience in a **{script_tone}** tone.
{lang_rule}

TOPIC: {script_topic.strip()}
FORMAT / LENGTH: {script_len}

STRICTLY INCLUDE THESE 5 SECTIONS (with headings in the target language's native script):
### 🪝 1. 3 High-Retention Opening Hooks (First 5 Seconds)
- Write 3 scroll-stopping opening lines the creator can speak word-for-word.

### 🎬 2. Complete Word-for-Word Spoken Script + Visual/B-Roll Cues
- Write the full script divided into Hook, Body Points, Pattern Interrupts, and Ending CTA. Include `[Visual / On-screen text]` cues in brackets.

### 🎯 3. 3 Clickable Titles & Thumbnail Text Ideas
- Give 3 high-CTR titles and short 3-word thumbnail text ideas.

### 📝 4. Copy-Paste Description & 15 Hashtags/Tags
- Write a ready-to-paste video description and 15 searchable tags.

### 💡 5. Pro Delivery & Editing Tips
- Give 3 quick tips on pacing, background music, and retention for this exact script.
"""
            report_box = st.empty()
            full_text = ""
            try:
                for piece in generate_report_stream(script_prompt):
                    full_text += piece
                    report_box.markdown(full_text)
                script_status_slot.empty()
                st.session_state.script_report = full_text
                if not st.session_state.pro_unlocked:
                    increment_free_used(st.session_state.verified_email)
                log_usage_to_sheet(st.session_state.verified_email or "PRO", "ViralScript", script_topic.strip()[:80])
                st.rerun()
            except Exception as e:
                script_status_slot.empty()
                st.error(str(e))

    if st.session_state.script_report:
        st.success(ui["ready"])
        st.download_button(
            ui["download"],
            data=st.session_state.script_report,
            file_name="TrendSutra_Viral_Script.txt",
            mime="text/plain",
            key="dl_script_persist"
        )
        st.markdown(st.session_state.script_report)

# --- TAB 5: AI THUMBNAIL CHECKER ---
with tab_thumb:
    th1, th2 = st.columns([3.5, 4.5])
    with th1:
        thumb_file = st.file_uploader("Upload Thumbnail Image (JPG / PNG / WEBP):", type=["jpg", "jpeg", "png", "webp"], label_visibility="collapsed")
    with th2:
        thumb_title = st.text_input("Optional Title", placeholder="Optional: Enter your video title to check Title + Thumbnail match...", label_visibility="collapsed")
        tb_a, tb_b = st.columns([2.2, 2.3])
        with tb_a:
            run_thumb = st.button(ui["thumb_btn"], key="btn_thumb", type="primary", use_container_width=True)
        with tb_b:
            thumb_status_slot = st.empty()

    if run_thumb:
        if not st.session_state.verified_email and not st.session_state.pro_unlocked:
            st.warning(f"⚠️ {ui['login_prompt']}")
        elif thumb_file is None:
            st.warning("⚠️ Upload a thumbnail image first.")
        elif not st.session_state.pro_unlocked and free_left <= 0:
            st.error(f"🔒 {ui['free_done']}")
        else:
            thumb_status_slot.markdown(f'<div class="loading-pill">{ui["generating"]}</div>', unsafe_allow_html=True)
            pil_img = Image.open(thumb_file)
            lang_rule = build_lang_instruction(report_lang)
            thumb_prompt = f"""
You are a YouTube CTR & Thumbnail Design Expert ("సలహాదారు").
Analyze this uploaded YouTube/Reels thumbnail image for a **{audience_scope}** audience.
Video Title Context: {thumb_title.strip() if thumb_title.strip() else "Not provided"}
{lang_rule}

STRICTLY PROVIDE THESE 5 SECTIONS (with headings in the target language's native script):
### 📊 1. Overall CTR Score (Out of 10) & First Impression
- Give a clear score (e.g., **7.5 / 10**) and explain what a viewer notices in the first 0.5 seconds on mobile.

### 📱 2. Mobile Screen Readability & Text Check
- Evaluate if the text is too long, too small, or hidden by YouTube's timestamp badge, and suggest better 2–4 word thumbnail text.

### 🎨 3. Colors, Contrast & Emotion Analysis
- Analyze facial expression/subject focus, background clutter, and color contrast against YouTube's dark/light mode.

### 🛠️ 4. Top 3 Exact Fixes to Double Clicks (CTR)
- Give 3 specific, actionable edits the creator should make right now to boost clicks.

### 🔥 5. 3 Better Title + Thumbnail Combinations
- Suggest 3 winning Title + Thumbnail text pairs for A/B testing.
"""
            report_box = st.empty()
            full_text = ""
            try:
                for piece in generate_report_stream([thumb_prompt, pil_img]):
                    full_text += piece
                    report_box.markdown(full_text)
                thumb_status_slot.empty()
                st.session_state.thumb_report = full_text
                if not st.session_state.pro_unlocked:
                    increment_free_used(st.session_state.verified_email)
                log_usage_to_sheet(st.session_state.verified_email or "PRO", "ThumbnailCheck", thumb_title.strip()[:80] or "Image")
                st.rerun()
            except Exception as e:
                thumb_status_slot.empty()
                st.error(str(e))

    if st.session_state.thumb_report:
        st.success(ui["ready"])
        st.download_button(
            ui["download"],
            data=st.session_state.thumb_report,
            file_name="TrendSutra_Thumbnail_Audit.txt",
            mime="text/plain",
            key="dl_thumb_persist"
        )
        st.markdown(st.session_state.thumb_report)
