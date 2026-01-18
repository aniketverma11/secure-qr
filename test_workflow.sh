#!/bin/bash

# Test script for Secure PDF QR System

BASE_URL="http://127.0.0.1:8000"
EMAIL="test@example.com"
PASSWORD="test123"

echo "🔒 Secure PDF QR System - Test Script"
echo "======================================"
echo ""

# 1. Register
echo "1️⃣  Registering user..."
curl -s -X POST "$BASE_URL/register" \
  -H "Content-Type: application/json" \
  -d "{\"email\": \"$EMAIL\", \"password\": \"$PASSWORD\"}" | jq .
echo ""

# 2. Login
echo "2️⃣  Logging in..."
LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\": \"$EMAIL\", \"password\": \"$PASSWORD\"}")

TOKEN=$(echo $LOGIN_RESPONSE | jq -r '.access_token')
echo "Access Token: $TOKEN"
echo ""

# 3. Create a test PDF
echo "3️⃣  Creating test PDF..."
echo "This is a test PDF document" > test_document.txt
# Convert to PDF (simple text file for demo)
cat > test.pdf << 'EOF'
%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj
3 0 obj
<<
/Type /Page
/Parent 2 0 R
/Resources <<
/Font <<
/F1 <<
/Type /Font
/Subtype /Type1
/BaseFont /Helvetica
>>
>>
>>
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj
4 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
100 700 Td
(Test PDF Document) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000317 00000 n 
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
410
%%EOF
EOF
echo "Test PDF created: test.pdf"
echo ""

# 4. Upload PDF
echo "4️⃣  Uploading PDF with scan limit of 3..."
UPLOAD_RESPONSE=$(curl -s -X POST "$BASE_URL/upload-pdf" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@test.pdf" \
  -F "scan_limit=3")

echo $UPLOAD_RESPONSE | jq .
UNIQUE_ID=$(echo $UPLOAD_RESPONSE | jq -r '.unique_id')
echo ""
echo "Unique ID: $UNIQUE_ID"
echo ""

# 5. Download QR Code
echo "5️⃣  Downloading QR code..."
curl -s "$BASE_URL/qr/$UNIQUE_ID" --output "qr_$UNIQUE_ID.png"
echo "QR code saved: qr_$UNIQUE_ID.png"
echo ""

# 6. Verify and download PDF (1st time)
echo "6️⃣  Verifying QR code (1st scan)..."
curl -s -X GET "$BASE_URL/verify/$UNIQUE_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -D - --output "downloaded_1.pdf" 2>&1 | grep -E "(HTTP|X-Scan)"
echo "PDF downloaded: downloaded_1.pdf"
echo ""

# 7. Verify and download PDF (2nd time)
echo "7️⃣  Verifying QR code (2nd scan)..."
curl -s -X GET "$BASE_URL/verify/$UNIQUE_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -D - --output "downloaded_2.pdf" 2>&1 | grep -E "(HTTP|X-Scan)"
echo "PDF downloaded: downloaded_2.pdf"
echo ""

# 8. Verify and download PDF (3rd time)
echo "8️⃣  Verifying QR code (3rd scan)..."
curl -s -X GET "$BASE_URL/verify/$UNIQUE_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -D - --output "downloaded_3.pdf" 2>&1 | grep -E "(HTTP|X-Scan)"
echo "PDF downloaded: downloaded_3.pdf"
echo ""

# 9. Try 4th time (should fail)
echo "9️⃣  Verifying QR code (4th scan - should FAIL)..."
curl -s -X GET "$BASE_URL/verify/$UNIQUE_ID" \
  -H "Authorization: Bearer $TOKEN" | jq .
echo ""

# 10. Health check
echo "🏥 Health Check..."
curl -s "$BASE_URL/health" | jq .
echo ""

echo "✅ Test completed!"
echo ""
echo "Generated files:"
echo "  - test.pdf (original)"
echo "  - qr_$UNIQUE_ID.png (QR code)"
echo "  - downloaded_1.pdf, downloaded_2.pdf, downloaded_3.pdf (verified downloads)"
