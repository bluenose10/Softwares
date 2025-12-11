/**
 * AI Image Editor UI - Generate and edit images with Google Gemini
 */

/**
 * Show status message in a specific status element
 * @param {string} elementId - ID of the status element
 * @param {string} message - Message to display
 * @param {string} type - Type of message: 'success', 'error', 'info', 'warning'
 */
function showStatus(elementId, message, type = 'info') {
    const statusEl = document.getElementById(elementId);
    if (!statusEl) return;

    if (!message) {
        statusEl.style.display = 'none';
        statusEl.innerHTML = '';
        return;
    }

    const iconMap = {
        'success': '✓',
        'error': '✗',
        'info': 'ℹ',
        'warning': '⚠'
    };

    const icon = iconMap[type] || iconMap['info'];

    statusEl.innerHTML = `
        <div class="status-message ${type}">
            <span class="status-icon">${icon}</span>
            <span class="status-text">${message}</span>
        </div>
    `;
    statusEl.style.display = 'block';
}

// AI Image state management
const aiImageState = {
    activeTab: 'generate',  // 'generate' or 'edit'
    apiKeyConfigured: false,

    // Generation state
    generatePrompt: '',
    generateStyle: 'photorealistic',
    generateAspectRatio: '1:1',
    generateSize: '1k',
    generating: false,
    generatedImageUrl: null,

    // Edit state
    editFile: null,
    editAction: 'enhance_quality',
    editCustomPrompt: '',
    editStyle: null,
    editing: false,
    originalImageUrl: null,
    editedImageUrl: null,

    // Presets
    stylePresets: {},
    actionPresets: {}
};

/**
 * Initialize AI Image Editor
 */
function initializeAIImage() {
    checkAPIKey();
    loadPresets();
    initializeGenerateTab();
    initializeEditTab();
    initializeTabs();
}

/**
 * Check if Google API key is configured
 */
async function checkAPIKey() {
    try {
        const response = await fetch('/api/ai-image/check-api-key');
        const data = await response.json();
        aiImageState.apiKeyConfigured = data.api_key_configured;

        if (!aiImageState.apiKeyConfigured) {
            showAPIKeyWarning();
        }
    } catch (error) {
        console.error('Failed to check API key:', error);
    }
}

/**
 * Show API key warning message
 */
function showAPIKeyWarning() {
    const panels = ['ai-generate', 'ai-edit'];
    panels.forEach(panelId => {
        const statusEl = document.getElementById(`${panelId}-status`);
        if (statusEl) {
            statusEl.innerHTML = `
                <div class="api-key-warning">
                    <strong>⚠️ Google API Key Not Configured</strong>
                    <p>To use AI image features, add your Google API key to the .env file:</p>
                    <code>GOOGLE_API_KEY=your_key_here</code>
                </div>
            `;
            statusEl.style.display = 'block';
        }
    });
}

/**
 * Load style and action presets
 */
async function loadPresets() {
    try {
        const response = await fetch('/api/ai-image/presets');
        const data = await response.json();
        aiImageState.stylePresets = data.style_presets;
        aiImageState.actionPresets = data.action_presets;
    } catch (error) {
        console.error('Failed to load presets:', error);
    }
}

/**
 * Initialize tab navigation
 */
function initializeTabs() {
    const generateTab = document.getElementById('ai-generate-tab');
    const editTab = document.getElementById('ai-edit-tab');

    const generateContent = document.getElementById('ai-generate-content');
    const editContent = document.getElementById('ai-edit-content');

    generateTab.addEventListener('click', () => {
        aiImageState.activeTab = 'generate';
        generateTab.classList.add('active');
        editTab.classList.remove('active');
        generateContent.classList.add('active');
        editContent.classList.remove('active');
    });

    editTab.addEventListener('click', () => {
        aiImageState.activeTab = 'edit';
        editTab.classList.add('active');
        generateTab.classList.remove('active');
        editContent.classList.add('active');
        generateContent.classList.remove('active');
    });
}

/**
 * Initialize Generate tab
 */
function initializeGenerateTab() {
    const promptTextarea = document.getElementById('ai-generate-prompt');
    const styleButtons = document.querySelectorAll('.style-preset-btn');
    const aspectRatioButtons = document.querySelectorAll('.aspect-ratio-btn');
    const sizeButtons = document.querySelectorAll('.size-btn');
    const generateBtn = document.getElementById('ai-generate-btn');

    // Prompt input
    promptTextarea.addEventListener('input', (e) => {
        aiImageState.generatePrompt = e.target.value;
    });

    // Style selection
    styleButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            styleButtons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            aiImageState.generateStyle = btn.dataset.style;
        });
    });

    // Aspect ratio selection
    aspectRatioButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            aspectRatioButtons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            aiImageState.generateAspectRatio = btn.dataset.ratio;
        });
    });

    // Size selection
    sizeButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            sizeButtons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            aiImageState.generateSize = btn.dataset.size;
        });
    });

    // Generate button
    generateBtn.addEventListener('click', generateAIImage);
}

/**
 * Initialize Edit tab
 */
function initializeEditTab() {
    const uploadZone = document.getElementById('ai-edit-upload-zone');
    const fileInput = document.getElementById('ai-edit-file-input');
    const actionButtons = document.querySelectorAll('.action-preset-btn');
    const customPromptInput = document.getElementById('ai-edit-custom-prompt');
    const editBtn = document.getElementById('ai-edit-btn');

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
            handleEditFile(files[0]);
        }
    });

    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleEditFile(e.target.files[0]);
        }
    });

    // Action selection
    actionButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            actionButtons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            aiImageState.editAction = btn.dataset.action;

            // Show/hide custom prompt based on action
            const promptContainer = document.getElementById('ai-edit-prompt-container');
            if (['add_elements', 'remove_object', 'change_style'].includes(aiImageState.editAction)) {
                promptContainer.style.display = 'block';
            } else {
                promptContainer.style.display = 'none';
            }
        });
    });

    // Custom prompt
    customPromptInput.addEventListener('input', (e) => {
        aiImageState.editCustomPrompt = e.target.value;
    });

    // Edit button
    editBtn.addEventListener('click', editAIImage);
}

/**
 * Handle file selection for editing
 */
function handleEditFile(file) {
    if (!file.type.startsWith('image/')) {
        showStatus('ai-edit-status', 'Please select an image file', 'error');
        return;
    }

    aiImageState.editFile = file;

    // Show preview
    const reader = new FileReader();
    reader.onload = (e) => {
        aiImageState.originalImageUrl = e.target.result;
        displayOriginalImage();
    };
    reader.readAsDataURL(file);
}

/**
 * Display original image preview
 */
function displayOriginalImage() {
    const container = document.getElementById('ai-edit-preview');
    container.innerHTML = `
        <div class="image-preview-container">
            <div class="image-preview-box">
                <p class="preview-label">Original</p>
                <img src="${aiImageState.originalImageUrl}" alt="Original image" class="preview-image">
            </div>
        </div>
    `;
    container.style.display = 'block';
}

/**
 * Generate AI image
 */
async function generateAIImage() {
    if (!aiImageState.apiKeyConfigured) {
        showStatus('ai-generate-status', 'Google API key not configured. Check .env file.', 'error');
        return;
    }

    if (!aiImageState.generatePrompt || aiImageState.generatePrompt.trim().length < 3) {
        showStatus('ai-generate-status', 'Please enter a description (at least 3 characters)', 'error');
        return;
    }

    if (aiImageState.generating) {
        return;
    }

    aiImageState.generating = true;
    const generateBtn = document.getElementById('ai-generate-btn');
    generateBtn.disabled = true;
    generateBtn.textContent = 'Generating...';

    showStatus('ai-generate-status', 'Generating image with AI... This may take 10-30 seconds.', 'info');

    try {
        const response = await fetch('/api/ai-image/generate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                prompt: aiImageState.generatePrompt,
                style: aiImageState.generateStyle,
                aspect_ratio: aiImageState.generateAspectRatio,
                size: aiImageState.generateSize
            })
        });

        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            aiImageState.generatedImageUrl = url;

            displayGeneratedImage(url);
            showStatus('ai-generate-status', '', 'success');
        } else {
            const error = await response.json();
            showStatus('ai-generate-status', error.detail || 'Generation failed', 'error');
        }
    } catch (error) {
        showStatus('ai-generate-status', 'Error generating image', 'error');
    } finally {
        aiImageState.generating = false;
        generateBtn.disabled = false;
        generateBtn.textContent = 'Generate Image';
    }
}

/**
 * Display generated image
 */
function displayGeneratedImage(url) {
    const resultContainer = document.getElementById('ai-generate-result');
    resultContainer.innerHTML = `
        <div class="generated-image-container">
            <img src="${url}" alt="Generated image" class="generated-image">
            <a href="${url}" download="generated_image.png" class="btn btn-primary">
                Download Generated Image
            </a>
        </div>
    `;
    resultContainer.style.display = 'block';
}

/**
 * Edit AI image
 */
async function editAIImage() {
    if (!aiImageState.apiKeyConfigured) {
        showStatus('ai-edit-status', 'Google API key not configured. Check .env file.', 'error');
        return;
    }

    if (!aiImageState.editFile) {
        showStatus('ai-edit-status', 'Please upload an image first', 'error');
        return;
    }

    if (aiImageState.editing) {
        return;
    }

    // Check if custom prompt is needed but missing
    if (['add_elements', 'remove_object'].includes(aiImageState.editAction)) {
        if (!aiImageState.editCustomPrompt || aiImageState.editCustomPrompt.trim().length === 0) {
            showStatus('ai-edit-status', 'Please provide instructions for this action', 'error');
            return;
        }
    }

    aiImageState.editing = true;
    const editBtn = document.getElementById('ai-edit-btn');
    editBtn.disabled = true;
    editBtn.textContent = 'Editing...';

    showStatus('ai-edit-status', 'Editing image with AI... This may take 10-30 seconds.', 'info');

    try {
        const formData = new FormData();
        formData.append('file', aiImageState.editFile);
        formData.append('action', aiImageState.editAction);

        if (aiImageState.editCustomPrompt) {
            formData.append('custom_prompt', aiImageState.editCustomPrompt);
        }

        if (aiImageState.editStyle) {
            formData.append('style', aiImageState.editStyle);
        }

        const response = await fetch('/api/ai-image/edit', {
            method: 'POST',
            body: formData
        });

        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            aiImageState.editedImageUrl = url;

            displayEditedComparison(url);
            showStatus('ai-edit-status', '', 'success');
        } else {
            const error = await response.json();
            showStatus('ai-edit-status', error.detail || 'Edit failed', 'error');
        }
    } catch (error) {
        showStatus('ai-edit-status', 'Error editing image', 'error');
    } finally {
        aiImageState.editing = false;
        editBtn.disabled = false;
        editBtn.textContent = 'Edit Image';
    }
}

/**
 * Display before/after comparison
 */
function displayEditedComparison(editedUrl) {
    const container = document.getElementById('ai-edit-preview');
    container.innerHTML = `
        <div class="image-comparison">
            <div class="comparison-box">
                <p class="preview-label">Before</p>
                <img src="${aiImageState.originalImageUrl}" alt="Original" class="comparison-image">
            </div>
            <div class="comparison-arrow">→</div>
            <div class="comparison-box">
                <p class="preview-label">After</p>
                <img src="${editedUrl}" alt="Edited" class="comparison-image">
            </div>
        </div>
        <a href="${editedUrl}" download="edited_image.png" class="btn btn-primary">
            Download Edited Image
        </a>
    `;
}

// Initialize when DOM is loaded
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeAIImage);
} else {
    initializeAIImage();
}
