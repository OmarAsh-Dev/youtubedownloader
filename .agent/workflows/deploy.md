---
description: Deploy YouTube Downloader to Render
---

# Deploy YouTube Downloader to Render

This workflow guides you through deploying the YouTube Downloader Flask application to Render's free tier.

## Prerequisites

1. A [Render account](https://render.com) (sign up for free)
2. Your code pushed to a Git repository (GitHub, GitLab, or Bitbucket)
3. FFmpeg will be automatically installed during deployment

---

## Step 1: Push Your Code to Git

If you haven't already, push your code to GitHub:

```bash
git add .
git commit -m "Prepare for Render deployment"
git push origin main
```

---

## Step 2: Create a New Web Service on Render

1. Log in to [Render Dashboard](https://dashboard.render.com/)
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub/GitLab repository
4. Select the `youtubedownloader` repository

---

## Step 3: Configure the Web Service

Use the following settings:

| Setting | Value |
|---------|-------|
| **Name** | `youtube-downloader` (or your preferred name) |
| **Region** | Choose closest to you |
| **Branch** | `main` (or your default branch) |
| **Runtime** | `Python 3` |
| **Build Command** | `chmod +x build.sh && ./build.sh` |
| **Start Command** | `gunicorn app:app` |
| **Instance Type** | `Free` |

---

## Step 4: Add Environment Variables (Optional)

In the **Environment** section, you can add:

| Key | Value | Description |
|-----|-------|-------------|
| `PYTHON_VERSION` | `3.11.0` | Python version to use |
| `PORT` | `10000` | Port (Render sets this automatically) |

---

## Step 5: Deploy

1. Click **"Create Web Service"**
2. Render will automatically:
   - Install dependencies from `requirements.txt`
   - Run the build script to install FFmpeg
   - Start your Flask app with Gunicorn

The deployment process takes **5-10 minutes**. Watch the logs for any errors.

---

## Step 6: Access Your App

Once deployed, Render provides a URL like:
```
https://youtube-downloader-xxxx.onrender.com
```

Visit this URL to access your YouTube downloader!

---

## Troubleshooting

### Build Fails
- Check the **Logs** tab in Render dashboard
- Ensure `build.sh` has execute permissions
- Verify all dependencies in `requirements.txt`

### FFmpeg Not Found
- Ensure `build.sh` ran successfully during build
- Check that `FFMPEG_PATH` in `app.py` uses the environment variable

### App Crashes on Startup
- Check that `gunicorn` is in `requirements.txt`
- Verify the start command is `gunicorn app:app`
- Review logs for Python errors

### Free Tier Limitations
- **Spins down after 15 minutes of inactivity** (first request may be slow)
- **750 hours/month** of usage
- **Limited disk space** - temp files are cleaned up, but large downloads may fill disk

---

## Updating Your Deployment

To deploy updates:

```bash
git add .
git commit -m "Update description"
git push origin main
```

Render will **automatically redeploy** when you push to your connected branch.

---

## Notes

- ⚠️ **Legal Notice**: Ensure you comply with YouTube's Terms of Service
- 🔒 **Security**: This app has no authentication - anyone with the URL can use it
- 💰 **Costs**: Free tier is fine for personal use; consider upgrading for heavy usage
- 📦 **Storage**: Downloaded files are temporary and deleted after sending to user
