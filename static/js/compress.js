/**
 * Video Compression UI - Three compression modes:
 * 1. Target Size (two-pass encoding)
 * 2. Quality Preset (CRF encoding)
 * 3. Resolution (downscaling + CRF)
 */

// Compression state management
const compressState = {
    activeMode: 'target-size',  // 'target-size', 'quality', 'resolution'
    selectedFile: null,
    videoInfo: null,
    targetSizeMb: 100,
    qualityPreset: 'medium',
    resolution: '1080p',
    compressing: false,
    estimate: null
};

/**
 * Initialize compression UI
 */
function initializeCompress() {
    initializeCompressTabs();
    initializeTargetSizeMode();
    initializeQualityMode();
    initializeResolutionMode();
}

/**
 * Initialize tab navigation
 */
function initializeCompressTabs() {
    const targetTab = document.getElementById('compress-target-tab');
    const qualityTab = document.getElementById('compress-quality-tab');
    const resolutionTab = document.getElementById('compress-resolution-tab');

    const targetContent = document.getElementById('compress-target-content');
    const qualityContent = document.getElementById('compress-quality-content');
    const resolutionContent = document.getElementById('compress-resolution-content');

    targetTab.addEventListener('click', () => {
        compressState.activeMode = 'target-size';
        targetTab.classList.add('active');
        qualityTab.classList.remove('active');
        resolutionTab.classList.remove('active');

        targetContent.classList.add('active');
        qualityContent.classList.remove('active');
        resolutionContent.classList.remove('active');
    });

    qualityTab.addEventListener('click', () => {
        compressState.activeMode = 'quality';
        qualityTab.classList.add('active');
        targetTab.classList.remove('active');
        resolutionTab.classList.remove('active');

        qualityContent.classList.add('active');
        targetContent.classList.remove('active');
        resolutionContent.classList.remove('active');
    });

    resolutionTab.addEventListener('click', () => {
        compressState.activeMode = 'resolution';
        resolutionTab.classList.add('active');
        targetTab.classList.remove('active');
        qualityTab.classList.remove('active');

        resolutionContent.classList.add('active');
        targetContent.classList.remove('active');
        qualityContent.classList.remove('active');
    });
}

/**
 * Initialize Target Size mode
 */
function initializeTargetSizeMode() {
    const uploadZone = document.getElementById('compress-target-upload-zone');
    const fileInput = document.getElementById('compress-target-file-input');
    const estimateBtn = document.getElementById('compress-target-estimate-btn');
    const compressBtn = document.getElementById('compress-target-btn');
    const targetSizeInput = document.getElementById('target-size-input');

    // Upload zone
    uploadZone.addEventListener('click', () => fileInput.click());

    uploadZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadZone.classList.add('drag-over');
    });

    uploadZone.addEventListener('dragleave', () => {
        uploadZone.classList.remove('drag-over');
    });

    uploadZone.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadZone.classList.remove('drag-over');

        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handleCompressFile(files[0], 'target-size');
        }
    });

    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleCompressFile(e.target.files[0], 'target-size');
        }
    });

    // Target size input
    targetSizeInput.addEventListener('input', (e) => {
        compressState.targetSizeMb = parseFloat(e.target.value) || 100;
        compressState.estimate = null;  // Clear estimate when size changes
        document.getElementById('compress-target-estimate-result').innerHTML = '';

        // Update button text
        compressBtn.textContent = `Compress to ${compressState.targetSizeMb} MB`;
    });

    // Estimate button
    estimateBtn.addEventListener('click', () => estimateCompression('target-size'));

    // Compress button
    compressBtn.addEventListener('click', () => compressVideo('target-size'));
}

/**
 * Initialize Quality mode
 */
function initializeQualityMode() {
    const uploadZone = document.getElementById('compress-quality-upload-zone');
    const fileInput = document.getElementById('compress-quality-file-input');
    const estimateBtn = document.getElementById('compress-quality-estimate-btn');
    const compressBtn = document.getElementById('compress-quality-btn');
    const qualityButtons = document.querySelectorAll('.quality-preset-btn');

    // Upload zone
    uploadZone.addEventListener('click', () => fileInput.click());

    uploadZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadZone.classList.add('drag-over');
    });

    uploadZone.addEventListener('dragleave', () => {
        uploadZone.classList.remove('drag-over');
    });

    uploadZone.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadZone.classList.remove('drag-over');

        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handleCompressFile(files[0], 'quality');
        }
    });

    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleCompressFile(e.target.files[0], 'quality');
        }
    });

    // Quality preset buttons
    qualityButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            qualityButtons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            compressState.qualityPreset = btn.dataset.preset;
            compressState.estimate = null;  // Clear estimate when preset changes
            document.getElementById('compress-quality-estimate-result').innerHTML = '';
        });
    });

    // Estimate button
    estimateBtn.addEventListener('click', () => estimateCompression('quality'));

    // Compress button
    compressBtn.addEventListener('click', () => compressVideo('quality'));
}

/**
 * Initialize Resolution mode
 */
function initializeResolutionMode() {
    const uploadZone = document.getElementById('compress-resolution-upload-zone');
    const fileInput = document.getElementById('compress-resolution-file-input');
    const estimateBtn = document.getElementById('compress-resolution-estimate-btn');
    const compressBtn = document.getElementById('compress-resolution-btn');
    const resolutionSelect = document.getElementById('resolution-select');
    const qualityButtons = document.querySelectorAll('.resolution-quality-btn');

    // Upload zone
    uploadZone.addEventListener('click', () => fileInput.click());

    uploadZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadZone.classList.add('drag-over');
    });

    uploadZone.addEventListener('dragleave', () => {
        uploadZone.classList.remove('drag-over');
    });

    uploadZone.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadZone.classList.remove('drag-over');

        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handleCompressFile(files[0], 'resolution');
        }
    });

    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleCompressFile(e.target.files[0], 'resolution');
        }
    });

    // Resolution select
    resolutionSelect.addEventListener('change', (e) => {
        compressState.resolution = e.target.value;
        compressState.estimate = null;  // Clear estimate when resolution changes
        document.getElementById('compress-resolution-estimate-result').innerHTML = '';
    });

    // Quality preset buttons
    qualityButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            qualityButtons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            compressState.qualityPreset = btn.dataset.preset;
            compressState.estimate = null;  // Clear estimate when preset changes
            document.getElementById('compress-resolution-estimate-result').innerHTML = '';
        });
    });

    // Estimate button
    estimateBtn.addEventListener('click', () => estimateCompression('resolution'));

    // Compress button
    compressBtn.addEventListener('click', () => compressVideo('resolution'));
}

/**
 * Handle file selection for compression
 */
async function handleCompressFile(file, mode) {
    if (!file.type.startsWith('video/')) {
        showStatus(`compress-${mode}-status`, 'Please select a video file', 'error');
        return;
    }

    compressState.selectedFile = file;
    compressState.estimate = null;

    // Show file info
    try {
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch('/api/video/info', {
            method: 'POST',
            body: formData
        });

        if (response.ok) {
            compressState.videoInfo = await response.json();
            displayVideoInfo(mode);
        } else {
            const error = await response.json();
            showStatus(`compress-${mode}-status`, error.detail || 'Failed to read video info', 'error');
        }
    } catch (error) {
        showStatus(`compress-${mode}-status`, 'Error loading video info', 'error');
    }
}

/**
 * Display video information
 */
function displayVideoInfo(mode) {
    const info = compressState.videoInfo;
    const sizeMb = (info.size / (1024 * 1024)).toFixed(2);

    const infoHtml = `
        <div class="video-info-display">
            <p><strong>📹 ${info.filename}</strong></p>
            <p>Duration: ${info.duration_formatted} | Size: ${sizeMb} MB</p>
            <p>Resolution: ${info.resolution} | Codec: ${info.video_codec}</p>
        </div>
    `;

    document.getElementById(`compress-${mode}-info`).innerHTML = infoHtml;

    // Update target size max (can't be larger than original)
    if (mode === 'target-size') {
        const targetInput = document.getElementById('target-size-input');
        targetInput.max = Math.floor(parseFloat(sizeMb));

        // Show original size hint
        document.getElementById('compress-target-original-size').textContent = `(Original: ${sizeMb} MB)`;
    }
}

/**
 * Estimate compression output size
 */
async function estimateCompression(mode) {
    if (!compressState.selectedFile) {
        showStatus(`compress-${mode}-status`, 'Please select a video file first', 'error');
        return;
    }

    const formData = new FormData();
    formData.append('file', compressState.selectedFile);
    formData.append('mode', mode === 'target-size' ? 'target_size' : mode);

    if (mode === 'target-size') {
        formData.append('target_size_mb', compressState.targetSizeMb);
    } else if (mode === 'quality') {
        formData.append('preset', compressState.qualityPreset);
    } else if (mode === 'resolution') {
        formData.append('resolution', compressState.resolution);
        formData.append('preset', compressState.qualityPreset);
    }

    try {
        showStatus(`compress-${mode}-status`, 'Estimating...', 'info');

        const response = await fetch('/api/video/compress/estimate', {
            method: 'POST',
            body: formData
        });

        if (response.ok) {
            const estimate = await response.json();
            compressState.estimate = estimate;
            displayEstimate(mode, estimate);
            showStatus(`compress-${mode}-status`, '', 'success');
        } else {
            const error = await response.json();
            showStatus(`compress-${mode}-status`, error.detail || 'Estimation failed', 'error');
        }
    } catch (error) {
        showStatus(`compress-${mode}-status`, 'Error estimating compression', 'error');
    }
}

/**
 * Display compression estimate
 */
function displayEstimate(mode, estimate) {
    const estimateHtml = `
        <div class="estimate-result">
            <p><strong>Estimated Output:</strong> ~${estimate.estimated_size_mb} MB</p>
            <p><strong>Reduction:</strong> ${estimate.reduction_percent}% (from ${estimate.original_size_mb} MB)</p>
        </div>
    `;

    document.getElementById(`compress-${mode}-estimate-result`).innerHTML = estimateHtml;
}

/**
 * Compress video
 */
async function compressVideo(mode) {
    if (!compressState.selectedFile) {
        showStatus(`compress-${mode}-status`, 'Please select a video file first', 'error');
        return;
    }

    if (compressState.compressing) {
        showStatus(`compress-${mode}-status`, 'Compression already in progress', 'error');
        return;
    }

    compressState.compressing = true;

    const formData = new FormData();
    formData.append('file', compressState.selectedFile);

    let endpoint = '';

    if (mode === 'target-size') {
        endpoint = '/api/video/compress/target-size';
        formData.append('target_size_mb', compressState.targetSizeMb);
    } else if (mode === 'quality') {
        endpoint = '/api/video/compress/quality';
        formData.append('preset', compressState.qualityPreset);
    } else if (mode === 'resolution') {
        endpoint = '/api/video/compress/resolution';
        formData.append('resolution', compressState.resolution);
        formData.append('preset', compressState.qualityPreset);
    }

    try {
        showStatus(`compress-${mode}-status`, 'Compressing video... This may take several minutes.', 'info');

        // Disable compress button
        const compressBtn = document.getElementById(`compress-${mode}-btn`);
        compressBtn.disabled = true;
        compressBtn.textContent = 'Compressing...';

        const response = await fetch(endpoint, {
            method: 'POST',
            body: formData
        });

        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);

            // Get actual file size
            const actualSizeMb = (blob.size / (1024 * 1024)).toFixed(2);
            const originalSizeMb = compressState.videoInfo.size / (1024 * 1024);
            const reductionPct = (((originalSizeMb - actualSizeMb) / originalSizeMb) * 100).toFixed(1);

            // Display result
            const resultHtml = `
                <div class="compress-result">
                    <p><strong>✓ Compression Complete!</strong></p>
                    <p>Output Size: ${actualSizeMb} MB (${reductionPct}% reduction)</p>
                    <a href="${url}" download="compressed_${compressState.selectedFile.name}" class="btn btn-primary">
                        Download Compressed Video
                    </a>
                </div>
            `;

            document.getElementById(`compress-${mode}-result`).innerHTML = resultHtml;
            showStatus(`compress-${mode}-status`, '', 'success');
        } else {
            const error = await response.json();
            showStatus(`compress-${mode}-status`, error.detail || 'Compression failed', 'error');
        }
    } catch (error) {
        showStatus(`compress-${mode}-status`, 'Error during compression', 'error');
    } finally {
        compressState.compressing = false;

        // Re-enable compress button
        const compressBtn = document.getElementById(`compress-${mode}-btn`);
        if (compressBtn) {
            compressBtn.disabled = false;

            if (mode === 'target-size') {
                compressBtn.textContent = `Compress to ${compressState.targetSizeMb} MB`;
            } else {
                compressBtn.textContent = 'Compress Video';
            }
        }
    }
}

// Initialize when DOM is loaded
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeCompress);
} else {
    initializeCompress();
}
