# LAFC-Evict v0.2 Publication Status

Publication date: 2026-08-11

## Hugging Face Dataset

- Repository: https://huggingface.co/datasets/SoroushVahidi/lafc-evict
- Repo type: dataset
- Visibility: public
- Final verified revision: `b77413fef197e808aed9cfa708878064a5c00493`
- Upload commit messages used: `publish v0.2 real-data preview`, `fix dataset card provenance wording`, `record v0.2 public release status`
- Uploaded release files: 15
- Remote file count: 16, including Hugging Face-managed `.gitattributes`
- Staged release package bytes: 140,145,059
- Parquet payload bytes: 140,106,094

## Scope

- Version: `0.2-preview`
- Included family: `wiki2018`
- Excluded pending review: `brightkite`, `citibike`, `cloudphysics`, `metacdn`, `metakv`, `twemcache`
- Total rows: 4,800,000
- Configs:
  - `cross_family_evict_value_v1`: 2,700,000 rows
  - `objective_ablation_scalar`: 2,100,000 rows

## Payload Hashes

- `data/cross_family_evict_value_v1.parquet`: `38ae87b88bf8367d41f0dc8638eaf12fa5416b559d24c7023f39b9f1c7b6bb8f`
- `data/objective_ablation_scalar.parquet`: `90a2cb7913e234323190810906644e110f5c9ebeaaea47203857f61b822757f9`

Both remote Parquet files were re-downloaded from the public Hub repository and matched the local SHA-256 hashes exactly.

## Validation

- Canonical tests before publication: `100 passed`
- Preview validator: passed
- Security/privacy scan: passed with no findings
- `git diff --check`: passed
- Dataset card license metadata: `cc0-1.0`
- Dataset card attribution wording: verified present in the rendered Hugging Face `README.md`
- Dataset-server viewer/indexing: upload succeeded; Hub indexing returned a temporary "not ready" response at verification time.

## Preservation

The historical synthetic repository `SoroushVahidi/lafc-evict-sample` was not modified. Its verified revision after publication was `c80dd3c55d837afa0405e78ef7a0475455256eb1`.
