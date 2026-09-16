# LAFC-Evict Release Roadmap

## Done

- [x] v0.1 synthetic workflow sample published separately
- [x] v0.2 published preview uploaded to Hugging Face
- [x] v0.2 DOI-backed archival representation published on Zenodo
- [x] v0.2 integrity and Wiki2018 provenance validation
- [x] v0.3 Wiki2018-only candidate built and locally validated

## Current

- Review v0.3 candidate metadata and publication readiness.
- Package and host the four additional families now cleared for public
  release (cloudphysics/Alibaba Block, metacdn, metakv, twemcache; see
  `dataset_card/LICENSE_DATA.md`, reviewed 2026-09-15) -- legal clearance is
  resolved, packaging/upload has not started.
- Keep the published v0.2 scientific payload immutable.

## Future

- Possible v0.3 publication, only after separate approval and final gates.
- v1.0 stable/full release after the newly-cleared families are packaged,
  hosted, and pass the same quality gates as the current release.
- Expanded configs where scientifically justified and independently validated.

## Guardrails

- No upload or Zenodo publication is implied by this roadmap.
- Brightkite and CitiBike remain blocked pending license/privacy review.
  Cloudphysics (Alibaba Block), metacdn, metakv, and twemcache are cleared
  for public release as of the 2026-09-15 review but are not yet packaged
  or hosted in any public release.

## Benchmark usability

1. Add a baseline benchmark notebook for candidate, decision, and pairwise views.
2. Add example release manifests for hosted dataset snapshots.
3. Document any intentionally allowed cross-split or trace-family exceptions.
