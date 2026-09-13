# LAFC-Evict Dataset Card

## Name

**LAFC-Evict: Counterfactual Supervision for Learned Cache Eviction**

## Current public release

The current public release is **v0.3** (corrected 2026-09-12; this section
previously said v0.2), available on Hugging Face:

- https://huggingface.co/datasets/SoroushVahidi/lafc-evict (v0.3, revision
  `2113cc4d1edee57275d769d8760da77ed67c875d`, published 2026-08-13)

It contains Wiki2018-derived pseudonymized supervision, two configs, and
22,356,992 rows under CC0 1.0. The prior **v0.2 published preview** (4,800,000
rows) remains published and pinnable for reproducibility on both Hugging Face
and Zenodo (https://doi.org/10.5281/zenodo.21895844 -- this DOI identifies
v0.2 only; **Zenodo does not yet have a v0.3 version** due to an unresolved
deposit-token permission error, tracked in
`publication/LAFC_EVICT_PUBLICATION_STATE.json`).

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

The published v0.3 release (like v0.2 before it) contains only Wiki2018-derived
rows. CloudPhysics, MetaCDN, MetaKV, and Twemcache are not currently cleared
for public release. CitiBike and Brightkite remain blocked. A separate,
substantially larger internal multi-family research build exists (see
`RELEASE_SCOPE.md`, `lafc-evict-full-heavy_r1`) but is not part of any public
release and is not in scope for the AWS Open Data submission.

## Intended benchmark views

- candidate-row regression or ranking tasks,
- decision-level evaluation,
- pairwise preference evaluation within each eviction decision.

## Current status (updated 2026-09-12)

The v0.1-open trees are historical unpublished local staging artifacts. The
**v0.3 tree is published** on Hugging Face (this section previously said it
was "a locally validated candidate and is not published" -- corrected). The
wiki2018-only v0.3 payload is also publicly hosted through AWS Open Data in
bucket `lafc-evict-open-data` (`us-west-2`); AWS Open Data Registry PR #3335
is pending maintainer activity unless later repository documentation proves it
merged. Future releases still require:

- upstream trace-license review,
- redistribution review per trace family,
- host selection and persistent identifiers,
- release-specific manifests and checksums.
