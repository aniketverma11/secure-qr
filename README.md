# 🔒 Secure PDF QR System

A FastAPI-based system for secure PDF document management with QR code access control and scan limits.

## ✨ Features

- 🔐 **User Authentication** - Email/password login with JWT tokens
- 📄 **PDF Upload** - Upload PDFs and generate unique QR codes
- 🎫 **Scan Limits** - Control how many times a QR can be scanned
- 🔍 **Verification** - Secure PDF access with token validation
- 💾 **SQLite Database** - Lightweight, file-based storage

---

## 🚀 Quick Start

### 1. Install Dependencies
```bash
cd /home/aniket/aniket/secury-poc
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Start Server
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. Register & Login
```bash
# Register
curl -X POST "http://127.0.0.1:8000/register" \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "yourpassword"}'

# Login
curl -X POST "http://127.0.0.1:8000/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "yourpassword"}'
```

### 4. Upload PDF & Generate QR
```bash
curl -X POST "http://127.0.0.1:8000/upload-pdf" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -F "file=@document.pdf" \
  -F "scan_limit=5"
```

### 5. Verify & Download PDF
```bash
curl -X GET "http://127.0.0.1:8000/verify/UNIQUE_ID" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  --output downloaded.pdf
```

---

## 📋 API Endpoints

### POST /register
Register a new user account.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "yourpassword"
}
```

**Response:**
```json
{
  "message": "User registered successfully",
  "email": "user@example.com"
}
```

---

### POST /login
Login and receive access token.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "yourpassword"
}
```

**Response:**
```json
{
  "access_token": "your-token-here",
  "token_type": "bearer"
}
```

---

### POST /upload-pdf
Upload PDF and generate QR code (requires authentication).

**Headers:**
```
Authorization: Bearer YOUR_ACCESS_TOKEN
```

**Form Data:**
- `file`: PDF file
- `scan_limit`: Maximum number of scans (integer)

**Response:**
```json
{
  "unique_id": "abc123xyz",
  "filename": "document.pdf",
  "scan_limit": 5,
  "scan_count": 0,
  "qr_url": "http://127.0.0.1:8000/qr/abc123xyz"
}
```

---

### GET /qr/{unique_id}
Get QR code image for a document.

**Response:** PNG image

---

### GET /verify/{unique_id}
Verify QR and download PDF (requires authentication).

**Headers:**
```
Authorization: Bearer YOUR_ACCESS_TOKEN
```

**Response:** PDF file (if scan limit not exceeded)

**Headers in Response:**
- `X-Scan-Count`: Current scan count
- `X-Scan-Limit`: Maximum scan limit

---

## 🔄 How It Works

```
┌──────────────┐
│ 1. Register  │  POST /register
│   & Login    │  POST /login → Get access token
└──────┬───────┘
       │
       ▼
┌──────────────────────────────────────┐
│ 2. Upload PDF                        │
│ POST /upload-pdf                     │
│ - Save PDF to SQLite                 │
│ - Generate unique ID                 │
│ - Create QR code with verify URL     │
│ - Set scan limit                     │
└──────┬───────────────────────────────┘
       │
       ▼
┌──────────────┐
│ 3. User      │  Scans QR code
│ Scans QR     │  → Goes to /verify/{unique_id}
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ 4. System    │  ✓ Validates access token
│ Verifies     │  ✓ Checks scan limit
│              │  ✓ Increments scan count
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ 5. Returns   │  → User gets PDF file
│ PDF          │  (if limit not exceeded)
└──────────────┘
```

---

## 🗄️ Database Schema

### users
- `id` - Primary key
- `email` - Unique email address
- `password_hash` - SHA-256 hashed password
- `created_at` - Registration timestamp

### tokens
- `id` - Primary key
- `user_id` - Foreign key to users
- `token` - Access token
- `expires_at` - Token expiration time
- `created_at` - Creation timestamp

### documents
- `id` - Primary key
- `unique_id` - Unique identifier for QR code
- `user_id` - Foreign key to users
- `filename` - Original PDF filename
- `pdf_data` - Binary PDF data
- `scan_limit` - Maximum allowed scans
- `scan_count` - Current scan count
- `created_at` - Upload timestamp

---

## 🛠️ Tech Stack

- **FastAPI** - Web framework
- **SQLite** - Database
- **qrcode** - QR code generation
- **Pydantic** - Data validation
- **HTTPBearer** - Token authentication

---

## 🎯 Use Cases

- **Event Tickets** - Limited-use PDF tickets
- **Document Sharing** - Controlled access to sensitive PDFs
- **Certificates** - Verify authenticity with scan limits
- **Coupons** - One-time or limited-use vouchers
- **Access Passes** - Temporary document access

---

## 🔧 Configuration

### Change Base URL (for production)

Edit `.env`:
```
BASE_URL=https://your-domain.com
```

---

## 🚀 Production Checklist

- [ ] Update `BASE_URL` in `.env`
- [ ] Use secure password hashing (bcrypt instead of SHA-256)
- [ ] Add HTTPS/SSL certificates
- [ ] Implement rate limiting
- [ ] Add logging and monitoring
- [ ] Configure CORS properly
- [ ] Use PostgreSQL instead of SQLite
- [ ] Add password strength validation
- [ ] Implement refresh tokens
- [ ] Add email verification

---

## 📝 Example Workflow

```bash
# 1. Register
curl -X POST "http://127.0.0.1:8000/register" \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "test123"}'

# 2. Login
TOKEN=$(curl -X POST "http://127.0.0.1:8000/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "test123"}' \
  | jq -r '.access_token')

# 3. Upload PDF with 3 scan limit
curl -X POST "http://127.0.0.1:8000/upload-pdf" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@mydoc.pdf" \
  -F "scan_limit=3"

# 4. Verify and download (can do this 3 times)
curl -X GET "http://127.0.0.1:8000/verify/UNIQUE_ID" \
  -H "Authorization: Bearer $TOKEN" \
  --output downloaded.pdf
```

---

## 📄 License

MIT License - Feel free to use in your projects!

---

**Server URL:** http://127.0.0.1:8000  
**API Docs:** http://127.0.0.1:8000/docs  
**Health Check:** http://127.0.0.1:8000/health
