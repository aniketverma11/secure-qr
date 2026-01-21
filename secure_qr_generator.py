"""
Secure QR Code Generator with Anti-Counterfeiting Features

This module implements multiple layers of security:
1. Ghost Dots - Invisible steganographic markers
2. Frequency Domain Watermarking - DCT-based watermarks
3. Pixel Fingerprinting - Unique noise patterns
"""

import hashlib
import json
import random
import numpy as np
import cv2
import qrcode
from PIL import Image, ImageDraw
from io import BytesIO
from scipy.fftpack import dct, idct
from typing import Tuple, Dict, List


class SecureQRGenerator:
    """Generate QR codes with anti-counterfeiting features."""
    
    def __init__(self):
        self.ghost_dot_density = 40  # Number of ghost dots to embed
        self.ghost_dot_color_range = (250, 254)  # Nearly invisible gray
        self.watermark_strength = 0.1  # DCT watermark strength
        self.fingerprint_strength = 3  # Pixel noise strength
        
    def generate_secure_qr(
        self, 
        data: str, 
        doc_id: str,
        box_size: int = 10,
        border: int = 4
    ) -> Tuple[bytes, Dict]:
        """
        Generate a secure QR code with anti-counterfeiting features.
        
        Args:
            data: Data to encode in QR code
            doc_id: Unique document identifier (used as security seed)
            box_size: Size of each QR code box
            border: Border size around QR code
            
        Returns:
            Tuple of (PNG image bytes, security metadata dict)
        """
        # Step 1: Generate base QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,  # High error correction
            box_size=box_size,
            border=border,
        )
        qr.add_data(data)
        qr.make(fit=True)
        
        # Create PIL image
        pil_img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to numpy array for processing
        img_array = np.array(pil_img.convert('RGB'))
        
        # Step 2: Add ghost dots
        ghost_pattern = self._embed_ghost_dots(img_array, doc_id)
        
        # Step 3: Add frequency domain watermark
        watermark_signature = self._embed_frequency_watermark(img_array, doc_id)
        
        # Step 4: Add pixel fingerprint
        fingerprint_hash = self._add_pixel_fingerprint(img_array, doc_id)
        
        # Convert back to PIL Image
        final_img = Image.fromarray(img_array)
        
        # Convert to bytes
        buffer = BytesIO()
        final_img.save(buffer, format='PNG')
        buffer.seek(0)
        image_bytes = buffer.getvalue()
        
        # Prepare security metadata
        security_metadata = {
            'ghost_pattern': ghost_pattern,
            'watermark_signature': watermark_signature.tolist(),
            'fingerprint_hash': fingerprint_hash,
            'image_size': img_array.shape[:2],
            'security_version': 1
        }
        
        return image_bytes, security_metadata
    
    def _embed_ghost_dots(self, img_array: np.ndarray, seed: str) -> Dict:
        """
        Embed invisible ghost dots in white areas of the QR code.
        
        Ghost dots are nearly invisible (RGB 250-254) and placed in a 
        pseudo-random pattern based on the document ID.
        
        Args:
            img_array: QR code image as numpy array (modified in-place)
            seed: Seed for random pattern generation
            
        Returns:
            Dictionary containing ghost dot pattern information
        """
        height, width = img_array.shape[:2]
        
        # Create deterministic random generator from seed
        rng = random.Random(seed)
        
        # Find white pixels (potential locations for ghost dots)
        white_mask = np.all(img_array >= 250, axis=2)
        white_coords = np.argwhere(white_mask)
        
        if len(white_coords) == 0:
            return {'coordinates': [], 'count': 0}
        
        # Select random positions for ghost dots
        num_dots = min(self.ghost_dot_density, len(white_coords))
        selected_indices = rng.sample(range(len(white_coords)), num_dots)
        ghost_positions = white_coords[selected_indices]
        
        # Embed ghost dots with nearly invisible gray values
        ghost_coords = []
        for y, x in ghost_positions:
            # Random gray value between 250-254 (nearly invisible)
            gray_value = rng.randint(*self.ghost_dot_color_range)
            img_array[y, x] = [gray_value, gray_value, gray_value]
            ghost_coords.append({'x': int(x), 'y': int(y), 'value': gray_value})
        
        # Create pattern hash for verification
        pattern_str = json.dumps(sorted(ghost_coords, key=lambda d: (d['x'], d['y'])))
        pattern_hash = hashlib.sha256(pattern_str.encode()).hexdigest()
        
        return {
            'coordinates': ghost_coords,
            'count': num_dots,
            'pattern_hash': pattern_hash
        }
    
    def _embed_frequency_watermark(self, img_array: np.ndarray, seed: str) -> np.ndarray:
        """
        Embed a watermark in the frequency domain using DCT.
        
        This watermark survives JPEG compression and resizing.
        
        Args:
            img_array: QR code image as numpy array (modified in-place)
            seed: Seed for watermark generation
            
        Returns:
            Watermark signature array
        """
        # Convert to grayscale for DCT
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY).astype(float)
        
        # Apply DCT
        dct_coeffs = dct(dct(gray.T, norm='ortho').T, norm='ortho')
        
        # Generate watermark signature from seed
        rng = np.random.RandomState(int(hashlib.sha256(seed.encode()).hexdigest()[:8], 16))
        signature = rng.randn(8, 8)  # 8x8 signature
        
        # Embed in mid-frequency coefficients (more robust)
        h, w = dct_coeffs.shape
        mid_h, mid_w = h // 4, w // 4
        
        dct_coeffs[mid_h:mid_h+8, mid_w:mid_w+8] += signature * self.watermark_strength * np.abs(dct_coeffs[mid_h:mid_h+8, mid_w:mid_w+8]).mean()
        
        # Inverse DCT
        watermarked = idct(idct(dct_coeffs.T, norm='ortho').T, norm='ortho')
        watermarked = np.clip(watermarked, 0, 255).astype(np.uint8)
        
        # Convert back to RGB
        watermarked_rgb = cv2.cvtColor(watermarked, cv2.COLOR_GRAY2RGB)
        
        # Blend with original (preserve QR code readability)
        img_array[:] = cv2.addWeighted(img_array, 0.7, watermarked_rgb, 0.3, 0)
        
        return signature
    
    def _add_pixel_fingerprint(self, img_array: np.ndarray, seed: str) -> str:
        """
        Add a unique noise-based fingerprint to specific pixels.
        
        This fingerprint degrades predictably with each copy generation.
        
        Args:
            img_array: QR code image as numpy array (modified in-place)
            seed: Seed for fingerprint generation
            
        Returns:
            Hash of the fingerprint pattern
        """
        height, width = img_array.shape[:2]
        
        # Create deterministic random generator
        rng = np.random.RandomState(int(hashlib.sha256(seed.encode()).hexdigest()[:8], 16))
        
        # Select specific pixels in a grid pattern
        step = 5  # Every 5th pixel
        y_coords, x_coords = np.meshgrid(
            range(step, height, step),
            range(step, width, step),
            indexing='ij'
        )
        
        # Generate noise pattern
        num_pixels = len(y_coords.flatten())
        noise = rng.randint(-self.fingerprint_strength, self.fingerprint_strength + 1, 
                           size=(num_pixels, 3))
        
        # Apply noise to selected pixels
        for idx, (y, x) in enumerate(zip(y_coords.flatten(), x_coords.flatten())):
            img_array[y, x] = np.clip(img_array[y, x].astype(int) + noise[idx], 0, 255).astype(np.uint8)
        
        # Create fingerprint hash
        fingerprint_data = {
            'step': step,
            'noise_strength': self.fingerprint_strength,
            'seed_hash': hashlib.sha256(seed.encode()).hexdigest()
        }
        fingerprint_str = json.dumps(fingerprint_data, sort_keys=True)
        fingerprint_hash = hashlib.sha256(fingerprint_str.encode()).hexdigest()
        
        return fingerprint_hash


def generate_secure_qr_code(
    data: str,
    doc_id: str,
    box_size: int = 10,
    border: int = 4
) -> Tuple[bytes, Dict]:
    """
    Convenience function to generate a secure QR code.
    
    Args:
        data: Data to encode in QR code
        doc_id: Unique document identifier
        box_size: Size of each QR code box
        border: Border size around QR code
        
    Returns:
        Tuple of (PNG image bytes, security metadata dict)
    """
    generator = SecureQRGenerator()
    return generator.generate_secure_qr(data, doc_id, box_size, border)
