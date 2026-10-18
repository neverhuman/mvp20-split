# Amphora | Current engineering verification

Receipts in this directory describe actual local checks, independently from what the attachments reported.

- `source_python312.json`: exact source-profile invocation, timestamp, platform, elapsed time, original twelve-gate nested report, PLGA aggregate check and fresh static boundary check.
- `pinned_arithmetic.json`: same source profile with NumPy 1.26.4 in a task-local Python 3.12 environment; four pilot intervals, ten stage-2 intervals and Holm recomputed; zero fits.
- `missing_dependency.json`: plain Python 3.12 without NumPy returns the expected exit 3 for requested bootstrap, with no silent downgrade.
- `tooling_test_receipt.json` and `coverage.json`: focused functional suite and measured line/branch coverage. Renderer/projection verification is a separate artifact tier and is not implied by core coverage.
- `preservation.json`: final diff/source checks against the pinned baseline; no scientific, historical evidence or production edits.
- `pdf_visual_qa.json`: final workplan PDF hash/page count, text/font checks and all-page inspection.
- `scoped_drift_audit.md`: current tooling/module/plan alignment and explicitly planned follow-ups.

Recorded original acceptance inside a fresh hash/assertion check remains historical execution. A current arithmetic receipt is not a new scientific cohort or current installed-service acceptance. The internal capsule remains unqualified for investor distribution until its separate disclosure/editorial/package gates pass.
