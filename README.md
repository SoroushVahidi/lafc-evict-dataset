# LAFC-Evict: A Large-Scale Counterfactual Dataset for Learned Cache Eviction

**In plain words.** Machine-learned cache-eviction policies need training labels, but real caches only ever record what *did* happen, not what would have happened under a different eviction. LAFC-Evict fills that gap. At every full-cache miss, for every item that could be evicted, it simulates forcing that eviction and records the resulting future miss cost. The v1.0 release has about 278 million candidate rows drawn from five public cache-trace families (Alibaba Block, MetaCDN, MetaKV, Twemcache, Wiki2018). This repository holds the schema, validation and release tooling, reproducibility evidence and the manuscript. The data itself is hosted on Hugging Face and AWS Open Data.

## Preprint and related paper

- **Preprint:** S. Vahidi. *LAFC-Evict: A Large-Scale Counterfactual Benchmark for Learned Cache Eviction.* SSRN, 2026. [ssrn.com/abstract=7625523](https://ssrn.com/abstract=7625523) · [doi:10.2139/ssrn.7625523](https://doi.org/10.2139/ssrn.7625523). Not yet peer-reviewed.
- Related published method paper: S. Vahidi. *Decision-aligned eviction-value prediction for learning-augmented caching.* Knowledge-Based Systems 356 (2027), article 117353. [doi:10.1016/j.knosys.2026.117353](https://doi.org/10.1016/j.knosys.2026.117353). Code: [Augmented-caching](https://github.com/SoroushVahidi/Augmented-caching)

```bibtex
@misc{vahidi2026lafcevict,
  author = {Vahidi, Soroush},
  title  = {{LAFC-Evict}: A Large-Scale Counterfactual Benchmark for Learned Cache Eviction},
  year   = {2026},
  note   = {SSRN preprint},
  doi    = {10.2139/ssrn.7625523}
}
```

## Get the data

| Where | What |
|---|---|
| [Hugging Face, pinned v1.0](https://huggingface.co/datasets/SoroushVahidi/lafc-evict/tree/37173bc96de2a615455bf9713bb90d846156af29) | Full manuscript-referenced v1.0 release |
| [AWS Registry of Open Data](https://registry.opendata.aws/lafc-evict/) | `s3://lafc-evict-open-data/v1.0/` (anonymous access); historical v0.3 at the bucket root |
| [lafc-evict-tutorial](https://github.com/SoroushVahidi/lafc-evict-tutorial) | Credential-free notebook that reads a small slice from S3 |

---

LAFC-Evict is a public dataset and reproducibility repository for learned cache eviction. It releases candidate-level finite-horizon counterfactual supervision for cache-eviction decisions: for each full-cache miss and resident candidate, the benchmark records the miss-cost label that would follow from forcing that candidate's eviction under the documented continuation policy. The repository contains the public benchmark metadata, validation code, reproducibility evidence, and manuscript package for studying decision-aligned learned eviction methods.

## Paper

Current canonical manuscript:

- **LAFC-Evict: A Large-Scale Counterfactual Benchmark for Learned Cache Eviction**
- Submitted for consideration to *Performance Evaluation*
- PDF: [`paper/performance_evaluation/LAFC-Evict-Performance-Evaluation.pdf`](paper/performance_evaluation/LAFC-Evict-Performance-Evaluation.pdf)
- Submission-state record: [`docs/PERFORMANCE_EVALUATION_FINAL_SUBMISSION_STATE.md`](docs/PERFORMANCE_EVALUATION_FINAL_SUBMISSION_STATE.md)

The `paper/performance_evaluation/` tree is the current manuscript package. The separate `paper/sigmod2027/` tree is retained as historical conference-manuscript development material and is not the canonical Performance Evaluation submission.

## Dataset

The five-family manuscript benchmark is **LAFC-Evict v1.0** on Hugging Face:

- Dataset: <https://huggingface.co/datasets/SoroushVahidi/lafc-evict>
- Revision/branch: `v1.0`
- Manuscript-pinned data commit: `37173bc96de2a615455bf9713bb90d846156af29`

| View | Rows |
| --- | ---: |
| Candidate rows | 277,995,072 |
| Decision-horizon rows | 2,363,286 |
| Canonical pairwise sample | 1,000,000 |

Public v1.0 includes five evaluated trace families: Alibaba Block (`cloudphysics` internally), MetaCDN (`metacdn`), MetaKV (`metakv`), Twemcache (`twemcache`), and Wiki2018 (`wiki2018`). Citi Bike and BrightKite are outside the five-family decision-level benchmark.

Other hosting:

- Hugging Face `main`: older v0.3, Wiki2018-only state.
- Hugging Face `v1.1`: the same benchmark payload and a separate 60-row BrightKite statistical companion.
- AWS Open Data (bucket `lafc-evict-open-data`, region `us-west-2`): **v1.0** under the `v1.0/` prefix (per the [registry entry](https://registry.opendata.aws/lafc-evict/), updated 2026-09-24); the older v0.3 Wiki2018-only payload remains at the bucket root.
- Zenodo: v0.2 archival preview only. Version DOI: <https://doi.org/10.5281/zenodo.21895844>; concept DOI: <https://doi.org/10.5281/zenodo.21895843>. There is no v1.0 Zenodo DOI.

Use the [revision verification guide](docs/RELEASE_REVISION_VERIFICATION.md) for immutable loading and checksum comparison. The release-status documents are [`docs/LAFC_EVICT_PUBLICATION_STATE.md`](docs/LAFC_EVICT_PUBLICATION_STATE.md) and [`publication/LAFC_EVICT_PUBLICATION_STATE.json`](publication/LAFC_EVICT_PUBLICATION_STATE.json).

## Quick Start

Install the repository tooling and run the core public smoke tests:

```bash
git clone https://github.com/SoroushVahidi/lafc-evict-dataset.git
cd lafc-evict-dataset
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
python -m pytest -q tests
```

The command above is the base repository test contract. For local integrity checks and a fully synthetic workflow, see the [release tooling guide](docs/RELEASE_TOOLING.md). Some analysis-specific tests under `analysis/` require additional simulator or policy dependencies, such as `libcachesim`, and are documented with the corresponding frozen analysis campaign rather than required for the base install.

Useful starting points after cloning:

- Release status: [`docs/LAFC_EVICT_PUBLICATION_STATE.md`](docs/LAFC_EVICT_PUBLICATION_STATE.md)
- Dataset card and licensing: [`dataset_card/`](dataset_card/)
- Reproducibility evidence index: [`analysis/README.md`](analysis/README.md)
- Current documentation index: [`docs/README.md`](docs/README.md)
- Source-family governance registry: [`manifests/source_family_registry.yaml`](manifests/source_family_registry.yaml)

## Reproducing / Inspecting the Paper

The manuscript's compact reproducibility evidence is organized under [`analysis/`](analysis/). Start with [`analysis/README.md`](analysis/README.md), which maps the dated analysis directories to the manuscript evidence they support.

The index points to the target-characterization analysis, long-horizon sensitivity, closed-loop evaluation, offline/closed-loop linkage, mechanistic locality evidence, continuation-policy sensitivity, expanded comparator robustness, and feature/provenance audits. Directory names are intentionally preserved for provenance; do not rename analysis directories that are cited by the paper.

Detailed export and release-workflow documentation lives in [`dataset_card/REPRODUCE.md`](dataset_card/REPRODUCE.md). Historical v0.1/v0.1-open builder commands are kept there as release-engineering provenance, not as the recommended first workflow for new users.

## Repository Structure

```text
analysis/       Frozen analysis campaigns and manuscript evidence
dataset_card/   Dataset card, release scope, schema, licensing, provenance
docs/           Current public docs plus retained historical audit records
examples/       Tiny synthetic input used for tests and smoke checks
hpc/            Historical/operational HPC helpers, not the first user path
internal/       Historical internal support material retained for provenance
manifests/      Release and source-family governance manifests
metadata/       Model-feature schema and related metadata
paper/          Current Performance Evaluation manuscript and historical SIGMOD tree
publication/    Host-state records, publication templates, archived bundle metadata
scripts/        Release, validation, checksum, and benchmark-view utilities
src/            Python package for schema, validation, release, and publication tools
tests/          Base repository pytest suite
```

The `release/` directory is generated local material and is ignored by Git. Large dataset payloads are hosted externally and represented here by manifests, checksums, and publication-state records.

## Citation

For repository/dataset citation metadata, see [`CITATION.cff`](CITATION.cff). Until the Performance Evaluation article is formally published, do not invent a journal DOI, volume, issue, or page numbers.

Conservative manuscript citation form:

```text
Soroush Vahidi. LAFC-Evict: A Large-Scale Counterfactual Benchmark for Learned Cache Eviction.
Submitted manuscript, Performance Evaluation, 2026.
```

Dataset/repository citation form:

```text
Soroush Vahidi. LAFC-Evict: Learning-Augmented Cache Eviction Dataset, version 1.0.
GitHub repository and Hugging Face dataset, 2026.
https://github.com/SoroushVahidi/lafc-evict-dataset
https://huggingface.co/datasets/SoroushVahidi/lafc-evict/tree/v1.0
```

The Zenodo DOI currently identifies the v0.2 archival preview, not v1.0. Cite the Zenodo version DOI only when referring specifically to the Zenodo v0.2 payload.

## Licensing

Repository code is licensed under MIT; see [`LICENSE`](LICENSE).

The dataset is multi-licensed by trace family:

- Wiki2018: CC0-1.0
- Twemcache: CC BY 4.0
- Alibaba Block: CC BY 4.0
- MetaKV: Apache-2.0
- MetaCDN: Apache-2.0

See [`THIRD_PARTY_DATA.md`](THIRD_PARTY_DATA.md), [`dataset_card/LICENSE_DATA.md`](dataset_card/LICENSE_DATA.md), and [`manifests/source_family_registry.yaml`](manifests/source_family_registry.yaml) for provenance and attribution details. LAFC-Evict releases generated supervision and benchmark views, not upstream raw traces.

## Acknowledgments / Support

The project acknowledges research-computing, API, and data-hosting support disclosed in the manuscript, including Google Cloud Research Credits, Cohere Labs Catalyst, CloudRift AI Builder, AWS Open Data Sponsorship, and NJIT Wulver high-performance computing resources.

## Contact

Soroush Vahidi
New Jersey Institute of Technology
sv96@njit.edu
