"""
RDT (Resonant Diffusion Transform) Noise Generator.

This module is research-oriented and deterministic by default.
"""

from __future__ import annotations

import math
from typing import Optional

import numpy as np


RPHI = 12.0
RDELTA = 6.0 * math.sqrt(6.0)
PHI = 1.6180339887498948
GOLDEN_RATIO_INV = 0x9E3779B9

INIT_STATE = np.array(
    [
        0x243F6A88,
        0x85A308D3,
        0x13198A2E,
        0x03707344,
        0xA4093822,
        0x299F31D0,
        0x082EFA98,
        0xEC4E6C89,
        0x452821E6,
        0x38D01377,
        0xBE5466CF,
        0x34E90C6C,
        0xC0AC29B7,
        0xC97C50DD,
        0x3F84D5B5,
        0xB5470917,
    ],
    dtype=np.uint32,
)


def _u32(v: int) -> np.uint32:
    return np.uint32(v & 0xFFFFFFFF)


def rotl32(x: np.uint32, n: int) -> np.uint32:
    """32-bit rotate-left with defined behavior for n=0."""
    n &= 31
    if n == 0:
        return np.uint32(x)
    xi = int(x)
    return _u32((xi << n) | (xi >> (32 - n)))


def _advance_state(
    F: np.ndarray,
    F_prev: np.ndarray,
    step: int,
    Rphi: float,
    Rdelta: float,
    variant: str,
    chaos: float,
    rng: np.random.Generator,
) -> np.ndarray:
    """One diffusion step from (F_prev, F) -> F_next."""
    L = F[:8].copy()
    R = F[8:].copy()

    delta = np.zeros(16, dtype=np.uint32)
    for i in range(16):
        fi = int(F[i])
        fpi = int(F_prev[i])
        fpn = int(F_prev[(i + 1) % 16])
        diff = fi - fpi
        grad = fpn - fpi
        phi_term = int(grad / PHI)
        delta[i] = _u32(diff + phi_term)

    E = np.zeros(16, dtype=np.uint32)
    for i in range(8):
        if variant == "standard":
            coupling = int(L[i]) ^ int(R[i])
        elif variant == "double":
            c1 = int(L[i]) ^ int(R[i])
            c2 = int(L[(i + 4) % 8]) ^ int(R[(i + 4) % 8])
            coupling = c1 + c2
        elif variant == "split":
            coupling = int(L[i]) + int(R[i]) if (i % 2 == 0) else (int(L[i]) ^ int(R[i]))
        elif variant == "harmonic":
            coupling = (int(L[i]) ^ int(R[i])) % 65521
        elif variant == "twisted":
            coupling = int(L[i]) ^ int(R[(8 - i - 1) % 8])
        elif variant == "resonant":
            coupling = int(L[i]) ^ int(R[i]) ^ int(F_prev[i])
        else:
            coupling = int(L[i]) ^ int(R[i])

        e0 = int(Rphi) * int(F_prev[i]) + int(Rdelta) * int(delta[i]) + coupling
        e1 = int(Rphi) * int(F_prev[i + 8]) + int(Rdelta) * int(delta[i + 8]) + coupling
        E[i] = _u32(e0)
        E[i + 8] = _u32(e1)

    phase_rot = np.zeros(16, dtype=np.uint32)
    for i in range(16):
        ei = int(E[i])
        sin_term = math.sin(ei / max(Rdelta, 1e-10))
        cos_term = math.cos(ei / max(Rphi, 1e-10))
        phase = sin_term + cos_term
        phase_rot[i] = np.uint32(int(((phase + 2.0) / 4.0) * 31.0) & 31)

    F_next = np.zeros(16, dtype=np.uint32)
    for i in range(16):
        rot_amount = int((int(phase_rot[i]) + step * 17 + i * 23) & 31)
        rotated = rotl32(E[i], rot_amount)
        F_next[i] = _u32(int(F_prev[i]) ^ int(rotated))

    perm = np.zeros(16, dtype=np.uint32)
    for i in range(16):
        perm[i] = _u32(int(F_next[(i + 1) % 16]) ^ GOLDEN_RATIO_INV)
    F_next = perm

    if chaos > 0.0:
        chaos_mask = np.uint32(int(chaos * 255.0))
        noise = rng.integers(0, 256, size=16, dtype=np.uint32)
        F_next ^= (noise & chaos_mask)

    return F_next


def generate_rdt_noise(
    length: int,
    phi_scale: float = 1.0,
    delta_scale: float = 1.0,
    depth: int = 4,
    chaos: float = 0.0,
    variant: str = "standard",
    sample_rate: int = 44100,
    seed: Optional[int] = None,
) -> np.ndarray:
    """
    Generate RDT noise samples in [-1, 1].

    `seed` only affects chaos injection (`chaos > 0`).
    When `chaos == 0`, output is deterministic regardless of seed.
    """
    if length < 1:
        return np.zeros(0, dtype=np.float32)
    if depth < 0:
        raise ValueError("depth must be >= 0")
    if not (0.0 <= chaos <= 1.0):
        raise ValueError("chaos must be in [0,1]")

    _ = sample_rate  # retained for API compatibility

    Rphi = RPHI * float(phi_scale)
    Rdelta = RDELTA * float(delta_scale)

    F = INIT_STATE.copy()
    F_prev = F.copy()
    rng = np.random.default_rng(seed)

    step = 0
    for _ in range(depth):
        F_next = _advance_state(F, F_prev, step, Rphi, Rdelta, variant, chaos, rng)
        F_prev = F
        F = F_next
        step += 1

    samples = np.zeros(length, dtype=np.float32)
    byte_index = 0
    for i in range(length):
        word_index = byte_index % 16
        byte_in_word = (byte_index // 16) % 4
        byte_val = (int(F[word_index]) >> (byte_in_word * 8)) & 0xFF
        samples[i] = (byte_val / 127.5) - 1.0
        byte_index += 1
        if byte_index >= 64:
            byte_index = 0
            F_next = _advance_state(F, F_prev, step, Rphi, Rdelta, variant, chaos, rng)
            F_prev = F
            F = F_next
            step += 1

    return samples


def _xorshift64star_step(state: int) -> int:
    state &= 0xFFFFFFFFFFFFFFFF
    state ^= (state >> 12) & 0xFFFFFFFFFFFFFFFF
    state ^= (state << 25) & 0xFFFFFFFFFFFFFFFF
    state ^= (state >> 27) & 0xFFFFFFFFFFFFFFFF
    return (state * 0x2545F4914F6CDD1D) & 0xFFFFFFFFFFFFFFFF


def generate_rdt_hybrid_noise(
    length: int,
    *,
    depth: int = 4,
    refresh_blocks: int = 8,
    chaos: float = 0.0,
    seed: Optional[int] = None,
) -> np.ndarray:
    """
    Faster hybrid variant: RDT state scheduler + xorshift64* stream core.

    Known method used: hybridize a heavy nonlinear generator with a fast stream
    generator, periodically reseeded/perturbed by the heavy core.
    """
    if length < 1:
        return np.zeros(0, dtype=np.float32)
    if refresh_blocks < 1:
        raise ValueError("refresh_blocks must be >=1")

    Rphi = RPHI
    Rdelta = RDELTA
    F = INIT_STATE.copy()
    F_prev = F.copy()
    rng = np.random.default_rng(seed)
    step = 0

    for _ in range(max(0, depth)):
        F_next = _advance_state(F, F_prev, step, Rphi, Rdelta, "standard", chaos, rng)
        F_prev = F
        F = F_next
        step += 1

    seed64 = 0
    for w in F:
        seed64 ^= int(w)
        seed64 = _xorshift64star_step(seed64)
    if seed is not None:
        seed64 ^= int(seed) & 0xFFFFFFFFFFFFFFFF
    if seed64 == 0:
        seed64 = 0x9E3779B97F4A7C15

    out = np.empty(length, dtype=np.float32)
    block_counter = 0
    for i in range(length):
        if i % 64 == 0:
            block_counter += 1
            if block_counter % refresh_blocks == 0:
                F_next = _advance_state(F, F_prev, step, Rphi, Rdelta, "standard", chaos, rng)
                F_prev = F
                F = F_next
                step += 1
                mix = 0
                for w in F:
                    mix ^= int(w)
                seed64 ^= mix & 0xFFFFFFFFFFFFFFFF
                seed64 = _xorshift64star_step(seed64)

        seed64 = _xorshift64star_step(seed64)
        byte_val = seed64 & 0xFF
        out[i] = (byte_val / 127.5) - 1.0

    return out


def generate_white_noise(length: int, seed: Optional[int] = None) -> np.ndarray:
    """Conventional baseline: IID uniform white noise in [-1, 1]."""
    rng = np.random.default_rng(seed)
    return rng.uniform(-1.0, 1.0, size=length).astype(np.float32)


def apply_color_filter(samples: np.ndarray, filter_type: str = "flat", sample_rate: int = 44100) -> np.ndarray:
    if filter_type == "flat":
        return samples.astype(np.float32, copy=False)

    spectrum = np.fft.rfft(samples)
    freqs = np.fft.rfftfreq(len(samples), 1.0 / sample_rate)
    freqs[0] = 1.0

    if filter_type == "pink":
        spectrum *= 1.0 / np.sqrt(freqs)
    elif filter_type == "brown":
        spectrum *= 1.0 / freqs
    elif filter_type == "blue":
        spectrum *= np.sqrt(freqs)
    elif filter_type == "violet":
        spectrum *= freqs
    else:
        raise ValueError(f"Unknown filter_type: {filter_type}")

    filtered = np.fft.irfft(spectrum, n=len(samples))
    max_val = float(np.max(np.abs(filtered)))
    if max_val > 0.0:
        filtered = filtered / max_val
    return filtered.astype(np.float32)


def calculate_entropy(samples: np.ndarray, bins: int = 256) -> float:
    byte_samples = ((samples + 1.0) * 127.5).clip(0, 255).astype(np.uint8)
    hist, _ = np.histogram(byte_samples, bins=bins, range=(0, 255))
    probs = hist / max(1, len(byte_samples))
    probs = probs[probs > 0]
    return float(-np.sum(probs * np.log2(probs)))


def calculate_autocorrelation(samples: np.ndarray, max_lag: int = 100) -> np.ndarray:
    n = len(samples)
    mean = float(np.mean(samples))
    var = float(np.var(samples))
    if var == 0.0:
        return np.zeros(max_lag + 1, dtype=np.float64)

    acf = np.zeros(max_lag + 1, dtype=np.float64)
    acf[0] = 1.0
    for lag in range(1, max_lag + 1):
        c = np.sum((samples[: n - lag] - mean) * (samples[lag:] - mean))
        acf[lag] = float(c / (n * var))
    return acf


if __name__ == "__main__":
    s = generate_rdt_noise(length=44100, depth=4, chaos=0.0)
    print("RDT entropy:", calculate_entropy(s))
    s2 = generate_rdt_noise(length=44100, depth=4, chaos=0.2, seed=123)
    print("RDT entropy (chaos):", calculate_entropy(s2))
