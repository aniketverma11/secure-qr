import uuid
import httpx
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import Response, JSONResponse, RedirectResponse, StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Dict, Any, Optional
from crypto_utils import encrypt_data, decrypt_data
from qr_utils import generate_qr_code

app = FastAPI(title="One-Time QR Code API")

# Enable CORS for the HTML page
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files (HTML page)
app.mount("/static", StaticFiles(directory="static"), name="static")

# In-memory storage for QR codes
qr_storage: Dict[str, Dict[str, Any]] = {}

class QRCreateRequest(BaseModel):
    """Request model for creating a secure QR code."""
    url: str  # Target URL to redirect to after validation
    data: Optional[Dict[str, Any]] = None  # Optional metadata to encrypt

@app.post("/create-qr")
async def create_secure_qr(request: QRCreateRequest):
    """
    Create a secure, one-time QR code that validates through your system.
    
    Flow:
    1. You provide the target URL (e.g., https://google.com)
    2. System generates QR with validation URL (e.g., http://your-system/decrypt/abc123)
    3. User scans QR → goes to your system first
    4. System validates it's the first scan
    5. System redirects to your target URL
    6. Second scan shows "expired" error
    
    Args:
        request: Contains target URL and optional metadata
    
    Returns:
        PNG image of QR code containing the system validation URL
    """
    try:
        # Generate unique ID for this QR code
        qr_id = str(uuid.uuid4())
        
        # Encrypt the metadata (if provided)
        encrypted_data = encrypt_data(request.data) if request.data else None
        
        # Store encrypted data with scan status and target URL
        qr_storage[qr_id] = {
            "encrypted_data": encrypted_data,
            "redirect_url": request.url,
            "scanned": False
        }
        
        # Generate QR code
        qr_image_bytes = generate_qr_code(qr_id)
        
        # Return QR code as PNG image
        return Response(
            content=qr_image_bytes,
            media_type="image/png",
            headers={
                "X-QR-ID": qr_id,
                "Content-Disposition": f"inline; filename=qr_{qr_id}.png"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Encryption failed: {str(e)}")

@app.get("/decrypt/{qr_id}")
async def decrypt_qr_data(qr_id: str):
    """
    Decrypt data for a given QR ID and redirect to the stored URL.
    Can only be accessed once - subsequent scans will show expired message.
    
    Args:
        qr_id: Unique identifier for the QR code
        
    Returns:
        Redirect to stored URL (first scan) or error message (subsequent scans)
        
    Raises:
        HTTPException: If QR code not found or already scanned
    """
    # Check if QR ID exists
    if qr_id not in qr_storage:
        raise HTTPException(status_code=404, detail="QR code not found")
    
    qr_data = qr_storage[qr_id]
    
    # Check if already scanned
    if qr_data["scanned"]:
        raise HTTPException(status_code=410, detail="QR code expired - already scanned")
    
    try:
        # Mark as scanned FIRST (expire the QR code immediately)
        qr_storage[qr_id]["scanned"] = True
        
        # Proxy the target URL content (user sees content but address bar shows system URL)
        if qr_data.get("redirect_url"):
            target_url = qr_data["redirect_url"]
            
            try:
                # Fetch content from target URL
                async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
                    response = await client.get(target_url)
                    
                    # Get content type from target response
                    content_type = response.headers.get("content-type", "text/html")
                    
                    # Return the content with original content type
                    # User sees the content but address bar shows: http://your-system/decrypt/{qr_id}
                    return Response(
                        content=response.content,
                        media_type=content_type,
                        headers={
                            "X-Proxied-From": target_url,
                            "X-QR-Validated": "true"
                        }
                    )
            except httpx.RequestError as e:
                raise HTTPException(
                    status_code=502, 
                    detail=f"Failed to fetch content from target URL: {str(e)}"
                )
        
        # If no redirect URL (shouldn't happen with new API), return data
        if qr_data.get("encrypted_data"):
            decrypted_data = decrypt_data(qr_data["encrypted_data"])
            return JSONResponse(
                content={
                    "status": "success",
                    "data": decrypted_data,
                    "message": "QR code has been marked as expired"
                }
            )
        
        # No URL and no data - invalid QR
        raise HTTPException(status_code=400, detail="Invalid QR code configuration")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")

@app.get("/")
async def root():
    """Redirect to the HTML QR generator page."""
    return RedirectResponse(url="/static/index.html")

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "active_qr_codes": len(qr_storage),
        "expired_qr_codes": sum(1 for qr in qr_storage.values() if qr["scanned"])
    }
