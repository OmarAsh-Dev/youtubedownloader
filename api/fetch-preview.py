from flask import Flask, request, jsonify
import yt_dlp

app = Flask(__name__)

@app.route("/", methods=["GET"])
def fetch_preview():
    url = request.args.get("url")
    if not url:
        return jsonify({"error": "No URL provided"}), 400

    try:
        with yt_dlp.YoutubeDL({"quiet": True}) as ydl:
            info = ydl.extract_info(url, download=False)
            video_id = info.get("id")
        return jsonify({"video_id": video_id})
    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500
