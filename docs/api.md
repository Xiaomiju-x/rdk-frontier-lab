# CLI, API and schema stability

Version 0.1 is alpha. Incompatible changes require a documented minor release and
migration notes. Schema version 1 is explicit; unknown versions and extra receipt
fields are rejected.

| Command | Effect |
| --- | --- |
| `rdk-lab doctor` | Show tool capabilities; no device probe |
| `rdk-lab catalog [--target s600] [--group frontier] [--json]` | Read packaged historical metadata |
| `rdk-lab demo [--output NEW_FILE]` | Six-number arithmetic replay; optional new receipt |
| `rdk-lab verify MANIFEST` | Verify local paths, sizes and SHA-256 |
| `rdk-lab evaluate RECEIPT` | Check consistency and derive a scoped decision |
| `rdk-lab compare X5_JSON S100_JSON S600_JSON` | Same-contract independent BPU receipt comparison |

Use `python -m rdk_lab` as an equivalent prefix. No command executes submitted
model code. Exit 0: this operation's contract passed, not universally BPU/accuracy.
Exit 1: rejected input or a failing gate. Exit 2: incomplete result/comparison, or
argparse usage error; JSON versus usage text distinguishes them.

## Python API

```python
from pathlib import Path
from rdk_lab.io import verify_manifest
from rdk_lab.contracts import validate_result, compare_boards
from rdk_lab.numerics import compare_vectors, summarize_latencies

integrity = verify_manifest(Path("examples/fixture/manifest.json"))
metrics = compare_vectors([1.0, 2.0], [1.0, 2.0])
timing = summarize_latencies([1.0, 2.0, 3.0])
```

[Fixture schema](../schemas/fixture.schema.json) · [Result schema](../schemas/result.schema.json) · [Catalogue schema](../schemas/catalogue.schema.json)

JSON Schema describes syntax; the Python validator adds cross-field semantics
and rejects duplicate keys/non-finite decoded values.

## Decisions

- `DEMO_PASS/DEMO_FAIL`: synthetic host example only; cannot impersonate a board.
- `CPU_PASS/BPU_PASS/HYBRID_PASS`: submitted consistency gates pass, not attestation.
- `FAIL`: recorded failure, including numeric/task or cleanup failure.
- `INCOMPLETE`: some required gates remain unpassed.

Comparison requires three distinct targets/artifacts, BPU-only execution and
identical algorithm/source/fixture/contract/timing identities. It returns
`NEGATIVE`, `INCOMPLETE` or `CROSS_BOARD_CONTRACT_PASS`. None certifies that a
contributor's measurements are truthful or independently reproduced.

## Numerical definitions

- `relative_l2 = ||actual-golden||₂ / ||golden||₂`, not range-normalized NRMSE.
  Historical model-specific NRMSE retains its original definition.
- Cosine is normalized dot product. Both-zero vectors give 1; zero actual against
  nonzero golden gives 0. Nonzero actual against zero golden is rejected as undefined.
- `max_abs` is maximum absolute difference; overflow is rejected.
- Percentiles interpolate linearly at `(n-1)*q`, not nearest-rank.
- Throughput is `1000 / mean(latency_ms)`, not `1000 / P50`. Samples must be
  strictly positive and finite; failure placeholders of zero are forbidden.

PSNR, IoU, decoded keypoints and semantic matching remain model-specific gates;
generic vector cosine cannot replace them.
