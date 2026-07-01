# Anonymous Submission Bundle Manifest

Run `python scripts/sigmod2027/build_anonymous_submission_bundle.py` to assemble
a review-safe copy of the paper materials. It refuses to run if
`scripts/sigmod2027/redact_result_metadata.py --check` would still change
anything, so a forgotten redaction pass cannot leak into a bundle silently.

## Included

- `latex/main.tex`, `latex/sections/*.tex`, `latex/tables/*.tex`, `latex/figures/*`, `latex/refs.bib`
- `results/metadata_tables/*` (manifest-backed summary tables; already review-safe)
- `results/baselines/**/*.{json,csv,md}` and `results/candidate_label_stats/*.{json,csv}`,
  after redaction (see below)
- `results/README.md`, `results/full_validation_summary.md`

## Excluded

- `latex/TODO.md` — dev notes, mentions the internal HPC cluster name
- `latex/main.pdf` — regenerate fresh for the bundle rather than reusing a locally
  built PDF, which can carry local build/user metadata
- `technical/` — internal planning/execution notes, heavy with the HPC cluster
  nickname and job-status language not relevant to reviewers
- `related_work/` — internal literature-search drafting notes, superseded by
  `latex/sections/10_related_work.tex`
- `anonymous_artifact_plan.md`, `submission_checklist.md`, `experiments_plan.md`,
  `outline.md`, `related_work_notes.md`, this directory's own `README.md` — internal
  planning documents for the maintainers, not reviewer-facing content
- `results/submitted_jobs_*` — moved out of the paper tree entirely; see
  `internal/wulver_job_logs/` at the repo root
- anything under `.git/` — a bundle must never carry version-control history

## Redaction policy applied to included result files

`scripts/sigmod2027/redact_result_metadata.py` rewrites, in place, only
non-scientific environment metadata:

- absolute HPC paths (e.g. `/mmfs1/scratch/<user>/.../lafc-evict-v0.1-open-current-contract-preserved`)
  become the relative placeholder `release/<evaluated-open-release>`
- the `requires_wolverine` field is renamed to `requires_large_memory_machine`
  (same boolean value)
- prose mentions of the internal HPC cluster nickname become a neutral
  description of the execution environment

It never changes row counts, metrics, split names, timestamps, or validation
status. Re-run it after regenerating any result file and before building a
bundle or committing.

## Scope note

This manifest covers the *paper submission* bundle only. The broader
anonymous *dataset/artifact* release described in `anonymous_artifact_plan.md`
(schema docs, validation scripts, sample release, etc.) is a separate,
larger effort and is not produced by this script.
