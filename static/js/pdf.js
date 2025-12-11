/**
 * PDF Tools Feature
 * Handles PDF merge and split operations
 */

// State management
const pdfState = {
    // Merge state
    mergeFiles: [],
    draggedIndex: null,

    // Split state
    splitFile: null,
    splitMode: 'all',
    pageRange: '',
    pdfInfo: null,

    // Processing state
    processing: false
};

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    initializePdfTools();
});

function initializePdfTools() {
    // Check if we're on the PDF tools page
    const pdfPanel = document.getElementById('pdf-tools');
    if (!pdfPanel) return;

    // Tab navigation
    initializeTabs();

    // Merge functionality
    initializeMergeTab();

    // Split functionality
    initializeSplitTab();
}

// ============================================
// Tab Navigation
// ============================================

function initializeTabs() {
    const mergeTab = document.getElementById('merge-tab');
    const splitTab = document.getElementById('split-tab');
    const mergeContent = document.getElementById('merge-content');
    const splitContent = document.getElementById('split-content');

    if (!mergeTab || !splitTab) return;

    mergeTab.addEventListener('click', () => {
        mergeTab.classList.add('active');
        splitTab.classList.remove('active');
        mergeContent.style.display = 'block';
        splitContent.style.display = 'none';
    });

    splitTab.addEventListener('click', () => {
        splitTab.classList.add('active');
        mergeTab.classList.remove('active');
        splitContent.style.display = 'block';
        mergeContent.style.display = 'none';
    });
}

// ============================================
// Merge Tab
// ============================================

function initializeMergeTab() {
    const uploadZone = document.getElementById('pdf-merge-upload-zone');
    const fileInput = document.getElementById('pdf-merge-file-input');
    const mergeBtn = document.getElementById('merge-pdfs-btn');

    if (!uploadZone || !fileInput) return;

    // Upload zone click
    uploadZone.addEventListener('click', () => {
        fileInput.click();
    });

    // File input change
    fileInput.addEventListener('change', (e) => {
        handleMergeFiles(e.target.files);
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
        handleMergeFiles(e.dataTransfer.files);
    });

    // Merge button
    if (mergeBtn) {
        mergeBtn.addEventListener('click', mergePDFs);
    }
}

function handleMergeFiles(files) {
    for (const file of files) {
        if (file.type !== 'application/pdf') {
            window.MediaToolkit.showToast(`Skipped ${file.name}: Not a PDF`, 'warning');
            continue;
        }

        // Check if already added
        if (pdfState.mergeFiles.find(f => f.name === file.name && f.size === file.size)) {
            continue;
        }

        pdfState.mergeFiles.push(file);
    }

    renderMergeFileList();
    updateMergeButton();
}

function renderMergeFileList() {
    const fileList = document.getElementById('merge-file-list');
    const fileListContainer = document.getElementById('merge-file-list-container');

    if (!fileList) return;

    if (pdfState.mergeFiles.length === 0) {
        fileListContainer.style.display = 'none';
        return;
    }

    fileListContainer.style.display = 'block';
    fileList.innerHTML = '';

    let totalPages = 0;

    pdfState.mergeFiles.forEach((file, index) => {
        const item = document.createElement('div');
        item.className = 'file-item sortable-item';
        item.draggable = true;
        item.dataset.index = index;

        item.innerHTML = `
            <div class="drag-handle">
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <line x1="3" y1="12" x2="21" y2="12"></line>
                    <line x1="3" y1="6" x2="21" y2="6"></line>
                    <line x1="3" y1="18" x2="21" y2="18"></line>
                </svg>
            </div>
            <div class="file-info">
                <span class="file-name">${file.name}</span>
                <span class="file-size">${window.MediaToolkit.formatFileSize(file.size)}</span>
            </div>
            <div class="file-actions">
                <button class="btn-remove" data-index="${index}">×</button>
            </div>
        `;

        // Drag events for reordering
        item.addEventListener('dragstart', handleDragStart);
        item.addEventListener('dragover', handleDragOver);
        item.addEventListener('drop', handleDrop);
        item.addEventListener('dragend', handleDragEnd);

        fileList.appendChild(item);
    });

    // Add event listeners to remove buttons
    document.querySelectorAll('#merge-file-list .btn-remove').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const index = parseInt(e.target.dataset.index);
            removeMergeFile(index);
        });
    });
}

function removeMergeFile(index) {
    pdfState.mergeFiles.splice(index, 1);
    renderMergeFileList();
    updateMergeButton();
}

function updateMergeButton() {
    const mergeBtn = document.getElementById('merge-pdfs-btn');
    if (!mergeBtn) return;

    const fileCount = pdfState.mergeFiles.length;
    mergeBtn.disabled = fileCount < 2 || pdfState.processing;

    if (pdfState.processing) {
        mergeBtn.textContent = 'Merging...';
    } else {
        mergeBtn.textContent = fileCount < 2 ? 'Add at least 2 PDFs' : `Merge ${fileCount} PDFs`;
    }
}

// Drag and drop reordering
function handleDragStart(e) {
    pdfState.draggedIndex = parseInt(e.target.dataset.index);
    e.target.classList.add('dragging');
}

function handleDragOver(e) {
    e.preventDefault();
    const item = e.currentTarget;
    item.classList.add('drag-over');
}

function handleDrop(e) {
    e.preventDefault();
    const item = e.currentTarget;
    item.classList.remove('drag-over');

    const dropIndex = parseInt(item.dataset.index);

    if (pdfState.draggedIndex !== null && pdfState.draggedIndex !== dropIndex) {
        // Reorder array
        const draggedFile = pdfState.mergeFiles[pdfState.draggedIndex];
        pdfState.mergeFiles.splice(pdfState.draggedIndex, 1);
        pdfState.mergeFiles.splice(dropIndex, 0, draggedFile);

        renderMergeFileList();
    }
}

function handleDragEnd(e) {
    e.target.classList.remove('dragging');
    document.querySelectorAll('.drag-over').forEach(el => {
        el.classList.remove('drag-over');
    });
    pdfState.draggedIndex = null;
}

async function mergePDFs() {
    if (pdfState.mergeFiles.length < 2 || pdfState.processing) return;

    pdfState.processing = true;
    updateMergeButton();

    const formData = new FormData();
    pdfState.mergeFiles.forEach(file => {
        formData.append('files', file);
    });

    try {
        const response = await fetch('/api/pdf/merge', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Merge failed');
        }

        const blob = await response.blob();
        window.MediaToolkit.downloadBlob(blob, 'merged.pdf');

        window.MediaToolkit.showToast('PDFs merged successfully!', 'success');

        // Clear the list
        pdfState.mergeFiles = [];
        renderMergeFileList();

    } catch (error) {
        window.MediaToolkit.showToast(`Merge failed: ${error.message}`, 'error');
    } finally {
        pdfState.processing = false;
        updateMergeButton();
    }
}

// ============================================
// Split Tab
// ============================================

function initializeSplitTab() {
    const uploadZone = document.getElementById('pdf-split-upload-zone');
    const fileInput = document.getElementById('pdf-split-file-input');
    const modeRadios = document.querySelectorAll('input[name="split-mode"]');
    const pageRangeInput = document.getElementById('page-range-input');
    const splitBtn = document.getElementById('split-pdf-btn');

    if (!uploadZone || !fileInput) return;

    // Upload zone click
    uploadZone.addEventListener('click', () => {
        fileInput.click();
    });

    // File input change
    fileInput.addEventListener('change', (e) => {
        handleSplitFile(e.target.files[0]);
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
        if (e.dataTransfer.files.length > 0) {
            handleSplitFile(e.dataTransfer.files[0]);
        }
    });

    // Mode selection
    modeRadios.forEach(radio => {
        radio.addEventListener('change', (e) => {
            pdfState.splitMode = e.target.value;
            updatePageRangeVisibility();
        });
    });

    // Page range input
    if (pageRangeInput) {
        pageRangeInput.addEventListener('input', (e) => {
            pdfState.pageRange = e.target.value;
        });
    }

    // Split button
    if (splitBtn) {
        splitBtn.addEventListener('click', splitPDF);
    }
}

async function handleSplitFile(file) {
    if (!file) return;

    if (file.type !== 'application/pdf') {
        window.MediaToolkit.showToast('Please select a PDF file', 'warning');
        return;
    }

    pdfState.splitFile = file;

    // Get PDF info
    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch('/api/pdf/info', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) throw new Error('Failed to read PDF');

        pdfState.pdfInfo = await response.json();
        renderSplitFileInfo();
        updateSplitButton();

    } catch (error) {
        window.MediaToolkit.showToast(`Failed to read PDF: ${error.message}`, 'error');
    }
}

function renderSplitFileInfo() {
    const infoContainer = document.getElementById('split-file-info');
    if (!infoContainer || !pdfState.pdfInfo) return;

    infoContainer.style.display = 'block';
    infoContainer.innerHTML = `
        <div class="pdf-info-item">
            <strong>File:</strong> ${pdfState.pdfInfo.filename}
        </div>
        <div class="pdf-info-item">
            <strong>Pages:</strong> ${pdfState.pdfInfo.page_count}
        </div>
        <div class="pdf-info-item">
            <strong>Size:</strong> ${window.MediaToolkit.formatFileSize(pdfState.pdfInfo.size)}
        </div>
    `;
}

function updatePageRangeVisibility() {
    const pageRangeContainer = document.getElementById('page-range-container');
    if (!pageRangeContainer) return;

    if (pdfState.splitMode === 'range') {
        pageRangeContainer.style.display = 'block';
    } else {
        pageRangeContainer.style.display = 'none';
    }
}

function updateSplitButton() {
    const splitBtn = document.getElementById('split-pdf-btn');
    if (!splitBtn) return;

    splitBtn.disabled = !pdfState.splitFile || pdfState.processing;
    splitBtn.textContent = pdfState.processing ? 'Splitting...' : 'Split PDF';
}

async function splitPDF() {
    if (!pdfState.splitFile || pdfState.processing) return;

    if (pdfState.splitMode === 'range' && !pdfState.pageRange.trim()) {
        window.MediaToolkit.showToast('Please enter a page range', 'warning');
        return;
    }

    pdfState.processing = true;
    updateSplitButton();

    const formData = new FormData();
    formData.append('file', pdfState.splitFile);
    formData.append('mode', pdfState.splitMode);

    if (pdfState.splitMode === 'range') {
        formData.append('pages', pdfState.pageRange);
    }

    try {
        const response = await fetch('/api/pdf/split', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Split failed');
        }

        const blob = await response.blob();
        const contentDisposition = response.headers.get('content-disposition');
        let filename = 'split.zip';

        if (contentDisposition) {
            const match = contentDisposition.match(/filename="(.+)"/);
            if (match) filename = match[1];
        }

        window.MediaToolkit.downloadBlob(blob, filename);
        window.MediaToolkit.showToast('PDF split successfully!', 'success');

    } catch (error) {
        window.MediaToolkit.showToast(`Split failed: ${error.message}`, 'error');
    } finally {
        pdfState.processing = false;
        updateSplitButton();
    }
}
