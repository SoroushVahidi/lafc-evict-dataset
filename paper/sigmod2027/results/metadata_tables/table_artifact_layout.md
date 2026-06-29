# table_artifact_layout

Artifact paths are release-relative for manuscript safety. The anonymous review artifact is not finalized yet.

| artifact | relative_path | status | notes |
| --- | --- | --- | --- |
| candidate rows | data/candidate_rows/ | present | partitioned candidate-row parquet shards |
| decision view | data/decision_view/decision_view.parquet | present | single derived decision-view parquet |
| pairwise sample | data/pairwise_sample/pairwise_sample.parquet | present | capped shipped sample; not full pairwise materialization |
| release manifest | metadata/release_manifest.json | present | manifest-backed release metadata |
| validation report | metadata/validation_report.md | present | present but stale; June 29 validation log is authoritative |
| checksums | metadata/checksums.sha256 | present | 175 checksum entries |
| publication bundle | anonymous review artifact path pending | local bundle exists | anonymous artifact not finalized yet; public-facing upload pending |
