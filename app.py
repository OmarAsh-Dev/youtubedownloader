from flask import Flask, render_template, request, jsonify, send_file
from yt_dlp import YoutubeDL
import threading
import tempfile
import shutil
import os
import uuid
import time
from urllib.parse import urlparse, parse_qs, urlunparse, urlencode

app = Flask(__name__)
downloads = {}

FFMPEG_PATH = r"C:\ffmpeg-7.1.1-essentials_build\bin\ffmpeg.exe"


def strip_playlist_param(url):
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    query.pop("list", None)
    cleaned_query = urlencode(query, doseq=True)
    cleaned_url = parsed._replace(query=cleaned_query)
    return urlunparse(cleaned_url)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/fetch-preview")
def fetch_preview():
    url = request.args.get("url")
    url = strip_playlist_param(url)

    ydl_opts = {"quiet": True, "no_warnings": True}
    formats = []

    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        if info.get("_type") == "playlist" and info.get("entries"):
            info = info["entries"][0]

        video_id = info.get("id")
        all_formats = info.get("formats", [])

        resolutions = set()
        for f in all_formats:
            if f.get("vcodec") != "none":
                height = f.get("height")
                if height:
                    resolutions.add(str(height))

        resolutions = sorted(resolutions, key=lambda h: int(h))
        resolutions.append("audio")

    return jsonify({"video_id": video_id, "formats": resolutions})


@app.route("/api/start-download", methods=["POST"])
def start_download():
    data = request.get_json()
    url = data.get("url")
    quality = data.get("quality")

    url = strip_playlist_param(url)

    with YoutubeDL({"quiet": True, "no_warnings": True, "extract_flat": True}) as ydl:
        info = ydl.extract_info(url, download=False)
        if info.get("_type") == "playlist" and info.get("entries"):
            first = info["entries"][0]
            url = f"https://www.youtube.com/watch?v={first['id']}"

    download_id = str(uuid.uuid4())
    temp_dir = tempfile.mkdtemp()
    downloads[download_id] = {"progress": 0, "status": "starting", "file_path": None}

    def progress_hook(d):
        if d["status"] == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate") or 1
            downloaded = d.get("downloaded_bytes", 0)
            downloads[download_id]["progress"] = int(downloaded / total * 100)
            downloads[download_id]["status"] = "downloading"

    def download():
        try:
            if quality == "audio":
                fmt = "bestaudio"
                postprocessors = [
                    {
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "mp3",
                        "preferredquality": "192",
                    }
                ]
            else:
                # Exclude Opus audio in video downloads
                fmt = f"bestvideo[height={quality}]+bestaudio[acodec!=opus]/best[height={quality}]"
                postprocessors = []

            ydl_opts = {
                "format": fmt,
                "outtmpl": os.path.join(temp_dir, "%(title)s.%(ext)s"),
                "progress_hooks": [progress_hook],
                "ffmpeg_location": FFMPEG_PATH,
                "quiet": True,
                "no_warnings": True,
                "noplaylist": True,
                "merge_output_format": "mp4",
                "postprocessors": postprocessors,
            }
            with YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            time.sleep(1)

            for file in os.listdir(temp_dir):
                path = os.path.join(temp_dir, file)
                if os.path.isfile(path) and os.path.getsize(path) > 1000:
                    downloads[download_id]["file_path"] = path
                    downloads[download_id]["status"] = "done"
                    return

            downloads[download_id]["status"] = "error: file not written"
        except Exception as e:
            downloads[download_id]["status"] = f"error: {e}"

    threading.Thread(target=download, daemon=True).start()
    return jsonify({"download_id": download_id})


@app.route("/api/progress/<download_id>")
def get_progress(download_id):
    data = downloads.get(download_id)
    if not data:
        return jsonify({"status": "error: download not found"}), 404
    return jsonify({"status": data["status"], "progress": data["progress"]})


@app.route("/api/get-file/<download_id>")
def get_file(download_id):
    data = downloads.get(download_id)
    if not data:
        return jsonify({"error": "Download ID not found"}), 404

    file_path = data.get("file_path")

    wait_time = 0
    while (not file_path or not os.path.exists(file_path) or os.path.getsize(file_path) < 1000) and wait_time < 10:
        time.sleep(0.5)
        wait_time += 0.5
        file_path = data.get("file_path")

    if not file_path or not os.path.exists(file_path) or os.path.getsize(file_path) < 1000:
        return jsonify({"error": "File not ready. Please try again."}), 400

    try:
        return send_file(file_path, as_attachment=True)
    finally:
        shutil.rmtree(os.path.dirname(file_path), ignore_errors=True)
        downloads.pop(download_id, None)


if __name__ == "__main__":
    app.run(debug=True)
