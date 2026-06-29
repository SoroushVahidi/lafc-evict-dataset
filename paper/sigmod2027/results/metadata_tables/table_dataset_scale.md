# table_dataset_scale

All values are manifest-backed unless noted otherwise. The preserved release passed full real-release validation on 2026-06-29.

| metric | value | notes |
| --- | --- | --- |
| candidate rows | 277,995,072 | manifest-backed; preserved release passed full validation on 2026-06-29 |
| decision rows | 2,363,286 | manifest-backed and decision-view-backed; preserved release passed full validation on 2026-06-29 |
| pairwise-sample rows | 1,000,000 | manifest-backed and pairwise-sample-backed; preserved release passed full validation on 2026-06-29 |
| candidate parquet files | 168 | counted from manifest file inventory only |
| total release files | 176 | manifest-backed |
| manifest file_inventory count | 176 | manifest-backed |
| checksum entry count | 175 | checksums.sha256 line count |
| selected trace families | cloudphysics, metacdn, metakv, twemcache, wiki2018 | manifest-backed |
| excluded/pending trace families | brightkite, citibike | manifest-backed |
| full validation status | passed | preserved release passed full validation on 2026-06-29; release-internal metadata/validation_report.md was not refreshed by the validator CLI |
