
import io
from PIL import Image
from pdf_utils import stamp_pdf_with_qr

# Create a dummy PDF
from pypdf import PdfWriter
buffer = io.BytesIO()
writer = PdfWriter()
writer.add_blank_page(width=595, height=842)
writer.write(buffer)
pdf_bytes = buffer.getvalue()

# Create a dummy QR
qr_img = Image.new('RGB', (100, 100), color='black')
qr_buffer = io.BytesIO()
qr_img.save(qr_buffer, format='PNG')
qr_bytes = qr_buffer.getvalue()

try:
    result = stamp_pdf_with_qr(pdf_bytes, qr_bytes)
    print(f"Success! Output size: {len(result)} bytes")
except Exception as e:
    print(f"Error: {e}")
