import streamlit as st
from google import genai
from google.genai import types
from googleapiclient.discovery import build
import re
import time
import requests
import random
import smtplib
import base64
from email.mime.text import MIMEText

# --- 1. PAGE CONFIG ---
page_icon_val = "logo.png" if os.path.exists("logo.png") else "🇮🇳"
st.set_page_config(page_title="TrendSutra AI - 1 AI • 1 India", page_icon=page_icon_val, layout="wide")

# --- 2. LOAD SECRETS ---
GEMINI_KEY_1 = str(st.secrets.get("GEMINI_API_KEY", "")).strip()
GEMINI_KEY_2 = str(st.secrets.get("GEMINI_API_KEY_2", "")).strip()
GEMINI_KEY_3 = str(st.secrets.get("GEMINI_API_KEY_3", "")).strip()
GEMINI_KEY_4 = str(st.secrets.get("GEMINI_API_KEY_4", "")).strip()

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
    "Kashmiri (कॉशुर / كٲشُر)",
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
        "free_left": "{n}/3 Free Reports Left",
        "free_over": "0/3 Free Reports Left",
        "gen_btn": "Generate Growth Report 🔍",
        "fetching": "🔄 Fetching video details & comments... ⏳",
        "generating": "⚡ Generating your report... ⏳",
        "done": "✅ Growth Audit Report is ready!",
        "download": "📥 Download Complete Growth Report (.txt)",
        "otp_send_btn": "Send OTP 📩",
        "otp_sent": "✅ 6-digit OTP sent to {email}! Check Inbox/Spam.",
        "otp_verify_btn": "Verify OTP ✅",
        "otp_wrong": "❌ Incorrect OTP! Please try again.",
        "lock_msg": "🔒 Your 3 Free Reports are finished! Please upgrade to a Pro Plan on the left."
    },
    "Telugu": {
        "free_left": "{n}/3 ఉచిత రిపోర్ట్‌లు మిగిలాయి",
        "free_over": "0/3 ఉచిత రిపోర్ట్‌లు మిగిలాయి",
        "gen_btn": "గ్రోత్ రిపోర్ట్ తయారు చేయండి 🔍",
        "fetching": "🔄 వీడియో వివరాలు & కామెంట్లు సేకరిస్తోంది... ⏳",
        "generating": "⚡ రిపోర్ట్ తయారవుతోంది... ⏳",
        "done": "✅ గ్రోత్ ఆడిట్ రిపోర్ట్ సిద్ధమైంది!",
        "download": "📥 పూర్తి రిపోర్ట్ డౌన్‌లోడ్ చేయండి (.txt)",
        "otp_send_btn": "OTP పంపండి 📩",
        "otp_sent": "✅ {email} కి 6-అంకెల OTP పంపబడింది! ఇన్‌బాక్స్ చెక్ చేయండి.",
        "otp_verify_btn": "OTP నిర్ధారించండి ✅",
        "otp_wrong": "❌ తప్పు OTP! దయచేసి మళ్ళీ చెక్ చేయండి.",
        "lock_msg": "🔒 మీ 3 ఉచిత రిపోర్ట్‌లు పూర్తయ్యాయి! అన్‌లిమిటెడ్ రిపోర్ట్‌ల కోసం ఎడమ వైపు Pro Plan తీసుకోండి."
    },
    "Hindi": {
        "free_left": "{n}/3 मुफ्त रिपोर्ट बाकी हैं",
        "free_over": "0/3 मुफ्त रिपोर्ट बाकी हैं",
        "gen_btn": "ग्रोथ रिपोर्ट बनाएं 🔍",
        "fetching": "🔄 वीडियो विवरण और कमेंट्स लिए जा रहे हैं... ⏳",
        "generating": "⚡ आपकी रिपोर्ट तैयार हो रही है... ⏳",
        "done": "✅ ग्रोथ ऑडिट रिपोर्ट तैयार है!",
        "download": "📥 पूरी रिपोर्ट डाउनलोड करें (.txt)",
        "otp_send_btn": "OTP भेजें 📩",
        "otp_sent": "✅ {email} पर 6-अंकों का OTP भेजा गया है! इनबॉक्स देखें।",
        "otp_verify_btn": "OTP सत्यापित करें ✅",
        "otp_wrong": "❌ गलत OTP! कृपया पुनः प्रयास करें।",
        "lock_msg": "🔒 आपकी 3 मुफ्त रिपोर्ट पूरी हो गई हैं! अनलिमिटेड रिपोर्ट के लिए बाईं ओर Pro Plan लें।"
    },
    "Tamil": {
        "free_left": "{n}/3 இலவச அறிக்கைகள் உள்ளன",
        "free_over": "0/3 இலவச அறிக்கைகள் உள்ளன",
        "gen_btn": "வளர்ச்சி அறிக்கையை உருவாக்கவும் 🔍",
        "fetching": "🔄 வீடியோ விவரங்கள் சேகரிக்கப்படுகின்றன... ⏳",
        "generating": "⚡ உங்கள் அறிக்கை தயாராகிறது... ⏳",
        "done": "✅ வளர்ச்சி ஆய்வு அறிக்கை தயாராக உள்ளது!",
        "download": "📥 முழு அறிக்கையைப் பதிவிறக்கவும் (.txt)",
        "otp_send_btn": "OTP அனுப்பு 📩",
        "otp_sent": "✅ {email} க்கு 6-இலக்க OTP அனுப்பப்பட்டுள்ளது!",
        "otp_verify_btn": "OTP சரிபார்க்கவும் ✅",
        "otp_wrong": "❌ தவறான OTP! மீண்டும் முயற்சிக்கவும்.",
        "lock_msg": "🔒 உங்கள் 3 இலவச அறிக்கைகள் முடிந்துவிட்டன! இடதுபுறம் உள்ள Pro Plan பெறவும்."
    },
    "Kannada": {
        "free_left": "{n}/3 ಉಚಿತ ವರದಿಗಳು ಬಾಕಿ ಇವೆ",
        "free_over": "0/3 ಉಚಿತ ವರದಿಗಳು ಬಾಕಿ ಇವೆ",
        "gen_btn": "ಗ್ರೋತ್ ವರದಿ ರಚಿಸಿ 🔍",
        "fetching": "🔄 ವೀಡಿಯೊ ವಿವರಗಳನ್ನು ಸಂಗ್ರಹಿಸಲಾಗುತ್ತಿದೆ... ⏳",
        "generating": "⚡ ನಿಮ್ಮ ವರದಿ ಸಿದ್ಧವಾಗುತ್ತಿದೆ... ⏳",
        "done": "✅ ಗ್ರೋತ್ ಆಡಿಟ್ ವರದಿ ಸಿದ್ಧವಾಗಿದೆ!",
        "download": "📥 ಪೂರ್ಣ ವರದಿ ಡೌನ್‌ಲೋಡ್ ಮಾಡಿ (.txt)",
        "otp_send_btn": "OTP ಕಳುಹಿಸಿ 📩",
        "otp_sent": "✅ {email} ಗೆ 6-ಅಂಕಿಯ OTP ಕಳುಹಿಸಲಾಗಿದೆ!",
        "otp_verify_btn": "OTP ದೃಢೀಕರಿಸಿ ✅",
        "otp_wrong": "❌ ತಪ್ಪಾದ OTP! ದಯವಿಟ್ಟು ಮತ್ತೆ ಪ್ರಯತ್ನಿಸಿ.",
        "lock_msg": "🔒 ನಿಮ್ಮ 3 ಉಚಿತ ವರದಿಗಳು ಮುಗಿದಿವೆ! ಎಡಭಾಗದಲ್ಲಿ Pro Plan ಆಯ್ಕೆಮಾಡಿ."
    },
    "Malayalam": {
        "free_left": "{n}/3 സൗജന്യ റിപ്പോർട്ടുകൾ ബാക്കിയുണ്ട്",
        "free_over": "0/3 സൗജന്യ റിപ്പോർട്ടുകൾ ബാക്കിയുണ്ട്",
        "gen_btn": "ഗ്രോത്ത് റിപ്പോർട്ട് നിർമ്മിക്കുക 🔍",
        "fetching": "🔄 വീഡിയോ വിവരങ്ങൾ ശേഖരിക്കുന്നു... ⏳",
        "generating": "⚡ റിപ്പോർട്ട് തയ്യാറാകുന്നു... ⏳",
        "done": "✅ ഗ്രോത്ത് ഓഡിറ്റ് റിപ്പോർട്ട് തയ്യാറായി!",
        "download": "📥 പൂർണ്ണ റിപ്പോർട്ട് ഡൗൺലോഡ് ചെയ്യുക (.txt)",
        "otp_send_btn": "OTP അയയ്ക്കുക 📩",
        "otp_sent": "✅ {email} എന്നതിലേക്ക് 6-അക്ക OTP അയച്ചിരിക്കുന്നു!",
        "otp_verify_btn": "OTP പരിശോധിക്കുക ✅",
        "otp_wrong": "❌ തെറ്റായ OTP! വീണ്ടും ശ്രമിക്കുക.",
        "lock_msg": "🔒 നിങ്ങളുടെ 3 സൗജന്യ റിപ്പോർട്ടുകൾ കഴിഞ്ഞു! ഇടതുവശത്ത് Pro Plan തിരഞ്ഞെടുക്കുക."
    },
    "Marathi": {
        "free_left": "{n}/3 मोफत रिपोर्ट शिल्लक आहेत",
        "free_over": "0/3 मोफत रिपोर्ट शिल्लक आहेत",
        "gen_btn": "ग्रोथ रिपोर्ट तयार करा 🔍",
        "fetching": "🔄 व्हिडिओ माहिती गोळा केली जात आहे... ⏳",
        "generating": "⚡ तुमचा रिपोर्ट तयार होत आहे... ⏳",
        "done": "✅ ग्रोथ ऑडिट रिपोर्ट तयार आहे!",
        "download": "📥 संपूर्ण रिपोर्ट डाउनलोड करा (.txt)",
        "otp_send_btn": "OTP पाठवा 📩",
        "otp_sent": "✅ {email} वर 6-अंकी OTP पाठवला आहे!",
        "otp_verify_btn": "OTP सत्यापित करा ✅",
        "otp_wrong": "❌ चुकीचा OTP! कृपया पुन्हा प्रयत्न करा.",
        "lock_msg": "🔒 तुमचे 3 मोफत रिपोर्ट संपले आहेत! डावीकडे Pro Plan निवडा."
    },
    "Bengali": {
        "free_left": "{n}/3 ফ্রি রিপোর্ট বাকি আছে",
        "free_over": "0/3 ফ্রি রিপোর্ট বাকি আছে",
        "gen_btn": "গ্রোথ রিপোর্ট তৈরি করুন 🔍",
        "fetching": "🔄 ভিডিওর তথ্য সংগ্রহ করা হচ্ছে... ⏳",
        "generating": "⚡ আপনার রিপোর্ট তৈরি হচ্ছে... ⏳",
        "done": "✅ গ্রোথ অডিট রিপোর্ট তৈরি হয়েছে!",
        "download": "📥 সম্পূর্ণ রিপোর্ট ডাউনলোড করুন (.txt)",
        "otp_send_btn": "OTP পাঠান 📩",
        "otp_sent": "✅ {email}-এ ৬-সংখ্যার OTP পাঠানো হয়েছে!",
        "otp_verify_btn": "OTP যাচাই করুন ✅",
        "otp_wrong": "❌ ভুল OTP! আবার চেষ্টা করুন।",
        "lock_msg": "🔒 আপনার ৩টি ফ্রি রিপোর্ট শেষ হয়েছে! বাম দিকে Pro Plan বেছে নিন।"
    },
    "Gujarati": {
        "free_left": "{n}/3 મફત રિપોર્ટ બાકી છે",
        "free_over": "0/3 મફત રિપોર્ટ બાકી છે",
        "gen_btn": "ગ્રોથ રિપોર્ટ બનાવો 🔍",
        "fetching": "🔄 વિડિઓ વિગતો લેવામાં આવી રહી છે... ⏳",
        "generating": "⚡ તમારો રિપોર્ટ તૈયાર થઈ રહ્યો છે... ⏳",
        "done": "✅ ગ્રોથ ઓડિટ રિપોર્ટ તૈયાર છે!",
        "download": "📥 સંપૂર્ણ રિપોર્ટ ડાઉનલોડ કરો (.txt)",
        "otp_send_btn": "OTP મોકલો 📩",
        "otp_sent": "✅ {email} પર 6-અંકનો OTP મોકલવામાં આવ્યો છે!",
        "otp_verify_btn": "OTP ચકાસો ✅",
        "otp_wrong": "❌ ખોટો OTP! ફરી પ્રયાસ કરો.",
        "lock_msg": "🔒 તમારા 3 મફત રિપોર્ટ પૂરા થઈ ગયા છે! ડાબી બાજુ Pro Plan લો."
    },
    "Punjabi": {
        "free_left": "{n}/3 ਮੁਫ਼ਤ ਰਿਪੋਰਟਾਂ ਬਾਕੀ ਹਨ",
        "free_over": "0/3 ਮੁਫ਼ਤ ਰਿਪੋਰਟਾਂ ਬਾਕੀ ਹਨ",
        "gen_btn": "ਗਰੋਥ ਰਿਪੋਰਟ ਬਣਾਓ 🔍",
        "fetching": "🔄 ਵੀਡੀਓ ਵੇਰਵੇ ਲਏ ਜਾ ਰਹੇ ਹਨ... ⏳",
        "generating": "⚡ ਤੁਹਾਡੀ ਰਿਪੋਰਟ ਤਿਆਰ ਹੋ ਰਹੀ ਹੈ... ⏳",
        "done": "✅ ਗਰੋਥ ਆਡਿਟ ਰਿਪੋਰਟ ਤਿਆਰ ਹੈ!",
        "download": "📥 ਪੂਰੀ ਰਿਪੋਰਟ ਡਾਊਨਲੋਡ ਕਰੋ (.txt)",
        "otp_send_btn": "OTP ਭੇਜੋ 📩",
        "otp_sent": "✅ {email} ਤੇ 6-ਅੰਕਾਂ ਦਾ OTP ਭੇਜਿਆ ਗਿਆ ਹੈ!",
        "otp_verify_btn": "OTP ਪੁਸ਼ਟੀ ਕਰੋ ✅",
        "otp_wrong": "❌ ਗਲਤ OTP! ਦੁਬਾਰਾ ਕੋਸ਼ਿਸ਼ ਕਰੋ।",
        "lock_msg": "🔒 ਤੁਹਾਡੀਆਂ 3 ਮੁਫ਼ਤ ਰਿਪੋਰਟਾਂ ਖਤਮ ਹੋ ਗਈਆਂ ਹਨ! ਖੱਬੇ ਪਾਸੇ Pro Plan ਲਓ।"
    },
    "Odia": {
        "free_left": "{n}/3 ମାଗଣା ରିପୋର୍ଟ ବାକି ଅଛି",
        "free_over": "0/3 ମାଗଣା ରିପୋର୍ଟ ବାକି ଅଛି",
        "gen_btn": "ଗ୍ରୋଥ୍ ରିପୋର୍ଟ ତିଆରି କରନ୍ତୁ 🔍",
        "fetching": "🔄 ଭିଡିଓ ତଥ୍ୟ ସଂଗ୍ରହ ହେଉଛି... ⏳",
        "generating": "⚡ ଆପଣଙ୍କ ରିପୋର୍ଟ ପ୍ରସ୍ତୁତ ହେଉଛି... ⏳",
        "done": "✅ ଗ୍ରୋଥ୍ ଅଡିଟ୍ ରିପୋର୍ଟ ପ୍ରସ୍ତୁତ ଅଛି!",
        "download": "📥 ସମ୍ପୂର୍ଣ୍ଣ ରିପୋର୍ଟ ଡାଉନଲୋଡ୍ କରନ୍ତୁ (.txt)",
        "otp_send_btn": "OTP ପଠାନ୍ତୁ 📩",
        "otp_sent": "✅ {email} କୁ 6-ଅଙ୍କ ବିଶିଷ୍ଟ OTP ପଠାଯାଇଛି!",
        "otp_verify_btn": "OTP ଯାଞ୍ଚ କରନ୍ତୁ ✅",
        "otp_wrong": "❌ ଭୁଲ OTP! ପୁଣି ଚେଷ୍ଟା କରନ୍ତୁ।",
        "lock_msg": "🔒 ଆପଣଙ୍କର 3ଟି ମାଗଣା ରିପୋର୍ଟ ଶେଷ ହୋଇଛି! ବାମ ପାର୍ଶ୍ୱରେ Pro Plan ନିଅନ୍ତୁ।"
    },
    "Assamese": {
        "free_left": "{n}/3 বিনামূলীয়া ৰিপৰ্ট বাকী আছে",
        "free_over": "0/3 বিনামূলীয়া ৰিপৰ্ট বাকী আছে",
        "gen_btn": "গ্ৰোথ ৰিপৰ্ট তৈয়াৰ কৰক 🔍",
        "fetching": "🔄 ভিডিঅ'ৰ তথ্য সংগ্ৰহ কৰা হৈছে... ⏳",
        "generating": "⚡ আপোনাৰ ৰিপৰ্ট প্ৰস্তুত হৈ আছে... ⏳",
        "done": "✅ গ্ৰোথ অডিট ৰিপৰ্ট প্ৰস্তুত!",
        "download": "📥 সম্পূৰ্ণ ৰিপৰ্ট ডাউনলোড কৰক (.txt)",
        "otp_send_btn": "OTP পঠাওক 📩",
        "otp_sent": "✅ {email} লৈ ৬-সংখ্যাৰ OTP পঠোৱা হৈছে!",
        "otp_verify_btn": "OTP নিশ্চিত কৰক ✅",
        "otp_wrong": "❌ ভুল OTP! পুনৰ চেষ্টা কৰক।",
        "lock_msg": "🔒 আপোনাৰ ৩টা বিনামূলীয়া ৰিপৰ্ট শেষ হৈছে! বাওঁফালে Pro Plan লওক।"
    },
    "Urdu": {
        "free_left": "{n}/3 مفت رپورٹس باقی ہیں",
        "free_over": "0/3 مفت رپورٹس باقی ہیں",
        "gen_btn": "گروتھ رپورٹ بنائیں 🔍",
        "fetching": "🔄 ویڈیو کی تفصیلات حاصل کی جا رہی ہیں... ⏳",
        "generating": "⚡ آپ کی رپورٹ تیار ہو رہی ہے... ⏳",
        "done": "✅ گروتھ آڈٹ رپورٹ تیار ہے!",
        "download": "📥 مکمل رپورٹ ڈاؤن لوڈ کریں (.txt)",
        "otp_send_btn": "OTP بھیجیں 📩",
        "otp_sent": "✅ {email} پر 6 ہندسوں کا OTP بھیج دیا گیا ہے!",
        "otp_verify_btn": "OTP کی تصدیق کریں ✅",
        "otp_wrong": "❌ غلط OTP! براہ کرم دوبارہ کوشش کریں۔",
        "lock_msg": "🔒 آپ کی 3 مفت رپورٹس مکمل ہو گئی ہیں! بائیں جانب Pro Plan منتخب کریں۔"
    },
    "Bhojpuri": {
        "free_left": "{n}/3 मुफ्त रिपोर्ट बाचल बा",
        "free_over": "0/3 मुफ्त रिपोर्ट बाचल बा",
        "gen_btn": "ग्रोथ रिपोर्ट बनाईं 🔍",
        "fetching": "🔄 वीडियो के जानकारी लिहल जा रहल बा... ⏳",
        "generating": "⚡ रउआ रिपोर्ट तैयार हो रहल बा... ⏳",
        "done": "✅ ग्रोथ ऑडिट रिपोर्ट तैयार बा!",
        "download": "📥 पूरा रिपोर्ट डाउनलोड करीं (.txt)",
        "otp_send_btn": "OTP भेजीं 📩",
        "otp_sent": "✅ {email} पर 6-अंक के OTP भेज दिहल गइल बा!",
        "otp_verify_btn": "OTP सत्यापित करीं ✅",
        "otp_wrong": "❌ गलत OTP! फिर से कोशिश करीं।",
        "lock_msg": "🔒 रउआ 3 मुफ्त रिपोर्ट पूरा हो गइल बा! बायां तरफ Pro Plan लीं।"
    }
}

def resolve_ui_lang(selected_option, detected_lang=""):
    target = detected_lang.strip() if (selected_option.startswith("Auto-Detect") and detected_lang) else selected_option
    if not target or target.startswith("Auto-Detect"):
        return "English"
    low = target.lower()
    if "tenglish" in low or "telugu" in low:
        return "Telugu"
    if "hinglish" in low or "hindi" in low:
        return "Hindi"
    if "tamil" in low:
        return "Tamil"
    if "kannada" in low:
        return "Kannada"
    if "malayalam" in low:
        return "Malayalam"
    if "marathi" in low:
        return "Marathi"
    if "bengali" in low:
        return "Bengali"
    if "gujarati" in low:
        return "Gujarati"
    if "punjabi" in low:
        return "Punjabi"
    if "odia" in low:
        return "Odia"
    if "assamese" in low:
        return "Assamese"
    if "urdu" in low:
        return "Urdu"
    if "bhojpuri" in low:
        return "Bhojpuri"
    return "English"

def t(key, ui_lang, **kwargs):
    lang_dict = UI_TEXT.get(ui_lang, UI_TEXT["English"])
    template = lang_dict.get(key, UI_TEXT["English"][key])
    return template.format(**kwargs) if kwargs else template

# --- 3. COMPACT SINGLE-SCREEN DARK STYLING ---
st.markdown("""
<style>
    [data-testid="stToolbarActions"], [data-testid="stDecoration"], #MainMenu, footer, .viewerBadge_container__1QSob {
        display: none !important;
        visibility: hidden !important;
    }
    [data-testid="stSidebarCollapsedControl"] {
        display: flex !important;
        visibility: visible !important;
    }
    .block-container {
        padding-top: 0.75rem !important;
        padding-bottom: 0.8rem !important;
        max-width: 1220px !important;
    }
    section[data-testid="stSidebar"] > div:first-child {
        padding-top: 0.45rem !important;
        padding-bottom: 0.3rem !important;
    }
    section[data-testid="stSidebar"] .stMarkdown p {
        margin-bottom: 0.22rem !important;
        font-size: 0.84rem !important;
        line-height: 1.25 !important;
    }
    section[data-testid="stSidebar"] hr {
        margin: 0.42rem 0 !important;
    }
    section[data-testid="stSidebar"] .stAlert {
        padding: 0.38rem 0.65rem !important;
        margin-bottom: 0.3rem !important;
    }
    section[data-testid="stSidebar"] .stTextInput {
        margin-bottom: -0.45rem !important;
    }
    section[data-testid="stSidebar"] .stRadio > div {
        gap: 0.45rem !important;
    }
    .center-header-card {
        background: linear-gradient(135deg, #0b1324 0%, #162238 100%);
        padding: 13px 20px;
        border-radius: 12px;
        border-bottom: 3px solid #10b981;
        margin-bottom: 10px;
        text-align: center;
    }
    .center-title-row {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 11px;
    }
    .center-title-text {
        margin: 0;
        font-size: 1.65rem;
        font-weight: 800;
        color: #ffffff;
        letter-spacing: 0.3px;
    }
    .india-badge {
        background: rgba(16, 185, 129, 0.16);
        border: 1px solid #10b981;
        color: #6ee7b7;
        font-size: 0.72rem;
        font-weight: 700;
        padding: 2px 9px;
        border-radius: 999px;
    }
    .center-sub-text {
        margin: 4px 0 0 0;
        color: #cbd5e1;
        font-size: 0.88rem;
    }
    .user-strip {
        background: #111827;
        border: 1px solid #374151;
        padding: 7px 14px;
        border-radius: 9px;
        color: #e5e7eb;
        font-size: 0.86rem;
    }
    .loading-pill {
        background: rgba(16, 185, 129, 0.14);
        border: 1px solid #10b981;
        color: #6ee7b7;
        padding: 7px 14px;
        border-radius: 8px;
        font-weight: 600;
        font-size: 0.86rem;
        display: inline-block;
    }
</style>
""", unsafe_allow_html=True)

# --- 4. SESSION STATE ---
for k, v in {
    "verified_email": "",
    "otp_code": "",
    "otp_target": "",
    "pro_unlocked": False,
    "pro_label": "",
    "yt_report": "",
    "yt_vid": "",
    "yt_stats": None,
    "detected_lang": "",
    "ig_report": "",
    "tt_report": ""
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# --- 5. CHECK GOOGLE OAUTH LOGIN ---
try:
    if hasattr(st, "user") and getattr(st.user, "is_logged_in", False):
        g_email = getattr(st.user, "email", "")
        if g_email:
            st.session_state.verified_email = g_email.strip().lower()
except Exception:
    pass

# --- 6. GOOGLE SHEET HELPERS (NO-CACHE LIVE SYNC) ---
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
        return False
    for _ in range(2):
        try:
            r = requests.get(
                SHEET_API,
                params={"device": user_id, "inc": "1", "_ts": int(time.time() * 1000)},
                timeout=10,
                allow_redirects=True
            )
            if r.status_code == 200 and r.text.strip().isdigit():
                return True
        except Exception:
            time.sleep(0.4)
    return False

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

# --- 7. AUTO-UNLOCK IF RAZORPAY REDIRECTED WITH PAYMENT ID ---
try:
    qp_pid = st.query_params.get("razorpay_payment_id", "")
    if qp_pid and not st.session_state.pro_unlocked:
        st_res = verify_payment_id(qp_pid, plan="1m")
        if st_res == "VALID":
            st.session_state.pro_unlocked = True
            st.session_state.pro_label = "PRO ACTIVE"
            st.query_params.clear()
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

# --- 8. YOUTUBE DATA FETCHER ---
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
            "description": snip.get("description", "")[:1200],
            "tags": snip.get("tags", [])[:20],
            "default_audio_lang": snip.get("defaultAudioLanguage", "") or snip.get("defaultLanguage", ""),
            "views": int(stats.get("viewCount", 0)),
            "likes": int(stats.get("likeCount", 0)),
            "comment_count": int(stats.get("commentCount", 0)),
            "comments": comments
        }
    except Exception:
        return None

# --- 9. 4-KEY SMART FAILOVER (FREE KEYS 4 -> 3 -> 2 FIRST, THEN PAID KEY 1) ---
def get_ordered_api_keys():
    keys = []
    for k in [GEMINI_KEY_4, GEMINI_KEY_3, GEMINI_KEY_2, GEMINI_KEY_1]:
        if k and k not in keys:
            keys.append(k)
    return keys

def clean_mentor_word(text):
    return text.replace("మెంటర్", "సలహాదారు").replace("స్ట్రాటజిస్ట్", "సలహాదారు")

def generate_report_stream(prompt):
    api_keys = get_ordered_api_keys()
    if not api_keys:
        raise RuntimeError("API Key missing in Streamlit Secrets.")
    candidate_models = ["gemini-2.5-flash", "gemini-2.5-flash-lite"]
    last_err = ""
    for api_k in api_keys:
        try:
            client = genai.Client(api_key=api_k)
        except Exception as e:
            last_err = str(e)
            continue
        for model_name in candidate_models:
            try:
                response = client.models.generate_content_stream(
                    model=model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(temperature=0.82, max_output_tokens=8192)
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
                continue
    raise RuntimeError(f"AI Server busy. Please try again in 5 seconds. ({last_err})")

def build_language_instruction(selected_lang):
    if selected_lang.startswith("Auto-Detect"):
        return (
            "1. FIRST LINE MANDATORY: Detect the primary spoken/written language of this video from its title, audio language tag, description, and comments. "
            "Output the very first line strictly in English as: `🌐 Detected Video Language: <Language Name>` (for example: `🌐 Detected Video Language: Hindi` or `🌐 Detected Video Language: Tamil` or `🌐 Detected Video Language: Urdu` or `🌐 Detected Video Language: Telugu`).\n"
            "2. IMMEDIATELY AFTER THAT FIRST LINE, write the ENTIRE 6-section report—including ALL 6 section headings AND all body text—strictly in that SAME detected language using its NATIVE SCRIPT (e.g., Devanagari for Hindi/Marathi/Bhojpuri, Telugu script for Telugu, Tamil script for Tamil, Perso-Arabic Nastaliq script for Urdu, Kannada script for Kannada, Malayalam script for Malayalam, Bengali script for Bengali, Gujarati script for Gujarati, Gurmukhi for Punjabi, Odia script for Odia). Do NOT write Hindi or Urdu in Roman/English letters!"
        )
    return (
        f"Write the ENTIRE 6-section report—including ALL 6 section headings AND all body text—strictly in **{selected_lang}** using its NATIVE SCRIPT "
        f"(e.g., Devanagari for Hindi/Marathi/Bhojpuri, Telugu script for Telugu, Tamil script for Tamil, Perso-Arabic script for Urdu, etc.). Do NOT leave section headings in English!"
    )

# --- 10. SIDEBAR ---
with st.sidebar:
    st.markdown("### ⚙️ Settings")
    report_lang = st.selectbox(
        "🔍 Type to Search Language (A–Z):",
        LANGUAGE_OPTIONS,
        index=0
    )
    ui_lang = resolve_ui_lang(report_lang, st.session_state.detected_lang)
    audience_scope = st.radio("Target Audience:", ["Regional", "Global", "Both"], horizontal=True, label_visibility="collapsed")

    st.divider()
    st.markdown("### 💎 Pro Plans")

    free_used = get_free_used_count(st.session_state.verified_email) if st.session_state.verified_email else 0
    free_left = max(0, 3 - free_used)

    if st.session_state.pro_unlocked:
        st.success(f"✅ {st.session_state.pro_label}")
    elif st.session_state.verified_email:
        if free_left > 0:
            st.info(f"🎁 {t('free_left', ui_lang, n=free_left)}")
        else:
            st.error(f"🔒 {t('free_over', ui_lang)}")
    else:
        st.info("🎁 Login for 3 Free Reports")

    st.markdown(f"• **1 Month:** ₹100 👉 [Pay ₹100]({RAZORPAY_1M})")
    st.markdown(f"• **12 Months:** ₹1,000 👉 [Pay ₹1,000]({RAZORPAY_12M})")

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
                st.error("⏰ Plan Expired!")
            elif status == "ALREADY_USED":
                st.error("❌ Used on 3 devices!")
            else:
                st.error("❌ Invalid ID.")

    st.divider()
    st.caption("📩 support@aiengtel.com | © TrendSutra AI")

# --- 11. CENTER-ALIGNED HEADER WITH LOGO ---
logo_html = ""
if os.path.exists("logo.png"):
    with open("logo.png", "rb") as f:
        b64_logo = base64.b64encode(f.read()).decode()
    logo_html = f'<img src="data:image/png;base64,{b64_logo}" style="width:42px; height:42px; border-radius:9px; object-fit:cover;" />'

st.markdown(f"""
<div class="center-header-card">
    <div class="center-title-row">
        {logo_html}
        <span class="center-title-text">TrendSutra AI</span>
        <span class="india-badge">🇮🇳 1 AI • 1 India</span>
    </div>
    <p class="center-sub-text">A to Z Growth Analyzer in All 22 Indian Languages + Bhojpuri for YouTube, Instagram & TikTok</p>
</div>
""", unsafe_allow_html=True)

# --- 12. COMPACT SINGLE-ROW LOGIN BAR ---
if not st.session_state.verified_email and not st.session_state.pro_unlocked:
    lc1, lc2, lc3, lc4 = st.columns([2.2, 0.4, 2.5, 1.4])
    with lc1:
        if st.button("🔵 Continue with Gmail", type="primary", use_container_width=True):
            try:
                st.login("google")
            except Exception as e:
                st.error(f"Google Login error: {e}")
    with lc2:
        st.markdown("<div style='text-align:center; padding-top:7px; color:#94a3b8; font-weight:700;'>OR</div>", unsafe_allow_html=True)
    with lc3:
        email_in = st.text_input("Mail ID", placeholder="Login with Mail ID", label_visibility="collapsed")
    with lc4:
        if st.button(t("otp_send_btn", ui_lang), use_container_width=True):
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
                    st.success(t("otp_sent", ui_lang, email=clean_em))
                else:
                    st.error(f"Error: {err_msg}")

    if st.session_state.otp_target:
        oc1, oc2 = st.columns([3, 1.5])
        with oc1:
            otp_in = st.text_input("OTP", placeholder=f"Enter 6-digit OTP sent to {st.session_state.otp_target}", max_chars=6, label_visibility="collapsed")
        with oc2:
            if st.button(t("otp_verify_btn", ui_lang), type="primary", use_container_width=True):
                if otp_in.strip() == st.session_state.otp_code:
                    st.session_state.verified_email = st.session_state.otp_target
                    st.session_state.otp_code = ""
                    st.rerun()
                else:
                    st.error(t("otp_wrong", ui_lang))
    st.stop()
else:
    u1, u2 = st.columns([4.5, 1])
    with u1:
        badge_txt = st.session_state.pro_label if st.session_state.pro_unlocked else f"🎁 {t('free_left', ui_lang, n=free_left)}"
        st.markdown(f'<div class="user-strip">👤 Logged in as <b>{st.session_state.verified_email or "Pro Member"}</b> &nbsp;|&nbsp; {badge_txt}</div>', unsafe_allow_html=True)
    with u2:
        if st.button("Logout 🚪", use_container_width=True):
            for k in ["verified_email", "pro_unlocked", "yt_report", "ig_report", "tt_report", "detected_lang"]:
                st.session_state[k] = "" if isinstance(st.session_state[k], str) else False
            try:
                if hasattr(st, "logout"):
                    st.logout()
            except Exception:
                pass
            st.rerun()

# --- 13. MAIN ANALYZER TABS ---
tab_yt, tab_ig, tab_tt = st.tabs(["📺 YouTube Analyzer", "📸 Instagram Reels Analyzer", "🎵 TikTok Analyzer"])

with tab_yt:
    yc1, yc2 = st.columns([3.6, 1.4])
    with yc1:
        yt_url = st.text_input("YouTube URL", placeholder="Paste YouTube Video or Shorts Link...", label_visibility="collapsed")
    with yc2:
        run_yt = st.button(t("gen_btn", ui_lang), key="btn_yt", type="primary", use_container_width=True)
    yt_status_slot = st.empty()

    if run_yt:
        if not yt_url.strip():
            st.warning("Please paste a YouTube link.")
        elif not st.session_state.pro_unlocked and free_left <= 0:
            st.error(t("lock_msg", ui_lang))
        else:
            vid_id = extract_youtube_id(yt_url.strip())
            if not vid_id:
                st.error("❌ Please enter a valid YouTube link.")
            else:
                yt_status_slot.markdown(f'<div class="loading-pill">{t("fetching", ui_lang)}</div>', unsafe_allow_html=True)
                data = fetch_youtube_details(vid_id)
                if not data:
                    yt_status_slot.empty()
                    st.error("❌ Could not fetch video details. Make sure the video is Public.")
                else:
                    st.session_state.yt_stats = data
                    st.session_state.yt_vid = vid_id
                    comments_block = "\n".join(data["comments"][:15]) if data["comments"] else "No public comments available."
                    lang_rule = build_language_instruction(report_lang)
                    prompt = f"""
You are a warm, encouraging, expert human social media growth advisor ("సలహాదారు").
Write a comprehensive, deeply detailed, easy-to-understand growth audit report (1,100 to 1,500 words) for a **{audience_scope}** audience.
Use simple everyday spoken words (never use complex bookish words, and NEVER use the word 'మెంటర్'—use 'సలహాదారు' if needed in Telugu).

LANGUAGE & SCRIPT RULE (CRITICAL):
{lang_rule}

VIDEO DATA:
- Channel: {data['channel']}
- Title: {data['title']}
- Audio Language Tag: {data['default_audio_lang']}
- Views: {data['views']:,} | Likes: {data['likes']:,} | Comments: {data['comment_count']:,}
- Description: {data['description']}
- Tags: {', '.join(data['tags'])}
- Real Audience Comments:
{comments_block}

STRICTLY FOLLOW THIS 6-SECTION STRUCTURE (Translate every heading below into the target language's native script!):
### 🎬 1. [Translate: Video Story Recap & Creator Appreciation]
- First, warmly retell the core story/message of this video based on its title, description, and comments so the creator feels you truly watched and understood their hard work.
- Then genuinely praise the creator's effort, topic choice, presentation, and strengths.

### 💬 2. [Translate: Real Audience Comments & Replies]
- Pick 4 to 5 real viewer comments from the list above, translate them naturally into the target language's native script, quote them with the viewer's name, explain what the audience loves or asks for, and give 3 ready-to-copy reply templates.

### 🔥 3. [Translate: 3 Next Viral Video Ideas + 5-Sec Hooks]
- Give 3 fresh, high-potential follow-up video ideas tailored to this channel. For each idea, write an exact word-for-word **5-second opening Hook** and a **Thumbnail visual idea**.

### 🎯 4. [Translate: Copy-Paste SEO Makeover (Titles, Description & 15 Tags)]
- Provide 3 clickable high-CTR title options, a strong 3-line SEO description hook, and 15 searchable comma-separated tags.

### 💰 5. [Translate: Monetization & Brand Earning Blueprint]
- Explain 3 practical ways this specific channel can earn money (AdSense, Affiliate links, Brand sponsorships) with realistic examples.

### 📅 6. [Translate: Step-by-Step 30-Day Action Plan]
- Give a clear Week 1 to Week 4 checklist of simple daily/weekly actions to double views and subscribers.
"""
                    yt_status_slot.markdown(f'<div class="loading-pill">{t("generating", ui_lang)}</div>', unsafe_allow_html=True)
                    report_box = st.empty()
                    full_text = ""
                    detected_updated = False
                    try:
                        for piece in generate_report_stream(prompt):
                            full_text += piece
                            if not detected_updated and "\n" in full_text:
                                first_line = full_text.split("\n", 1)[0].strip()
                                if "Detected Video Language:" in first_line:
                                    det = first_line.split("Detected Video Language:", 1)[-1].strip()
                                    st.session_state.detected_lang = det
                                    active_ui = resolve_ui_lang(report_lang, det)
                                    yt_status_slot.markdown(f'<div class="loading-pill">{t("generating", active_ui)}</div>', unsafe_allow_html=True)
                                    detected_updated = True
                            report_box.markdown(full_text)
                        yt_status_slot.empty()
                        st.session_state.yt_report = full_text
                        if not st.session_state.pro_unlocked:
                            increment_free_used(st.session_state.verified_email)
                        log_usage_to_sheet(st.session_state.verified_email or "PRO", "YouTube", yt_url.strip())
                        st.rerun()
                    except Exception as e:
                        yt_status_slot.empty()
                        st.error(str(e))

    if st.session_state.yt_report:
        if st.session_state.yt_stats:
            d = st.session_state.yt_stats
            m1, m2, m3 = st.columns(3)
            m1.metric("👀 Views", f"{d['views']:,}")
            m2.metric("👍 Likes", f"{d['likes']:,}")
            m3.metric("💬 Comments", f"{d['comment_count']:,}")
        st.markdown(st.session_state.yt_report)
        st.success(t("done", ui_lang))
        st.download_button(
            t("download", ui_lang),
            data=st.session_state.yt_report,
            file_name=f"TrendSutra_YouTube_Report_{st.session_state.yt_vid or 'Video'}.txt",
            mime="text/plain",
            use_container_width=True
        )

with tab_ig:
    ic1, ic2 = st.columns([3.6, 1.4])
    with ic1:
        ig_url = st.text_input("Instagram URL", placeholder="Paste Instagram Reel Link...", label_visibility="collapsed")
    with ic2:
        run_ig = st.button(t("gen_btn", ui_lang), key="btn_ig", type="primary", use_container_width=True)
    ig_status_slot = st.empty()

    if run_ig:
        if not ig_url.strip():
            st.warning("Please paste an Instagram Reel link.")
        elif not st.session_state.pro_unlocked and free_left <= 0:
            st.error(t("lock_msg", ui_lang))
        else:
            ig_status_slot.markdown(f'<div class="loading-pill">{t("generating", ui_lang)}</div>', unsafe_allow_html=True)
            lang_rule = build_language_instruction(report_lang)
            ig_prompt = f"""
You are a warm, encouraging human Instagram Reels growth advisor ("సలహాదారు").
Write a detailed 6-section Instagram Reels growth audit (1,000+ words) for a **{audience_scope}** audience using simple spoken words.
{lang_rule}
Reel Link: {ig_url.strip()}
Include 6 translated headings in native script:
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
        st.markdown(st.session_state.ig_report)
        st.success(t("done", ui_lang))
        st.download_button(
            t("download", ui_lang),
            data=st.session_state.ig_report,
            file_name="TrendSutra_Instagram_Report.txt",
            mime="text/plain",
            use_container_width=True
        )

with tab_tt:
    tc1, tc2 = st.columns([3.6, 1.4])
    with tc1:
        tt_url = st.text_input("TikTok URL", placeholder="Paste TikTok Video Link...", label_visibility="collapsed")
    with tc2:
        run_tt = st.button(t("gen_btn", ui_lang), key="btn_tt", type="primary", use_container_width=True)
    tt_status_slot = st.empty()

    if run_tt:
        if not tt_url.strip():
            st.warning("Please paste a TikTok link.")
        elif not st.session_state.pro_unlocked and free_left <= 0:
            st.error(t("lock_msg", ui_lang))
        else:
            tt_status_slot.markdown(f'<div class="loading-pill">{t("generating", ui_lang)}</div>', unsafe_allow_html=True)
            lang_rule = build_language_instruction(report_lang)
            tt_prompt = f"""
You are a warm, encouraging human TikTok growth advisor ("సలహాదారు").
Write a detailed 6-section TikTok growth audit (1,000+ words) for a **{audience_scope}** audience using simple spoken words.
{lang_rule}
TikTok Link: {tt_url.strip()}
Include 6 translated headings in native script:
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
        st.markdown(st.session_state.tt_report)
        st.success(t("done", ui_lang))
        st.download_button(
            t("download", ui_lang),
            data=st.session_state.tt_report,
            file_name="TrendSutra_TikTok_Report.txt",
            mime="text/plain",
            use_container_width=True
        )
