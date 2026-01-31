import os
from vision_analyzer import VisionAnalyzer

# Define your test images and what the result SHOULD be
TEST_SUITE = {
    "test_images/pear_01.jpg": "Pear",
    "test_images/inv_tri_01.jpg": "Inverted Triangle",
    "test_images/hourglass_01.jpg": "Hourglass",
    "test_images/rect_01.jpg": "Rectangle",
    "test_images/apple_01.jpg": "Apple"
}

def run_benchmarks():
    analyzer = VisionAnalyzer()
    passed = 0
    
    print("--- STARTING BATCH TEST ---")
    for img_path, expected in TEST_SUITE.items():
        if not os.path.exists(img_path):
            print(f"Skipping {img_path}: File not found")
            continue
            
        result = analyzer.analyze_photo(img_path)
        actual = result['body_shape']
        
        status = "✅ PASS" if actual == expected else "❌ FAIL"
        if actual == expected: passed += 1
        
        print(f"{status} | Image: {img_path}")
        print(f"      Expected: {expected} | Actual: {actual}")
        print(f"      Ratios: {result['body_ratios']}\n")

    print(f"--- FINAL SCORE: {passed}/{len(TEST_SUITE)} ---")

if __name__ == "__main__":
    run_benchmarks()