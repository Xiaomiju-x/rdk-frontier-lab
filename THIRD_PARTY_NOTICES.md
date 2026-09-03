# Third-party and asset notices

## Code shipped here

| Component | Origin | License |
| --- | --- | --- |
| Public CLI, contracts, metrics and publication tools | First-party public implementation informed by the laboratory's validation work | Apache-2.0 |
| `rdk_lab/geometry.py` | Public NumPy port of the first-party C14 weighted Kabsch partition | MIT; [grant](recipes/weighted_kabsch_6d/LICENSE) |
| `recipes/weighted_kabsch_6d/neural_reference.py` | First-party C14 scorer/geometry source, preserved with attribution | MIT; same grant |
| Scalar fixture and analytic geometry inputs | First-party generated numbers, no third-party media | [CC0-1.0](LICENSES/CC0-1.0.txt) |
| Hero SVG | Original first-party vector artwork | Apache-2.0 |

The core runtime depends only on the Python standard library. Optional NumPy and
development tools retain their own licenses; installing them does not make their
binaries part of this source release. The software bill of materials distinguishes
first-party distributed files from external requirements.

## Referenced, not redistributed

The [upstream registry](registry/upstreams.json) records references to D-Robotics,
NVIDIA, Ascend, Google, Meta, IBM, OpenMMLab and other projects. Their source trees,
weights, datasets and platform binaries are **not** included. Model names and
reported measurements do not grant permission to download, redistribute or deploy
those assets.

[Asset-review notes](registry/asset_review.json) preserve historical engineering
findings. They are not legal advice, a definitive license opinion, or a replacement
for the exact upstream terms. A code license does not automatically license the
checkpoint, training data, evaluation inputs, fonts or audio.

In particular, source-subgraph probes and first-party miniature substitutes must
not be represented as the upstream trained FoundationPose, BEVFusion, GR00T,
SAM, V-JEPA or other full model. See the exact catalogue note for each boundary.

If you identify missing attribution or a rights issue, contact the maintainer
before posting restricted material. Corrections are tracked in version control.
