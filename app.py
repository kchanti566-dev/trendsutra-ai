import re
from fpdf import FPDF
from google import genai
from googleapiclient.discovery import build
import streamlit as st

st.set_page_config(
    page_title="CreatorPulse by AIENGTEL - Free AI Growth Analyzer",
    page_icon="🚀",
    layout="wide",
)

with st.sidebar:
  st.image("https://icons8.com", width=60)
  st.title("CreatorPulse AI")
  st.caption("Powered by **AIENGTEL.com**")
  st.divider()
  st.success("🎉 **Limited Time Free Launch!**")
  st.write(
      "✅ పూర్తి 5-స్టెప్ A-to-Z గ్రోత్ రిపోర్ట్\n✅ ఆదాయ మార్గాలు & SEO"
      " సీక్రెట్స్\n✅ ఉచిత PDF డౌన్‌లోడ్"
  )
  st.divider()
  st.markdown("🌐 [Explore AI Tools on AIENGTEL](https://aiengtel.com)")

st.title("🚀 CreatorPulse by AIENGTEL")
st.subheader("YouTube, Instagram & TikTok (A to Z Growth Analyzer)")
st.write(
    "ఏదైనా వీడియో లింక్ ఇవ్వండి—ప్రేక్షకుల నాడి, వైరల్ ఐడియాలు, మరియు ఆదాయ"
    " మార్గాలను AI ఉచితంగా విశ్లేషిస్తుంది!"
)

GEMINI_KEYS = [
    st.secrets["GEMINI_API_KEY"],
    st.secrets["GEMINI_API_KEY_2"],
]
YOUTUBE_KEY = st.secrets["YOUTUBE_API_KEY"]

output_lang = st.selectbox(
    "రిపోర్ట్ ఏ భాషలో కావాలి?", ["Telugu (తెలుగు)", "Tenglish", "English"]
)


def extract_video_id(url):
  pattern = r"(?:v=|\/|live\/|shorts\/)([0-9A-Za-z_-]{11}).*"
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
  last_error = ""
  for key in GEMINI_KEYS:
    client = genai.Client(api_key=key)
    for model_name in ["gemini-2.5-flash", "gemini-2.5-flash-lite"]:
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
            report = generate_ai_report("YouTube", raw_data, output_lang)
            display_full_report(report)

with tab2:
  insta_url = st.text_input(
      "🔗 Instagram Reel లింక్:", placeholder="https://instagram.com..."
  )
  insta_caption = st.text_area(
      "📝 Reel క్యాప్షన్ / వివరాలు (ఐచ్ఛికం - మంచి ఫలితాల కోసం):",
      height=80,
  )
  if st.button("🔥 Instagram Reel విశ్లేషణ ప్రారంభించు"):
    if not insta_url:
      st.error("దయచేసి Instagram Reel లింక్ ఇవ్వండి.")
    else:
      with st.spinner("AI Instagram రిపోర్ట్ తయారు చేస్తోంది..."):
        fetched_text = f"Reel Link: {insta_url}\nCaption: {insta_caption}"
        report = generate_ai_report(
            "Instagram Reels", fetched_text, output_lang
        )
        display_full_report(report)

with tab3:
  tiktok_url = st.text_input(
      "🔗 TikTok వీడియో లింక్:", placeholder="https://tiktok.com..."
  )
  tt_caption = st.text_area(
      "📝 TikTok క్యాప్షన్ / వివరాలు (ఐచ్ఛికం):", height=80
  )
  if st.button("🎵 TikTok విశ్లేషణ ప్రారంభించు"):
    if not tiktok_url:
      st.error("దయచేసి TikTok లింక్ ఇవ్వండి.")
    else:
      with st.spinner("AI TikTok రిపోర్ట్ తయారు చేస్తోంది..."):
        fetched_tt = f"TikTok Link: {tiktok_url}\nCaption: {tt_caption}"
        report = generate_ai_report("TikTok", fetched_tt, output_lang)
        display_full_report(report)
