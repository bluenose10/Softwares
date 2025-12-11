# Deployment Quick Start 🚀

## 5-Minute Deploy to Render.com

### Prerequisites
- ✅ GitHub account (sign up at github.com)
- ✅ Render account (sign up at render.com)
- ✅ Git installed on your computer

---

## Step 1: Push to GitHub (2 minutes)

```powershell
# In your media-toolkit folder
cd C:\Users\User\Desktop\software\media-toolkit

# Initialize git
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit"

# Create repo on GitHub.com, then:
git remote add origin https://github.com/YOUR-USERNAME/media-toolkit.git
git branch -M main
git push -u origin main
```

---

## Step 2: Deploy to Render (3 minutes)

1. Go to https://render.com/dashboard
2. Click **"New +"** → **"Web Service"**
3. Click **"Build and deploy from Git repository"**
4. Connect your GitHub and select `media-toolkit` repo
5. Render auto-detects Docker ✅
6. Select **"Free"** plan
7. Click **"Create Web Service"**

**That's it!** ☕ Wait 5-10 minutes for build.

---

## Your App is Live!

URL: `https://media-toolkit-xxxx.onrender.com`

### What Works:
- ✅ Image Conversion
- ✅ PDF Tools (Merge/Split)
- ✅ Audio Extraction (**FFmpeg included!**)

### Free Tier Details:
- **Cost**: $0/month forever
- **Caveat**: Sleeps after 15 min inactivity (wakes in 30 sec)
- **Storage**: Temporary (perfect for file processing)

---

## Update Your App

```powershell
# Make changes to your code, then:
git add .
git commit -m "Updated feature"
git push
```

Render **auto-deploys** on push! 🎉

---

## Test FFmpeg is Working

1. Visit your deployed URL
2. Click "Audio Extraction"
3. Upload any video (MP4, etc.)
4. Extract to MP3
5. ✅ Downloads successfully = FFmpeg working!

---

## Files Created for Deployment

| File | Purpose |
|------|---------|
| `Dockerfile` | Builds container with FFmpeg |
| `.dockerignore` | Excludes unnecessary files |
| `render.yaml` | Render configuration (optional) |

**No changes needed** - these files are ready to go!

---

## Troubleshooting

**Build failed?**
- Check Render logs for errors
- Verify all files are on GitHub: `git status`

**App shows 502?**
- Wait 30 seconds (waking from sleep)
- Check Render dashboard for errors

**FFmpeg not working?**
- Verify Dockerfile has `apt-get install -y ffmpeg`
- Check build logs show "Installing FFmpeg"

---

## Next: Share Your App!

Your app is now live at:
```
https://media-toolkit-xxxx.onrender.com
```

Share this URL and anyone can use your Media Toolkit!

**Full guide**: See [DEPLOY_TO_RENDER.md](DEPLOY_TO_RENDER.md) for detailed instructions.
