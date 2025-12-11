/**
 * Media Toolkit - Core JavaScript
 * Handles navigation, utilities, and UI interactions
 */

// ============================================
// Navigation Functions
// ============================================

/**
 * Show a specific feature panel and hide the main menu
 * @param {string} panelId - The ID of the panel to show
 */
function showPanel(panelId) {
    const mainMenu = document.getElementById('main-menu');
    const panel = document.getElementById(panelId);

    if (!panel) {
        console.error(`Panel with ID "${panelId}" not found`);
        return;
    }

    // Hide main menu
    mainMenu.style.display = 'none';

    // Show selected panel
    panel.style.display = 'block';
}

/**
 * Hide all panels and show the main menu
 */
function showMainMenu() {
    const mainMenu = document.getElementById('main-menu');
    const panels = document.querySelectorAll('.panel');

    // Hide all panels
    panels.forEach(panel => {
        panel.style.display = 'none';
    });

    // Show main menu
    mainMenu.style.display = 'block';
}

// ============================================
// Utility Functions
// ============================================

/**
 * Format bytes to human-readable file size
 * @param {number} bytes - The number of bytes
 * @param {number} decimals - Number of decimal places (default: 2)
 * @returns {string} Formatted file size (e.g., "1.5 MB")
 */
function formatFileSize(bytes, decimals = 2) {
    if (bytes === 0) return '0 Bytes';

    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];

    const i = Math.floor(Math.log(bytes) / Math.log(k));

    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}

/**
 * Format seconds to duration string
 * @param {number} seconds - Duration in seconds
 * @returns {string} Formatted duration (e.g., "1:23" or "1:23:45")
 */
function formatDuration(seconds) {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);

    if (hours > 0) {
        return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    } else {
        return `${minutes}:${secs.toString().padStart(2, '0')}`;
    }
}

/**
 * Show a toast notification
 * @param {string} message - The message to display
 * @param {string} type - Type of toast: 'success', 'error', 'warning', 'info'
 * @param {number} duration - Duration in milliseconds (default: 5000)
 */
function showToast(message, type = 'info', duration = 5000) {
    const container = document.getElementById('toast-container');

    // Create toast element
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;

    // Create message element
    const messageEl = document.createElement('div');
    messageEl.className = 'toast-message';
    messageEl.textContent = message;

    // Create close button
    const closeBtn = document.createElement('button');
    closeBtn.className = 'toast-close';
    closeBtn.innerHTML = '&times;';
    closeBtn.onclick = () => removeToast(toast);

    // Assemble toast
    toast.appendChild(messageEl);
    toast.appendChild(closeBtn);
    container.appendChild(toast);

    // Auto-remove after duration
    setTimeout(() => removeToast(toast), duration);
}

/**
 * Remove a toast notification with fade-out animation
 * @param {HTMLElement} toast - The toast element to remove
 */
function removeToast(toast) {
    toast.style.animation = 'fadeOut 0.3s ease';
    setTimeout(() => {
        if (toast.parentNode) {
            toast.parentNode.removeChild(toast);
        }
    }, 300);
}

/**
 * Validate file type
 * @param {File} file - The file to validate
 * @param {string[]} allowedTypes - Array of allowed MIME types or extensions
 * @returns {boolean} True if file type is allowed
 */
function validateFileType(file, allowedTypes) {
    const fileExtension = '.' + file.name.split('.').pop().toLowerCase();
    const mimeType = file.type.toLowerCase();

    return allowedTypes.some(type => {
        if (type.startsWith('.')) {
            return fileExtension === type.toLowerCase();
        }
        return mimeType === type.toLowerCase() || mimeType.startsWith(type.toLowerCase());
    });
}

/**
 * Create a download link for a blob
 * @param {Blob} blob - The blob to download
 * @param {string} filename - The filename for the download
 */
function downloadBlob(blob, filename) {
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.style.display = 'none';
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
}

/**
 * Set button loading state
 * @param {HTMLButtonElement} button - Button element
 * @param {boolean} loading - Whether button should be in loading state
 * @param {string} loadingText - Text to show while loading (default: "Processing...")
 */
function setButtonLoading(button, loading, loadingText = 'Processing...') {
    if (loading) {
        button.disabled = true;
        button.dataset.originalText = button.textContent;
        button.innerHTML = `<span class="spinner"></span> ${loadingText}`;
        button.classList.add('loading');
    } else {
        button.disabled = false;
        button.textContent = button.dataset.originalText || button.textContent;
        button.classList.remove('loading');
    }
}

// ============================================
// API Helper Functions
// ============================================

/**
 * Make an API request with error handling
 * @param {string} endpoint - API endpoint
 * @param {object} options - Fetch options
 * @returns {Promise<Response>} The fetch response
 */
async function apiRequest(endpoint, options = {}) {
    try {
        const response = await fetch(endpoint, {
            ...options,
            headers: {
                ...options.headers,
            }
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || errorData.error || `HTTP ${response.status}: ${response.statusText}`);
        }

        return response;
    } catch (error) {
        console.error('API request failed:', error);
        throw error;
    }
}

/**
 * Upload file with progress tracking
 * @param {string} endpoint - API endpoint
 * @param {FormData} formData - Form data containing file(s)
 * @param {Function} onProgress - Progress callback (receives percentage)
 * @returns {Promise<Response>} The fetch response
 */
async function uploadFile(endpoint, formData, onProgress = null) {
    return new Promise((resolve, reject) => {
        const xhr = new XMLHttpRequest();

        // Track upload progress
        if (onProgress) {
            xhr.upload.addEventListener('progress', (e) => {
                if (e.lengthComputable) {
                    const percentage = (e.loaded / e.total) * 100;
                    onProgress(percentage);
                }
            });
        }

        // Handle completion
        xhr.addEventListener('load', () => {
            if (xhr.status >= 200 && xhr.status < 300) {
                resolve(xhr.response);
            } else {
                try {
                    const errorData = JSON.parse(xhr.responseText);
                    reject(new Error(errorData.detail || errorData.error || `Upload failed: ${xhr.statusText}`));
                } catch {
                    reject(new Error(`Upload failed: ${xhr.statusText}`));
                }
            }
        });

        // Handle errors
        xhr.addEventListener('error', () => {
            reject(new Error('Network error during upload'));
        });

        xhr.addEventListener('abort', () => {
            reject(new Error('Upload cancelled'));
        });

        // Send request
        xhr.open('POST', endpoint);
        xhr.responseType = 'blob';
        xhr.send(formData);
    });
}

// ============================================
// Event Listeners
// ============================================

document.addEventListener('DOMContentLoaded', () => {
    // Card click handlers - navigate to feature panels
    const cards = document.querySelectorAll('.card');
    cards.forEach(card => {
        card.addEventListener('click', () => {
            const panelId = card.getAttribute('data-panel');
            if (panelId) {
                showPanel(panelId);
            }
        });
    });

    // Back button handlers - return to main menu
    const backButtons = document.querySelectorAll('.back-button');
    backButtons.forEach(button => {
        button.addEventListener('click', (e) => {
            e.stopPropagation();
            showMainMenu();
        });
    });

    // Add fadeOut animation to CSS if not present
    if (!document.querySelector('style#dynamic-animations')) {
        const style = document.createElement('style');
        style.id = 'dynamic-animations';
        style.textContent = `
            @keyframes fadeOut {
                from {
                    opacity: 1;
                    transform: translateX(0);
                }
                to {
                    opacity: 0;
                    transform: translateX(20px);
                }
            }
        `;
        document.head.appendChild(style);
    }

    // Load usage statistics
    loadUsageStats();

    console.log('Media Toolkit initialized');
});

// ============================================
// Usage Statistics & Limits
// ============================================

async function loadUsageStats() {
    try {
        const response = await fetch('/api/usage/stats');
        const stats = await response.json();

        displayUsageBanner(stats);
    } catch (error) {
        console.error('Failed to load usage stats:', error);
    }
}

function displayUsageBanner(stats) {
    const banner = document.getElementById('usage-banner');

    if (!banner) return;

    if (stats.is_pro) {
        banner.style.display = 'none';
        return;
    }

    // Show banner for free users
    const remaining = stats.conversions_remaining;
    const used = stats.conversions_used;
    const total = used + remaining;

    let bannerClass = 'info';
    let message = '';

    if (remaining === 0) {
        bannerClass = 'warning';
        message = `⚠️ Daily limit reached (${used}/${total} conversions used). <a href="/pricing">Upgrade to Pro ($9/month)</a> for unlimited conversions or wait ${stats.hours_until_reset} hours for reset.`;
    } else if (remaining <= 2) {
        bannerClass = 'warning';
        message = `⚠️ Only ${remaining} conversions left today (${used}/${total} used). <a href="/pricing">Upgrade to Pro</a> for unlimited access.`;
    } else {
        message = `Free Tier: ${used}/${total} conversions used today • ${stats.max_file_size_mb}MB file limit • <a href="/pricing">Upgrade to Pro ($9/mo)</a> for unlimited conversions + 500MB files`;
    }

    banner.className = `usage-banner ${bannerClass}`;
    banner.innerHTML = message;
    banner.style.display = 'block';
}
});

// ============================================
// Global Exports (for module usage)
// ============================================

window.MediaToolkit = {
    showPanel,
    showMainMenu,
    formatFileSize,
    formatDuration,
    showToast,
    validateFileType,
    downloadBlob,
    setButtonLoading,
    apiRequest,
    uploadFile
};
