# 🎨 Frontend User Guide

## 🌐 Access the Application

Open your browser and go to: **http://127.0.0.1:8000**

The application will automatically redirect you to the login page.

---

## 📱 Features Overview

### 1️⃣ **Authentication**
- **Register**: Create a new account with email and password
- **Login**: Access your account
- **Logout**: Securely sign out

### 2️⃣ **Upload PDF**
- Upload PDF documents
- Set scan limits (how many times QR can be scanned)
- Automatically generate QR codes
- Download QR code images

### 3️⃣ **Scan QR Code**
- **Camera Scanner**: Use your device camera to scan QR codes
- **Manual Entry**: Enter unique ID manually if camera not available
- Instant verification and PDF download

### 4️⃣ **My Documents**
- View all uploaded documents (coming soon)
- Track scan counts and limits

---

## 🚀 Quick Walkthrough

### Step 1: Register/Login

1. Open http://127.0.0.1:8000
2. Click "Register" tab
3. Enter your email and password
4. Click "Register" button
5. Switch to "Login" tab
6. Enter credentials and login

### Step 2: Upload a PDF

1. Click "📤 Upload PDF" tab
2. Click the upload area or drag & drop a PDF
3. Set the scan limit (e.g., 5)
4. Click "Upload & Generate QR"
5. Your QR code will be displayed
6. Click "Download QR Code" to save it

### Step 3: Scan QR Code

**Option A: Using Camera**
1. Click "📷 Scan QR" tab
2. Click "Start Scanner"
3. Allow camera access
4. Point camera at QR code
5. Automatic verification and download

**Option B: Manual Entry**
1. Click "📷 Scan QR" tab
2. Scroll to "Or enter Unique ID manually"
3. Paste the unique ID
4. Click "Verify"
5. Download the PDF

---

## 🎯 Key Features

### ✨ Modern UI
- Dark theme with gradient accents
- Smooth animations and transitions
- Fully responsive design
- Toast notifications for feedback

### 🔒 Security
- Token-based authentication
- Secure PDF storage
- Scan limit enforcement
- Automatic session management

### 📷 QR Scanner
- Real-time camera scanning
- Automatic QR detection
- Manual ID entry fallback
- Instant verification

### 📊 Smart Features
- File name display
- Scan count tracking
- Limit enforcement
- Download management

---

## 📱 Mobile Support

The application is fully responsive and works on:
- 📱 Mobile phones
- 💻 Tablets
- 🖥️ Desktop computers

### Mobile Tips:
- Use the camera scanner for best experience
- Ensure good lighting when scanning
- Hold steady for 2-3 seconds
- Allow camera permissions when prompted

---

## 🎨 UI Components

### Color Scheme
- **Primary**: Purple gradient (#667eea → #764ba2)
- **Background**: Dark slate (#0f172a)
- **Cards**: Slate (#1e293b)
- **Success**: Green (#4ade80)
- **Error**: Red (#f87171)

### Sections
1. **Header**: Logo, user info, logout
2. **Auth**: Login/Register forms
3. **Upload**: PDF upload and QR generation
4. **Scanner**: Camera scanner and manual entry
5. **Documents**: Document management (coming soon)

---

## 🔧 Troubleshooting

### Camera Not Working
- **Chrome/Edge**: Allow camera permissions
- **Firefox**: Check privacy settings
- **Safari**: Enable camera in site settings
- **Fallback**: Use manual ID entry

### Upload Failed
- Check file is PDF format
- Ensure file size is reasonable
- Verify you're logged in
- Check internet connection

### QR Scan Failed
- Ensure QR code is clear and visible
- Check lighting conditions
- Try manual ID entry
- Verify you're logged in

### Token Expired
- Simply login again
- Tokens expire after 24 hours
- Your data is safe

---

## 💡 Tips & Tricks

### Best Practices
1. **Strong Passwords**: Use secure passwords
2. **Scan Limits**: Set appropriate limits for your use case
3. **QR Storage**: Save QR codes securely
4. **Regular Cleanup**: Remove old documents periodically

### Use Cases
- **Event Tickets**: Set limit to 1 scan
- **Shared Documents**: Set limit to 5-10 scans
- **Team Access**: Higher limits for team documents
- **One-time Links**: Limit 1 for maximum security

---

## 🎬 Demo Workflow

```
1. Register → test@example.com / password123
2. Login → Get access token (automatic)
3. Upload → Select "document.pdf", Limit: 3
4. Generate → QR code created
5. Download → Save QR image
6. Scan → Use camera or manual ID
7. Verify → PDF downloaded (1/3 scans used)
8. Repeat → Scan 2 more times
9. Limit → 4th scan fails (limit exceeded)
```

---

## 🌟 Advanced Features

### Keyboard Shortcuts
- `Tab`: Navigate between fields
- `Enter`: Submit forms
- `Esc`: Close modals (future)

### Browser Support
- ✅ Chrome 90+
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ Edge 90+

### Performance
- Instant page loads
- Real-time scanning
- Smooth animations
- Optimized images

---

## 📞 Support

### Common Questions

**Q: How long do tokens last?**
A: 24 hours from login

**Q: Can I change scan limits?**
A: Not after creation (future feature)

**Q: What's the max file size?**
A: No hard limit, but keep PDFs reasonable

**Q: Can I delete documents?**
A: Coming soon in "My Documents"

**Q: Is my data secure?**
A: Yes, encrypted storage and token auth

---

## 🎉 Enjoy!

Your complete PDF QR system is ready to use!

**Quick Access:**
- 🏠 Home: http://127.0.0.1:8000
- 📖 API Docs: http://127.0.0.1:8000/docs
- 🏥 Health: http://127.0.0.1:8000/health
