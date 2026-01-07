#!/usr/bin/env python3
"""
Check what the correct hex values should be
"""

import json

# Load test vectors
with open('test_vectors.json', 'r') as f:
    vectors = json.load(f)

expected_hex = vectors['initialization_state']['state_hex']
expected_dec = vectors['initialization_state']['state_decimal']

print("=" * 80)
print("HEX VALUE VERIFICATION")
print("=" * 80)

print("\nConverting expected decimal values to hex:")
print(f"{'Index':<6} {'Test Vector Hex':<15} {'Expected Dec':<15} {'Dec→Hex':<15} {'Match':<6}")
print("-" * 80)

for i in range(16):
    expected_hex_val = expected_hex[i]
    expected_dec_val = expected_dec[i]
    computed_hex = hex(expected_dec_val)

    match = "✓" if expected_hex_val.lower() == computed_hex.lower() else "✗"

    print(f"{i:<6} {expected_hex_val:<15} {expected_dec_val:<15} {computed_hex:<15} {match:<6}")

print("\n" + "=" * 80)
print("CHECKING SOURCE CODE HEX VALUES")
print("=" * 80)

# The hex values currently in rdt.py
source_hex = [
    0x243F6A88, 0x85A308D3, 0x13198A2E, 0x03707344,
    0xA4093822, 0x299F31D0, 0x082EFA98, 0xEC4E6C89,
    0x452821E6, 0x38D01377, 0xBE5466CF, 0x34E90C6C,
    0xC0AC29B7, 0xC97C50DD, 0x3F84D5B5, 0xB5470917
]

print("\nComparing source code hex values:")
print(f"{'Index':<6} {'Source Hex':<15} {'Source Dec':<15} {'Expected Dec':<15} {'Match':<6}")
print("-" * 80)

mismatches = []
for i in range(16):
    source_val = source_hex[i]
    source_dec = source_val
    expected_dec_val = expected_dec[i]

    match = "✓" if source_dec == expected_dec_val else "✗"

    print(f"{i:<6} {hex(source_val):<15} {source_dec:<15} {expected_dec_val:<15} {match:<6}")

    if source_dec != expected_dec_val:
        mismatches.append((i, hex(source_val), source_dec, expected_dec_val))

if mismatches:
    print("\n" + "=" * 80)
    print(f"FOUND {len(mismatches)} MISMATCHES - NEED CORRECTION")
    print("=" * 80)

    print("\nCorrected hex values needed:")
    print("INIT_STATE = np.array([")

    for row_start in range(0, 16, 4):
        hex_vals = []
        for i in range(row_start, min(row_start + 4, 16)):
            correct_hex = hex(expected_dec[i])
            hex_vals.append(correct_hex)
        print(f"    {', '.join(hex_vals)},")

    print("], dtype=np.uint32)")
