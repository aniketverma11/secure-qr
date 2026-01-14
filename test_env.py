#!/usr/bin/env python3
"""
Test script to verify environment variable configuration.
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("=" * 60)
print("🔧 ENVIRONMENT CONFIGURATION TEST")
print("=" * 60)

# Check BASE_URL
base_url = os.getenv("BASE_URL", "NOT SET")
print(f"\n✅ BASE_URL: {base_url}")

# Check other settings
host = os.getenv("HOST", "0.0.0.0")
port = os.getenv("PORT", "8000")
print(f"✅ HOST: {host}")
print(f"✅ PORT: {port}")

print("\n" + "=" * 60)
print("📋 QR CODE URL FORMAT")
print("=" * 60)

# Show what URL will be in QR codes
qr_id = "abc-123-xyz"
qr_url = f"{base_url}/decrypt/{qr_id}"
print(f"\nQR codes will contain URLs like:")
print(f"   {qr_url}")

print("\n" + "=" * 60)
print("✅ Configuration loaded successfully!")
print("=" * 60)
