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

    try:
        body = json.loads(request.body.decode())
    except:
        body = None

    url = body.get("url") if body else None

    if not url:
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": "URL must be provided"})
        }

    temp_dir = tempfile.mkdtemp()
    try:
        ydl_opts = {
            "format": "best[ext=mp4]",
            "outtmpl": os.path.join(temp_dir, "%(title)s.%(ext)s"),
            "quiet": True,
            "no_warnings": True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)
            filename = os.path.basename(file_path)

        # Read the file and base64 encode
        with open(file_path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode()

        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "filename": filename,
                "file_content": encoded
            })
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": f"Server error: {str(e)}"})
        }

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
