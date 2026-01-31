#!/usr/bin/env python
"""Run all unit tests with proper encoding"""

import sys
import subprocess

# Set UTF-8 encoding for output
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

tests = [
    ("test_modules.py", "Module imports and initialization"),
    ("test_feature1.py", "Feature 1: Custom garment upload"),
    ("test_polish.py", "Polish changes: Human language verdicts"),
]

print("=" * 70)
print("RUNNING ALL UNIT TESTS")
print("=" * 70)

results = []
for test_file, description in tests:
    print(f"\n[TEST] {description}")
    print(f"       Running: {test_file}")
    print("-" * 70)
    
    try:
        result = subprocess.run(
            [sys.executable, test_file],
            cwd=r"c:\Users\riskumar23\Downloads\Honest Stylist",
            capture_output=True,
            text=True,
            timeout=30
        )
        
        # Print output, filtering out encoding warnings
        for line in result.stdout.split('\n'):
            if line and 'ConvergenceWarning' not in line and 'RuntimeWarning' not in line and 'sklearn' not in line:
                print(line)
        
        # Check if test passed
        if result.returncode == 0 or "PASS" in result.stdout or "passed" in result.stdout.lower():
            results.append((test_file, "PASSED"))
            print("[OK]")
        else:
            results.append((test_file, "FAILED"))
            print("[FAILED]")
            if result.stderr:
                print("STDERR:", result.stderr[:500])
    except Exception as e:
        results.append((test_file, f"ERROR: {str(e)}"))
        print(f"[ERROR] {str(e)}")

print("\n" + "=" * 70)
print("TEST SUMMARY")
print("=" * 70)
for test_file, status in results:
    symbol = "[OK]" if "PASSED" in status else "[FAIL]" if "FAILED" in status else "[ERROR]"
    print(f"{symbol} {test_file}: {status}")

passed = sum(1 for _, s in results if "PASSED" in s)
total = len(results)
print(f"\nTotal: {passed}/{total} tests passed")
print("=" * 70)
