import os
import re
import time
from google import genai
from googleapiclient.discovery import build
import requests
import streamlit as st
from streamlit_js_eval import get_cookie, set_cookie

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

# --- మీ Google Sheet Apps Script Web App URL ---
GOOGLE_SHEET_API = "https://script.google.com/macros/s/AKfycbzEkkgxBP7aOKIXkEiOG7_rWc0quvnvTVqQDSWUAMk2zOPN7W8Ue_uOPwH7edmJJtEd/exec"

# --- మీ రెండు పూర్తి Razorpay పేమెంట్ లింక్‌లను ఇక్కడ పేస్ట్ చేయండి ---
PAY_1_MONTH_LINK = "https://rzp.io/rzp/yop8jYS"
PAY_12_MONTHS_LINK = "https://rzp.io/rzp/sjonGmqw"

cookie_free_used = get_cookie("ts_free_used_v3")
cookie_pro = get_cookie("ts_pro_active")

if "free_used_count" not in st.session_state:
  st.session_state.free_used_count = (
      int(cookie_free_used)
      if (cookie_free_used and str(cookie_free_used).isdigit())
      else 0
  )
elif cookie_free_used and str(cookie_free_used).isdigit():
  st.session_state.free_used_count = max(
      st.session_state.free_used_count, int(cookie_free_used)
  )

if "is_pro_user" not in st.session_state:
  st.session_state.is_pro_user = True if cookie_pro == "yes" else False
elif cookie_pro == "yes":
  st.session_state.is_pro_user = True


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
    set_cookie("ts_pro_active", "yes", 30)
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
        set_cookie("ts_pro_active", "yes", 30)
        st.rerun()
      elif res_status == "ALREADY_USED":
        st.error("❌ ఈ Payment ID ఇప్పటికే వేరే వారు వాడారు!")
      else:
        st.error("❌ సరైన Payment ID ఇవ్వండి.")
if os.path.isfile("logo.png"):
  col_logo, col_title = st.columns((1, 5))
  with col_logo:
    st.image("logo.png", width=100)
  with col_title:
    st.markdown("# TrendSutra AI")
    st.markdown(
        "**A to Z Growth Analyzer for YouTube, Instagram & TikTok | Powered by"
        " [AIENGTEL.com](https://aiengtel.com)**"
    )
else:
  st.markdown("# 🚀 TrendSutra AI")
  st.markdown(
      "**A to Z Growth Analyzer for YouTube, Instagram & TikTok | Powered by"
      " [AIENGTEL.com](https://aiengtel.com)**"
  )

col1, col2 = st.columns(2)
with col1:
  platform = st.selectbox(
      "Select Platform:", ("YouTube", "Instagram Reels", "TikTok")
  )
with col2:
  video_url = st.text_input(
      "Channel / Profile / Video Link:",
      placeholder="https://youtu.be... లేదా Reel / TikTok లింక్ పేస్ట్ చేయండి",
  )


def extract_youtube_id(url):
  pattern = r"(?:v=|\/|live\/|shorts\/)([0-9A-Za-z_-]{11}).*"
  match = re.search(pattern, url)
  return match.group(1) if match else None


def fetch_youtube_info(url):
  vid_id = extract_youtube_id(url)
  if not vid_id:
    return (
        None,
        "సరైన YouTube వీడియో లింక్ ఇవ్వండి (ఉదా: https://youtu.be...).",
    )
  try:
    youtube = build("youtube", "v3", developerKey=YOUTUBE_KEY)
    vid_res = (
        youtube.videos().list(part="snippet,statistics", id=vid_id).execute()
    )
    items_list = vid_res.get("items", ())
    if not items_list:
      return None, "ఈ వీడియో వివరాలు దొరకలేదు (ప్రైవేట్ వీడియో కావచ్చు)."
    item = next(iter(items_list))
    snippet = item.get("snippet", {})
    stats = item.get("statistics", {})
    comments = []
    try:
      com_res = (
          youtube.commentThreads()
          .list(
              part="snippet",
              videoId=vid_id,
              maxResults=40,
              order="relevance",
              textFormat="plainText",
          )
          .execute()
      )
      for c in com_res.get("items", ()):
        comments.append(
            c.get("snippet", {})
            .get("topLevelComment", {})
            .get("snippet", {})
            .get("textDisplay", "")
        )
    except Exception:
      comments.append("కామెంట్లు ఆఫ్ చేసి ఉన్నాయి.")
    summary = (
        f"Title: {snippet.get('title')}\nViews:"
        f" {stats.get('viewCount', '0')}, Likes:"
        f" {stats.get('likeCount', '0')}, Comments:"
        f" {stats.get('commentCount', '0')}\nDescription:"
        f" {snippet.get('description', '')[:800]}\nTags:"
        f" {snippet.get('tags', ())}\nTop Comments: {comments}"
    )
    return summary, stats
  except Exception as e:
    return None, f"YouTube API లోపం: {str(e)}"


def fetch_rapidapi_safe(host, path, params, fallback_label):
  try:
    api_url = "https://" + host + path
    headers = {"x-rapidapi-key": RAPIDAPI_KEY, "x-rapidapi-host": host}
    res = requests.get(api_url, headers=headers, params=params, timeout=15)
    if res.status_code == 200 and res.text and res.text.strip():
      return f"{fallback_label} Data:\n{res.text[:3500]}"
    return (
        f"{fallback_label} URL provided (API status {res.status_code}). Analyze"
        " based on URL structure & niche."
    )
  except Exception as e:
    return f"{fallback_label} URL provided (Fetch note: {str(e)})."


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
  models_list = (
      "gemini-3.5-flash-lite",
      "gemini-3.8-flash",
      "gemini-2.5-flash",
  )
  for attempt in range(2):
    for key in GEMINI_KEYS:
      client = genai.Client(api_key=key)
      for model_name in models_list:
        try:
          resp = client.models.generate_content(
              model=model_name, contents=prompt
          )
          if resp and resp.text:
            return True, resp.text
        except Exception:
          time.sleep(1.5)
          continue
  return (
      False,
      "⚠️ AI సర్వర్ ప్రస్తుతం బిజీగా ఉంది. దయచేసి 5 సెకన్ల తర్వాత మళ్ళీ క్లిక్ చేయండి.",
  )


if "generated_report" not in st.session_state:
  st.session_state.generated_report = ""
if "report_stats" not in st.session_state:
  st.session_state.report_stats = None
if "report_platform" not in st.session_state:
  st.session_state.report_platform = ""

if st.button("Generate Accurate Growth Report 🔍"):
  if not st.session_state.is_pro_user and st.session_state.free_used_count >= 3:
    st.session_state.generated_report = ""
    st.error("🔒 **మీ 3 ఉచిత రిపోర్ట్‌లు పూర్తయ్యాయి!**")
    st.markdown(
        "### 🚀 Unlimited Growth Reports పొందడానికి Pro Plan ఎంచుకోండి:\n"
        f"* **1 Month Unlimited Plan — ₹100/-** 👉 [Click Here to Pay"
        f" ₹100]({PAY_1_MONTH_LINK})\n"
        f"* **12 Months Unlimited Plan — ₹1,000/-** 👉 [Click Here to Pay"
        f" ₹1,000]({PAY_12_MONTHS_LINK})\n\n"
        "*(పేమెంట్ పూర్తయిన వెంటనే మీ అకౌంట్ ఆటోమేటిక్‌గా అన్‌లాక్ అవుతుంది!)*"
    )
  elif not video_url.strip():
    st.warning("⚠️ దయచేసి ముందుగా వీడియో లేదా ప్రొఫైల్ లింక్ పేస్ట్ చేయండి.")
  else:
    data_text = ""
    stats_obj = None
    with st.spinner(f"{platform} నుండి డేటా తీసుకుంటోంది..."):
      if platform == "YouTube":
        data_text, stats_obj = fetch_youtube_info(video_url.strip())
      elif platform == "Instagram Reels":
        ig_host = "instagram-scraper-stable-api.p." + "rapidapi.com"
        data_text = fetch_rapidapi_safe(
            ig_host,
            "/get_media_data.php",
            {"reel_post_code_or_url": video_url.strip()},
            f"Instagram Reel ({video_url.strip()})",
        )
      elif platform == "TikTok":
        tt_host = "tiktok-api23.p." + "rapidapi.com"
        data_text = fetch_rapidapi_safe(
            tt_host,
            "/api/post/detail",
            {"url": video_url.strip()},
            f"TikTok Video ({video_url.strip()})",
        )
    if platform == "YouTube" and not data_text:
      st.error(f"⚠️ {stats_obj}")
    else:
      with st.spinner("TrendSutra AI రిపోర్ట్ తయారు చేస్తోంది..."):
        success, result_text = generate_growth_report(
            platform, data_text, report_lang, target_audience
        )
        if success:
          st.session_state.generated_report = result_text
          st.session_state.report_stats = (
              stats_obj if platform == "YouTube" else None
          )
          st.session_state.report_platform = platform
          if not st.session_state.is_pro_user:
            st.session_state.free_used_count += 1
            set_cookie(
                "ts_free_used_v3", str(st.session_state.free_used_count), 365
            )
            st.rerun()
        else:
          st.session_state.generated_report = ""
          st.error(result_text)

if st.session_state.generated_report:
  if isinstance(st.session_state.report_stats, dict):
    m1, m2, m3 = st.columns(3)
    m1.metric(
        "👀 Views", f"{int(st.session_state.report_stats.get('viewCount', 0)):,}"
    )
    m2.metric(
        "👍 Likes", f"{int(st.session_state.report_stats.get('likeCount', 0)):,}"
    )
    m3.metric(
        "💬 Comments",
        f"{int(st.session_state.report_stats.get('commentCount', 0)):,}",
    )
  st.success("✅ మీ Growth Report రెడీ అయింది!")
  file_content = (
      f"=== TrendSutra AI - {st.session_state.report_platform} Growth"
      f" Report ===\nPowered by AIENGTEL.com\n\n{st.session_state.generated_report}"
  )
  st.download_button(
      label="📥 Download Growth Report (.txt)",
      data=file_content,
      file_name=f"TrendSutra_AI_{st.session_state.report_platform}_Report.txt",
      mime="text/plain",
  )
  st.markdown("---")
  st.markdown(st.session_state.generated_report)
