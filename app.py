import re
from fpdf import FPDF
from google import genai
from googleapiclient.discovery import build
import requests
import streamlit as st

st.set_page_config(
    page_title="CreatorPulse by AIENGTEL - Free AI Growth Analyzer",
    page_icon="🚀",
    layout="wide",
)

with st.sidebar:
  st.header("🚀 CreatorPulse AI")
  st.caption("Powered by **AIENGTEL.com**")
  st.divider()
  st.success("🎉 **Limited Time Free Launch!**")
  st.write(
      "✅ YouTube, Instagram & TikTok ఆటోమేటిక్ విశ్లేషణ\n✅ Global & Regional"
      " గ్రోత్ స్ట్రాటజీ\n✅ ఉచిత PDF డౌన్‌లోడ్"
  )
  st.divider()
  st.markdown("🌐 [Explore AI Tools on AIENGTEL](https://aiengtel.com)")

st.title("🚀 CreatorPulse by AIENGTEL")
st.subheader("YouTube, Instagram & TikTok (A to Z Growth Analyzer)")
st.write(
    "ఏదైనా వీడియో లింక్ ఇవ్వండి—గ్లోబల్ & రీజనల్ స్థాయిలో ప్రేక్షకుల నాడి,"
    " వైరల్ ఐడియాలు, మరియు ఆదాయ మార్గాలను AI విశ్లేషిస్తుంది!"
)

GEMINI_KEYS = [
    st.secrets["GEMINI_API_KEY"],
    st.secrets["GEMINI_API_KEY_2"],
]
YOUTUBE_KEY = st.secrets["YOUTUBE_API_KEY"]
RAPIDAPI_KEY = st.secrets["RAPIDAPI_API_KEY"]

output_lang = st.selectbox(
    "రిపోర్ట్ ఏ భాషలో కావాలి?", ["Telugu (తెలుగు)", "Tenglish", "English"]
)


# 1. YouTube Helpers
def extract_youtube_id(url):
  pattern = r"(?:v=|\/|live\/|shorts\/)([0-9A-Za-z_-]{11}).*"
  match = re.search(pattern, url)
  return match.group(1) if match else None


def get_youtube_data(video_id):
  youtube = build("youtube", "v3", developerKey=YOUTUBE_KEY)
  vid_response = (
      youtube.videos().list(part="snippet,statistics", id=video_id).execute()
  )
  if not vid_response["items"]:
    return None
  snippet = vid_response["items"][0]["snippet"]
  stats = vid_response["items"][0]["statistics"]

  comments = []
  try:
    com_response = (
        youtube.commentThreads()
        .list(
            part="snippet",
            videoId=video_id,
            maxResults=50,
            order="relevance",
            textFormat="plainText",
        )
        .execute()
    )
    for item in com_response["items"]:
      comments.append(
          item["snippet"]["topLevelComment"]["snippet"]["textDisplay"]
      )
  except Exception:
    comments.append("కామెంట్లు ఆఫ్ చేసి ఉన్నాయి.")

  return {
      "title": snippet["title"],
      "description": snippet["description"][:1000],
      "tags": snippet.get("tags", []),
      "views": stats.get("viewCount", "0"),
      "likes": stats.get("likeCount", "0"),
      "comment_count": stats.get("commentCount", "0"),
      "comments": comments,
  }


# 2. Instagram Helpers
def extract_insta_code(url):
  pattern = r"(?:reel|p|tv)\/([A-Za-z0-9_-]+)"
  match = re.search(pattern, url)
  return match.group(1) if match else None


def get_insta_data(media_code):
  url = "https://rapidapi.com"
  headers = {
      "x-rapidapi-key": RAPIDAPI_KEY,
      "x-rapidapi-host": "://rapidapi.com",
  }
  res = requests.get(
      url, headers=headers, params={"media_code": media_code}, timeout=20
  )
  if res.status_code == 200:
    return str(res.json())[:4500]
  return None


# 3. TikTok Helpers
def extract_tiktok_id(url):
  # షార్ట్ లింక్ (://tiktok.com / ://tiktok.com) అయితే అసలు లింక్‌కు రీడైరెక్ట్ చేస్తుంది
  if "://tiktok.com" in url or "://tiktok.com" in url:
    try:
      r = requests.head(url, allow_redirects=True, timeout=10)
      url = r.url
    except Exception:
      pass
  pattern = r"\/video\/(\d+)"
  match = re.search(pattern, url)
  return match.group(1) if match else None


def get_tiktok_data(video_id):
  url = f"https://rapidapi.com{video_id}"
  headers = {
      "x-rapidapi-key": RAPIDAPI_KEY,
      "x-rapidapi-host": (
          "://rapidapi.com"
      ),
  }
  res = requests.get(url, headers=headers, timeout=20)
  if res.status_code == 200:
    return str(res.json())[:4500]
  return None


# 4. AI Report Generator (Global & Regional Level)
def generate_ai_report(platform, data_text, lang):
  prompt = f"""
    నువ్వు ఒక వరల్డ్-క్లాస్ {platform} గ్రోత్ మరియు వైరల్ కంటెంట్ స్ట్రాటజిస్ట్‌వి.
    క్రింది వీడియో డేటాను (భాష, దేశం, ప్రాంతం, ప్రేక్షకుల స్పందన) లోతుగా విశ్లేషించి, {lang} భాషలో A to Z గ్రోత్ రిపోర్ట్ తయారు చెయ్యి.
    ఈ కంటెంట్ ఏ రీజియన్ (Regional - ఉదా: తెలుగు/ఇండియా/లోకల్) లేదా గ్లోబల్ (Global) ఆడియన్స్ కోసం ఉందో గుర్తించి, దానికి తగ్గట్టుగా స్ట్రాటజీ ఇవ్వు.
    
    డేటా: {data_text}
    
    ఈ 5 విభాగాలలో స్పష్టమైన సమాధానం ఇవ్వు:
    1. 🌍 రీజనల్ & గ్లోబల్ ఆడియన్స్ నాడి (Audience Sentiment, Language/Region Reach & Top Questions)
    2. 🪝 వైరల్ హుక్ & తర్వాతి 3 వీడియో ఐడియాలు (టైటిల్ / థంబ్‌నెయిల్ / స్క్రిప్ట్ ఐడియాతో)
    3. 💰 ఆదాయ మార్గం (Local & Global Monetization / Brand Deals / Affiliate Idea)
    4. 🔍 SEO, క్యాప్షన్ & హ్యాష్‌ట్యాగ్ మెరుగుదలలు (Regional + Global Tags)
    5. 🚀 ఎంగేజ్‌మెంట్ పెంచే ప్రో-టిప్
    """
  last_error = ""
  for key in GEMINI_KEYS:
    client = genai.Client(api_key=key)
        for model_name in [
        "gemini-3.5-flash-lite",
        "gemini-3.5-flash",
        "gemini-3-flash-preview",
    ]:
      try:
        response = client.models.generate_content(
            model=model_name, contents=prompt
        )
        return response.text
      except Exception as e:
        last_error = str(e)
        continue
  return f"⚠️ అన్ని API కీల పరిమితి పూర్తయింది: {last_error}"


def create_pdf(report_text):
  pdf = FPDF()
  pdf.add_page()
  pdf.set_font("Arial", size=11)
  clean_text = report_text.encode("latin-1", "replace").decode("latin-1")
  pdf.multi_cell(0, 8, txt=clean_text)
  return bytes(pdf.output())


def display_full_report(report_text):
  st.markdown(report_text)
  st.download_button(
      label="📥 Download Full Report (PDF)",
      data=create_pdf(report_text),
      file_name="CreatorPulse_Growth_Report.pdf",
      mime="application/pdf",
  )


tab1, tab2, tab3 = st.tabs(["🎬 YouTube", "📱 Instagram Reels", "🎵 TikTok"])

with tab1:
  yt_url = st.text_input(
      "🔗 YouTube వీడియో లేదా Shorts లింక్:", placeholder="https://youtu.be..."
  )
  if st.button("🚀 YouTube విశ్లేషణ ప్రారంభించు"):
    vid_id = extract_youtube_id(yt_url) if yt_url else None
    if not vid_id:
      st.error("దయచేసి సరైన YouTube వీడియో లేదా Shorts లింక్ ఇవ్వండి.")
    else:
      with st.spinner("YouTube డేటా సేకరిస్తోంది..."):
        info = get_youtube_data(vid_id)
      if info:
        c1, c2, c3 = st.columns(3)
        c1.metric("👀 Views", info["views"])
        c2.metric("👍 Likes", info["likes"])
        c3.metric("💬 Comments", info["comment_count"])
        with st.spinner("Global & Regional AI రిపోర్ట్ తయారు చేస్తోంది..."):
          raw_data = (
              f"Title: {info['title']}\nDesc:"
              f" {info['description']}\nTags: {info['tags']}\nComments:"
              f" {info['comments']}"
          )
          display_full_report(
              generate_ai_report("YouTube", raw_data, output_lang)
          )
      else:
        st.error("ఈ వీడియో వివరాలు లభించలేదు. పబ్లిక్ వీడియో లింక్ ఇవ్వండి.")

with tab2:
  insta_url = st.text_input(
      "🔗 Instagram Reel లేదా Post లింక్:",
      placeholder="https://instagram.com...",
  )
  if st.button("🔥 Instagram విశ్లేషణ ప్రారంభించు"):
    media_code = extract_insta_code(insta_url) if insta_url else None
    if not media_code:
      st.error("దయచేసి సరైన Instagram Reel లేదా Post లింక్ ఇవ్వండి.")
    else:
      with st.spinner("Instagram డేటా సేకరిస్తోంది..."):
        insta_data = get_insta_data(media_code)
      if insta_data:
        with st.spinner("Global & Regional AI రిపోర్ట్ తయారు చేస్తోంది..."):
          display_full_report(
              generate_ai_report("Instagram Reels", insta_data, output_lang)
          )
      else:
        st.error(
            "Instagram డేటా పొందడంలో సమస్య వచ్చింది (ప్రైవేట్ అకౌంట్ లేదా API"
            " పరిమితి అయి ఉండవచ్చు)."
        )

with tab3:
  tiktok_url = st.text_input(
      "🔗 TikTok వీడియో లింక్:",
      placeholder="https://tiktok.com...",
  )
  if st.button("🎵 TikTok విశ్లేషణ ప్రారంభించు"):
    tt_id = extract_tiktok_id(tiktok_url) if tiktok_url else None
    if not tt_id:
      st.error("దయచేసి సరైన TikTok వీడియో లింక్ ఇవ్వండి.")
    else:
      with st.spinner("TikTok డేటా సేకరిస్తోంది..."):
        tt_data = get_tiktok_data(tt_id)
      if tt_data:
        with st.spinner("Global & Regional AI రిపోర్ట్ తయారు చేస్తోంది..."):
          display_full_report(
              generate_ai_report("TikTok", tt_data, output_lang)
          )
      else:
        st.error(
            "TikTok డేటా పొందడంలో సమస్య వచ్చింది (లింక్ చెక్ చేయండి లేదా API"
            " పరిమితి పూర్తయి ఉండవచ్చు)."
        )
