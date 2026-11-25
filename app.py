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

st.markdown(
    '<style>#MainMenu,footer,.stDeployButton,div[data-testid="stToolbarActions"],div[data-testid="stDecoration"],div[data-testid="stStatusWidget"],.viewerBadge_container__1QSob,.viewerBadge_link__1S137{display:none!important;}header[data-testid="stHeader"]{height:1.2rem!important;background:transparent!important;}.block-container{padding-top:0.4rem!important;padding-bottom:1rem!important;max-width:98%!important;}section[data-testid="stSidebar"]>div:first-child{padding-top:0.2rem!important;padding-bottom:0.2rem!important;}section[data-testid="stSidebar"] .stMarkdown p{margin-bottom:0.25rem!important;font-size:0.9rem!important;}section[data-testid="stSidebar"] h3{margin-top:0.35rem!important;margin-bottom:0.2rem!important;font-size:1.05rem!important;}section[data-testid="stSidebar"] div[data-testid="stSelectbox"],section[data-testid="stSidebar"] div[data-testid="stRadio"]{margin-bottom:-0.45rem!important;}section[data-testid="stSidebar"] div[data-testid="stTextInput"]{margin-top:0.4rem!important;margin-bottom:-0.35rem!important;}div.stButton>button:first-child{background-color:#c92a2a;color:white;font-weight:bold;border-radius:6px;border:none;width:100%;}div.stDownloadButton>button:first-child{background-color:#2b8a3e;color:white;font-weight:bold;border-radius:6px;border:none;}</style>',
    unsafe_allow_html=True,
)

GEMINI_KEYS = [
    k.strip()
    for k in (
        st.secrets.get('GEMINI_API_KEY', ''),
        st.secrets.get('GEMINI_API_KEY_2', ''),
    )
    if str(k).strip()
]
YOUTUBE_KEY = str(st.secrets.get('YOUTUBE_API_KEY', '')).strip()
RAPIDAPI_KEY = str(st.secrets.get('RAPIDAPI_API_KEY', '')).strip()

GOOGLE_SHEET_API = 'https://script.google.com/macros/s/AKfycbzEkkgxBP7aOKIXkEiOG7_rWc0quvnvTVqQDSWUAMk2zOPN7W8Ue_uOPwH7edmJJtEd/exec'
PAY_1_MONTH_LINK = 'https://rzp.io/rzp/yop8jYS'
PAY_12_MONTHS_LINK = 'https://rzp.io/rzp/sjonGmqw'

@st.cache_data(ttl=3600, show_spinner=False)
def get_public_ip():
    for srv in ('https://api.ipify.org', 'https://icanhazip.com'):
        try:
            r = requests.get(srv, timeout=3)
            if r.status_code == 200 and r.text.strip():
                return r.text.strip()
        except Exception:
            pass
    return 'unknown_ip'

def get_device_fingerprint():
    ip = get_public_ip()
    headers = {}
    try:
        headers = dict(st.context.headers)
    except Exception:
        pass
    ua = headers.get('User-Agent', headers.get('user-agent', ''))
    lang = headers.get('Accept-Language', headers.get('accept-language', ''))
    base_ua = re.sub(r'Chrome/[0-9.]+|Safari/[0-9.]+|Edg/[0-9.]+|Firefox/[0-9.]+', '', ua)
    raw = f'{ip}|{base_ua}|{lang}'
    return 'dev_' + hashlib.sha256(raw.encode('utf-8')).hexdigest()[:16]

def sheet_get_device_count(dev_id):
    try:
        res = requests.get(
            f'{GOOGLE_SHEET_API}?device={dev_id}&t={int(time.time())}',
            headers={'User-Agent': 'Mozilla/5.0'},
            allow_redirects=True,
            timeout=6,
        )
        txt = res.text.strip()
        if txt.isdigit():
            return int(txt)
    except Exception:
        pass
    return None

def sheet_inc_device_count(dev_id):
    try:
        res = requests.get(
            f'{GOOGLE_SHEET_API}?device={dev_id}&inc=1&t={int(time.time())}',
            headers={'User-Agent': 'Mozilla/5.0'},
            allow_redirects=True,
            timeout=6,
        )
        txt = res.text.strip()
        if txt.isdigit():
            return int(txt)
    except Exception:
        pass
    return None

def log_usage_to_sheet(dev_id, plat, url_str):
    try:
        requests.get(
            GOOGLE_SHEET_API,
            params={'log': '1', 'device': dev_id, 'platform': plat, 'url': url_str},
            headers={'User-Agent': 'Mozilla/5.0'},
            allow_redirects=True,
            timeout=5,
        )
    except Exception:
        pass

device_id = get_device_fingerprint()

ls_free = streamlit_js_eval(
    js_expressions="localStorage.getItem('ts_device_free_v7')", key='ls_get_free'
)
ls_pro = streamlit_js_eval(
    js_expressions="localStorage.getItem('ts_device_pro_v7')", key='ls_get_pro'
)

if 'free_used_count' not in st.session_state:
    sheet_cnt = sheet_get_device_count(device_id)
    st.session_state.free_used_count = sheet_cnt if sheet_cnt is not None else 0
if 'is_pro_user' not in st.session_state:
    st.session_state.is_pro_user = False

if ls_free and str(ls_free).isdigit():
    ls_val = int(ls_free)
    if ls_val > st.session_state.free_used_count:
        st.session_state.free_used_count = ls_val
        st.rerun()

if ls_pro == 'yes' and not st.session_state.is_pro_user:
    st.session_state.is_pro_user = True
    st.rerun()

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
            f'{GOOGLE_SHEET_API}?pid={clean_pid}&t={int(time.time())}',
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
        streamlit_js_eval(
            js_expressions="localStorage.setItem('ts_device_pro_v7', 'yes')",
            key='ls_pro_url',
        )
    elif st_val == 'ALREADY_USED':
        st.sidebar.error('⚠️ ఈ Payment ID గరిష్టంగా 3 డివైజ్‌లలో వాడబడింది!')

with st.sidebar:
    st.markdown('### 🌍 Settings')
    report_lang = st.selectbox(
        'Report Language / భాష:',
        ('Telugu (తెలుగు)', 'English (Global)', 'Tenglish'),
    )
    target_audience = st.radio(
        'Target Audience:',
        ('Regional', 'Global', 'Both'),
        horizontal=True,
    )
    st.markdown('### 💎 Pro Plans (Unlimited)')
    if st.session_state.is_pro_user:
        st.success('✅ **PRO UNLIMITED ACTIVE!**\n\nఅన్‌లిమిటెడ్ రిపోర్ట్‌లు పొందవచ్చు.')
    else:
        rem = max(0, 3 - st.session_state.free_used_count)
        if rem > 0:
            st.caption(f'🎁 **Free Trial:** మీకు **{rem} ఉచిత రిపోర్ట్‌లు** మిగిలి ఉన్నాయి.')
        else:
            st.error('🔒 **Free Trial: 0 ఉచిత రిపోర్ట్‌లు మిగిలి ఉన్నాయి!**')
        st.markdown(
            f'• **1 Month:** **₹100/-** 👉 [Pay ₹100]({PAY_1_MONTH_LINK})  \n'
            f'• **12 Months:** **₹1,000/-** 👉 [Pay ₹1,000]({PAY_12_MONTHS_LINK})'
        )
        st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
        manual_pid = st.text_input(
            'Payment ID:',
            placeholder='pay_P9x82kLm01',
            label_visibility='collapsed',
        )
        st.markdown("<div style='height:4px;'></div>", unsafe_allow_html=True)
        if st.button('Unlock with Payment ID 🔓'):
            res_st = verify_payment_id(manual_pid)
            if res_st == 'OWNER_VALID':
                st.session_state.is_pro_user = True
                st.rerun()
            elif res_st == 'VALID':
                st.session_state.is_pro_user = True
                streamlit_js_eval(
                    js_expressions="localStorage.setItem('ts_device_pro_v7', 'yes')",
                    key=f'ls_pro_{int(time.time())}',
                )
                time.sleep(0.5)
                st.rerun()
            elif res_st == 'ALREADY_USED':
                st.error('❌ ఈ Payment ID 3 డివైజ్‌లలో వాడబడింది! admin@aiengtel.com కి మెసేజ్ చేయండి.')
            else:
                st.error('❌ సరైన Payment ID ఇవ్వండి.')

if os.path.isfile('logo.png'):
    c1, c2 = st.columns((1, 6))
    with c1:
        st.image('logo.png', width=90)
    with c2:
        st.markdown('# TrendSutra AI')
        st.markdown('**A to Z Growth Analyzer for YouTube, Instagram & TikTok | Powered by [AIENGTEL.com](https://aiengtel.com)**')
else:
    st.markdown('# 🚀 TrendSutra AI\n**A to Z Growth Analyzer for YouTube, Instagram & TikTok | Powered by [AIENGTEL.com](https://aiengtel.com)**')

col1, col2 = st.columns(2)
with col1:
    platform = st.selectbox('Select Platform:', ('YouTube', 'Instagram Reels', 'TikTok'))
with col2:
    video_url = st.text_input('Channel / Profile / Video Link:', placeholder='https://youtu.be/... లేదా Reel / TikTok లింక్ పేస్ట్ చేయండి')

@st.cache_data(ttl=300, show_spinner=False)
def fetch_youtube_info(url):
    m = re.search(r'(?:v=|\/|live\/|shorts\/)([0-9A-Za-z_-]{11}).*', url)
    if not m:
        return None, 'సరైన YouTube వీడియో లింక్ ఇవ్వండి.'
    try:
        yt = build('youtube', 'v3', developerKey=YOUTUBE_KEY)
        vr = yt.videos().list(part='snippet,statistics', id=m.group(1)).execute()
        items = vr.get('items', [])
        if not items:
            return None, 'వీడియో వివరాలు దొరకలేదు.'
        sn, st_obj = items[0]['snippet'], items[0]['statistics']
        coms = []
        try:
            cr = yt.commentThreads().list(
                part='snippet', videoId=m.group(1), maxResults=40, order='relevance', textFormat='plainText'
            ).execute()
            coms = [c['snippet']['topLevelComment']['snippet']['textDisplay'] for c in cr.get('items', [])]
        except Exception:
            coms = ['కామెంట్లు ఆఫ్ చేసి ఉన్నాయి.']
        views = int(st_obj.get('viewCount', 0))
        likes = int(st_obj.get('likeCount', 0))
        cmts = int(st_obj.get('commentCount', 0))
        like_rate = round((likes / views * 100), 2) if views > 0 else 0
        cmt_rate = round((cmts / views * 100), 2) if views > 0 else 0
        summary = (
            f"Channel: {sn.get('channelTitle','')}\n"
            f"Title: {sn.get('title','')}\n"
            f"Views: {views:,} | Likes: {likes:,} ({like_rate}%) | Comments: {cmts:,} ({cmt_rate}%)\n"
            f"Description: {sn.get('description','')[:800]}\n"
            f"Tags: {sn.get('tags', [])}\n"
            f"Top Audience Comments: {coms}"
        )
        return summary, st_obj
    except Exception as e:
        return None, f'YouTube Error: {str(e)}'

@st.cache_resource(show_spinner=False)
def get_active_models(api_key):
    try:
        client = genai.Client(api_key=api_key)
        all_m = []
        for m in client.models.list():
            name = getattr(m, 'name', '')
            actions = getattr(m, 'supported_actions', []) or []
            if 'generateContent' in actions and 'flash' in name.lower():
                clean = name.replace('models/', '')
                if not any(old in clean for old in ('1.0', '1.5', '2.0', '2.5-flash-preview', 'image', 'audio', 'tts')):
                    all_m.append(clean)
        lite_m = [x for x in all_m if 'lite' in x]
        other_m = [x for x in all_m if 'lite' not in x]
        ordered = lite_m + other_m
        if ordered:
            return ordered
    except Exception:
        pass
    return ['gemini-3.5-flash-lite', 'gemini-3.5-flash', 'gemini-2.5-flash-lite']

def build_advisor_prompt(platform_name, raw_data, lang, audience):
    return (
        f'You are a warm, friendly, helpful {platform_name} Growth Advisor (సలహాదారు) talking directly to a creator in {lang} for a {audience} audience. '
        'CRITICAL LANGUAGE & STYLE RULES:\n'
        '- NEVER use the word మెంటర్ (Mentor) or స్ట్రాటజిస్ట్ (Strategist). Always call yourself సలహాదారు (Advisor) or మీ గ్రోత్ సలహాదారు.\n'
        '- Write in VERY SIMPLE, EVERYDAY, EASY-TO-READ Telugu/English that any beginner can understand immediately. Avoid heavy bookish words (like శుభపరిణామం, విశ్లేషణాత్మక, పరిణామం) — use simple spoken words like చాలా మంచి విషయం, సులభంగా, ఇలా చేయండి.\n'
        '- Keep sentences short and clear. Use simple bullet points.\n'
        '- When writing Telugu action items, ALWAYS use exact spelling పని 1, పని 2, పని 3.\n'
        '- Give a complete, helpful report covering all parts below:\n\n'
        '### 1. 📊 వీడియో పనితీరు ఎలా ఉంది?\n'
        '- Explain in simple words how Views, Likes %, and Comments % are doing right now, what viewers liked, and how to get more views.\n\n'
        '### 2. 💬 ఆడియన్స్ ఏం అంటున్నారు?\n'
        '- Summarize the main points from comments in simple words, and give 3 short, friendly replies the creator can copy-paste.\n\n'
        '### 3. 🔥 తర్వాత తీయాల్సిన 3 వైరల్ వీడియో ఐడియాలు\n'
        '- Suggest 3 simple next video ideas, a catchy 5-second opening line, and easy thumbnail text for each.\n\n'
        '### 4. 🎯 కాపీ-పేస్ట్ SEO (టైటిల్, డిస్క్రిప్షన్ & ట్యాగ్స్)\n'
        '- Give 3 simple, clickable Titles, a short 4-line Description, and 15 searchable Tags.\n\n'
        '### 5. 💰 డబ్బు సంపాదించే మార్గాలు\n'
        '- Share 3 practical ways to earn money from this channel/page (YouTube Ads, Affiliate links, Brand promotions).\n\n'
        '### 6. 📅 30 రోజుల సులభమైన ప్లాన్\n'
        '- Give simple weekly steps using పని 1, పని 2, పని 3 so the creator knows what to do starting tomorrow.\n\n'
        f'Live Video Data:\n{raw_data}'
    )

if 'generated_report' not in st.session_state:
    st.session_state.generated_report = ''
if 'report_stats' not in st.session_state:
    st.session_state.report_stats = None

if st.button('Generate Accurate Growth Report 🔍'):
    if not st.session_state.is_pro_user and st.session_state.free_used_count >= 3:
        st.session_state.generated_report = ''
        st.error('🔒 **ఈ డివైజ్‌లో మీ 3 ఉచిత రిపోర్ట్‌లు పూర్తయ్యాయి!**')
        st.markdown(
            f'* **1 Month Unlimited (₹100):** 👉 [Pay ₹100]({PAY_1_MONTH_LINK})\n'
            f'* **12 Months Unlimited (₹1,000):** 👉 [Pay ₹1,000]({PAY_12_MONTHS_LINK})'
        )
    elif not video_url.strip():
        st.warning('⚠️ ముందుగా వీడియో లింక్ పేస్ట్ చేయండి.')
    else:
        clean_url = video_url.strip()
        if platform == 'YouTube':
            with st.spinner('YouTube వీడియో వివరాలు తీసుకుంటోంది...'):
                d_txt, st_obj = fetch_youtube_info(clean_url)
        else:
            d_txt, st_obj = f'{platform} URL: {clean_url}', None

        if platform == 'YouTube' and not d_txt:
            st.error(f'⚠️ {st_obj}')
        else:
            st.session_state.report_stats = st_obj
            if isinstance(st_obj, dict):
                m1, m2, m3 = st.columns(3)
                m1.metric('👀 Views', f"{int(st_obj.get('viewCount', 0)):,}")
                m2.metric('👍 Likes', f"{int(st_obj.get('likeCount', 0)):,}")
                m3.metric('💬 Comments', f"{int(st_obj.get('commentCount', 0)):,}")

            status_box = st.empty()
            status_box.info('⏳ సలహాదారు మీ రిపోర్ట్ రాస్తున్నారు...')
            report_box = st.empty()

            prompt = build_advisor_prompt(platform, d_txt, report_lang, target_audience)
            full_text = ''
            success = False
            last_err = 'API Key missing in Secrets'

            for key in GEMINI_KEYS:
                client = genai.Client(api_key=key)
                models = get_active_models(key)
                for m in models:
                    try:
                        stream = client.models.generate_content_stream(
                            model=m,
                            contents=prompt,
                            config=types.GenerateContentConfig(
                                temperature=0.8,
                                max_output_tokens=8192,
                            ),
                        )
                        chunks = []
                        for chunk in stream:
                            if chunk.text:
                                chunks.append(chunk.text)
                                clean_live = ''.join(chunks).replace('మెంటర్', 'సలహాదారు').replace('స్ట్రాటజిస్ట్', 'సలహాదారు')
                                report_box.markdown(clean_live)
                        full_text = ''.join(chunks).strip().replace('మెంటర్', 'సలహాదారు').replace('స్ట్రాటజిస్ట్', 'సలహాదారు')
                        if full_text:
                            success = True
                            break
                    except Exception as e:
                        last_err = str(e)
                        continue
                if success:
                    break

            if success:
                status_box.empty()
                st.session_state.generated_report = full_text
                log_usage_to_sheet(device_id, platform, clean_url)
                if not st.session_state.is_pro_user:
                    new_cnt = st.session_state.free_used_count + 1
                    sheet_new = sheet_inc_device_count(device_id)
                    if sheet_new is not None and sheet_new >= new_cnt:
                        new_cnt = sheet_new
                    st.session_state.free_used_count = new_cnt
                    streamlit_js_eval(
                        js_expressions=f"localStorage.setItem('ts_device_free_v7', '{new_cnt}')",
                        key=f'ls_f_{int(time.time())}',
                    )
                    time.sleep(0.5)
                    st.rerun()
            else:
                status_box.empty()
                report_box.empty()
                st.session_state.generated_report = ''
                if '429' in last_err or 'RESOURCE_EXHAUSTED' in last_err:
                    st.error('⚠️ నేటి ఉచిత AI కోటా పూర్తయింది. దయచేసి కాసేపటి తర్వాత మళ్ళీ ప్రయత్నించండి.')
                else:
                    st.error(f'⚠️ AI సర్వర్ బిజీగా ఉంది. దయచేసి మళ్ళీ నొక్కండి. ({last_err[:90]})')

elif st.session_state.generated_report:
    if isinstance(st.session_state.report_stats, dict):
        m1, m2, m3 = st.columns(3)
        m1.metric('👀 Views', f"{int(st.session_state.report_stats.get('viewCount', 0)):,}")
        m2.metric('👍 Likes', f"{int(st.session_state.report_stats.get('likeCount', 0)):,}")
        m3.metric('💬 Comments', f"{int(st.session_state.report_stats.get('commentCount', 0)):,}")
    st.success('✅ Growth Audit Report సిద్ధమైంది!')
    st.download_button(
        '📥 Download Full Growth Report (.txt)',
        st.session_state.generated_report,
        'TrendSutra_Report.txt',
    )
    st.markdown(st.session_state.generated_report)
