# LAFC-Evict Dataset Card

## Name

**LAFC-Evict: Counterfactual Supervision for Learned Cache Eviction**

## What this repository releases

This repository prepares a public dataset package for cache-eviction supervision. The canonical unit is:

- one candidate victim,
- at one full-cache miss eviction decision,
- for one cache capacity,
- for one finite horizon.

Each row combines:

- trace provenance fields,
- decision identifiers,
- candidate features,
- counterfactual supervision labels.

## What the main `v1` label means

The primary `v1` label is:

- `y_loss`: finite-horizon counterfactual miss count under **LRU continuation** after forcing eviction of the candidate victim.
- `y_value = -y_loss`.

This is a finite-window supervision signal. It should **not** be described as offline-optimal unless a different label family is explicitly released and documented.

## What is not included in GitHub

- raw traces,
- processed traces,
- large generated candidate tables,
- model files,
- training logs,
- Slurm artifacts.

Public release artifacts should be hosted separately, for example on Hugging Face or Zenodo.

## Intended benchmark views

- candidate-row regression or ranking tasks,
- decision-level evaluation,
- pairwise preference evaluation within each eviction decision.

## Current status

This repository is a release scaffold. Final public releases still require:

- upstream trace-license review,
- redistribution review per trace family,
- host selection and persistent identifiers,
- release-specific manifests and checksums.
