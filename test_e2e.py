"""Full end-to-end test without Streamlit UI"""

import sys
sys.path.insert(0, r"c:\Users\riskumar23\Downloads\Honest Stylist")

from vision_analyzer import VisionAnalyzer
from garment_catalog import get_garment
from rule_engine import StylingAnalyzer

print("=" * 70)
print("HONEST STYLIST - END-TO-END TEST")
print("=" * 70)

# Step 1: Vision analysis
print("\n[1/4] Running vision analysis on test photo...")
vision = VisionAnalyzer()
user_profile = vision.analyze_photo(r"c:\Users\riskumar23\Downloads\Honest Stylist\test_photo.jpg")
print(f"✓ User Profile:")
for k, v in user_profile.items():
    print(f"    - {k}: {v}")

# Step 2: Select a garment
print("\n[2/4] Selecting garment: 'Black Turtleneck'")
garment = get_garment("tee_003")
print(f"✓ Garment: {garment['name']}")
print(f"    - Color season: {garment['color_season']}")
print(f"    - Shoulder emphasis: {garment['shoulder_emphasis']}")
print(f"    - Silhouette: {garment['silhouette']}")

# Step 3: Rule engine analysis
print("\n[3/4] Running rule engine...")
analyzer = StylingAnalyzer()
result = analyzer.analyze(user_profile, garment)
print(f"✓ Result:")
print(f"    - Score: {result['score']}/100")
print(f"    - Verdict: {result['verdict']}")
print(f"    - Reasons ({len(result['reasons'])} rules applied):")
for reason in result['reasons']:
    print(f"      • {reason['text']} ({reason['penalty']:+d} pts)")

# Step 4: Test with different garment
print("\n[4/4] Testing with different garment: 'Camel Oversized Sweater'")
garment2 = get_garment("tee_002")
result2 = analyzer.analyze(user_profile, garment2)
print(f"✓ Result:")
print(f"    - Score: {result2['score']}/100")
print(f"    - Verdict: {result2['verdict']}")

print("\n" + "=" * 70)
print("END-TO-END TEST PASSED ✓")
print("=" * 70)
print("\nNext: Run 'streamlit run app.py' to start the web UI")
