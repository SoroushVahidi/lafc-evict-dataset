# Technical Track

This directory tracks the technical work needed to turn the current preserved open release into a submission-ready SIGMOD benchmark package without mixing unvalidated results into the manuscript.

The main principle is synchronization:

- manuscript claims should be tied to a concrete source,
- result-producing jobs should be registered before their numbers enter the paper,
- anything not yet extracted or validated should remain marked as pending.

Current known-good lightweight state:

- repository tests passed,
- publication bundle validation passed,
- preserved open release metadata is available,
- full real-release validation is still pending and must not be represented as complete.

Files here:

- `statistics_jobs.md`: benchmark-statistics jobs and their data dependencies.
- `baseline_jobs.md`: minimum baseline experiments for the submission.
- `result_registry.md`: source-of-truth table for figures, tables, and key numbers.
- `full_validation_plan.md`: deferred full validation command and usage notes.
