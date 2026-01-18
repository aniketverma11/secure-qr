"""
Test script for Secure PDF QR System
Demonstrates the complete workflow using Python requests
"""

import requests
import json
from io import BytesIO

BASE_URL = "http://127.0.0.1:8000"
EMAIL = "demo@example.com"
PASSWORD = "demo123"

def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

def main():
    print_section("🔒 Secure PDF QR System - Python Test")
    
    # 1. Register
    print_section("1️⃣  Registering User")
    try:
        response = requests.post(
            f"{BASE_URL}/register",
            json={"email": EMAIL, "password": PASSWORD}
        )
        print(f"Status: {response.status_code}")
        print(json.dumps(response.json(), indent=2))
    except Exception as e:
        print(f"Registration failed (user might already exist): {e}")
    
    # 2. Login
    print_section("2️⃣  Logging In")
    response = requests.post(
        f"{BASE_URL}/login",
        json={"email": EMAIL, "password": PASSWORD}
    )
    print(f"Status: {response.status_code}")
    login_data = response.json()
    print(json.dumps(login_data, indent=2))
    
    token = login_data["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # 3. Create a test PDF
    print_section("3️⃣  Creating Test PDF")
    pdf_content = b"""%PDF-1.4
1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj
2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj
3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]/Contents 4 0 R>>endobj
4 0 obj<</Length 44>>stream
BT /F1 12 Tf 100 700 Td (Secure PDF Test) Tj ET
endstream endobj
xref 0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000229 00000 n 
trailer<</Size 5/Root 1 0 R>>
startxref 322
%%EOF"""
    
    print("Test PDF created in memory")
    
    # 4. Upload PDF
    print_section("4️⃣  Uploading PDF with Scan Limit = 5")
    files = {"file": ("test_document.pdf", BytesIO(pdf_content), "application/pdf")}
    data = {"scan_limit": 5}
    
    response = requests.post(
        f"{BASE_URL}/upload-pdf",
        headers=headers,
        files=files,
        data=data
    )
    print(f"Status: {response.status_code}")
    upload_data = response.json()
    print(json.dumps(upload_data, indent=2))
    
    unique_id = upload_data["unique_id"]
    
    # 5. Download QR Code
    print_section("5️⃣  Downloading QR Code")
    response = requests.get(f"{BASE_URL}/qr/{unique_id}")
    qr_filename = f"qr_{unique_id}.png"
    with open(qr_filename, "wb") as f:
        f.write(response.content)
    print(f"QR code saved: {qr_filename}")
    print(f"QR URL: {BASE_URL}/verify/{unique_id}")
    
    # 6. Verify multiple times
    print_section("6️⃣  Testing Scan Limit (5 scans allowed)")
    
    for i in range(1, 7):  # Try 6 times (should fail on 6th)
        print(f"\n--- Scan #{i} ---")
        response = requests.get(
            f"{BASE_URL}/verify/{unique_id}",
            headers=headers
        )
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            print(f"✅ Success!")
            print(f"Scan Count: {response.headers.get('X-Scan-Count')}")
            print(f"Scan Limit: {response.headers.get('X-Scan-Limit')}")
            
            # Save PDF
            pdf_filename = f"downloaded_{i}.pdf"
            with open(pdf_filename, "wb") as f:
                f.write(response.content)
            print(f"PDF saved: {pdf_filename}")
        else:
            print(f"❌ Failed!")
            print(json.dumps(response.json(), indent=2))
    
    # 7. Health Check
    print_section("🏥 Health Check")
    response = requests.get(f"{BASE_URL}/health")
    print(json.dumps(response.json(), indent=2))
    
    print_section("✅ Test Completed!")
    print(f"Check the generated files:")
    print(f"  - {qr_filename}")
    print(f"  - downloaded_1.pdf through downloaded_5.pdf")

if __name__ == "__main__":
    main()
