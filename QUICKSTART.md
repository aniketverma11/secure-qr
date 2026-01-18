# 🚀 Quick Start Guide

## System Overview

This is a **Secure PDF QR System** with:
- ✅ User authentication (email/password)
- ✅ PDF upload with unique QR codes
- ✅ Scan limit enforcement
- ✅ SQLite database storage
- ✅ Token-based API access

---

## Quick Start (3 Steps)

### 1. Start the Server
```bash
cd /home/aniket/aniket/secury-poc
source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Server will be available at: **http://127.0.0.1:8000**

### 2. Test with Python Script
```bash
# In a new terminal
cd /home/aniket/aniket/secury-poc
source venv/bin/activate
python test_workflow.py
```

### 3. View API Documentation
Open in browser: **http://127.0.0.1:8000/docs**

---

## API Workflow

### Step 1: Register & Login
```bash
# Register
curl -X POST "http://127.0.0.1:8000/register" \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "yourpassword"}'

# Login (get token)
curl -X POST "http://127.0.0.1:8000/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "yourpassword"}'
```

Response:
```json
{
  "access_token": "your-token-here",
  "token_type": "bearer"
}
```

### Step 2: Upload PDF
```bash
curl -X POST "http://127.0.0.1:8000/upload-pdf" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@document.pdf" \
  -F "scan_limit=5"
```

Response:
```json
{
  "unique_id": "abc123xyz",
  "filename": "document.pdf",
  "scan_limit": 5,
  "scan_count": 0,
  "qr_url": "http://127.0.0.1:8000/qr/abc123xyz"
}
```

### Step 3: Get QR Code
```bash
# Download QR code image
curl "http://127.0.0.1:8000/qr/abc123xyz" --output qr.png
```

### Step 4: Verify & Download PDF
```bash
curl -X GET "http://127.0.0.1:8000/verify/abc123xyz" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  --output downloaded.pdf
```

**Note:** This can only be done `scan_limit` times!

---

## Key Features

### 🔐 Authentication
- Email/password registration
- Bearer token authentication
- 24-hour token expiration

### 📄 PDF Management
- Upload PDFs via API
- Unique ID generation
- Binary storage in SQLite

### 🎫 QR Code Generation
- Automatic QR creation on upload
- Embedded verify URL
- PNG format output

### 🔢 Scan Limits
- Configurable per document
- Automatic count increment
- Hard limit enforcement

---

## Database Schema

**users**
- id, email, password_hash, created_at

**tokens**
- id, user_id, token, expires_at, created_at

**documents**
- id, unique_id, user_id, filename, pdf_data, scan_limit, scan_count, created_at

---

## Testing

### Automated Test (Python)
```bash
python test_workflow.py
```

This will:
1. Register a user
2. Login and get token
3. Upload a test PDF
4. Download QR code
5. Verify 6 times (5 succeed, 1 fails)
6. Show health status

### Manual Test (cURL)
```bash
./test_workflow.sh
```

---

## API Endpoints

| Method | Endpoint | Auth Required | Description |
|--------|----------|---------------|-------------|
| POST | `/register` | No | Register new user |
| POST | `/login` | No | Login and get token |
| POST | `/upload-pdf` | Yes | Upload PDF and generate QR |
| GET | `/qr/{unique_id}` | No | Get QR code image |
| GET | `/verify/{unique_id}` | Yes | Verify and download PDF |
| GET | `/health` | No | System health check |

---

## Files

- `main.py` - FastAPI application
- `qr_utils.py` - QR code generation
- `requirements.txt` - Python dependencies
- `test_workflow.py` - Python test script
- `test_workflow.sh` - Bash test script
- `secure_qr.db` - SQLite database (auto-created)
- `qr_codes/` - Generated QR images (auto-created)

---

## Production Deployment

Before deploying to production:

1. **Security**
   - Use bcrypt for password hashing (not SHA-256)
   - Add HTTPS/SSL certificates
   - Implement rate limiting
   - Add CORS restrictions

2. **Database**
   - Migrate to PostgreSQL
   - Add database migrations
   - Implement backups

3. **Configuration**
   - Set `BASE_URL` in `.env`
   - Use secure secret keys
   - Configure token expiration

4. **Monitoring**
   - Add logging
   - Set up error tracking
   - Monitor scan patterns

---

## Troubleshooting

### Server won't start
```bash
# Check if port 8000 is in use
lsof -i :8000

# Kill existing process
kill -9 <PID>
```

### Database locked
```bash
# Remove database and restart
rm secure_qr.db
# Database will be recreated on next start
```

### Token expired
```bash
# Login again to get new token
curl -X POST "http://127.0.0.1:8000/login" ...
```

---

## Support

- **API Docs**: http://127.0.0.1:8000/docs
- **Health Check**: http://127.0.0.1:8000/health
- **README**: See README.md for detailed documentation
