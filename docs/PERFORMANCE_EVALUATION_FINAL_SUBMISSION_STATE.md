# Performance Evaluation Final Submission State

Recorded on **2026-09-17**.

## Submission Metadata

- **Final Master SHA:** `7906ade0aaffa9a8227bcc549be5426f3563e9cb`
- **Final PDF Path:** `paper/performance_evaluation/LAFC-Evict-A-Large-Scale-Counterfactual-Benchmark-for-Learned-Cache-Eviction.pdf`
- **Final PDF SHA-256:** `29a2b417de4d8883367d7c442549e9a9924cde41b5c8caa14c3ad33357c03715`
- **Final Page Count:** 53 pages
- **Build Command:** `latexmk -pdf main.tex` (executed inside `paper/performance_evaluation/latex/`)
- **Build Status:** PASS (0 errors, 0 undefined references, 0 undefined citations, 0 multiply-defined labels)
- **Repository URL:** `https://github.com/SoroushVahidi/lafc-evict-dataset`

## Dataset Release State

- **Hugging Face Release:** LAFC-Evict v1.0 (Revision `v1.0`, Commit `37173bc96de2a615455bf9713bb90d846156af29`)
  - Includes full five-family (Alibaba Block, MetaCDN, MetaKV, Twemcache, Wiki2018) derived supervision.
  - Scale: 277,995,072 candidate-level rows, 2,363,286 decision-horizon rows, and 1,000,000 canonical pairwise sample rows.
- **AWS Open Data:** Hosts older v0.3 wiki2018-only payload.
- **Zenodo:** Archives v0.2 preview only (DOI `10.5281/zenodo.21895844`).

## Related Manuscript Disclosure

A related manuscript currently under consideration at *Knowledge-Based Systems* focuses on the design and closed-loop evaluation of a learned cache-eviction model/policy. The present *Performance Evaluation* manuscript instead focuses on the LAFC-Evict counterfactual dataset and evaluation benchmark, including target characterization, degeneracy, horizon/capacity sensitivity, continuation robustness, offline–closed-loop correspondence, expanded comparator robustness, and release methodology. The two works share some underlying caching infrastructure and counterfactual-label concepts, and this related submission is disclosed transparently in our cover letter.

## Verdict

No further manuscript edits are planned before submission.