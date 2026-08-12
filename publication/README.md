# Publication Tooling

This directory contains templates, records, and helpers for preparing LAFC-Evict
publication metadata. The authoritative current state is
`LAFC_EVICT_PUBLICATION_STATE.json`.

- All publication scripts are **dry-run by default**.
- Hugging Face is the current interactive dataset host.
- Zenodo is the current DOI-backed archival host.
- GitHub Releases are intended for code release notes and small metadata assets, not the main large dataset payload.

The current public release is v0.2. The v0.1-open trees are historical local
staging artifacts. The v0.3 tree is a local candidate and is not published.
Future publication actions require separate approval and must pass validation,
security/privacy, provenance, and checksum gates.
