#!/usr/bin/env python3
"""
Test chaos parameter breaks determinism
"""

import numpy as np
from rdt import generate_rdt_noise

print("=" * 60)
print("TEST: Chaos Parameter")
print("=" * 60)

# Test with chaos = 0.0 (should be deterministic)
print("\n1. Testing chaos=0.0 (deterministic):")
s1 = generate_rdt_noise(length=1000, chaos=0.0)
s2 = generate_rdt_noise(length=1000, chaos=0.0)

if np.allclose(s1, s2):
    print("  ✓ chaos=0.0 produces identical outputs")
else:
    print("  ✗ chaos=0.0 produces different outputs (unexpected!)")

# Test with chaos > 0.0 (should be non-deterministic)
print("\n2. Testing chaos>0.0 (non-deterministic):")
chaos_values = [0.3, 0.6, 1.0]

for chaos in chaos_values:
    s1 = generate_rdt_noise(length=1000, chaos=chaos)
    s2 = generate_rdt_noise(length=1000, chaos=chaos)

    if np.allclose(s1, s2):
        print(f"  ✗ chaos={chaos} produces identical outputs (unexpected!)")
    else:
        print(f"  ✓ chaos={chaos} produces different outputs")

print("\n" + "=" * 60)
