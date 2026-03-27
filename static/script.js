/**
 * Smart Chef AI — Multi-Agent Recipe Generator UI Logic
 * Handles text input, file upload, API calls, agent pipeline animation, and result rendering
 */

// ==========================================
// Tab Switching
// ==========================================

function switchTab(tabId) {
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
    document.querySelector(`[data-tab="${tabId}"]`).classList.add('active');
    document.getElementById(tabId).classList.add('active');
}

// ==========================================
// Pipeline Animation
// ==========================================

function animatePipeline(stage) {
    const steps = ['pipeline-input', 'pipeline-analyzer', 'pipeline-chef', 'pipeline-output'];
    // Reset all
    steps.forEach(id => {
        const el = document.getElementById(id);
        el.classList.remove('active', 'completed', 'rejected');
    });

    if (stage === 'analyzing') {
        document.getElementById('pipeline-input').classList.add('completed');
        document.getElementById('pipeline-analyzer').classList.add('active');
    } else if (stage === 'cooking') {
        document.getElementById('pipeline-input').classList.add('completed');
        document.getElementById('pipeline-analyzer').classList.add('completed');
        document.getElementById('pipeline-chef').classList.add('active');
    } else if (stage === 'done') {
        steps.forEach(id => document.getElementById(id).classList.add('completed'));
    } else if (stage === 'rejected') {
        document.getElementById('pipeline-input').classList.add('completed');
        document.getElementById('pipeline-analyzer').classList.add('rejected');
        document.getElementById('pipeline-chef').classList.add('rejected');
        document.getElementById('pipeline-output').classList.add('rejected');
    } else if (stage === 'reset') {
        // Already reset above
    }
}

// ==========================================
// File Upload
// ==========================================

let selectedFile = null;

const uploadZone = document.getElementById('upload-zone');

uploadZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadZone.classList.add('dragover');
});

uploadZone.addEventListener('dragleave', () => {
    uploadZone.classList.remove('dragover');
});

uploadZone.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadZone.classList.remove('dragover');
    const files = e.dataTransfer.files;
    if (files.length > 0) handleFile(files[0]);
});

uploadZone.addEventListener('click', () => {
    document.getElementById('file-input').click();
});

function handleFileSelect(event) {
    const file = event.target.files[0];
    if (file) handleFile(file);
}

function handleFile(file) {
    const allowedExtensions = ['.pdf', '.docx', '.doc', '.txt', '.png', '.jpg', '.jpeg', '.webp', '.bmp', '.gif'];
    const fileExt = '.' + file.name.split('.').pop().toLowerCase();

    if (!allowedExtensions.includes(fileExt)) {
        showError('Unsupported file type. Please upload PDF, DOCX, TXT, or image files.');
        return;
    }

    if (file.size > 10 * 1024 * 1024) {
        showError('File is too large. Maximum size is 10MB.');
        return;
    }

    selectedFile = file;
    showFilePreview(file);
}

function showFilePreview(file) {
    const preview = document.getElementById('file-preview');
    const zone = document.getElementById('upload-zone');

    const ext = file.name.split('.').pop().toLowerCase();
    const iconMap = {
        'pdf': '📕', 'docx': '📘', 'doc': '📘', 'txt': '📄',
        'png': '🖼️', 'jpg': '🖼️', 'jpeg': '🖼️', 'webp': '🖼️', 'bmp': '🖼️', 'gif': '🖼️',
    };

    document.getElementById('file-icon').textContent = iconMap[ext] || '📄';
    document.getElementById('file-name').textContent = file.name;
    document.getElementById('file-size').textContent = formatFileSize(file.size);

    zone.style.display = 'none';
    preview.style.display = 'block';
}

function removeFile() {
    selectedFile = null;
    document.getElementById('file-input').value = '';
    document.getElementById('file-preview').style.display = 'none';
    document.getElementById('upload-zone').style.display = 'block';
}

function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

// ==========================================
// Form Submission — Text Input
// ==========================================

async function handleTextSubmit(event) {
    event.preventDefault();

    const ingredients = document.getElementById('ingredients').value.trim();
    if (!ingredients) {
        showError('Please enter at least some ingredients.');
        return;
    }

    const formData = new FormData();
    formData.append('ingredients', ingredients);
    formData.append('dietary_restrictions', document.getElementById('dietary').value);
    formData.append('cuisine_preference', document.getElementById('cuisine').value);
    formData.append('meal_type', document.getElementById('meal-type').value);

    const btn = document.getElementById('btn-text-generate');
    await sendRequest('/api/generate', formData, btn, false);
}

// ==========================================
// Form Submission — File Upload
// ==========================================

async function handleUploadSubmit(event) {
    event.preventDefault();

    if (!selectedFile) {
        showError('Please select a file to upload.');
        return;
    }

    const formData = new FormData();
    formData.append('file', selectedFile);
    formData.append('dietary_restrictions', document.getElementById('upload-dietary').value);
    formData.append('cuisine_preference', document.getElementById('upload-cuisine').value);
    formData.append('meal_type', document.getElementById('upload-meal').value);

    const btn = document.getElementById('btn-upload-generate');
    await sendRequest('/api/upload', formData, btn, true);
}

// ==========================================
// API Request Handler
// ==========================================

async function sendRequest(endpoint, formData, button, isUpload) {
    button.classList.add('loading');
    button.disabled = true;
    hideError();
    document.getElementById('result-section').style.display = 'none';

    // Animate pipeline
    animatePipeline('analyzing');

    // Update button text for stages
    const loadingText = button.querySelector('.btn-loading');
    if (isUpload) {
        loadingText.innerHTML = '<div class="spinner"></div> Agent 1 analyzing document...';
    } else {
        loadingText.innerHTML = '<div class="spinner"></div> Agent pipeline processing...';
    }

    // Simulate stage transition
    setTimeout(() => {
        animatePipeline('cooking');
        loadingText.innerHTML = '<div class="spinner"></div> Agent 2: Chef Gemini cooking...';
    }, 2000);

    try {
        const response = await fetch(endpoint, {
            method: 'POST',
            body: formData,
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || 'Something went wrong');
        }

        // Check if the response is a rejection
        const isRejected = data.recipe &&
            (data.recipe.toLowerCase().includes('rejected') ||
                data.recipe.toLowerCase().includes('not contain food') ||
                data.recipe.toLowerCase().includes('not food-related') ||
                data.recipe.toLowerCase().includes('not related to food') ||
                data.recipe.toLowerCase().includes('does not appear to be'));

        if (isRejected) {
            animatePipeline('rejected');
        } else {
            animatePipeline('done');
        }

        displayResult(data, isRejected, isUpload);
    } catch (error) {
        console.error('Error:', error);
        animatePipeline('reset');
        showError(error.message || 'Failed to process request. Please try again.');
    } finally {
        button.classList.remove('loading');
        button.disabled = false;
    }
}

// ==========================================
// Result Display
// ==========================================

function displayResult(data, isRejected, isUpload) {
    const resultSection = document.getElementById('result-section');
    const resultCard = document.getElementById('result-card');
    const recipeContent = document.getElementById('recipe-content');
    const extractedInfo = document.getElementById('extracted-info');
    const agentStatus = document.getElementById('agent-status');
    const resultTitleText = document.getElementById('result-title-text');

    // Update card style based on rejection
    resultCard.classList.remove('rejected');
    if (isRejected) {
        resultCard.classList.add('rejected');
        resultTitleText.textContent = '❌ Content Rejected';
    } else {
        resultTitleText.textContent = '✅ Generated Recipe';
    }

    // Update agent status indicators
    const statusAnalyzer = document.getElementById('status-analyzer');
    const statusChef = document.getElementById('status-chef');
    const analyzerResult = document.getElementById('analyzer-result');
    const chefResult = document.getElementById('chef-result');

    statusAnalyzer.className = 'agent-step completed';
    analyzerResult.textContent = isRejected ? 'Non-food detected ❌' : 'Food content found ✅';

    if (isRejected) {
        statusChef.className = 'agent-step rejected';
        chefResult.textContent = 'Skipped (rejected) ⛔';
    } else {
        statusChef.className = 'agent-step completed';
        chefResult.textContent = 'Recipe generated ✅';
    }

    if (isRejected) {
        statusAnalyzer.className = 'agent-step rejected';
    }

    // Parse markdown to HTML
    if (typeof marked !== 'undefined') {
        recipeContent.innerHTML = marked.parse(data.recipe || 'No response generated.');
    } else {
        recipeContent.innerHTML = (data.recipe || 'No response generated.')
            .replace(/\n/g, '<br>')
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>');
    }

    // Show extracted text if present (from file upload)
    if (data.extracted_text && isUpload) {
        const filenameEl = document.getElementById('extracted-filename');
        if (filenameEl) filenameEl.textContent = data.file_name || 'uploaded file';
        document.getElementById('extracted-text').textContent = data.extracted_text;
        extractedInfo.style.display = 'block';
    } else {
        extractedInfo.style.display = 'none';
    }

    resultSection.style.display = 'block';
    resultSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

// ==========================================
// Copy Recipe
// ==========================================

function copyRecipe() {
    const recipeContent = document.getElementById('recipe-content');
    const text = recipeContent.innerText;

    navigator.clipboard.writeText(text).then(() => {
        const btn = document.querySelector('.btn-copy');
        btn.classList.add('copied');
        btn.innerHTML = `
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>
            Copied!
        `;
        setTimeout(() => {
            btn.classList.remove('copied');
            btn.innerHTML = `
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
                Copy
            `;
        }, 2000);
    }).catch(() => {
        const range = document.createRange();
        range.selectNodeContents(recipeContent);
        window.getSelection().removeAllRanges();
        window.getSelection().addRange(range);
        document.execCommand('copy');
        window.getSelection().removeAllRanges();
    });
}

// ==========================================
// Error Handling
// ==========================================

function showError(message) {
    const toast = document.getElementById('error-toast');
    document.getElementById('error-message').textContent = message;
    toast.style.display = 'flex';
    setTimeout(() => { toast.style.display = 'none'; }, 5000);
}

function hideError() {
    document.getElementById('error-toast').style.display = 'none';
}

// ==========================================
// Initialize
// ==========================================

document.addEventListener('DOMContentLoaded', () => {
    const ingredientsInput = document.getElementById('ingredients');
    if (ingredientsInput) ingredientsInput.focus();
});
