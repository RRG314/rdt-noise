#!/usr/bin/env python3
"""
Analyze initialization constants to find the discrepancy
"""

import json

# Load test vectors
with open('test_vectors.json', 'r') as f:
    vectors = json.load(f)

expected_hex = vectors['initialization_state']['state_hex']
expected_dec = vectors['initialization_state']['state_decimal']

# Current constants from rdt.py
from rdt import INIT_STATE

print("=" * 70)
print("INITIALIZATION CONSTANT ANALYSIS")
print("=" * 70)

print("\nComparing current vs expected values:\n")
print(f"{'Index':<6} {'Expected Hex':<12} {'Expected Dec':<12} {'Current Dec':<12} {'Match':<6}")
print("-" * 70)

mismatches = []
for i in range(16):
    exp_hex = expected_hex[i]
    exp_dec = expected_dec[i]
    cur_dec = int(INIT_STATE[i])
    match = "✓" if exp_dec == cur_dec else "✗"

    print(f"{i:<6} {exp_hex:<12} {exp_dec:<12} {cur_dec:<12} {match:<6}")

    if exp_dec != cur_dec:
        mismatches.append({
            'index': i,
            'expected_hex': exp_hex,
            'expected_dec': exp_dec,
            'current_dec': cur_dec,
            'difference': cur_dec - exp_dec
        })

print("\n" + "=" * 70)
print(f"MISMATCHES: {len(mismatches)} out of 16")
print("=" * 70)

if mismatches:
    print("\nDetailed mismatch analysis:")
    for m in mismatches:
        print(f"\n  Index {m['index']}:")
        print(f"    Expected: {m['expected_hex']} = {m['expected_dec']}")
        print(f"    Current:  {hex(m['current_dec'])} = {m['current_dec']}")
        print(f"    Diff:     {m['difference']:+d}")

print("\n" + "=" * 70)
print("RECOMMENDATION:")
print("=" * 70)
print("\nThe INIT_STATE array in rdt.py needs to use the correct hex values.")
print("These are π-based constants (fractional part of π digits).")
print("\nCorrect initialization should be:")
print("\nINIT_STATE = np.array([")
for i in range(0, 16, 4):
    hex_vals = ", ".join([expected_hex[j] for j in range(i, min(i+4, 16))])
    print(f"    {hex_vals},")
print("], dtype=np.uint32)")
