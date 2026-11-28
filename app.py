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
page_icon_val = "logo.png" if os.path.exists("logo.png") else "🇮🇳"
st.set_page_config(page_title="TrendSutra AI - 1 AI • 1 India", page_icon=page_icon_val, layout="wide")

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

# --- 3. ALL 22 SCHEDULED INDIAN LANGUAGES + BHOJPURI (A-Z) ---
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

# --- 4. DYNAMIC MULTI-LANGUAGE UI STRINGS ---
UI_TEXT = {
    "English": {
        "gen_btn": "Generate Growth Report 🔍",
        "free_left": "{n}/3 Free Reports Left",
        "free_done": "0/3 Free Reports Left (Upgrade to Pro)",
        "fetching": "🔄 Fetching video details & comments... ⏳",
        "generating": "⚡ Generating growth report... ⏳",
        "done": "✅ Growth Audit Report is ready!",
        "dl_btn": "📥 Download Complete Growth Report (.txt)",
        "send_otp": "Send OTP 📩",
        "otp_sent": "✅ 6-digit OTP sent to {em}! Check Inbox / Spam.",
        "verify_otp": "Verify OTP ✅",
        "login_prompt": "Login with Gmail or Email ID to get 3 Free Growth Reports:",
        "sec1": "### 🎬 1. Video Story Recap & Creator Appreciation",
        "sec2": "### 💬 2. Real Audience Comments Translated & Reply Templates",
        "sec3": "### 🔥 3. Next 3 Viral Video Ideas & 5-Second Hooks",
        "sec4": "### 🎯 4. Copy-Paste SEO Makeover (Titles, Description & 15 Tags)",
        "sec5": "### 💰 5. Monetization & Brand Earning Blueprint",
        "sec6": "### 📅 6. Step-by-Step 30-Day Action Plan",
        "script_rule": "Write the entire report in pure English."
    },
    "Telugu": {
        "gen_btn": "గ్రోత్ రిపోర్ట్ తయారు చేయండి 🔍",
        "free_left": "{n}/3 ఉచిత రిపోర్ట్‌లు మిగిలాయి",
        "free_done": "0/3 ఉచిత రిపోర్ట్‌లు మిగిలాయి (Pro తీసుకోండి)",
        "fetching": "🔄 వీడియో వివరాలు & కామెంట్లు సేకరిస్తోంది... ⏳",
        "generating": "⚡ రిపోర్ట్ తయారవుతోంది... ⏳",
        "done": "✅ గ్రోత్ ఆడిట్ రిపోర్ట్ సిద్ధమైంది!",
        "dl_btn": "📥 పూర్తి రిపోర్ట్ డౌన్‌లోడ్ చేయండి (.txt)",
        "send_otp": "OTP పంపండి 📩",
        "otp_sent": "✅ {em} కి 6-అంకెల OTP పంపబడింది! ఇన్‌బాక్స్ / Spam చెక్ చేయండి.",
        "verify_otp": "OTP నిర్ధారించండి ✅",
        "login_prompt": "3 ఉచిత గ్రోత్ రిపోర్ట్‌ల కోసం Gmail లేదా Email ID తో లాగిన్ అవ్వండి:",
        "sec1": "### 🎬 1. మీ వీడియో కథ & క్రియేటర్ అభినందన",
        "sec2": "### 💬 2. ఆడియన్స్ ఏం అంటున్నారు? (కామెంట్ల అనువాదం & రిప్లైలు)",
        "sec3": "### 🔥 3. తదుపరి తీయాల్సిన 3 వైరల్ వీడియో ఐడియాలు & 5-సెకన్ల Hooks",
        "sec4": "### 🎯 4. కాపీ-పేస్ట్ SEO మేకోవర్ (టైటిల్స్, డిస్క్రిప్షన్ & 15 ట్యాగ్స్)",
        "sec5": "### 💰 5. ఆదాయ మార్గాలు (Monetization & Brand Earning Blueprint)",
        "sec6": "### 📅 6. 30 రోజుల కార్యాచరణ ప్రణాళిక",
        "script_rule": "Write the ENTIRE report strictly in natural Telugu script (తెలుగు లిపి). Do NOT write Telugu in English letters."
    },
    "Hindi": {
        "gen_btn": "ग्रोथ रिपोर्ट बनाएं 🔍",
        "free_left": "{n}/3 मुफ्त रिपोर्ट बाकी हैं",
        "free_done": "0/3 मुफ्त रिपोर्ट बाकी हैं (Pro लें)",
        "fetching": "🔄 वीडियो की जानकारी और कमेंट्स लिए जा रहे हैं... ⏳",
        "generating": "⚡ ग्रोथ रिपोर्ट तैयार हो रही है... ⏳",
        "done": "✅ ग्रोथ ऑडिट रिपोर्ट तैयार है!",
        "dl_btn": "📥 पूरी रिपोर्ट डाउनलोड करें (.txt)",
        "send_otp": "OTP भेजें 📩",
        "otp_sent": "✅ {em} पर 6-अंकों का OTP भेजा गया है! Inbox / Spam देखें।",
        "verify_otp": "OTP सत्यापित करें ✅",
        "login_prompt": "3 मुफ्त ग्रोथ रिपोर्ट पाने के लिए Gmail या Email ID से लॉगिन करें:",
        "sec1": "### 🎬 1. वीडियो की कहानी और क्रिएटर की सराहना",
        "sec2": "### 💬 2. दर्शक क्या कह रहे हैं? (कमेंट्स का अनुवाद और रिप्लाई)",
        "sec3": "### 🔥 3. अगले 3 वायरल वीडियो आइडिया और 5-सेकंड हुक्स",
        "sec4": "### 🎯 4. कॉपी-पेस्ट SEO मेकओवर (टाइटल, डिस्क्रिप्शन और 15 टैग्स)",
        "sec5": "### 💰 5. कमाई के तरीके (Monetization और ब्रांड स्पॉन्सरशिप)",
        "sec6": "### 📅 6. 30 दिनों की कार्य योजना (Action Plan)",
        "script_rule": "Write the ENTIRE report strictly in Devanagari Hindi script (हिन्दी देवनागरी लिपि). Do NOT write Hinglish."
    },
    "Tamil": {
        "gen_btn": "வளர்ச்சி அறிக்கையை உருவாக்கு 🔍",
        "free_left": "{n}/3 இலவச அறிக்கைகள் உள்ளன",
        "free_done": "0/3 இலவச அறிக்கைகள் உள்ளன (Pro பெறவும்)",
        "fetching": "🔄 வீடியோ விவரங்கள் & கருத்துகள் சேகரிக்கப்படுகின்றன... ⏳",
        "generating": "⚡ வளர்ச்சி அறிக்கை தயாராகிறது... ⏳",
        "done": "✅ வளர்ச்சி அறிக்கை தயாராகிவிட்டது!",
        "dl_btn": "📥 முழு அறிக்கையை பதிவிறக்கவும் (.txt)",
        "send_otp": "OTP அனுப்பு 📩",
        "otp_sent": "✅ {em} க்கு 6-இலக்க OTP அனுப்பப்பட்டது! Inbox / Spam பார்க்கவும்.",
        "verify_otp": "OTP சரிபார் ✅",
        "login_prompt": "3 இலவச அறிக்கைகளைப் பெற Gmail அல்லது Email ID மூலம் உள்நுழையவும்:",
        "sec1": "### 🎬 1. வீடியோ கதை சுருக்கம் & படைப்பாளர் பாராட்டு",
        "sec2": "### 💬 2. பார்வையாளர்கள் என்ன சொல்கிறார்கள்? (கருத்துகள் & பதில்கள்)",
        "sec3": "### 🔥 3. அடுத்த 3 வைரல் வீடியோ யோசனைகள் & 5-வினாடி Hooks",
        "sec4": "### 🎯 4. காப்பி-பேஸ்ட் SEO மேம்பாடு (தலைப்புகள், விளக்கம் & 15 குறிச்சொற்கள்)",
        "sec5": "### 💰 5. வருமான வழிகள் (Monetization & பிராண்ட் வருவாய்)",
        "sec6": "### 📅 6. 30 நாள் செயல் திட்டம்",
        "script_rule": "Write the ENTIRE report strictly in Tamil script (தமிழ் எழுத்துக்கள்)."
    },
    "Kannada": {
        "gen_btn": "ಗ್ರೋತ್ ರಿಪೋರ್ಟ್ ರಚಿಸಿ 🔍",
        "free_left": "{n}/3 ಉಚಿತ ವರದಿಗಳು ಉಳಿದಿವೆ",
        "free_done": "0/3 ಉಚಿತ ವರದಿಗಳು ಉಳಿದಿವೆ (Pro ಪಡೆಯಿರಿ)",
        "fetching": "🔄 ವೀಡಿಯೊ ವಿವರಗಳು ಮತ್ತು ಕಾಮೆಂಟ್‌ಗಳನ್ನು ಸಂಗ್ರಹಿಸಲಾಗುತ್ತಿದೆ... ⏳",
        "generating": "⚡ ವರದಿ ಸಿದ್ಧವಾಗುತ್ತಿದೆ... ⏳",
        "done": "✅ ಗ್ರೋತ್ ಆಡಿಟ್ ವರದಿ ಸಿದ್ಧವಾಗಿದೆ!",
        "dl_btn": "📥 ಪೂರ್ಣ ವರದಿಯನ್ನು ಡೌನ್‌ಲೋಡ್ ಮಾಡಿ (.txt)",
        "send_otp": "OTP ಕಳುಹಿಸಿ 📩",
        "otp_sent": "✅ {em} ಗೆ 6-ಅಂಕಿಯ OTP ಕಳುಹಿಸಲಾಗಿದೆ! Inbox / Spam ಪರಿಶೀಲಿಸಿ.",
        "verify_otp": "OTP ಪರಿಶೀಲಿಸಿ ✅",
        "login_prompt": "3 ಉಚಿತ ವರದಿಗಳನ್ನು ಪಡೆಯಲು Gmail ಅಥವಾ Email ID ಮೂಲಕ ಲಾಗಿನ್ ಆಗಿ:",
        "sec1": "### 🎬 1. ವೀಡಿಯೊ ಕಥೆ ಮತ್ತು ಕ್ರಿಯೇಟರ್ ಪ್ರಶಂಸೆ",
        "sec2": "### 💬 2. ವೀಕ್ಷಕರು ಏನು ಹೇಳುತ್ತಿದ್ದಾರೆ? (ಕಾಮೆಂಟ್ ಅನುವಾದ ಮತ್ತು ಉತ್ತರಗಳು)",
        "sec3": "### 🔥 3. ಮುಂದಿನ 3 ವೈರಲ್ ವೀಡಿಯೊ ಐಡಿಯಾಗಳು ಮತ್ತು 5-ಸೆಕೆಂಡ್ Hooks",
        "sec4": "### 🎯 4. ಕಾಪಿ-ಪೇಸ್ಟ್ SEO ಮೇಕೋವರ್ (ಶೀರ್ಷಿಕೆಗಳು, ವಿವರಣೆ ಮತ್ತು 15 ಟ್ಯಾಗ್‌ಗಳು)",
        "sec5": "### 💰 5. ಆದಾಯದ ಮಾರ್ಗಗಳು (Monetization ಮತ್ತು ಬ್ರಾಂಡ್ ಗಳಿಕೆ)",
        "sec6": "### 📅 6. 30 ದಿನಗಳ ಕಾರ್ಯ ಯೋಜನೆ",
        "script_rule": "Write the ENTIRE report strictly in Kannada script (ಕನ್ನಡ ಲಿಪಿ)."
    },
    "Malayalam": {
        "gen_btn": "ഗ്രോത്ത് റിപ്പോർട്ട് തയ്യാറാക്കുക 🔍",
        "free_left": "{n}/3 സൗജന്യ റിപ്പോർട്ടുകൾ ബാക്കിയുണ്ട്",
        "free_done": "0/3 സൗജന്യ റിപ്പോർട്ടുകൾ ബാക്കിയുണ്ട് (Pro എടുക്കുക)",
        "fetching": "🔄 വീഡിയോ വിവരങ്ങളും കമന്റുകളും ശേഖരിക്കുന്നു... ⏳",
        "generating": "⚡ റിപ്പോർട്ട് തയ്യാറാകുന്നു... ⏳",
        "done": "✅ ഗ്രോത്ത് ഓഡിറ്റ് റിപ്പോർട്ട് തയ്യാറായി!",
        "dl_btn": "📥 പൂർണ്ണ റിപ്പോർട്ട് ഡൗൺലോഡ് ചെയ്യുക (.txt)",
        "send_otp": "OTP അയക്കുക 📩",
        "otp_sent": "✅ {em} ലേക്ക് 6-അക്ക OTP അയച്ചിട്ടുണ്ട്! Inbox / Spam പരിശോധിക്കുക.",
        "verify_otp": "OTP സ്ഥിരീകരിക്കുക ✅",
        "login_prompt": "3 സൗജന്യ റിപ്പോർട്ടുകൾ ലഭിക്കാൻ Gmail അല്ലെങ്കിൽ Email ID ഉപയോഗിച്ച് ലോഗിൻ ചെയ്യുക:",
        "sec1": "### 🎬 1. വീഡിയോ കഥാ സംഗ്രഹവും ക്രിയേറ്റർ അഭിനന്ദനവും",
        "sec2": "### 💬 2. പ്രേക്ഷകർ എന്ത് പറയുന്നു? (കമന്റ് വിവർത്തനവും മറുപടികളും)",
        "sec3": "### 🔥 3. അടുത്ത 3 വൈറൽ വീഡിയോ ആശയങ്ങളും 5-സെക്കൻഡ് Hooks-ഉം",
        "sec4": "### 🎯 4. കോപ്പി-പേസ്റ്റ് SEO മേക്കോവർ (ടൈറ്റിലുകൾ, വിവരണം & 15 ടാഗുകൾ)",
        "sec5": "### 💰 5. വരുമാന മാർഗ്ഗങ്ങൾ (Monetization & ബ്രാൻഡ് വരുമാനം)",
        "sec6": "### 📅 6. 30 ദിവസത്തെ കർമ്മ പദ്ധതി",
        "script_rule": "Write the ENTIRE report strictly in Malayalam script (മലയാളം ലിപി)."
    },
    "Marathi": {
        "gen_btn": "ग्रोथ रिपोर्ट तयार करा 🔍",
        "free_left": "{n}/3 मोफत रिपोर्ट शिल्लक आहेत",
        "free_done": "0/3 मोफत रिपोर्ट शिल्लक आहेत (Pro घ्या)",
        "fetching": "🔄 व्हिडिओ माहिती आणि कमेंट्स गोळा करत आहे... ⏳",
        "generating": "⚡ रिपोर्ट तयार होत आहे... ⏳",
        "done": "✅ ग्रोथ ऑडिट रिपोर्ट तयार आहे!",
        "dl_btn": "📥 संपूर्ण रिपोर्ट डाउनलोड करा (.txt)",
        "send_otp": "OTP पाठवा 📩",
        "otp_sent": "✅ {em} वर 6-अंकी OTP पाठवला आहे! Inbox / Spam तपासा.",
        "verify_otp": "OTP तपासा ✅",
        "login_prompt": "3 मोफत रिपोर्ट मिळवण्यासाठी Gmail किंवा Email ID ने लॉगिन करा:",
        "sec1": "### 🎬 1. व्हिडिओची कथा आणि क्रिएटरचे कौतुक",
        "sec2": "### 💬 2. प्रेक्षक काय म्हणत आहेत? (कमेंट्सचे भाषांतर आणि उत्तरे)",
        "sec3": "### 🔥 3. पुढील 3 व्हायरल व्हिडिओ कल्पना आणि 5-सेकंद Hooks",
        "sec4": "### 🎯 4. कॉपी-पेस्ट SEO मेकओव्हर (शीर्षके, वर्णन आणि 15 टॅग्स)",
        "sec5": "### 💰 5. कमाईचे मार्ग (Monetization आणि ब्रँड उत्पन्न)",
        "sec6": "### 📅 6. 30 दिवसांची कृती योजना",
        "script_rule": "Write the ENTIRE report strictly in Marathi Devanagari script (मराठी लिपी)."
    },
    "Bengali": {
        "gen_btn": "গ্রোথ রিপোর্ট তৈরি করুন 🔍",
        "free_left": "{n}/3 ফ্রি রিপোর্ট বাকি আছে",
        "free_done": "0/3 ফ্রি রিপোর্ট বাকি আছে (Pro নিন)",
        "fetching": "🔄 ভিডিওর তথ্য ও কমেন্ট সংগ্রহ করা হচ্ছে... ⏳",
        "generating": "⚡ রিপোর্ট তৈরি হচ্ছে... ⏳",
        "done": "✅ গ্রোথ অডিট রিপোর্ট তৈরি হয়ে গেছে!",
        "dl_btn": "📥 সম্পূর্ণ রিপোর্ট ডাউনলোড করুন (.txt)",
        "send_otp": "OTP পাঠান 📩",
        "otp_sent": "✅ {em} এ ৬-সংখ্যার OTP পাঠানো হয়েছে! Inbox / Spam দেখুন।",
        "verify_otp": "OTP যাচাই করুন ✅",
        "login_prompt": "৩টি ফ্রি রিপোর্ট পেতে Gmail বা Email ID দিয়ে লগইন করুন:",
        "sec1": "### 🎬 1. ভিডিওর গল্প ও ক্রিয়েটরের প্রশংসা",
        "sec2": "### 💬 2. দর্শকরা কী বলছেন? (কমেন্ট অনুবাদ ও উত্তর)",
        "sec3": "### 🔥 3. পরবর্তী ৩টি ভাইরাল ভিডিও আইডিয়া ও ৫-সেকেন্ড Hooks",
        "sec4": "### 🎯 4. কপি-পেস্ট SEO মেকওভার (টাইটেল, ডেসক্রিপশন ও ১৫টি ট্যাগ)",
        "sec5": "### 💰 5. আয়ের উপায় (Monetization ও ব্র্যান্ড আয়)",
        "sec6": "### 📅 6. ৩০ দিনের অ্যাকশন প্ল্যান",
        "script_rule": "Write the ENTIRE report strictly in Bengali script (বাংলা লিপি)."
    },
    "Gujarati": {
        "gen_btn": "ગ્રોથ રિપોર્ટ બનાવો 🔍",
        "free_left": "{n}/3 મફત રિપોર્ટ બાકી છે",
        "free_done": "0/3 મફત રિપોર્ટ બાકી છે (Pro લો)",
        "fetching": "🔄 વીડિયોની માહિતી અને કોમેન્ટ્સ લેવામાં આવી રહી છે... ⏳",
        "generating": "⚡ રિપોર્ટ તૈયાર થઈ રહ્યો છે... ⏳",
        "done": "✅ ગ્રોથ ઓડિટ રિપોર્ટ તૈયાર છે!",
        "dl_btn": "📥 સંપૂર્ણ રિપોર્ટ ડાઉનલોડ કરો (.txt)",
        "send_otp": "OTP મોકલો 📩",
        "otp_sent": "✅ {em} પર 6-અંકનો OTP મોકલવામાં આવ્યો છે! Inbox / Spam જુઓ.",
        "verify_otp": "OTP ચકાસો ✅",
        "login_prompt": "3 મફત રિપોર્ટ મેળવવા માટે Gmail અથવા Email ID થી લોગિન કરો:",
        "sec1": "### 🎬 1. વીડિયોની વાર્તા અને ક્રિએટરની પ્રશંસા",
        "sec2": "### 💬 2. દર્શકો શું કહી રહ્યા છે? (કોમેન્ટ અનુવાદ અને જવાબો)",
        "sec3": "### 🔥 3. આગામી 3 વાયરલ વીડિયો આઇડિયા અને 5-સેકન્ડ Hooks",
        "sec4": "### 🎯 4. કોપી-પેસ્ટ SEO મેકઓવર (ટાઇટલ, વર્ણન અને 15 ટેગ્સ)",
        "sec5": "### 💰 5. કમાણીના રસ્તાઓ (Monetization અને બ્રાન્ડ આવક)",
        "sec6": "### 📅 6. 30 દિવસનો એક્શન પ્લાન",
        "script_rule": "Write the ENTIRE report strictly in Gujarati script (ગુજરાતી લિપિ)."
    },
    "Punjabi": {
        "gen_btn": "ਗਰੋਥ ਰਿਪੋਰਟ ਬਣਾਓ 🔍",
        "free_left": "{n}/3 ਮੁਫ਼ਤ ਰਿਪੋਰਟਾਂ ਬਾਕੀ ਹਨ",
        "free_done": "0/3 ਮੁਫ਼ਤ ਰਿਪੋਰਟਾਂ ਬਾਕੀ ਹਨ (Pro ਲਵੋ)",
        "fetching": "🔄 ਵੀਡੀਓ ਦੀ ਜਾਣਕਾਰੀ ਅਤੇ ਕਮੈਂਟ ਲਏ ਜਾ ਰਹੇ ਹਨ... ⏳",
        "generating": "⚡ ਰਿਪੋਰਟ ਤਿਆਰ ਹੋ ਰਹੀ ਹੈ... ⏳",
        "done": "✅ ਗਰੋਥ ਆਡਿਟ ਰਿਪੋਰਟ ਤਿਆਰ ਹੈ!",
        "dl_btn": "📥 ਪੂਰੀ ਰਿਪੋਰਟ ਡਾਊਨਲੋਡ ਕਰੋ (.txt)",
        "send_otp": "OTP ਭੇਜੋ 📩",
        "otp_sent": "✅ {em} ਤੇ 6-ਅੰਕਾਂ ਦਾ OTP ਭੇਜਿਆ ਗਿਆ ਹੈ! Inbox / Spam ਦੇਖੋ।",
        "verify_otp": "OTP ਪੁਸ਼ਟੀ ਕਰੋ ✅",
        "login_prompt": "3 ਮੁਫ਼ਤ ਰਿਪੋਰਟਾਂ ਲੈਣ ਲਈ Gmail ਜਾਂ Email ID ਨਾਲ ਲੌਗਇਨ ਕਰੋ:",
        "sec1": "### 🎬 1. ਵੀਡੀਓ ਦੀ ਕਹਾਣੀ ਅਤੇ ਕ੍ਰਿਏਟਰ ਦੀ ਸ਼ਲਾਘਾ",
        "sec2": "### 💬 2. ਦਰਸ਼ਕ ਕੀ ਕਹਿ ਰਹੇ ਹਨ? (ਕਮੈਂਟ ਅਨੁਵਾਦ ਅਤੇ ਜਵਾਬ)",
        "sec3": "### 🔥 3. ਅਗਲੇ 3 ਵਾਇਰਲ ਵੀਡੀਓ ਆਈਡੀਆ ਅਤੇ 5-ਸਕਿੰਟ Hooks",
        "sec4": "### 🎯 4. ਕਾਪੀ-ਪੇਸਟ SEO ਮੇਕਓਵਰ (ਟਾਈਟਲ, ਵੇਰਵਾ ਅਤੇ 15 ਟੈਗ)",
        "sec5": "### 💰 5. ਕਮਾਈ ਦੇ ਤਰੀਕੇ (Monetization ਅਤੇ ਬ੍ਰਾਂਡ ਆਮਦਨ)",
        "sec6": "### 📅 6. 30 ਦਿਨਾਂ ਦੀ ਕਾਰਜ ਯੋਜਨਾ",
        "script_rule": "Write the ENTIRE report strictly in Gurmukhi Punjabi script (ਪੰਜਾਬੀ ਗੁਰਮੁਖੀ ਲਿਪੀ)."
    },
    "Odia": {
        "gen_btn": "ଗ୍ରୋଥ୍ ରିପୋର୍ଟ ତିଆରି କରନ୍ତୁ 🔍",
        "free_left": "{n}/3 ମାଗଣା ରିପୋର୍ଟ ବାକି ଅଛି",
        "free_done": "0/3 ମାଗଣା ରିପୋର୍ଟ ବାକି ଅଛି (Pro ନିଅନ୍ତୁ)",
        "fetching": "🔄 ଭିଡିଓ ତଥ୍ୟ ଏବଂ କମେଣ୍ଟ ସଂଗ୍ରହ କରାଯାଉଛି... ⏳",
        "generating": "⚡ ରିପୋର୍ଟ ପ୍ରସ୍ତୁତ ହେଉଛି... ⏳",
        "done": "✅ ଗ୍ରୋଥ୍ ଅଡିଟ୍ ରିପୋର୍ଟ ପ୍ରସ୍ତୁତ ହୋଇଯାଇଛି!",
        "dl_btn": "📥 ସମ୍ପୂର୍ଣ୍ଣ ରିପୋର୍ଟ ଡାଉନଲୋଡ୍ କରନ୍ତୁ (.txt)",
        "send_otp": "OTP ପଠାନ୍ତୁ 📩",
        "otp_sent": "✅ {em} କୁ 6-ଅଙ୍କ ବିଶିଷ୍ଟ OTP ପଠାଯାଇଛି! Inbox / Spam ଯାଞ୍ଚ କରନ୍ତୁ।",
        "verify_otp": "OTP ଯାଞ୍ଚ କରନ୍ତୁ ✅",
        "login_prompt": "3ଟି ମାଗଣା ରିପୋର୍ଟ ପାଇବା ପାଇଁ Gmail କିମ୍ବା Email ID ରେ ଲଗଇନ୍ କରନ୍ତୁ:",
        "sec1": "### 🎬 1. ଭିଡିଓ କାହାଣୀ ଏବଂ କ୍ରିଏଟର ପ୍ରଶଂସା",
        "sec2": "### 💬 2. ଦର୍ଶକ କଣ କହୁଛନ୍ତି? (କମେଣ୍ଟ ଅନୁବାଦ ଏବଂ ଉତ୍ତର)",
        "sec3": "### 🔥 3. ପରବର୍ତ୍ତୀ 3ଟି ଭାଇରାଲ୍ ଭିଡିଓ ଆଇଡିଆ ଏବଂ 5-ସେକେଣ୍ଡ Hooks",
        "sec4": "### 🎯 4. କପି-ପେଷ୍ଟ SEO ମେକଓଭର (ଟାଇଟଲ୍, ବିବରଣୀ ଏବଂ 15 ଟ୍ୟାଗ୍)",
        "sec5": "### 💰 5. ରୋଜଗାରର ଉପାୟ (Monetization ଏବଂ ବ୍ରାଣ୍ଡ ଆୟ)",
        "sec6": "### 📅 6. 30 ଦିନର କାର୍ଯ୍ୟ ଯୋଜନା",
        "script_rule": "Write the ENTIRE report strictly in Odia script (ଓଡ଼ିଆ ଲିପି)."
    },
    "Assamese": {
        "gen_btn": "গ্ৰোথ ৰিপোৰ্ট বনাওক 🔍",
        "free_left": "{n}/3 বিনামূলীয়া ৰিপোৰ্ট বাকী আছে",
        "free_done": "0/3 বিনামূলীয়া ৰিপোৰ্ট বাকী আছে (Pro লওক)",
        "fetching": "🔄 ভিডিঅ'ৰ তথ্য আৰু কমেণ্ট সংগ্ৰহ কৰা হৈছে... ⏳",
        "generating": "⚡ ৰিপোৰ্ট প্ৰস্তুত হৈ আছে... ⏳",
        "done": "✅ গ্ৰোথ অডিট ৰিপোৰ্ট সাজু হৈছে!",
        "dl_btn": "📥 সম্পূৰ্ণ ৰিপোৰ্ট ডাউনলোড কৰক (.txt)",
        "send_otp": "OTP পঠিয়াওক 📩",
        "otp_sent": "✅ {em} লৈ ৬-অংকৰ OTP পঠিওৱা হৈছে! Inbox / Spam চাওক।",
        "verify_otp": "OTP নিশ্চিত কৰক ✅",
        "login_prompt": "৩টা বিনামূলীয়া ৰিপোৰ্ট পাবলৈ Gmail বা Email ID ৰে লগইন কৰক:",
        "sec1": "### 🎬 1. ভিডিঅ'ৰ কাহিনী আৰু ক্ৰিয়েটৰৰ প্ৰশংসা",
        "sec2": "### 💬 2. দৰ্শকে কি কৈছে? (কমেণ্ট অনুবাদ আৰু উত্তৰ)",
        "sec3": "### 🔥 3. পৰৱৰ্তী ৩টা ভাইৰেল ভিডিঅ' আইডিয়া আৰু ৫-ছেকেণ্ড Hooks",
        "sec4": "### 🎯 4. কপি-পেষ্ট SEO মেকঅভাৰ (শিৰোনাম, বিৱৰণ আৰু ১৫টা টেগ)",
        "sec5": "### 💰 5. উপাৰ্জনৰ উপায় (Monetization আৰু ব্ৰেণ্ড আয়)",
        "sec6": "### 📅 6. ৩০ দিনৰ কাৰ্য পৰিকল্পনা",
        "script_rule": "Write the ENTIRE report strictly in Assamese script (অসমীয়া লিপি)."
    },
    "Urdu": {
        "gen_btn": "گروتھ رپورٹ بنائیں 🔍",
        "free_left": "{n}/3 مفت رپورٹس باقی ہیں",
        "free_done": "0/3 مفت رپورٹس باقی ہیں (Pro لیں)",
        "fetching": "🔄 ویڈیو کی تفصیلات اور کمنٹس حاصل کیے جا رہے ہیں... ⏳",
        "generating": "⚡ گروتھ رپورٹ تیار ہو رہی ہے... ⏳",
        "done": "✅ گروتھ آڈٹ رپورٹ تیار ہے!",
        "dl_btn": "📥 مکمل رپورٹ ڈاؤن لوڈ کریں (.txt)",
        "send_otp": "OTP بھیجیں 📩",
        "otp_sent": "✅ {em} پر 6 ہندسوں کا OTP بھیج دیا گیا ہے! Inbox / Spam چیک کریں۔",
        "verify_otp": "OTP کی تصدیق کریں ✅",
        "login_prompt": "3 مفت رپورٹس حاصل کرنے کے لیے Gmail یا Email ID سے لاگ ان کریں:",
        "sec1": "### 🎬 1. ویڈیو کی کہانی اور کریئیٹر کی تعریف",
        "sec2": "### 💬 2. ناظرین کیا کہہ رہے ہیں؟ (کمنٹس کا ترجمہ اور جوابات)",
        "sec3": "### 🔥 3. اگلے 3 وائرل ویڈیو آئیڈیاز اور 5 سیکنڈ کے Hooks",
        "sec4": "### 🎯 4. کاپی پیسٹ SEO میک اوور (عنوانات، تفصیل اور 15 ٹیگز)",
        "sec5": "### 💰 5. کمائی کے طریقے (Monetization اور برانڈ آمدنی)",
        "sec6": "### 📅 6. 30 دن کا عملی منصوبہ",
        "script_rule": "Write the ENTIRE report strictly in Nastaliq/Arabic Urdu script (اردو رسم الخط). Do NOT write Roman Urdu in English letters."
    },
    "Bhojpuri": {
        "gen_btn": "ग्रोथ रिपोर्ट बनाईं 🔍",
        "free_left": "{n}/3 मुफ्त रिपोर्ट बाचल बा",
        "free_done": "0/3 मुफ्त रिपोर्ट बाचल बा (Pro लीं)",
        "fetching": "🔄 वीडियो के जानकारी आ कमेंट जुटावल जा रहल बा... ⏳",
        "generating": "⚡ ग्रोथ रिपोर्ट तैयार हो रहल बा... ⏳",
        "done": "✅ ग्रोथ ऑडिट रिपोर्ट तैयार बा!",
        "dl_btn": "📥 पूरा रिपोर्ट डाउनलोड करीं (.txt)",
        "send_otp": "OTP भेजीं 📩",
        "otp_sent": "✅ {em} पर 6-अंक के OTP भेज दिहल गइल बा! Inbox / Spam देखीं।",
        "verify_otp": "OTP सत्यापित करीं ✅",
        "login_prompt": "3 मुफ्त रिपोर्ट खातिर Gmail या Email ID से लॉगिन करीं:",
        "sec1": "### 🎬 1. वीडियो के कहानी आ क्रिएटर के तारीफ",
        "sec2": "### 💬 2. दर्शक लोग का कहत बा? (कमेंट के अनुवाद आ जवाब)",
        "sec3": "### 🔥 3. अगिला 3 वायरल वीडियो आइडिया आ 5-सेकंड Hooks",
        "sec4": "### 🎯 4. कॉपी-पेस्ट SEO मेकओवर (टाइटल, डिस्क्रिप्शन आ 15 टैग्स)",
        "sec5": "### 💰 5. कमाई के तरीका (Monetization आ ब्रांड स्पॉन्सरशिप)",
        "sec6": "### 📅 6. 30 दिन के कार्य योजना",
        "script_rule": "Write the ENTIRE report strictly in Devanagari Bhojpuri script (भोजपुरी देवनागरी लिपि)."
    }
}

def get_ui(lang_selection):
    if "Auto-Detect" in lang_selection:
        det = st.session_state.get("detected_ui_lang", "English")
        return UI_TEXT.get(det, UI_TEXT["English"])
    if "Tenglish" in lang_selection:
        d = dict(UI_TEXT["Telugu"])
        d["script_rule"] = "Write the report in natural Tenglish (Telugu words written in English script mixed with easy English)."
        return d
    if "Hinglish" in lang_selection:
        d = dict(UI_TEXT["Hindi"])
        d["script_rule"] = "Write the report in natural Hinglish (Hindi words written in English script mixed with easy English)."
        return d
    for k in UI_TEXT:
        if k.lower() in lang_selection.lower():
            return UI_TEXT[k]
    d = dict(UI_TEXT["English"])
    d["script_rule"] = f"Write the ENTIRE report including ALL section headings strictly in the native script of {lang_selection}."
    return d

# --- 5. CUSTOM STYLING ---
st.markdown("""
<style>
    [data-testid="stToolbarActions"], .stDeployButton, #MainMenu, footer { display: none !important; }
    [data-testid="stSidebarCollapsedControl"] { display: flex !important; visibility: visible !important; }
    .block-container { padding-top: 0.7rem !important; padding-bottom: 1rem !important; max-width: 1220px; }
    section[data-testid="stSidebar"] > div { padding-top: 0.6rem !important; }
    section[data-testid="stSidebar"] .stMarkdown p { margin-bottom: 0.25rem !important; font-size: 0.88rem !important; }
    section[data-testid="stSidebar"] hr { margin: 0.45rem 0 !important; }

    .center-header {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        padding: 14px 20px;
        border-radius: 14px;
        border-bottom: 3px solid #10b981;
        text-align: center;
        margin-bottom: 12px;
    }
    .brand-row {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        gap: 12px;
    }
    .brand-title {
        font-size: 1.85rem;
        font-weight: 800;
        color: #ffffff;
        margin: 0;
        letter-spacing: 0.4px;
    }
    .india-badge {
        background: rgba(16, 185, 129, 0.18);
        border: 1px solid #10b981;
        color: #6ee7b7;
        font-size: 0.78rem;
        padding: 3px 10px;
        border-radius: 20px;
        font-weight: 700;
    }
    .brand-sub {
        color: #cbd5e1;
        font-size: 0.92rem;
        margin: 4px 0 0 0;
    }
    .status-pill {
        background: rgba(16, 185, 129, 0.15);
        border: 1px solid #10b981;
        color: #6ee7b7;
        padding: 7px 14px;
        border-radius: 8px;
        font-weight: 600;
        display: inline-block;
        margin-top: 6px;
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
    ("ig_report", ""),
    ("tt_report", ""),
    ("detected_ui_lang", "English")
]:
    if key not in st.session_state:
        st.session_state[key] = default

# --- 7. CHECK GOOGLE OAUTH ---
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
        r = requests.get(SHEET_API, params={"device": user_id, "_ts": int(time.time())}, timeout=8, allow_redirects=True)
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
            r = requests.get(SHEET_API, params={"device": user_id, "inc": "1", "_ts": int(time.time())}, timeout=8, allow_redirects=True)
            if r.status_code == 200:
                return
        except Exception:
            time.sleep(0.5)

def log_usage_to_sheet(user_id, platform, url):
    if not SHEET_API:
        return
    try:
        requests.get(SHEET_API, params={"log": "1", "device": user_id, "platform": platform, "url": url, "_ts": int(time.time())}, timeout=6, allow_redirects=True)
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
        r = requests.get(SHEET_API, params={"pid": pid, "plan": plan, "_ts": int(time.time())}, timeout=10, allow_redirects=True)
        if r.status_code == 200:
            res = r.text.strip().upper()
            if res in ["VALID", "ALREADY_USED", "EXPIRED", "INVALID"]:
                return res
    except Exception:
        pass
    return "ERROR"

if "razorpay_payment_id" in st.query_params and not st.session_state.pro_unlocked:
    auto_pid = str(st.query_params["razorpay_payment_id"]).strip()
    if auto_pid.startswith("pay_"):
        st_res = verify_payment_id(auto_pid, plan="1m")
        if st_res == "VALID":
            st.session_state.pro_unlocked = True
            st.session_state.pro_label = "PRO UNLIMITED ACTIVE"

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
            "default_audio_lang": snip.get("defaultAudioLanguage", snip.get("defaultLanguage", "")),
            "description": snip.get("description", "")[:1200],
            "tags": snip.get("tags", [])[:20],
            "views": int(stats.get("viewCount", 0)),
            "likes": int(stats.get("likeCount", 0)),
            "comment_count": int(stats.get("commentCount", 0)),
            "comments": comments
        }
    except Exception:
        return None

def detect_ui_lang_from_video(data):
    code = str(data.get("default_audio_lang", "")).lower()
    code_map = {
        "te": "Telugu", "hi": "Hindi", "ta": "Tamil", "kn": "Kannada",
        "ml": "Malayalam", "mr": "Marathi", "bn": "Bengali", "gu": "Gujarati",
        "pa": "Punjabi", "or": "Odia", "as": "Assamese", "ur": "Urdu", "bho": "Bhojpuri"
    }
    for prefix, lname in code_map.items():
        if code.startswith(prefix):
            return lname
    blob = f"{data.get('title', '')} {data.get('description', '')} {' '.join(data.get('comments', [])[:8])}"
    for ch in blob:
        cp = ord(ch)
        if 0x0C00 <= cp <= 0x0C7F: return "Telugu"
        if 0x0B80 <= cp <= 0x0BFF: return "Tamil"
        if 0x0C80 <= cp <= 0x0CFF: return "Kannada"
        if 0x0D00 <= cp <= 0x0D7F: return "Malayalam"
        if 0x0980 <= cp <= 0x09FF: return "Bengali"
        if 0x0A80 <= cp <= 0x0AFF: return "Gujarati"
        if 0x0A00 <= cp <= 0x0A7F: return "Punjabi"
        if 0x0B00 <= cp <= 0x0B7F: return "Odia"
        if 0x0600 <= cp <= 0x06FF: return "Urdu"
        if 0x0900 <= cp <= 0x097F: return "Hindi"
    low = blob.lower()
    if any(w in low for w in ["urdu", "shairi", "ghazal", "bhootna", "shoki"]):
        return "Urdu"
    if any(w in low for w in ["hindi", "kahani", "kya", "hai", "kaise"]):
        return "Hindi"
    if any(w in low for w in ["tamil", "thalapathy", "thala", "kodi", "padam"]):
        return "Tamil"
    if any(w in low for w in ["telugu", "ela", "cheppandi", "bagundi"]):
        return "Telugu"
    return "English"

# --- 10. 4-KEY SMART FAILOVER GEMINI STREAMING ---
def get_best_models(client):
    preferred = ["gemini-2.5-flash", "gemini-2.5-flash-lite", "gemini-3.5-flash", "gemini-3.5-flash-lite"]
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
    return preferred[:3]

def clean_mentor_word(text):
    return text.replace("మెంటర్", "సలహాదారు").replace("స్ట్రాటజిస్ట్", "సలహాదారు")

def generate_report_stream(prompt):
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
        except Exception as e:
            last_err = str(e)
            continue
    raise RuntimeError(f"AI Server busy. Please try again in 5 seconds. ({last_err})")

# --- 11. SIDEBAR (NO-SCROLL COMPACT + A-Z LANGUAGE SEARCH) ---
with st.sidebar:
    st.markdown("**⚙️ Settings**")
    report_lang = st.selectbox(
        "🔍 Type to Search Language (A–Z):",
        LANGUAGES_AZ,
        index=0
    )
    ui = get_ui(report_lang)
    audience_scope = st.radio("Target Audience:", ["Regional", "Global", "Both"], horizontal=True, label_visibility="collapsed")

    st.divider()
    st.markdown("**💎 Pro Plans**")

    free_used = get_free_used_count(st.session_state.verified_email) if st.session_state.verified_email else 0
    free_left = max(0, 3 - free_used)

    if st.session_state.pro_unlocked:
        st.success(f"✅ {st.session_state.pro_label}")
    elif st.session_state.verified_email:
        if free_left > 0:
            st.info(f"🎁 {ui['free_left'].format(n=free_left)}")
        else:
            st.error(f"🔒 {ui['free_done']}")
    else:
        st.info("🎁 3 Free Reports on Login")

    st.markdown(f"• **1 Month:** ₹100 👉 [Pay ₹100]({RAZORPAY_1M})")
    st.markdown(f"• **12 Months:** ₹1,000 👉 [Pay ₹1,000]({RAZORPAY_12M})")

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
                st.session_state.pro_label = f"PRO ACTIVE ({plan_choice})"
                st.rerun()
            elif status == "EXPIRED":
                st.error("⏰ Plan Expired!")
            elif status == "ALREADY_USED":
                st.error("❌ Used on 3 devices!")
            else:
                st.error("❌ Invalid ID")

    st.divider()
    st.caption("📩 support@aiengtel.com | © 2026 aiengtel.com")

# --- 12. CENTER LOGO HEADER ---
logo_html = ""
if os.path.exists("logo.png"):
    with open("logo.png", "rb") as lf:
        b64_logo = base64.b64encode(lf.read()).decode()
    logo_html = f'<img src="data:image/png;base64,{b64_logo}" style="height:36px; width:36px; border-radius:8px; object-fit:contain;" />'

st.markdown(f"""
<div class="center-header">
    <div class="brand-row">
        {logo_html}
        <h1 class="brand-title">TrendSutra AI</h1>
        <span class="india-badge">🇮🇳 1 AI • 1 India</span>
    </div>
    <p class="brand-sub">A to Z Growth Analyzer in All 22 Indian Languages + Bhojpuri for YouTube, Instagram & TikTok</p>
</div>
""", unsafe_allow_html=True)

# --- 13. COMPACT SINGLE-ROW LOGIN BAR ---
if not st.session_state.verified_email and not st.session_state.pro_unlocked:
    st.caption(f"🔐 {ui['login_prompt']}")
    lc1, lc2, lc3, lc4 = st.columns([2.2, 0.4, 2.5, 1.5], vertical_alignment="bottom")
    with lc1:
        if st.button("Continue with Gmail", type="primary", use_container_width=True):
            try:
                st.login("google")
            except Exception as e:
                st.error(f"Google Login Error: {e}")
    with lc2:
        st.markdown("<div style='text-align:center; padding-bottom:8px; font-weight:700; color:#94a3b8;'>OR</div>", unsafe_allow_html=True)
    with lc3:
        email_in = st.text_input("Login with Mail ID", placeholder="Login with Mail ID (creator@gmail.com)", label_visibility="collapsed")
    with lc4:
        if st.button(ui["send_otp"], use_container_width=True):
            clean_em = email_in.strip().lower()
            if "@" not in clean_em or "." not in clean_em.split("@")[-1]:
                st.error("❌ Enter valid Email")
            elif clean_em.split("@")[-1] in TEMP_DOMAINS:
                st.error("❌ Temp email blocked")
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
        oc1, oc2 = st.columns([2.5, 1.5], vertical_alignment="bottom")
        with oc1:
            otp_in = st.text_input("Enter 6-digit OTP", placeholder="Enter 6-digit OTP", max_chars=6, label_visibility="collapsed")
        with oc2:
            if st.button(ui["verify_otp"], type="primary", use_container_width=True):
                if otp_in.strip() == st.session_state.otp_code:
                    st.session_state.verified_email = st.session_state.otp_target
                    st.session_state.otp_code = ""
                    st.rerun()
                else:
                    st.error("❌ Invalid OTP")
else:
    uc1, uc2 = st.columns([5, 1], vertical_alignment="center")
    with uc1:
        badge_txt = st.session_state.pro_label if st.session_state.pro_unlocked else ui["free_left"].format(n=free_left)
        who_txt = st.session_state.verified_email if st.session_state.verified_email else "PRO User"
        st.caption(f"👤 Logged in as **{who_txt}**  |  🎁 **{badge_txt}**")
    with uc2:
        if st.button("Logout 🚪", use_container_width=True):
            st.session_state.verified_email = ""
            st.session_state.pro_unlocked = False
            st.session_state.yt_report = ""
            st.session_state.detected_ui_lang = "English"
            try:
                if hasattr(st, "logout"):
                    st.logout()
            except Exception:
                pass
            st.rerun()

# --- 14. MAIN WORKSPACE TABS ---
tab_yt, tab_ig, tab_tt = st.tabs(["📺 YouTube Analyzer", "📸 Instagram Reels Analyzer", "🎵 TikTok Analyzer"])

with tab_yt:
    yc1, yc2 = st.columns([4.2, 1.5], vertical_alignment="bottom")
    with yc1:
        yt_url = st.text_input("YouTube URL", placeholder="Paste YouTube Video or Shorts Link (https://...)", label_visibility="collapsed")
    with yc2:
        run_yt = st.button(ui["gen_btn"], key="btn_yt", type="primary", use_container_width=True)

    yt_status = st.empty()

    if run_yt:
        if not yt_url.strip():
            st.warning("Please paste a YouTube link.")
        elif not st.session_state.pro_unlocked and free_left <= 0:
            st.error(f"🔒 {ui['free_done']}")
        else:
            vid_id = extract_youtube_id(yt_url.strip())
            if not vid_id:
                st.error("❌ Invalid YouTube Video or Shorts link.")
            else:
                yt_status.markdown(f'<div class="status-pill">{ui["fetching"]}</div>', unsafe_allow_html=True)
                data = fetch_youtube_details(vid_id)
                if not data:
                    yt_status.empty()
                    st.error("❌ Could not fetch video details. Make sure the video is Public.")
                else:
                    if "Auto-Detect" in report_lang:
                        det_lang = detect_ui_lang_from_video(data)
                        st.session_state.detected_ui_lang = det_lang
                        active_ui = UI_TEXT.get(det_lang, UI_TEXT["English"])
                    else:
                        active_ui = ui

                    m1, m2, m3 = st.columns(3)
                    m1.metric("👀 Views", f"{data['views']:,}")
                    m2.metric("👍 Likes", f"{data['likes']:,}")
                    m3.metric("💬 Comments", f"{data['comment_count']:,}")

                    comments_block = "\n".join(data["comments"][:15]) if data["comments"] else "No public comments available."
                    if "Auto-Detect" in report_lang:
                        lang_instruction = (
                            "STEP 1: Detect the primary spoken/written language of this video from its Title, Audio Language Tag, Description, and Audience Comments.\n"
                            "STEP 2: Print the first line strictly as: `🌐 **Detected Video Language:** <Language Name>`\n"
                            "STEP 3: Write the ENTIRE report (including ALL 6 section headings, story recap, comment translations, hooks, and action plan) STRICTLY in that detected language's native script! "
                            "(CRITICAL SCRIPT RULE: If the video is Urdu, write in Urdu script اردو; if Tamil, write in Tamil script தமிழ்; if Telugu, write in Telugu script తెలుగు; if Hindi, write in Devanagari Hindi script हिन्दी. NEVER write Urdu, Hindi, or Telugu in English/Roman letters unless the video itself is purely in English)."
                        )
                    else:
                        lang_instruction = (
                            f"TARGET LANGUAGE: **{report_lang}**.\n"
                            f"{active_ui['script_rule']}\n"
                            "CRITICAL: Every single heading, paragraph, story recap, and comment translation MUST be in that exact target language and its native script."
                        )

                    prompt = f"""
You are a warm, encouraging, expert human social media growth advisor.
Write a deeply detailed, easy-to-understand growth audit report (1,100 to 1,500 words) for a **{audience_scope}** audience.
Use simple everyday spoken words (never use complex bookish words; in Telugu use 'సలహాదారు' and NEVER use 'మెంటర్').

{lang_instruction}

VIDEO DATA:
- Channel: {data['channel']}
- Title: {data['title']}
- Audio Language Hint: {data['default_audio_lang']}
- Views: {data['views']:,} | Likes: {data['likes']:,} | Comments: {data['comment_count']:,}
- Description: {data['description']}
- Tags: {', '.join(data['tags'])}
- Real Audience Comments:
{comments_block}

STRICTLY FOLLOW THIS 6-SECTION STRUCTURE (All 6 headings must be in the target report language!):
{active_ui['sec1']}
- Warmly retell the core story/message of this video based on its title, description, and comments so the creator feels you truly understood their video, then genuinely praise their effort and strengths.

{active_ui['sec2']}
- Pick 4 to 5 real viewer comments from the list above, translate them naturally into the report language, quote them with the viewer's name, and give 3 ready-to-copy reply templates.

{active_ui['sec3']}
- Give 3 fresh follow-up video ideas tailored to this channel, each with an exact word-for-word **5-second opening Hook** and a **Thumbnail idea**.

{active_ui['sec4']}
- Provide 3 clickable high-CTR title options, a strong 3-line SEO description hook, and 15 searchable comma-separated tags.

{active_ui['sec5']}
- Explain 3 practical ways this specific channel can earn money (AdSense, Affiliate links, Brand sponsorships).

{active_ui['sec6']}
- Give a clear Week 1 to Week 4 checklist of simple actions to grow views and subscribers.
"""
                    yt_status.markdown(f'<div class="status-pill">{active_ui["generating"]}</div>', unsafe_allow_html=True)
                    report_box = st.empty()
                    full_text = ""
                    try:
                        for piece in generate_report_stream(prompt):
                            full_text += piece
                            report_box.markdown(full_text)
                        yt_status.empty()
                        st.session_state.yt_report = full_text
                        st.session_state.yt_vid_id = vid_id
                        if not st.session_state.pro_unlocked and st.session_state.verified_email:
                            increment_free_used(st.session_state.verified_email)
                        log_usage_to_sheet(st.session_state.verified_email or "PRO", "YouTube", yt_url.strip())
                        st.rerun()
                    except Exception as e:
                        yt_status.empty()
                        st.error(str(e))

    if st.session_state.yt_report:
        st.success(ui["done"])
        st.markdown(st.session_state.yt_report)
        st.download_button(
            ui["dl_btn"],
            data=st.session_state.yt_report,
            file_name=f"TrendSutra_YouTube_Report_{st.session_state.yt_vid_id or 'audit'}.txt",
            mime="text/plain",
            use_container_width=True
        )

with tab_ig:
    ic1, ic2 = st.columns([4.2, 1.5], vertical_alignment="bottom")
    with ic1:
        ig_url = st.text_input("Instagram URL", placeholder="Paste Instagram Reel Link (https://www.instagram.com/reel/...)", label_visibility="collapsed")
    with ic2:
        run_ig = st.button(ui["gen_btn"], key="btn_ig", type="primary", use_container_width=True)

    ig_status = st.empty()

    if run_ig:
        if not ig_url.strip():
            st.warning("Please paste an Instagram Reel link.")
        elif not st.session_state.pro_unlocked and free_left <= 0:
            st.error(f"🔒 {ui['free_done']}")
        else:
            ig_status.markdown(f'<div class="status-pill">{ui["generating"]}</div>', unsafe_allow_html=True)
            ig_lang_rule = "Detect the language from the link/context or use English if unknown, writing all headings and content in that language's native script." if "Auto-Detect" in report_lang else f"Write the ENTIRE report and all section headings strictly in **{report_lang}**. {ui['script_rule']}"
            ig_prompt = f"""
You are a warm, encouraging human Instagram Reels growth advisor.
Write a detailed 6-section Instagram Reels growth audit (1,000+ words) for a **{audience_scope}** audience using simple spoken words (in Telugu use 'సలహాదారు', never 'మెంటర్').
{ig_lang_rule}
Reel Link: {ig_url.strip()}
Include 6 translated headings covering:
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
                ig_status.empty()
                st.session_state.ig_report = full_text
                if not st.session_state.pro_unlocked and st.session_state.verified_email:
                    increment_free_used(st.session_state.verified_email)
                log_usage_to_sheet(st.session_state.verified_email or "PRO", "Instagram", ig_url.strip())
                st.rerun()
            except Exception as e:
                ig_status.empty()
                st.error(str(e))

    if st.session_state.ig_report:
        st.success(ui["done"])
        st.markdown(st.session_state.ig_report)
        st.download_button(
            ui["dl_btn"],
            data=st.session_state.ig_report,
            file_name="TrendSutra_Instagram_Report.txt",
            mime="text/plain",
            use_container_width=True
        )

with tab_tt:
    tc1, tc2 = st.columns([4.2, 1.5], vertical_alignment="bottom")
    with tc1:
        tt_url = st.text_input("TikTok URL", placeholder="Paste TikTok Video Link (https://www.tiktok.com/...)", label_visibility="collapsed")
    with tc2:
        run_tt = st.button(ui["gen_btn"], key="btn_tt", type="primary", use_container_width=True)

    tt_status = st.empty()

    if run_tt:
        if not tt_url.strip():
            st.warning("Please paste a TikTok link.")
        elif not st.session_state.pro_unlocked and free_left <= 0:
            st.error(f"🔒 {ui['free_done']}")
        else:
            tt_status.markdown(f'<div class="status-pill">{ui["generating"]}</div>', unsafe_allow_html=True)
            tt_lang_rule = "Detect the language from the link/context or use English if unknown, writing all headings and content in that language's native script." if "Auto-Detect" in report_lang else f"Write the ENTIRE report and all section headings strictly in **{report_lang}**. {ui['script_rule']}"
            tt_prompt = f"""
You are a warm, encouraging human TikTok growth advisor.
Write a detailed 6-section TikTok growth audit (1,000+ words) for a **{audience_scope}** audience using simple spoken words (in Telugu use 'సలహాదారు', never 'మెంటర్').
{tt_lang_rule}
TikTok Link: {tt_url.strip()}
Include 6 translated headings covering:
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
                if not st.session_state.pro_unlocked and st.session_state.verified_email:
                    increment_free_used(st.session_state.verified_email)
                log_usage_to_sheet(st.session_state.verified_email or "PRO", "TikTok", tt_url.strip())
                st.rerun()
            except Exception as e:
                tt_status.empty()
                st.error(str(e))

    if st.session_state.tt_report:
        st.success(ui["done"])
        st.markdown(st.session_state.tt_report)
        st.download_button(
            ui["dl_btn"],
            data=st.session_state.tt_report,
            file_name="TrendSutra_TikTok_Report.txt",
            mime="text/plain",
            use_container_width=True
        )
