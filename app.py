import streamlit as st
from google import genai
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

# 2. Gemini API Auto-Rotation Function (Updated SDK)
def generate_with_rotation(prompt):
    api_keys = [
        st.secrets.get("GEMINI_API_KEY"),
        st.secrets.get("GEMINI_API_KEY_2")
    ]
    api_keys = [k for k in api_keys if k]
    
    if not api_keys:
        return "⚠️ API Key కనుగొనబడలేదు! దయచేసి Streamlit Cloud -> Settings -> Secrets లో GEMINI_API_KEY ని యాడ్ చేయండి."

    last_error = ""
    for key in api_keys:
        try:
            client = genai.Client(api_key=key)
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
            )
            return response.text
        except Exception as e:
            last_error = str(e)
            continue
    return f"⚠️ API Error: {last_error}"

# 3. Safe PDF Generation Function (Fixed AttributeError)
def create_pdf(report_text, platform, username):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    pdf.cell(0, 10, text=f"CreatorPulse AI - Growth Report ({platform})", new_x="LMARGIN", new_y="NEXT", align='C')
    pdf.cell(0, 10, text=f"Account: {username} | Powered by AIENGTEL.com", new_x="LMARGIN", new_y="NEXT", align='C')
    pdf.ln(8)
    # తెలుగు/ప్రాంతీయ అక్షరాల వల్ల PDF క్రాష్ అవ్వకుండా సురక్షితంగా మార్చడం
    clean_text = report_text.encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 8, text=clean_text)
    return bytes(pdf.output())

# 4. Sidebar - Global & Regional Settings + AIENGTEL Branding
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
            Profile/Video Link: {handle}
            Niche: {niche if niche else 'General Content Creation'}
            Target Audience Scope: {audience_type}
            Output Language: {selected_lang}

            Provide a comprehensive, actionable A-to-Z growth report strictly in {selected_lang}.
            Structure the report with these sections:
            1. **Profile & Content Optimization** (Tailored for {audience_type}).
            2. **3 Viral Content & Hook Ideas** (Culturally relevant to the target audience).
            3. **SEO, Keywords & Hashtag Strategy** (Mix of local/regional and global trending tags).
            4. **Best Posting Times & Consistency Plan**.
            5. **Monetization & Brand Deal Roadmap**.
            
            Make it practical, encouraging, and easy to read with bullet points.
            """
            
            report = generate_with_rotation(prompt)
            
            if report.startswith("⚠️"):
                st.error(report)
            else:
                st.success("✅ Your Custom Growth Report is Ready!")
                st.markdown(report)
                
                if is_pro:
                    try:
                        pdf_bytes = create_pdf(report, platform, handle)
                        st.download_button(
                            label="📥 Download Full Report as PDF (Free Launch Gift)",
                            data=pdf_bytes,
                            file_name="CreatorPulse_Growth_Report.pdf",
                            mime="application/pdf"
                        )
                    except Exception as pdf_err:
                        st.warning(f"PDF download skipped: {pdf_err}")
