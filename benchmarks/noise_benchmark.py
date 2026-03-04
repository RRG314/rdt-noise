#!/usr/bin/env python3
"""Honest RDT-noise benchmark against conventional noise baselines."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import time

import numpy as np

import sys
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from rdt import (
    apply_color_filter,
    calculate_autocorrelation,
    calculate_entropy,
    generate_rdt_hybrid_noise,
    generate_rdt_noise,
    generate_white_noise,
)



def spectral_flatness(samples: np.ndarray) -> float:
    spec = np.abs(np.fft.rfft(samples)) + 1e-12
    geo = np.exp(np.mean(np.log(spec)))
    arith = np.mean(spec)
    return float(geo / arith)



def eval_generator(name: str, fn, length: int, repeats: int = 3):
    times = []
    out = None
    for _ in range(repeats):
        t0 = time.perf_counter()
        out = fn(length)
        t1 = time.perf_counter()
        times.append((t1 - t0) * 1000.0)
    assert out is not None

    acf = calculate_autocorrelation(out, max_lag=32)
    acf_mean_abs = float(np.mean(np.abs(acf[1:])))

    return {
        "name": name,
        "time_ms_mean": float(np.mean(times)),
        "time_ms_min": float(np.min(times)),
        "entropy_bits_per_byte": float(calculate_entropy(out)),
        "acf_lag1": float(acf[1]),
        "acf_mean_abs_1_32": acf_mean_abs,
        "spectral_flatness": spectral_flatness(out),
        "rms": float(np.sqrt(np.mean(out * out))),
    }



def run(length: int, seed: int) -> dict[str, object]:
    baselines = [
        (
            "rdt_standard",
            lambda n: generate_rdt_noise(n, depth=4, chaos=0.0, seed=seed),
        ),
        (
            "rdt_chaos_seeded",
            lambda n: generate_rdt_noise(n, depth=4, chaos=0.2, seed=seed),
        ),
        (
            "rdt_hybrid_fast",
            lambda n: generate_rdt_hybrid_noise(n, depth=4, refresh_blocks=8, chaos=0.0, seed=seed),
        ),
        (
            "white_uniform",
            lambda n: generate_white_noise(n, seed=seed),
        ),
        (
            "white_pink_filtered",
            lambda n: apply_color_filter(generate_white_noise(n, seed=seed), "pink"),
        ),
    ]

    results = [eval_generator(name, fn, length) for name, fn in baselines]

    # Failure/superiority notes relative to conventional white noise.
    by_name = {r["name"]: r for r in results}
    white = by_name["white_uniform"]
    rdt = by_name["rdt_standard"]

    findings = {
        "rdt_vs_white_speed_ratio": rdt["time_ms_mean"] / max(1e-9, white["time_ms_mean"]),
        "rdt_vs_white_entropy_delta": rdt["entropy_bits_per_byte"] - white["entropy_bits_per_byte"],
        "rdt_vs_white_acf_abs_delta": rdt["acf_mean_abs_1_32"] - white["acf_mean_abs_1_32"],
    }
    if "rdt_hybrid_fast" in by_name:
        hy = by_name["rdt_hybrid_fast"]
        findings["hybrid_speedup_vs_rdt"] = rdt["time_ms_mean"] / max(1e-9, hy["time_ms_mean"])
        findings["hybrid_entropy_delta_vs_rdt"] = hy["entropy_bits_per_byte"] - rdt["entropy_bits_per_byte"]
        findings["hybrid_acf_abs_delta_vs_rdt"] = hy["acf_mean_abs_1_32"] - rdt["acf_mean_abs_1_32"]

    return {
        "length": length,
        "seed": seed,
        "results": results,
        "findings": findings,
    }



def to_markdown(obj: dict[str, object]) -> str:
    lines = ["# RDT Noise Honest Benchmark", "", f"- length: `{obj['length']}` samples", f"- seed: `{obj['seed']}`", ""]
    lines.append("| generator | time_ms(mean) | entropy | acf_lag1 | acf_mean_abs(1..32) | flatness | rms |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|")
    for r in obj["results"]:
        lines.append(
            f"| {r['name']} | {r['time_ms_mean']:.3f} | {r['entropy_bits_per_byte']:.4f} | "
            f"{r['acf_lag1']:.5f} | {r['acf_mean_abs_1_32']:.5f} | {r['spectral_flatness']:.5f} | {r['rms']:.5f} |"
        )

    f = obj["findings"]
    lines.append("")
    lines.append("## Findings")
    lines.append(f"- RDT/white speed ratio: `{f['rdt_vs_white_speed_ratio']:.3f}` ( >1 means RDT slower )")
    lines.append(f"- RDT-white entropy delta: `{f['rdt_vs_white_entropy_delta']:.4f}` bits/byte")
    lines.append(f"- RDT-white acf abs delta: `{f['rdt_vs_white_acf_abs_delta']:.5f}`")
    if "hybrid_speedup_vs_rdt" in f:
        lines.append(f"- Hybrid speedup vs RDT standard: `{f['hybrid_speedup_vs_rdt']:.3f}x`")
        lines.append(f"- Hybrid entropy delta vs RDT standard: `{f['hybrid_entropy_delta_vs_rdt']:.4f}` bits/byte")
        lines.append(f"- Hybrid acf abs delta vs RDT standard: `{f['hybrid_acf_abs_delta_vs_rdt']:.5f}`")
    lines.append("- Positive/negative values are reported directly; no claim of universal superiority.")
    return "\n".join(lines) + "\n"



def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--length", type=int, default=262144)
    parser.add_argument("--seed", type=int, default=1729)
    parser.add_argument("--out", type=Path, default=ROOT / "results" / "noise_benchmark_results.json")
    parser.add_argument("--report", type=Path, default=ROOT / "results" / "noise_benchmark_report.md")
    args = parser.parse_args()

    obj = run(length=args.length, seed=args.seed)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(obj, indent=2), encoding="utf-8")
    args.report.write_text(to_markdown(obj), encoding="utf-8")
    print(f"Wrote JSON: {args.out}")
    print(f"Wrote report: {args.report}")


if __name__ == "__main__":
    main()
