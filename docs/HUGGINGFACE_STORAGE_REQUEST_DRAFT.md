# Hugging Face Storage Request Draft

Draft date: 2026-08-11

Do not send yet. Publish the small public preview first, then adapt this with the final repository URL and early usage metrics.

## Intended Contact

Official Hugging Face storage documentation says storage grants for research teams and non-profits are evaluated case by case for high-impact open-source work and asks applicants to contact `datasets@huggingface.co` with a detailed proposal.

Source: https://huggingface.co/docs/hub/storage-limits

## Draft Message

Subject: Storage grant request for LAFC-Evict open research dataset

Hello Hugging Face Datasets team,

I am Soroush Vahidi, preparing the LAFC-Evict dataset for reproducible research on learning-augmented caching and cache-eviction supervision. The dataset supports academic work on decision-aligned eviction-value prediction and is intended for public reuse by systems and machine-learning researchers.

We are first publishing a small public preview at:

`TODO: https://huggingface.co/datasets/SoroushVahidi/lafc-evict`

The preview is intentionally compact and community-reviewable:

- public dataset repository;
- Parquet format;
- approximately 134 MB;
- 4.8M derived rows;
- two configs, `cross_family_evict_value_v1` and `objective_ablation_scalar`;
- Wiki2018-only source scope;
- source provenance and licensing reviewed before upload;
- no raw trace rows or raw Wikimedia page titles;
- deterministic public object pseudonyms.

The full curated release would be useful to the research community because it provides reproducible, derived supervision rows for learning-augmented caching experiments without requiring users to rerun large local derivation pipelines. We plan to keep the release efficient and avoid unnecessary raw duplication.

Current local derived source trees are much larger than the proposed public preview:

- objective-ablation CSV tree: approximately 121 GB;
- cross-family CSV tree: approximately 93 GB;
- optional historical corpus: approximately 96 GB.

Based on local preview compression measurements, the current objective-ablation plus cross-family material is estimated to compress to roughly 12 GB as curated Parquet. The exact full-release scope will remain subject to source-family licensing/provenance review, and families without clear redistribution status will remain excluded.

Additional Hugging Face public storage would support:

- a full curated Parquet release rather than ad hoc local-only archives;
- reproducible benchmarks for the associated research;
- standard Hugging Face Dataset Viewer / Data Studio inspection;
- stable public versioning for future paper and artifact references;
- eventual local disk cleanup only after public preservation is verified.

We are not requesting storage for unnecessary raw duplication. For larger private or mutable preservation needs, we may separately evaluate Hugging Face Storage Buckets or another archive mechanism, but the public dataset repository would contain curated, documented Parquet artifacts.

Supporting information to include before sending:

- final public dataset URL;
- public GitHub/project URL;
- associated manuscript/preprint URL;
- dataset card link;
- exact full-release size estimate and file count;
- early usage metrics if available;
- confirmation that all included source families passed provenance/licensing review.

Thank you for considering this request.

Soroush Vahidi

## Storage Strategy Notes

Preview publication:

- small;
- public;
- scientifically representative;
- suitable for establishing the public project.

Future full curated release:

- compressed Parquet;
- estimated around 12 GB for the current objective-ablation plus cross-family data;
- only includes source families that pass provenance review.

Private/raw preservation:

- potentially much larger;
- may later use Hugging Face Storage Buckets or another archival system;
- should not be treated as replaced by the 134 MB public preview.
