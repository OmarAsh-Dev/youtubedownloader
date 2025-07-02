# 🎬 YouTube Downloader Flask App

A simple **YouTube video and audio downloader** built with **Flask**, **yt-dlp**, and **FFmpeg**.
Supports selecting video quality and downloading audio-only MP3.

---

## ✨ Features

✅ Download YouTube videos in selectable resolutions (360p, 720p, 1080p, etc.)
✅ Download audio-only as MP3
✅ Progress bar during download
✅ Video preview embedded before download
✅ Clean, responsive frontend UI

---

## 🚀 Getting Started

### 1️⃣ Clone the repository

```bash
[git clone https://github.com/yourusername/youtubedownloader.git](https://github.com/OmarAsh-Dev/youtubedownloader.git)
cd youtubedownloader
```

---

### 2️⃣ Create and activate a virtual environment

**Windows:**

```powershell
python -m venv venv
venv\Scripts\activate
```

**macOS/Linux:**

```bash
python3 -m venv venv
source venv/bin/activate
```

---

### 3️⃣ Install dependencies

```bash
pip install -r requirements.txt
```

**`requirements.txt` should contain:**

```
Flask
yt-dlp
```

---

### 4️⃣ Download and configure FFmpeg

* Download FFmpeg binaries from [ffmpeg.org](https://ffmpeg.org/download.html).
* Extract them and **note the path** to the `ffmpeg.exe` (Windows) or `ffmpeg` binary (macOS/Linux).
* In `app.py`, update:

  ```python
  FFMPEG_PATH = r"C:\path\to\ffmpeg\bin\ffmpeg.exe"
  ```

  **Tip:** Use raw string literals (`r"..."`) for Windows paths.

---

### 5️⃣ Run the application

```bash
python app.py
```

Visit [http://127.0.0.1:5000](http://127.0.0.1:5000) in your browser.

---

## 🛠️ Project Structure

```
.
├── app.py
├── templates/
│   └── index.html
├── static/
│   └── styles/
│       └── style.css
└── requirements.txt
```

---

## ❤️ Credits

* [yt-dlp](https://github.com/yt-dlp/yt-dlp)
* [FFmpeg](https://ffmpeg.org/)

---

## ⚠️ Disclaimer

This project is for educational purposes only.
Always respect copyright laws and YouTube's terms of service.
