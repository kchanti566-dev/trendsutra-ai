def get_youtube_real_data(url_or_handle):
    raw_yt_key = str(st.secrets.get("YOUTUBE_API_KEY", "")).strip()
    key_match = re.search(r"(AIza[0-9A-Za-z_-]{35})", raw_yt_key)
    clean_yt_key = key_match.group(1) if key_match else ""

    vid_match = re.search(r"(?:v=|youtu\.be\/|shorts\/|live\/)([0-9A-Za-z_-]{11})", url_or_handle)
    if vid_match:
        video_id = vid_match.group(1)
        if clean_yt_key:
            try:
                api_url = "https://googleapis.com"
                params = {"part": "snippet,statistics", "id": video_id, "key": clean_yt_key}
                r = requests.get(api_url, params=params, timeout=6).json()
                if "error" in r:
                    return None, f"⚠️ YouTube API Key Error: {r['error'].get('message')}"
                items = r.get("items", [])
                if items:
                    first_item = items[0]
                    snippet = first_item.get("snippet", {})
                    stats = first_item.get("statistics", {})
                    tags = ", ".join(snippet.get("tags", [])[:10])
                    data_summary = f"Type: YouTube Video | Title: {snippet.get('title')} | Channel: {snippet.get('channelTitle')} | Desc: {snippet.get('description', '')[:300]} | Tags: {tags} | Views: {stats.get('viewCount', '0')}, Likes: {stats.get('likeCount', '0')}"
                    return data_summary, f"🎥 **{snippet.get('title')}** (Channel: {snippet.get('channelTitle')} | 👁️ {stats.get('viewCount', '0')} Views)"
            except Exception as e:
                return None, f"⚠️ Connection Error: {str(e)}"

    handle_match = re.search(r"@([0-9A-Za-z_.-]+)", url_or_handle)
    if handle_match and clean_yt_key:
        try:
            handle_name = "@" + handle_match.group(1)
            api_url = "https://googleapis.com"
            params = {"part": "snippet,statistics", "forHandle": handle_name, "key": clean_yt_key}
            r = requests.get(api_url, params=params, timeout=6).json()
            items = r.get("items", [])
            if items:
                first_item = items[0]
                snippet = first_item.get("snippet", {})
                stats = first_item.get("statistics", {})
                data_summary = f"Type: YouTube Channel | Channel: {snippet.get('title')} | Bio: {snippet.get('description', '')[:300]} | Subscribers: {stats.get('subscriberCount', 'Hidden')}, Views: {stats.get('viewCount', '0')}, Videos: {stats.get('videoCount', '0')}"
                return data_summary, f"📺 **{snippet.get('title')}** (👥 {stats.get('subscriberCount', 'Hidden')} Subscribers | 🎬 {stats.get('videoCount', '0')} Videos)"
        except Exception as e:
            return None, f"⚠️ Channel Error: {str(e)}"

    if not clean_yt_key:
        return None, "⚠️ Streamlit Secrets లో YOUTUBE_API_KEY సరిగ్గా లేదు (AIzaSy... తో మొదలవ్వాలి)."

    return None, "⚠️ ఈ లింక్ నుండి వీడియో వివరాలు దొరకలేదు. దయచేసి సరైన YouTube వీడియో లింక్ ఇవ్వండి."
