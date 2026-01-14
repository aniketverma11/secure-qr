# 🔒 Secure QR Code Validation System

A FastAPI-based system that creates **one-time use QR codes** that validate through your server before redirecting to the target URL.

## ✨ Key Feature

**You only provide the target URL** - the system automatically wraps it in a validation layer:

```bash
# You provide:
"https://google.com"

# QR code contains:
"http://your-system.com/decrypt/abc-123"

# User scans → validates → redirects to Google
```

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

### 3. Create Your First QR Code
```bash
curl -X POST "http://127.0.0.1:8000/create-qr" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://google.com"}' \
  --output my_qr.png
```

### 4. Scan the QR Code
- **First scan**: ✅ Redirects to Google
- **Second scan**: ❌ "QR code expired"

---

## 🔄 How It Works

```
┌──────────────┐
│ You Create   │  POST {"url": "https://google.com"}
│   QR Code    │
└──────┬───────┘
       │
       ▼
┌──────────────────────────────────────┐
│ System Generates QR                  │
│ Contains: your-system/decrypt/abc123 │
│ (NOT the final URL!)                 │
└──────┬───────────────────────────────┘
       │
       ▼
┌──────────────┐
│ User Scans   │  → Goes to your system first
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ System       │  ✓ Validates first scan
│ Validates    │  ✓ Marks as used
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ Redirects    │  → User arrives at https://google.com
└──────────────┘
```

---

## 📋 Features

✅ **One-time use** - Expires after first scan  
✅ **Server validation** - All scans go through your system  
✅ **AES-256 encryption** - Optional metadata encryption  
✅ **Simple API** - Just provide the target URL  
✅ **Fast** - In-memory storage, no database needed  
✅ **Secure** - Unique IDs, immediate expiry  

---

## 📚 API Endpoints

### POST /create-qr
Create a secure QR code

**Request:**
```json
{
  "url": "https://your-target-url.com",
  "data": {  // Optional metadata
    "key": "value"
  }
}
```

**Response:** PNG image of QR code

---

### GET /decrypt/{qr_id}
Validation endpoint (embedded in QR code)

- **First access**: Redirects to target URL
- **Subsequent access**: HTTP 410 "QR code expired"

---

## 📖 Documentation

- **[USAGE.md](USAGE.md)** - Detailed usage guide with examples
- **[API Reference](http://127.0.0.1:8000/docs)** - Interactive API docs (when server is running)

---

## 🛠️ Tech Stack

- **FastAPI** - Web framework
- **qrcode** - QR code generation
- **cryptography** - AES-256 encryption
- **Pydantic** - Data validation

---

## 📁 Project Structure

```
secury-poc/
├── main.py           # FastAPI app with endpoints
├── qr_utils.py       # QR code generation
├── crypto_utils.py   # AES encryption
├── requirements.txt  # Dependencies
├── README.md         # This file
└── USAGE.md          # Detailed usage guide
```

---

## 🔧 Configuration

### Change Base URL (for production)

Edit `qr_utils.py`:
```python
def generate_qr_code(qr_id: str, base_url: str = "https://your-domain.com"):
    # ...
```

---

## 🎯 Use Cases

- **Event tickets** - One-time entry validation
- **Secure links** - Prevent link sharing
- **Product authentication** - Verify genuine products
- **Access tokens** - Single-use access codes
- **Download links** - One-time file downloads

---

## 🚀 Production Checklist

- [ ] Update `base_url` in `qr_utils.py`
- [ ] Replace in-memory storage with Redis/PostgreSQL
- [ ] Add authentication to `/create-qr` endpoint
- [ ] Enable HTTPS with SSL certificates
- [ ] Add rate limiting
- [ ] Set up logging and monitoring
- [ ] Configure CORS if needed

---

## 📝 Example Usage

### Event Ticket
```bash
curl -X POST "http://127.0.0.1:8000/create-qr" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://event.com/ticket-validated",
    "data": {
      "ticket_id": "T12345",
      "event": "Concert 2026"
    }
  }' \
  --output ticket.png
```

### Secure Link
```bash
curl -X POST "http://127.0.0.1:8000/create-qr" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://secure-portal.com/dashboard"
  }' \
  --output secure_link.png
```

---

## 🔍 Health Check

```bash
curl http://127.0.0.1:8000/health
```

Response:
```json
{
  "status": "healthy",
  "active_qr_codes": 10,
  "expired_qr_codes": 5
}
```

---

## 📄 License

MIT License - Feel free to use in your projects!

---

## 🤝 Contributing

Contributions welcome! Please feel free to submit a Pull Request.

---

**Server URL:** http://127.0.0.1:8000  
**API Docs:** http://127.0.0.1:8000/docs  
**Health Check:** http://127.0.0.1:8000/health
