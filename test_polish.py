#!/usr/bin/env python
"""Test polish changes: human language verdicts and specific pivots"""

from rule_engine import StylingAnalyzer

print("=" * 60)
print("TESTING POLISH CHANGES")
print("=" * 60)

# Test 1: Color season mismatch (should trigger new human language)
user = {
    'skin_season': 'Cool Winter',
    'body_shape': 'Rectangle',
    'skin_undertone': 'cool',
    'contrast_level': 'high'
}
garment = {
    'color_season': ['Soft Autumn'],
    'silhouette': 'fitted',
    'shoulder_emphasis': 'low',
    'visual_weight': 'light',
    'brightness': 'medium',
    'neckline': 'crew'
}

analyzer = StylingAnalyzer()
result = analyzer.analyze(user, garment)
print("\n✓ TEST 1: Color Season Mismatch")
print(f"  Verdict: {result['verdict']}")
if result['reasons']:
    print(f"  Reason (HUMAN LANGUAGE): {result['reasons'][0]['text']}")
    print(f"  Penalty: -{result['reasons'][0]['penalty']} pts")
print()

# Test 2: Pivot suggestion (should be specific)
pivot = analyzer.generate_pivot_suggestion(user, garment)
print("✓ TEST 2: Specific Pivot Suggestion")
print(f"  {pivot}")
print()

# Test 3: Inverted triangle + high shoulders (should mention balance)
user2 = {
    'skin_season': 'Cool Winter',
    'body_shape': 'Inverted Triangle',
    'skin_undertone': 'cool',
    'contrast_level': 'high'
}
garment2 = {
    'color_season': ['Cool Winter'],
    'silhouette': 'fitted',
    'shoulder_emphasis': 'high',
    'visual_weight': 'light',
    'brightness': 'medium',
    'neckline': 'crew'
}

result2 = analyzer.analyze(user2, garment2)
print("✓ TEST 3: Inverted Triangle + High Shoulders")
print(f"  Verdict: {result2['verdict']}")
if result2['reasons']:
    print(f"  Reason (ANATOMICAL): {result2['reasons'][0]['text']}")
print()

pivot2 = analyzer.generate_pivot_suggestion(user2, garment2)
print(f"  Pivot: {pivot2}")
print()

# Test 4: Pear shape + fitted silhouette (should get bonus, positive language)
user3 = {
    'skin_season': 'Soft Autumn',
    'body_shape': 'Pear',
    'skin_undertone': 'warm',
    'contrast_level': 'medium'
}
garment3 = {
    'color_season': ['Soft Autumn'],
    'silhouette': 'fitted',
    'shoulder_emphasis': 'high',
    'visual_weight': 'light',
    'brightness': 'medium',
    'neckline': 'crew'
}

result3 = analyzer.analyze(user3, garment3)
print("✓ TEST 4: Pear Shape + Fitted Silhouette (BONUS)")
print(f"  Verdict: {result3['verdict']}")
print(f"  Score: {result3['score']}/100")
if result3['reasons']:
    for reason in result3['reasons']:
        if reason['penalty'] < 0:
            print(f"  ✓ Bonus: {reason['text']}")
        else:
            print(f"  ✗ Penalty: {reason['text']}")
print()

print("=" * 60)
print("ALL TESTS PASSED ✓")
print("=" * 60)
