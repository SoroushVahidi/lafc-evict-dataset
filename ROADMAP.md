# LAFC-Evict Release Roadmap

## Completed

- [x] v0.1 synthetic workflow sample published separately.
- [x] v0.2 Wiki2018 preview uploaded to Hugging Face.
- [x] v0.2 DOI-backed archival representation published on Zenodo.
- [x] v0.2 integrity and Wiki2018 provenance validation.
- [x] v0.3 Wiki2018-only payload published on Hugging Face `main` and AWS Open Data.
- [x] Five-family v1.0 release published on Hugging Face revision `v1.0`.
- [x] Performance Evaluation manuscript package integrated with canonical PDF at `paper/performance_evaluation/LAFC-Evict-Performance-Evaluation.pdf`.
- [x] Provenance review completed for the five public v1.0 families: Alibaba Block, MetaCDN, MetaKV, Twemcache, and Wiki2018.

## Current

- Keep public documentation synchronized with the v1.0 Hugging Face release, the older v0.3 AWS/HF-main state, and the v0.2 Zenodo archival state.
- Preserve the published v0.2 Zenodo payload and v0.3 AWS/HF-main payload as historical active releases.
- Keep CitiBike and Brightkite excluded unless a future license/privacy review explicitly clears them.

## Future / Optional

- Consider a Zenodo v1.0 archival version only after a separate publication decision; no v1.0 Zenodo DOI currently exists.
- Add benchmark notebooks or examples for candidate, decision, and pairwise views if they can be kept lightweight and reproducible.
- Add future benchmark extensions only when scientifically justified, independently validated, and compatible with upstream licensing.
- Create GitHub tag/release metadata for v1.0 only during final release closure, not during documentation polish.

## Guardrails

- Do not describe v0.3 as the current full release; v0.3 is the older Wiki2018-only release.
- Do not describe the Zenodo concept DOI as identifying v1.0.
- Do not include Brightkite or CitiBike in public releases without explicit future clearance.
