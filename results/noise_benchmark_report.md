# RDT Noise Honest Benchmark

- length: `262144` samples
- seed: `1729`

| generator | time_ms(mean) | entropy | acf_lag1 | acf_mean_abs(1..32) | flatness | rms |
|---|---:|---:|---:|---:|---:|---:|
| rdt_standard | 317.176 | 7.9916 | -0.00241 | 0.00167 | 0.84553 | 0.58052 |
| rdt_chaos_seeded | 330.347 | 7.9915 | -0.00182 | 0.00149 | 0.84680 | 0.57892 |
| rdt_hybrid_fast | 176.603 | 7.9915 | 0.00275 | 0.00160 | 0.84574 | 0.57949 |
| white_uniform | 1.540 | 7.9936 | 0.00070 | 0.00170 | 0.84475 | 0.57824 |
| white_pink_filtered | 4.857 | 7.0230 | 0.86672 | 0.65437 | 0.69822 | 0.24762 |

## Findings
- RDT/white speed ratio: `205.945` ( >1 means RDT slower )
- RDT-white entropy delta: `-0.0020` bits/byte
- RDT-white acf abs delta: `-0.00002`
- Hybrid speedup vs RDT standard: `1.796x`
- Hybrid entropy delta vs RDT standard: `-0.0001` bits/byte
- Hybrid acf abs delta vs RDT standard: `-0.00007`
- Positive/negative values are reported directly; no claim of universal superiority.
