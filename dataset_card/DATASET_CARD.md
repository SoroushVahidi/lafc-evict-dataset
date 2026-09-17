# LAFC-Evict Dataset Card

## Name

**LAFC-Evict: Counterfactual Supervision for Learned Cache Eviction**

## Current public release

The current public release is **v1.0**, available on Hugging Face:

- https://huggingface.co/datasets/SoroushVahidi/lafc-evict (v1.0, revision
  `v1.0`, commit `37173bc96de2a615455bf9713bb90d846156af29`, published 2026-09-17)

It contains full five-family (Alibaba Block, MetaCDN, MetaKV, Twemcache, Wiki2018)
derived supervision, consisting of 277,995,072 candidate-level rows,
2,363,286 decision-horizon rows, and a 1,000,000-row canonical pairwise sample.
The older v0.3 release (wiki2018-only, 22,356,992 rows) remains available separately
on Hugging Face `main` revision and AWS Open Data. The prior **v0.2 published preview**
(4,800,000 rows) remains published and pinnable on both Hugging Face and Zenodo
(https://doi.org/10.5281/zenodo.21895844 -- this DOI identifies v0.2 only; Zenodo
does not yet have a v0.3 or v1.0 version DOI).

## Associated Paper / Preprint

This dataset release accompanies the public preprint/manuscript:  
**Decision-aligned eviction-value prediction for robust learning-augmented caching**  
Soroush Vahidi.  
Available at SSRN 6636732.  
Status: public preprint; manuscript under peer review.

The paper describes the learning-augmented caching setting and the experiments
that motivated this dataset release. This repository provides dataset-release
artifacts, schemas, validation tools, benchmark views, and reproducibility
utilities. When using the data artifact, cite the paper/preprint and the
specific host/version used; cite the Zenodo DOI only for DOI-backed Zenodo
versions. As of this handoff, v0.3 has no documented Zenodo DOI.

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

The published v1.0 release contains all five evaluated trace families: Alibaba Block
(internal key `cloudphysics`), MetaCDN, MetaKV, Twemcache, and Wiki2018. It represents
the full evaluated corpus described in the manuscript. CitiBike and Brightkite remain
blocked and are excluded.

## Intended benchmark views

- candidate-row regression or ranking tasks,
- decision-level evaluation,
- pairwise preference evaluation within each eviction decision.

## Current status (updated 2026-09-17)

The v0.1-open trees are historical unpublished local staging artifacts. The
**v1.0 tree is published** on Hugging Face. The older wiki2018-only v0.3 payload
remains publicly hosted through AWS Open Data in bucket `lafc-evict-open-data` (`us-west-2`).
Zenodo currently archives v0.2 only.
