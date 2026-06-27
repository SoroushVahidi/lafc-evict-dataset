# Publication Checklist

- Confirm release scope and source-family governance status.
- Dry-run the real release build with `scripts/build_real_release.py --dry-run`.
- Build the real release with `scripts/build_real_release.py --overwrite` only after disk-space and family-scope checks pass.
- Validate the release directory with `scripts/validate_real_release.py`.
- Validate the release directory and checksum manifest.
- Prepare a publication bundle with `prepare_publication_bundle.py`.
- Validate the publication bundle with `validate_publication_bundle.py`.
- Dry-run Hugging Face upload.
- Dry-run Zenodo deposit creation.
- Dry-run GitHub Release creation.
- Review synthetic disclaimers for sample releases.
- Review citations and metadata before any real upload.
