"""
RDT (Resonant Diffusion Transform) Noise Generator
A deterministic structured noise generation system

Author: Steven Reid
Date: October 24, 2025
License: MIT
"""

import numpy as np
from typing import Optional, Tuple

# Constants from the paper
RPHI = 12.0
RDELTA = 6.0 * np.sqrt(6.0)  # ≈ 14.6969384567
PHI = 1.6180339887498948
GOLDEN_RATIO_INV = 0x9E3779B9

# π-based initialization constants (hexadecimal from paper)
INIT_STATE = np.array([
    0x243F6A88, 0x85A308D3, 0x13198A2E, 0x03707344,
    0xA4093822, 0x299F31D0, 0x082EFA98, 0xEC4E6C89,
    0x452821E6, 0x38D01377, 0xBE5466CF, 0x34E90C6C,
    0xC0AC29B7, 0xC97C50DD, 0x3F84D5B5, 0xB5470917
], dtype=np.uint32)


def rotl32(x: np.uint32, n: int) -> np.uint32:
    """32-bit left rotation"""
    n = n & 31  # Ensure n is in range 0-31
    return np.uint32((x << n) | (x >> (32 - n)))


def generate_rdt_noise(
    length: int,
    phi_scale: float = 1.0,
    delta_scale: float = 1.0,
    depth: int = 4,
    chaos: float = 0.0,
    variant: str = "standard",
    sample_rate: int = 44100
) -> np.ndarray:
    """
    Generate RDT noise samples
    
    Parameters:
    -----------
    length : int
        Number of samples to generate
    phi_scale : float
        Scale factor for Rφ (default 1.0 = paper-accurate)
    delta_scale : float
        Scale factor for RΔ (default 1.0 = paper-accurate)
    depth : int
        Recursive iteration depth (recommended: 4-6)
    chaos : float
        Chaos injection level (0.0-1.0, 0.0 = deterministic)
    variant : str
        Geometric variant: "standard", "double", "split", "harmonic", "twisted", "resonant"
    sample_rate : int
        Sample rate in Hz (for reference, not used in generation)
    
    Returns:
    --------
    samples : np.ndarray
        Generated noise samples in range [-1.0, 1.0]
    """
    
    # Scale constants
    Rphi = RPHI * phi_scale
    Rdelta = RDELTA * delta_scale
    
    # Initialize state
    F = INIT_STATE.copy()
    F_prev = F.copy()
    
    # Recursive diffusion loop
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
                coupling = np.uint32(L[i] ^ R[i])  # Default to standard
            
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
            # Prevent division by zero
            sin_term = np.sin(E[i] / max(Rdelta, 1e-10))
            cos_term = np.cos(E[i] / max(Rphi, 1e-10))
            phase = sin_term + cos_term
            
            # Map phase [-2, 2] to rotation amount [0, 31]
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
    
    # Convert state to audio samples
    samples = np.zeros(length, dtype=np.float32)
    byte_index = 0
    
    for i in range(length):
        word_index = byte_index % 16
        byte_in_word = (byte_index // 16) % 4
        
        # Extract byte
        byte_val = (F[word_index] >> (byte_in_word * 8)) & 0xFF
        
        # Convert to [-1.0, 1.0]
        samples[i] = (byte_val / 127.5) - 1.0
        
        byte_index += 1
        
        # Refresh state if needed (cycle through state)
        if byte_index >= 64:  # 16 words * 4 bytes
            byte_index = 0
    
    return samples


def apply_color_filter(
    samples: np.ndarray,
    filter_type: str = "flat",
    sample_rate: int = 44100
) -> np.ndarray:
    """
    Apply spectral color filtering to noise
    
    Parameters:
    -----------
    samples : np.ndarray
        Input samples
    filter_type : str
        "flat" (white), "pink" (1/f), "brown" (1/f²), "blue" (f), "violet" (f²)
    sample_rate : int
        Sample rate in Hz
    
    Returns:
    --------
    filtered : np.ndarray
        Filtered samples
    """
    
    if filter_type == "flat":
        return samples
    
    # Compute FFT
    spectrum = np.fft.rfft(samples)
    freqs = np.fft.rfftfreq(len(samples), 1.0 / sample_rate)
    
    # Avoid division by zero
    freqs[0] = 1.0
    
    # Apply filter
    if filter_type == "pink":
        # 1/f
        spectrum *= 1.0 / np.sqrt(freqs)
    elif filter_type == "brown":
        # 1/f²
        spectrum *= 1.0 / freqs
    elif filter_type == "blue":
        # f
        spectrum *= np.sqrt(freqs)
    elif filter_type == "violet":
        # f²
        spectrum *= freqs
    
    # Inverse FFT
    filtered = np.fft.irfft(spectrum, n=len(samples))
    
    # Normalize to [-1, 1]
    max_val = np.max(np.abs(filtered))
    if max_val > 0:
        filtered = filtered / max_val
    
    return filtered.astype(np.float32)


def calculate_entropy(samples: np.ndarray, bins: int = 256) -> float:
    """
    Calculate Shannon entropy of samples
    
    Returns entropy in bits per sample
    """
    # Convert to byte-like values
    byte_samples = ((samples + 1.0) * 127.5).astype(np.uint8)
    
    # Calculate histogram
    hist, _ = np.histogram(byte_samples, bins=bins, range=(0, 255))
    
    # Calculate probabilities
    probs = hist / len(byte_samples)
    probs = probs[probs > 0]  # Remove zeros
    
    # Calculate entropy
    entropy = -np.sum(probs * np.log2(probs))
    
    return entropy


def calculate_autocorrelation(samples: np.ndarray, max_lag: int = 100) -> np.ndarray:
    """
    Calculate autocorrelation function
    
    Returns ACF values for lags 0 to max_lag
    """
    n = len(samples)
    mean = np.mean(samples)
    var = np.var(samples)
    
    if var == 0:
        return np.zeros(max_lag + 1)
    
    acf = np.zeros(max_lag + 1)
    
    for lag in range(max_lag + 1):
        if lag == 0:
            acf[0] = 1.0
        else:
            c = np.sum((samples[:n-lag] - mean) * (samples[lag:] - mean))
            acf[lag] = c / (n * var)
    
    return acf


# Example usage and test
if __name__ == "__main__":
    print("=" * 60)
    print("RDT Noise Generator - Python Implementation")
    print("=" * 60)
    
    # Generate paper-accurate RDT
    print("\n1. Generating Pure RDT (paper-accurate)...")
    samples = generate_rdt_noise(
        length=44100,  # 1 second at 44.1kHz
        phi_scale=1.0,
        delta_scale=1.0,
        depth=4,
        chaos=0.0,
        variant="standard"
    )
    
    # Calculate statistics
    entropy = calculate_entropy(samples)
    rms = np.sqrt(np.mean(samples ** 2))
    peak = np.max(np.abs(samples))
    mean = np.mean(samples)
    std = np.std(samples)
    
    print(f"\nStatistics:")
    print(f"  Length: {len(samples)} samples")
    print(f"  Entropy: {entropy:.4f} bits/byte")
    print(f"  RMS: {rms:.4f}")
    print(f"  Peak: {peak:.4f}")
    print(f"  Mean: {mean:.6f}")
    print(f"  Std Dev: {std:.4f}")
    
    # Autocorrelation
    acf = calculate_autocorrelation(samples, max_lag=20)
    print(f"\nAutocorrelation:")
    print(f"  ACF(0): {acf[0]:.4f}")
    print(f"  ACF(1): {acf[1]:.4f}")
    print(f"  ACF(10): {acf[10]:.4f}")
    
    # Test determinism
    print("\n2. Testing determinism...")
    samples2 = generate_rdt_noise(
        length=44100,
        phi_scale=1.0,
        delta_scale=1.0,
        depth=4,
        chaos=0.0,
        variant="standard"
    )
    
    if np.allclose(samples, samples2):
        print("  ✓ Deterministic: Identical output!")
    else:
        print("  ✗ Non-deterministic: Outputs differ")
    
    # Test variants
    print("\n3. Generating all 6 variants...")
    variants = ["standard", "double", "split", "harmonic", "twisted", "resonant"]
    
    for v in variants:
        v_samples = generate_rdt_noise(length=1000, variant=v)
        v_entropy = calculate_entropy(v_samples)
        v_acf = calculate_autocorrelation(v_samples, max_lag=10)
        print(f"  {v:10s}: entropy={v_entropy:.4f}, ACF(10)={v_acf[10]:.4f}")
    
    # Save example
    print("\n4. Saving example WAV file...")
    try:
        from scipy.io import wavfile
        # Generate 3 seconds
        audio = generate_rdt_noise(length=132300, depth=4)
        # Convert to 16-bit PCM
        audio_int = (audio * 32767).astype(np.int16)
        wavfile.write("rdt_example.wav", 44100, audio_int)
        print("  ✓ Saved: rdt_example.wav")
    except ImportError:
        print("  (scipy not available, skipping WAV export)")
    
    print("\n" + "=" * 60)
    print("✓ All tests complete!")
    print("=" * 60)
