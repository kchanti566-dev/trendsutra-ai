import os
import re
import time
import hashlib
import requests
import streamlit as st
from google import genai
from google.genai import types
from googleapiclient.discovery import build
from streamlit_js_eval import streamlit_js_eval

st.set_page_config(
    page_title='TrendSutra AI - Growth Analyzer',
    page_icon='logo.png' if os.path.isfile('logo.png') else '🚀',
    layout='wide',
    initial_sidebar_state='expanded',
)

st.markdown('''
<style>
#MainMenu, footer, .stDeployButton, div[data-testid='stToolbarActions'],
div[data-testid='stStatusWidget'], div[data-testid='stDecoration'],
a[href*='streamlit.io'], div[class*='viewerBadge'] {
    display: none !important;
    visibility: hidden !important;
}
header[data-testid='stHeader'] { height: 1.2rem !important; background: transparent !important; }
.block-container { padding-top: 0.2rem !important; margin-top: -1.8rem !important; }
section[data-testid='stSidebar'] > div:first-child { padding-top: 0.2rem !important; margin-top: -1.2rem !important; }
section[data-testid='stSidebar'] .stMarkdown p { margin-bottom: 0.25rem !important; line-height: 1.35 !important; }
section[data-testid='stSidebar'] div[data-testid='stRadio'] > div { flex-direction: row !important; gap: 0.6rem !important; }
div.stButton > button:first-child {
    background-color: #c92a2a; color: white; font-weight: bold;
    border-radius: 6px; border: none; padding: 0.45rem 1rem;
}
div.stDownloadButton > button:first-child {
    background-color: #2b8a3e; color: white; font-weight: bold;
    border-radius: 6px; border: none;
}
.loading-pill {
    display: inline-flex; align-items: center; gap: 8px;
    background: #1e293b; color: #38bdf8; border: 1px solid #38bdf8;
    padding: 7px 14px; border-radius: 8px; font-weight: 600; font-size: 0.92rem;
    margin-top: 2px;
}
</style>
''', unsafe_allow_html=True)

GEMINI_KEYS = [
    k.strip() for k in (
        st.secrets.get('GEMINI_API_KEY', ''),
        st.secrets.get('GEMINI_API_KEY_2', ''),
    ) if k and str(k).strip()
]
YOUTUBE_KEY = str(st.secrets.get('YOUTUBE_API_KEY', '')).strip()
GOOGLE_SHEET_API = 'https://script.google.com/macros/s/AKfycbzEkkgxBP7aOKIXkEiOG7_rWc0quvnvTVqQDSWUAMk2zOPN7W8Ue_uOPwH7edmJJtEd/exec'
PAY_1_MONTH_LINK = 'https://rzp.io/rzp/yop8jYS'
PAY_12_MONTHS_LINK = 'https://rzp.io/rzp/sjonGmqw'

def get_client_real_ip():
    try:
        headers = st.context.headers
        xff = headers.get('X-Forwarded-For', '') or headers.get('x-forwarded-for', '')
        if xff:
            ip = xff.split(',')[0].strip()
            if ip and not ip.startswith(('10.', '127.', '172.', '192.168.')):
                return ip
        xri = headers.get('X-Real-Ip', '') or headers.get('x-real-ip', '')
        if xri:
            return xri.strip()
    except Exception:
        pass
    return ''

def get_stable_device_id():
    if 'locked_device_id' in st.session_state and st.session_state.locked_device_id:
        return st.session_state.locked_device_id
    ip = get_client_real_ip()
    ua = ''
    try:
        headers = st.context.headers
        ua = headers.get('User-Agent', '') or headers.get('user-agent', '')
    except Exception:
        ua = ''
    os_sig = 'unknown_os'
    for tag in ('Windows NT 10', 'Windows NT 11', 'Android', 'iPhone', 'iPad', 'Mac OS X', 'Linux'):
        if tag in ua:
            os_sig = tag
            break
    raw_sig = f'{ip}|{os_sig}' if ip else f'ua_only|{ua[:90]}'
    dev_id = 'dev_' + hashlib.sha256(raw_sig.encode('utf-8')).hexdigest()[:16]
    st.session_state.locked_device_id = dev_id
    return dev_id

def fetch_sheet_device_count(dev_id):
    try:
        res = requests.get(
            f'{GOOGLE_SHEET_API}?device={dev_id}&t={int(time.time())}',
            headers={'User-Agent': 'Mozilla/5.0', 'Cache-Control': 'no-cache'},
            allow_redirects=True,
            timeout=10,
        )
        txt = res.text.strip()
        if txt.isdigit():
            return min(3, int(txt))
    except Exception:
        pass
    return None

def increment_sheet_device_count(dev_id):
    try:
        res = requests.get(
            f'{GOOGLE_SHEET_API}?device={dev_id}&inc=1&t={int(time.time())}',
            headers={'User-Agent': 'Mozilla/5.0', 'Cache-Control': 'no-cache'},
            allow_redirects=True,
            timeout=10,
        )
        txt = res.text.strip()
        if txt.isdigit():
            return min(3, int(txt))
    except Exception:
        pass
    return None

def log_usage_to_sheet(dev_id, platform_name, url_str):
    try:
        requests.get(
            GOOGLE_SHEET_API,
            params={'log': '1', 'device': dev_id, 'platform': platform_name, 'url': url_str[:250]},
            headers={'User-Agent': 'Mozilla/5.0'},
            allow_redirects=True,
            timeout=6,
        )
    except Exception:
        pass

DEVICE_ID = get_stable_device_id()
ls_free = streamlit_js_eval(js_expressions="localStorage.getItem('ts_free_v8')", key='ls_f_v8')
ls_pro = streamlit_js_eval(js_expressions="localStorage.getItem('ts_pro_v8')", key='ls_p_v8')

if 'free_used_count' not in st.session_state:
    st.session_state.free_used_count = 0
if 'is_pro_user' not in st.session_state:
    st.session_state.is_pro_user = False

sheet_cnt = fetch_sheet_device_count(DEVICE_ID)
if sheet_cnt is not None and sheet_cnt > st.session_state.free_used_count:
    st.session_state.free_used_count = sheet_cnt

if ls_free and str(ls_free).isdigit():
    local_cnt = min(3, int(ls_free))
    if local_cnt > st.session_state.free_used_count:
        st.session_state.free_used_count = local_cnt

if ls_pro == 'yes' and not st.session_state.is_pro_user:
    st.session_state.is_pro_user = True

def verify_payment_id(pid):
    if not pid:
        return 'INVALID'
    clean_pid = pid.strip()
    owner_key = str(st.secrets.get('OWNER_SECRET_CODE', '')).strip()
    if owner_key and clean_pid == owner_key:
        return 'OWNER_VALID'
    if not clean_pid.startswith('pay_'):
        return 'INVALID'
    try:
        res = requests.get(
            f'{GOOGLE_SHEET_API}?pid={clean_pid}',
            headers={'User-Agent': 'Mozilla/5.0'},
            allow_redirects=True,
            timeout=12,
        )
        txt = res.text.strip()
        if 'ALREADY_USED' in txt:
            return 'ALREADY_USED'
        if 'VALID' in txt:
            return 'VALID'
        return 'INVALID'
    except Exception:
        return 'ERROR'

url_pid = st.query_params.get('razorpay_payment_id', '')
if url_pid and not st.session_state.is_pro_user:
    st_val = verify_payment_id(url_pid)
    if st_val == 'VALID':
        st.session_state.is_pro_user = True
        streamlit_js_eval(js_expressions="localStorage.setItem('ts_pro_v8', 'yes')", key='ls_pro_url_v8')
    elif st_val == 'ALREADY_USED':
        st.sidebar.error('⚠️ ఈ Payment ID గరిష్టంగా 3 డివైజ్‌లలో వాడబడింది!')

with st.sidebar:
    st.markdown('### 🌍 Settings')
    report_lang = st.selectbox('Report Language / భాష:', ('Telugu (తెలుగు)', 'English (Global)', 'Tenglish'))
    target_audience = st.radio('Target Audience:', ('Regional', 'Global', 'Both'))
    st.markdown('### 💎 Pro Plans (Unlimited)')
    if st.session_state.is_pro_user:
        st.success('✅ **PRO UNLIMITED ACTIVE!**  \nఅన్‌లిమిటెడ్ రిపోర్ట్‌లు పొందవచ్చు.')
    else:
        rem = max(0, 3 - st.session_state.free_used_count)
        if rem == 0:
            st.error('🔒 **Free Trial: 0 ఉచిత రిపోర్ట్‌లు మిగిలి ఉన్నాయి!**')
        else:
            st.info(f'🎁 **Free Trial:** మీకు **{rem} ఉచిత రిపోర్ట్‌లు** మిగిలి ఉన్నాయి.')
        st.markdown(
            f'• **1 Month:** **₹100/-** 👉 [Pay ₹100]({PAY_1_MONTH_LINK})  \n'
            f'• **12 Months:** **₹1,000/-** 👉 [Pay ₹1,000]({PAY_12_MONTHS_LINK})'
        )
        st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
        manual_pid = st.text_input('🔑 Payment ID:', placeholder='pay_P9x82kLm01', label_visibility='collapsed')
        if st.button('Unlock with Payment ID 🔓'):
            res_st = verify_payment_id(manual_pid)
            if res_st == 'OWNER_VALID':
                st.session_state.is_pro_user = True
                st.rerun()
            elif res_st == 'VALID':
                st.session_state.is_pro_user = True
                streamlit_js_eval(js_expressions="localStorage.setItem('ts_pro_v8', 'yes')", key=f'ls_p_btn_{int(time.time())}')
                time.sleep(0.4)
                st.rerun()
            elif res_st == 'ALREADY_USED':
                st.error('❌ ఈ Payment ID గరిష్టంగా 3 డివైజ్‌లలో వాడబడింది! admin@aiengtel.com కి మెసేజ్ చేయండి.')
            else:
                st.error('❌ సరైన Payment ID ఇవ్వండి.')

if os.path.isfile('logo.png'):
    c1, c2 = st.columns((1, 5))
    with c1:
        st.image('logo.png', width=95)
    with c2:
        st.markdown('# TrendSutra AI')
        st.markdown('**A to Z Growth Analyzer for YouTube, Instagram & TikTok | Powered by [AIENGTEL.com](https://aiengtel.com)**')
else:
    st.markdown('# 🚀 TrendSutra AI  \n**A to Z Growth Analyzer for YouTube, Instagram & TikTok | Powered by [AIENGTEL.com](https://aiengtel.com)**')

col1, col2 = st.columns(2)
with col1:
    platform = st.selectbox('Select Platform:', ('YouTube', 'Instagram Reels', 'TikTok'))
with col2:
    video_url = st.text_input('Channel / Profile / Video Link:', placeholder='https://youtu.be/... లేదా Reel / TikTok లింక్ పేస్ట్ చేయండి')

@st.cache_data(ttl=600, show_spinner=False)
def fetch_youtube_info(url):
    m = re.search(r'(?:v=|\/|live\/|shorts\/)([0-9A-Za-z_-]{11}).*', url)
    if not m:
        return None, 'సరైన YouTube వీడియో లింక్ ఇవ్వండి.', []
    if not YOUTUBE_KEY:
        return None, 'YouTube API Key లేదు.', []
    try:
        yt = build('youtube', 'v3', developerKey=YOUTUBE_KEY)
        vr = yt.videos().list(part='snippet,statistics', id=m.group(1)).execute()
        items = vr.get('items', [])
        if not items:
            return None, 'వీడియో వివరాలు దొరకలేదు.', []
        sn, st_obj = items[0]['snippet'], items[0]['statistics']
        coms = []
        try:
            cr = yt.commentThreads().list(part='snippet', videoId=m.group(1), maxResults=25, order='relevance', textFormat='plainText').execute()
            for c in cr.get('items', []):
                top = c['snippet']['topLevelComment']['snippet']
                author = top.get('authorDisplayName', 'Viewer')
                text = top.get('textDisplay', '').replace('\n', ' ').strip()
                if text:
                    coms.append(f'{author}: {text[:220]}')
        except Exception:
            coms = []
        raw_summary = (
            f"Channel: {sn.get('channelTitle','')}\n"
            f"Title: {sn.get('title','')}\n"
            f"PublishedAt: {sn.get('publishedAt','')}\n"
            f"Views: {st_obj.get('viewCount','0')}, Likes: {st_obj.get('likeCount','0')}, Comments: {st_obj.get('commentCount','0')}\n"
            f"Description: {sn.get('description','')[:1400]}\n"
            f"Tags: {sn.get('tags',[])[:20]}\n"
            f"Real Viewer Comments: {coms[:15]}"
        )
        return raw_summary, st_obj, coms[:5]
    except Exception as e:
        return None, f'YouTube Error: {str(e)}', []

@st.cache_resource(show_spinner=False)
def get_best_models(api_key):
    valid = []
    try:
        client = genai.Client(api_key=api_key)
        for mod in client.models.list():
            name = getattr(mod, 'name', '') or ''
            short = name.replace('models/', '')
            methods = getattr(mod, 'supported_generation_methods', []) or []
            if 'generateContent' in methods and 'gemini' in short.lower():
                if any(b in short.lower() for b in ('image', 'tts', 'audio', 'robotics', 'embedding', 'aqa', '1.5', '2.0')):
                    continue
                if 'flash' in short.lower():
                    valid.append(short)
    except Exception:
        pass
    lite_models = [m for m in valid if 'lite' in m.lower()]
    std_flash = [m for m in valid if 'lite' not in m.lower() and 'pro' not in m.lower()]
    ordered = lite_models + std_flash
    for fb in ('gemini-2.5-flash-lite', 'gemini-3.5-flash-lite', 'gemini-3.5-flash'):
        if fb not in ordered:
            ordered.append(fb)
    return ordered[:4]

def clean_advisor_words(txt):
    return (
        txt.replace('మెంటర్', 'సలహాదారు')
        .replace('గ్రోత్ మెంటర్', 'గ్రోత్ సలహాదారు')
        .replace('కంటెంట్ స్ట్రాటజిస్ట్', 'కంటెంట్ సలహాదారు')
        .replace('స్ట్రాటజిస్ట్', 'సలహాదారు')
    )

def build_growth_prompt(platform_name, raw_data, lang, audience, top_comments):
    comments_block = '\n'.join([f'- {c}' for c in top_comments]) if top_comments else 'No public comments available.'
    return (
        f'You are a warm, encouraging, human {platform_name} Growth Advisor (సలహాదారు) at TrendSutra AI. '
        f'Write a rich, easy-to-understand, deeply helpful A-to-Z Growth Audit Report in {lang} for a {audience} audience. '
        'CRITICAL RULES:\n'
        '1. NEVER use the words మెంటర్ or స్ట్రాటజిస్ట్—always use సలహాదారు when referring to yourself.\n'
        '2. Use simple, everyday spoken language that any creator can understand in 10 seconds without jargon. Write a thorough, detailed report (1,100 to 1,400 words) so the creator feels they got massive value.\n'
        '3. Start Section 1 by genuinely praising the creator effort, topic selection, and storytelling, AND clearly retell/summarize the story or main content of their video from the title, description, and comments so they immediately see you understood their video!\n'
        f'4. In Section 2, take the Real Viewer Comments provided below, TRANSLATE those exact real comments into {lang}, display 4-5 of them with the commenter name, explain what viewers loved or asked for, and give 3 copy-paste reply templates.\n'
        '5. Use exact Telugu spelling పని 1, పని 2, పని 3 in the 30-day plan.\n\n'
        'Follow these exact 6 sections with clear headings and bullet points:\n'
        '## 🎬 1. మీ వీడియో కథ & క్రియేటర్ అభినందన (Video Story Recap & Creator Praise)\n'
        '- Warmly praise the creator hard work, presentation, and topic choice.\n'
        '- Retell the core story or key points of the video clearly in simple words based on the video details.\n'
        '- Analyze current Views, Likes, and Comments engagement simply and show what is working well.\n\n'
        '## 💬 2. ఆడియన్స్ ఏం అంటున్నారు? (Translated Real Viewer Comments & Replies)\n'
        '- Show 4 to 5 real viewer comments translated clearly into the selected language with commenter names.\n'
        '- Explain viewer emotions and what they want next.\n'
        '- Give 3 ready-to-copy pinned/reply comments to boost engagement.\n\n'
        '## 🔥 3. తర్వాత తీయాల్సిన 3 వైరల్ వీడియో ఐడియాలు (Next 3 Viral Video Ideas)\n'
        '- Give 3 specific follow-up video ideas based on this exact story/topic.\n'
        '- For each idea include: Video Concept, exact 5-second Opening Hook dialogue, and Thumbnail visual idea.\n\n'
        '## 🎯 4. కాపీ-పేస్ట్ టైటిల్స్, డిస్క్రిప్షన్ & ట్యాగ్స్ (SEO Makeover)\n'
        '- 3 High-CTR clickable titles.\n'
        '- A ready-to-paste first 3 lines of video description.\n'
        '- 15 searchable tags separated by commas.\n\n'
        '## 💰 5. ఈ ఛానల్ ద్వారా సంపాదించే 3 సులభమైన మార్గాలు (Earning Blueprint)\n'
        '- 3 practical ways to earn money (AdSense boost, Affiliate products, Local/Brand sponsorships) tailored to this niche.\n\n'
        '## 📅 6. వచ్చే 30 రోజుల కార్యాచరణ ప్రణాళిక (30-Day Step-by-Step Plan)\n'
        '- Simple weekly steps written clearly as పని 1, పని 2, పని 3, పని 4.\n\n'
        f'Real Viewer Comments:\n{comments_block}\n\n'
        f'Video Data:\n{raw_data}'
    )

if 'generated_report' not in st.session_state:
    st.session_state.generated_report = ''
if 'report_stats' not in st.session_state:
    st.session_state.report_stats = None

btn_col, status_col = st.columns([1.3, 2.7])
with btn_col:
    generate_clicked = st.button('Generate Accurate Growth Report 🔍')
with status_col:
    status_placeholder = st.empty()

if generate_clicked:
    latest_cnt = fetch_sheet_device_count(DEVICE_ID)
    if latest_cnt is not None and latest_cnt > st.session_state.free_used_count:
        st.session_state.free_used_count = latest_cnt

    if not st.session_state.is_pro_user and st.session_state.free_used_count >= 3:
        st.session_state.generated_report = ''
        st.session_state.report_stats = None
        st.error('🔒 **మీ 3 ఉచిత రిపోర్ట్‌లు పూర్తయ్యాయి!**')
        st.markdown(
            f'* **1 Month Unlimited (₹100):** 👉 [Pay ₹100]({PAY_1_MONTH_LINK})\n'
            f'* **12 Months Unlimited (₹1,000):** 👉 [Pay ₹1,000]({PAY_12_MONTHS_LINK})'
        )
    elif not video_url.strip():
        st.warning('⚠️ ముందుగా వీడియో లింక్ పేస్ట్ చేయండి.')
    else:
        status_placeholder.markdown(
            "<div class='loading-pill'>🔄 రిపోర్ట్ లోడ్ అవుతోంది... దయచేసి వేచి ఉండండి (ఆపడానికి పేజీ Refresh చేయండి)</div>",
            unsafe_allow_html=True,
        )
        clean_link = video_url.strip()
        if platform == 'YouTube':
            d_txt, st_obj, top_coms = fetch_youtube_info(clean_link)
        else:
            d_txt, st_obj, top_coms = f'{platform} Link: {clean_link}', None, []

        if platform == 'YouTube' and not d_txt:
            status_placeholder.empty()
            st.error(f'⚠️ {st_obj}')
        elif not GEMINI_KEYS:
            status_placeholder.empty()
            st.error('⚠️ API Key సెటప్ కాలేదు.')
        else:
            if isinstance(st_obj, dict):
                m1, m2, m3 = st.columns(3)
                m1.metric('👀 Views', f"{int(st_obj.get('viewCount', 0)):,}")
                m2.metric('👍 Likes', f"{int(st_obj.get('likeCount', 0)):,}")
                m3.metric('💬 Comments', f"{int(st_obj.get('commentCount', 0)):,}")

            prompt = build_growth_prompt(platform, d_txt, report_lang, target_audience, top_coms)
            stream_box = st.empty()
            full_text = ''
            success = False
            last_err = ''

            for key in GEMINI_KEYS:
                if success:
                    break
                client = genai.Client(api_key=key)
                models_to_try = get_best_models(key)
                for m_name in models_to_try:
                    try:
                        full_text = ''
                        response_stream = client.models.generate_content_stream(
                            model=m_name,
                            contents=prompt,
                            config=types.GenerateContentConfig(
                                temperature=0.8,
                                max_output_tokens=8192,
                            ),
                        )
                        for chunk in response_stream:
                            if chunk and chunk.text:
                                full_text += clean_advisor_words(chunk.text)
                                stream_box.markdown(full_text + ' ▌')
                        if len(full_text.strip()) > 200:
                            stream_box.markdown(full_text)
                            success = True
                            break
                    except Exception as e:
                        last_err = str(e)
                        continue

            status_placeholder.empty()
            if success:
                st.session_state.generated_report = full_text
                st.session_state.report_stats = st_obj
                log_usage_to_sheet(DEVICE_ID, platform, clean_link)
                if not st.session_state.is_pro_user:
                    new_cnt = increment_sheet_device_count(DEVICE_ID)
                    if new_cnt is not None:
                        st.session_state.free_used_count = new_cnt
                    else:
                        st.session_state.free_used_count = min(3, st.session_state.free_used_count + 1)
                    streamlit_js_eval(
                        js_expressions=f"localStorage.setItem('ts_free_v8', '{st.session_state.free_used_count}')",
                        key=f'ls_inc_{int(time.time())}',
                    )
                    time.sleep(0.5)
                    st.rerun()
            else:
                st.session_state.generated_report = ''
                if '429' in last_err or 'RESOURCE_EXHAUSTED' in last_err:
                    st.error('⚠️ AI సర్వర్ తాత్కాలికంగా రద్దీగా ఉంది. 30 సెకన్ల తర్వాత మళ్ళీ ప్రయత్నించండి.')
                else:
                    st.error(f'⚠️ రిపోర్ట్ లోడ్ కాలేదు: {last_err[:120]}')

if st.session_state.generated_report and not generate_clicked:
    if isinstance(st.session_state.report_stats, dict):
        m1, m2, m3 = st.columns(3)
        m1.metric('👀 Views', f"{int(st.session_state.report_stats.get('viewCount', 0)):,}")
        m2.metric('👍 Likes', f"{int(st.session_state.report_stats.get('likeCount', 0)):,}")
        m3.metric('💬 Comments', f"{int(st.session_state.report_stats.get('commentCount', 0)):,}")
    st.success('✅ Growth Audit Report సిద్ధమైంది!')
    st.download_button(
        '📥 Download Growth Report (.txt)',
        st.session_state.generated_report,
        'TrendSutra_Report.txt',
    )
    st.markdown(st.session_state.generated_report)
