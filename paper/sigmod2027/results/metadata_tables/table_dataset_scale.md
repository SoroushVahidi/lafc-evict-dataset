# table_dataset_scale

All values are manifest-backed unless noted otherwise. Full real-release validation remains pending.

| metric | value | notes |
| --- | --- | --- |
| candidate rows | 277,995,072 | manifest-backed; pending full validation |
| decision rows | 2,363,286 | manifest-backed and decision-view-backed; pending full validation |
| pairwise-sample rows | 1,000,000 | manifest-backed and pairwise-sample-backed; pending full validation |
| candidate parquet files | 168 | counted from manifest file inventory only |
| total release files | 176 | manifest-backed |
| manifest file_inventory count | 176 | manifest-backed |
| checksum entry count | 175 | checksums.sha256 line count |
| selected trace families | cloudphysics, metacdn, metakv, twemcache, wiki2018 | manifest-backed |
| excluded/pending trace families | brightkite, citibike | manifest-backed |
| full validation status | pending | full real-release validation has not been run |
