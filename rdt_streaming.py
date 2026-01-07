"""
RDT with Streaming Approach (Option C)
Testing continuous state refresh for higher entropy
"""

import numpy as np
from typing import Optional, Tuple

# Import constants from original
from rdt import (
    RPHI, RDELTA, PHI, GOLDEN_RATIO_INV, INIT_STATE, rotl32,
    calculate_entropy, calculate_autocorrelation, apply_color_filter
)


def generate_rdt_noise_streaming(
    length: int,
    phi_scale: float = 1.0,
    delta_scale: float = 1.0,
    depth: int = 4,
    chaos: float = 0.0,
    variant: str = "standard",
    sample_rate: int = 44100
) -> np.ndarray:
    """
    Generate RDT noise samples using streaming approach

    Instead of generating state once and cycling, this generates samples
    in blocks, feeding each block's output back into the diffusion process
    for continuous mixing and higher entropy.

    Parameters: Same as original generate_rdt_noise()
    """

    # Scale constants
    Rphi = RPHI * phi_scale
    Rdelta = RDELTA * delta_scale

    # Initialize state
    F = INIT_STATE.copy()
    F_prev = F.copy()

    # Allocate output
    samples = np.zeros(length, dtype=np.float32)

    # Process in blocks of 64 bytes
    block_size = 64  # 16 words * 4 bytes
    samples_generated = 0

    while samples_generated < length:
        # Recursive diffusion loop for this block
        for n in range(depth):
            # Split state into left (L) and right (R) halves
            L = F[:8].copy()
            R = F[8:].copy()

            # Compute local difference operator Δₙ
            delta = np.zeros(16, dtype=np.uint32)
            for i in range(16):
                diff = np.uint32(F[i] - F_prev[i])
                grad = np.uint32(F_prev[(i + 1) % 16] - F_prev[i])
                phi_term = np.uint32(grad / PHI)
                delta[i] = np.uint32(diff + phi_term)

            # Compute energy Eₙ with variant-specific coupling
            E = np.zeros(16, dtype=np.uint32)
            for i in range(8):
                # Variant-specific field coupling
                if variant == "standard":
                    coupling = np.uint32(L[i] ^ R[i])
                elif variant == "double":
                    c1 = np.uint32(L[i] ^ R[i])
                    c2 = np.uint32(L[(i+4)%8] ^ R[(i+4)%8])
                    coupling = np.uint32(c1 + c2)
                elif variant == "split":
                    if i % 2 == 0:
                        coupling = np.uint32(L[i] + R[i])
                    else:
                        coupling = np.uint32(L[i] ^ R[i])
                elif variant == "harmonic":
                    coupling = np.uint32((L[i] ^ R[i]) % 65521)
                elif variant == "twisted":
                    coupling = np.uint32(L[i] ^ R[(8-i-1)%8])
                elif variant == "resonant":
                    coupling = np.uint32(L[i] ^ R[i] ^ F_prev[i])
                else:
                    coupling = np.uint32(L[i] ^ R[i])

                # Compute energy for both halves
                E[i] = np.uint32(
                    int(Rphi) * F_prev[i] +
                    int(Rdelta) * delta[i] +
                    coupling
                )
                E[i + 8] = np.uint32(
                    int(Rphi) * F_prev[i + 8] +
                    int(Rdelta) * delta[i + 8] +
                    coupling
                )

            # Compute phase Φₙ
            Phi = np.zeros(16, dtype=np.uint32)
            for i in range(16):
                sin_term = np.sin(E[i] / max(Rdelta, 1e-10))
                cos_term = np.cos(E[i] / max(Rphi, 1e-10))
                phase = sin_term + cos_term
                Phi[i] = np.uint32(int(((phase + 2.0) / 4.0) * 31.0) & 31)

            # Apply diffusion operator D[Fₙ]
            F_next = np.zeros(16, dtype=np.uint32)
            for i in range(16):
                rot_amount = int((Phi[i] + n * 17 + i * 23) & 31)
                rotated = rotl32(E[i], rot_amount)
                F_next[i] = np.uint32(F_prev[i] ^ rotated)

            # Golden ratio permutation
            for i in range(16):
                F_next[i] = np.uint32(F_next[(i + 1) % 16] ^ GOLDEN_RATIO_INV)

            # Optional chaos injection
            if chaos > 0.0:
                for i in range(16):
                    noise = np.random.randint(0, 256, dtype=np.uint32)
                    chaos_mask = np.uint32(int(chaos * 255))
                    F_next[i] = np.uint32(F_next[i] ^ (noise & chaos_mask))

            # Update for next iteration
            F_prev = F.copy()
            F = F_next.copy()

        # Extract samples from current state
        samples_in_block = min(block_size, length - samples_generated)

        for byte_idx in range(samples_in_block):
            word_index = byte_idx % 16
            byte_in_word = (byte_idx // 16) % 4

            # Extract byte
            byte_val = (F[word_index] >> (byte_in_word * 8)) & 0xFF

            # Convert to [-1.0, 1.0]
            samples[samples_generated] = (byte_val / 127.5) - 1.0
            samples_generated += 1

        # STREAMING KEY: Feed current state forward for next block
        # This maintains continuous diffusion instead of cycling
        # F is already set to F_next from the diffusion loop
        # F_prev is already set to the previous F
        # This creates a chain where each block builds on the last

    return samples


# Test the streaming approach
if __name__ == "__main__":
    print("=" * 70)
    print("RDT STREAMING APPROACH TEST (Option C)")
    print("=" * 70)

    # Test 1: Generate with streaming approach
    print("\n1. Generating RDT with Streaming Approach...")
    samples_streaming = generate_rdt_noise_streaming(
        length=44100,
        phi_scale=1.0,
        delta_scale=1.0,
        depth=4,
        chaos=0.0,
        variant="standard"
    )

    # Calculate statistics
    entropy_streaming = calculate_entropy(samples_streaming)
    rms_streaming = np.sqrt(np.mean(samples_streaming ** 2))
    peak_streaming = np.max(np.abs(samples_streaming))
    mean_streaming = np.mean(samples_streaming)
    std_streaming = np.std(samples_streaming)

    print(f"\nStreaming Statistics:")
    print(f"  Length: {len(samples_streaming)} samples")
    print(f"  Entropy: {entropy_streaming:.4f} bits/byte")
    print(f"  RMS: {rms_streaming:.4f}")
    print(f"  Peak: {peak_streaming:.4f}")
    print(f"  Mean: {mean_streaming:.6f}")
    print(f"  Std Dev: {std_streaming:.4f}")

    # Test 2: Compare with original approach
    print("\n2. Comparing with Original Approach...")
    from rdt import generate_rdt_noise

    samples_original = generate_rdt_noise(
        length=44100,
        phi_scale=1.0,
        delta_scale=1.0,
        depth=4,
        chaos=0.0,
        variant="standard"
    )

    entropy_original = calculate_entropy(samples_original)
    mean_original = np.mean(samples_original)

    print(f"\nOriginal Statistics:")
    print(f"  Entropy: {entropy_original:.4f} bits/byte")
    print(f"  Mean: {mean_original:.6f}")

    print(f"\nImprovement:")
    print(f"  Entropy: {entropy_streaming:.4f} vs {entropy_original:.4f} (Δ{entropy_streaming - entropy_original:+.4f})")
    print(f"  Mean: {mean_streaming:.6f} vs {mean_original:.6f} (Δ{abs(mean_streaming):+.6f} vs {abs(mean_original):+.6f})")

    # Test 3: Check determinism
    print("\n3. Testing Determinism (streaming)...")
    samples_streaming2 = generate_rdt_noise_streaming(
        length=44100,
        phi_scale=1.0,
        delta_scale=1.0,
        depth=4,
        chaos=0.0,
        variant="standard"
    )

    if np.allclose(samples_streaming, samples_streaming2):
        print("  ✓ Deterministic: Identical output!")
    else:
        print("  ✗ Non-deterministic: Outputs differ")
        diff_count = np.sum(samples_streaming != samples_streaming2)
        print(f"    Different samples: {diff_count}/{len(samples_streaming)}")

    # Test 4: Autocorrelation
    print("\n4. Autocorrelation Analysis...")
    acf_streaming = calculate_autocorrelation(samples_streaming, max_lag=20)
    acf_original = calculate_autocorrelation(samples_original, max_lag=20)

    print(f"  Streaming ACF(1): {acf_streaming[1]:.4f}")
    print(f"  Original ACF(1):  {acf_original[1]:.4f}")
    print(f"  Streaming ACF(10): {acf_streaming[10]:.4f}")
    print(f"  Original ACF(10):  {acf_original[10]:.4f}")

    # Test 5: Check against target
    print("\n5. Target Comparison...")
    print(f"  Target entropy: 7.99-8.01 bits/byte")
    print(f"  Achieved: {entropy_streaming:.4f} bits/byte")

    if 7.99 <= entropy_streaming <= 8.01:
        print("  ✓ MEETS TARGET!")
    elif entropy_streaming >= 7.9:
        print("  ~ Close to target")
    else:
        print("  ✗ Below target")

    print("\n" + "=" * 70)
    print("Streaming Test Complete!")
    print("=" * 70)
