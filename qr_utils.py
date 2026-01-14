import os
import qrcode
from io import BytesIO
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def generate_qr_code(qr_id: str, base_url: str = None) -> bytes:
    """Generate QR code containing the decrypt URL and return as PNG bytes."""
    # Use provided base_url, or get from environment, or fallback to localhost
    if base_url is None:
        base_url = os.getenv("BASE_URL", "http://127.0.0.1:8000")
    
    # Create the URL that will be embedded in QR code
    decrypt_url = f"{base_url}/decrypt/{qr_id}"
    
    # Create QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(decrypt_url)
    qr.make(fit=True)
    
    # Create image
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to bytes
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    
    return buffer.getvalue()
