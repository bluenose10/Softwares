/**
 * Image Conversion Feature
 * Handles image upload, conversion, and download
 */

// State management
const imageState = {
    selectedFiles: [],
    outputFormat: 'jpg',
    quality: 85,
    converting: false,
    results: []
};

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    initializeImageConverter();
});

function initializeImageConverter() {
    const uploadZone = document.getElementById('image-upload-zone');
    const fileInput = document.getElementById('image-file-input');
    const formatButtons = document.querySelectorAll('.format-btn');
    const qualitySlider = document.getElementById('quality-slider');
    const qualityValue = document.getElementById('quality-value');
    const convertBtn = document.getElementById('convert-all-btn');

    if (!uploadZone) return; // Not on image converter page

    // Upload zone click
    uploadZone.addEventListener('click', () => {
        fileInput.click();
    });

    // File input change
    fileInput.addEventListener('change', (e) => {
        handleFiles(e.target.files);
    });

    // Drag and drop
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
        handleFiles(e.dataTransfer.files);
    });

    // Format button selection
    formatButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            // Update active state
            formatButtons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            // Update state
            imageState.outputFormat = btn.dataset.format;

            // Show/hide quality slider
            updateQualityVisibility();
        });
    });

    // Quality slider
    if (qualitySlider) {
        qualitySlider.addEventListener('input', (e) => {
            imageState.quality = parseInt(e.target.value);
            qualityValue.textContent = imageState.quality;
        });
    }

    // Convert button
    if (convertBtn) {
        convertBtn.addEventListener('click', convertAllImages);
    }
}

function handleFiles(files) {
    const validTypes = ['image/png', 'image/jpeg', 'image/webp', 'image/gif',
                       'image/bmp', 'image/tiff', 'image/heic', 'image/heif'];

    for (const file of files) {
        // Check file type
        const isValidType = validTypes.some(type => file.type.startsWith('image/')) ||
                           file.name.toLowerCase().match(/\.(heic|heif)$/);

        if (!isValidType) {
            window.MediaToolkit.showToast(`Skipped ${file.name}: Not a supported image`, 'warning');
            continue;
        }

        // Check if already added
        if (imageState.selectedFiles.find(f => f.name === file.name && f.size === file.size)) {
            continue;
        }

        imageState.selectedFiles.push(file);
    }

    renderFileList();
    updateConvertButton();
}

function renderFileList() {
    const fileList = document.getElementById('file-list');
    const fileListContainer = document.getElementById('file-list-container');

    if (!fileList) return;

    if (imageState.selectedFiles.length === 0) {
        fileListContainer.style.display = 'none';
        return;
    }

    fileListContainer.style.display = 'block';
    fileList.innerHTML = '';

    imageState.selectedFiles.forEach((file, index) => {
        const item = document.createElement('div');
        item.className = 'file-item';

        // Check if this file has a result
        const result = imageState.results.find(r => r.originalName === file.name);
        const statusClass = result ? (result.success ? 'success' : 'error') : '';
        const statusIcon = result ? (result.success ? '✓' : '✗') : '';

        item.innerHTML = `
            <div class="file-info">
                <span class="file-name">${file.name}</span>
                <span class="file-size">${window.MediaToolkit.formatFileSize(file.size)}</span>
            </div>
            <div class="file-actions">
                ${result ? `<span class="file-status ${statusClass}">${statusIcon}</span>` : ''}
                ${result && result.success ? `<button class="btn-download-single" data-index="${index}">Download</button>` : ''}
                ${!imageState.converting ? `<button class="btn-remove" data-index="${index}">×</button>` : ''}
            </div>
        `;

        fileList.appendChild(item);
    });

    // Add event listeners to remove buttons
    document.querySelectorAll('.btn-remove').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const index = parseInt(e.target.dataset.index);
            removeFile(index);
        });
    });

    // Add event listeners to download buttons
    document.querySelectorAll('.btn-download-single').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const index = parseInt(e.target.dataset.index);
            downloadSingleFile(index);
        });
    });
}

function removeFile(index) {
    imageState.selectedFiles.splice(index, 1);

    // Also remove result if exists
    const removedFileName = imageState.selectedFiles[index]?.name;
    imageState.results = imageState.results.filter(r => r.originalName !== removedFileName);

    renderFileList();
    updateConvertButton();
}

function updateConvertButton() {
    const convertBtn = document.getElementById('convert-all-btn');
    if (!convertBtn) return;

    convertBtn.disabled = imageState.selectedFiles.length === 0 || imageState.converting;
    convertBtn.textContent = imageState.converting ? 'Converting...' : `Convert ${imageState.selectedFiles.length > 1 ? 'All' : ''} (${imageState.selectedFiles.length})`;
}

function updateQualityVisibility() {
    const qualityContainer = document.getElementById('quality-container');
    if (!qualityContainer) return;

    const qualityFormats = ['jpg', 'jpeg', 'webp'];
    if (qualityFormats.includes(imageState.outputFormat)) {
        qualityContainer.style.display = 'block';
    } else {
        qualityContainer.style.display = 'none';
    }
}

async function convertAllImages() {
    if (imageState.selectedFiles.length === 0 || imageState.converting) return;

    imageState.converting = true;
    imageState.results = [];
    updateConvertButton();

    const resultsContainer = document.getElementById('results-container');
    const downloadAllBtn = document.getElementById('download-all-btn');

    try {
        if (imageState.selectedFiles.length === 1) {
            // Single file conversion
            await convertSingleFile(imageState.selectedFiles[0]);
        } else {
            // Bulk conversion
            await convertBulkFiles();
        }

        // Show results
        if (resultsContainer) {
            resultsContainer.style.display = 'block';
        }

        // Show download all button for multiple files
        if (downloadAllBtn && imageState.selectedFiles.length > 1) {
            downloadAllBtn.style.display = 'block';
        }

        renderFileList();

        const successCount = imageState.results.filter(r => r.success).length;
        window.MediaToolkit.showToast(
            `Successfully converted ${successCount} of ${imageState.selectedFiles.length} images`,
            'success'
        );

    } catch (error) {
        window.MediaToolkit.showToast(`Conversion failed: ${error.message}`, 'error');
    } finally {
        imageState.converting = false;
        updateConvertButton();
    }
}

async function convertSingleFile(file) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('format', imageState.outputFormat);
    formData.append('quality', imageState.quality);

    try {
        const response = await fetch('/api/image/convert', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Conversion failed');
        }

        const blob = await response.blob();
        const filename = `${file.name.split('.')[0]}.${imageState.outputFormat}`;

        imageState.results.push({
            originalName: file.name,
            success: true,
            blob: blob,
            filename: filename
        });

        // Auto-download single file
        window.MediaToolkit.downloadBlob(blob, filename);

    } catch (error) {
        imageState.results.push({
            originalName: file.name,
            success: false,
            error: error.message
        });
        throw error;
    }
}

async function convertBulkFiles() {
    const formData = new FormData();

    imageState.selectedFiles.forEach(file => {
        formData.append('files', file);
    });
    formData.append('format', imageState.outputFormat);
    formData.append('quality', imageState.quality);

    try {
        const response = await fetch('/api/image/convert-bulk', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Bulk conversion failed');
        }

        const blob = await response.blob();

        // Store ZIP for download all button
        imageState.bulkResultBlob = blob;

        // Mark all as successful (server only returns successful conversions)
        imageState.selectedFiles.forEach(file => {
            imageState.results.push({
                originalName: file.name,
                success: true
            });
        });

    } catch (error) {
        // Mark all as failed
        imageState.selectedFiles.forEach(file => {
            imageState.results.push({
                originalName: file.name,
                success: false,
                error: error.message
            });
        });
        throw error;
    }
}

function downloadSingleFile(index) {
    const result = imageState.results.find(
        r => r.originalName === imageState.selectedFiles[index].name
    );

    if (result && result.blob) {
        window.MediaToolkit.downloadBlob(result.blob, result.filename);
    }
}

function downloadAllAsZip() {
    if (imageState.bulkResultBlob) {
        window.MediaToolkit.downloadBlob(imageState.bulkResultBlob, 'converted_images.zip');
    }
}

// Export for download all button
window.downloadAllAsZip = downloadAllAsZip;
