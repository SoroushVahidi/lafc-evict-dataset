# Anonymous Artifact Plan

## Goal

Prepare a review artifact that lets SIGMOD/PACMMOD reviewers inspect the benchmark structure, schema, release metadata, validation logic, and at least one runnable example without exposing author identity.

## Current status

- The preserved release and publication bundle are useful technical inputs.
- The current publication bundle is not anonymous yet because it still mentions the associated public preprint and author identity.
- Full real-release validation is still pending and must not be represented as complete.

## Review artifact options

## Option A: Anonymous repository plus hosted data artifact

- Create an anonymous repository or review-only archive with no author names or public profile links.
- Include the benchmark code, schema docs, validation scripts, and the anonymous paper appendix material.
- Host the review data payload separately through an anonymous review mechanism if the venue permits it.
- Replace final public URLs with `to be added after acceptance` where necessary.

## Option B: Anonymous archive with sample release plus metadata for the real release

- If the full open release cannot be anonymously hosted before submission, include:
  - the synthetic sample release already in the repo,
  - the canonical schema,
  - validation scripts,
  - release-building scripts,
  - release manifest structure,
  - checksums format,
  - dataset card and datasheet,
  - anonymous release statistics for the preserved open release.
- State clearly that the full open release is under anonymous packaging and final public hosting will be added after acceptance.

## Required anonymity checks

- No author names in README, dataset card, release notes, or bundle metadata.
- No personal paths such as `/home/soroush`, `/tmp`, or `/mmfs1`.
- No GitHub username, Hugging Face username, or Zenodo identity.
- No acknowledgments or institution names.
- No preprint identifiers if they reveal authorship.
- No PDF metadata with author-identifying fields.

## Files to include

- Anonymous project README for reviewers.
- Schema documentation.
- Datasheet and limitations notes.
- Validation scripts and release-construction scripts.
- Sample release.
- If feasible, anonymous metadata for the preserved `lafc-evict-v0.1-open` release:
  release manifest, validation report, checksums, and aggregate statistics.

## Files to exclude or rewrite

- Current public-facing publication bundle files that mention the author or preprint.
- Any final Hugging Face, GitHub, or Zenodo identifiers.
- Any local-machine commands containing personal absolute paths.
- Any acknowledgments section.

## Practical packaging plan

1. Fork the current publication bundle into an anonymous review-bundle generator.
2. Strip associated-paper fields from the generated README, dataset card, release notes, and metadata JSON.
3. Replace final hosting identifiers with placeholders.
4. Re-scan all public-facing text files for personal paths and identity-bearing strings.
5. Produce one compressed anonymous package for review.

## Reviewer-facing message

The artifact should say:

"This anonymous review package contains benchmark code, schema documentation, validation utilities, a synthetic runnable sample, and anonymous metadata/statistics for the benchmark release. Final public hosting links and persistent identifiers will be added after acceptance."
