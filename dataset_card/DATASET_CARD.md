# LAFC-Evict Dataset Card

## Name

**LAFC-Evict: Counterfactual Supervision for Learned Cache Eviction**

## Current public release

The current public release is the **v0.2 published preview**, available on
Hugging Face and archived on Zenodo:

- https://huggingface.co/datasets/SoroushVahidi/lafc-evict
- https://doi.org/10.5281/zenodo.21895844

It contains Wiki2018-derived pseudonymized supervision, two configs, and
4,800,000 rows under CC0 1.0.

## Associated Paper / Preprint

This dataset release accompanies the public preprint/manuscript:  
**Decision-aligned eviction-value prediction for robust learning-augmented caching**  
Soroush Vahidi.  
Available at SSRN 6636732.  
Status: public preprint; manuscript under peer review.

The paper describes the learning-augmented caching setting and the experiments that motivated this dataset release. This repository provides dataset-release artifacts, schemas, validation tools, benchmark views, and reproducibility utilities. When using the data artifact, cite both the paper/preprint and the current dataset release DOI.

## What this repository releases

This repository prepares a public dataset package for cache-eviction supervision. It releases **generated counterfactual supervision labels and benchmark views**, not upstream raw traces. The canonical unit is:

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

## Raw traces and citation

Raw traces are external source artifacts and must be cited separately according to their own provenance, attribution, and licensing terms.

## What is not included in GitHub

- raw traces,
- processed traces,
- large generated candidate tables,
- model files,
- training logs,
- Slurm artifacts.

Public release artifacts are hosted separately from this code repository. The
canonical publication repository is `lafc-evict-dataset`; scientific/source
data remain in `Augmented-caching`.

## Current public scope

The published v0.2 release contains only Wiki2018-derived rows. CloudPhysics,
MetaCDN, MetaKV, and Twemcache are not currently cleared for public release.
CitiBike and Brightkite remain blocked.

## Intended benchmark views

- candidate-row regression or ranking tasks,
- decision-level evaluation,
- pairwise preference evaluation within each eviction decision.

## Current status

The v0.1-open trees are historical unpublished local staging artifacts. The
v0.3 tree is a locally validated candidate and is not published. Future
releases still require:

- upstream trace-license review,
- redistribution review per trace family,
- host selection and persistent identifiers,
- release-specific manifests and checksums.
