import re
from google import genai
from googleapiclient.discovery import build
import requests
import streamlit as st

st.set_page_config(
    page_title="TrendSutra AI - Growth Analyzer",
    page_icon="🚀",
    layout="wide",
)

# API కీలు Streamlit Secrets నుండి రహస్యంగా వస్తాయి
GEMINI_KEYS = [
    st.secrets.get("GEMINI_API_KEY", ""),
    st.secrets.get("GEMINI_API_KEY_2", ""),
]
GEMINI_KEYS = [k for k in GEMINI_KEYS if k]
YOUTUBE_KEY = st.secrets.get("YOUTUBE_API_KEY", "")
RAPIDAPI_KEY = st.secrets.get("RAPIDAPI_API_KEY", "")

# --- ఎడమ వైపు సైడ్‌బార్ (Left Sidebar) ---
with st.sidebar:
  st.markdown("## 🌍 Global & Regional Settings")
  report_lang = st.selectbox(
      "Report Language / భాషను ఎంచుకోండి:",
      ["English (Global)", "Telugu (తెలుగు)", "Tenglish"],
  )

  target_audience = st.radio(
      "Target Audience / ఆడియన్స్ రకం:",
      [
          "Regional / Local Audience",
          "Global / International Audience",
          "Both (Global + Regional)",
      ],
  )

  st.markdown("---")
  st.success(
      "🎉 **FREE LAUNCH OFFER!**\n\nUnlimited Deep AI Audits are 100% FREE for"
      " a limited time!"
  )

# --- ప్రధాన పేజీ (Main Header) ---
st.markdown("# 🚀 TrendSutra AI")
st.markdown(
    "**A to Z Growth Analyzer for YouTube, Instagram & TikTok | Powered by"
    " [AIENGTEL.com](https://aiengtel.com)**"
)

st.info(
    "🎁 **Special Launch Access:** Enjoy unlimited real-data AI Growth Audits"
    " for free!"
)

# --- ఇన్‌పుట్ విభాగం (Platform & Link) ---
col1, col2 = st.columns([1, 2])
with col1:
  platform = st.selectbox(
      "Select Platform:", ["YouTube", "Instagram Reels", "TikTok"]
  )
with col2:
  video_url = st.text_input(
      "Channel / Profile / Video Link:",
      placeholder="https://youtu.be... లేదా Reel / TikTok లింక్ పేస్ట్ చేయండి",
  )


# --- డేటా సేకరణ ఫంక్షన్లు (Safe Fetching without JSON Crash) ---
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
    if not vid_res.get("items"):
      return None, "ఈ వీడియో వివరాలు దొరకలేదు (ప్రైవేట్ వీడియో కావచ్చు)."

    item = vid_res["items"][0]
    snippet = item["snippet"]
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
      for c in com_res.get("items", []):
        comments.append(
            c["snippet"]["topLevelComment"]["snippet"]["textDisplay"]
        )
    except Exception:
      comments.append("కామెంట్లు ఆఫ్ చేసి ఉన్నాయి.")

    summary = (
        f"Title: {snippet.get('title')}\n"
        f"Views: {stats.get('viewCount', '0')}, Likes:"
        f" {stats.get('likeCount', '0')}, Comments:"
        f" {stats.get('commentCount', '0')}\n"
        f"Description: {snippet.get('description', '')[:800]}\n"
        f"Tags: {snippet.get('tags', [])}\n"
        f"Top Comments: {comments}"
    )
    return summary, stats
  except Exception as e:
    return None, f"YouTube API లోపం: {str(e)}"


def fetch_rapidapi_safe(api_url, host, params, fallback_label):
  try:
    headers = {"x-rapidapi-key": RAPIDAPI_KEY, "x-rapidapi-host": host}
    res = requests.get(api_url, headers=headers, params=params, timeout=15)
    # ఖాళీ రెస్పాన్స్ చెక్ (Expecting value line 1 column 1 ఎర్రర్ రాకుండా ఆపుతుంది)
    if res.status_code == 200 and res.text and res.text.strip():
      return f"{fallback_label} Data:\n{res.text[:3500]}"
    return (
        f"{fallback_label} URL provided (API returned empty/rate-limited"
        f" status {res.status_code}). Analyze based on URL structure & niche."
    )
  except Exception as e:
    return f"{fallback_label} URL provided (Fetch note: {str(e)})."


def generate_growth_report(platform_name, raw_data, lang, audience):
  prompt = f"""
    You are an elite {platform_name} Growth Strategist and Viral Content Architect.
    Analyze the following data and create a comprehensive, actionable A-to-Z Growth Audit Report.
    
    - Output Language: {lang} (Write strictly in this language; if Telugu, use natural, clear Telugu).
    - Target Audience Focus: {audience}
    
    Source Data:
    {raw_data}
    
    Structure the report clearly into these 5 sections:
    1. 📊 **Audience Pulse & Sentiment (ప్రేక్షకుల నాడి):** Key questions, pain points, and emotional triggers from the audience.
    2. 🪝 **Viral Hook & Next 3 Video Ideas:** High-CTR titles, thumbnail concepts, and first 3-second hooks tailored for {audience}.
    3. 💰 **Monetization Blueprint (ఆదాయ మార్గాలు):** Specific digital products, courses, brand deals, or affiliate angles this audience will pay for.
    4. 🔍 **SEO, Caption & Hashtag Optimization:** Exact improvements to titles, descriptions, and discoverability tags.
    5. 🚀 **30-Day Growth Action Plan:** 3 immediate steps to double engagement and shares.
    """
  last_err = ""
  for key in GEMINI_KEYS:
    client = genai.Client(api_key=key)
    for model_name in ["gemini-3.5-flash-lite", "gemini-3.8-flash"]:
      try:
        resp = client.models.generate_content(model=model_name, contents=prompt)
        return resp.text
      except Exception as e:
        last_err = str(e)
        continue
  return f"⚠️ AI సర్వర్ ప్రస్తుతం బిజీగా ఉంది. దయచేసి కొద్దిసేపటి తర్వాత ప్రయత్నించండి. ({last_err})"


# --- ఎరుపు రంగు బటన్ (Red Action Button) ---
st.markdown(
    """
<style>
div.stButton > button:first-child {
    background-color: #c92a2a;
    color: white;
    font-weight: bold;
    border-radius: 6px;
    padding: 0.5rem 1.2rem;
    border: none;
}
div.stButton > button:first-child:hover {
    background-color: #a61e1e;
    color: white;
}
</style>
""",
    unsafe_allow_html=True,
)

if st.button("Generate Accurate Growth Report 🔍"):
  if not video_url.strip():
    st.warning("⚠️ దయచేసి ముందుగా వీడియో లేదా ప్రొఫైల్ లింక్ పేస్ట్ చేయండి.")
  else:
    data_text = ""
    stats_obj = None

    with st.spinner(f"{platform} నుండి డేటా సేకరిస్తోంది..."):
      if platform == "YouTube":
        data_text, stats_obj = fetch_youtube_info(video_url.strip())
      elif platform == "Instagram Reels":
        data_text = fetch_rapidapi_safe(
            "https://rapidapi.com",
            "://rapidapi.com",
            {"reel_post_code_or_url": video_url.strip()},
            f"Instagram Reel ({video_url.strip()})",
        )
      elif platform == "TikTok":
        data_text = fetch_rapidapi_safe(
            "https://rapidapi.com",
            "://rapidapi.com",
            {"url": video_url.strip()},
            f"TikTok Video ({video_url.strip()})",
        )

    if platform == "YouTube" and not data_text:
      st.error(f"⚠️ {stats_obj}")
    else:
      if platform == "YouTube" and isinstance(stats_obj, dict):
        m1, m2, m3 = st.columns(3)
        m1.metric("👀 Views", f"{int(stats_obj.get('viewCount', 0)):,}")
        m2.metric("👍 Likes", f"{int(stats_obj.get('likeCount', 0)):,}")
        m3.metric("💬 Comments", f"{int(stats_obj.get('commentCount', 0)):,}")

      with st.spinner("TrendSutra AI లోతుగా విశ్లేషిస్తోంది..."):
        report = generate_growth_report(
            platform, data_text, report_lang, target_audience
        )
        st.success("✅ Growth Audit Report సిద్ధమైంది!")
        st.markdown(report)
