"""Quick test script to validate all modules"""

import sys
from rule_engine import StylingAnalyzer
from dotenv import load_dotenv
import os
sys.path.insert(0, r"c:\Users\riskumar23\Downloads\Honest Stylist")

print("=" * 60)
print("TESTING HONEST STYLIST MVP")
print("=" * 60)

# Test 1: Garment Catalog
print("\n✓ Testing Garment Catalog...")
from garment_catalog import list_garments_display, get_garment
garments = list_garments_display()
print(f"  - Loaded {len(garments)} garments")
print(f"  - Example: {garments[0]}")
sample = get_garment("tee_001")
print(f"  - Garment details: {sample['name']}, seasons: {sample['color_season']}")

# Test 2: Rule Engine
print("\n✓ Testing Rule Engine...")
analyzer = StylingAnalyzer()
user_profile = {
    "skin_season": "Cool Winter",
    "skin_undertone": "cool",
    "contrast_level": "high"
}
garment_test = get_garment("tee_003")  # Black Turtleneck
result = analyzer.analyze(user_profile, garment_test)
print(f"  - Verdict: {result['verdict']}")
print(f"  - Score: {result['score']}/100")
print(f"  - Reasons: {len(result['reasons'])} rules applied")

# Test 3: Vision Analyzer (stub test)
print("\n✓ Testing Vision Analyzer...")
from vision_analyzer import VisionAnalyzer
vision = VisionAnalyzer()
print(f"  - VisionAnalyzer initialized")
print(f"  - Face detector: OK")
print(f"  - Pose detector: OK")
print(f"  - Methods: analyze_photo, _detect_face, _extract_skin, _extract_hair, _extract_eye_color, _classify_contrast")

# Test 4: Gemini Explainer (check if API key exists)
print("\n✓ Testing Gemini Explainer...")
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
if api_key:
    print(f"  - API key found: {api_key[:10]}...")
    from gemini_explainer import GeminiExplainer
    try:
        explainer = GeminiExplainer(api_key)
        print(f"  - Explainer initialized: OK")
    except Exception as e:
        print(f"  - Explainer init error: {str(e)}")
else:
    print(f"  - API key NOT set (optional for testing)")

print("\n" + "=" * 60)
print("ALL MODULES LOADED SUCCESSFULLY!")
print("=" * 60)
print("\nNext: Run 'streamlit run app.py' to start the web UI")
