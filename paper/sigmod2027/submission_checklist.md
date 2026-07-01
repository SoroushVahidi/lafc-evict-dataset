# Submission Checklist

## Venue constraints

- Abstract and COI deadline: July 10, 2026.
- Full paper deadline: July 17, 2026.
- Track: Research Track.
- Paper type: Experiment & Analysis.
- Category: Benchmarks and Datasets.
- Format: ACM 2-column proceedings submission format.
- Length: 12 pages excluding references.
- Title must end with `: [Experiments & Analysis]`.

## Double-anonymity

- Remove author names from the submission draft.
- Remove affiliations and acknowledgments from the submission draft.
- Do not reference the public preprint in a way that breaks anonymity.
- Do not expose personal paths such as `/home/<username>`, `/tmp`, or `/mmfs1`.
- Do not expose GitHub usernames, Hugging Face usernames, Zenodo identity, or institution-identifying metadata.
- Check PDF metadata before submission.
- Check artifact metadata and filenames before sharing with reviewers.

## Artifact and repository checks

- Prepare an anonymous review artifact or anonymous repository.
- Ensure public-facing bundle files are anonymized.
- Include schema docs, validation scripts, release metadata, and checksums.
- Decide whether the full open release can be hosted anonymously in time.
- If not, ship the sample release plus anonymous metadata and scripts, and clearly state what the artifact contains.

## Scientific and policy checks

- Confirm there is no simultaneous substantially overlapping submission.
- Verify benchmark claims match what the current release actually supports.
- Claim full real-release validation only as a preserved-release result backed by the June 29, 2026 local validation log, not by the stale internal `metadata/validation_report.md`.
- Do not claim public hosting or DOI assignment is complete yet.
- Make the finite-horizon continuation-policy label definition explicit.
- Make the trace-family release-governance boundary explicit.

## Current project gating items

- Full real-release validation passed on the preserved release on 2026-06-29.
- Final public upload is still pending.
- Final anonymous artifact packaging is still pending.
- Baseline experiment results are still pending.
- Final paper figures and tables are still pending.
- Need to verify ORCID, CMT, and any ACM profile requirements separately.

## Final pre-submission pass

- Confirm anonymous title page.
- Confirm page count excluding references.
- Confirm no deanonymizing text in figures, captions, appendix, or artifact description.
- Confirm the artifact URL, if used, is anonymous and review-safe.
- Confirm all reported numbers are reproducible from the actual release and scripts.
