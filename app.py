import re
import time
from googleapiclient.discovery import build
import google.generativeai as genai
import requests
import streamlit as st

st.set_page_config(
    page_title="CreatorPulse AI - Growth Analyzer", page_icon="🚀", layout="wide"
)
st.title("🚀 YouTube, Instagram & TikTok AI (A to Z Growth Analyzer)")
st.write(
    "ఏదైనా వీడియో లింక్ ఇవ్వండి—ప్రేక్షకుల నాడి, వైరల్ ఐడియాలు, మరియు ఆదాయ"
    " మార్గాలను AI చెప్తుంది!"
)

# API కీలు Streamlit Secrets నుండి రహస్యంగా వస్తాయి
GEMINI_KEY = st.secrets["GEMINI_API_KEY"]
YOUTUBE_KEY = st.secrets["YOUTUBE_API_KEY"]
RAPIDAPI_KEY = st.secrets["RAPIDAPI_API_KEY"]

output_lang = st.selectbox(
    "రిపోర్ట్ ఏ భాషలో కావాలి?", ["Telugu (తెలుగు)", "Tenglish", "English"]
)


def extract_video_id(url):
  pattern = r"(?:v=|\/)([0-9A-Za-z_-]{11}).*"
  match = re.search(pattern, url)
  return match.group(1) if match else None


def get_youtube_data(video_id):
  youtube = build("youtube", "v3", developerKey=YOUTUBE_KEY)
  vid_response = (
      youtube.videos().list(part="snippet,statistics", id=video_id).execute()
  )
  if not vid_response["items"]:
    return None, None
  snippet = vid_response["items"][0]["snippet"]
  stats = vid_response["items"][0]["statistics"]
  video_info = {
      "title": snippet["title"],
      "description": snippet["description"][:1000],
      "tags": snippet.get("tags", []),
      "views": stats.get("viewCount", "0"),
      "likes": stats.get("likeCount", "0"),
      "comment_count": stats.get("commentCount", "0"),
  }
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
  return video_info, comments


def generate_ai_report(platform, data_text, lang):
  genai.configure(api_key=GEMINI_KEY)
  prompt = f"""
    నువ్వు ఒక టాప్ {platform} గ్రోత్ మరియు వైరల్ కంటెంట్ స్ట్రాటజిస్ట్‌వి.
    క్రింది వీడియో డేటా మరియు కామెంట్లను లోతుగా విశ్లేషించి, {lang} భాషలో A to Z గ్రోత్ రిపోర్ట్ తయారు చెయ్యి:
    డేటా: {data_text}
    
    ఈ 5 విభాగాలలో స్పష్టమైన సమాధానం ఇవ్వు:
    1. 📊 ప్రేక్షకుల నాడి (Audience Sentiment & Top 5 Questions)
    2. 🪝 వైరల్ హుక్ & తర్వాతి 3 వీడియో ఐడియాలు (టైటిల్ / థంబ్‌నెయిల్ / స్క్రిప్ట్ ఐడియాతో)
    3. 💰 ఆదాయ మార్గం (Monetization / Product / Affiliate Idea)
    4. 🔍 SEO, క్యాప్షన్ & హ్యాష్‌ట్యాగ్ మెరుగుదలలు
    5. 🚀 ఎంగేజ్‌మెంట్ పెంచే ప్రో-టిప్
    """
  models_to_try = [
      "gemini-2.5-flash-lite",
      "gemini-3.8-flash",
      "gemini-2.0-flash-lite",
  ]
  for attempt in range(2):
    for model_name in models_to_try:
      try:
        model = genai.GenerativeModel(model_name)
        return model.generate_content(prompt).text
      except Exception:
        continue
    if attempt == 0:
      st.info("⏳ సర్వర్ బిజీగా ఉంది, 20 సెకన్లు వేచి ఉండి మళ్ళీ ప్రయత్నిస్తోంది...")
      time.sleep(20)
  return "⚠️ ప్రస్తుతం ఎక్కువ మంది యూజర్లు వాడుతున్నారు. దయచేసి కొద్దిసేపటి తర్వాత ప్రయత్నించండి."


tab1, tab2, tab3 = st.tabs(["🎬 YouTube", "📱 Instagram Reels", "🎵 TikTok"])

with tab1:
  yt_url = st.text_input(
      "🔗 YouTube వీడియో లింక్:", placeholder="https://youtu.be..."
  )
  if st.button("🚀 YouTube విశ్లేషణ ప్రారంభించు"):
    if not yt_url:
      st.error("దయచేసి YouTube లింక్ ఇవ్వండి.")
    else:
      vid_id = extract_video_id(yt_url)
      if not vid_id:
        st.error("సరైన YouTube లింక్ ఇవ్వండి.")
      else:
        with st.spinner("YouTube డేటా సేకరిస్తోంది..."):
          info, comments = get_youtube_data(vid_id)
        if info:
          c1, c2, c3 = st.columns(3)
          c1.metric("👀 Views", info["views"])
          c2.metric("👍 Likes", info["likes"])
          c3.metric("💬 Comments", info["comment_count"])
          with st.spinner("AI రిపోర్ట్ తయారు చేస్తోంది..."):
            raw_data = (
                f"Title: {info['title']}\nDesc:"
                f" {info['description']}\nTags: {info['tags']}\nComments:"
                f" {comments}"
            )
            st.markdown(generate_ai_report("YouTube", raw_data, output_lang))

with tab2:
  insta_url = st.text_input(
      "🔗 Instagram Reel లింక్:", placeholder="https://instagram.com..."
  )
  if st.button("🔥 Instagram Reel విశ్లేషణ ప్రారంభించు"):
    if not insta_url:
      st.error("దయచేసి Instagram Reel లింక్ ఇవ్వండి.")
    else:
      with st.spinner("Instagram డేటా సేకరిస్తోంది..."):
        fetched_text = f"Reel Link: {insta_url}\n"
        try:
          api_url = "https://rapidapi.com"
          headers = {
              "x-rapidapi-key": RAPIDAPI_KEY,
              "x-rapidapi-host": (
                  "://rapidapi.com"
              ),
          }
          res = requests.get(
              api_url,
              headers=headers,
              params={"reel_post_code_or_url": insta_url},
              timeout=15,
          )
          if res.status_code == 200:
            fetched_text += f"API Data: {str(res.json())[:3500]}"
        except Exception:
          pass
      with st.spinner("AI Instagram రిపోర్ట్ తయారు చేస్తోంది..."):
        st.markdown(
            generate_ai_report("Instagram Reels", fetched_text, output_lang)
        )

with tab3:
  tiktok_url = st.text_input(
      "🔗 TikTok వీడియో లింక్:",
      placeholder="https://tiktok.com...",
  )
  if st.button("🎵 TikTok విశ్లేషణ ప్రారంభించు"):
    if not tiktok_url:
      st.error("దయచేసి TikTok లింక్ ఇవ్వండి.")
    else:
      with st.spinner("TikTok డేటా సేకరిస్తోంది..."):
        fetched_tt = f"TikTok Link: {tiktok_url}\n"
        try:
          tt_api = "https://rapidapi.com"
          headers = {
              "x-rapidapi-key": RAPIDAPI_KEY,
              "x-rapidapi-host": "://rapidapi.com",
          }
          res = requests.get(
              tt_api, headers=headers, params={"url": tiktok_url}, timeout=15
          )
          if res.status_code == 200:
            fetched_tt += f"API Data: {str(res.json())[:3500]}"
        except Exception:
          pass
      with st.spinner("AI TikTok రిపోర్ట్ తయారు చేస్తోంది..."):
        st.markdown(generate_ai_report("TikTok", fetched_tt, output_lang))
