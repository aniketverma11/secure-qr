import qrcode
from io import BytesIO

def generate_qr_code(qr_id: str, base_url: str = "http://127.0.0.1:8000") -> bytes:
    """Generate QR code containing the decrypt URL and return as PNG bytes."""
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
