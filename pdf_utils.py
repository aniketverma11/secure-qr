
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
    # CRITICAL: Do NOT resize the PIL image itself (e.g. img.resize()).
    # Resizing destroys the pixel-perfect steganography (ghost dots, watermarks).
    # Instead, we serve the original full-resolution image to ReportLab and tell 
    # ReportLab to display it at a smaller size (scaling).
    qr_image = Image.open(io.BytesIO(qr_image_bytes))
    
    # Create the overlay PDF in memory
    packet = io.BytesIO()
    c = canvas.Canvas(packet, pagesize=(page_width, page_height))
    
    # QR Code Settings
    qr_display_size = 100  # 100 points (approx 1.4 inches)
    margin = 20
    
    # Position: Bottom Right
    # (0,0) is bottom-left
    x = page_width - qr_display_size - margin
    y = margin # Bottom margin
    
    # Draw QR code
    # We pass the original full-res image. ReportLab scales it to fit (width, height)
    # This preserves the underlying pixel data in the PDF object.
    c.drawImage(ImageReader(qr_image), x, y, width=qr_display_size, height=qr_display_size, mask='auto', preserveAspectRatio=True)
    
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
    Extract QR code from PDF.
    
    Strategy:
    1. Try to extract raw embedded images directly (preserves steganography).
    2. Fallback to rendering page as image (for scanned PDFs).
    
    Args:
        pdf_bytes: PDF file bytes
        
    Returns:
        Tuple (cropped_qr_numpy_array, decoded_text) or (None, None) if not found
    """
    detector = cv2.QRCodeDetector()
    
    # Strategy 1: Direct Image Extraction (Best for digital verification)
    try:
        reader = PdfReader(io.BytesIO(pdf_bytes))
        for page in reader.pages:
            if '/XObject' in page['/Resources']:
                xObject = page['/Resources']['/XObject'].get_object()
                for obj in xObject:
                    if xObject[obj]['/Subtype'] == '/Image':
                        try:
                            # Extract raw image bytes
                            img_obj = xObject[obj]
                            data = img_obj.get_data()
                            
                            # Convert to PIL Image
                            # Note: handle different filters/color spaces if needed
                            # pypdf's get_data() usually handles simple cases well
                            
                            # We'll rely on PIL to open the raw data if possible,
                            # or reconstruct from bytes if it's raw pixel data.
                            # pypdf images can be complex. simpler to use PIL on extracted bytes if robust.
                            # Let's try simple PIL open first.
                            try:
                                pil_image = Image.open(io.BytesIO(data))
                            except:
                                # Sometimes data is raw pixels, not a file format.
                                # pypdf helper might be needed.
                                continue
                                
                            # Convert to numpy/opencv
                            cv_image = np.array(pil_image.convert('RGB'))
                            cv_image = cv_image[:, :, ::-1].copy() # RGB to BGR
                            
                            # Detect
                            decoded_text, points, straight_qrcode = detector.detectAndDecode(cv_image)
                            
                            if decoded_text:
                                # For direct extraction, verify the ORIGINAL image, not the crop
                                # straight_qrcode is a re-sampled crop.
                                # The verification logic prefers the original input if it's a pure QR code image.
                                # If the extracted image contains JUST the QR code (which it should for our stamped PDFs),
                                # we should return the whole image to preserve steganography.
                                
                                # Convert back to RGB
                                rgb_result = cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB)
                                return rgb_result, decoded_text
                                
                        except Exception as e:
                            print(f"Failed to process embedded image: {e}")
                            continue
    except Exception as e:
        print(f"Direct extraction failed: {e}")

    # Strategy 2: Render Page (Fallback)
    try:
        # Higher DPI for better quality
        images = convert_from_bytes(pdf_bytes, dpi=300)
    except Exception as e:
        print(f"Error converting PDF to images: {e}")
        return None, None
        
    for i, pil_image in enumerate(images):
        cv_image = np.array(pil_image)
        cv_image = cv_image[:, :, ::-1].copy()
        
        decoded_text, points, straight_qrcode = detector.detectAndDecode(cv_image)
        
        if decoded_text:
            if straight_qrcode is not None:
                if len(straight_qrcode.shape) == 2:
                    straight_qrcode = cv2.cvtColor(straight_qrcode, cv2.COLOR_GRAY2RGB)
                elif straight_qrcode.shape[2] == 4:
                    straight_qrcode = cv2.cvtColor(straight_qrcode, cv2.COLOR_BGRA2RGB)
                else:
                    straight_qrcode = cv2.cvtColor(straight_qrcode, cv2.COLOR_BGR2RGB)
                    
                return straight_qrcode, decoded_text
            
    return None, None
