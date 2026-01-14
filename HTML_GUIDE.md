# 🎨 HTML QR Generator - Quick Guide

## Access the Interface

Simply open your browser to:
```
http://127.0.0.1:8000/
```

You'll see a beautiful, modern form to generate QR codes!

---

## How to Use

### 1. Enter Target URL
Type the URL you want users to see content from:
```
https://example.com
```

### 2. Add Metadata (Optional)
Add JSON metadata to encrypt and store:
```json
{
  "ticket_id": "T12345",
  "event": "Concert 2026"
}
```

### 3. Click "Generate QR Code"
The system will:
- ✅ Create a unique QR code
- ✅ Display it on the page
- ✅ Enable download button

### 4. Download QR Code
Click the "Download QR Code" button to save the PNG image.

---

## Features

✅ **Modern Design** - Beautiful gradient interface  
✅ **Real-time Generation** - Instant QR code creation  
✅ **Download Support** - Save QR codes as PNG  
✅ **Error Handling** - Clear error messages  
✅ **Loading States** - Visual feedback during generation  
✅ **Responsive** - Works on mobile and desktop  

---

## What Happens When Scanned?

1. **User scans QR code**
2. **Browser opens**: `http://your-system/decrypt/{unique-id}`
3. **System validates**: Checks if first scan
4. **System proxies**: Fetches content from target URL
5. **User sees**: Content from target URL
6. **Address bar shows**: Your system URL (target URL HIDDEN!)
7. **Second scan**: Shows "QR code expired" error

---

## Example Use Cases

### Simple URL
```
Target URL: https://google.com
Metadata: (leave empty)
```
User sees Google but address bar shows your system URL.

### Event Ticket
```
Target URL: https://event-system.com/validated
Metadata: {"ticket_id": "T12345", "seat": "A12"}
```
User sees validation page, system logs ticket info.

### Secure Document
```
Target URL: https://files.example.com/report.pdf
Metadata: {"document": "Q4-Report", "user": "Alice"}
```
User sees PDF, system tracks who accessed it.

---

## Screenshots

### Form Interface
![QR Generator Form](file:///home/aniket/.gemini/antigravity/brain/3ee3755d-0f14-4f79-ad59-283e9afe4a2f/generated_qr_code_1768363019873.png)

Clean, modern interface with gradient background and clear input fields.

---

## Technical Details

### Files
- **static/index.html** - The HTML form
- **main.py** - Backend API with CORS and static file serving

### API Endpoint Used
```
POST http://127.0.0.1:8000/create-qr
Content-Type: application/json

{
  "url": "https://example.com",
  "data": { ... }  // optional
}
```

### Response
- PNG image of QR code
- Header: `X-QR-ID` with unique identifier

---

## Browser Compatibility

✅ Chrome / Edge  
✅ Firefox  
✅ Safari  
✅ Mobile browsers  

---

## Customization

### Change Colors
Edit `static/index.html` and modify the CSS:
```css
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
```

### Change API URL
For production, update the fetch URL in the JavaScript:
```javascript
const response = await fetch('https://your-domain.com/create-qr', {
  // ...
});
```

---

## Production Deployment

1. **Update CORS settings** in `main.py`:
```python
allow_origins=["https://your-domain.com"]
```

2. **Update API URL** in `static/index.html`:
```javascript
fetch('https://your-api-domain.com/create-qr', ...)
```

3. **Serve with HTTPS** using Nginx or Caddy

---

## Troubleshooting

### QR Code Not Generating?
- Check browser console for errors
- Verify server is running on port 8000
- Check CORS is enabled

### Invalid JSON Error?
- Metadata must be valid JSON
- Use double quotes for keys and strings
- Leave empty if no metadata needed

### Can't Download QR Code?
- Ensure browser allows downloads
- Check popup blocker settings

---

## Summary

You now have a **beautiful web interface** to generate secure QR codes without using command-line tools! 🎉

**Access it at**: http://127.0.0.1:8000/
