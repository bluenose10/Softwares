# 🎬 Media Toolkit

A comprehensive web-based media processing SaaS application with AI-powered image generation and editing capabilities. Features an SEO-optimized landing page and 6 powerful tools for all your media needs.

## ✨ Features

### 1. 🖼️ Image Conversion
- Convert images between formats (JPG, PNG, WEBP, GIF, BMP, HEIC, HEIF)
- Batch conversion support
- Adjustable quality settings for lossy formats
- Preview before conversion

### 2. 📄 PDF Tools
- **Merge PDFs**: Combine multiple PDF files into one
- **Split PDFs**: Extract specific pages or split into individual pages
- Drag-and-drop reordering
- Preview PDF information

### 3. 🎵 Audio Extraction
- Extract audio from video files
- Multiple output formats (MP3, WAV, AAC, FLAC, OGG)
- Adjustable bitrate for compressed formats
- Support for all common video formats

### 4. ✂️ Video Splitting
- Split videos into equal parts
- Upload or use local file paths
- Preview split points before processing
- Download individual parts or ZIP archive

### 5. 🗜️ Video Compression
- **Target Size Mode**: Compress to specific file size
- **Quality Mode**: Choose quality preset (Low/Medium/High)
- **Resolution Mode**: Downscale to target resolution (4K/1440p/1080p/720p/480p/360p)
- Size estimation before compression
- Two-pass encoding for accurate results

### 6. 🤖 AI Image Editor
- **Image Generation**: Create images from text prompts using Imagen 4
  - 6 style presets (Photorealistic, Digital Art, Watercolor, Minimalist, 3D Render, Anime)
  - Multiple aspect ratios (1:1, 4:5, 9:16, 16:9)
  - Adjustable size (1K, 2K, 4K)
- **Image Editing**: Transform images with AI using Gemini 3 Pro Image
  - Remove background
  - Change artistic style
  - Add/remove elements
  - Enhance quality
  - Color correction
  - Custom prompts

## 🚀 Quick Start

### Prerequisites
- Python 3.11 or higher
- FFmpeg (for video/audio features)
- Google API key (for AI features)

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd media-toolkit
```

2. **Install Python dependencies**
```bash
pip install -r requirements.txt
```

3. **Install FFmpeg**

**Windows:**
- Download from [ffmpeg.org](https://ffmpeg.org/download.html)
- Add to PATH

**macOS:**
```bash
brew install ffmpeg
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get update
sudo apt-get install ffmpeg
```

4. **Configure environment variables**

Create a `.env` file in the project root:
```env
# Google Gemini API Key for AI Image Editor
# Get your key from: https://aistudio.google.com/apikey
GOOGLE_API_KEY=your_api_key_here

# Optional server configuration
HOST=127.0.0.1
PORT=8000
```

5. **Run the application**
```bash
python run.py
```

The application will be available at:
- **Landing Page**: `http://127.0.0.1:8000/`
- **App Dashboard**: `http://127.0.0.1:8000/app`

## 🌐 Deployment to Render.com

### Option 1: Blueprint Deployment

1. Push your code to GitHub
2. Go to [Render.com](https://render.com)
3. Click "New +" → "Blueprint"
4. Select your repository
5. Render will automatically detect `render.yaml`
6. Add your `GOOGLE_API_KEY` environment variable
7. Deploy!

### Option 2: Manual Deployment

1. Create a new Web Service on Render
2. Connect your repository
3. Configure:
   - **Environment**: Python
   - **Build Command**: `bash build.sh`
   - **Start Command**: `python run.py`
4. Add environment variables:
   - `GOOGLE_API_KEY`: Your Google API key
   - `HOST`: `0.0.0.0`
   - `PORT`: `8000`
5. Deploy!

## 📁 Project Structure

```
media-toolkit/
├── app/
│   ├── routers/          # API endpoints
│   │   ├── image.py
│   │   ├── pdf.py
│   │   ├── audio.py
│   │   ├── video.py
│   │   └── ai_image.py
│   ├── services/         # Business logic
│   │   ├── image_service.py
│   │   ├── pdf_service.py
│   │   ├── audio_service.py
│   │   ├── video_service.py
│   │   └── ai_image_service.py
│   ├── config.py         # Configuration
│   └── main.py           # FastAPI application
├── static/
│   ├── css/
│   │   └── styles.css    # Dark theme styles
│   └── js/
│       ├── main.js       # Core utilities
│       ├── image.js
│       ├── pdf.js
│       ├── audio.js
│       ├── video.js
│       ├── compress.js
│       └── ai-image.js
├── templates/
│   └── index.html        # Main HTML
├── uploads/              # Temporary uploads
├── outputs/              # Processed files
├── requirements.txt      # Python dependencies
├── render.yaml           # Render.com config
├── build.sh              # Build script
├── run.py                # Entry point
└── .env                  # Environment variables
```

## 🔧 API Endpoints

### Image Conversion
- `POST /api/image/convert` - Convert images

### PDF Tools
- `POST /api/pdf/merge` - Merge PDFs
- `POST /api/pdf/split` - Split PDF

### Audio Extraction
- `POST /api/audio/extract` - Extract audio from video

### Video Processing
- `POST /api/video/split` - Split video
- `POST /api/video/compress/target-size` - Compress to target size
- `POST /api/video/compress/quality` - Compress by quality
- `POST /api/video/compress/resolution` - Compress by resolution
- `POST /api/video/compress/estimate` - Estimate output size

### AI Image Editor
- `GET /api/ai-image/check-api-key` - Check if API key is configured
- `GET /api/ai-image/presets` - Get style and action presets
- `POST /api/ai-image/generate` - Generate image from prompt
- `POST /api/ai-image/edit` - Edit existing image

## 🛠️ Technologies Used

- **Backend**: FastAPI, Python 3.11
- **Frontend**: Vanilla JavaScript, HTML5, CSS3
- **Image Processing**: Pillow, pillow-heif
- **PDF Processing**: pypdf
- **Video/Audio**: FFmpeg
- **AI**: Google Gemini API (Imagen 4, Gemini 3 Pro Image)
- **Deployment**: Render.com

## 🚀 SEO & Marketing Features

### SEO-Optimized Landing Page
- Professional homepage at `/` with conversion-focused design
- Comprehensive meta tags (title, description, keywords)
- Open Graph tags for social media sharing
- Twitter Card meta tags
- Schema.org structured data (WebApplication, FAQPage)
- Semantic HTML with proper heading hierarchy
- Mobile-responsive design
- Fast page load with optimized assets

### SEO Infrastructure
- **Sitemap**: `/sitemap.xml` - Auto-indexed by search engines
- **Robots.txt**: `/robots.txt` - Crawler configuration
- **Clean URLs**: Semantic, keyword-rich URLs
- **Internal Linking**: Strategic linking between pages
- **Alt Text**: All images include descriptive alt attributes

### Key SEO Features
✓ **Landing Page** (`/`) - Marketing homepage with features, benefits, and CTAs
✓ **App Dashboard** (`/app`) - Full-featured tool interface
✓ **Sitemap XML** - All pages indexed for search engines
✓ **Robots.txt** - Proper crawler directives
✓ **Structured Data** - Rich snippets for better SERP display
✓ **Mobile-First** - Responsive design for all devices

## 📝 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GOOGLE_API_KEY` | Google Gemini API key | Required for AI features |
| `HOST` | Server host | `127.0.0.1` |
| `PORT` | Server port | `8000` |
| `MAX_UPLOAD_SIZE_MB` | Maximum upload size in MB | `500` |
| `TEMP_FILE_RETENTION_HOURS` | Hours to keep temp files | `1` |

## 🐛 Troubleshooting

### FFmpeg not found
**Error**: "FFmpeg is not installed"

**Solution**: Install FFmpeg and ensure it's in your system PATH
```bash
# Test FFmpeg installation
ffmpeg -version
```

### Google API Key errors
**Error**: "Google API Key Not Configured"

**Solution**:
1. Get an API key from [Google AI Studio](https://aistudio.google.com/apikey)
2. Add it to your `.env` file: `GOOGLE_API_KEY=your_key_here`
3. Restart the server

### Port already in use
**Error**: "Address already in use"

**Solution**: Change the port in `.env`:
```env
PORT=8080
```

### Upload fails for large files
**Solution**: Increase `MAX_UPLOAD_SIZE_MB` in `.env` or use local file path mode (for video features)

## 📄 License

This project is open source and available under the MIT License.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📧 Support

For issues and questions, please open an issue on GitHub.

---

Built with ❤️ using FastAPI and Google Gemini AI
