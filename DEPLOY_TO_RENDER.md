# Deploy Media Toolkit to Render.com 🚀

Complete step-by-step guide to deploy your Media Toolkit to the internet with FFmpeg support.

---

## Prerequisites

1. **GitHub Account** - Create one at https://github.com if you don't have it
2. **Render.com Account** - Sign up at https://render.com (free)
3. **Git Installed** - Download from https://git-scm.com/downloads

---

## Step 1: Push Your Code to GitHub

### 1.1 Initialize Git Repository (if not already done)

Open PowerShell in your `media-toolkit` folder:

```powershell
cd C:\Users\User\Desktop\software\media-toolkit

# Initialize git (if not already initialized)
git init

# Check status
git status
```

### 1.2 Stage All Files

```powershell
# Add all files
git add .

# Verify what will be committed
git status
```

### 1.3 Create Initial Commit

```powershell
# Commit with message
git commit -m "Initial commit - Media Toolkit with FFmpeg support"
```

### 1.4 Create GitHub Repository

1. Go to https://github.com/new
2. Repository name: `media-toolkit`
3. Description: "Media processing toolkit with image conversion, PDF tools, and audio extraction"
4. Keep it **Public** (required for Render free tier)
5. **Don't** initialize with README (you already have one)
6. Click **"Create repository"**

### 1.5 Push to GitHub

GitHub will show you commands. Use these:

```powershell
# Add GitHub as remote (replace YOUR-USERNAME)
git remote add origin https://github.com/YOUR-USERNAME/media-toolkit.git

# Push code
git branch -M main
git push -u origin main
```

**Your code is now on GitHub!** ✅

---

## Step 2: Deploy to Render.com

### 2.1 Sign Up for Render

1. Go to https://render.com
2. Click **"Get Started"**
3. Sign up with GitHub (recommended) or email
4. Verify your email if needed

### 2.2 Create New Web Service

1. From Render Dashboard, click **"New +"**
2. Select **"Web Service"**
3. Click **"Build and deploy from a Git repository"**
4. Click **"Connect account"** to link your GitHub

### 2.3 Connect Your Repository

1. Render will show your GitHub repositories
2. Find `media-toolkit` in the list
3. Click **"Connect"**

### 2.4 Configure the Service

Render will auto-detect the Docker setup. Fill in these settings:

**Basic Settings:**
- **Name**: `media-toolkit` (or choose your own)
- **Region**: `Oregon (US West)` (or closest to you)
- **Branch**: `main`
- **Environment**: `Docker` ✅ (should auto-detect)

**Instance Type:**
- Select **"Free"** (0$/month)

**Advanced Settings (Optional):**
- **Health Check Path**: `/health` (already configured in render.yaml)

### 2.5 Add Environment Variable (Optional)

If you want to use the AI Image Editor (Phase 7):

1. Scroll to **"Environment Variables"**
2. Click **"Add Environment Variable"**
3. Key: `GOOGLE_API_KEY`
4. Value: `your-actual-api-key` (get from Google AI Studio)
5. Click **"Add"**

**Note**: You can skip this for now and add it later when you implement Phase 7.

### 2.6 Deploy!

1. Scroll to bottom
2. Click **"Create Web Service"**

**Render will now:**
- ✅ Clone your repository
- ✅ Build the Docker image (includes FFmpeg)
- ✅ Deploy to the internet
- ✅ Give you a public URL

---

## Step 3: Monitor Deployment

### 3.1 Watch the Build

You'll see a log screen showing:

```
==> Cloning from https://github.com/YOUR-USERNAME/media-toolkit...
==> Building Docker image...
==> Installing FFmpeg...
==> Installing Python packages...
==> Starting service...
==> Your service is live at https://media-toolkit-xxxx.onrender.com
```

**Build time**: ~5-10 minutes (first time)

### 3.2 Check for Success

Look for these lines:
```
✓ Upload directory: /app/uploads
✓ Output directory: /app/outputs
✓ Server running on http://0.0.0.0:8000
==> Live on https://media-toolkit-xxxx.onrender.com
```

---

## Step 4: Test Your Deployment

### 4.1 Visit Your App

Click the URL Render gives you (looks like `https://media-toolkit-xxxx.onrender.com`)

You should see your Media Toolkit home page! 🎉

### 4.2 Test Features

1. **Image Conversion**: ✅ Should work
2. **PDF Tools**: ✅ Should work
3. **Audio Extraction**: ✅ Should work (FFmpeg is installed!)

### 4.3 Verify FFmpeg

Try extracting audio from a video:
1. Click "Audio Extraction"
2. Upload a video file
3. Select format (MP3)
4. Click "Extract Audio"
5. ✅ Should work perfectly!

---

## Step 5: Manage Your Deployment

### 5.1 View Logs

From Render Dashboard:
1. Click on your service
2. Go to **"Logs"** tab
3. See real-time logs of your app

### 5.2 Update Your App

When you make changes to your code:

```powershell
# In your local media-toolkit folder
git add .
git commit -m "Add new feature"
git push
```

**Render automatically redeploys** when you push to GitHub! 🚀

### 5.3 Custom Domain (Optional)

Free tier includes:
- Custom domain support
- Automatic HTTPS
- `yourapp.onrender.com` subdomain

To add custom domain:
1. Go to **"Settings"** tab
2. Scroll to **"Custom Domains"**
3. Add your domain (e.g., `media-toolkit.yoursite.com`)

---

## Important Notes About Free Tier

### ✅ What You Get (Free Forever)
- 750 hours/month runtime
- FFmpeg fully working
- Automatic HTTPS
- Automatic deployments
- Public URL

### ⚠️ Limitations
- **Spins down after 15 minutes** of inactivity
  - First request after sleep takes ~30 seconds to wake up
  - Subsequent requests are fast
- 512 MB RAM
- Shared CPU
- No persistent storage (uploads/outputs are temporary)

### 💡 Solutions for Limitations

**Keep app alive (optional):**
1. Use a service like UptimeRobot.com (free)
2. Ping your `/health` endpoint every 10 minutes
3. App stays awake 24/7

**Storage:**
- Files in `uploads/` and `outputs/` are deleted when app restarts
- This is fine for a processing tool (files are temporary anyway)
- For permanent storage, upgrade to paid tier or use cloud storage

---

## Troubleshooting

### Build Failed

**Problem**: "Error building Docker image"

**Solution**: Check logs for specific error. Common issues:
- Missing files: Make sure you committed all files
- Python errors: Check requirements.txt has all dependencies

### App Won't Start

**Problem**: "Service failed to start"

**Solution**:
1. Check logs for error messages
2. Test locally: `docker build -t media-toolkit .`
3. Verify all files are pushed to GitHub

### FFmpeg Not Working

**Problem**: "FFmpeg is not installed" error

**Solution**:
1. Verify Dockerfile includes `ffmpeg` installation
2. Check build logs show "Installing FFmpeg"
3. Redeploy if needed

### 502 Bad Gateway

**Problem**: Site shows 502 error

**Solution**:
- App is probably sleeping (free tier)
- Wait 30 seconds and refresh
- Or app crashed - check logs

---

## Cost Summary

| Item | Cost |
|------|------|
| GitHub (Public Repo) | **FREE** |
| Render Free Tier | **FREE** |
| Domain (Optional) | ~$10-15/year |
| **Total** | **$0/month** |

---

## Next Steps

✅ **You're live on the internet!**

Now you can:
1. Share the URL with anyone
2. Use it from any device
3. Process media files online
4. Continue building Phases 5-7

**Your deployed app includes:**
- ✅ Image Conversion (working)
- ✅ PDF Tools (working)
- ✅ Audio Extraction (working with FFmpeg!)
- ⏳ Video Splitting (Phase 5 - coming soon)
- ⏳ Video Compression (Phase 6 - coming soon)
- ⏳ AI Image Editor (Phase 7 - coming soon)

---

## Alternative: Deploy to Other Platforms

The same Dockerfile works on:
- **Railway.app** - Similar to Render, also has free tier
- **Fly.io** - Free allowance, more control
- **Google Cloud Run** - Pay per use, very cheap
- **AWS ECS** - More complex, enterprise-grade
- **Your own VPS** - DigitalOcean, Linode, etc.

---

## Need Help?

Common commands:

```powershell
# View local git status
git status

# Pull latest changes from GitHub
git pull

# Force push (if needed)
git push --force

# View git history
git log --oneline

# Create new branch
git checkout -b new-feature
```

**Render Dashboard**: https://dashboard.render.com

**GitHub Repo**: https://github.com/YOUR-USERNAME/media-toolkit

---

## 🎉 Congratulations!

Your Media Toolkit is now live on the internet with full FFmpeg support!

**Share your app**: `https://media-toolkit-xxxx.onrender.com`

Users can now:
- Convert images online
- Merge/split PDFs
- Extract audio from videos
- All from their browser, no software installation needed!
