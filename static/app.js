// API Configuration
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

function downloadQR() {
    if (!currentQRData) return;
    
    const link = document.createElement('a');
    link.href = `${API_BASE}/qr/${currentQRData.unique_id}`;
    link.download = `qr_${currentQRData.unique_id}.png`;
    link.click();
    
    showToast('QR code downloaded!', 'success');
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
        verifyQRCode(uniqueId);
    } else {
        showToast('Invalid QR code format', 'error');
    }
}

function onScanError(error) {
    // Ignore scan errors (they happen frequently during scanning)
}

function verifyManualId() {
    const uniqueId = document.getElementById('manualUniqueId').value.trim();
    
    if (!uniqueId) {
        showToast('Please enter a unique ID', 'error');
        return;
    }
    
    verifyQRCode(uniqueId);
}

async function verifyQRCode(uniqueId) {
    try {
        const response = await fetch(`${API_BASE}/verify/${uniqueId}`, {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        
        if (response.ok) {
            const blob = await response.blob();
            currentPDFBlob = blob;
            
            const scanCount = response.headers.get('X-Scan-Count');
            const scanLimit = response.headers.get('X-Scan-Limit');
            const filename = response.headers.get('Content-Disposition')?.match(/filename="(.+)"/)?.[1] || 'document.pdf';
            
            displayScanSuccess(filename, scanCount, scanLimit);
            showToast('Verification successful!', 'success');
        } else {
            const data = await response.json();
            displayScanError(data.detail || 'Verification failed');
            showToast(data.detail || 'Verification failed', 'error');
        }
    } catch (error) {
        displayScanError('Network error: ' + error.message);
        showToast('Network error: ' + error.message, 'error');
    }
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

// Toast Notifications
function showToast(message, type = 'success') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = `toast ${type} show`;
    
    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}
