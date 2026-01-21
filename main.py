import hashlib
import secrets
import sqlite3
from datetime import datetime, timedelta
from typing import Optional
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form
from fastapi.responses import Response, FileResponse, RedirectResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, EmailStr
from qr_utils import generate_qr_code
from secure_qr_generator import generate_secure_qr_code
from counterfeit_detector import verify_qr_code_bytes
import os
import json
import base64

app = FastAPI(title="Secure PDF QR System")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Security
security = HTTPBearer()

# Database setup
DB_PATH = "secure_qr.db"

def init_db():
    """Initialize SQLite database with required tables."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Access tokens table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            token TEXT UNIQUE NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    
    # PDF documents table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            unique_id TEXT UNIQUE NOT NULL,
            user_id INTEGER NOT NULL,
            filename TEXT NOT NULL,
            pdf_data BLOB NOT NULL,
            scan_limit INTEGER NOT NULL,
            scan_count INTEGER DEFAULT 0,
            ghost_pattern TEXT,
            frequency_signature TEXT,
            fingerprint_hash TEXT,
            security_version INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    
    conn.commit()
    conn.close()

# Initialize database on startup
init_db()

# Pydantic models
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class DocumentResponse(BaseModel):
    unique_id: str
    filename: str
    scan_limit: int
    scan_count: int
    qr_url: str

# Helper functions
def hash_password(password: str) -> str:
    """Hash password using SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()

def create_access_token(user_id: int) -> str:
    """Create a new access token for user."""
    token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(hours=24)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO tokens (user_id, token, expires_at) VALUES (?, ?, ?)",
        (user_id, token, expires_at)
    )
    conn.commit()
    conn.close()
    
    return token

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> int:
    """Verify access token and return user_id."""
    token = credentials.credentials
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT user_id FROM tokens WHERE token = ? AND expires_at > ?",
        (token, datetime.utcnow())
    )
    result = cursor.fetchone()
    conn.close()
    
    if not result:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    return result[0]

# API Endpoints

@app.post("/register")
async def register(request: LoginRequest):
    """Register a new user."""
    password_hash = hash_password(request.password)
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (email, password_hash) VALUES (?, ?)",
            (request.email, password_hash)
        )
        conn.commit()
        conn.close()
        
        return {"message": "User registered successfully", "email": request.email}
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Email already registered")

@app.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """Login with email and password."""
    password_hash = hash_password(request.password)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id FROM users WHERE email = ? AND password_hash = ?",
        (request.email, password_hash)
    )
    result = cursor.fetchone()
    conn.close()
    
    if not result:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    user_id = result[0]
    access_token = create_access_token(user_id)
    
    return LoginResponse(access_token=access_token)

@app.post("/upload-pdf", response_model=DocumentResponse)
async def upload_pdf(
    file: UploadFile = File(...),
    scan_limit: int = Form(...),
    user_id: int = Depends(verify_token)
):
    """
    Upload PDF file and generate QR code.
    
    Args:
        file: PDF file to upload
        scan_limit: Maximum number of times QR can be scanned
        user_id: Authenticated user ID (from token)
    
    Returns:
        Document info with QR code URL
    """
    # Validate file type
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    # Read PDF data
    pdf_data = await file.read()
    
    # Generate unique ID
    unique_id = secrets.token_urlsafe(16)
    
    # Generate secure QR code with anti-counterfeiting features
    base_url = os.getenv("BASE_URL", "http://127.0.0.1:8000")
    verify_url = f"{base_url}/verify/{unique_id}"
    qr_image_bytes, security_metadata = generate_secure_qr_code(verify_url, unique_id)
    
    # Save to database with security metadata
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO documents (unique_id, user_id, filename, pdf_data, scan_limit,
                                  ghost_pattern, frequency_signature, fingerprint_hash, security_version)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (unique_id, user_id, file.filename, pdf_data, scan_limit,
         json.dumps(security_metadata['ghost_pattern']),
         json.dumps(security_metadata['watermark_signature']),
         security_metadata['fingerprint_hash'],
         security_metadata['security_version'])
    )
    conn.commit()
    conn.close()
    
    # Save QR code to file
    qr_filename = f"qr_{unique_id}.png"
    qr_path = os.path.join("qr_codes", qr_filename)
    os.makedirs("qr_codes", exist_ok=True)
    
    with open(qr_path, "wb") as f:
        f.write(qr_image_bytes)
    
    base_url = os.getenv("BASE_URL", "http://127.0.0.1:8000")
    
    return DocumentResponse(
        unique_id=unique_id,
        filename=file.filename,
        scan_limit=scan_limit,
        scan_count=0,
        qr_url=f"{base_url}/qr/{unique_id}"
    )

@app.get("/qr/{unique_id}")
async def get_qr_code(unique_id: str):
    """Get QR code image for a document."""
    qr_path = os.path.join("qr_codes", f"qr_{unique_id}.png")
    
    if not os.path.exists(qr_path):
        raise HTTPException(status_code=404, detail="QR code not found")
    
    return FileResponse(qr_path, media_type="image/png")

@app.get("/verify/{unique_id}")
async def verify_and_get_pdf(
    unique_id: str,
    user_id: int = Depends(verify_token)
):
    """
    Verify QR code and return PDF if scan limit not exceeded.
    
    Args:
        unique_id: Unique document identifier from QR code
        user_id: Authenticated user ID (from token)
    
    Returns:
        PDF file if valid, error otherwise
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get document info
    cursor.execute(
        """SELECT id, user_id, filename, pdf_data, scan_limit, scan_count 
           FROM documents WHERE unique_id = ?""",
        (unique_id,)
    )
    result = cursor.fetchone()
    
    if not result:
        conn.close()
        raise HTTPException(status_code=404, detail="Document not found")
    
    doc_id, doc_user_id, filename, pdf_data, scan_limit, scan_count = result
    
    # Verify user owns this document
    if doc_user_id != user_id:
        conn.close()
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Check scan limit
    if scan_count >= scan_limit:
        conn.close()
        raise HTTPException(
            status_code=410, 
            detail=f"Scan limit exceeded ({scan_count}/{scan_limit})"
        )
    
    # Increment scan count
    cursor.execute(
        "UPDATE documents SET scan_count = scan_count + 1 WHERE id = ?",
        (doc_id,)
    )
    conn.commit()
    conn.close()
    
    # Return PDF file
    return Response(
        content=pdf_data,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "X-Scan-Count": str(scan_count + 1),
            "X-Scan-Limit": str(scan_limit)
        }
    )


@app.post("/verify-secure/{unique_id}")
async def verify_secure_and_get_pdf(
    unique_id: str,
    file: UploadFile = File(...),
    user_id: int = Depends(verify_token)
):
    """
    Verify QR authenticity first, then return PDF only if authentic.
    
    This endpoint combines authenticity verification with PDF retrieval.
    Only AUTHENTIC QR codes will grant access to the PDF.
    
    Args:
        unique_id: Unique document identifier
        file: Scanned QR code image
        user_id: Authenticated user ID (from token)
        
    Returns:
        JSON with verification results and PDF data if authentic
    """
    # Get document and security metadata from database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute(
        """SELECT id, user_id, filename, pdf_data, scan_limit, scan_count,
                  ghost_pattern, frequency_signature, fingerprint_hash, security_version
           FROM documents WHERE unique_id = ?""",
        (unique_id,)
    )
    result = cursor.fetchone()
    
    if not result:
        conn.close()
        raise HTTPException(status_code=404, detail="Document not found")
    
    (doc_id, doc_user_id, filename, pdf_data, scan_limit, scan_count,
     ghost_pattern_json, freq_sig_json, fingerprint_hash, security_version) = result
    
    # Verify user owns this document
    if doc_user_id != user_id:
        conn.close()
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Check scan limit
    if scan_count >= scan_limit:
        conn.close()
        raise HTTPException(
            status_code=410,
            detail=f"Scan limit exceeded ({scan_count}/{scan_limit})"
        )
    
    # Parse security metadata
    security_metadata = {
        'ghost_pattern': json.loads(ghost_pattern_json) if ghost_pattern_json else {},
        'watermark_signature': json.loads(freq_sig_json) if freq_sig_json else [],
        'fingerprint_hash': fingerprint_hash or '',
        'security_version': security_version or 1
    }
    
    # Read uploaded QR image
    image_bytes = await file.read()
    
    # Verify authenticity
    from PIL import Image
    from io import BytesIO
    import numpy as np
    from counterfeit_detector import CounterfeitDetector
    
    img = Image.open(BytesIO(image_bytes))
    img_array = np.array(img.convert('RGB'))
    
    detector = CounterfeitDetector()
    verification_result = detector.verify_qr_authenticity(img_array, security_metadata)
    
    # Only allow access if AUTHENTIC
    if verification_result['verdict'] != 'AUTHENTIC':
        conn.close()
        return {
            'success': False,
            'verdict': verification_result['verdict'],
            'authenticity_score': verification_result['authenticity_score'],
            'details': verification_result['details'],
            'warnings': verification_result['warnings'],
            'message': f"Access denied: QR code is {verification_result['verdict']}. Authenticity score: {verification_result['authenticity_score']}%"
        }
    
    # Increment scan count only if authentic
    cursor.execute(
        "UPDATE documents SET scan_count = scan_count + 1 WHERE id = ?",
        (doc_id,)
    )
    conn.commit()
    conn.close()
    
    # Return success with PDF data
    pdf_base64 = base64.b64encode(pdf_data).decode('utf-8')
    
    return {
        'success': True,
        'verdict': verification_result['verdict'],
        'authenticity_score': verification_result['authenticity_score'],
        'details': verification_result['details'],
        'warnings': verification_result['warnings'],
        'pdf_data': pdf_base64,
        'filename': filename,
        'scan_count': scan_count + 1,
        'scan_limit': scan_limit,
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    }


@app.post("/verify-authenticity/{unique_id}")
async def verify_qr_authenticity(
    unique_id: str,
    file: UploadFile = File(...),
    user_id: int = Depends(verify_token)
):
    """
    Verify the authenticity of a scanned QR code.
    
    This endpoint analyzes a scanned QR code image to detect counterfeits,
    screenshots, or physical copies using multi-layer security analysis.
    
    Args:
        unique_id: Unique document identifier
        file: Scanned QR code image file
        user_id: Authenticated user ID (from token)
        
    Returns:
        Detailed authenticity report with verdict and scores
    """
    # Validate file type
    allowed_extensions = ['.png', '.jpg', '.jpeg', '.bmp', '.webp']
    if not any(file.filename.lower().endswith(ext) for ext in allowed_extensions):
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid file type. Allowed: {', '.join(allowed_extensions)}"
        )
    
    # Get document and security metadata from database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute(
        """SELECT user_id, ghost_pattern, frequency_signature, fingerprint_hash, security_version
           FROM documents WHERE unique_id = ?""",
        (unique_id,)
    )
    result = cursor.fetchone()
    conn.close()
    
    if not result:
        raise HTTPException(status_code=404, detail="Document not found")
    
    doc_user_id, ghost_pattern_json, freq_sig_json, fingerprint_hash, security_version = result
    
    # Verify user owns this document
    if doc_user_id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Parse security metadata
    security_metadata = {
        'ghost_pattern': json.loads(ghost_pattern_json) if ghost_pattern_json else {},
        'watermark_signature': json.loads(freq_sig_json) if freq_sig_json else [],
        'fingerprint_hash': fingerprint_hash or '',
        'security_version': security_version or 1
    }
    
    # Read uploaded image
    image_bytes = await file.read()
    
    # Verify authenticity
    from PIL import Image
    from io import BytesIO
    import numpy as np
    
    img = Image.open(BytesIO(image_bytes))
    img_array = np.array(img.convert('RGB'))
    
    from counterfeit_detector import CounterfeitDetector
    detector = CounterfeitDetector()
    verification_result = detector.verify_qr_authenticity(img_array, security_metadata)
    
    # Add timestamp
    verification_result['timestamp'] = datetime.utcnow().isoformat() + 'Z'
    verification_result['unique_id'] = unique_id
    
    return verification_result


@app.get("/")
async def root():
    """Redirect to the frontend application."""
    return RedirectResponse(url="/static/index.html")

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM users")
    user_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM documents")
    doc_count = cursor.fetchone()[0]
    
    conn.close()
    
    return {
        "status": "healthy",
        "users": user_count,
        "documents": doc_count
    }
