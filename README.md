# rdt-noise

RDT-based structured noise generator with reproducible baseline comparison.

## What this repo includes
- `generate_rdt_noise(...)`: RDT-style deterministic generator
- `generate_rdt_hybrid_noise(...)`: upgraded RDT + xorshift64* hybrid (faster stream, still RDT-seeded)
- Optional chaos mode with **seeded reproducibility**
- Conventional baseline: `generate_white_noise(...)`
- Honest benchmark report comparing RDT vs conventional noise

## Install

```bash
pip install -r requirements.txt
```

Only `numpy` is required for core generation.

## Quick usage

```python
from rdt import generate_rdt_noise

samples = generate_rdt_noise(
    length=44100,
    depth=4,
    chaos=0.0,     # deterministic mode
)
```

Seeded chaos mode:

```python
samples = generate_rdt_noise(length=44100, chaos=0.2, seed=1729)
```

Hybrid fast variant:

```python
from rdt import generate_rdt_hybrid_noise
samples = generate_rdt_hybrid_noise(length=44100, depth=4, refresh_blocks=8, seed=1729)
```

## Tests

```bash
python tests/run_tests.py
```

## Honest benchmark

```bash
python benchmarks/noise_benchmark.py --length 262144 --seed 1729
```

Outputs:
- `results/noise_benchmark_results.json`
- `results/noise_benchmark_report.md`

Metrics reported:
- generation time
- entropy (byte histogram)
- autocorrelation summary
- spectral flatness

## Scope
This is research code. The benchmark is intended to show both strengths and failure cases rather than force a universal win claim.

## License
MIT
