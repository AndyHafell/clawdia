#!/usr/bin/env python3
"""
Crop FACE ONLY from full-frame reference images.
Uses OpenCV Haar cascade for face detection, then creates a tight crop
around the face — hair to chin, ear to ear. No body/shoulders.
"""

import cv2
import os
import sys
from pathlib import Path

# Paths (project root is one level up from pipeline/)
BASE = Path(__file__).parent.parent
INPUT_DIR = BASE / "face_references_new"
OUTPUT_DIR = BASE / "face_references"

# Create output dir if needed
OUTPUT_DIR.mkdir(exist_ok=True)

# Load Haar cascade for face detection
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

# How much padding around the detected face (as multiplier of face size)
# FACE ONLY — tight crop: hair to chin, ear to ear
PAD_TOP = 0.55     # Above the face (forehead + hair)
PAD_BOTTOM = 0.35  # Below the face (chin + a bit of neck)
PAD_LEFT = 0.35    # Left of face (ear)
PAD_RIGHT = 0.35   # Right of face (ear)

def crop_face(image_path, output_path):
    """Detect face and crop tightly — face only, no body."""
    img = cv2.imread(str(image_path))
    if img is None:
        print(f"  ERROR: Could not read {image_path.name}")
        return False

    h, w = img.shape[:2]
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Detect faces - try multiple scale factors for reliability
    faces = face_cascade.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(100, 100)
    )

    if len(faces) == 0:
        # Try with more lenient settings
        faces = face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.05,
            minNeighbors=3,
            minSize=(80, 80)
        )

    if len(faces) == 0:
        print(f"  WARNING: No face detected in {image_path.name} — using center crop fallback")
        # Fallback: tight center-right crop for face area only
        cx, cy = int(w * 0.6), int(h * 0.3)
        crop_size = int(min(w, h) * 0.4)  # tight square-ish crop
        x1 = max(0, cx - crop_size // 2)
        y1 = max(0, cy - crop_size // 2)
        x2 = min(w, x1 + crop_size)
        y2 = min(h, y1 + int(crop_size * 1.1))
        cropped = img[y1:y2, x1:x2]
        cv2.imwrite(str(output_path), cropped, [cv2.IMWRITE_PNG_COMPRESSION, 1])
        crop_h_out, crop_w_out = cropped.shape[:2]
        print(f"  Fallback crop: {crop_w_out}x{crop_h_out}")
        return True

    # Use the largest detected face (in case of false positives)
    faces = sorted(faces, key=lambda f: f[2] * f[3], reverse=True)
    fx, fy, fw, fh = faces[0]

    # Calculate crop region with padding
    pad_top = int(fh * PAD_TOP)
    pad_bottom = int(fh * PAD_BOTTOM)
    pad_left = int(fw * PAD_LEFT)
    pad_right = int(fw * PAD_RIGHT)

    x1 = max(0, fx - pad_left)
    y1 = max(0, fy - pad_top)
    x2 = min(w, fx + fw + pad_right)
    y2 = min(h, fy + fh + pad_bottom)

    cropped = img[y1:y2, x1:x2]

    # Save as high-quality PNG
    cv2.imwrite(str(output_path), cropped, [cv2.IMWRITE_PNG_COMPRESSION, 1])

    crop_h_out, crop_w_out = cropped.shape[:2]
    print(f"  Face at ({fx},{fy}) {fw}x{fh} -> Crop: {crop_w_out}x{crop_h_out}")
    return True


def main():
    png_files = sorted(INPUT_DIR.glob("*.png"))

    if not png_files:
        print("No PNG files found in face_references_new/")
        sys.exit(1)

    print(f"Found {len(png_files)} images to crop\n")

    success = 0
    for img_path in png_files:
        output_path = OUTPUT_DIR / img_path.name
        print(f"Processing: {img_path.name}")
        if crop_face(img_path, output_path):
            success += 1

    print(f"\nDone! {success}/{len(png_files)} images cropped and saved to face_references/")


if __name__ == "__main__":
    main()
