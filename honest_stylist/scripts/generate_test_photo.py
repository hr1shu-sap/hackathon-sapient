"""Create a test image and validate vision analysis"""

import cv2
import numpy as np
import os

# Create a simple test image (face-colored rectangle)
output_path = r"c:\Users\riskumar23\Downloads\Honest Stylist\test_photo.jpg"

# Create 400x300 image with skin-tone color
img = np.zeros((300, 400, 3), dtype=np.uint8)

# Fill with approximate skin tone (BGR)
# Skin tone in BGR: roughly B=150, G=130, R=180
skin_color = [150, 130, 180]
img[:] = skin_color

# Add some variety (shoulders and neck)
cv2.rectangle(img, (50, 100), (350, 250), (140, 120, 170), -1)

# Save
cv2.imwrite(output_path, img)
print(f"✓ Created test photo: {output_path}")

# Now test vision analysis on it
import sys
sys.path.insert(0, r"c:\Users\riskumar23\Downloads\Honest Stylist")

from honest_stylist.app.vision_analyzer import VisionAnalyzer

print("\nTesting Vision Analysis on test photo...")
analyzer = VisionAnalyzer()
result = analyzer.analyze_photo(output_path)

print(f"✓ Analysis complete!")
print(f"  - Skin tone: {result['skin_hex']}")
print(f"  - Undertone: {result['skin_undertone']}")
print(f"  - Contrast: {result['contrast_level']}")
print(f"  - Body shape: {result['body_shape']}")
print(f"  - Season: {result['skin_season']}")
print(f"  - Confidence: {result['confidence']}")
