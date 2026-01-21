// API Configuration
// const API_BASE = 'http://localhost:8000';
const API_BASE = 'https://dev-be.secury.ai';

// State Management
let authToken = localStorage.getItem('authToken');
let userEmail = localStorage.getItem('userEmail');
let currentQRData = null;
let currentPDFBlob = null;
let html5QrCode = null;

// Initialize App
document.addEventListener('DOMContentLoaded', () => {
    if (authToken) {
        showApp();
    } else {
        showAuth();
    }
});

// Auth Functions
function showTab(tab) {
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
    
    event.target.classList.add('active');
    document.getElementById(tab + 'Tab').classList.add('active');
}

async function register(event) {
    event.preventDefault();
    const email = document.getElementById('registerEmail').value;
    const password = document.getElementById('registerPassword').value;
    
    try {
        const response = await fetch(`${API_BASE}/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showToast('Registration successful! Please login.', 'success');
            showTab('login');
            document.getElementById('loginEmail').value = email;
        } else {
            showToast(data.detail || 'Registration failed', 'error');
        }
    } catch (error) {
        showToast('Network error: ' + error.message, 'error');
    }
}

async function login(event) {
    event.preventDefault();
    const email = document.getElementById('loginEmail').value;
    const password = document.getElementById('loginPassword').value;
    
    try {
        const response = await fetch(`${API_BASE}/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            authToken = data.access_token;
            userEmail = email;
            localStorage.setItem('authToken', authToken);
            localStorage.setItem('userEmail', email);
            
            showToast('Login successful!', 'success');
            showApp();
        } else {
            showToast(data.detail || 'Login failed', 'error');
        }
    } catch (error) {
        showToast('Network error: ' + error.message, 'error');
    }
}

function logout() {
    authToken = null;
    userEmail = null;
    localStorage.removeItem('authToken');
    localStorage.removeItem('userEmail');
    
    showToast('Logged out successfully', 'success');
    showAuth();
}

function showAuth() {
    document.getElementById('authSection').style.display = 'block';
    document.getElementById('appSection').style.display = 'none';
    document.getElementById('userInfo').style.display = 'none';
}

function showApp() {
    document.getElementById('authSection').style.display = 'none';
    document.getElementById('appSection').style.display = 'block';
    document.getElementById('userInfo').style.display = 'flex';
    document.getElementById('userEmail').textContent = userEmail;
}

// Section Navigation
function showSection(section) {
    document.querySelectorAll('.nav-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.content-section').forEach(sec => sec.classList.remove('active'));
    
    event.target.classList.add('active');
    document.getElementById(section + 'Section').classList.add('active');
    
    if (section === 'documents') {
        loadDocuments();
    }
}

// File Upload
function updateFileName() {
    const fileInput = document.getElementById('pdfFile');
    const fileName = document.getElementById('fileName');
    
    if (fileInput.files.length > 0) {
        fileName.textContent = fileInput.files[0].name;
    }
}

async function uploadPDF(event) {
    event.preventDefault();
    
    const fileInput = document.getElementById('pdfFile');
    const scanLimit = document.getElementById('scanLimit').value;
    
    if (!fileInput.files.length) {
        showToast('Please select a PDF file', 'error');
        return;
    }
    
    const formData = new FormData();
    formData.append('file', fileInput.files[0]);
    formData.append('scan_limit', scanLimit);
    
    try {
        const response = await fetch(`${API_BASE}/upload-pdf`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${authToken}` },
            body: formData
        });
        
        const data = await response.json();
        
        if (response.ok) {
            currentQRData = data;
            displayUploadResult(data);
            showToast('QR code generated successfully!', 'success');
        } else {
            showToast(data.detail || 'Upload failed', 'error');
        }
    } catch (error) {
        showToast('Network error: ' + error.message, 'error');
    }
}

function displayUploadResult(data) {
    document.querySelector('.upload-form').style.display = 'none';
    document.getElementById('uploadResult').style.display = 'block';
    
    document.getElementById('qrImage').src = `${API_BASE}/qr/${data.unique_id}`;
    document.getElementById('resultFilename').textContent = data.filename;
    document.getElementById('resultUniqueId').textContent = data.unique_id;
    document.getElementById('resultScanLimit').textContent = data.scan_limit;
    document.getElementById('resultScanCount').textContent = data.scan_count;
}

async function downloadQR() {
    if (!currentQRData) return;
    
    try {
        // Fetch the QR code image
        const response = await fetch(`${API_BASE}/qr/${currentQRData.unique_id}`);
        const blob = await response.blob();
        
        // Create download link
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `secure_qr_${currentQRData.unique_id}.png`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
        
        showToast('QR code downloaded!', 'success');
    } catch (error) {
        showToast('Download failed: ' + error.message, 'error');
    }
}

// Download Stamped PDF
async function downloadStampedPDF() {
    const uniqueId = document.getElementById('resultUniqueId').textContent;
    if (!uniqueId) {
        showToast('Error: No document ID found', 'error');
        return;
    }
    
    console.log('Initiating PDF download for ID:', uniqueId);
    showToast('Preparing PDF with embedded QR...', 'success');
    
    try {
        const response = await fetch(`${API_BASE}/stamp-pdf/${uniqueId}`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
        
        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = url;
            a.download = `stamped_${uniqueId}.pdf`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            showToast('PDF Downloaded!', 'success');
        } else {
            try {
                const err = await response.json();
                showToast(`Error: ${err.detail || 'Download failed'}`, 'error');
            } catch (e) {
                showToast(`Error: Download failed (${response.status})`, 'error');
            }
        }
    } catch (error) {
        console.error('Download error:', error);
        showToast('Network error during download', 'error');
    }
}

function resetUpload() {
    document.querySelector('.upload-form').style.display = 'block';
    document.getElementById('uploadResult').style.display = 'none';
    document.getElementById('pdfFile').value = '';
    document.getElementById('fileName').textContent = 'Choose PDF file';
    document.getElementById('scanLimit').value = '5';
    currentQRData = null;
}

// QR Scanner
async function startScanner() {
    const scannerDiv = document.getElementById('scanner');
    const placeholder = document.getElementById('scannerPlaceholder');
    
    placeholder.style.display = 'none';
    scannerDiv.style.display = 'block';
    
    document.getElementById('startScanBtn').style.display = 'none';
    document.getElementById('stopScanBtn').style.display = 'block';
    
    html5QrCode = new Html5Qrcode("scanner");
    
    try {
        await html5QrCode.start(
            { facingMode: "environment" },
            {
                fps: 10,
                qrbox: { width: 250, height: 250 }
            },
            onScanSuccess,
            onScanError
        );
    } catch (err) {
        showToast('Camera access denied or not available', 'error');
        stopScanner();
    }
}

function stopScanner() {
    if (html5QrCode) {
        html5QrCode.stop().then(() => {
            html5QrCode.clear();
        });
    }
    
    document.getElementById('scanner').style.display = 'none';
    document.getElementById('scannerPlaceholder').style.display = 'flex';
    document.getElementById('startScanBtn').style.display = 'block';
    document.getElementById('stopScanBtn').style.display = 'none';
}

function onScanSuccess(decodedText) {
    stopScanner();
    
    // Extract unique ID from URL
    const urlMatch = decodedText.match(/\/verify\/([^\/\?]+)/);
    if (urlMatch) {
        const uniqueId = urlMatch[1];
        // Fill in the unique ID and prompt for image upload
        document.getElementById('scanUniqueId').value = uniqueId;
        showToast('QR detected! Now upload the QR image to verify authenticity.', 'success');
        // Scroll to upload section
        document.querySelector('.upload-verify-section').scrollIntoView({ behavior: 'smooth' });
    } else {
        showToast('Invalid QR code format', 'error');
    }
}

// Handle QR image upload and auto-decode
async function handleQRImageUpload() {
    const fileInput = document.getElementById('scanQRImage');
    const fileName = document.getElementById('scanFileName');
    const statusDiv = document.getElementById('qrDecodeStatus');
    const verifyButton = document.getElementById('verifyButton');
    const uniqueIdField = document.getElementById('scanUniqueId');
    
    if (fileInput.files.length > 0) {
        const file = fileInput.files[0];
        fileName.textContent = file.name;
        
        // Reset UI
        statusDiv.style.display = 'block';
        statusDiv.className = 'decode-status decoding';
        verifyButton.disabled = true;
        
        // Check if PDF
        if (file.type === 'application/pdf') {
            statusDiv.innerHTML = `📄 PDF selected.<br><small>Click "Verify" to scan document.</small>`;
            statusDiv.className = 'decode-status success'; // Visual cue that it's ready
            verifyButton.disabled = false;
            uniqueIdField.value = 'PDF_UPLOAD'; // Placeholder to bypass check
            return;
        }
        
        statusDiv.textContent = '🔍 Decoding QR code...';
        
        try {
            // Attempt 1: Try HTML5 QR Code scanner
             try {
                const html5QrCode = new Html5Qrcode("reader");
                const decodedText = await html5QrCode.scanFile(file, false);
                await html5QrCode.clear();
                handleDecodedQR(decodedText);
                return;
            } catch (err) {
                console.warn('HTML5 QR scan failed, trying fallback...', err);
            }

            // Attempt 2: Fallback to jsQR
            statusDiv.textContent = '🔄 Trying alternative scanner...';
            const decodedText = await scanWithJsQR(file);
            handleDecodedQR(decodedText);

        } catch (error) {
            console.error('All QR decode attempts failed:', error);
            
            // Show error
            statusDiv.className = 'decode-status error';
            statusDiv.innerHTML = `❌ Could not decode QR code.<br><small>${error.message || 'No QR code found'}</small>`;
            verifyButton.disabled = true;
            uniqueIdField.value = '';
            
            showToast('Failed to decode QR code. Please try a clearer image.', 'error');
        }
    }
}

// Helper to handle successful decode
function handleDecodedQR(decodedText) {
    const statusDiv = document.getElementById('qrDecodeStatus');
    const verifyButton = document.getElementById('verifyButton');
    const uniqueIdField = document.getElementById('scanUniqueId');
    
    // Extract unique ID from URL
    const urlMatch = decodedText.match(/\/verify\/([^\/\?]+)/);
    
    if (urlMatch) {
        const uniqueId = urlMatch[1];
        uniqueIdField.value = uniqueId;
        
        // Show success
        statusDiv.className = 'decode-status success';
        statusDiv.innerHTML = `✅ QR code detected!<br><small>Document ID: <code>${uniqueId}</code></small>`;
        verifyButton.disabled = false;
        
        showToast('QR code decoded successfully!', 'success');
    } else {
        throw new Error('Invalid QR code format - missing verification URL');
    }
}

// Fallback scanner using jsQR
function scanWithJsQR(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = (e) => {
            const img = new Image();
            img.onload = () => {
                const canvas = document.createElement('canvas');
                const context = canvas.getContext('2d');
                canvas.width = img.width;
                canvas.height = img.height;
                context.drawImage(img, 0, 0);
                
                const imageData = context.getImageData(0, 0, canvas.width, canvas.height);
                const code = jsQR(imageData.data, imageData.width, imageData.height);
                
                if (code) {
                    resolve(code.data);
                } else {
                    reject(new Error('jsQR could not find a QR code'));
                }
            };
            img.onerror = () => reject(new Error('Failed to load image'));
            img.src = e.target.result;
        };
        reader.onerror = () => reject(new Error('Failed to read file'));
        reader.readAsDataURL(file);
    });
}

// Verify uploaded QR code or PDF
async function verifyUploadedQR(event) {
    event.preventDefault();
    
    const uniqueId = document.getElementById('scanUniqueId').value.trim();
    const fileInput = document.getElementById('scanQRImage');
    
    if (!fileInput.files.length) {
        showToast('Please select a file', 'error');
        return;
    }
    
    const file = fileInput.files[0];
    
    // Handle PDF Verification
    if (file.type === 'application/pdf') {
        await verifyPDFFile(file);
        return;
    }
    
    // Handle Image Verification
    if (!uniqueId || uniqueId === 'PDF_UPLOAD') {
        showToast('Please ensure QR code is decoded first', 'error');
        return;
    }
    
    // Use the secure verification endpoint for images
    await verifyQRCodeSecure(uniqueId, file);
}

// New: Verify full PDF file
async function verifyPDFFile(file) {
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        showToast('Scanning PDF for authentic QR...', 'success');
        
        // Use the new PDF verification endpoint
        const response = await fetch(`${API_BASE}/verify-pdf`, {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            displaySecureScanSuccess(data);
            showToast('✅ Authentic Document! Verified from PDF.', 'success');
        } else {
            displaySecureScanError(data);
            showToast(`❌ ${data.verdict || 'Verification Failed'}`, 'error');
        }
    } catch (error) {
        displayScanError('Network error: ' + error.message);
        showToast('Network error: ' + error.message, 'error');
    }
}

// New secure verification with QR image
async function verifyQRCodeSecure(uniqueId, qrImageFile) {
    const formData = new FormData();
    formData.append('file', qrImageFile);
    
    try {
        showToast('Verifying QR authenticity...', 'success');
        
        const response = await fetch(`${API_BASE}/verify-secure/${uniqueId}`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${authToken}` },
            body: formData
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            // Authentic - show PDF
            displaySecureScanSuccess(data);
            showToast('✅ Authentic QR! Document loaded.', 'success');
        } else {
            // Counterfeit or suspicious
            displaySecureScanError(data);
            showToast(`❌ ${data.verdict}: Access denied`, 'error');
        }
    } catch (error) {
        displayScanError('Network error: ' + error.message);
        showToast('Network error: ' + error.message, 'error');
    }
}

function displaySecureScanSuccess(data) {
    // Show in scan section
    document.getElementById('scanResult').style.display = 'block';
    document.getElementById('scanSuccess').style.display = 'block';
    document.getElementById('scanError').style.display = 'none';
    
    // Set verdict and score
    document.getElementById('scanVerdictTitle').textContent = `✅ ${data.verdict}`;
    document.getElementById('scanScoreValue').textContent = `${data.authenticity_score}%`;
    
    // Set document info
    document.getElementById('scanFilename').textContent = data.filename;
    document.getElementById('scanUsedCount').textContent = data.scan_count;
    document.getElementById('scanTotalLimit').textContent = data.scan_limit;
    
    // Set security badges
    const details = data.details;
    setBadgeStatus('scanGhostBadge', details.ghost_dots.status);
    setBadgeStatus('scanFreqBadge', details.frequency_watermark.status);
    setBadgeStatus('scanFingerprintBadge', details.pixel_fingerprint.status);
    setBadgeStatus('scanMetadataBadge', details.metadata.status);
    
    // Display PDF inline
    const pdfData = data.pdf_data;
    const pdfBlob = base64ToBlob(pdfData, 'application/pdf');
    const pdfUrl = URL.createObjectURL(pdfBlob);
    document.getElementById('pdfViewer').src = pdfUrl;
}

function displaySecureScanError(data) {
    document.getElementById('scanResult').style.display = 'block';
    document.getElementById('scanSuccess').style.display = 'none';
    document.getElementById('scanError').style.display = 'block';
    
    // Set verdict and score
    const verdict = data.verdict || 'COUNTERFEIT';
    const score = data.authenticity_score || 0;
    
    let verdictClass = verdict === 'SUSPICIOUS' ? 'suspicious' : 'counterfeit';
    let verdictEmoji = verdict === 'SUSPICIOUS' ? '⚠️' : '❌';
    
    document.getElementById('scanErrorVerdictTitle').textContent = `${verdictEmoji} ${verdict}`;
    document.getElementById('scanErrorVerdictTitle').className = `verdict-${verdictClass}`;
    
    const scoreCircle = document.getElementById('scanErrorScoreCircle');
    scoreCircle.className = `score-circle score-${verdictClass}`;
    document.getElementById('scanErrorScoreValue').textContent = `${score}%`;
    
    // Set error message
    document.getElementById('scanErrorMessage').textContent = 
        data.message || `This QR code appears to be ${verdict.toLowerCase()}. Access denied for security reasons.`;
    
    // Set security details
    const details = data.details;
    if (details) {
        document.getElementById('scanErrorGhost').textContent = 
            `${details.ghost_dots.score}% (${details.ghost_dots.status})`;
        document.getElementById('scanErrorFreq').textContent = 
            `${details.frequency_watermark.score}% (${details.frequency_watermark.status})`;
        document.getElementById('scanErrorFingerprint').textContent = 
            `${details.pixel_fingerprint.score}% (${details.pixel_fingerprint.status})`;
        document.getElementById('scanErrorMetadata').textContent = 
            `${details.metadata.score}% (${details.metadata.status})`;
    }
}

function setBadgeStatus(badgeId, status) {
    const badge = document.getElementById(badgeId);
    badge.className = `security-badge badge-${status.toLowerCase()}`;
}

function base64ToBlob(base64, contentType) {
    const byteCharacters = atob(base64);
    const byteNumbers = new Array(byteCharacters.length);
    for (let i = 0; i < byteCharacters.length; i++) {
        byteNumbers[i] = byteCharacters.charCodeAt(i);
    }
    const byteArray = new Uint8Array(byteNumbers);
    return new Blob([byteArray], { type: contentType });
}

function resetScan() {
    document.getElementById('scanResult').style.display = 'none';
    document.getElementById('scanUniqueId').value = '';
    document.getElementById('scanQRImage').value = '';
    document.getElementById('scanFileName').textContent = 'Choose QR code image';
    document.getElementById('qrDecodeStatus').style.display = 'none';
    document.getElementById('verifyButton').disabled = true;
}

// Legacy function - kept for compatibility
async function verifyQRCode(uniqueId) {
    showToast('Please use the Verify Authenticity section to upload QR image', 'warning');
    document.getElementById('verifyUniqueId').value = uniqueId;
    showSection('verify');
}

function displayScanSuccess(filename, scanCount, scanLimit) {
    document.getElementById('scanResult').style.display = 'block';
    document.getElementById('scanSuccess').style.display = 'block';
    document.getElementById('scanError').style.display = 'none';
    
    document.getElementById('scanFilename').textContent = filename;
    document.getElementById('scanUsedCount').textContent = scanCount;
    document.getElementById('scanTotalLimit').textContent = scanLimit;
}

function displayScanError(message) {
    document.getElementById('scanResult').style.display = 'block';
    document.getElementById('scanSuccess').style.display = 'none';
    document.getElementById('scanError').style.display = 'block';
    
    document.getElementById('scanErrorMessage').textContent = message;
}

function downloadPDF() {
    if (!currentPDFBlob) return;
    
    const url = URL.createObjectURL(currentPDFBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = document.getElementById('scanFilename').textContent;
    link.click();
    
    URL.revokeObjectURL(url);
    showToast('PDF downloaded!', 'success');
}

// Documents List
async function loadDocuments() {
    const listDiv = document.getElementById('documentsList');
    listDiv.innerHTML = '<p class="loading">Loading documents...</p>';
    
    // Note: This endpoint doesn't exist in the backend yet
    // You would need to add a GET /documents endpoint
    showToast('Documents list feature coming soon!', 'warning');
    listDiv.innerHTML = '<p class="loading">Feature coming soon...</p>';
}

// QR Authenticity Verification
function updateVerifyFileName() {
    const fileInput = document.getElementById('verifyQRImage');
    const fileName = document.getElementById('verifyFileName');
    
    if (fileInput.files.length > 0) {
        fileName.textContent = fileInput.files[0].name;
    }
}

async function verifyAuthenticity(event) {
    event.preventDefault();
    
    const uniqueId = document.getElementById('verifyUniqueId').value.trim();
    const fileInput = document.getElementById('verifyQRImage');
    
    if (!fileInput.files.length) {
        showToast('Please select a QR code image', 'error');
        return;
    }
    
    // Use the secure verification endpoint
    await verifyQRCodeSecure(uniqueId, fileInput.files[0]);
    
    // Also show detailed results in verify section
    const formData = new FormData();
    formData.append('file', fileInput.files[0]);
    
    try {
        const response = await fetch(`${API_BASE}/verify-authenticity/${uniqueId}`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${authToken}` },
            body: formData
        });
        
        const data = await response.json();
        
        if (response.ok) {
            displayVerificationResult(data);
        }
    } catch (error) {
        console.error('Detailed verification error:', error);
    }
}

function displayVerificationResult(data) {
    document.querySelector('.verify-form').style.display = 'none';
    document.getElementById('verifyResult').style.display = 'block';
    document.getElementById('verifySuccess').style.display = 'block';
    
    // Set verdict and score
    const verdict = data.verdict;
    const score = data.authenticity_score;
    
    let verdictEmoji = '';
    let verdictClass = '';
    
    if (verdict === 'AUTHENTIC') {
        verdictEmoji = '✅';
        verdictClass = 'authentic';
    } else if (verdict === 'SUSPICIOUS') {
        verdictEmoji = '⚠️';
        verdictClass = 'suspicious';
    } else {
        verdictEmoji = '❌';
        verdictClass = 'counterfeit';
    }
    
    document.getElementById('verdictTitle').textContent = `${verdictEmoji} ${verdict}`;
    document.getElementById('verdictTitle').className = `verdict-${verdictClass}`;
    
    // Set score circle
    const scoreCircle = document.getElementById('scoreCircle');
    scoreCircle.className = `score-circle score-${verdictClass}`;
    document.getElementById('scoreValue').textContent = `${score}%`;
    
    // Set security layer details
    const details = data.details;
    
    // Ghost Dots
    setLayerDetails('ghost', details.ghost_dots);
    if (details.ghost_dots.detected !== undefined) {
        document.getElementById('ghostDetails').textContent = 
            `Detected: ${details.ghost_dots.detected}/${details.ghost_dots.expected} dots`;
    }
    
    // Frequency Watermark
    setLayerDetails('freq', details.frequency_watermark);
    if (details.frequency_watermark.correlation !== undefined) {
        document.getElementById('freqDetails').textContent = 
            `Correlation: ${(details.frequency_watermark.correlation * 100).toFixed(1)}%`;
    }
    
    // Pixel Fingerprint
    setLayerDetails('fingerprint', details.pixel_fingerprint);
    if (details.pixel_fingerprint.integrity !== undefined) {
        document.getElementById('fingerprintDetails').textContent = 
            `Integrity: ${(details.pixel_fingerprint.integrity * 100).toFixed(1)}%`;
    }
    
    // Metadata
    setLayerDetails('metadata', details.metadata);
    if (details.metadata.sharpness !== undefined) {
        document.getElementById('metadataDetails').textContent = 
            `Sharpness: ${details.metadata.sharpness.toFixed(1)}`;
    }
    
    // Warnings
    if (data.warnings && data.warnings.length > 0) {
        document.getElementById('warningsSection').style.display = 'block';
        const warningsList = document.getElementById('warningsList');
        warningsList.innerHTML = '';
        data.warnings.forEach(warning => {
            const li = document.createElement('li');
            li.textContent = warning;
            warningsList.appendChild(li);
        });
    } else {
        document.getElementById('warningsSection').style.display = 'none';
    }
}

function setLayerDetails(prefix, layerData) {
    const score = layerData.score || 0;
    const status = layerData.status || 'UNKNOWN';
    
    document.getElementById(`${prefix}Score`).textContent = `${score.toFixed(1)}%`;
    
    const statusElement = document.getElementById(`${prefix}Status`);
    statusElement.textContent = status;
    statusElement.className = `layer-status status-${status.toLowerCase()}`;
}

function resetVerify() {
    document.querySelector('.verify-form').style.display = 'block';
    document.getElementById('verifyResult').style.display = 'none';
    document.getElementById('verifyUniqueId').value = '';
    document.getElementById('verifyQRImage').value = '';
    document.getElementById('verifyFileName').textContent = 'Choose QR code image';
}

// Toast Notifications
function showToast(message, type = 'success') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = `toast ${type} show`;
    
    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}
