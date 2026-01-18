import hashlib
import secrets
import sqlite3
from datetime import datetime, timedelta
from typing import Optional
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form
from fastapi.responses import Response, FileResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from qr_utils import generate_qr_code
import os

app = FastAPI(title="Secure PDF QR System")

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
    
    # Save to database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO documents (unique_id, user_id, filename, pdf_data, scan_limit)
           VALUES (?, ?, ?, ?, ?)""",
        (unique_id, user_id, file.filename, pdf_data, scan_limit)
    )
    conn.commit()
    conn.close()
    
    # Generate QR code
    qr_image_bytes = generate_qr_code(unique_id)
    
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
