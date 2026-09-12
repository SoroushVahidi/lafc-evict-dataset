# Dataset Card Index

This directory contains the release-facing documentation for LAFC-Evict.

The current public release is **v0.3** (22,356,992 rows, wiki2018-only,
published on Hugging Face 2026-08-13; corrected here 2026-09-12 — this
directory previously still said v0.2). Release/version/host truth is
maintained in `docs/LAFC_EVICT_PUBLICATION_STATE.md` and
`publication/LAFC_EVICT_PUBLICATION_STATE.json`.

**Relationship to the generated release package.** The public-facing
`README.md` and `dataset_card.md` shipped inside `release/<version>/` (e.g.
`release/lafc-evict-v0.3-candidate/`) are generated at build time by
`src/lafc_evict_dataset/release_v0_3.py`, not copied verbatim from this
directory. Documentation content added or corrected only in the generated
output (e.g. during AWS Open Data release preparation) must be reflected
back into this tracked source directory to survive a future rebuild — that
is what this pass did. Chain: this directory (tracked, hand-authored) →
`release/lafc-evict-v0.3-candidate/{README.md,dataset_card.md}` (generated,
git-ignored) → `release/aws-open-data-v0.3-staging/` (local AWS freeze,
git-ignored, never uploaded).

Associated paper/preprint metadata should be kept consistent across this directory, `README.md`, `CITATION.cff`, and publication templates. The current public preprint metadata is: `Decision-aligned eviction-value prediction for robust learning-augmented caching`, `Soroush Vahidi`, `Available at SSRN 6636732`, and status `public preprint; manuscript under peer review`.

- `DATASET_CARD.md`: short-form dataset card.
- `DATASHEET.md`: datasheet-style questions and answers.
- `LICENSE_DATA.md`: upstream licensing and redistribution review checklist.
- `PROVENANCE.md`: separation of raw traces, processed traces, generated features, generated labels, and benchmark tasks.
- `RELEASE_SCOPE.md`: named release profiles and intended use.
- `SCHEMA.md`: canonical column-level schema.
- `REPRODUCE.md`: how to export a public release from existing generated candidate rows, and where the candidate-row generator itself lives.
- `GLOSSARY.md`: plain-language terminology (decision point, candidate row, horizon, capacity, `y_loss`, etc.).
- v0.2 HF and Zenodo packages use different directory layouts but identical
  scientific Parquet payloads. v0.3's HF and zenodo-flat packages are
  scientifically identical as well; see `RELEASE_SCOPE.md` for the one
  known non-scientific packaging difference between them.
- `ETHICS_AND_LIMITATIONS.md`: scientific, legal, and privacy caveats.

Note: `SCHEMA.md`, `DATASHEET.md`, `LICENSE_DATA.md`, and `PROVENANCE.md`
still narrate v0.2 as "the current public release" as of 2026-09-12 and were
not rewritten in this pass (out of scope for the specific AWS-release
documentation gaps being closed here); their substantive family-clearance
and schema content remains accurate, only the "current version" framing is
stale. Treat `README.md`, `DATASET_CARD.md`, and `RELEASE_SCOPE.md` (updated
2026-09-12) as authoritative on which version is current.
