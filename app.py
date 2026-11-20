import re
import requests
import streamlit as st
from google import genai
from google.genai import types

st.set_page_config(
    page_title="TrendSutra AI | Growth Analyzer",
    page_icon="📈",
    layout="wide",
)


def get_gemini_keys():
    keys = []
    if "GEMINI_API_KEYS" in st.secrets:
        val = st.secrets["GEMINI_API_KEYS"]
        if isinstance(val, list):
            keys.extend([str(k).strip() for k in val if k and str(k).strip()])
        elif isinstance(val, str):
            keys.extend([k.strip() for k in val.split(",") if k.strip()])
    if "GEMINI_API_KEY" in st.secrets and st.secrets["GEMINI_API_KEY"]:
        single_key = str(st.secrets["GEMINI_API_KEY"]).strip()
        if single_key and single_key not in keys:
            keys.append(single_key)
    return keys


def extract_video_id(text: str):
    patterns = [
        r"(?:v=|/v/|youtu\.be/|/shorts/|/live/)([A-Za-z0-9_-]{11})",
    ]
    for p in patterns:
        m = re.search(p, text)
        if m:
            return m.group(1)
    return None


def _extract_output_text(res) -> str:
    if not res:
        return ""
    if getattr(res, "text", None) and str(res.text).strip():
        return str(res.text).strip()
    outputs = getattr(res, "outputs", None) or []
    parts = []
    for item in outputs:
        t = getattr(item, "text", None)
        if t:
            parts.append(str(t))
    return "\n".join(parts).strip()


def generate_with_rotation(prompt: str) -> str:
    keys = get_gemini_keys()
    if not keys:
        return "❌ Streamlit Secrets లో Gemini API Key లేదు. దయచేసి యాడ్ చేయండి."

    if "gemini_key_idx" not in st.session_state:
        st.session_state.gemini_key_idx = 0

    total = len(keys)
    errors = []

    for attempt in range(total):
        idx = (st.session_state.gemini_key_idx + attempt) % total
        api_key = keys[idx]
        try:
            client = genai.Client(
                api_key=api_key,
                http_options=types.HttpOptions(timeout=15000),
            )

            # 1) Try Interactions API with gemini-3.8-flash
            try:
                inter = client.interactions.create(
                    model="gemini-3.8-flash",
                    input=prompt,
                )
                out = _extract_output_text(inter)
                if out:
                    st.session_state.gemini_key_idx = (idx + 1) % total
                    return out
            except Exception as e_inter:
                errors.append(f"Key#{idx+1} [interactions gemini-3.8-flash]: {e_inter}")

            # 2) Try generate_content with gemini-3.8-flash
            try:
                resp = client.models.generate_content(
                    model="gemini-3.8-flash",
                    contents=prompt,
                )
                out = _extract_output_text(resp)
                if out:
                    st.session_state.gemini_key_idx = (idx + 1) % total
                    return out
            except Exception as e_gc:
                errors.append(f"Key#{idx+1} [generate_content gemini-3.8-flash]: {e_gc}")

            # 3) Auto-discover first available flash model for this key
            try:
                avail_models = []
                for m in client.models.list():
                    m_name = getattr(m, "name", "")
                    if "flash" in m_name.lower():
                        avail_models.append(m_name)
                for m_name in avail_models[:2]:
                    try:
                        resp_m = client.models.generate_content(
                            model=m_name,
                            contents=prompt,
                        )
                        out_m = _extract_output_text(resp_m)
                        if out_m:
                            st.session_state.gemini_key_idx = (idx + 1) % total
                            return out_m
                    except Exception as e_m:
                        errors.append(f"Key#{idx+1} [{m_name}]: {e_m}")
            except Exception as e_list:
                errors.append(f"Key#{idx+1} [models.list]: {e_list}")

        except Exception as e_client:
            errors.append(f"Key#{idx+1} [client]: {e_client}")

    return "❌ రిపోర్ట్ జనరేట్ కాలేదు. వివరాలు:\n- " + "\n- ".join(errors[-4:])


def fetch_youtube_stats(user_input: str) -> str:
    yt_key = st.secrets.get("YOUTUBE_API_KEY", "")
    if not yt_key:
        return f"YouTube Input: {user_input}"

    vid_id = extract_video_id(user_input)
    try:
        if vid_id:
            v_url = "https://www.googleapis.com/youtube/v3/videos"
            v_res = requests.get(
                v_url,
                params={"part": "snippet,statistics", "id": vid_id, "key": yt_key},
                timeout=8,
            ).json()
            items = v_res.get("items", [])
            if items:
                sn = items[0].get("snippet", {})
                st_data = items[0].get("statistics", {})
                return (
                    f"Video Title: {sn.get('title', 'N/A')}\n"
                    f"Channel: {sn.get('channelTitle', 'N/A')}\n"
                    f"Views: {st_data.get('viewCount', 'N/A')} | Likes: {st_data.get('likeCount', 'N/A')} | Comments: {st_data.get('commentCount', 'N/A')}\n"
                    f"Tags: {', '.join(sn.get('tags', [])[:10])}"
                )

        search_url = "https://www.googleapis.com/youtube/v3/search"
        r = requests.get(
            search_url,
            params={
                "part": "snippet",
                "q": user_input,
                "type": "channel",
                "maxResults": 1,
                "key": yt_key,
            },
            timeout=8,
        ).json()
        items = r.get("items", [])
        if not items:
            return f"Input/Query: {user_input}"

        ch = items[0]
        ch_id = ch["id"]["channelId"]
        title = ch["snippet"]["title"]
        desc = ch["snippet"].get("description", "")

        s_res = requests.get(
            "https://www.googleapis.com/youtube/v3/channels",
            params={"part": "statistics", "id": ch_id, "key": yt_key},
            timeout=8,
        ).json()
        stats = s_res.get("items", [{}])[0].get("statistics", {})

        return (
            f"Channel: {title}\n"
            f"Subscribers: {stats.get('subscriberCount', 'Hidden/N/A')}\n"
            f"Total Views: {stats.get('viewCount', 'N/A')}\n"
            f"Total Videos: {stats.get('videoCount', 'N/A')}\n"
            f"Description: {desc[:250]}"
        )
    except Exception as e:
        return f"YouTube lookup note: {e} | Input: {user_input}"


def fetch_rapidapi_info(platform: str, username: str) -> str:
    rapid_key = st.secrets.get("RAPIDAPI_API_KEY", "")
    clean_user = username.lstrip("@").strip()
    if not rapid_key:
        return f"{platform} Handle/Niche: @{clean_user}"
    try:
        if platform == "Instagram":
            url = "https://instagram-scraper-stable-api.p.rapidapi.com/ig_get_fb_profile_hover.php"
            headers = {
                "x-rapidapi-key": rapid_key,
                "x-rapidapi-host": "instagram-scraper-stable-api.p.rapidapi.com",
            }
            resp = requests.get(
                url,
                headers=headers,
                params={"username_or_url": clean_user},
                timeout=8,
            )
            return f"Instagram Data (@{clean_user}): {resp.text[:800]}"
        return f"TikTok Handle/Niche: @{clean_user}"
    except Exception as e:
        return f"{platform} lookup note: {e} | @{clean_user}"


st.title("📈 TrendSutra AI")
st.caption("YouTube, Instagram & TikTok A to Z Growth Analyzer • 100% Free Access")

with st.sidebar:
    st.header("⚙️ TrendSutra AI Controls")
    platform = st.selectbox("ప్లాట్‌ఫామ్ ఎంచుకోండి", ["YouTube", "Instagram", "TikTok"])
    target_input = st.text_input(
        "ఛానెల్ పేరు / @Username / Link / Niche",
        placeholder="ఉదా: @creator లేదా Tech Telugu",
    )
    goal = st.selectbox(
        "ప్రధాన లక్ష్యం",
        [
            "A to Z Growth Audit",
            "Viral Hook & Content Ideas",
            "Algorithm & Retention Fix",
            "Monetization Roadmap",
        ],
    )
    keys_count = len(get_gemini_keys())
    st.success(f"🔑 Active Gemini Keys: {keys_count} (Auto-Rotation Ready)")

st.markdown("---")

if st.button("🚀 Analyze Now", type="primary"):
    if not target_input.strip():
        st.warning("దయచేసి ఛానెల్ పేరు / @Username / Link లేదా Niche ఎంటర్ చేయండి.")
    else:
        with st.spinner("TrendSutra AI వేగంగా విశ్లేషిస్తోంది..."):
            if platform == "YouTube":
                raw_data = fetch_youtube_stats(target_input.strip())
            else:
                raw_data = fetch_rapidapi_info(platform, target_input.strip())

            prompt = (
                f"You are TrendSutra AI. Give a crisp, practical growth report in Telugu "
                f"(key English terms allowed). Keep it concise and actionable.\n"
                f"Platform: {platform} | Input: {target_input.strip()} | Goal: {goal}\n"
                f"Data: {raw_data}\n\n"
                f"Sections:\n"
                f"1. **Current Snapshot & Fixes**\n"
                f"2. **Reach & Retention Strategy**\n"
                f"3. **5 Viral Hook Ideas**\n"
                f"4. **7-Day Action Steps**"
            )
            report = generate_with_rotation(prompt)
            st.markdown("### 📊 TrendSutra AI Growth Report")
            st.markdown(report)
