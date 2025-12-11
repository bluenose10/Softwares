# Revenue Protection - Usage Limits Enforced

## Overview

All API endpoints are now protected with usage limits to force users to upgrade to Pro and protect your revenue.

## What's Protected

### Free Tier Limits (Per IP Address)
- **5 conversions per day**
- **25MB max file size**
- **Resets every 24 hours**

### Pro Tier ($9/month)
- **Unlimited conversions**
- **500MB max file size**
- **No waiting**

## Enforcement Mechanism

### Middleware Decorator
Location: `app/middleware/usage_check.py`

```python
@require_usage_limit(file_size_mb=25)
```

This decorator:
1. Checks user's IP address
2. Verifies they haven't exceeded 5 conversions/day
3. Blocks request if limit reached (429 error)
4. Increments usage counter on success
5. Pro users bypass all limits

## Protected Endpoints

### ✅ Image Converter (`app/routers/image.py`)
- `/api/image/convert` - Image format conversion

### ✅ PDF Tools (`app/routers/pdf.py`)
- `/api/pdf/info` - PDF information
- `/api/pdf/merge` - Merge multiple PDFs
- `/api/pdf/split` - Split PDF into parts

### ✅ Audio Extractor (`app/routers/audio.py`)
- `/api/audio/info` - Video information
- `/api/audio/extract` - Extract audio from video

### ✅ Video Tools (`app/routers/video.py`)
- `/api/video/info` - Video information
- `/api/video/split` - Split video into parts
- `/api/video/compress/target-size` - Compress to target size
- `/api/video/compress/quality` - Compress by quality
- `/api/video/compress/resolution` - Compress by resolution
- `/api/video/compress/estimate` - Estimate compression

### ✅ AI Image Editor (`app/routers/ai_image.py`)
- `/api/ai-image/generate` - Generate images from text
- `/api/ai-image/edit` - Edit images with AI

## User Experience

### Free User Reaches Limit
```
HTTP 429 Too Many Requests

{
  "error": "Usage limit exceeded",
  "message": "Free limit of 5 conversions per day reached. Upgrade to Pro for unlimited conversions or wait 12 hours.",
  "upgrade_url": "/pricing"
}
```

### Bot Protection
- IP-based tracking prevents bot abuse
- File size limits prevent resource exhaustion
- Daily reset prevents persistent hammering

### Conversion Funnel
1. User tries 5 free conversions
2. Sees value of tools
3. Hits limit → 429 error
4. Frontend shows "Upgrade to Pro" popup
5. Redirects to `/pricing`
6. User pays $9/month
7. Unlimited access immediately

## Revenue Projections

With usage limits enforced:

| Free Users | Conversion Rate | Paying Users | Monthly Revenue |
|------------|----------------|--------------|-----------------|
| 1,000      | 5%             | 50           | $437            |
| 5,000      | 3%             | 150          | $1,311          |
| 10,000     | 2%             | 200          | $1,746          |
| 50,000     | 1%             | 500          | $4,365          |

**Key Insight**: Even 1% conversion rate from 10,000 free users = $1,746/month passive income

## Anti-Abuse Measures

### 1. IP-Based Tracking
- Prevents single user from creating multiple accounts
- Tracks usage per client IP address
- Simple but effective for MVP

### 2. File Size Limits
- Free: 25MB max (prevents resource exhaustion)
- Pro: 500MB max (prevents abuse while allowing real use)

### 3. Daily Reset
- Limits reset every 24 hours
- Encourages users to come back daily
- Builds habit before they pay

### 4. Pro Status Bypass
- Pro users checked first
- No limits, no delays
- Premium experience

## Limitations & Future Improvements

### Current Limitations
- **IP-based tracking** - Users on VPN or changing networks lose Pro status
- **No user accounts** - Can't track across devices
- **No email collection** - Can't re-market to free users

### Phase 2 Improvements (Optional)
1. Add user accounts (email + password)
2. Link Stripe customer ID to user account
3. Track Pro status by user ID, not IP
4. Email marketing to free users who hit limit
5. Analytics dashboard for conversion tracking

## Testing

### Test Free Tier Limit
```bash
# Use Image Converter 6 times
# 6th request should return 429 error

curl -X POST http://localhost:8000/api/image/convert \
  -F "file=@test.jpg" \
  -F "format=png" \
  -F "quality=85"

# After 5 requests:
# {"error":"Usage limit exceeded","message":"Free limit of 5 conversions per day reached..."}
```

### Test Pro Bypass
```bash
# After upgrading to Pro
# Should work unlimited times

# Check Pro status:
curl http://localhost:8000/api/usage/stats
# {"is_pro":true,"conversions_used":"unlimited",...}
```

## Summary

**Revenue Protection Status**: ✅ FULLY PROTECTED

- All conversion endpoints require usage limits
- Free users forced to upgrade after 5 uses
- Pro users get unlimited access
- Bots and abusers blocked by IP + file size limits

**Your money is protected. Users must pay to continue using your tools.**
