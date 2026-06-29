# SIGMOD/PACMMOD 2027 Paper Planning

This directory is a planning package for the first anonymous SIGMOD/PACMMOD 2027 Research Track submission built around the LAFC-Evict dataset.

Target venue profile:

- ACM SIGMOD/PACMMOD 2027
- Research Track
- Experiment & Analysis paper type
- Benchmarks and Datasets category
- Double-anonymous review
- 12-page limit excluding references
- ACM 2-column proceedings format for submission

Current paper thesis:

LAFC-Evict should be positioned as a benchmark paper, not a raw-systems paper. The core claim is that learned cache-eviction research lacks a large-scale, decision-aligned, counterfactual benchmark that exposes candidate-level supervision, decision-level summaries, and pairwise preference structure across multiple trace families, capacities, and horizons. LAFC-Evict fills that gap with a release-focused benchmark package plus validation and reproducibility tooling.

Current release state relevant to the paper:

- Preserved current-contract release exists locally at `release/lafc-evict-v0.1-open-current-contract-preserved`.
- Lightweight metadata repair completed.
- Publication bundle regeneration and bundle validation passed.
- Repository tests passed.
- Full real-release validation passed on the preserved release on 2026-06-29; the paper should cite that pass while keeping anonymous artifact packaging and final public hosting claims pending.

Important drafting constraints:

- Keep the submission double-anonymous.
- Do not copy author names, personal paths, or public preprint identifiers into the anonymous draft.
- Treat the current public-facing publication bundle as a starting point for structure only, not as a submission-ready anonymous artifact.

Files in this directory:

- `outline.md`: anonymous paper structure and abstract draft.
- `submission_checklist.md`: venue-specific submission constraints and project gating items.
- `anonymous_artifact_plan.md`: review artifact plan and anonymity requirements.
- `experiments_plan.md`: minimum experimental package for the submission.
- `related_work_notes.md`: categories and questions for literature search.

This directory now contains a tracked LaTeX draft, but the manuscript is still not submission-ready.
