"""
Counterfeit Detection Module

This module implements algorithms to detect copied, screenshot, or 
physically reproduced QR codes by analyzing security features.
"""

import hashlib
import json
import numpy as np
import cv2
from PIL import Image
from scipy.fftpack import dct
from scipy.stats import pearsonr
from typing import Dict, Tuple, List
import piexif


class CounterfeitDetector:
    """Detect counterfeit QR codes using multi-layer analysis."""
    
    def __init__(self):
        # Detection thresholds
        self.authenticity_threshold = 70  # Minimum score for authentic
        self.suspicious_threshold = 40    # Below this is counterfeit
        
        # Scoring weights
        # Scoring weights - Adjusted to prioritize robust features
        # Frequency watermark is reduced due to high sensitivity to browser resizing
        self.weights = {
            'ghost_dots': 0.45,      # Increased from 0.35
            'frequency': 0.10,       # Reduced from 0.30
            'fingerprint': 0.35,     # Increased from 0.25
            'metadata': 0.10         # Kept at 0.10
        }
    
    def verify_qr_authenticity(
        self,
        scanned_image: np.ndarray,
        security_metadata: Dict
    ) -> Dict:
        """
        Verify the authenticity of a scanned QR code.
        
        Args:
            scanned_image: Scanned QR code as numpy array
            security_metadata: Original security metadata from database
            
        Returns:
            Dictionary containing verification results and authenticity score
        """
        results = {}
        
        # 1. Ghost Dot Detection
        ghost_result = self._detect_ghost_dots(
            scanned_image,
            security_metadata.get('ghost_pattern', {})
        )
        results['ghost_dots'] = ghost_result
        
        # 2. Frequency Watermark Verification
        freq_result = self._verify_frequency_watermark(
            scanned_image,
            np.array(security_metadata.get('watermark_signature', [])),
            expected_size=security_metadata.get('image_size')
        )
        results['frequency_watermark'] = freq_result
        
        # 3. Pixel Fingerprint Analysis
        fingerprint_result = self._analyze_pixel_fingerprint(
            scanned_image,
            security_metadata.get('fingerprint_hash', '')
        )
        results['pixel_fingerprint'] = fingerprint_result
        
        # 4. Metadata Analysis
        metadata_result = self._analyze_metadata(scanned_image)
        results['metadata'] = metadata_result
        
        # Calculate overall authenticity score
        authenticity_score = (
            ghost_result['score'] * self.weights['ghost_dots'] +
            freq_result['score'] * self.weights['frequency'] +
            fingerprint_result['score'] * self.weights['fingerprint'] +
            metadata_result['score'] * self.weights['metadata']
        )
        
        # Determine verdict
        if authenticity_score >= self.authenticity_threshold:
            verdict = "AUTHENTIC"
            warnings = []
        elif authenticity_score >= self.suspicious_threshold:
            verdict = "SUSPICIOUS"
            warnings = ["Authenticity score is below recommended threshold"]
        else:
            verdict = "COUNTERFEIT"
            warnings = ["Multiple security features failed verification"]
        
        return {
            'verdict': verdict,
            'authenticity_score': round(authenticity_score, 2),
            'details': results,
            'warnings': warnings
        }
    
    def _detect_ghost_dots(
        self,
        img_array: np.ndarray,
        ghost_pattern: Dict
    ) -> Dict:
        """
        Detect ghost dots in the scanned image.
        
        Ghost dots are destroyed by screenshots and physical copies due to
        color quantization and print/scan degradation.
        
        Args:
            img_array: Scanned QR code image
            ghost_pattern: Original ghost dot pattern
            
        Returns:
            Detection result dictionary
        """
        if not ghost_pattern or 'coordinates' not in ghost_pattern:
            return {
                'score': 0,
                'detected': 0,
                'expected': 0,
                'status': 'NO_PATTERN'
            }
        
        expected_coords = ghost_pattern['coordinates']
        expected_count = ghost_pattern['count']
        
        if expected_count == 0:
            return {
                'score': 100,
                'detected': 0,
                'expected': 0,
                'status': 'PASS'
            }
        
        # Check each expected ghost dot location
        detected = 0
        height, width = img_array.shape[:2]
        
        for coord in expected_coords:
            x, y = coord['x'], coord['y']
            expected_value = coord['value']
            
            # Check if coordinates are within image bounds
            if y >= height or x >= width:
                continue
            
            # Get pixel value
            pixel = img_array[y, x]
            pixel_gray = int(np.mean(pixel))
            
            # Ghost dots should be in range 250-254
            # Allow some tolerance for camera noise
            if 245 <= pixel_gray <= 255:
                # Check if it's close to expected value
                if abs(pixel_gray - expected_value) <= 5:
                    detected += 1
        
        # Calculate detection rate
        detection_rate = (detected / expected_count) * 100 if expected_count > 0 else 0
        
        # Score based on detection rate
        # Original: 95-100% detection
        # Screenshot/Copy: 20-40% detection
        score = min(100, detection_rate * 1.05)  # Slight boost for high detection
        
        status = 'PASS' if score >= 70 else 'FAIL'
        
        return {
            'score': round(score, 2),
            'detected': detected,
            'expected': expected_count,
            'detection_rate': round(detection_rate, 2),
            'status': status
        }
    
    def _verify_frequency_watermark(
        self,
        img_array: np.ndarray,
        original_signature: np.ndarray,
        expected_size: Tuple[int, int] = None
    ) -> Dict:
        """
        Verify frequency domain watermark.
        
        Watermark degrades with compression and print/scan cycles.
        
        Args:
            img_array: Scanned QR code image
            original_signature: Original watermark signature
            expected_size: Expected image dimensions (height, width) from metadata
            
        Returns:
            Verification result dictionary
        """
        if original_signature.size == 0:
            return {
                'score': 0,
                'correlation': 0,
                'status': 'NO_SIGNATURE'
            }
        
        try:
            # Convert to grayscale
            if len(img_array.shape) == 3:
                gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY).astype(float)
            else:
                gray = img_array.astype(float)
                
            # CRITICAL: Resize to match the original generation size exactly
            # DCT frequency bins depend on image size. If sizes mismatch, we look at wrong frequencies.
            if expected_size:
                # expected_size is (height, width)
                # cv2.resize expects (width, height)
                target_h, target_w = expected_size[0], expected_size[1]
                if gray.shape != (target_h, target_w):
                    gray = cv2.resize(gray, (target_w, target_h), interpolation=cv2.INTER_LANCZOS4)
            
            # Apply DCT
            dct_coeffs = dct(dct(gray.T, norm='ortho').T, norm='ortho')
            dct_coeffs = dct(dct(gray.T, norm='ortho').T, norm='ortho')
            
            # Extract watermark from mid-frequency region
            h, w = dct_coeffs.shape
            mid_h, mid_w = h // 4, w // 4
            
            sig_h, sig_w = original_signature.shape
            extracted = dct_coeffs[mid_h:mid_h+sig_h, mid_w:mid_w+sig_w]
            
            # Ensure same shape
            if extracted.shape != original_signature.shape:
                return {
                    'score': 0,
                    'correlation': 0,
                    'status': 'SIZE_MISMATCH'
                }
            
            # Calculate correlation
            correlation, _ = pearsonr(
                original_signature.flatten(),
                extracted.flatten()
            )
            
            # Handle NaN
            if np.isnan(correlation):
                correlation = 0
            
            # Score based on correlation
            # Original: 0.85-1.0
            # Digital copy: 0.5-0.7
            # Physical copy: 0.3-0.5
            score = max(0, min(100, correlation * 100))
            
            status = 'PASS' if score >= 50 else 'FAIL'
            
            return {
                'score': round(score, 2),
                'correlation': round(correlation, 4),
                'status': status
            }
            
        except Exception as e:
            return {
                'score': 0,
                'correlation': 0,
                'status': f'ERROR: {str(e)}'
            }
    
    def _analyze_pixel_fingerprint(
        self,
        img_array: np.ndarray,
        original_hash: str
    ) -> Dict:
        """
        Analyze pixel fingerprint integrity.
        
        Noise pattern degrades with each copy generation.
        
        Args:
            img_array: Scanned QR code image
            original_hash: Original fingerprint hash
            
        Returns:
            Analysis result dictionary
        """
        if not original_hash:
            return {
                'score': 0,
                'integrity': 0,
                'status': 'NO_FINGERPRINT'
            }
        
        try:
            height, width = img_array.shape[:2]
            
            # Extract pixels in grid pattern (same as embedding)
            step = 5
            y_coords, x_coords = np.meshgrid(
                range(step, height, step),
                range(step, width, step),
                indexing='ij'
            )
            
            # Analyze noise characteristics
            pixel_values = []
            for y, x in zip(y_coords.flatten(), x_coords.flatten()):
                if y < height and x < width:
                    pixel_values.append(img_array[y, x])
            
            if not pixel_values:
                return {
                    'score': 0,
                    'integrity': 0,
                    'status': 'NO_PIXELS'
                }
            
            pixel_values = np.array(pixel_values)
            
            # Calculate noise variance (should be consistent in original)
            variance = np.var(pixel_values)
            
            # Original images have controlled noise variance
            # Copies have reduced variance due to smoothing
            # Expected variance range: 50-200 for original
            expected_variance_range = (50, 200)
            
            if expected_variance_range[0] <= variance <= expected_variance_range[1]:
                integrity = 0.9 + (variance / 2000)  # High integrity
            elif variance < expected_variance_range[0]:
                integrity = variance / expected_variance_range[0] * 0.6  # Low variance = copy
            else:
                integrity = 0.7  # High variance = possible manipulation
            
            integrity = min(1.0, max(0, integrity))
            score = integrity * 100
            
            status = 'PASS' if score >= 60 else 'FAIL'
            
            return {
                'score': round(score, 2),
                'integrity': round(integrity, 4),
                'variance': round(float(variance), 2),
                'status': status
            }
            
        except Exception as e:
            return {
                'score': 0,
                'integrity': 0,
                'status': f'ERROR: {str(e)}'
            }
    
    def _analyze_metadata(self, img_array: np.ndarray) -> Dict:
        """
        Analyze image metadata for screenshot indicators.
        
        Screenshots typically lack camera EXIF data and have specific
        software signatures.
        
        Args:
            img_array: Scanned QR code image (note: metadata is lost in numpy array)
            
        Returns:
            Metadata analysis result
        """
        # Note: This is a simplified version since we receive numpy array
        # In production, you'd analyze the original image file before conversion
        
        # For now, we'll do basic image quality analysis
        # Screenshots often have different compression artifacts
        
        try:
            # Analyze image sharpness (Laplacian variance)
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
            
            # Original camera images: higher variance (sharper)
            # Screenshots: lower variance (smoother)
            # Expected range for camera: 100-1000+
            # Screenshots: 20-100
            
            if laplacian_var > 100:
                score = 90  # Likely camera image
                has_camera_characteristics = True
            elif laplacian_var > 50:
                score = 60  # Uncertain
                has_camera_characteristics = False
            else:
                score = 30  # Likely screenshot
                has_camera_characteristics = False
            
            status = 'PASS' if score >= 50 else 'FAIL'
            
            return {
                'score': round(score, 2),
                'sharpness': round(float(laplacian_var), 2),
                'has_camera_characteristics': has_camera_characteristics,
                'status': status
            }
            
        except Exception as e:
            return {
                'score': 50,  # Neutral score on error
                'status': f'ERROR: {str(e)}'
            }


def verify_qr_code(
    scanned_image_path: str,
    security_metadata: Dict
) -> Dict:
    """
    Convenience function to verify a QR code from file path.
    
    Args:
        scanned_image_path: Path to scanned QR code image
        security_metadata: Original security metadata from database
        
    Returns:
        Verification results dictionary
    """
    # Load image
    img = Image.open(scanned_image_path)
    img_array = np.array(img.convert('RGB'))
    
    # Verify
    detector = CounterfeitDetector()
    return detector.verify_qr_authenticity(img_array, security_metadata)


def verify_qr_code_bytes(
    image_bytes: bytes,
    security_metadata: Dict
) -> Dict:
    """
    Convenience function to verify a QR code from image bytes.
    
    Args:
        image_bytes: QR code image as bytes
        security_metadata: Original security metadata from database
        
    Returns:
        Verification results dictionary
    """
    # Load image from bytes
    from io import BytesIO
    img = Image.open(BytesIO(image_bytes))
    img_array = np.array(img.convert('RGB'))
    
    # Verify
    detector = CounterfeitDetector()
    return detector.verify_qr_authenticity(img_array, security_metadata)
