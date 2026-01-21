#!/usr/bin/env python3
"""
Test script for Anti-Counterfeiting QR System

This script demonstrates the security features and tests detection capabilities.
"""

import os
import sys
import numpy as np
from PIL import Image
from io import BytesIO
import cv2

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from secure_qr_generator import generate_secure_qr_code
from counterfeit_detector import verify_qr_code_bytes


def simulate_screenshot(image_bytes: bytes) -> bytes:
    """
    Simulate a screenshot by applying color quantization and compression.
    
    Screenshots typically:
    - Lose subtle color variations (ghost dots)
    - Apply color quantization
    - Use PNG compression
    """
    img = Image.open(BytesIO(image_bytes))
    img_array = np.array(img.convert('RGB'))
    
    # Apply color quantization (simulates screenshot color reduction)
    # Round to nearest 5 in RGB space
    quantized = (img_array // 5) * 5
    
    # Convert back to image
    screenshot_img = Image.fromarray(quantized.astype(np.uint8))
    
    # Save with PNG compression
    buffer = BytesIO()
    screenshot_img.save(buffer, format='PNG', optimize=True)
    buffer.seek(0)
    
    return buffer.getvalue()


def simulate_physical_copy(image_bytes: bytes) -> bytes:
    """
    Simulate a physical photocopy by applying blur, noise, and degradation.
    
    Physical copies typically:
    - Lose fine details (ghost dots)
    - Add printer/scanner noise
    - Reduce sharpness
    - Introduce slight distortion
    """
    img = Image.open(BytesIO(image_bytes))
    img_array = np.array(img.convert('RGB'))
    
    # Apply slight blur (print/scan degradation)
    blurred = cv2.GaussianBlur(img_array, (3, 3), 0.5)
    
    # Add noise (scanner artifacts)
    noise = np.random.normal(0, 5, blurred.shape)
    noisy = np.clip(blurred + noise, 0, 255).astype(np.uint8)
    
    # Reduce contrast slightly
    adjusted = cv2.convertScaleAbs(noisy, alpha=0.95, beta=5)
    
    # Convert back to image
    copy_img = Image.fromarray(adjusted)
    
    # Save with JPEG compression (scanner output)
    buffer = BytesIO()
    copy_img.save(buffer, format='JPEG', quality=85)
    buffer.seek(0)
    
    return buffer.getvalue()


def simulate_digital_copy(image_bytes: bytes) -> bytes:
    """
    Simulate a digital copy with JPEG compression.
    """
    img = Image.open(BytesIO(image_bytes))
    
    # Save with JPEG compression
    buffer = BytesIO()
    img.save(buffer, format='JPEG', quality=75)
    buffer.seek(0)
    
    return buffer.getvalue()


def print_result(title: str, result: dict):
    """Pretty print verification result."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")
    print(f"Verdict: {result['verdict']}")
    print(f"Authenticity Score: {result['authenticity_score']:.2f}%")
    print(f"\nDetailed Scores:")
    print(f"  Ghost Dots:          {result['details']['ghost_dots']['score']:.2f}% - {result['details']['ghost_dots']['status']}")
    print(f"  Frequency Watermark: {result['details']['frequency_watermark']['score']:.2f}% - {result['details']['frequency_watermark']['status']}")
    print(f"  Pixel Fingerprint:   {result['details']['pixel_fingerprint']['score']:.2f}% - {result['details']['pixel_fingerprint']['status']}")
    print(f"  Metadata Analysis:   {result['details']['metadata']['score']:.2f}% - {result['details']['metadata']['status']}")
    
    if result['warnings']:
        print(f"\nWarnings:")
        for warning in result['warnings']:
            print(f"  ⚠️  {warning}")
    
    # Additional details
    ghost = result['details']['ghost_dots']
    if 'detected' in ghost and 'expected' in ghost:
        print(f"\nGhost Dots: {ghost['detected']}/{ghost['expected']} detected")


def main():
    """Run comprehensive tests."""
    print("="*60)
    print("  Anti-Counterfeiting QR Code System - Test Suite")
    print("="*60)
    
    # Test data
    test_url = "https://example.com/verify/test123"
    test_doc_id = "TEST_DOC_12345"
    
    print(f"\nGenerating secure QR code for: {test_url}")
    print(f"Document ID: {test_doc_id}")
    
    # Generate secure QR code
    original_bytes, security_metadata = generate_secure_qr_code(test_url, test_doc_id)
    
    print(f"\n✅ Secure QR code generated successfully!")
    print(f"   - Ghost dots: {security_metadata['ghost_pattern']['count']}")
    print(f"   - Watermark signature: {len(security_metadata['watermark_signature'])} coefficients")
    print(f"   - Fingerprint hash: {security_metadata['fingerprint_hash'][:16]}...")
    print(f"   - Security version: {security_metadata['security_version']}")
    
    # Save original
    os.makedirs("test_output", exist_ok=True)
    with open("test_output/original_qr.png", "wb") as f:
        f.write(original_bytes)
    print(f"\n💾 Saved original QR to: test_output/original_qr.png")
    
    # Test 1: Verify original
    print(f"\n{'='*60}")
    print("TEST 1: Verifying Original QR Code")
    print(f"{'='*60}")
    result_original = verify_qr_code_bytes(original_bytes, security_metadata)
    print_result("Original QR Code", result_original)
    
    # Test 2: Verify screenshot
    print(f"\n{'='*60}")
    print("TEST 2: Verifying Screenshot")
    print(f"{'='*60}")
    screenshot_bytes = simulate_screenshot(original_bytes)
    with open("test_output/screenshot_qr.png", "wb") as f:
        f.write(screenshot_bytes)
    print(f"💾 Saved screenshot simulation to: test_output/screenshot_qr.png")
    
    result_screenshot = verify_qr_code_bytes(screenshot_bytes, security_metadata)
    print_result("Screenshot (Counterfeit)", result_screenshot)
    
    # Test 3: Verify physical copy
    print(f"\n{'='*60}")
    print("TEST 3: Verifying Physical Copy")
    print(f"{'='*60}")
    physical_bytes = simulate_physical_copy(original_bytes)
    with open("test_output/physical_copy_qr.jpg", "wb") as f:
        f.write(physical_bytes)
    print(f"💾 Saved physical copy simulation to: test_output/physical_copy_qr.jpg")
    
    result_physical = verify_qr_code_bytes(physical_bytes, security_metadata)
    print_result("Physical Copy (Counterfeit)", result_physical)
    
    # Test 4: Verify digital copy
    print(f"\n{'='*60}")
    print("TEST 4: Verifying Digital Copy (JPEG)")
    print(f"{'='*60}")
    digital_bytes = simulate_digital_copy(original_bytes)
    with open("test_output/digital_copy_qr.jpg", "wb") as f:
        f.write(digital_bytes)
    print(f"💾 Saved digital copy simulation to: test_output/digital_copy_qr.jpg")
    
    result_digital = verify_qr_code_bytes(digital_bytes, security_metadata)
    print_result("Digital Copy (JPEG)", result_digital)
    
    # Summary
    print(f"\n{'='*60}")
    print("  TEST SUMMARY")
    print(f"{'='*60}")
    print(f"Original QR:     {result_original['verdict']:12} ({result_original['authenticity_score']:.1f}%)")
    print(f"Screenshot:      {result_screenshot['verdict']:12} ({result_screenshot['authenticity_score']:.1f}%)")
    print(f"Physical Copy:   {result_physical['verdict']:12} ({result_physical['authenticity_score']:.1f}%)")
    print(f"Digital Copy:    {result_digital['verdict']:12} ({result_digital['authenticity_score']:.1f}%)")
    
    print(f"\n✅ All tests completed! Check test_output/ directory for generated images.")
    print(f"\n{'='*60}\n")


if __name__ == "__main__":
    main()
