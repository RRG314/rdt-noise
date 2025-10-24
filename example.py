#!/usr/bin/env python3
"""
Simple RDT Noise Example
Demonstrates basic usage of the RDT noise generator
"""

import numpy as np
from rdt import generate_rdt_noise, apply_color_filter, calculate_entropy

def main():
    print("RDT Noise - Simple Example")
    print("=" * 50)
    
    # Example 1: Generate pure RDT
    print("\n1. Pure RDT Noise")
    print("-" * 50)
    
    samples = generate_rdt_noise(
        length=44100,      # 1 second at 44.1kHz
        phi_scale=1.0,     # Paper-accurate
        delta_scale=1.0,   # Paper-accurate
        depth=4,           # Recommended depth
        chaos=0.0          # Deterministic
    )
    
    print(f"Generated {len(samples)} samples")
    print(f"Entropy: {calculate_entropy(samples):.4f} bits/byte")
    print(f"RMS Level: {np.sqrt(np.mean(samples**2)):.4f}")
    
    # Example 2: Generate pink noise
    print("\n2. Pink RDT Noise")
    print("-" * 50)
    
    pink_samples = generate_rdt_noise(length=44100)
    pink_samples = apply_color_filter(pink_samples, filter_type="pink")
    
    print(f"Generated {len(pink_samples)} samples")
    print(f"Filter: Pink (1/f)")
    
    # Example 3: Try different variants
    print("\n3. Geometric Variants")
    print("-" * 50)
    
    variants = ["standard", "harmonic", "resonant"]
    
    for variant in variants:
        v_samples = generate_rdt_noise(length=10000, variant=variant)
        entropy = calculate_entropy(v_samples)
        print(f"{variant:10s}: entropy = {entropy:.4f} bits/byte")
    
    # Example 4: Parameter exploration
    print("\n4. Parameter Exploration")
    print("-" * 50)
    
    phi_values = [0.5, 1.0, 1.5]
    
    for phi in phi_values:
        p_samples = generate_rdt_noise(length=10000, phi_scale=phi)
        entropy = calculate_entropy(p_samples)
        print(f"φ-scale = {phi:.1f}: entropy = {entropy:.4f} bits/byte")
    
    print("\n" + "=" * 50)
    print("✓ Examples complete!")
    
    # Optional: Save audio file
    try:
        from scipy.io import wavfile
        print("\nSaving audio example...")
        audio = generate_rdt_noise(length=132300)  # 3 seconds
        audio_int = (audio * 32767).astype(np.int16)
        wavfile.write("rdt_simple_example.wav", 44100, audio_int)
        print("✓ Saved: rdt_simple_example.wav")
    except ImportError:
        print("\n(Install scipy to save audio files)")

if __name__ == "__main__":
    main()
