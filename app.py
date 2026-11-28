import os
import re
import json
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
from PIL import Image

st.set_page_config(
    page_title="TrendSutra AI - 1 AI • 1 India",
    page_icon="logo.png" if os.path.exists("logo.png") else "📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

def get_secret(key, default=""):
    try:
        return str(st.secrets.get(key, default)).strip()
    except Exception:
        return default

GEMINI_KEYS = []
for k_name in ["GEMINI_API_KEY_4", "GEMINI_API_KEY_3", "GEMINI_API_KEY_2", "GEMINI_API_KEY"]:
    val = get_secret(k_name)
    if val and val not in GEMINI_KEYS:
        GEMINI_KEYS.append(val)

YOUTUBE_KEY = get_secret("YOUTUBE_API_KEY")
SHEET_API = get_secret("GOOGLE_SHEET_API")
OWNER_CODE = get_secret("OWNER_SECRET_CODE")
SENDER_EMAIL = get_secret("SENDER_EMAIL")
SENDER_PASS = get_secret("SENDER_APP_PASSWORD").replace(" ", "")

RAZORPAY_1M = "https://rzp.io/rzp/70Y3L0K"
RAZORPAY_12M = "https://rzp.io/rzp/77zX68U"

TEMP_DOMAINS = {
    "mailinator.com", "tempmail.com", "10minutemail.com", "guerrillamail.com",
    "yopmail.com", "throwawaymail.com", "fakeinbox.com", "trashmail.com",
    "getnada.com", "temp-mail.org", "dispostable.com", "maildrop.cc"
}

LANG_OPTIONS = [
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
    "Sindhi (सिन्धी / سنڌي)",
    "Tamil (தமிழ்)",
    "Telugu (తెలుగు)",
    "Tenglish (Telugu + English)",
    "Urdu (اردو)"
]

UI_TEXT = {
    "English": {
        "free_left": "Free Reports Left",
        "free_over": "Your 3 Free Reports are completed!",
        "login_prompt": "Login with Gmail or Email OTP to unlock 3 Free Reports",
        "send_otp": "Send OTP 📩",
        "otp_sent": "6-digit OTP sent to {email}! Check Inbox/Spam.",
        "verify_otp": "Verify OTP ✅",
        "gen_btn": "Generate Growth Report 🔍",
        "fetching": "Fetching video details & comments...",
        "generating": "Generating report...",
        "ready": "Growth Audit Report Ready!",
        "download": "Download Complete Report (.txt)",
        "script_btn": "Generate Viral Script ✍️",
        "thumb_btn": "Analyze Thumbnail CTR 🖼️"
    },
    "Telugu": {
        "free_left": "ఉచిత రిపోర్ట్‌లు మిగిలాయి",
        "free_over": "మీ 3 ఉచిత రిపోర్ట్‌లు పూర్తయ్యాయి!",
        "login_prompt": "3 ఉచిత రిపోర్ట్‌ల కోసం Gmail లేదా Email OTP తో లాగిన్ అవ్వండి",
        "send_otp": "OTP పంపండి 📩",
        "otp_sent": "{email} కి 6-అంకెల OTP పంపబడింది! ఇన్‌బాక్స్ చెక్ చేయండి.",
        "verify_otp": "OTP నిర్ధారించండి ✅",
        "gen_btn": "గ్రోత్ రిపోర్ట్ తయారు చేయండి 🔍",
        "fetching": "వీడియో వివరాలు & కామెంట్లు సేకరిస్తోంది...",
        "generating": "రిపోర్ట్ తయారవుతోంది...",
        "ready": "గ్రోత్ ఆడిట్ రిపోర్ట్ సిద్ధమైంది!",
        "download": "పూర్తి రిపోర్ట్ డౌన్‌లోడ్ చేయండి (.txt)",
        "script_btn": "వైరల్ స్క్రిప్ట్ రాయండి ✍️",
        "thumb_btn": "థంబ్‌నెయిల్ చెక్ చేయండి 🖼️"
    },
    "Hindi": {
        "free_left": "मुफ्त रिपोर्ट बाकी हैं",
        "free_over": "आपकी 3 मुफ्त रिपोर्ट पूरी हो गई हैं!",
        "login_prompt": "3 मुफ्त रिपोर्ट पाने के लिए Gmail या Email OTP से लॉगिन करें",
        "send_otp": "OTP भेजें 📩",
        "otp_sent": "{email} पर 6-अंकों का OTP भेजा गया है!",
        "verify_otp": "OTP सत्यापित करें ✅",
        "gen_btn": "ग्रोथ रिपोर्ट बनाएं 🔍",
        "fetching": "वीडियो विवरण और कमेंट्स लिए जा रहे हैं...",
        "generating": "रिपोर्ट तैयार हो रही है...",
        "ready": "ग्रोथ ऑडिट रिपोर्ट तैयार है!",
        "download": "पूरी रिपोर्ट डाउनलोड करें (.txt)",
        "script_btn": "वायरल स्क्रिप्ट लिखें ✍️",
        "thumb_btn": "थंबनेल चेक करें 🖼️"
    },
    "Tamil": {
        "free_left": "இலவச அறிக்கைகள் உள்ளன",
        "free_over": "உங்கள் 3 இலவச அறிக்கைகள் முடிந்துவிட்டன!",
        "login_prompt": "3 இலவச அறிக்கைகளைப் பெற Gmail அல்லது Email OTP மூலம் உள்நுழையவும்",
        "send_otp": "OTP அனுப்பு 📩",
        "otp_sent": "{email} க்கு 6-இலக்க OTP அனுப்பப்பட்டது!",
        "verify_otp": "OTP சரிபார் ✅",
        "gen_btn": "வளர்ச்சி அறிக்கையை உருவாக்கு 🔍",
        "fetching": "வீடியோ விவரங்கள் சேகரிக்கப்படுகின்றன...",
        "generating": "அறிக்கை தயாராகிறது...",
        "ready": "வளர்ச்சி அறிக்கை தயார்!",
        "download": "முழு அறிக்கையைப் பதிவிறக்கவும் (.txt)",
        "script_btn": "வைரல் ஸ்கிரிப்ட் உருவாக்கு ✍️",
        "thumb_btn": "தம்ப்நெயில் சரிபார் 🖼️"
    },
    "Kannada": {
        "free_left": "ಉಚಿತ ವರದಿಗಳು ಉಳಿದಿವೆ",
        "free_over": "ನಿಮ್ಮ 3 ಉಚಿತ ವರದಿಗಳು ಪೂರ್ಣಗೊಂಡಿವೆ!",
        "login_prompt": "3 ಉಚಿತ ವರದಿಗಳಿಗಾಗಿ Gmail ಅಥವಾ Email OTP ಮೂಲಕ ಲಾಗಿನ್ ಆಗಿ",
        "send_otp": "OTP ಕಳುಹಿಸಿ 📩",
        "otp_sent": "{email} ಗೆ 6-ಅಂಕಿಯ OTP ಕಳುಹಿಸಲಾಗಿದೆ!",
        "verify_otp": "OTP ದೃಢೀಕರಿಸಿ ✅",
        "gen_btn": "ಗ್ರೋತ್ ವರದಿ ರಚಿಸಿ 🔍",
        "fetching": "ವೀಡಿಯೊ ವಿವರಗಳನ್ನು ಪಡೆಯಲಾಗುತ್ತಿದೆ...",
        "generating": "ವರದಿ ಸಿದ್ಧವಾಗುತ್ತಿದೆ...",
        "ready": "ಗ್ರೋತ್ ಆಡಿಟ್ ವರದಿ ಸಿದ್ಧವಾಗಿದೆ!",
        "download": "ಪೂರ್ಣ ವರದಿ ಡೌನ್‌ಲೋಡ್ ಮಾಡಿ (.txt)",
        "script_btn": "ವೈರಲ್ ಸ್ಕ್ರಿಪ್ಟ್ ರಚಿಸಿ ✍️",
        "thumb_btn": "ಥಂಬ್‌ನೇಲ್ ಪರಿಶೀಲಿಸಿ 🖼️"
    },
    "Malayalam": {
        "free_left": "സൗജന്യ റിപ്പോർട്ടുകൾ ബാക്കിയുണ്ട്",
        "free_over": "നിങ്ങളുടെ 3 സൗജന്യ റിപ്പോർട്ടുകൾ പൂർത്തിയായി!",
        "login_prompt": "3 സൗജന്യ റിപ്പോർട്ടുകൾക്കായി Gmail അല്ലെങ്കിൽ Email OTP ഉപയോഗിച്ച് ലോഗിൻ ചെയ്യുക",
        "send_otp": "OTP അയക്കുക 📩",
        "otp_sent": "{email}-ലേക്ക് 6-അക്ക OTP അയച്ചു!",
        "verify_otp": "OTP സ്ഥിരീകരിക്കുക ✅",
        "gen_btn": "ഗ്രോത്ത് റിപ്പോർട്ട് തയ്യാറാക്കുക 🔍",
        "fetching": "വീഡിയോ വിവരങ്ങൾ ശേഖരിക്കുന്നു...",
        "generating": "റിപ്പോർട്ട് തയ്യാറാകുന്നു...",
        "ready": "ഗ്രോത്ത് ഓഡിറ്റ് റിപ്പോർട്ട് തയ്യാറായി!",
        "download": "പൂർണ്ണ റിപ്പോർട്ട് ഡൗൺലോഡ് ചെയ്യുക (.txt)",
        "script_btn": "വൈറൽ സ്ക്രിപ്റ്റ് തയ്യാറാക്കുക ✍️",
        "thumb_btn": "തംബ്നെയിൽ പരിശോധിക്കുക 🖼️"
    },
    "Marathi": {
        "free_left": "मोफत रिपोर्ट शिल्लक आहेत",
        "free_over": "तुमचे 3 मोफत रिपोर्ट पूर्ण झाले आहेत!",
        "login_prompt": "3 मोफत रिपोर्टसाठी Gmail किंवा Email OTP ने लॉगिन करा",
        "send_otp": "OTP पाठवा 📩",
        "otp_sent": "{email} वर 6-अंकी OTP पाठवला आहे!",
        "verify_otp": "OTP तपासा ✅",
        "gen_btn": "ग्रोथ रिपोर्ट तयार करा 🔍",
        "fetching": "व्हिडिओ माहिती गोळा केली जात आहे...",
        "generating": "रिपोर्ट तयार होत आहे...",
        "ready": "ग्रोथ ऑडिट रिपोर्ट तयार आहे!",
        "download": "संपूर्ण रिपोर्ट डाउनलोड करा (.txt)",
        "script_btn": "व्हायरल स्क्रिप्ट तयार करा ✍️",
        "thumb_btn": "थंबनेल तपासा 🖼️"
    },
    "Bengali": {
        "free_left": "ফ্রি রিপোর্ট বাকি আছে",
        "free_over": "আপনার ৩টি ফ্রি রিপোর্ট শেষ হয়েছে!",
        "login_prompt": "৩টি ফ্রি রিপোর্টের জন্য Gmail বা Email OTP দিয়ে লগইন করুন",
        "send_otp": "OTP পাঠান 📩",
        "otp_sent": "{email}-এ ৬-সংখ্যার OTP পাঠানো হয়েছে!",
        "verify_otp": "OTP যাচাই করুন ✅",
        "gen_btn": "গ্রোথ রিপোর্ট তৈরি করুন 🔍",
        "fetching": "ভিডিওর তথ্য সংগ্রহ করা হচ্ছে...",
        "generating": "রিপোর্ট তৈরি হচ্ছে...",
        "ready": "গ্রোথ অডিট রিপোর্ট তৈরি!",
        "download": "সম্পূর্ণ রিপোর্ট ডাউনলোড করুন (.txt)",
        "script_btn": "ভাইরাল স্ক্রিপ্ট লিখুন ✍️",
        "thumb_btn": "থাম্বনেইল যাচাই করুন 🖼️"
    },
    "Gujarati": {
        "free_left": "મફત રિપોર્ટ બાકી છે",
        "free_over": "તમારા 3 મફત રિપોર્ટ પૂર્ણ થઈ ગયા છે!",
        "login_prompt": "3 મફત રિપોર્ટ માટે Gmail અથવા Email OTP થી લોગિન કરો",
        "send_otp": "OTP મોકલો 📩",
        "otp_sent": "{email} પર 6-અંકનો OTP મોકલવામાં આવ્યો છે!",
        "verify_otp": "OTP ચકાસો ✅",
        "gen_btn": "ગ્રોથ રિપોર્ટ બનાવો 🔍",
        "fetching": "વિડિઓ વિગતો મેળવવામાં આવી રહી છે...",
        "generating": "રિપોર્ટ તૈયાર થઈ રહ્યો છે...",
        "ready": "ગ્રોથ ઓડિટ રિપોર્ટ તૈયાર છે!",
        "download": "સંપૂર્ણ રિપોર્ટ ડાઉનલોડ કરો (.txt)",
        "script_btn": "વાયરલ સ્ક્રિપ્ટ બનાવો ✍️",
        "thumb_btn": "થમ્બનેઇલ તપાસો 🖼️"
    },
    "Punjabi": {
        "free_left": "ਮੁਫ਼ਤ ਰਿਪੋਰਟਾਂ ਬਾਕੀ ਹਨ",
        "free_over": "ਤੁਹਾਡੀਆਂ 3 ਮੁਫ਼ਤ ਰਿਪੋਰਟਾਂ ਪੂਰੀਆਂ ਹੋ ਗਈਆਂ ਹਨ!",
        "login_prompt": "3 ਮੁਫ਼ਤ ਰਿਪੋਰਟਾਂ ਲਈ Gmail ਜਾਂ Email OTP ਨਾਲ ਲੌਗਇਨ ਕਰੋ",
        "send_otp": "OTP ਭੇਜੋ 📩",
        "otp_sent": "{email} 'ਤੇ 6-ਅੰਕਾਂ ਦਾ OTP ਭੇਜਿਆ ਗਿਆ ਹੈ!",
        "verify_otp": "OTP ਪੁਸ਼ਟੀ ਕਰੋ ✅",
        "gen_btn": "ਗਰੋਥ ਰਿਪੋਰਟ ਬਣਾਓ 🔍",
        "fetching": "ਵੀਡੀਓ ਜਾਣਕਾਰੀ ਇਕੱਠੀ ਕੀਤੀ ਜਾ ਰਹੀ ਹੈ...",
        "generating": "ਰਿਪੋਰਟ ਤਿਆਰ ਹੋ ਰਹੀ ਹੈ...",
        "ready": "ਗਰੋਥ ਆਡਿਟ ਰਿਪੋਰਟ ਤਿਆਰ ਹੈ!",
        "download": "ਪੂਰੀ ਰਿਪੋਰਟ ਡਾਊਨਲੋਡ ਕਰੋ (.txt)",
        "script_btn": "ਵਾਇਰਲ ਸਕ੍ਰਿਪਟ ਲਿਖੋ ✍️",
        "thumb_btn": "ਥੰਬਨੇਲ ਚੈੱਕ ਕਰੋ 🖼️"
    },
    "Odia": {
        "free_left": "ମାଗଣା ରିପୋର୍ଟ ବାକି ଅଛି",
        "free_over": "ଆପଣଙ୍କର ୩ଟି ମାଗଣା ରିପୋର୍ଟ ଶେଷ ହୋଇଯାଇଛି!",
        "login_prompt": "୩ଟି ମାଗଣା ରିପୋର୍ଟ ପାଇଁ Gmail କିମ୍ବା Email OTP ସହ ଲଗଇନ୍ କରନ୍ତୁ",
        "send_otp": "OTP ପଠାନ୍ତୁ 📩",
        "otp_sent": "{email} କୁ ୬-ଅଙ୍କ ବିଶିଷ୍ଟ OTP ପଠାଯାଇଛି!",
        "verify_otp": "OTP ଯାଞ୍ଚ କରନ୍ତୁ ✅",
        "gen_btn": "ଗ୍ରୋଥ୍ ରିପୋର୍ଟ ତିଆରି କରନ୍ତୁ 🔍",
        "fetching": "ଭିଡିଓ ତଥ୍ୟ ସଂଗ୍ରହ କରାଯାଉଛି...",
        "generating": "ରିପୋର୍ଟ ପ୍ରସ୍ତୁତ ହେଉଛି...",
        "ready": "ଗ୍ରୋଥ୍ ଅଡିଟ୍ ରିପୋର୍ଟ ପ୍ରସ୍ତୁତ!",
        "download": "ସମ୍ପୂର୍ଣ୍ଣ ରିପୋର୍ଟ ଡାଉନଲୋଡ୍ କରନ୍ତୁ (.txt)",
        "script_btn": "ଭାଇରାଲ୍ ସ୍କ୍ରିପ୍ଟ ଲେଖନ୍ତୁ ✍️",
        "thumb_btn": "ଥମ୍ବନେଲ୍ ଯାଞ୍ଚ କରନ୍ତୁ 🖼️"
    },
    "Assamese": {
        "free_left": "বিনামূলীয়া ৰিপ'ৰ্ট বাকী আছে",
        "free_over": "আপোনাৰ ৩টা বিনামূলীয়া ৰিপ'ৰ্ট সম্পূৰ্ণ হৈছে!",
        "login_prompt": "৩টা বিনামূলীয়া ৰিপ'ৰ্টৰ বাবে Gmail বা Email OTP ৰে লগইন কৰক",
        "send_otp": "OTP পঠিয়াওক 📩",
        "otp_sent": "{email} লৈ ৬-সংখ্যাৰ OTP পঠিওৱা হৈছে!",
        "verify_otp": "OTP নিশ্চিত কৰক ✅",
        "gen_btn": "গ্ৰোথ ৰিপ'ৰ্ট বনাওক 🔍",
        "fetching": "ভিডিঅ'ৰ তথ্য সংগ্ৰহ কৰা হৈছে...",
        "generating": "ৰিপ'ৰ্ট প্ৰস্তুত হৈ আছে...",
        "ready": "গ্ৰোথ অডিট ৰিপ'ৰ্ট সাজু!",
        "download": "সম্পূৰ্ণ ৰিপ'ৰ্ট ডাউনলোড কৰক (.txt)",
        "script_btn": "ভাইৰেল স্ক্ৰিপ্ট লিখক ✍️",
        "thumb_btn": "থাম্বনেইল পৰীক্ষা কৰক 🖼️"
    },
    "Urdu": {
        "free_left": "مفت رپورٹس باقی ہیں",
        "free_over": "آپ کی 3 مفت رپورٹس مکمل ہو گئی ہیں!",
        "login_prompt": "3 مفت رپورٹس حاصل کرنے کے لیے Gmail یا Email OTP سے لاگ ان کریں",
        "send_otp": "OTP بھیجیں 📩",
        "otp_sent": "{email} پر 6 ہندسوں کا OTP بھیج دیا گیا ہے!",
        "verify_otp": "OTP تصدیق کریں ✅",
        "gen_btn": "گروتھ رپورٹ بنائیں 🔍",
        "fetching": "ویڈیو کی تفصیلات حاصل کی جا رہی ہیں...",
        "generating": "رپورٹ تیار ہو رہی ہے...",
        "ready": "گروتھ آڈٹ رپورٹ تیار ہے!",
        "download": "مکمل رپورٹ ڈاؤن لوڈ کریں (.txt)",
        "script_btn": "وائرل اسکرپٹ لکھیں ✍️",
        "thumb_btn": "تھمب نیل چیک کریں 🖼️"
    },
    "Bhojpuri": {
        "free_left": "मुफ्त रिपोर्ट बाचल बा",
        "free_over": "रउआ 3 गो मुफ्त रिपोर्ट पूरा हो गइल बा!",
        "login_prompt": "3 गो मुफ्त रिपोर्ट खातिर Gmail या Email OTP से लॉगिन करीं",
        "send_otp": "OTP भेजीं 📩",
        "otp_sent": "{email} पर 6 अंक के OTP भेज दिहल गइल बा!",
        "verify_otp": "OTP सत्यापित करीं ✅",
        "gen_btn": "ग्रोथ रिपोर्ट बनाईं 🔍",
        "fetching": "वीडियो के जानकारी जुटावल जा रहल बा...",
        "generating": "रिपोर्ट तैयार हो रहल बा...",
        "ready": "ग्रोथ ऑडिट रिपोर्ट तैयार बा!",
        "download": "पूरा रिपोर्ट डाउनलोड करीं (.txt)",
        "script_btn": "वायरल स्क्रिप्ट लिखीं ✍️",
        "thumb_btn": "थंबनेल चेक करीं 🖼️"
    }
}

def get_ui(selected_lang):
    if selected_lang.startswith("Auto-Detect"):
        return UI_TEXT["English"]
    base = selected_lang.split("(")[0].strip()
    if base in ("Hinglish",):
        return UI_TEXT["Hindi"]
    if base in ("Tenglish",):
        return UI_TEXT["Telugu"]
    return UI_TEXT.get(base, UI_TEXT["English"])

st.markdown("""
<style>
    [data-testid="stToolbarActions"],
    [data-testid="stDecoration"],
    .stDeployButton,
    #MainMenu,
    footer {
        display: none !important;
    }
    header[data-testid="stHeader"] {
        background: transparent !important;
        pointer-events: none !important;
    }
    [data-testid="stSidebarCollapsedControl"] {
        pointer-events: auto !important;
        visibility: visible !important;
        opacity: 1 !important;
        z-index: 999999 !important;
    }
    .block-container {
        padding-top: 3.6rem !important;
        padding-bottom: 1rem !important;
        max-width: 1180px;
    }
    section[data-testid="stSidebar"] .block-container {
        padding-top: 0.7rem !important;
        padding-bottom: 0.5rem !important;
    }
    section[data-testid="stSidebar"] hr {
        margin: 0.45rem 0 !important;
    }
    section[data-testid="stSidebar"] .stMarkdown p {
        margin-bottom: 0.25rem !important;
        font-size: 0.88rem !important;
        line-height: 1.45 !important;
    }
    .main-header {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        padding: 15px 22px;
        border-radius: 14px;
        border: 2px solid #10b981;
        margin-bottom: 12px;
        text-align: center;
        box-shadow: 0 4px 16px rgba(16, 185, 129, 0.14);
    }
    .header-title-row {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 12px;
    }
    .main-header h1 {
        margin: 0;
        font-size: 1.75rem;
        color: #ffffff;
        font-weight: 800;
        letter-spacing: 0.3px;
    }
    .main-header p {
        margin: 4px 0 0 0;
        color: #cbd5e1;
        font-size: 0.92rem;
    }
    .india-badge {
        display: inline-block;
        margin-top: 6px;
        padding: 3px 12px;
        border-radius: 999px;
        background: rgba(16, 185, 129, 0.15);
        border: 1px solid rgba(16, 185, 129, 0.45);
        color: #6ee7b7;
        font-size: 0.78rem;
        font-weight: 600;
    }
    .status-strip {
        background: #1e293b;
        border: 1px solid #334155;
        border-radius: 10px;
        padding: 8px 14px;
        color: #f8fafc;
        font-size: 0.9rem;
        display: flex;
        align-items: center;
        height: 40px;
    }
    .loading-pill {
        background: rgba(16, 185, 129, 0.15);
        border: 1.5px solid #10b981;
        color: #6ee7b7;
        padding: 8px 14px;
        border-radius: 8px;
        font-weight: 600;
        font-size: 0.88rem;
        text-align: center;
        height: 40px;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    div.stButton > button {
        height: 40px !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
    }
    div[data-testid="stTextInput"] input {
        height: 40px !important;
        border-radius: 8px !important;
    }
</style>
""", unsafe_allow_html=True)

for key, default_val in [
    ("verified_email", ""),
    ("otp_code", ""),
    ("otp_target", ""),
    ("pro_unlocked", False),
    ("pro_label", ""),
    ("yt_report", ""),
    ("yt_vid_id", ""),
    ("ig_report", ""),
    ("tt_report", ""),
    ("script_report", ""),
    ("thumb_report", ""),
    ("exhausted_keys", []),
    ("exhausted_date", "")
]:
    if key not in st.session_state:
        st.session_state[key] = default_val

today_str = datetime.now().strftime("%Y-%m-%d")
if st.session_state.exhausted_date != today_str:
    st.session_state.exhausted_keys = []
    st.session_state.exhausted_date = today_str

try:
    if hasattr(st, "user") and getattr(st.user, "is_logged_in", False):
        g_email = getattr(st.user, "email", "")
        if g_email:
            st.session_state.verified_email = g_email.strip().lower()
except Exception:
    pass

def get_free_used_count(user_id):
    if not SHEET_API or not user_id:
        return 0
    try:
        r = requests.get(
            SHEET_API,
            params={"device": user_id.strip().lower(), "_ts": str(time.time())},
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
                params={"device": user_id.strip().lower(), "inc": "1", "_ts": str(time.time())},
                timeout=10,
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
            params={
                "log": "1",
                "device": (user_id or "PRO").strip().lower(),
                "platform": platform,
                "url": url,
                "_ts": str(time.time())
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

try:
    qp = st.query_params
    auto_pid = str(qp.get("razorpay_payment_id", "")).strip()
    if auto_pid.startswith("pay_") and not st.session_state.pro_unlocked:
        st_res = verify_payment_id(auto_pid, plan="1m")
        if st_res == "VALID":
            st.session_state.pro_unlocked = True
            st.session_state.pro_label = "PRO ACTIVE"
            st.query_params.clear()
            st.rerun()
except Exception:
    pass

def send_otp_email(to_email, code):
    if not SENDER_EMAIL or not SENDER_PASS:
        return False, "SMTP not configured in Secrets"
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
            "description": snip.get("description", "")[:1200],
            "tags": snip.get("tags", [])[:20],
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
        client = genai.Client(api_key=api_key, http_options=types.HttpOptions(timeout=8000))
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

def generate_report_stream(contents_payload):
    if not GEMINI_KEYS:
        raise RuntimeError("No GEMINI_API_KEY configured in Secrets.")
    active_keys = [k for k in GEMINI_KEYS if k not in st.session_state.exhausted_keys]
    if not active_keys:
        st.session_state.exhausted_keys = []
        active_keys = GEMINI_KEYS[:]

    last_err = ""
    for api_key in active_keys:
        is_paid_backup = (api_key == GEMINI_KEYS[-1] and len(GEMINI_KEYS) > 1)
        timeout_ms = 35000 if is_paid_backup else 12000
        try:
            client = genai.Client(api_key=api_key, http_options=types.HttpOptions(timeout=timeout_ms))
            models = discover_models_for_key(api_key)
        except Exception as e:
            last_err = str(e)
            continue

        key_quota_hit = False
        for model_name in models:
            try:
                response = client.models.generate_content_stream(
                    model=model_name,
                    contents=contents_payload,
                    config=types.GenerateContentConfig(
                        temperature=0.80,
                        max_output_tokens=6500
                    )
                )
                yielded = False
                for chunk in response:
                    if chunk.text:
                        yielded = True
                        yield clean_mentor_word(chunk.text)
                if yielded:
                    return
            except Exception as e:
                err_str = str(e)
                last_err = err_str
                if any(tok in err_str.lower() for tok in ["429", "quota", "resource_exhausted", "rate", "exceeded"]):
                    key_quota_hit = True
                    break
                continue

        if key_quota_hit and not is_paid_backup:
            if api_key not in st.session_state.exhausted_keys:
                st.session_state.exhausted_keys.append(api_key)

    raise RuntimeError(f"AI servers are busy right now. Please try again in 5 seconds. ({last_err})")

def build_language_directive(selected_lang):
    if selected_lang.startswith("Auto-Detect"):
        return """
LANGUAGE DETECTION & NATIVE SCRIPT RULE (CRITICAL):
1. Detect the primary spoken/written language of this video/content from its title, description, tags, and audience comments.
2. Output the very first line in exact format: `🌐 **Detected Video Language:** <Language Name>`
3. Write the ENTIRE report — INCLUDING ALL 6 SECTION HEADINGS AND ALL BODY TEXT — in that detected language's NATIVE SCRIPT (for example: Telugu in తెలుగు లిపి, Hindi in देवनागरी, Tamil in தமிழ், Kannada in ಕನ್ನಡ, Malayalam in മലയാളം, Marathi in मराठी, Bengali in বাংলা, Gujarati in ગુજરાતી, Punjabi in ਪੰਜਾਬੀ, Odia in ଓଡ଼ିଆ, Assamese in অসমীয়া, Urdu in اردو script, Bhojpuri in देवनागरी, etc.).
4. Use simple, warm, everyday spoken words that any creator can easily understand.
"""
    else:
        return f"""
STRICT TARGET LANGUAGE & NATIVE SCRIPT RULE (CRITICAL):
1. Write the ENTIRE report — INCLUDING ALL 6 SECTION HEADINGS AND ALL BODY TEXT — strictly in **{selected_lang}** using its NATIVE SCRIPT (never transliterate into English letters unless English/Hinglish/Tenglish was chosen).
2. Output the very first line in exact format: `🌐 **Report Language:** {selected_lang}`
3. Use simple, warm, everyday spoken words that any creator can easily understand.
"""

logo_html = ""
if os.path.exists("logo.png"):
    with open("logo.png", "rb") as img_f:
        b64 = base64.b64encode(img_f.read()).decode()
    logo_html = f'<img src="data:image/png;base64,{b64}" style="width:40px; height:40px; border-radius:9px; object-fit:contain;" />'

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
        LANG_OPTIONS,
        index=0
    )
    ui = get_ui(report_lang)
    audience_scope = st.radio("Audience:", ["Regional", "Global", "Both"], horizontal=True)

    st.divider()
    st.markdown("### 💎 Pro Plans")

    free_used = get_free_used_count(st.session_state.verified_email) if st.session_state.verified_email else 0
    free_left = max(0, 3 - free_used)

    if st.session_state.pro_unlocked:
        st.success(f"✅ {st.session_state.pro_label}")
    elif st.session_state.verified_email:
        if free_left > 0:
            st.info(f"🎁 **{free_left}/3 {ui['free_left']}**")
        else:
            st.error(f"🔒 {ui['free_over']}")
    else:
        st.info("🎁 Login for **3 Free Reports**")

    st.markdown(
        f"<div style='font-size:0.86rem; line-height:1.65; margin-bottom:6px;'>"
        f"• <b>1 Month:</b> ₹100 👉 <a href='{RAZORPAY_1M}' target='_blank'>Pay ₹100</a><br>"
        f"• <b>12 Months:</b> ₹1,000 👉 <a href='{RAZORPAY_12M}' target='_blank'>Pay ₹1,000</a>"
        f"</div>",
        unsafe_allow_html=True
    )
    plan_choice = st.radio("Plan:", ["1M (₹100)", "12M (₹1,000)"], horizontal=True, label_visibility="collapsed")
    pay_input = st.text_input("Payment ID:", placeholder="Paste Payment ID (pay_...)", label_visibility="collapsed")
    if st.button("Unlock Pro 🔓", use_container_width=True):
        if not pay_input.strip():
            st.warning("Enter Payment ID")
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
                st.error("Plan Expired! Please recharge.")
            elif status == "ALREADY_USED":
                st.error("Used on max 3 devices.")
            else:
                st.error("Invalid Payment ID")

    st.divider()
    st.caption("📩 support@aiengtel.com | aiengtel.com")

if not st.session_state.verified_email and not st.session_state.pro_unlocked:
    col_g, col_or, col_e, col_b = st.columns([2.1, 0.4, 2.3, 1.5])
    with col_g:
        if st.button("🔵 Continue with Gmail", type="primary", use_container_width=True):
            try:
                st.login("google")
            except Exception as e:
                st.error(f"Gmail Login error: {e}")
    with col_or:
        st.markdown("<div style='text-align:center; padding-top:9px; color:#94a3b8; font-weight:700;'>OR</div>", unsafe_allow_html=True)
    with col_e:
        email_in = st.text_input("Email", placeholder="Login with Mail ID (Enter Email)", label_visibility="collapsed")
    with col_b:
        if st.button(ui["send_otp"], use_container_width=True):
            clean_em = email_in.strip().lower()
            if "@" not in clean_em or "." not in clean_em.split("@")[-1]:
                st.error("Enter valid Email ID")
            elif clean_em.split("@")[-1] in TEMP_DOMAINS:
                st.error("Temp email not allowed")
            else:
                code = str(random.randint(100000, 999999))
                ok, err_msg = send_otp_email(clean_em, code)
                if ok:
                    st.session_state.otp_code = code
                    st.session_state.otp_target = clean_em
                    st.toast(ui["otp_sent"].format(email=clean_em), icon="📩")
                else:
                    st.error(f"OTP Error: {err_msg}")

    if st.session_state.otp_target:
        oc1, oc2, oc3 = st.columns([2.5, 1.8, 1.5])
        with oc1:
            st.info(ui["otp_sent"].format(email=st.session_state.otp_target))
        with oc2:
            otp_in = st.text_input("OTP", placeholder="Enter 6-digit OTP", max_chars=6, label_visibility="collapsed")
        with oc3:
            if st.button(ui["verify_otp"], type="primary", use_container_width=True):
                if otp_in.strip() == st.session_state.otp_code:
                    st.session_state.verified_email = st.session_state.otp_target
                    st.session_state.otp_code = ""
                    st.rerun()
                else:
                    st.error("Wrong OTP")
else:
    s1, s2 = st.columns([4.8, 1.2])
    with s1:
        who = st.session_state.verified_email if st.session_state.verified_email else "Pro Member"
        badge = f"✅ {st.session_state.pro_label}" if st.session_state.pro_unlocked else f"🎁 {free_left}/3 {ui['free_left']}"
        st.markdown(f'<div class="status-strip">👤 Logged in as <b>&nbsp;{who}&nbsp;</b> | &nbsp;<b>{badge}</b></div>', unsafe_allow_html=True)
    with s2:
        if st.button("Logout", use_container_width=True):
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

tab_yt, tab_ig, tab_tt, tab_sc, tab_th = st.tabs([
    "📺 YouTube Analyzer",
    "📸 Instagram Reels",
    "🎵 TikTok Analyzer",
    "✍️ Viral Script Generator",
    "🖼️ AI Thumbnail Checker"
])

with tab_yt:
    c_in, c_btn, c_st = st.columns([3.5, 1.6, 1.5])
    with c_in:
        yt_url = st.text_input("YT Link", placeholder="Paste YouTube Video or Shorts Link...", label_visibility="collapsed")
    with c_btn:
        run_yt = st.button(ui["gen_btn"], key="btn_yt", type="primary", use_container_width=True)
    with c_st:
        yt_status = st.empty()

    if run_yt:
        if not st.session_state.verified_email and not st.session_state.pro_unlocked:
            st.warning(f"🔐 {ui['login_prompt']}")
        elif not yt_url.strip():
            st.warning("Paste a YouTube link first.")
        elif not st.session_state.pro_unlocked and free_left <= 0:
            st.error(f"🔒 {ui['free_over']}")
        else:
            vid_id = extract_youtube_id(yt_url.strip())
            if not vid_id:
                st.error("❌ Invalid YouTube link.")
            else:
                yt_status.markdown(f'<div class="loading-pill">🔄 {ui["fetching"]}</div>', unsafe_allow_html=True)
                data = fetch_youtube_details(vid_id)
                if not data:
                    yt_status.empty()
                    st.error("❌ Could not fetch video data. Check if the video is Public.")
                else:
                    lang_rule = build_language_directive(report_lang)
                    comments_block = "\n".join(data["comments"][:15]) if data["comments"] else "No public comments."
                    prompt = f"""
You are a warm, encouraging human social media growth advisor ("సలహాదారు").
Write a comprehensive, deeply helpful growth audit report (1,000–1,300 words) for a **{audience_scope}** audience.
NEVER use the word 'మెంటర్'—use 'సలహాదారు' if Telugu is used.

{lang_rule}

VIDEO DATA:
- Channel: {data['channel']}
- Title: {data['title']}
- Views: {data['views']:,} | Likes: {data['likes']:,} | Comments: {data['comment_count']:,}
- Description: {data['description']}
- Tags: {', '.join(data['tags'])}
- Real Audience Comments:
{comments_block}

WRITE THESE 6 SECTIONS (TRANSLATE ALL 6 HEADINGS INTO THE TARGET/DETECTED LANGUAGE'S NATIVE SCRIPT):
### 🎬 1. Video Story Recap & Creator Appreciation
- Warmly retell the core story/message of this video and genuinely praise the creator's effort, topic, and presentation.
### 💬 2. Real Audience Comments & Reply Templates
- Quote 4–5 real comments above, translate/explain them naturally in the target/detected language, and give 3 ready-to-copy reply templates.
### 🔥 3. 3 Next Viral Video Ideas + 5-Sec Opening Hooks
- Give 3 fresh follow-up video ideas with exact word-for-word 5-second opening hooks and thumbnail concepts.
### 🎯 4. Copy-Paste SEO Makeover (Titles, Description & 15 Tags)
- Provide 3 high-CTR titles, a 3-line SEO description, and 15 comma-separated tags.
### 💰 5. Monetization & Earning Blueprint
- Explain 3 practical ways this channel can earn money (AdSense, Affiliate, Brand deals).
### 📅 6. 30-Day Step-by-Step Growth Action Plan
- Give a Week 1 to Week 4 checklist of simple actions to grow views and subscribers.
"""
                    yt_status.markdown(f'<div class="loading-pill">⚡ {ui["generating"]} ⏳</div>', unsafe_allow_html=True)
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
                        log_usage_to_sheet(st.session_state.verified_email, "YouTube", yt_url.strip())
                        st.rerun()
                    except Exception as e:
                        yt_status.empty()
                        st.error(str(e))

    if st.session_state.yt_report:
        st.success(f"✅ {ui['ready']}")
        st.markdown(st.session_state.yt_report)
        st.download_button(
            f"📥 {ui['download']}",
            data=st.session_state.yt_report,
            file_name=f"TrendSutra_YouTube_{st.session_state.yt_vid_id or 'Report'}.txt",
            mime="text/plain",
            use_container_width=True
        )

with tab_ig:
    ic_in, ic_btn, ic_st = st.columns([3.5, 1.6, 1.5])
    with ic_in:
        ig_url = st.text_input("IG Link", placeholder="Paste Instagram Reel Link...", label_visibility="collapsed")
    with ic_btn:
        run_ig = st.button(ui["gen_btn"], key="btn_ig", type="primary", use_container_width=True)
    with ic_st:
        ig_status = st.empty()

    if run_ig:
        if not st.session_state.verified_email and not st.session_state.pro_unlocked:
            st.warning(f"🔐 {ui['login_prompt']}")
        elif not ig_url.strip():
            st.warning("Paste an Instagram Reel link first.")
        elif not st.session_state.pro_unlocked and free_left <= 0:
            st.error(f"🔒 {ui['free_over']}")
        else:
            lang_rule = build_language_directive(report_lang)
            ig_prompt = f"""
You are a warm, encouraging human Instagram Reels growth advisor ("సలహాదారు").
Write a detailed 6-section Instagram Reels growth audit (900+ words) for a **{audience_scope}** audience.
{lang_rule}
Reel Link: {ig_url.strip()}
Translate all 6 headings into the target/detected language's native script:
1. Creator Appreciation & Reel Strategy Overview
2. Watch-Time, Audio & 3-Second Retention Hook Analysis
3. 3 Viral Follow-Up Reel Ideas with word-for-word 3-second Hooks
4. Copy-Paste Caption & 15 Trending Hashtags
5. Brand Collaboration & Monetization Plan
6. 30-Day Instagram Growth Action Plan
"""
            ig_status.markdown(f'<div class="loading-pill">⚡ {ui["generating"]} ⏳</div>', unsafe_allow_html=True)
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
                log_usage_to_sheet(st.session_state.verified_email, "Instagram", ig_url.strip())
                st.rerun()
            except Exception as e:
                ig_status.empty()
                st.error(str(e))

    if st.session_state.ig_report:
        st.success(f"✅ {ui['ready']}")
        st.markdown(st.session_state.ig_report)
        st.download_button(
            f"📥 {ui['download']}",
            data=st.session_state.ig_report,
            file_name="TrendSutra_Instagram_Report.txt",
            mime="text/plain",
            use_container_width=True
        )

with tab_tt:
    tc_in, tc_btn, tc_st = st.columns([3.5, 1.6, 1.5])
    with tc_in:
        tt_url = st.text_input("TT Link", placeholder="Paste TikTok Video Link...", label_visibility="collapsed")
    with tc_btn:
        run_tt = st.button(ui["gen_btn"], key="btn_tt", type="primary", use_container_width=True)
    with tc_st:
        tt_status = st.empty()

    if run_tt:
        if not st.session_state.verified_email and not st.session_state.pro_unlocked:
            st.warning(f"🔐 {ui['login_prompt']}")
        elif not tt_url.strip():
            st.warning("Paste a TikTok link first.")
        elif not st.session_state.pro_unlocked and free_left <= 0:
            st.error(f"🔒 {ui['free_over']}")
        else:
            lang_rule = build_language_directive(report_lang)
            tt_prompt = f"""
You are a warm, encouraging human TikTok growth advisor ("సలహాదారు").
Write a detailed 6-section TikTok growth audit (900+ words) for a **{audience_scope}** audience.
{lang_rule}
TikTok Link: {tt_url.strip()}
Translate all 6 headings into the target/detected language's native script:
1. Creator Appreciation & Viral Potential Overview
2. Completion Rate & Looping Hook Formula
3. 3 Viral Follow-Up TikTok Ideas with word-for-word 3-second Hooks
4. Copy-Paste Caption & 15 FYP Hashtags
5. Creator Rewards & Brand Monetization Plan
6. 30-Day TikTok Growth Action Plan
"""
            tt_status.markdown(f'<div class="loading-pill">⚡ {ui["generating"]} ⏳</div>', unsafe_allow_html=True)
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
                log_usage_to_sheet(st.session_state.verified_email, "TikTok", tt_url.strip())
                st.rerun()
            except Exception as e:
                tt_status.empty()
                st.error(str(e))

    if st.session_state.tt_report:
        st.success(f"✅ {ui['ready']}")
        st.markdown(st.session_state.tt_report)
        st.download_button(
            f"📥 {ui['download']}",
            data=st.session_state.tt_report,
            file_name="TrendSutra_TikTok_Report.txt",
            mime="text/plain",
            use_container_width=True
        )

with tab_sc:
    sc1, sc2, sc3, sc4 = st.columns([2.6, 1.3, 1.3, 1.5])
    with sc1:
        script_topic = st.text_input("Topic", placeholder="Enter Video Topic (e.g., How to save mobile battery)...", label_visibility="collapsed")
    with sc2:
        script_len = st.selectbox("Length", ["60 Sec Shorts/Reel", "3-5 Min Video", "8-10 Min Deep Dive"], label_visibility="collapsed")
    with sc3:
        script_tone = st.selectbox("Tone", ["Engaging & Energetic", "Storytelling & Emotional", "Funny & Relatable", "Educational & Clear"], label_visibility="collapsed")
    with sc4:
        run_sc = st.button(ui["script_btn"], key="btn_sc", type="primary", use_container_width=True)

    sc_status = st.empty()
    if run_sc:
        if not st.session_state.verified_email and not st.session_state.pro_unlocked:
            st.warning(f"🔐 {ui['login_prompt']}")
        elif not script_topic.strip():
            st.warning("Enter your video topic first.")
        elif not st.session_state.pro_unlocked and free_left <= 0:
            st.error(f"🔒 {ui['free_over']}")
        else:
            lang_rule = build_language_directive(report_lang)
            sc_prompt = f"""
You are a top viral video scriptwriter for Indian & Global creators.
Write a complete, word-for-word, ready-to-shoot video script for:
- Topic: {script_topic.strip()}
- Format / Duration: {script_len}
- Style / Tone: {script_tone}
- Target Audience: {audience_scope}

{lang_rule}
(If Auto-Detect was selected, detect the language of the Topic text above; if unclear, write in English).

INCLUDE THESE 5 CLEAR SECTIONS (ALL HEADINGS & DIALOGUES IN THE TARGET/DETECTED LANGUAGE'S NATIVE SCRIPT):
### 🎣 1. 3 Scroll-Stopping 5-Second Opening Hooks
### 🎬 2. Complete Word-for-Word Spoken Script (With Visual & B-Roll Cues)
### 📣 3. High-Converting Subscribe / Comment Call-To-Action (CTA)
### 🖼️ 4. 3 High-CTR Thumbnail Text & Visual Ideas
### 🔍 5. Viral Title, Caption & 15 Hashtags
"""
            sc_status.markdown(f'<div class="loading-pill">⚡ {ui["generating"]} ⏳</div>', unsafe_allow_html=True)
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
                log_usage_to_sheet(st.session_state.verified_email, "ScriptGen", script_topic.strip()[:80])
                st.rerun()
            except Exception as e:
                sc_status.empty()
                st.error(str(e))

    if st.session_state.script_report:
        st.success(f"✅ {ui['ready']}")
        st.markdown(st.session_state.script_report)
        st.download_button(
            f"📥 {ui['download']}",
            data=st.session_state.script_report,
            file_name="TrendSutra_Viral_Script.txt",
            mime="text/plain",
            use_container_width=True
        )

with tab_th:
    th1, th2, th3 = st.columns([2.5, 2.2, 1.6])
    with th1:
        thumb_file = st.file_uploader("Upload Thumbnail", type=["jpg", "jpeg", "png", "webp"], label_visibility="collapsed")
    with th2:
        thumb_title = st.text_input("Video Title", placeholder="Optional: Enter Video Title for CTR check...", label_visibility="collapsed")
    with th3:
        run_th = st.button(ui["thumb_btn"], key="btn_th", type="primary", use_container_width=True)

    th_status = st.empty()
    if thumb_file is not None:
        st.image(thumb_file, width=340)

    if run_th:
        if not st.session_state.verified_email and not st.session_state.pro_unlocked:
            st.warning(f"🔐 {ui['login_prompt']}")
        elif thumb_file is None:
            st.warning("Please upload a thumbnail image (JPG/PNG) first.")
        elif not st.session_state.pro_unlocked and free_left <= 0:
            st.error(f"🔒 {ui['free_over']}")
        else:
            pil_img = Image.open(thumb_file)
            lang_rule = build_language_directive(report_lang)
            th_prompt = f"""
You are a YouTube & Social Media Thumbnail CTR Optimization Expert.
Carefully inspect the uploaded thumbnail image and evaluate its click-through potential.
Optional Video Title Context: {thumb_title.strip() or "Not provided"}
Target Audience: {audience_scope}

{lang_rule}
(If Auto-Detect was selected, detect the language of the text inside the thumbnail or title; if none, write in English).

PROVIDE THIS 5-PART THUMBNAIL AUDIT (ALL HEADINGS & ANALYSIS IN THE TARGET/DETECTED LANGUAGE'S NATIVE SCRIPT):
### ⭐ 1. Overall CTR Score (Out of 10) & First-Impression Verdict
### 📱 2. Mobile Screen Readability & Text Clarity Check
### 🎨 3. Color Contrast, Face/Subject Focus & Emotion Analysis
### 🛠️ 4. Top 3 Exact Fixes to Double Your Clicks (CTR)
### ✍️ 5. 3 Better Short Thumbnail Text Alternatives (Max 3–4 Words Each)
"""
            th_status.markdown(f'<div class="loading-pill">⚡ {ui["generating"]} ⏳</div>', unsafe_allow_html=True)
            report_box = st.empty()
            full_text = ""
            try:
                for piece in generate_report_stream([th_prompt, pil_img]):
                    full_text += piece
                    report_box.markdown(full_text)
                th_status.empty()
                st.session_state.thumb_report = full_text
                if not st.session_state.pro_unlocked:
                    increment_free_used(st.session_state.verified_email)
                log_usage_to_sheet(st.session_state.verified_email, "ThumbnailCheck", thumb_title.strip()[:80] or "Image")
                st.rerun()
            except Exception as e:
                th_status.empty()
                st.error(str(e))

    if st.session_state.thumb_report:
        st.success(f"✅ {ui['ready']}")
        st.markdown(st.session_state.thumb_report)
        st.download_button(
            f"📥 {ui['download']}",
            data=st.session_state.thumb_report,
            file_name="TrendSutra_Thumbnail_Audit.txt",
            mime="text/plain",
            use_container_width=True
        )
