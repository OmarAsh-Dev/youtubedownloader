from flask import Flask, request, jsonify, send_from_directory, render_template
import os
import yt_dlp


app = Flask(__name__)

DOWNLOAD_FOLDER = os.path.join(os.path.expanduser('~'), 'Downloads')

if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/fetch-preview', methods=['GET'])
def fetch_preview():
    url = request.args.get('url')

    if not url:
        return jsonify({'error': 'No URL provided'}), 400

    try:
        # Use yt-dlp to extract video ID
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(url, download=False)
            video_id = info.get('id')
        return jsonify({'video_id': video_id})

    except Exception as e:
        app.logger.error(f"Error fetching video preview: {e}")
        return jsonify({'error': f"Server error: {e}"}), 500

@app.route('/download', methods=['POST'])
def download():
    data = request.json
    app.logger.debug(f"Received data: {data}")
    url = data.get('url')

    if not url:
        app.logger.error('No URL provided in request')
        return jsonify({'error': 'URL must be provided'}), 400

    try:
        # Configure yt-dlp options
        ydl_opts = {
            'format': 'best[ext=mp4]',
            'outtmpl': os.path.join(DOWNLOAD_FOLDER, '%(title)s.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
        }
        
        # Download the video
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)
            
        return jsonify({'message': 'Download completed', 'file': os.path.basename(file_path)})
    
    except Exception as e:
        app.logger.error(f"Error downloading video: {e}")
        return jsonify({'error': f"Server error: {e}"}), 500

@app.route('/downloads/<filename>')
def serve_file(filename):
    return send_from_directory(DOWNLOAD_FOLDER, filename)

if __name__ == '__main__':
    app.run(debug=True)
