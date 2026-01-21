
import io
import cv2
import numpy as np
from PIL import Image
from pypdf import PdfReader, PdfWriter, PageObject
import tempfile
import os
from pdf2image import convert_from_bytes
from typing import Optional, Tuple, List

def stamp_pdf_with_qr(pdf_bytes: bytes, qr_image_bytes: bytes) -> bytes:
    """
    Overlay the QR code onto the last page of the PDF using ReportLab.
    
    Args:
        pdf_bytes: Original PDF file bytes
        qr_image_bytes: QR code image bytes
        
    Returns:
        Modified PDF bytes with QR stamped on last page
    """
    from reportlab.pdfgen import canvas
    from reportlab.lib.utils import ImageReader
    
    # Read original PDF
    reader = PdfReader(io.BytesIO(pdf_bytes))
    writer = PdfWriter()
    
    if len(reader.pages) == 0:
        return pdf_bytes
        
    # Copy all pages
    for page in reader.pages:
        writer.add_page(page)
        
    # Get the last page
    last_page = writer.pages[-1]
    
    # Get page dimensions
    try:
        page_width = float(last_page.mediabox.width)
        page_height = float(last_page.mediabox.height)
    except:
        page_width, page_height = 595, 842
        
    # Prepare QR image
    qr_image = Image.open(io.BytesIO(qr_image_bytes))
    
    # Create the overlay PDF in memory
    packet = io.BytesIO()
    c = canvas.Canvas(packet, pagesize=(page_width, page_height))
    
    # QR Code Settings
    qr_size = 100  # 100 points (approx 1.4 inches)
    margin = 20
    
    # Position: Bottom Right
    # (0,0) is bottom-left
    x = page_width - qr_size - margin
    y = margin # Bottom margin
    
    # Draw QR code
    # reportlab ImageReader helps handle PIL images
    c.drawImage(ImageReader(qr_image), x, y, width=qr_size, height=qr_size, mask='auto')
    
    c.save()
    packet.seek(0)
    
    # Merge overlay
    overlay_reader = PdfReader(packet)
    overlay_page = overlay_reader.pages[0]
    
    last_page.merge_page(overlay_page)
    
    # Write output
    output_buffer = io.BytesIO()
    writer.write(output_buffer)
    output_buffer.getvalue()
    
    return output_buffer.getvalue()

def extract_qr_from_pdf(pdf_bytes: bytes) -> Tuple[Optional[np.ndarray], Optional[str]]:
    """
    Convert PDF pages to images and search for a QR code.
    
    Args:
        pdf_bytes: PDF file bytes
        
    Returns:
        Tuple (cropped_qr_numpy_array, decoded_text) or (None, None) if not found
    """
    try:
        # Convert PDF pages to images
        # We use a lower DPI for speed, e.g. 200
        images = convert_from_bytes(pdf_bytes, dpi=200)
    except Exception as e:
        print(f"Error converting PDF to images: {e}")
        return None, None
        
    detector = cv2.QRCodeDetector()
    
    for i, pil_image in enumerate(images):
        # Convert PIL to opencv (numpy)
        cv_image = np.array(pil_image)
        # Convert RGB to BGR
        cv_image = cv_image[:, :, ::-1].copy()
        
        # Detect and decode
        decoded_text, points, straight_qrcode = detector.detectAndDecode(cv_image)
        
        if decoded_text:
            # QR Found!
            # straight_qrcode is the rectified, cropped QR code
            if straight_qrcode is not None:
                # Convert back to RGB for consistency with our system
                # straight_qrcode comes out as grayscale or uint8 usually
                if len(straight_qrcode.shape) == 2:
                    straight_qrcode = cv2.cvtColor(straight_qrcode, cv2.COLOR_GRAY2RGB)
                elif straight_qrcode.shape[2] == 4:
                    straight_qrcode = cv2.cvtColor(straight_qrcode, cv2.COLOR_BGRA2RGB)
                else:
                    straight_qrcode = cv2.cvtColor(straight_qrcode, cv2.COLOR_BGR2RGB)
                    
                return straight_qrcode, decoded_text
                
        # Fallback: sometimes detectAndDecode fails to provide strict crop
        # We can try to manually crop using 'points' if points found
        if points is not None and not decoded_text:
            # Try to decode again with robust settings or other libs if needed?
            # For now, we return None if text not decoded
            pass
            
    return None, None
