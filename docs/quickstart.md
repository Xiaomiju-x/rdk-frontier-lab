# Quickstart

## 1. No installation, no devices

Obtain this repository from its GitHub release or clone it:

```bash
git clone https://github.com/Xiaomiju-x/rdk-frontier-lab.git
cd rdk-frontier-lab
python -m rdk_lab doctor
python -m rdk_lab demo
python -m rdk_lab verify examples/fixture/manifest.json
```

Python 3.10–3.14 is supported. These commands use only the standard library.
`doctor` reports tooling capability, **not board health**. The scalar demo is six
arithmetic outputs, not an AI model benchmark. Expected decisions are `DEMO_PASS`
and `INTEGRITY_PASS`; neither certifies BPU execution.

## 2. Keep an immutable receipt

```bash
python -m rdk_lab demo --output local/demo-v1.json
python -m rdk_lab evaluate local/demo-v1.json
```

Reusing the filename fails. Use a fresh name; do not overwrite evidence to make
a new attempt look like an old one. `local/` is ignored. Atomic publication
requires hard-link support; unsupported filesystems fail rather than silently replace.

## 3. Inspect observations

```bash
python -m rdk_lab catalog --group official
python -m rdk_lab catalog --target s100 --json
```

`--target` filters intended targets, not successful deployments. Read each status
and scope note. Official S100 Depth Anything V2 and the separately exported
DAv2-Small numerical failure are different experiments.

## 4. Optional installation

```bash
python -m venv .venv
```

Activate with `source .venv/bin/activate` on Linux/macOS,
`.venv\Scripts\Activate.ps1` in PowerShell, or `.venv\Scripts\activate.bat` in CMD.
If policy blocks activation scripts, call the environment's Python directly;
do not weaken system execution policies.

```bash
python -m pip install .
rdk-lab doctor
```

Build tooling may be downloaded. Fully offline users can use source commands,
or install a reviewed release wheel with `python -m pip install --no-deps`
followed by its local filename. This project is not on PyPI in version 0.1.0.

## 5. Optional real geometry

```bash
python -m pip install ".[geometry]"
python examples/geometry_demo.py
```

This installs NumPy and executes weighted Kabsch on eight synthetic point pairs.
No Torch, camera, checkpoint or training is used. Read [the recipe](../recipes/weighted_kabsch_6d/README.md).

[API and exit codes](api.md) · [Results](results.md) · [Contributing](../CONTRIBUTING.md)
