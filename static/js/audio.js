/**
 * Audio Extraction Feature
 * Handles audio extraction from video files
 */

// State management
const audioState = {
    selectedFile: null,
    videoInfo: null,
    outputFormat: 'mp3',
    bitrate: 192,
    extracting: false,
    ffmpegAvailable: null
};

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    initializeAudioExtractor();
});

async function initializeAudioExtractor() {
    const audioPanel = document.getElementById('audio-extractor');
    if (!audioPanel) return;

    // Check FFmpeg availability
    await checkFFmpegAvailability();

    // Setup upload zone
    const uploadZone = document.getElementById('audio-upload-zone');
    const fileInput = document.getElementById('audio-file-input');
    const formatButtons = document.querySelectorAll('.audio-format-btn');
    const bitrateButtons = document.querySelectorAll('.bitrate-btn');
    const extractBtn = document.getElementById('extract-audio-btn');

    if (!uploadZone || !fileInput) return;

    // Upload zone click
    uploadZone.addEventListener('click', () => {
        if (audioState.ffmpegAvailable === false) {
            window.MediaToolkit.showToast(
                'FFmpeg is not installed. Please install FFmpeg to use this feature.',
                'error',
                8000
            );
            return;
        }
        fileInput.click();
    });

    // File input change
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleVideoFile(e.target.files[0]);
        }
    });

    // Drag and drop
    uploadZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        if (audioState.ffmpegAvailable !== false) {
            uploadZone.classList.add('drag-over');
        }
    });

    uploadZone.addEventListener('dragleave', () => {
        uploadZone.classList.remove('drag-over');
    });

    uploadZone.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadZone.classList.remove('drag-over');
        if (audioState.ffmpegAvailable === false) {
            window.MediaToolkit.showToast(
                'FFmpeg is not installed',
                'error'
            );
            return;
        }
        if (e.dataTransfer.files.length > 0) {
            handleVideoFile(e.dataTransfer.files[0]);
        }
    });

    // Format button selection
    formatButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            formatButtons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            audioState.outputFormat = btn.dataset.format;
            updateBitrateVisibility();
        });
    });

    // Bitrate button selection
    bitrateButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            bitrateButtons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            audioState.bitrate = parseInt(btn.dataset.bitrate);
        });
    });

    // Extract button
    if (extractBtn) {
        extractBtn.addEventListener('click', extractAudio);
    }
}

async function checkFFmpegAvailability() {
    try {
        const response = await fetch('/api/audio/check-ffmpeg');
        const data = await response.json();

        audioState.ffmpegAvailable = data.ffmpeg_installed && data.ffprobe_installed;

        if (!audioState.ffmpegAvailable) {
            showFFmpegWarning();
        }
    } catch (error) {
        console.error('Failed to check FFmpeg availability:', error);
    }
}

function showFFmpegWarning() {
    const uploadZone = document.getElementById('audio-upload-zone');
    if (!uploadZone) return;

    uploadZone.innerHTML = `
        <svg class="upload-icon" style="color: var(--error);" xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"></circle>
            <line x1="12" y1="8" x2="12" y2="12"></line>
            <line x1="12" y1="16" x2="12.01" y2="16"></line>
        </svg>
        <p class="upload-text" style="color: var(--error);">FFmpeg Not Installed</p>
        <p class="upload-hint">
            Audio extraction requires FFmpeg. Please install it to use this feature.<br>
            <a href="https://ffmpeg.org/download.html" target="_blank" style="color: var(--accent-primary);">Download FFmpeg</a>
        </p>
    `;
}

async function handleVideoFile(file) {
    if (!file) return;

    // Basic type check
    const videoTypes = ['video/'];
    const isVideo = videoTypes.some(type => file.type.startsWith(type)) ||
                    file.name.match(/\.(mp4|mkv|avi|mov|webm|flv|wmv|m4v|mpeg|mpg|3gp)$/i);

    if (!isVideo) {
        window.MediaToolkit.showToast('Please select a video file', 'warning');
        return;
    }

    audioState.selectedFile = file;

    // Show loading state
    showVideoInfoLoading();

    // Get video info
    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch('/api/audio/info', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to read video');
        }

        audioState.videoInfo = await response.json();
        renderVideoInfo();
        updateExtractButton();

    } catch (error) {
        window.MediaToolkit.showToast(`Failed to read video: ${error.message}`, 'error');
        hideVideoInfo();
        audioState.selectedFile = null;
        audioState.videoInfo = null;
        updateExtractButton();
    }
}

function showVideoInfoLoading() {
    const infoContainer = document.getElementById('video-info-container');
    if (!infoContainer) return;

    infoContainer.style.display = 'block';
    infoContainer.innerHTML = `
        <div class="video-info-loading">
            <div class="loading-spinner"></div>
            <p>Analyzing video...</p>
        </div>
    `;
}

function renderVideoInfo() {
    const infoContainer = document.getElementById('video-info-container');
    if (!infoContainer || !audioState.videoInfo) return;

    infoContainer.style.display = 'block';
    infoContainer.innerHTML = `
        <div class="video-info-card">
            <div class="video-info-header">
                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polygon points="23 7 16 12 23 17 23 7"></polygon>
                    <rect x="1" y="5" width="15" height="14" rx="2" ry="2"></rect>
                </svg>
                <span class="video-filename">${audioState.videoInfo.filename}</span>
            </div>
            <div class="video-info-details">
                <div class="info-item">
                    <span class="info-label">Duration:</span>
                    <span class="info-value">${audioState.videoInfo.duration_formatted}</span>
                </div>
                <div class="info-item">
                    <span class="info-label">Size:</span>
                    <span class="info-value">${window.MediaToolkit.formatFileSize(audioState.videoInfo.size)}</span>
                </div>
                <div class="info-item">
                    <span class="info-label">Video Codec:</span>
                    <span class="info-value">${audioState.videoInfo.video_codec.toUpperCase()}</span>
                </div>
                <div class="info-item">
                    <span class="info-label">Audio Codec:</span>
                    <span class="info-value">${audioState.videoInfo.audio_codec.toUpperCase()}</span>
                </div>
            </div>
        </div>
    `;
}

function hideVideoInfo() {
    const infoContainer = document.getElementById('video-info-container');
    if (infoContainer) {
        infoContainer.style.display = 'none';
    }
}

function updateBitrateVisibility() {
    const bitrateContainer = document.getElementById('bitrate-container');
    if (!bitrateContainer) return;

    const lossyFormats = ['mp3', 'aac', 'ogg'];
    if (lossyFormats.includes(audioState.outputFormat)) {
        bitrateContainer.style.display = 'block';
    } else {
        bitrateContainer.style.display = 'none';
    }
}

function updateExtractButton() {
    const extractBtn = document.getElementById('extract-audio-btn');
    if (!extractBtn) return;

    extractBtn.disabled = !audioState.selectedFile || audioState.extracting;

    if (audioState.extracting) {
        extractBtn.textContent = 'Extracting...';
    } else if (!audioState.selectedFile) {
        extractBtn.textContent = 'Select a video first';
    } else {
        extractBtn.textContent = 'Extract Audio';
    }
}

async function extractAudio() {
    if (!audioState.selectedFile || audioState.extracting) return;

    audioState.extracting = true;
    updateExtractButton();

    const formData = new FormData();
    formData.append('file', audioState.selectedFile);
    formData.append('format', audioState.outputFormat);
    formData.append('bitrate', audioState.bitrate);

    try {
        const response = await fetch('/api/audio/extract', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Extraction failed');
        }

        const blob = await response.blob();
        const filename = `${audioState.selectedFile.name.replace(/\.[^/.]+$/, '')}.${audioState.outputFormat}`;

        window.MediaToolkit.downloadBlob(blob, filename);

        window.MediaToolkit.showToast(
            `Audio extracted successfully! (${window.MediaToolkit.formatFileSize(blob.size)})`,
            'success'
        );

        // Show result
        showExtractionResult(filename, blob.size);

    } catch (error) {
        window.MediaToolkit.showToast(`Extraction failed: ${error.message}`, 'error');
    } finally {
        audioState.extracting = false;
        updateExtractButton();
    }
}

function showExtractionResult(filename, size) {
    const resultContainer = document.getElementById('extraction-result-container');
    if (!resultContainer) return;

    resultContainer.style.display = 'block';
    resultContainer.innerHTML = `
        <div class="extraction-result success">
            <div class="result-icon">✓</div>
            <div class="result-info">
                <div class="result-title">Audio extracted successfully!</div>
                <div class="result-details">${filename} (${window.MediaToolkit.formatFileSize(size)})</div>
            </div>
        </div>
    `;
}

// Add loading spinner styles dynamically
const style = document.createElement('style');
style.textContent = `
    .loading-spinner {
        width: 40px;
        height: 40px;
        border: 4px solid var(--bg-tertiary);
        border-top-color: var(--accent-primary);
        border-radius: 50%;
        animation: spin 1s linear infinite;
        margin: 0 auto var(--spacing-md);
    }

    @keyframes spin {
        to { transform: rotate(360deg); }
    }

    .video-info-loading {
        text-align: center;
        padding: var(--spacing-xl);
        color: var(--text-secondary);
    }
`;
document.head.appendChild(style);
