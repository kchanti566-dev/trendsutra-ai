import streamlit as st
import google.generativeai as genai
import requests
from fpdf import FPDF

# ==========================================
# ⚙️ LAUNCH SETTINGS (Free Launch vs Paid Pro)
# ==========================================
FREE_LAUNCH_MODE = True  # కొన్ని రోజుల తర్వాత దీనిని False అని మారిస్తే Pro Plan ఆన్ అవుతుంది!

# 1. Page Configuration
st.set_page_config(
    page_title="CreatorPulse AI by AIENGTEL - Global & Regional Growth Analyzer",
    page_icon="🚀",
    layout="wide"
)

# 2. Gemini API Auto-Rotation Function
def generate_with_rotation(prompt):
    api_keys = [
        st.secrets.get("GEMINI_API_KEY"),
        st.secrets.get("GEMINI_API_KEY_2")
    ]
    api_keys = [k for k in api_keys if k]
    
    for key in api_keys:
        try:
            genai.configure(api_key=key)
            model = genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            continue # మొదటి కీ లిమిట్ అయిపోతే రెండో కీకి మారుతుంది
    return "Error: Server is busy due to high traffic. Please try again in a minute."

# 3. PDF Generation Function
def create_pdf(report_text, platform, username):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"CreatorPulse AI - Growth Report ({platform})", ln=True, align='C')
    pdf.cell(200, 10, txt=f"Account: {username} | Powered by AIENGTEL.com", ln=True, align='C')
    pdf.ln(10)
    clean_text = report_text.encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 8, txt=clean_text)
    return pdf.output(dest="S").encode("latin-1")

# 4. Sidebar - Global & Regional Settings + AIENGTEL Branding
with st.sidebar:
    st.title("🌍 Global & Regional Settings")
    
    # భాష ఎంపిక (AIENGTEL మాదిరిగానే English & Telugu ముఖ్యంగా, ఇతర భాషలతో పాటు)
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
    
    # Free Launch Offer vs Paid Pro Plan Logic
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

# 5. Main App Interface
st.title("🚀 CreatorPulse AI")
st.markdown("##### A to Z Growth Analyzer for YouTube, Instagram & TikTok | Powered by **[AIENGTEL.com](https://aiengtel.com)**")

if FREE_LAUNCH_MODE:
    st.info("🎁 **Special Launch Access:** Enjoy unlimited AI Growth Audits & Free PDF Downloads for the next few days!")

col1, col2, col3 = st.columns(3)
with col1:
    platform = st.selectbox("Select Platform:", ["YouTube", "Instagram", "TikTok"])
with col2:
    handle = st.text_input("Channel / Profile Username:", placeholder="@username or link")
with col3:
    niche = st.text_input("Content Niche / Category:", placeholder="e.g., Tech, Vlogs, Cooking, Gaming")

if st.button("Generate Free Growth Report 🔍", type="primary"):
    if not handle:
        st.warning("Please enter a valid username or channel link!")
    else:
        with st.spinner(f"Analyzing {handle} for {audience_type} in {selected_lang}..."):
            prompt = f"""
            Act as an expert Global & Regional Social Media Growth Strategist. Analyze this creator profile:
            Platform: {platform}
            Profile: {handle}
            Niche: {niche}
            Target Audience Scope: {audience_type}
            Output Language: {selected_lang}

            Provide a comprehensive, actionable A-to-Z growth report strictly in {selected_lang}.
            Structure the report with these sections:
            1. **Profile & Bio Optimization** (Tailored for {audience_type}).
            2. **3 Viral Content & Hook Ideas** (Culturally relevant to the target audience).
            3. **SEO, Keywords & Hashtag Strategy** (Mix of local/regional and global trending tags).
            4. **Best Posting Times & Consistency Plan**.
            5. **Monetization & Brand Deal Roadmap**.
            
            Make it practical, encouraging, and easy to read with bullet points.
            """
            
            report = generate_with_rotation(prompt)
            
            st.success("✅ Your Custom Growth Report is Ready!")
            st.markdown(report)
            
            if is_pro:
                pdf_bytes = create_pdf(report, platform, handle)
                st.download_button(
                    label="📥 Download Full Report as PDF (Free Launch Gift)",
                    data=pdf_bytes,
                    file_name=f"{handle}_CreatorPulse_Report.pdf",
                    mime="application/pdf"
                )
