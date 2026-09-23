# molecule-property EEW/AHEW benchmark — EXECUTED under pinned RDKit (v1)

**Authority:** AUDIT_ONLY · **Promotes nothing · Modifies no live config, receipt, manifest, split, or lock.**
**Date basis:** 2026-07-25 cron run (xbabe2).

## What this is

`amphora-molecule-property/evidence/phase0/receipts/evaluation.v1.dsse.json` is an
immutable, signed 2026-07-22 evaluation with:

    phase0_eligible    = false
    scientific_outcome = FAILED
    failed_gates       = ["SCIENTIFIC_BENCHMARK_NOT_EXECUTED"]
    benchmark_execution_complete = false

Root cause (module's own benchmark/result.v1.json): backend_status.available=false,
pinned_rdkit_2026_03_2_available=false, exact_controls_executed=0. The Rust benchmark
runner could not load the pinned RDKit 2026.03.2 shared libraries, so the EEW/AHEW
exact controls never ran and every scientific gate defaulted false.

This study EXECUTES that exact benchmark (amphora-molecule-property-eew-ahew-v1, all
four control classes + the frozen 300-molecule ChEBI-252 CC-BY truth set) under
RDKit 2026.03.2 loaded in Python, and recomputes every gate the failed result listed.

## Result — all 10 gates PASS, two-replay byte-identical

- pinned_rdkit_2026_03_2_available ...................... PASS (2026.03.2)
- all_exact_controls_executed .......................... PASS (3/3)
- equivalent_weight_max_abs_error_at_most_0_5 .......... PASS (max 0.0338 g/eq)
- reactive_group_counts_100_percent ................... PASS
- invalid_and_out_of_domain_rejection_100_percent ..... PASS (3/3 rejected)
- minimum_300_truth_set_molecules ..................... PASS (300)
- structure_identity_and_mass_agree .................. PASS
- monodisperse_within_tolerance ...................... PASS (6/6)
- technical_grade_lower_bound_directional ............ PASS (3/3)
- negative_control_pass_rate_100_percent ............. PASS (5/5)

In-scope exact anchors (two-part epoxy-amine coating stoichiometry):
- DGEBA EEW = 170.21 g/eq (expected 170.2), epoxide groups = 2
- DETA  AHEW = 20.63 g/eq (expected 20.6), active N-H = 5
- IPDA  AHEW = 42.57 g/eq (expected 42.6), active N-H = 4

Truth set (300 mol, ChEBI-252 CC-BY, canonical_smiles): formula 300/300, full InChIKey
300/300, stored RDKit MW 300/300, PubChem MW independence 299/300 (99.67%, one at the
0.05 g/mol selection boundary).

- diagnostic_sha256 = 218c560391c5bb75b94c7139003b3c21dc8d0a1867293156e732c6521024ba2c
- Two-replay: diagnostic.canonical.json == diagnostic.runB.json (byte-identical)
- Receipt: replay_receipt.v1.dsse.json, DSSE Ed25519, key local-9028773f49591193
  (LOCAL_DEVELOPMENT_AUDIT_ONLY, NOT trust-anchored)

## Conclusion

The molecule-property Phase-0 benchmark FAILURE is a missing-backend infrastructure gap,
NOT a scientific deficiency. The core coating chemistry (EEW/AHEW) is exact and the
identity truth set reproduces. This is the strongest genuinely-in-scope, rights-clean
science evidence in the portfolio.

## What this does NOT do (honest boundary)

It does NOT promote the module. Promotion needs a deliberate keyed supersession of the
immutable FAILED evaluation + bundle re-freeze + evaluate/review/promote, plus: wiring
the ChEBI source eligible in the census, embedding an independent_toolkit_receipt, wiring
the pinned RDKit backend INTO the Rust runner (LD_LIBRARY_PATH / rpath / FFI so
backend_status.available=true in-runner), and adding >=8 SEALED_CONTROL split rows. That
was deliberately deferred from autonomous cron to avoid a locked/half-wired state before
the founder report. This receipt de-risks that supersession.

## Reproduce

    python3 execute_eew_ahew_benchmark.py /tmp/a.json
    python3 execute_eew_ahew_benchmark.py /tmp/b.json
    cmp /tmp/a.json /tmp/b.json   # byte-identical
    python3 sign_eew_ahew_executed.py
