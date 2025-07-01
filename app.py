from flask import Flask, request, jsonify, send_file, render_template
import yt_dlp
import tempfile
import os
import shutil

app = Flask(__name__, static_folder="static", template_folder="templates")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/fetch-preview", methods=["GET"])
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


@app.route("/api/download", methods=["POST"])
def download():
    url = request.json.get("url")
    if not url:
        return jsonify({"error": "URL must be provided"}), 400

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

        return send_file(
            file_path,
            as_attachment=True,
            download_name=filename,
            mimetype="video/mp4"
        )

    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    app.run(debug=True)
