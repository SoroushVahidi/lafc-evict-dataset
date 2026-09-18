# Dataset Card Index

This directory contains the release-facing documentation for LAFC-Evict.

The current public release is **v1.0** (277,995,072 rows, five-family,
published on Hugging Face 2026-09-17). Release/version/host truth is
maintained in `docs/LAFC_EVICT_PUBLICATION_STATE.md` and
`publication/LAFC_EVICT_PUBLICATION_STATE.json`.

**Relationship to generated release packages.** The public-facing files shipped
inside `release/<version>/` trees are generated local payloads and are ignored
by Git. This tracked directory is the source for release-facing documentation
that should stay consistent with `README.md`, `CITATION.cff`,
`docs/LAFC_EVICT_PUBLICATION_STATE.md`, and
`publication/LAFC_EVICT_PUBLICATION_STATE.json`.

Associated manuscript metadata should be kept consistent across this
directory, `README.md`, `CITATION.cff`, and publication templates. The current
canonical manuscript is `LAFC-Evict: A Large-Scale Counterfactual Benchmark
for Learned Cache Eviction`, submitted for consideration to *Performance
Evaluation*.

- `DATASET_CARD.md`: short-form dataset card.
- `DATASHEET.md`: datasheet-style questions and answers.
- `LICENSE_DATA.md`: upstream licensing and redistribution review checklist.
- `PROVENANCE.md`: separation of raw traces, processed traces, generated features, generated labels, and benchmark tasks.
- `RELEASE_SCOPE.md`: named release profiles and intended use.
- `SCHEMA.md`: canonical column-level schema.
- `REPRODUCE.md`: how to export a public release from existing generated candidate rows, and where the candidate-row generator itself lives.
- `GLOSSARY.md`: plain-language terminology (decision point, candidate row, horizon, capacity, `y_loss`, etc.).
- v0.2 HF and Zenodo packages use different directory layouts but identical
  scientific Parquet payloads. v0.3 remains active as the older Wiki2018-only
  HF-main/AWS payload. v1.0 is the current full five-family HF release.
- `ETHICS_AND_LIMITATIONS.md`: scientific, legal, and privacy caveats.
