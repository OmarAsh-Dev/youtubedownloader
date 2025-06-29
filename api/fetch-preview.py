import json
import yt_dlp
from urllib.parse import parse_qs

def handler(request):
    qs = parse_qs(request.url.split("?", 1)[1]) if "?" in request.url else {}
    url = qs.get("url", [None])[0]
    if not url:
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": "No URL provided"})
        }
    with yt_dlp.YoutubeDL({"quiet": True}) as ydl:
        info = ydl.extract_info(url, download=False)
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({"video_id": info.get("id")})
    }
