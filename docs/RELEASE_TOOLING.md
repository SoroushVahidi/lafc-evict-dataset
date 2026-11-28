# Release tooling

Use [src/lafc_evict_dataset](../src/lafc_evict_dataset/) for the maintained package, [scripts](../scripts/) for release entry points, [manifests](../manifests/) for source and release records, and [tests](../tests/) for software qualification. Frozen campaign code and research outputs live in [analysis](../analysis/). [Publication records](LAFC_EVICT_PUBLICATION_STATE.md) identify which versions have public payloads.

## Install and validate a synthetic release

For the tested Linux x86-64 Python 3.11 environment, install with the [qualification constraints](../configs/environments/python311-test.txt). On Wulver, select a Python 3.11 environment before creating the virtual environment. From the source checkout run the following.

```sh
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -c configs/environments/python311-test.txt -e '.[dev]'
python -m pip check
python -m pytest -q tests

fixture_dir="$(mktemp -d)"
python scripts/build_sample_release.py --input examples/tiny_candidate_rows.csv --output-dir "$fixture_dir/sample"
python scripts/validate_release_schema.py --input-path examples/tiny_candidate_rows.csv
lafc-verify-checksums "$fixture_dir/sample/metadata/checksums.sha256" --root "$fixture_dir/sample"
```

This workflow uses the included synthetic CSV and writes a local sample. Use the [schema reference](../dataset_card/SCHEMA.md) to understand candidate, decision and pairwise views. Set input and output paths explicitly if you run scripts from another directory. Use the [release reproduction guide](../dataset_card/REPRODUCE.md) and pinned campaign environments for historical builds. Archived preview builders accept `--cross-family-root` and `--objective-root` to locate historical inputs on another system.

## Verify downloaded payloads

Download the release and its checksum inventory using the [revision verification guide](RELEASE_REVISION_VERIFICATION.md). Run `lafc-verify-checksums <manifest> --root <release-directory>` with the directory containing the paths recorded in the inventory. The command reads local files and returns status 1 for missing or mismatched payloads and status 2 for invalid arguments or inventory inputs. To compare two declared inventories without hashing the payloads, use the existing `scripts/compare_release_checksums.py` command. Use the immutable revision in citations and reproduction records.

## Contribute

Include a small synthetic case for changes to schema, grouping or release validation. Keep generated Parquet, release bundles and trace inputs in a configured data directory. Record the exact source revision, transformation, rights and checksums for any proposed new data view. The [MIT software license](../LICENSE), [data licensing guide](../dataset_card/LICENSE_DATA.md), and [third-party source terms](../THIRD_PARTY_DATA.md) cover separate materials. See [CITATION.cff](../CITATION.cff) for citation information.
