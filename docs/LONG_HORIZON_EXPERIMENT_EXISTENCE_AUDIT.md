> **Historical / pre-production note (added 2026-09-15, Query 2 preservation pass):**
> This audit was written at 2026-09-15 14:45:00, *before* the long-horizon
> Slurm DAG (production job 1288869, validation 1288880, aggregation 1288881)
> was submitted on Wulver. As of this note, that DAG is active (17/20
> production tasks completed, 3 running; validation/aggregation still
> dependency-pending). The findings below (H32/64/128/256 did not exist,
> regeneration required, recommended horizons {32,64,128}) reflect the state
> that *justified* launching the DAG, not the DAG's current progress or
> results. Do not treat this document as describing current experiment
> status — see the PE project handoff documentation for that. One
> discrepancy worth flagging for Query 3: `RECOMMENDED_SCOPE` below lists 7
> trace families (including brightkite and citibike), while the manuscript's
> evaluated corpus and the actual submitted DAG scope use 5 families
> (alibaba-block/cloudphysics, metacdn, metakv, twemcache, wiki2018) — this
> was not reconciled as part of this preservation pass.
>
> Original content follows unmodified below.

LONG_HORIZON_EXPERIMENT_EXISTENCE_AUDIT

AUDIT_TIME: 2026-09-15 14:45:00

LOCAL_REPO: /home/soroush/projects/lafc-evict-dataset/repo
BRANCH: master
HEAD: bba07270c2c78223316620ddfecd4772c4423a14
WORKTREE_CLEAN: true

CURRENT_MANUSCRIPT_HORIZONS: {4, 8, 16}

EXISTING_HORIZON_ARTIFACTS:
- artifact: paper/sigmod2027/results/candidate_label_stats/y_loss_summary.csv
- horizons: 4, 8, 16
- scope: 7 trace families, capacities 32, 64, 128, 256
- status: COMPLETE
- validation state: VALIDATED (used for manuscript)

- artifact: data/derived/evict_value_v1_wulver_heavy_r1 dataset (on Wulver / local archive)
- horizons: 4, 8, 16
- scope: 7 trace families, 4 capacities, sample (50,000 req/trace)
- status: COMPLETE
- validation state: VALIDATED

LONGER_HORIZON_SEARCH_RESULTS:

H32_EXISTS: NO
H64_EXISTS: NO
H128_EXISTS: NO
H256_EXISTS: NO

EXISTING_EQUIVALENT_EXPERIMENT:
NO

BEST_EXISTING_EVIDENCE:
No existing datasets or analyses cover horizons > 16. Existing evidence for discriminativeness is strictly restricted to H={4, 8, 16} and generated via the heavy_r1 dataset build.

CAN_EXISTING_DATA_ANSWER_WITHOUT_NEW_SIMULATION:
NO

REGENERATION_REQUIRED:
YES

GENERATOR_SUPPORTS_ARBITRARY_H:
YES

PROCESSED_TRACES_AVAILABLE_LOCAL: YES
PROCESSED_TRACES_AVAILABLE_WULVER: YES (However, brightkite and citibike appear missing from Wulver ls output, which needs verification)

WULVER_RELEVANT_EXISTING_RUNS:
Previous successful heavy_r1 dataset generation on Wulver produced H={4,8,16}. Job name: evictv1-dsgen, generated ~289M rows.

PARTIAL_OR_FAILED_RUNS:
- NONE

CURRENT_RUNNING_RELATED_JOBS:
- NONE

SCIENTIFIC_NECESSITY_CLASS:
E

RECOMMENDED_HORIZONS:
{32, 64, 128}. To directly address the reviewer concern, these values span up to 8x the previous maximum horizon (16). H=256 is not recommended initially because it risks colliding with trace/chunk boundaries (e.g. chunks of 4096) and significantly increasing simulation overhead per candidate.

RECOMMENDED_SCOPE:
families: brightkite, citibike, cloudphysics, metacdn, metakv, twemcache, wiki2018
capacities: 32, 64, 128, 256
horizons: 32, 64, 128
sample/full-population: sample (max 50,000 requests per trace)

RECOMMENDED_EXECUTION_STAGES:
1. correctness/preflight -> Validate generator bounds at H=128 on a single family (e.g., metacdn)
2. full production run -> All 7 families on Wulver

KNOWN_GOOD_SBATCH_TEMPLATE_SOURCE:
/home/sv96/lafc-work/Augmented-caching/slurm/evict_value_v1_wulver_dataset.sbatch

RECOMMENDED_WULVER_RESOURCES:
partition: general
account: NONE
cpus: 16
memory: 64G
walltime: 24:00:00
array shape: N/A

RESOURCE_ESTIMATE_CONFIDENCE:
HIGH

ESTIMATED_TOTAL_CPU_HOURS: 384
ESTIMATED_OUTPUT_SIZE: 30 GB

RISKS_OR_BLOCKERS:
- Missing traces on Wulver: brightkite and citibike processed traces were not found in a spot check of Wulver's data/processed/ directory.
- Chunk boundaries: High horizons (H=128) may truncate at chunk borders, reducing valid rows.

FILES_MODIFIED:
NONE

EXPERIMENT_LAUNCH_STATUS:
NOT_LAUNCHED

NEXT_ACTION:
Investigate and synchronize missing brightkite and citibike processed traces to Wulver, then execute the H=128 correctness/preflight stage locally or on Wulver.
