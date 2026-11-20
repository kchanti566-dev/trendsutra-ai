import streamlit as st
from google import genai
import requests
import re
from fpdf import FPDF

# ==========================================
# ⚙️ LAUNCH SETTINGS
# ==========================================
FREE_LAUNCH_MODE = True  # కొన్ని రోజుల తర్వాత False చేస్తే Pro Plan ఆన్ అవుతుంది

# 1. Page Configuration
st.set_page_config(
    page_title="CreatorPulse AI by AIENGTEL - Global & Regional Growth Analyzer",
    page_icon="🚀",
    layout="wide"
)

# 2. Fast YouTube Video/Channel Info Fetcher (1 సెకనులో డేటా తెస్తుంది)
def get_youtube_context(url_or_handle):
    yt_key = st.secrets.get("YOUTUBE_API_KEY")
    if not yt_key:
        return ""
    try:
        # వీడియో ID తీయడం (youtu.be లేదా youtube.com లింక్ నుండి)
        vid_match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11}).*", url_or_handle)
        if vid_match:
            video_id = vid_match.group(1)
            api_url = f"https://googleapis.com{video_id}&key={yt_key}"
            res = requests.get(api_url, timeout=4).json()
            if res.get("items"):
                item = res["items"][0]
                snippet = item["snippet"]
                stats = item["statistics"]
                return (
                    f"Real Video Title: {snippet.get('title')} | "
                    f"Channel: {snippet.get('channelTitle')} | "
                    f"Views: {stats.get('viewCount', 'N/A')}, Likes: {stats.get('likeCount', 'N/A')}"
                )
    except Exception:
        pass
    return ""

# 3. Ultra-Fast Gemini API Auto-Rotation Function
def generate_fast_report(prompt):
    api_keys = [
        st.secrets.get("GEMINI_API_KEY"),
        st.secrets.get("GEMINI_API_KEY_2")
    ]
    api_keys = [k for k in api_keys if k]
    
    if not api_keys:
        return "⚠️ API Key కనుగొనబడలేదు! Streamlit Secrets లో GEMINI_API_KEY ని యాడ్ చేయండి."

    last_error = ""
    for key in api_keys:
        try:
            client = genai.Client(api_key=key)
            response = client.models.generate_content(
                model="gemini-3.8-flash",
                contents=prompt,
            )
            return response.text
        except Exception as e:
            last_error = str(e)
            continue
    return f"⚠️ API Error: {last_error}"

# 4. Safe PDF Generation Function
def create_pdf(report_text, platform, username):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    pdf.cell(0, 10, text=f"CreatorPulse AI - Growth Report ({platform})", new_x="LMARGIN", new_y="NEXT", align='C')
    pdf.cell(0, 10, text=f"Account: {username} | Powered by AIENGTEL.com", new_x="LMARGIN", new_y="NEXT", align='C')
    pdf.ln(8)
    clean_text = report_text.encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 8, text=clean_text)
    return bytes(pdf.output())

# 5. Sidebar - Global & Regional Settings + AIENGTEL Branding
with st.sidebar:
    st.title("🌍 Global & Regional Settings")
    
    selected_lang = st.selectbox(
        "Report Language / భాషను ఎంచుకోండి:",
        [
            "English (Global)", 
            "Telugu (తెలుగు)", 
            "Hindi (हिंदी)", 
            "Tamil (தமிழ்)", 
            "Kannada (ಕನ್ನಡ)",
            "Malayalam (മലയാളം)",
            "Spanish (Español)"
        ]
    )
    
    audience_type = st.radio(
        "Target Audience / ఆడియన్స్ రకం:",
        ["Regional / Local Audience", "Global / International Audience", "Both (Global + Regional)"]
    )
    
    st.divider()
    
    if FREE_LAUNCH_MODE:
        st.success("🎉 **FREE LAUNCH OFFER!**\nAll Pro features & PDF downloads are 100% FREE for a limited time!")
        is_pro = True
    else:
        region = st.radio("Select Currency:", ["India (₹ INR)", "International ($ USD)"])
        if region == "India (₹ INR)":
            st.info("💎 **Pro Plan: ₹199 / month**\n- Unlimited Audits & PDF Reports")
            st.markdown("[👉 Pay ₹199 via UPI / Razorpay](https://your-razorpay-link.com)")
        else:
            st.info("💎 **Pro Plan: $5 / month**\n- Unlimited Audits & PDF Reports")
            st.markdown("[👉 Pay $5 via International Card](https://your-international-link.com)")
        
        pro_code = st.text_input("Enter Pro Access Code:", type="password")
        is_pro = True if pro_code == "CREATORPRO2026" else False

    st.divider()
    st.markdown("### 🔗 Explore More AI Tools")
    st.markdown("Discover 100+ Best AI Tools in **English & తెలుగు** at **[AIENGTEL.com](https://aiengtel.com)** 🚀")

# 6. Main App Interface
st.title("🚀 CreatorPulse AI")
st.markdown("##### A to Z Growth Analyzer for YouTube, Instagram & TikTok | Powered by **[AIENGTEL.com](https://aiengtel.com)**")

if FREE_LAUNCH_MODE:
    st.info("🎁 **Special Launch Access:** Enjoy unlimited AI Growth Audits & Free PDF Downloads for the next few days!")

col1, col2, col3 = st.columns(3)
with col1:
    platform = st.selectbox("Select Platform:", ["YouTube", "Instagram", "TikTok"])
with col2:
    handle = st.text_input("Channel / Profile / Video Link:", placeholder="@username or video link")
with col3:
    niche = st.text_input("Content Niche / Category:", placeholder="e.g., Tech, Vlogs, Cooking, Gaming")

if st.button("Generate Free Growth Report 🔍", type="primary"):
    if not handle:
        st.warning("Please enter a valid username or link!")
    else:
        with st.spinner("⚡ Generating fast AI Growth Report..."):
            live_data = get_youtube_context(handle) if platform == "YouTube" else ""
            
            prompt = f"""
            Act as an expert Social Media Growth Strategist. Give a crisp, high-impact A-to-Z growth report strictly in {selected_lang}.
            Platform: {platform}
            Input Link/Handle: {handle}
            {live_data}
            Niche: {niche if niche else 'General'}
            Target Audience: {audience_type}

            Keep each section concise (3-4 bullet points max per section) for fast reading:
            1. **Profile / Video Audit & Optimization**
            2. **3 Viral Hook & Content Ideas**
            3. **SEO Keywords & Hashtags**
            4. **Best Posting Time & Growth Hack**
            5. **Monetization Tip**
            """
            
            report = generate_fast_report(prompt)
            
            if report.startswith("⚠️"):
                st.error(report)
            else:
                st.success("✅ Report Generated!")
                if live_data:
                    st.caption(f"📊 Fetched Live Stats: {live_data}")
                st.markdown(report)
                
                if is_pro:
                    try:
                        pdf_bytes = create_pdf(report, platform, handle)
                        st.download_button(
                            label="📥 Download Report as PDF",
                            data=pdf_bytes,
                            file_name="CreatorPulse_Report.pdf",
                            mime="application/pdf"
                        )
                    except Exception:
                        pass
