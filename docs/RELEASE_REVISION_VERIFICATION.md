# LAFC-Evict release revision verification

The following host and revision inventory was checked on 2026-11-25. Use immutable revisions for loading, comparison and citation.

| Version | Location | Scope |
|---|---|---|
| v0.1 | Historical synthetic sample | Workflow fixture. The v0.1-open real-data build remained local. |
| v0.2 | [Hugging Face snapshot](https://huggingface.co/datasets/SoroushVahidi/lafc-evict/tree/b77413fef197e808aed9cfa708878064a5c00493) · [Zenodo record 21895844](https://zenodo.org/records/21895844) | Wiki2018 preview, 4.8 million rows. The Zenodo version DOI applies to this preview. |
| v0.3 | [Hugging Face main as inspected](https://huggingface.co/datasets/SoroushVahidi/lafc-evict/tree/c336fd6e9be7b46f9c5aa5cffc8566bfa42a4d78) · [AWS bucket root](https://registry.opendata.aws/lafc-evict/) | Wiki2018 slice with 22,356,992 rows across two candidate views. |
| v1.0 | [Manuscript-referenced data commit](https://huggingface.co/datasets/SoroushVahidi/lafc-evict/tree/37173bc96de2a615455bf9713bb90d846156af29) · [GitHub code release](https://github.com/SoroushVahidi/lafc-evict-dataset/releases/tag/v1.0) | Five-family benchmark. Counts are 277,995,072 candidate rows, 2,363,286 decision-horizon rows and 1,000,000 pairwise sample rows. |
| v1.0 branch tip | [Hugging Face v1.0 as inspected](https://huggingface.co/datasets/SoroushVahidi/lafc-evict/tree/46fc39fd667d77a3042c94c9fb6ca612ce1c3fee) · [AWS v1.0 prefix](https://registry.opendata.aws/lafc-evict/) | All 170 scientific payload checksum entries match the manuscript revision. The v1.0 manifest matches byte for byte. The sole checksum entry that differs from the manuscript revision is the root license document. |
| v1.1 | [Hugging Face v1.1 as inspected](https://huggingface.co/datasets/SoroushVahidi/lafc-evict/tree/6e957259fbe01162f7b4bfc73e0b45273690980d) | Same five-family payload, with a separately documented 60-row BrightKite aggregate companion. It is outside the benchmark population. |

For cross-host equivalence, compare declared SHA-256 values at identical paths. The inventory comparison establishes the content identity asserted by those manifests. A fresh download and hash verifies bytes from a host.

```sh
curl -fSL 'https://huggingface.co/datasets/SoroushVahidi/lafc-evict/resolve/37173bc96de2a615455bf9713bb90d846156af29/metadata/checksums.sha256' -o manuscript.sha256
curl -fSL 'https://lafc-evict-open-data.s3.us-west-2.amazonaws.com/v1.0/metadata/checksums.sha256' -o aws.sha256
python scripts/compare_release_checksums.py manuscript.sha256 aws.sha256 --prefix data/
```

The LAFC-Evict software and dataset versions have separate identifiers. Use the immutable data commit in a replication record, alongside the checked-out code revision. For a small loading test, download a specific table at the pinned revision. The example below reads schema metadata from the canonical pairwise Parquet file.

```python
from huggingface_hub import hf_hub_download
from pyarrow.parquet import ParquetFile

path = hf_hub_download(
    repo_id="SoroushVahidi/lafc-evict",
    repo_type="dataset",
    revision="37173bc96de2a615455bf9713bb90d846156af29",
    filename="data/pairwise_sample/pairwise_sample.parquet",
)
print(ParquetFile(path).metadata.num_rows)
```

The repository's synthetic sample workflow runs without production data. See [schema and loading documentation](../dataset_card/SCHEMA.md) and [third-party attribution](../THIRD_PARTY_DATA.md).
