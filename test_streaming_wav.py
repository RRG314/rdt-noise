#!/usr/bin/env python3
"""
Generate WAV file with streaming approach and compare
"""

import numpy as np
from rdt_streaming import generate_rdt_noise_streaming
from rdt import calculate_entropy
from scipy.io import wavfile

print("=" * 70)
print("STREAMING WAV GENERATION TEST")
print("=" * 70)

# Generate 3 seconds with streaming
print("\nGenerating 3 seconds (132300 samples) with streaming approach...")
samples = generate_rdt_noise_streaming(
    length=132300,
    depth=4,
    chaos=0.0,
    variant="standard"
)

# Statistics
entropy = calculate_entropy(samples)
rms = np.sqrt(np.mean(samples ** 2))
mean = np.mean(samples)
peak = np.max(np.abs(samples))

print(f"\nStatistics:")
print(f"  Length: {len(samples)} samples (3 seconds)")
print(f"  Entropy: {entropy:.4f} bits/byte")
print(f"  RMS: {rms:.4f}")
print(f"  Peak: {peak:.4f}")
print(f"  Mean: {mean:.6f}")

# Save WAV file
print(f"\nSaving WAV file...")
audio_int = (samples * 32767).astype(np.int16)
wavfile.write("rdt_streaming.wav", 44100, audio_int)
print(f"  ✓ Saved: rdt_streaming.wav")

# Compare file sizes
import os
original_size = os.path.getsize("rdt_example.wav")
streaming_size = os.path.getsize("rdt_streaming.wav")

print(f"\nFile sizes:")
print(f"  Original: {original_size} bytes")
print(f"  Streaming: {streaming_size} bytes")
print(f"  Match: {original_size == streaming_size}")

print("\n" + "=" * 70)
print("WAV GENERATION COMPLETE")
print("=" * 70)
