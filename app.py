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
    """<style>
    #MainMenu, footer, .stDeployButton, div[data-testid="stToolbarActions"] {display: none !important;}
    header[data-testid="stHeader"] {height: 1.5rem !important; background: transparent !important;}
    .block-container {padding-top: 0rem !important; margin-top: -2.2rem !important; padding-bottom: 1rem !important;}
    section[data-testid="stSidebar"] > div:first-child {padding-top: 0rem !important; margin-top: -1.5rem !important;}
    div[data-testid="stSidebarUserContent"] {padding-top: 0rem !important;}
    div.stButton > button:first-child {background-color: #c92a2a; color: white; font-weight: bold; border-radius: 6px; padding: 0.5rem 1.2rem; border: none;}
    div.stDownloadButton > button:first-child {background-color: #2b8a3e; color: white; font-weight: bold; border-radius: 6px; padding: 0.5rem 1.2rem; border: none;}
    </style>""",
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

GOOGLE_SHEET_API = "https://script.google.com/macros/s/AKfycbzEkkgxBP7aOKIXkEiOG7_rWc0quvnvTVqQDSWUAMk2zOPN7W8Ue_uOPwH7edmJJtEd/exec"
PAY_1_MONTH_LINK = "https://rzp.io/rzp/yop8jYS"
PAY_12_MONTHS_LINK = "https://rzp.io/rzp/sjonGmqw"

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

if (
    ls_free
    and str(ls_free).isdigit()
    and int(ls_free) > st.session_state.free_used_count
):
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
    if "VALID" in txt:
      return "VALID"
    return "INVALID"
  except Exception:
    return "ERROR"


url_pid = st.query_params.get("razorpay_payment_id", "")
if url_pid and not st.session_state.is_pro_user:
  st_val = verify_payment_id(url_pid)
  if st_val == "VALID":
    st.session_state.is_pro_user = True
    streamlit_js_eval(
        js_expressions="localStorage.setItem('ts_device_pro_v5', 'yes')",
        key="ls_pro_url",
    )
    st.toast("🎉 Payment Verified! Unlimited Pro Access Unlocked!")
  elif st_val == "ALREADY_USED":
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
    rem = max(0, 3 - st.session_state.free_used_count)
    st.caption(f"🎁 **Free Trial:** మీకు **{rem} ఉచిత రిపోర్ట్‌లు** మిగిలి ఉన్నాయి.")
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
      res_st = verify_payment_id(manual_pid)
      if res_st == "OWNER_VALID":
        st.session_state.is_pro_user = True
        st.rerun()
      elif res_st == "VALID":
        st.session_state.is_pro_user = True
        streamlit_js_eval(
            js_expressions="localStorage.setItem('ts_device_pro_v5', 'yes')",
            key=f"ls_pro_{int(time.time())}",
        )
        time.sleep(0.6)
        st.rerun()
      elif res_st == "ALREADY_USED":
        st.error(
            "❌ ఈ Payment ID గరిష్టంగా 3 డివైజ్‌లలో వాడబడింది! support@aiengtel.com"
            " కి మెసేజ్ చేయండి."
        )
      else:
        st.error("❌ సరైన Payment ID ఇవ్వండి.")

if os.path.isfile("logo.png"):
  c1, c2 = st.columns((1, 5))
  with c1:
    st.image("logo.png", width=100)
  with c2:
    st.markdown("# TrendSutra AI")
    st.markdown(
        "**A to Z Growth Analyzer for YouTube, Instagram & TikTok | Powered by"
        " [AIENGTEL.com](https://aiengtel.com)**"
    )
else:
  st.markdown(
      "# 🚀 TrendSutra AI\n**A to Z Growth Analyzer for YouTube, Instagram &"
      " TikTok | Powered by [AIENGTEL.com](https://aiengtel.com)**"
  )

col1, col2 = st.columns(2)
with col1:
  platform = st.selectbox(
      "Select Platform:", ("YouTube", "Instagram Reels", "TikTok")
  )
with col2:
  video_url = st.text_input(
      "Channel / Profile / Video Link:",
      placeholder="https://youtu.be/... లేదా Reel / TikTok లింక్ పేస్ట్ చేయండి",
  )


def fetch_youtube_info(url):
  m = re.search(r"(?:v=|\/|live\/|shorts\/)([0-9A-Za-z_-]{11}).*", url)
  if not m:
    return None, "సరైన YouTube వీడియో లింక్ ఇవ్వండి."
  try:
    yt = build("youtube", "v3", developerKey=YOUTUBE_KEY)
    vr = yt.videos().list(part="snippet,statistics", id=m.group(1)).execute()
    items = vr.get("items", ())
    if not items:
      return None, "వీడియో వివరాలు దొరకలేదు."
    sn, st_obj = items[0]["snippet"], items[0]["statistics"]
    coms = []
    try:
      cr = (
          yt.commentThreads()
          .list(
              part="snippet",
              videoId=m.group(1),
              maxResults=30,
              order="relevance",
              textFormat="plainText",
          )
          .execute()
      )
      coms = [
          c["snippet"]["topLevelComment"]["snippet"]["textDisplay"]
          for c in cr.get("items", ())
      ]
    except Exception:
      coms = ["కామెంట్లు ఆఫ్ చేసి ఉన్నాయి."]
    return (
        f"Title: {sn.get('title')}\nViews: {st_obj.get('viewCount','0')},"
        f" Likes: {st_obj.get('likeCount','0')}\nDesc:"
        f" {sn.get('description','')[:600]}\nTags: {sn.get('tags',())}\nComments:"
        f" {coms}",
        st_obj,
    )
  except Exception as e:
    return None, f"YouTube Error: {str(e)}"


def generate_growth_report(platform_name, raw_data, lang, audience):
  prompt = (
      f"You are a friendly, practical {platform_name} Growth Advisor for"
      " TrendSutra AI.\nAnalyze the data and give an A-to-Z Growth"
      f" Report.\n- Output Language: {lang}\n- If {lang} is Telugu: Write in"
      " simple, natural, everyday spoken Telugu like a friend explaining to"
      ' another friend. Use exact Telugu spelling "పని 1", "పని 2", "పని 3"'
      ' (NEVER write "పను 1").\n- Target Audience:'
      f" {audience}\n- Start with 1 simple line mentioning TrendSutra AI, then"
      f" go straight to Section 1.\nSource Data: {raw_data}\nStructure into 5"
      " clear sections:\n"
      "1. 👥 **Viewers ఏమనుకుంటున్నారు? (Audience Feedback & Questions)**\n"
      "2. 🎥 **తర్వాత చేయాల్సిన 3 Viral Video Ideas (Titles & Hooks తో)**\n"
      "3. 💰 **ఈ ఛానెల్ ద్వారా డబ్బులు ఎలా సంపాదించాలి? (Earning Ideas)**\n"
      "4. 🔍 **Views పెరగడానికి Title, Description & Tags మార్పులు**\n"
      "5. 🚀 **రాబోయే 30 రోజుల్లో చేయాల్సిన 3 ముఖ్య పనులు (పని 1, పని 2, పని 3)**"
  )
  last_err = "API Key missing in Secrets"
  for attempt in range(3):
    for key in GEMINI_KEYS:
      if not key.strip():
        continue
      client = genai.Client(api_key=key.strip())
      try:
        avail = [
            m.name.replace("models/", "")
            for m in client.models.list()
            if "flash" in m.name and "lite" not in m.name
        ]
      except Exception:
        avail = ["gemini-2.5-flash", "gemini-3.5-flash", "gemini-2.5-pro"]
      models_to_try = avail[:3] if avail else ["gemini-2.5-flash", "gemini-3.5-flash"]
      for m in models_to_try:
        try:
          resp = client.models.generate_content(model=m, contents=prompt)
          if resp and resp.text:
            return True, resp.text
        except Exception as e:
          last_err = str(e)
          time.sleep(2)
  return False, f"⚠️ AI సర్వర్ బిజీగా ఉంది: {last_err[:120]}"


if "generated_report" not in st.session_state:
  st.session_state.generated_report = ""
if "report_stats" not in st.session_state:
  st.session_state.report_stats = None

if st.button("Generate Accurate Growth Report 🔍"):
  if not st.session_state.is_pro_user and st.session_state.free_used_count >= 3:
    st.session_state.generated_report = ""
    st.error("🔒 **ఈ డివైజ్‌లో మీ 3 ఉచిత రిపోర్ట్‌లు పూర్తయ్యాయి!**")
    st.markdown(
        f"* **1 Month Unlimited (₹100):** 👉 [Pay ₹100]({PAY_1_MONTH_LINK})\n*"
        f" **12 Months Unlimited (₹1,000):** 👉 [Pay ₹1,000]({PAY_12_MONTHS_LINK})"
    )
  elif not video_url.strip():
    st.warning("⚠️ ముందుగా వీడియో లింక్ పేస్ట్ చేయండి.")
  else:
    with st.spinner("రిపోర్ట్ తయారు చేస్తోంది..."):
      if platform == "YouTube":
        d_txt, st_obj = fetch_youtube_info(video_url.strip())
      else:
        d_txt, st_obj = f"{platform} URL: {video_url.strip()}", None
      if platform == "YouTube" and not d_txt:
        st.error(f"⚠️ {st_obj}")
      else:
        ok, res_txt = generate_growth_report(
            platform, d_txt, report_lang, target_audience
        )
        if ok:
          st.session_state.generated_report, st.session_state.report_stats = (
              res_txt,
              st_obj,
          )
          if not st.session_state.is_pro_user:
            st.session_state.free_used_count += 1
            streamlit_js_eval(
                js_expressions=(
                    "localStorage.setItem('ts_device_free_v5',"
                    f" '{st.session_state.free_used_count}')"
                ),
                key=f"ls_f_{int(time.time())}",
            )
            time.sleep(0.6)
            st.rerun()
        else:
          st.error(res_txt)

if st.session_state.generated_report:
  if isinstance(st.session_state.report_stats, dict):
    m1, m2, m3 = st.columns(3)
    m1.metric(
        "👀 Views", f"{int(st.session_state.report_stats.get('viewCount',0)):,}"
    )
    m2.metric(
        "👍 Likes", f"{int(st.session_state.report_stats.get('likeCount',0)):,}"
    )
    m3.metric(
        "💬 Comments",
        f"{int(st.session_state.report_stats.get('commentCount',0)):,}",
    )
  st.success("✅ Growth Audit Report సిద్ధమైంది!")
  st.download_button(
      "📥 Download Growth Report (.txt)",
      st.session_state.generated_report,
      "TrendSutra_Report.txt",
  )
  st.markdown(st.session_state.generated_report)
