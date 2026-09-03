# Offline examples

From the repository root:

```bash
python -m rdk_lab demo
python -m rdk_lab demo --output local/demo-receipt.json
python -m rdk_lab evaluate local/demo-receipt.json
python -m rdk_lab verify examples/fixture/manifest.json
```

The output path must be new. Re-running with the same path is intentionally
rejected, not silently overwritten. Use another filename to keep both results.

The scalar example is a six-number arithmetic contract, **not a trained model**.
It reports no latency, hardware or public-dataset accuracy. The fixture contains
only first-party synthetic numbers under CC0-1.0.

For actual geometry, install the optional NumPy extra and run
[`geometry_demo.py`](geometry_demo.py). It also uses synthetic data and no devices.
