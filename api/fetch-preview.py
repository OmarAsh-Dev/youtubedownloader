import json
import yt_dlp
from urllib.parse import parse_qs

def handler(request):
    # Parse query string
    query = parse_qs(request.url.split("?")[1]) if "?" in request.url else {}
    url = query.get("url", [None])[0]

    if not url:
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": "No URL provided"})
        }

    try:
        with yt_dlp.YoutubeDL({"quiet": True}) as ydl:
            info = ydl.extract_info(url, download=False)
            video_id = info.get("id")

        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"video_id": video_id})
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": f"Server error: {str(e)}"})
        }
