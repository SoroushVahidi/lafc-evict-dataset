# LAFC-Evict Scientific Evidence Index

This index maps each current scientific question to the repository artifact that
supports it. It is a navigation aid; the frozen reports remain the source of
exact numbers.

| Question / area | Evidence artifact | Branch / commit | Status | Key conclusion | Next action |
|---|---|---|---|---|---|
| Target discriminativeness | `analysis/sigmod_target_discriminativeness_20260913/` | `analysis/sigmod-target-discriminativeness-20260913` / `76d562f` | Frozen evidence | `B = CONDITIONALLY DISCRIMINATIVE`; labels are highly tie-dominated overall, but MetaCDN/Twemcache cap32 H16 are substantially more discriminative; wiki2018 is fully degenerate. | Integrate honestly into the journal manuscript and reviewer response. |
| Pairwise provenance | `analysis/pairwise_provenance_repair_20260913/` | `analysis/sigmod-target-discriminativeness-20260913` / `76d562f` | Frozen evidence plus durability risk | Historical shipped pairwise sample is noncanonical; regenerated canonical sample has balanced direction counts and SHA256 `1d770c6999ac999673b46805a6ca173e24b116793b35405d2d211cae7b9eda02`. | Decide durable preservation/release handling for the regenerated Parquet under `/tmp`. |
| Predictor feature issue | Target audit and pairwise repair reports | `76d562f` | Documented unresolved issue | `candidate_is_predictor_victim == candidate_is_lru_victim` across audited canonical data; related predictor fields include constants/placeholders. | Avoid unsupported predictor-field claims; fix upstream generation only in a separate authorized task. |
| Closed-loop pilot | `analysis/closed_loop_pilot_20260913/` | `experiment/closed-loop-pilot-20260913` / `983d7d0` | Frozen evidence | `B = MIXED`; LRU/random/MRU offline H=16 ordering agrees with closed-loop ordering on MetaCDN and Twemcache cap32; learned policy beats random/SIEVE but loses to LRU on Twemcache; MetaCDN learned policy blocked. | Use as feasibility evidence and retain exact split caveats. |
| Production closed-loop design | `analysis/closed_loop_production_design_20260913/` | `experiment/closed-loop-production-design-20260913` / `adc7c64` | Designed, not run | Tier 1 covers five families, capacities 32 and 128, LRU/MRU/random/SIEVE, random seeds 0..19; Tier 2 is narrow and approval-gated. | Run and validate Tier 1 only after design review. |
| Performance Evaluation manuscript | `paper/performance_evaluation/` | `manuscript/performance-evaluation-template-20260913` / `471b3c4` | Separate manuscript branch | Elsevier migration and acknowledgments/funding are complete; scientific reviewer revision is not incorporated. | Do not rewrite until production evidence is available or the user explicitly chooses a manuscript-only revision. |
| Public v0.3 release | `dataset_card/`, `publication/`, `docs/LAFC_EVICT_PUBLICATION_STATE.md` | `polish/final-handoff-20260914` after Query 2 | Current public status | v0.3 is wiki2018-only on Hugging Face and AWS Open Data; Zenodo remains v0.2 DOI-backed; public v0.3 is not the five-family scientific dataset. | Keep public/canonical distinction prominent in all future release docs. |
| Continuation-policy sensitivity | No completed experiment | n/a | Not run | Closed-loop replay does not test how labels change under alternative continuation policies. | Design and run a separate continuation-policy sensitivity experiment if needed for reviewer response. |
| Related-work/citation state | `paper/sigmod2027/latex/refs.bib`, related-work notes, manuscript branches | Multiple historical branches | Incomplete | Several references are present but need metadata checks; Cache-Coliseum, Learning Caching Policies with Subsampling, DAgger, Park, and QD-LP are high-priority gaps. | Verify against authoritative sources before editing bibliography metadata. |

## Current Hypothesis Summary

| Hypothesis | Current state |
|---|---|
| H_TARGET | CONDITIONALLY SUPPORTED |
| H_OFFLINE_CLOSED_LOOP | SUPPORTED IN PILOT ONLY |
| H_LEARNED_POLICY | NOT SUPPORTED AS SUPERIOR TO LRU |
| H_WIKI | NOT SUPPORTED AS A DISCRIMINATIVE SUPERVISED TARGET |
| H_CONTINUATION | UNKNOWN / NOT TESTED |
| H_PRACTICAL_USE | PARTIALLY SUPPORTED AND STRENGTHENED BY PILOT |
| H_PAIRWISE | OLD SHIPPED SAMPLE NOT CANONICAL |
