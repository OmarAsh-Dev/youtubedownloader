import json
import yt_dlp
import tempfile
import os
import shutil
import base64

def handler(request):
    if request.method != "POST":
        return {
            "statusCode": 405,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": "Invalid method"})
        }
    body = json.loads(request.body.decode())
    url = body.get("url")
    if not url:
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": "URL must be provided"})
        }
    temp_dir = tempfile.mkdtemp()
    try:
        opts = {
            "format": "best[ext=mp4]",
            "outtmpl": os.path.join(temp_dir, "%(title)s.%(ext)s"),
            "quiet": True,
        }
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filepath = ydl.prepare_filename(info)
        with open(filepath, "rb") as f:
            encoded = base64.b64encode(f.read()).decode()
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "filename": os.path.basename(filepath),
                "file_content": encoded
            })
        }
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
