/**
 * Video Splitting Feature
 * Handles video splitting with upload and local path modes
 */

// State management
const videoState = {
    inputMode: 'upload', // 'upload' or 'local'
    selectedFile: null,
    localPath: '',
    videoInfo: null,
    numParts: 5,
    splitPreview: null,
    splitting: false,
    ffmpegAvailable: null
};

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    initializeVideoSplitter();
});

async function initializeVideoSplitter() {
    const videoPanel = document.getElementById('video-splitter');
    if (!videoPanel) return;

    // Check FFmpeg availability
    await checkFFmpegAvailability();

    // Initialize tab navigation
    initializeVideoTabs();

    // Initialize upload mode
    initializeUploadMode();

    // Initialize local path mode
    initializeLocalMode();

    // Initialize parts input
    initializePartsInput();

    // Initialize split button
    const splitBtn = document.getElementById('split-video-btn');
    if (splitBtn) {
        splitBtn.addEventListener('click', splitVideo);
    }
}

// ============================================
// FFmpeg Check
// ============================================

async function checkFFmpegAvailability() {
    try {
        const response = await fetch('/api/video/check-ffmpeg');
        const data = await response.json();
        videoState.ffmpegAvailable = data.ffmpeg_installed;

        if (!videoState.ffmpegAvailable) {
            showFFmpegWarning();
        }
    } catch (error) {
        console.error('Failed to check FFmpeg:', error);
    }
}

function showFFmpegWarning() {
    const uploadZone = document.getElementById('video-upload-zone');
    if (uploadZone) {
        uploadZone.innerHTML = `
            <svg class="upload-icon" style="color: var(--error);" xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10"></circle>
                <line x1="12" y1="8" x2="12" y2="12"></line>
                <line x1="12" y1="16" x2="12.01" y2="16"></line>
            </svg>
            <p class="upload-text" style="color: var(--error);">FFmpeg Not Installed</p>
            <p class="upload-hint">
                Video splitting requires FFmpeg.<br>
                <a href="https://ffmpeg.org/download.html" target="_blank" style="color: var(--accent-primary);">Download FFmpeg</a>
            </p>
        `;
    }
}

// ============================================
// Tab Navigation
// ============================================

function initializeVideoTabs() {
    const uploadTab = document.getElementById('video-upload-tab');
    const localTab = document.getElementById('video-local-tab');
    const uploadContent = document.getElementById('video-upload-content');
    const localContent = document.getElementById('video-local-content');

    if (!uploadTab || !localTab) return;

    uploadTab.addEventListener('click', () => {
        videoState.inputMode = 'upload';
        uploadTab.classList.add('active');
        localTab.classList.remove('active');
        uploadContent.style.display = 'block';
        localContent.style.display = 'none';
        clearVideoState();
    });

    localTab.addEventListener('click', () => {
        videoState.inputMode = 'local';
        localTab.classList.add('active');
        uploadTab.classList.remove('active');
        localContent.style.display = 'block';
        uploadContent.style.display = 'none';
        clearVideoState();
    });
}

// ============================================
// Upload Mode
// ============================================

function initializeUploadMode() {
    const uploadZone = document.getElementById('video-upload-zone');
    const fileInput = document.getElementById('video-file-input');

    if (!uploadZone || !fileInput) return;

    uploadZone.addEventListener('click', () => {
        if (videoState.ffmpegAvailable === false) {
            window.MediaToolkit.showToast('FFmpeg is not installed', 'error');
            return;
        }
        fileInput.click();
    });

    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleVideoFile(e.target.files[0]);
        }
    });

    // Drag and drop
    uploadZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        if (videoState.ffmpegAvailable !== false) {
            uploadZone.classList.add('drag-over');
        }
    });

    uploadZone.addEventListener('dragleave', () => {
        uploadZone.classList.remove('drag-over');
    });

    uploadZone.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadZone.classList.remove('drag-over');
        if (videoState.ffmpegAvailable === false) {
            window.MediaToolkit.showToast('FFmpeg is not installed', 'error');
            return;
        }
        if (e.dataTransfer.files.length > 0) {
            handleVideoFile(e.dataTransfer.files[0]);
        }
    });
}

async function handleVideoFile(file) {
    const videoTypes = ['video/'];
    const isVideo = videoTypes.some(type => file.type.startsWith(type));

    if (!isVideo) {
        window.MediaToolkit.showToast('Please select a video file', 'warning');
        return;
    }

    videoState.selectedFile = file;
    showVideoLoading();

    // Get video info
    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch('/api/video/info', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to read video');
        }

        videoState.videoInfo = await response.json();
        renderVideoInfo();
        await updateSplitPreview();

    } catch (error) {
        window.MediaToolkit.showToast(`Failed to read video: ${error.message}`, 'error');
        clearVideoState();
    }
}

// ============================================
// Local Path Mode
// ============================================

function initializeLocalMode() {
    const loadBtn = document.getElementById('load-local-video-btn');
    const pathInput = document.getElementById('local-video-path');

    if (!loadBtn || !pathInput) return;

    loadBtn.addEventListener('click', async () => {
        const path = pathInput.value.trim();
        if (!path) {
            window.MediaToolkit.showToast('Please enter a file path', 'warning');
            return;
        }
        await loadLocalVideo(path);
    });

    pathInput.addEventListener('keypress', async (e) => {
        if (e.key === 'Enter') {
            const path = pathInput.value.trim();
            if (path) {
                await loadLocalVideo(path);
            }
        }
    });
}

async function loadLocalVideo(path) {
    videoState.localPath = path;
    showVideoLoading();

    try {
        const response = await fetch('/api/video/info-local', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ path })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to load video');
        }

        videoState.videoInfo = await response.json();
        renderVideoInfo();
        await updateSplitPreview();

    } catch (error) {
        window.MediaToolkit.showToast(`Failed to load video: ${error.message}`, 'error');
        clearVideoState();
    }
}

// ============================================
// Video Info Display
// ============================================

function showVideoLoading() {
    const infoContainer = document.getElementById('video-split-info-container');
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
    const infoContainer = document.getElementById('video-split-info-container');
    if (!infoContainer || !videoState.videoInfo) return;

    infoContainer.style.display = 'block';
    infoContainer.innerHTML = `
        <div class="video-info-card">
            <div class="video-info-header">
                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polygon points="23 7 16 12 23 17 23 7"></polygon>
                    <rect x="1" y="5" width="15" height="14" rx="2" ry="2"></rect>
                </svg>
                <span class="video-filename">${videoState.videoInfo.filename}</span>
            </div>
            <div class="video-info-details">
                <div class="info-item">
                    <span class="info-label">Duration:</span>
                    <span class="info-value">${videoState.videoInfo.duration_formatted}</span>
                </div>
                <div class="info-item">
                    <span class="info-label">Size:</span>
                    <span class="info-value">${window.MediaToolkit.formatFileSize(videoState.videoInfo.size)}</span>
                </div>
                <div class="info-item">
                    <span class="info-label">Codec:</span>
                    <span class="info-value">${videoState.videoInfo.video_codec.toUpperCase()}</span>
                </div>
                <div class="info-item">
                    <span class="info-label">Resolution:</span>
                    <span class="info-value">${videoState.videoInfo.resolution}</span>
                </div>
            </div>
        </div>
    `;

    updateSplitButton();
}

function clearVideoState() {
    videoState.selectedFile = null;
    videoState.localPath = '';
    videoState.videoInfo = null;
    videoState.splitPreview = null;

    const infoContainer = document.getElementById('video-split-info-container');
    if (infoContainer) {
        infoContainer.style.display = 'none';
    }

    const previewContainer = document.getElementById('split-preview-container');
    if (previewContainer) {
        previewContainer.style.display = 'none';
    }

    updateSplitButton();
}

// ============================================
// Parts Input
// ============================================

function initializePartsInput() {
    const partsInput = document.getElementById('num-parts-input');
    if (!partsInput) return;

    partsInput.addEventListener('input', async (e) => {
        const value = parseInt(e.target.value);
        if (value >= 2 && value <= 20) {
            videoState.numParts = value;
            await updateSplitPreview();
        }
    });
}

// ============================================
// Split Preview
// ============================================

async function updateSplitPreview() {
    if (!videoState.videoInfo) return;

    const previewContainer = document.getElementById('split-preview-container');
    if (!previewContainer) return;

    const duration = videoState.videoInfo.duration;
    const partDuration = duration / videoState.numParts;

    const preview = [];
    for (let i = 0; i < videoState.numParts; i++) {
        const start = i * partDuration;
        const end = (i + 1) * partDuration;
        preview.push({
            part: i + 1,
            start_formatted: window.MediaToolkit.formatDuration(start),
            end_formatted: window.MediaToolkit.formatDuration(end)
        });
    }

    videoState.splitPreview = preview;

    previewContainer.style.display = 'block';
    const table = previewContainer.querySelector('.split-preview-table');
    if (table) {
        table.innerHTML = preview.map(p => `
            <div class="preview-row">
                <span class="preview-part">Part ${p.part}</span>
                <span class="preview-time">${p.start_formatted} - ${p.end_formatted}</span>
            </div>
        `).join('');
    }
}

// ============================================
// Split Button
// ============================================

function updateSplitButton() {
    const splitBtn = document.getElementById('split-video-btn');
    if (!splitBtn) return;

    const hasVideo = (videoState.inputMode === 'upload' && videoState.selectedFile) ||
                     (videoState.inputMode === 'local' && videoState.localPath);

    splitBtn.disabled = !hasVideo || videoState.splitting;

    if (videoState.splitting) {
        splitBtn.textContent = 'Splitting...';
    } else if (!hasVideo) {
        splitBtn.textContent = 'Select a video first';
    } else {
        splitBtn.textContent = `Split into ${videoState.numParts} Parts`;
    }
}

// ============================================
// Split Video
// ============================================

async function splitVideo() {
    if (videoState.splitting) return;

    const hasVideo = (videoState.inputMode === 'upload' && videoState.selectedFile) ||
                     (videoState.inputMode === 'local' && videoState.localPath);

    if (!hasVideo) {
        window.MediaToolkit.showToast('Please select a video first', 'warning');
        return;
    }

    videoState.splitting = true;
    updateSplitButton();

    try {
        if (videoState.inputMode === 'upload') {
            await splitUploadedVideo();
        } else {
            await splitLocalVideo();
        }
    } catch (error) {
        window.MediaToolkit.showToast(`Split failed: ${error.message}`, 'error');
    } finally {
        videoState.splitting = false;
        updateSplitButton();
    }
}

async function splitUploadedVideo() {
    const formData = new FormData();
    formData.append('file', videoState.selectedFile);
    formData.append('parts', videoState.numParts);

    const response = await fetch('/api/video/split', {
        method: 'POST',
        body: formData
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Split failed');
    }

    const blob = await response.blob();
    const filename = `${videoState.selectedFile.name.replace(/\.[^/.]+$/, '')}_split.zip`;

    window.MediaToolkit.downloadBlob(blob, filename);
    window.MediaToolkit.showToast(
        `Video split into ${videoState.numParts} parts successfully!`,
        'success'
    );

    showSplitSuccess(filename, blob.size);
}

async function splitLocalVideo() {
    const response = await fetch('/api/video/split-local', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            path: videoState.localPath,
            parts: videoState.numParts
        })
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Split failed');
    }

    const result = await response.json();

    window.MediaToolkit.showToast(
        `Video split into ${result.num_parts} parts successfully!`,
        'success'
    );

    showLocalSplitSuccess(result.output_files);
}

function showSplitSuccess(filename, size) {
    const resultContainer = document.getElementById('video-split-result-container');
    if (!resultContainer) return;

    resultContainer.style.display = 'block';
    resultContainer.innerHTML = `
        <div class="extraction-result success">
            <div class="result-icon">✓</div>
            <div class="result-info">
                <div class="result-title">Video split successfully!</div>
                <div class="result-details">${filename} (${window.MediaToolkit.formatFileSize(size)})</div>
            </div>
        </div>
    `;
}

function showLocalSplitSuccess(files) {
    const resultContainer = document.getElementById('video-split-result-container');
    if (!resultContainer) return;

    resultContainer.style.display = 'block';
    resultContainer.innerHTML = `
        <div class="extraction-result success">
            <div class="result-icon">✓</div>
            <div class="result-info">
                <div class="result-title">Video split successfully!</div>
                <div class="result-details">${files.length} parts created in output directory</div>
            </div>
        </div>
        <div class="local-split-files">
            <h4>Output Files:</h4>
            ${files.map(f => `<div class="split-file-path">${f}</div>`).join('')}
        </div>
    `;
}
