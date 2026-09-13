# Publication Tooling

This directory contains templates, records, and helpers for preparing LAFC-Evict
publication metadata. The authoritative current state is
`LAFC_EVICT_PUBLICATION_STATE.json`.

- All publication scripts are **dry-run by default**.
- Hugging Face is the current interactive dataset host.
- AWS Open Data hosts the current wiki2018-only v0.3 public payload.
- Zenodo is the current DOI-backed archival host for v0.2.
- GitHub Releases are intended for code release notes and small metadata assets, not the main large dataset payload.

The current public release is v0.3, limited to wiki2018-derived supervision.
It is published on Hugging Face and hosted through AWS Open Data at
`lafc-evict-open-data` in `us-west-2`. Zenodo still serves v0.2 as the latest
documented DOI-backed release; no v0.3 Zenodo DOI has been minted. The
v0.1-open trees are historical local staging artifacts.

The full five-family canonical scientific dataset is not the same thing as the
public wiki2018-only v0.3 release. See
`docs/CURRENT_PROJECT_STATUS_AND_HANDOFF.md` before making publication,
manuscript, or cleanup decisions.
