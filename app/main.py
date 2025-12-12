"""FastAPI application entry point for Media Toolkit."""

from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.requests import Request
from fastapi.responses import JSONResponse
from app.config import settings


# Initialize FastAPI app
app = FastAPI(
    title="Media Toolkit",
    description="A Swiss Army knife for media processing",
    version="1.0.0"
)

# Configure CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for local development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Configure templates
templates = Jinja2Templates(directory="templates")


@app.on_event("startup")
async def startup_event():
    """Create necessary directories on startup."""
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    settings.output_dir.mkdir(parents=True, exist_ok=True)
    print(f"[OK] Upload directory: {settings.upload_dir.absolute()}")
    print(f"[OK] Output directory: {settings.output_dir.absolute()}")

    # Clean up old temporary files on startup
    from app.services.cleanup_service import cleanup_uploads_and_outputs
    result = cleanup_uploads_and_outputs(
        settings.upload_dir,
        settings.output_dir,
        settings.temp_file_retention_hours
    )
    if result["total_deleted"] > 0:
        print(f"[OK] Cleaned up {result['total_deleted']} old temporary files")

    print(f"[OK] Server running on http://{settings.host}:{settings.port}")


@app.get("/")
async def root(request: Request):
    """Serve the landing page."""
    return templates.TemplateResponse("landing.html", {"request": request})


@app.get("/app")
async def app_page(request: Request):
    """Serve the main application dashboard."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/pricing")
async def pricing_page(request: Request):
    """Serve the pricing/upgrade page."""
    return templates.TemplateResponse("pricing.html", {"request": request})


@app.get("/terms")
async def terms_page(request: Request):
    """Serve the Terms of Service page."""
    return templates.TemplateResponse("terms.html", {"request": request})


@app.get("/privacy")
async def privacy_page(request: Request):
    """Serve the Privacy Policy page."""
    return templates.TemplateResponse("privacy.html", {"request": request})


@app.get("/success")
async def success_page(request: Request):
    """Serve the payment success page."""
    return templates.TemplateResponse("success.html", {"request": request})


@app.get("/api/usage/stats")
async def get_usage_stats(request: Request):
    """Get usage statistics for current user."""
    from app.services.usage_tracker import usage_tracker

    client_ip = request.client.host
    stats = usage_tracker.get_usage_stats(client_ip)

    return JSONResponse(stats)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return JSONResponse({
        "status": "healthy",
        "version": "1.0.0",
        "upload_dir": str(settings.upload_dir.absolute()),
        "output_dir": str(settings.output_dir.absolute())
    })


@app.get("/sitemap.xml")
async def sitemap():
    """Serve sitemap.xml for SEO."""
    from fastapi.responses import FileResponse
    return FileResponse(
        "static/sitemap.xml",
        media_type="application/xml"
    )


@app.get("/robots.txt")
async def robots():
    """Serve robots.txt for SEO."""
    from fastapi.responses import FileResponse
    return FileResponse(
        "static/robots.txt",
        media_type="text/plain"
    )


@app.post("/api/cleanup")
async def cleanup_temp_files():
    """Clean up old temporary files."""
    from app.services.cleanup_service import cleanup_uploads_and_outputs, get_cleanup_stats

    # Get stats before cleanup
    stats_before = get_cleanup_stats(settings.upload_dir, settings.output_dir)

    # Clean up files older than configured retention period
    cleanup_result = cleanup_uploads_and_outputs(
        settings.upload_dir,
        settings.output_dir,
        settings.temp_file_retention_hours
    )

    # Get stats after cleanup
    stats_after = get_cleanup_stats(settings.upload_dir, settings.output_dir)

    return JSONResponse({
        "success": True,
        "deleted_files": cleanup_result["total_deleted"],
        "before": stats_before,
        "after": stats_after
    })


@app.get("/api/cleanup/stats")
async def get_temp_stats():
    """Get statistics about temporary files."""
    from app.services.cleanup_service import get_cleanup_stats

    stats = get_cleanup_stats(settings.upload_dir, settings.output_dir)

    return JSONResponse({
        "success": True,
        "stats": stats,
        "retention_hours": settings.temp_file_retention_hours
    })


# Include routers
from app.routers import image, pdf, audio, video, ai_image, payment

app.include_router(image.router)
app.include_router(pdf.router)
app.include_router(audio.router)
app.include_router(video.router)
app.include_router(ai_image.router)
app.include_router(payment.router)
