import os
import re
import time
from google import genai
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
    #MainMenu {visibility: hidden !important;}
    footer {visibility: hidden !important;}
    .stDeployButton {display: none !important;}
    div[data-testid="stToolbarActions"] {display: none !important;}
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

raw_keys = (
    st.secrets.get("GEMINI_API_KEY", ""),
    st.secrets.get("GEMINI_API_KEY_2", ""),
)
GEMINI_KEYS = [k for k in raw_keys if k]
YOUTUBE_KEY = st.secrets.get("YOUTUBE_API_KEY", "")
RAPIDAPI_KEY = st.secrets.get("RAPIDAPI_API_KEY", "")

GOOGLE_SHEET_API = "https://google.com"
PAY_1_MONTH_LINK = "https://rzp.io"
PAY_12_MONTHS_LINK = "https://rzp.io"

ls_free = streamlit_js_eval(
    js_expressions="localStorage.getItem('ts_free_v4')", key="ls_get_free"
)
ls_pro = streamlit_js_eval(
    js_expressions="localStorage.getItem('ts_pro_v4')", key="ls_get_pro"
)

if "free_used_count" not in st.session_state:
  st.session_state.free_used_count = 0
if "is_pro_user" not in st.session_state:
  st.session_state.is_pro_user = False

if ls_free and str(ls_free).isdigit():
  saved_count = int(ls_free)
  if saved_count > st.session_state.free_used_count:
    st.session_state.free_used_count = saved_count
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
    full_url = f"{GOOGLE_SHEET_API}?pid={clean_pid}"
    headers = {"User-Agent": "Mozilla/5.0"}
    res = requests.get(
        full_url, headers=headers, allow_redirects=True, timeout=15
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
        js_expressions="localStorage.setItem('ts_pro_v4', 'yes')",
        key="ls_set_pro_url",
    )
    st.toast("🎉 Payment Verified! Unlimited Pro Access Unlocked!")
  elif status == "ALREADY_USED":
    st.sidebar.error("⚠️ ఈ Payment ID ఇప్పటికే వాడబడింది!")

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
        "🔑 Payment ID (pay_...):",
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
            js_expressions="localStorage.setItem('ts_pro_v4', 'yes')",
            key=f"ls_set_pro_{int(time.time())}",
        )
        time.sleep(0.5)
        st.rerun()
      elif res_status == "ALREADY_USED":
        st.error("❌ ఈ Payment ID ఇప్పటికే వేరే వారు వాడారు!")
      else:
        st.error("❌ సరైన Payment ID ఇవ్వండి.")
