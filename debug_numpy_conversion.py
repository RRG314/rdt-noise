#!/usr/bin/env python3
"""
Debug numpy uint32 conversion issue
"""

import numpy as np

# Test direct conversion
print("=" * 70)
print("NUMPY UINT32 CONVERSION TEST")
print("=" * 70)

# Test a few problematic values
test_cases = [
    ("0x03707344", 0x03707344, 57694916),
    ("0xA4093822", 0xA4093822, 2752067106),
    ("0x299F31D0", 0x299F31D0, 699697872),
]

print("\nDirect Python int conversion:")
for name, hex_val, expected_dec in test_cases:
    python_val = int(hex_val)
    print(f"{name}: {python_val} (expected: {expected_dec}) {'✓' if python_val == expected_dec else '✗'}")

print("\nNumPy uint32 conversion (single value):")
for name, hex_val, expected_dec in test_cases:
    np_val = int(np.uint32(hex_val))
    print(f"{name}: {np_val} (expected: {expected_dec}) {'✓' if np_val == expected_dec else '✗'}")

print("\nNumPy array conversion:")
test_array = np.array([0x03707344, 0xA4093822, 0x299F31D0], dtype=np.uint32)
expected_array = [57694916, 2752067106, 699697872]
for i, (actual, expected) in enumerate(zip(test_array, expected_array)):
    actual_int = int(actual)
    print(f"[{i}]: {actual_int} (expected: {expected}) {'✓' if actual_int == expected else '✗'}")

# Now test with Python signed interpretation
print("\n" + "=" * 70)
print("CHECKING FOR SIGNED/UNSIGNED INTERPRETATION ISSUE")
print("=" * 70)

# Some of these hex values might be interpreted as signed integers
# if they have the high bit set
problem_vals = [
    0x85A308D3,  # High bit set
    0xA4093822,  # High bit set
    0xEC4E6C89,  # High bit set
    0xBE5466CF,  # High bit set
    0xC0AC29B7,  # High bit set
    0xC97C50DD,  # High bit set
    0xB5470917,  # High bit set
]

print("\nValues with high bit set:")
for val in problem_vals:
    as_signed = np.int32(val)
    as_unsigned = np.uint32(val)
    print(f"{hex(val)}: signed={int(as_signed):>12}, unsigned={int(as_unsigned):>12}")

# Check what's actually in INIT_STATE from rdt.py
print("\n" + "=" * 70)
print("ACTUAL INIT_STATE VALUES FROM rdt.py")
print("=" * 70)

from rdt import INIT_STATE

print(f"\nINIT_STATE dtype: {INIT_STATE.dtype}")
print(f"INIT_STATE shape: {INIT_STATE.shape}")
print("\nActual values:")
for i, val in enumerate(INIT_STATE):
    print(f"[{i:2d}] {hex(int(val)):>10} = {int(val):>10}")
