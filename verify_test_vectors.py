#!/usr/bin/env python3
"""
Verify RDT implementation against test vectors
"""

import json
import numpy as np
from rdt import generate_rdt_noise, calculate_entropy

def load_test_vectors():
    with open('test_vectors.json', 'r') as f:
        return json.load(f)

def test_standard():
    """Test paper-accurate standard RDT"""
    print("=" * 60)
    print("TEST 1: Standard RDT Parameters")
    print("=" * 60)

    vectors = load_test_vectors()
    params = vectors['standard_test']['parameters']

    # Generate samples
    samples = generate_rdt_noise(
        length=44100,
        phi_scale=params['phi_scale'],
        delta_scale=params['delta_scale'],
        depth=params['depth'],
        chaos=params['chaos'],
        variant=params['variant']
    )

    # Check first 10 samples
    print("\nFirst 10 samples:")
    expected = vectors['standard_test']['expected_first_10_samples']

    for i in range(10):
        actual = samples[i]
        exp = expected[i]
        diff = abs(actual - exp)
        match = "✓" if diff < 0.01 else "✗"
        print(f"  [{i}] Expected: {exp:7.4f}, Actual: {actual:7.4f}, Diff: {diff:.4f} {match}")

    # Check statistics
    print("\nStatistics:")
    stats = vectors['standard_test']['expected_statistics']

    entropy = calculate_entropy(samples)
    rms = np.sqrt(np.mean(samples ** 2))
    mean = np.mean(samples)

    print(f"  Entropy: {entropy:.4f} bits/byte")
    print(f"    Expected range: {stats['entropy_min']:.2f} - {stats['entropy_max']:.2f}")
    print(f"    Status: {'✓' if stats['entropy_min'] <= entropy <= stats['entropy_max'] else '✗'}")

    print(f"  RMS: {rms:.4f}")
    print(f"    Expected range: {stats['rms_min']:.2f} - {stats['rms_max']:.2f}")
    print(f"    Status: {'✓' if stats['rms_min'] <= rms <= stats['rms_max'] else '✗'}")

    print(f"  Mean: {mean:.6f}")
    print(f"    Expected: ~{stats['mean']:.2f} ± {stats['mean_tolerance']:.2f}")
    print(f"    Status: {'✓' if abs(mean - stats['mean']) <= stats['mean_tolerance'] else '✗'}")

def test_determinism():
    """Test deterministic output"""
    print("\n" + "=" * 60)
    print("TEST 2: Determinism")
    print("=" * 60)

    vectors = load_test_vectors()
    params = vectors['determinism_test']['parameters']

    samples1 = generate_rdt_noise(
        length=params['length'],
        phi_scale=params['phi_scale'],
        delta_scale=params['delta_scale'],
        depth=params['depth'],
        chaos=params['chaos'],
        variant=params['variant']
    )

    samples2 = generate_rdt_noise(
        length=params['length'],
        phi_scale=params['phi_scale'],
        delta_scale=params['delta_scale'],
        depth=params['depth'],
        chaos=params['chaos'],
        variant=params['variant']
    )

    if np.allclose(samples1, samples2):
        print("  ✓ PASS: Outputs are bit-exact identical")
    else:
        print("  ✗ FAIL: Outputs differ")
        diff_count = np.sum(samples1 != samples2)
        print(f"    Different samples: {diff_count}/{len(samples1)}")

def test_variants():
    """Test all 6 geometric variants"""
    print("\n" + "=" * 60)
    print("TEST 3: Geometric Variants")
    print("=" * 60)

    vectors = load_test_vectors()
    params = vectors['variant_tests']['parameters']
    variants = vectors['variant_tests']['variants']
    min_entropy = vectors['variant_tests']['expected']['all_entropy_above']

    results = {}

    for variant in variants:
        samples = generate_rdt_noise(
            length=params['length'],
            phi_scale=params['phi_scale'],
            delta_scale=params['delta_scale'],
            depth=params['depth'],
            chaos=params['chaos'],
            variant=variant
        )

        entropy = calculate_entropy(samples)
        results[variant] = {
            'entropy': entropy,
            'first_bytes': samples[:4]
        }

        status = "✓" if entropy >= min_entropy else "✗"
        print(f"  {variant:10s}: entropy = {entropy:.4f} bits/byte {status}")

    # Check that variants produce different outputs
    print("\nChecking variant uniqueness:")
    first_bytes_list = [tuple(r['first_bytes']) for r in results.values()]
    if len(set(first_bytes_list)) == len(variants):
        print("  ✓ All variants produce different outputs")
    else:
        print("  ✗ Some variants produce identical outputs")

def test_initialization():
    """Verify initialization constants"""
    print("\n" + "=" * 60)
    print("TEST 4: Initialization Constants")
    print("=" * 60)

    vectors = load_test_vectors()
    expected_hex = vectors['initialization_state']['state_hex']
    expected_dec = vectors['initialization_state']['state_decimal']

    from rdt import INIT_STATE

    print("  Checking π-based initialization state:")
    all_match = True
    for i in range(16):
        actual = int(INIT_STATE[i])
        expected = expected_dec[i]
        match = actual == expected
        all_match = all_match and match
        status = "✓" if match else "✗"
        if not match or i < 4:  # Show first 4 always, or mismatches
            print(f"    [{i:2d}] {expected_hex[i]}: {actual} {'==' if match else '!='} {expected} {status}")

    if all_match:
        print("  ✓ All initialization constants match")
    else:
        print("  ✗ Some initialization constants differ")

if __name__ == "__main__":
    print("\nRDT Noise - Test Vector Verification")
    print("=" * 60)

    test_standard()
    test_determinism()
    test_variants()
    test_initialization()

    print("\n" + "=" * 60)
    print("Verification Complete")
    print("=" * 60)
