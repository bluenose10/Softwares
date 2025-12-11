# Phase 4: Audio Extraction - Complete ✅

## What Was Built

### Backend
- **audio_service.py** - FFmpeg-based audio extraction
  - `extract_audio()` - Extract audio using FFmpeg subprocess
  - `get_video_info()` - Get video metadata using ffprobe
  - `format_duration()` - Format seconds to HH:MM:SS
  - `check_ffmpeg_installed()` - Verify FFmpeg availability
  - `check_ffprobe_installed()` - Verify ffprobe availability
  - `get_supported_formats()` - List video inputs and audio outputs
  - `validate_video_file()` - Validate video files

- **audio.py router** - API endpoints
  - `POST /api/audio/extract` - Extract audio from video
  - `POST /api/audio/info` - Get video information
  - `GET /api/audio/formats` - List supported formats
  - `GET /api/audio/check-ffmpeg` - Check FFmpeg availability

### Supported Formats

**Video Inputs:**
- MP4, MKV, AVI, MOV, WEBM, FLV, WMV, M4V, MPEG, MPG, 3GP

**Audio Outputs:**
- MP3 (libmp3lame)
- AAC (aac)
- WAV (pcm_s16le) - lossless
- FLAC (flac) - lossless
- OGG (libvorbis)

**Bitrate Options (for lossy formats):**
- 64 kbps (low)
- 128 kbps (standard)
- 192 kbps (good) - default
- 256 kbps (high)
- 320 kbps (maximum)

### Frontend
- **audio.js** - Full audio extraction UI logic
  - FFmpeg availability check on load
  - Shows warning if FFmpeg not installed
  - Video file upload with validation
  - Video info display (duration, size, codecs)
  - Format selector with bitrate options
  - Conditional bitrate display (only for lossy formats)
  - Extract button with loading state
  - Auto-download extracted audio
  - Success result display

- **Updated index.html** - Complete UI
  - Video upload zone
  - Video info card (responsive grid)
  - Format selector (MP3, AAC, WAV, FLAC, OGG)
  - Bitrate selector (conditional visibility)
  - Extract button
  - Result display

- **Updated styles.css** - Audio-specific styles
  - Video info card styling
  - Format/bitrate button groups
  - Result card with success state
  - Loading spinner animation
  - Responsive video info grid

## Installation

### 1. Install FFmpeg (REQUIRED)

**Windows:**
1. Download from https://ffmpeg.org/download.html
2. Extract to `C:\ffmpeg`
3. Add `C:\ffmpeg\bin` to PATH
4. Restart terminal/PowerShell
5. Verify: `ffmpeg -version`

**macOS:**
```bash
brew install ffmpeg
```

**Linux:**
```bash
# Ubuntu/Debian
sudo apt install ffmpeg

# Fedora/RHEL
sudo yum install ffmpeg
```

### 2. Restart the Server

```bash
# Stop server (Ctrl+C)
# Restart
uvicorn app.main:app --reload
```

## Testing Guide

### Test 1: FFmpeg Check

1. Navigate to http://127.0.0.1:8000
2. Click "Audio Extraction" card
3. **If FFmpeg is installed:**
   - ✅ Upload zone shows normally
4. **If FFmpeg NOT installed:**
   - ✅ Red warning icon appears
   - ✅ Message: "FFmpeg Not Installed"
   - ✅ Link to download FFmpeg

### Test 2: Video Info Display

1. With FFmpeg installed, click Audio Extraction
2. Upload a video file (MP4, MKV, etc.)
3. ✅ "Analyzing video..." spinner appears
4. ✅ Video info card displays:
   - Filename
   - Duration (formatted as MM:SS or H:MM:SS)
   - File size
   - Video codec (e.g., H.264)
   - Audio codec (e.g., AAC)

### Test 3: Extract to MP3

1. Upload a video
2. Keep MP3 format selected (default)
3. Select bitrate (try 192 kbps - default)
4. Click "Extract Audio"
5. ✅ Button shows "Extracting..."
6. ✅ Audio file auto-downloads
7. ✅ Success message appears with file size
8. ✅ Play the MP3 to verify

### Test 4: Lossless Formats (WAV/FLAC)

1. Upload a video
2. Select "WAV" or "FLAC" format
3. ✅ Bitrate selector DISAPPEARS (lossless doesn't use bitrate)
4. Click "Extract Audio"
5. ✅ Audio extracts successfully
6. ✅ File size is larger than MP3 (lossless)

### Test 5: Bitrate Options

1. Upload a video
2. Select MP3 format
3. ✅ Bitrate buttons visible
4. Try each bitrate (64, 128, 192, 256, 320 kbps)
5. ✅ Lower bitrates = smaller files
6. ✅ Higher bitrates = larger files, better quality

### Test 6: Format Switching

1. Upload a video
2. Switch between formats:
   - MP3 → ✅ Bitrate visible
   - WAV → ✅ Bitrate hidden
   - AAC → ✅ Bitrate visible
   - FLAC → ✅ Bitrate hidden
   - OGG → ✅ Bitrate visible

### Test 7: Error Handling

Try these to test error handling:

**Video without audio:**
- Upload video-only file
- ✅ Error: "Video does not contain an audio stream"

**Corrupted file:**
- Upload broken/invalid video
- ✅ Error: "Video file is invalid or corrupted"

**Non-video file:**
- Upload image or text file
- ✅ Error: "Invalid video file"

### Test 8: Different Video Formats

Test with various video containers:
- MP4 → ✅ Works
- MKV → ✅ Works
- AVI → ✅ Works
- MOV → ✅ Works
- WEBM → ✅ Works

## API Testing

### Check FFmpeg Availability

```bash
curl http://127.0.0.1:8000/api/audio/check-ffmpeg
```

Expected response:
```json
{
  "ffmpeg_installed": true,
  "ffprobe_installed": true
}
```

### Get Video Info

```bash
curl -X POST http://127.0.0.1:8000/api/audio/info \
  -F "file=@video.mp4"
```

Expected response:
```json
{
  "filename": "video.mp4",
  "duration": 332.5,
  "duration_formatted": "5:32",
  "size": 25748362,
  "video_codec": "h264",
  "audio_codec": "aac",
  "has_audio": true
}
```

### Extract Audio

```bash
curl -X POST http://127.0.0.1:8000/api/audio/extract \
  -F "file=@video.mp4" \
  -F "format=mp3" \
  -F "bitrate=192" \
  --output audio.mp3
```

### List Supported Formats

```bash
curl http://127.0.0.1:8000/api/audio/formats
```

Expected response:
```json
{
  "video_inputs": ["mp4", "mkv", "avi", "mov", "webm", "flv", "wmv", "m4v", "mpeg", "mpg", "3gp"],
  "audio_outputs": ["mp3", "aac", "wav", "flac", "ogg"],
  "bitrate_options": [64, 128, 192, 256, 320],
  "formats_with_bitrate": ["mp3", "aac", "ogg"]
}
```

## Features Implemented

✅ **FFmpeg Integration**
- Subprocess calls to ffmpeg and ffprobe
- Availability checking
- Error handling for missing FFmpeg

✅ **Video Analysis**
- Duration extraction
- Codec detection
- Audio stream validation
- File size reporting

✅ **Audio Extraction**
- 5 output formats (MP3, AAC, WAV, FLAC, OGG)
- 5 bitrate options for lossy formats
- Lossless extraction (WAV, FLAC)
- Proper codec selection per format

✅ **UI/UX**
- FFmpeg warning system
- Loading spinner during analysis
- Video info card with metadata
- Conditional bitrate selector
- Format/bitrate button groups
- Success result display
- Toast notifications

✅ **Error Handling**
- Missing FFmpeg detection
- Invalid video files
- Videos without audio
- Corrupted files
- Extraction timeouts (5 min)

## Known Limitations

1. **FFmpeg Required**: Feature completely depends on FFmpeg
   - Clear warning shown if not installed
   - Link to download page provided

2. **Timeout**: 5-minute extraction limit
   - Very large files may timeout
   - Consider increasing for production

3. **No Progress**: Extraction shows loading state only
   - Future: Parse FFmpeg stderr for progress percentage

4. **Temp Files**: Input/output files remain until cleanup
   - Use cleanup endpoint manually
   - Future: Auto-cleanup after 1 hour

## FFmpeg Commands Used

**Get video info:**
```bash
ffprobe -v quiet -print_format json -show_format -show_streams video.mp4
```

**Extract to MP3:**
```bash
ffmpeg -i input.mp4 -vn -acodec libmp3lame -ab 192k output.mp3
```

**Extract to WAV (lossless):**
```bash
ffmpeg -i input.mp4 -vn -acodec pcm_s16le output.wav
```

**Extract to FLAC (lossless):**
```bash
ffmpeg -i input.mp4 -vn -acodec flac output.flac
```

## File Structure Changes

```
media-toolkit/
├── app/
│   ├── routers/
│   │   └── audio.py          [NEW]
│   └── services/
│       └── audio_service.py  [NEW]
├── static/
│   └── js/
│       └── audio.js          [NEW]
├── templates/
│   └── index.html            [UPDATED - Audio extraction UI]
├── static/css/
│   └── styles.css            [UPDATED - Video info & result styles]
└── app/
    └── main.py               [UPDATED - Audio router]
```

## Troubleshooting

### "FFmpeg Not Installed" Error

**Windows:**
1. Download FFmpeg from https://ffmpeg.org/download.html
2. Extract to `C:\ffmpeg`
3. Add `C:\ffmpeg\bin` to system PATH:
   - Search "Environment Variables"
   - Edit PATH variable
   - Add `C:\ffmpeg\bin`
4. Restart PowerShell
5. Test: `ffmpeg -version`

**macOS/Linux:**
```bash
# Install FFmpeg
brew install ffmpeg  # macOS
sudo apt install ffmpeg  # Ubuntu/Debian

# Verify
ffmpeg -version
ffprobe -version
```

### "Video does not contain audio" Error

- Some videos are video-only (no audio track)
- Extract audio from original source
- Or use video with audio track

### Extraction Very Slow

- Large files take time
- High bitrates process slower
- Consider lower bitrate for faster extraction
- Check disk space (output may be large)

## Next Steps

Ready for **Phase 5: Video Splitting**
- Split videos into N equal parts
- FFmpeg-based video segmentation
- Duration-based splitting
- ZIP download of segments

---

**Phase 4 Status**: ✅ Complete and Ready to Test

**IMPORTANT**: Install FFmpeg before testing!
