#!/usr/bin/env python3
"""R-N02: APPEND (never rewrite) RETRACTION-INDEX entries in
amphora-molecule-property and amphora-molecule-role-ranker."""
import hashlib
from pathlib import Path

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MP_IDX = ROOT / "amphora-molecule-property/evidence/phase0/kpis/RETRACTION-INDEX.md"
RR_IDX = ROOT / "amphora-molecule-role-ranker/evidence/phase0/kpis/RETRACTION-INDEX.md"

MP_BEFORE = "76cd68e99762cc08b428a50519723efd891921725546b0c2e82d47ec7ad30c7a"
RR_BEFORE = "9da29c64684383f17ef8a7dec013244d60332db512b97899e710fd575f11252f"

DONE_FFI = "amphora-rdkit-ffi/evidence/phase0/repairs/R-N02/done/rn02-rdkit-ffi-coordinated-cn-fix-repair-receipt.v1.dsse.json"
DONE_MP = "amphora-molecule-property/evidence/phase0/repairs/R-N02/done/rn02-molecule-property-coordinated-cn-fix-repair-receipt.v1.dsse.json"
DONE_RR = "amphora-molecule-role-ranker/evidence/phase0/repairs/R-N02/done/rn02-molecule-role-ranker-coordinated-cn-fix-repair-receipt.v1.dsse.json"


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


assert sha(MP_IDX) == MP_BEFORE, "property RETRACTION-INDEX drifted before append"
assert sha(RR_IDX) == RR_BEFORE, "role-ranker RETRACTION-INDEX drifted before append"

ffi_sha, mp_sha, rr_sha = sha(ROOT / DONE_FFI), sha(ROOT / DONE_MP), sha(ROOT / DONE_RR)

OPEN = (
    "Quantitative question EXPLICITLY LEFT OPEN: whether guanidine/amidine N-H is exactly 0 in an "
    "AHEW / equivalent-weight sense is a mechanistic nucleophilicity question that R-N02 does NOT close "
    "(both refuting receipts scoped themselves the same way). R-N02 repairs CATEGORICAL CLASSIFICATION ONLY."
)

MP_ENTRY = f"""
## R-N02 - coordinated C=N (amidine/guanidine) categorical fix (interactive-2026-08-03)

Scope note: GENERALIZATION CLAIM ONLY is retracted. The amine-class receipt's arithmetic on its own 26
records is NOT retracted - all 26 (3 exact anchors + 6 monodisperse + 13 amine-class grid + 7 nonamine
controls + 1 hydroxyl probe) were re-derived pre- and post-fix and are byte-identical. The shipped rule
`n_active_amine_nh()` now excludes an N-H whose attached carbon bears a C=N double bond to another
nitrogen, symmetric with the pre-existing C=O/C=S amide exclusion; the extension was adopted verbatim from
the refuting receipt's own prototype ({{"O","S"}} -> {{"O","S","N"}}). The original refuting attack, re-run
UNMODIFIED, now returns SURVIVED. {OPEN}

| claim | refuted-by receipt path | superseded-by | date |
|---|---|---|---|
| `amphora-molecule-property/benchmarks/amine-class-active-nh-robustness-v1/amine_class_active_nh_robustness_receipt.v1.json` (sha256 `74e2c759...`) generalizes its active-N-H structure rule to the amine-hardener structure class as a whole (`amine_grid_classification_accuracy` 1.0, `nonamine_fail_closed_rate` 1.0 beyond the 13 tested structures) - i.e. guanidine/amidine-class curing agents are correctly classified | `amphora-molecule-property/evidence/audit/amine-nh-guanidine-conjugation-gap-v1/amine-nh-guanidine-conjugation-gap-receipt.v1.dsse.json` (sha256 `59c447c0...`, verdict REFUTED; guanidine/DICY/biguanide counted 4/4/5 active N-H, yielding a confident finite theoretical AHEW e.g. DICY 21.02 g/eq) | `{DONE_MP}` (sha256 `{mp_sha}`) - coordinated with `{DONE_FFI}` (sha256 `{ffi_sha}`) and `{DONE_RR}` (sha256 `{rr_sha}`) | 2026-08-03 |

Original receipts left byte-intact in place (supersede-never-rewrite); before/after sha256 of every signed
artifact in scope recorded in the R-N02 done-receipt payloads.
"""

RR_ENTRY = f"""
## R-N02 - coordinated C=N (amidine/guanidine) categorical fix (interactive-2026-08-03)

Scope note: GENERALIZATION INFERENCE ONLY is retracted. The flagship KPI's
`structural_inference_agreement_rate` = 1.0 ARITHMETIC STANDS and the KPI file is unmodified: the sha-locked
39-record fixture contains no amidine/guanidine record, so no fixture record was ever mis-scored by this bug -
independently re-verified under R-N02 by re-deriving all 39 records through the REAL production RDKit FFI both
pre- and post-fix (byte-identical, and 39/39 agreeing with the fixture's own recorded facts). What was refuted
is the inference that the deterministic role rule fails closed on real out-of-domain accelerator chemotypes
generally. The guanidine chemotype is now handled: `bridge.cc::count_reactive_amine_hydrogens` excludes N-H on
an amidine/guanidine carbon (C=N), so DPG and DOTG derive count 0 and fail closed to `out_of_domain`. New
regression tests through the real FFI: `amphora-molecule-capabilities/src/lib.rs::role_ranker_fails_closed_on_guanidine_class_accelerators_via_real_ffi`
and `amphora-rdkit-ffi/src/lib.rs::pinned_native_backend_excludes_guanidine_class_amine_hydrogens` (DPG, DOTG,
guanidine, DICY, biguanide). The original refuting attack, re-run UNMODIFIED, now returns
HYPOTHESIS_CORROBORATED (2/2 probes pass, 0 disagreements); the earlier live-runtime hostile-null probe still
passes 9/9. The sha-locked fixture was NOT edited; `reference/phase0-role-known-answer.v2.json` was created
alongside with the 39 v1 records byte-identical plus the 5 guanidine-class `out_of_domain` records the
refuting receipts' follow-ups asked for (evidence only; the signed KPI remains bound to v1). {OPEN}

| claim | refuted-by receipt path | superseded-by | date |
|---|---|---|---|
| The generalization inference from `amphora-molecule-role-ranker/evidence/phase0/kpis/role-classification-kpi.v1.json` (sha256 `88689040...`, `structural_inference_agreement_rate` 1.0) plus the prior `role-live-runtime-domain-probe-v1` SURVIVED verdict: that the deterministic role rule fails closed on real out-of-domain accelerator/catalyst chemotypes generally | `amphora-molecule-role-ranker/benchmarks/role-guanidine-accelerator-domain-probe-v1/replay_receipt.v1.dsse.json` (sha256 `414a68af...`, verdict CLAIM_REFUTED; DPG CAS 102-06-7 and DOTG CAS 97-39-2 classified `hardener` with `reactive_amine_hydrogen_count` 3 through the real FFI) | `{DONE_RR}` (sha256 `{rr_sha}`) - coordinated with `{DONE_FFI}` (sha256 `{ffi_sha}`) and `{DONE_MP}` (sha256 `{mp_sha}`) | 2026-08-03 |

Original receipts and the sha-locked fixture left byte-intact in place (supersede-never-rewrite); before/after
sha256 of every signed artifact in scope recorded in the R-N02 done-receipt payloads.
"""

with MP_IDX.open("a") as f:
    f.write(MP_ENTRY)
with RR_IDX.open("a") as f:
    f.write(RR_ENTRY)

print("APPENDED", MP_IDX, "sha256", sha(MP_IDX))
print("APPENDED", RR_IDX, "sha256", sha(RR_IDX))
# append-only proof: old bytes are still a prefix of the new file
assert Path(MP_IDX).read_bytes().endswith(MP_ENTRY.encode())
assert Path(RR_IDX).read_bytes().endswith(RR_ENTRY.encode())
print("append_only_verified", True)
