#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from rdt import generate_rdt_hybrid_noise, generate_rdt_noise


def test_deterministic_without_chaos() -> None:
    a = generate_rdt_noise(4096, chaos=0.0, depth=4, seed=123)
    b = generate_rdt_noise(4096, chaos=0.0, depth=4, seed=999)
    assert np.array_equal(a, b), "chaos=0 should be deterministic regardless of seed"


def test_seeded_chaos_reproducible() -> None:
    a = generate_rdt_noise(4096, chaos=0.3, depth=4, seed=123)
    b = generate_rdt_noise(4096, chaos=0.3, depth=4, seed=123)
    c = generate_rdt_noise(4096, chaos=0.3, depth=4, seed=124)
    assert np.array_equal(a, b), "same seed should reproduce"
    assert not np.array_equal(a, c), "different seeds should differ when chaos>0"


def test_output_range() -> None:
    x = generate_rdt_noise(8192, chaos=0.2, depth=4, seed=7)
    assert x.min() >= -1.0 - 1e-6
    assert x.max() <= 1.0 + 1e-6


def test_hybrid_reproducible() -> None:
    a = generate_rdt_hybrid_noise(4096, depth=4, refresh_blocks=8, seed=123)
    b = generate_rdt_hybrid_noise(4096, depth=4, refresh_blocks=8, seed=123)
    c = generate_rdt_hybrid_noise(4096, depth=4, refresh_blocks=8, seed=124)
    assert np.array_equal(a, b), "hybrid should reproduce with same seed"
    assert not np.array_equal(a, c), "hybrid should vary with seed"


def main() -> None:
    tests = [
        test_deterministic_without_chaos,
        test_seeded_chaos_reproducible,
        test_output_range,
        test_hybrid_reproducible,
    ]
    for t in tests:
        t()
        print(f"PASS: {t.__name__}")
    print("ALL TESTS PASSED")


if __name__ == "__main__":
    main()
