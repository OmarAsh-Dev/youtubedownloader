# Path to ffmpeg binary on your system. Keep this updated.
# In production (Render), ffmpeg is installed via build.sh and available in PATH
# In local development, use the configured path
FFMPEG_PATH = os.environ.get("FFMPEG_PATH") or shutil.which("ffmpeg") or r"C:\ffmpeg-7.1.1-essentials_build\bin\ffmpeg.exe"

# Helper to find ffprobe (try same dir as ffmpeg, then system PATH)
def find_ffprobe():
    # try same directory as FFMPEG_PATH
    try:
        ffmpeg_dir = os.path.dirname(FFMPEG_PATH)
        candidate = os.path.join(ffmpeg_dir, 'ffprobe.exe' if os.name == 'nt' else 'ffprobe')
        if os.path.exists(candidate):
            return candidate
    except Exception:
        pass

    # try PATH
    which = shutil.which('ffprobe')
    if which:
        return which

    # fallback: replace 'ffmpeg' with 'ffprobe' in the configured path
    try:
        alt = FFMPEG_PATH.replace('ffmpeg.exe', 'ffprobe.exe').replace('ffmpeg', 'ffprobe')
        if os.path.exists(alt):
            return alt
    except Exception:
        pass

    return None

FFPROBE_PATH = find_ffprobe()


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

    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        if info.get("_type") == "playlist" and info.get("entries"):
            info = info["entries"][0]

        video_id = info.get("id")
        all_formats = info.get("formats", []) or []

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

    # Resolve playlist -> first item (same approach you had)
    with YoutubeDL({"quiet": True, "no_warnings": True, "extract_flat": True}) as ydl:
        info = ydl.extract_info(url, download=False)
        if info.get("_type") == "playlist" and info.get("entries"):
            first = info["entries"][0]
            url = f"https://www.youtube.com/watch?v={first['id']}"

    download_id = str(uuid.uuid4())
    temp_dir = tempfile.mkdtemp()
    downloads[download_id] = {"progress": 0, "status": "starting", "file_path": None}

    def progress_hook(d):
        try:
            if d.get("status") == "downloading":
                total = d.get("total_bytes") or d.get("total_bytes_estimate") or 1
                downloaded = d.get("downloaded_bytes", 0)
                pct = int(downloaded / max(total, 1) * 100)
                downloads[download_id]["progress"] = max(0, min(100, pct))
                downloads[download_id]["status"] = "downloading"
        except Exception:
            pass

    def probe_audio_codec(path):
        """Return codec name for first audio stream (e.g., 'opus', 'aac'), or None if not available."""
        if not FFPROBE_PATH:
            return None
        try:
            cmd = [FFPROBE_PATH, "-v", "error", "-select_streams", "a:0",
                   "-show_entries", "stream=codec_name", "-of",
                   "default=nokey=1:noprint_wrappers=1", path]
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False)
            out = (res.stdout or "").strip()
            return out if out else None
        except Exception:
            return None

    def reencode_to_aac(input_path, bitrate="192k"):
        """Re-encode the audio to AAC while copying video. Returns path to new file or None on failure."""
        try:
            dirn = os.path.dirname(input_path)
            base = os.path.splitext(os.path.basename(input_path))[0]
            out_path = os.path.join(dirn, f"{base}.aac_reencoded.mp4")

            cmd = [FFMPEG_PATH, "-y", "-i", input_path,
                   "-c:v", "copy", "-c:a", "aac", "-b:a", bitrate,
                   "-movflags", "+faststart", out_path]
            # run and capture output
            subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

            if os.path.exists(out_path) and os.path.getsize(out_path) > 1000:
                return out_path
            return None
        except Exception:
            return None

    def download():
        try:
            # helper: is ffmpeg available (configured path or on PATH)
            def ffmpeg_available():
                if FFMPEG_PATH and os.path.exists(FFMPEG_PATH) and os.access(FFMPEG_PATH, os.X_OK):
                    return True
                return bool(shutil.which("ffmpeg"))

            # initialize postprocessors list (avoid UnboundLocalError)
            postprocessors = []

            # Try different youtube "player_client" extractor args until we get usable format URLs
            EXTRACTOR_CLIENT_TRIES = [
                {},
                {"player_client": ["android", "web"]},
                {"player_client": ["tv", "android", "web"]},
                {"player_client": ["mweb", "web"]},
                {"player_client": ["ios", "web"]},
            ]

            def find_working_extractor_args(url, base_opts):
                for args in EXTRACTOR_CLIENT_TRIES:
                    try_opts = dict(base_opts)
                    if args:
                        try_opts["extractor_args"] = {"youtube": args}
                    else:
                        try_opts.pop("extractor_args", None)
                    try_opts["quiet"] = True
                    try:
                        with YoutubeDL(try_opts) as ydl:
                            info = ydl.extract_info(url, download=False)
                    except Exception:
                        continue

                    fmts = info.get("formats") or []
                    usable = False
                    for f in fmts:
                        if f.get("url"):
                            ext = (f.get("ext") or "").lower()
                            if ext == "mhtml":
                                continue
                            vcodec = f.get("vcodec")
                            if vcodec and vcodec != "none":
                                usable = True
                                break
                            if f.get("height") or f.get("acodec"):
                                usable = True
                                break
                    if usable:
                        return {"youtube": args} if args else {}
                return {}

            # Prepare base options for extraction probing
            base_check_opts = {
                "ffmpeg_location": FFMPEG_PATH,
                "socket_timeout": 60,
                "retries": 2,
                "no_warnings": True,
                "quiet": True,
                "noplaylist": True,
            }

            found_extractor_args = find_working_extractor_args(url, base_check_opts)
            ffmpeg_ok = ffmpeg_available()

            # Build the desired format string depending on quality and ffmpeg availability
            merge_format = None
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
                # prefer adaptive (video-only + audio) if ffmpeg is available
                if ffmpeg_ok:
                    fmt = f"bestvideo[height<={quality}]+bestaudio/best[height<={quality}]/best"
                    merge_format = "mp4"
                else:
                    fmt = f"best[height<={quality}]/best"
                    merge_format = None

            ydl_opts = {
                "format": fmt,
                "outtmpl": os.path.join(temp_dir, "%(title)s.%(ext)s"),
                "progress_hooks": [progress_hook],
                "ffmpeg_location": FFMPEG_PATH if ffmpeg_ok else None,
                "quiet": True,
                "no_warnings": True,
                "noplaylist": True,
                "postprocessors": postprocessors,
                "socket_timeout": 60,
                "retries": 20,
                "fragment_retries": 20,
                "geo_bypass": True,
                "concurrent_fragments": 10  ,              # parallel fragment fetches
            }
            if merge_format and ffmpeg_ok:
                ydl_opts["merge_output_format"] = merge_format
            if found_extractor_args:
                ydl_opts["extractor_args"] = found_extractor_args

            # Attempt primary download, with a fallback to 'best' if format not available
            try:
                with YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])
            except Exception as exc_primary:
                err_text = str(exc_primary).lower()
                # If yt-dlp complains about format, retry with relaxed 'best'
                if "requested format is not available" in err_text or "format not available" in err_text:
                    ydl_opts["format"] = "best"
                    ydl_opts.pop("merge_output_format", None)
                    with YoutubeDL(ydl_opts) as ydl:
                        ydl.download([url])
                else:
                    raise

            # Give downloads a moment to flush files
            time.sleep(1)

            # pick the largest non-empty file in the temp dir as the downloaded artifact
            found_path = None
            for file in os.listdir(temp_dir):
                path = os.path.join(temp_dir, file)
                if os.path.isfile(path) and os.path.getsize(path) > 1000:
                    if not found_path or os.path.getsize(path) > os.path.getsize(found_path):
                        found_path = path

            if not found_path:
                downloads[download_id]["status"] = "error: file not written"
                return

            # Post-processing: re-encode Opus-in-MP4 to AAC if needed
            downloads[download_id]["status"] = "post-processing"
            lower = found_path.lower()
            if lower.endswith('.mp4') and FFPROBE_PATH:
                codec = probe_audio_codec(found_path)
                if codec == 'opus':
                    downloads[download_id]["status"] = "re-encoding audio to AAC"
                    reencoded = reencode_to_aac(found_path)
                    if reencoded:
                        try:
                            os.replace(reencoded, found_path)
                        except Exception:
                            found_path = reencoded

            downloads[download_id]["file_path"] = found_path
            downloads[download_id]["status"] = "done"
            downloads[download_id]["progress"] = 100
            return

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
    # Get port from environment variable (Render sets this) or use 5000 for local dev
    port = int(os.environ.get("PORT", 5000))
    # Only enable debug mode in local development
    debug = os.environ.get("FLASK_ENV") != "production"
    app.run(host="0.0.0.0", port=port, debug=debug)