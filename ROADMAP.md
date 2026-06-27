# LAFC-Evict Release Roadmap

## Milestones

- [x] scaffold created
- [x] scaffold audited
- [x] synthetic sample release dry-run
- [x] source-family release governance
- [x] memory-safe real release builder for `lafc-evict-v0.1-open`
- [ ] next: run full real release build for `lafc-evict-v0.1-open`

## Priority 0: Licensing and scope

1. Complete upstream license and redistribution review for each trace family.
2. Select the first public release subset for `lafc-evict-v0.1-open` using only registry-approved license-clean/open traces.
3. Keep CitiBike and Brightkite out of the first public release unless review clears them.

## Priority 1: Release build

1. Dry-run and then build `lafc-evict-v0.1-open` with `scripts/build_real_release.py` using the Wulver candidate-row manifest.
2. Validate the release with `scripts/validate_real_release.py`.
3. Generate and verify SHA256 checksums.

## Priority 2: Hosting and metadata

1. Prepare the Hugging Face dataset card and hosted files.
2. Prepare the Zenodo deposition and final DOI metadata.
3. Finalize `CITATION.cff`, release manifest values, and version tags.

## Priority 3: Benchmark usability

1. Add a baseline benchmark notebook for candidate, decision, and pairwise views.
2. Add example release manifests for hosted dataset snapshots.
3. Document any intentionally allowed cross-split or trace-family exceptions.
