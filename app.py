import os
import re
import time
from googleapiclient.discovery import build
import requests
import streamlit as st
from streamlit_js_eval import streamlit_js_eval

st.set_page_config(
    page_title="TrendSutra AI - Growth Analyzer",
    page_icon="logo.png" if os.path.isfile("logo.png") else "🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    #MainMenu, footer, .stDeployButton, div[data-testid="stToolbarActions"] {display: none !important;}
    header[data-testid="stHeader"] {height: 1.5rem !important; background: transparent !important;}
    .block-container {padding-top: 0rem !important; margin-top: -2.2rem !important; padding-bottom: 1rem !important;}
    section[data-testid="stSidebar"] > div:first-child {padding-top: 0rem !important; margin-top: -1.5rem !important;}
    div[data-testid="stSidebarUserContent"] {padding-top: 0rem !important;}
    div.stButton > button:first-child {background-color: #c92a2a; color: white; font-weight: bold; border-radius: 6px; padding: 0.5rem 1.2rem; border: none;}
    div.stDownloadButton > button:first-child {background-color: #2b8a3e; color: white; font-weight: bold; border-radius: 6px; padding: 0.5rem 1.2rem; border: none;}
    </style>
    """,
    unsafe_allow_html=True,
)

GEMINI_KEYS = [
    k
    for k in (
        st.secrets.get("GEMINI_API_KEY", ""),
        st.secrets.get("GEMINI_API_KEY_2", ""),
    )
    if k
]
YOUTUBE_KEY = st.secrets.get("YOUTUBE_API_KEY", "")
RAPIDAPI_KEY = st.secrets.get("RAPIDAPI_API_KEY", "")

GOOGLE_SHEET_API = "https://google.com"
PAY_1_MONTH_LINK = "https://rzp.io"
PAY_12_MONTHS_LINK = "https://rzp.io"

ls_free = streamlit_js_eval(
    js_expressions="localStorage.getItem('ts_device_free_v5')", key="ls_get_free"
)
ls_pro = streamlit_js_eval(
    js_expressions="localStorage.getItem('ts_device_pro_v5')", key="ls_get_pro"
)

if "free_used_count" not in st.session_state:
  st.session_state.free_used_count = 0
if "is_pro_user" not in st.session_state:
  st.session_state.is_pro_user = False

if ls_free and str(ls_free).isdigit() and int(ls_free) > st.session_state.free_used_count:
  st.session_state.free_used_count = int(ls_free)
  st.rerun()
if ls_pro == "yes" and not st.session_state.is_pro_user:
  st.session_state.is_pro_user = True
  st.rerun()
def verify_payment_id(pid):
  if not pid:
    return "INVALID"
  clean_pid = pid.strip()
  owner_key = str(st.secrets.get("OWNER_SECRET_CODE", "")).strip()
  if owner_key and clean_pid == owner_key:
    return "OWNER_VALID"
  if not clean_pid.startswith("pay_"):
    return "INVALID"
  try:
    res = requests.get(
        f"{GOOGLE_SHEET_API}?pid={clean_pid}",
        headers={"User-Agent": "Mozilla/5.0"},
        allow_redirects=True,
        timeout=15,
    )
    txt = res.text.strip()
    if "ALREADY_USED" in txt:
      return "ALREADY_USED"
    if "INVALID" in txt:
      return "INVALID"
    if "VALID" in txt:
      return "VALID"
    return "INVALID"
  except Exception:
    return "ERROR"


url_pid = st.query_params.get("razorpay_payment_id", "")
if url_pid and not st.session_state.is_pro_user:
  status = verify_payment_id(url_pid)
  if status == "VALID":
    st.session_state.is_pro_user = True
    streamlit_js_eval(
        js_expressions="localStorage.setItem('ts_device_pro_v5', 'yes')",
        key="ls_set_pro_url",
    )
    st.toast("🎉 Payment Verified! Unlimited Pro Access Unlocked!")
  elif status == "ALREADY_USED":
    st.sidebar.error("⚠️ ఈ Payment ID గరిష్టంగా 3 డివైజ్‌లలో వాడబడింది!")

with st.sidebar:
  st.markdown("### 🌍 Settings")
  report_lang = st.selectbox(
      "Report Language / భాష:",
      ("English (Global)", "Telugu (తెలుగు)", "Tenglish"),
  )
  target_audience = st.radio(
      "Target Audience:",
      ("Regional / Local", "Global / International", "Both (Global + Local)"),
  )
  st.markdown("### 💎 Pro Plans (Unlimited)")
  if st.session_state.is_pro_user:
    st.success("✅ **PRO UNLIMITED ACTIVE!**\n\nఅన్‌లిమిటెడ్ రిపోర్ట్‌లు పొందవచ్చు.")
  else:
    remaining = max(0, 3 - st.session_state.free_used_count)
    st.caption(f"🎁 **Free Trial:** మీకు **{remaining} ఉచిత రిపోర్ట్‌లు** మిగిలి ఉన్నాయి.")
    st.markdown(
        f"• **1 Month:** **₹100/-** 👉 [Pay ₹100]({PAY_1_MONTH_LINK})  \n• **12"
        f" Months:** **₹1,000/-** 👉 [Pay ₹1,000]({PAY_12_MONTHS_LINK})"
    )
    manual_pid = st.text_input(
        "🔑 Payment ID:",
        placeholder="pay_P9x82kLm01",
        label_visibility="collapsed",
    )
    if st.button("Unlock with Payment ID 🔓"):
      res_status = verify_payment_id(manual_pid)
      if res_status == "OWNER_VALID":
        st.session_state.is_pro_user = True
        st.rerun()
      elif res_status == "VALID":
        st.session_state.is_pro_user = True
        streamlit_js_eval(
            js_expressions="localStorage.setItem('ts_device_pro_v5', 'yes')",
            key=f"ls_set_pro_{int(time.time())}",
        )
        time.sleep(0.6)
        st.rerun()
      elif res_status == "ALREADY_USED":
        st.error(
            "❌ ఈ Payment ID గరిష్టంగా 3 డివైజ్‌లలో వాడబడింది! support@aiengtel.com కి"
            " మెసేజ్ చేయండి."
        )
      else:
        st.error("❌ సరైన Payment ID ఇవ్వండి.")
# --- STEP 3.1: FETCH SOCIAL MEDIA DATA ---
def fetch_social_data(platform, url_or_topic):
    # YouTube కోసం oEmbed API (API Key అవసరం లేకుండానే టైటిల్, ఛానల్ వివరాలు వస్తాయి)
    if platform == "YouTube" and ("youtube.com" in url_or_topic or "youtu.be" in url_or_topic):
        try:
            oembed_url = f"https://youtube.com{url_or_topic}&format=json"
            res = requests.get(oembed_url, timeout=10)
            if res.status_code == 200:
                data = res.json()
                return f"Title: {data.get('title')}, Author: {data.get('author_name')}"
        except Exception as e:
            return f"Topic/URL: {url_or_topic} (Metadata fetch skipped)"
            
    # Instagram Reels / TikTok కోసం డైరెక్ట్ స్క్రాపింగ్ బ్లాక్ అవుతుంది కాబట్టి ఇన్‌పుట్‌ను నేరుగా పంపుతాము
    return f"Platform: {platform} | Input/Link: {url_or_topic}"
# --- STEP 3.2: GEMINI REST API CALL ---
def generate_growth_report(api_key, platform, content_info, niche):
    url = f"https://googleapis.com{api_key}"
    headers = {"Content-Type": "application/json"}
    
    prompt = f"""
    Act as a viral social media strategist. Analyze this {platform} content in the '{niche}' niche:
    {content_info}
    
    Provide a structured Growth Report with:
    1. Viral Hook Ideas (3 options)
    2. Trending Hashtags & SEO Keywords
    3. Content Improvement Tips for higher retention
    4. Best Posting Strategy
    """
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 200:
        return response.json()["candidates"][0]["content"]["parts"][0]["text"]
    else:
        return f"Error {response.status_code}: {response.text}"
# --- STEP 3.3: UI INPUTS & BUTTON ---
st.subheader("🚀 Generate Viral Growth Report")

col1, col2 = st.columns(2)
with col1:
    platform = st.selectbox("Select Platform", ["YouTube", "Instagram Reels", "TikTok"])
with col2:
    niche = st.text_input("Your Niche / Category", placeholder="ఉదా: Tech, Cooking, Fitness")

url_or_topic = st.text_input("Paste Video Link or Enter Topic", placeholder="YouTube URL లేదా వీడియో టాపిక్...")

generate_btn = st.button("✨ Generate Growth Report", type="primary", use_container_width=True)
# --- STEP 3.4: EXECUTION & OUTPUT ---
if generate_btn:
    if not GEMINI_API_KEY:  # Step 1 లో మీరు ఇచ్చిన API Key వేరియబుల్ పేరు ఇక్కడ ఉండాలి
        st.error("దయచేసి ముందుగా Gemini API Key ఎంటర్ చేయండి!")
    elif not url_or_topic:
        st.warning("దయచేసి వీడియో లింక్ లేదా టాపిక్ ఇవ్వండి.")
    else:
        with st.spinner("TrendSutra AI అనలైజ్ చేస్తోంది..."):
            fetched_data = fetch_social_data(platform, url_or_topic)
            report = generate_growth_report(GEMINI_API_KEY, platform, fetched_data, niche)
            
            st.success("రిపోర్ట్ సిద్ధమైంది!")
            st.markdown(report)
            
            # రిపోర్ట్ డౌన్‌లోడ్ బటన్
            st.download_button(
                label="📥 Download Report (.txt)",
                data=report,
                file_name=f"TrendSutra_{platform}_Report.txt",
                mime="text/plain"
            )
