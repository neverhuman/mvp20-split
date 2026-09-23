#!/usr/bin/env python3
"""R-C04 fire-2: rights-boundary audit of the remediation path proposed by
fire 1's checkpoint (cluster-bootstrap-data-audit-v1). Fire 1 characterized
the missing per-row prediction arrays as a pure 'pipeline re-run-and-persist
gap' requiring 'no rights review... derives from the same already-cleared,
non-quarantined model-fitting step'. This script checks that claim by hash
comparison against the module's own quarantine metadata. Reads only
already-signed JSON bytes and quarantine *metadata* files (rights.json,
acquisition-receipt.json, manifest.json) -- never opens, parses, or derives
from the quarantined row-level CSV/JSONL.GZ payload itself."""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-viscosity-score"


def sha(b):
    return hashlib.sha256(b).hexdigest()


def load_json(p):
    raw = p.read_bytes()
    return json.loads(raw), sha(raw)


out = {"files_examined": {}}

ffw_receipt_path = MOD / "reference/mvp20/data/polyverse_melt_viscosity_fox_flory_whitten_physical_baseline_receipt.v1.json"
ffw, ffw_sha = load_json(ffw_receipt_path)
out["files_examined"]["ffw_receipt"] = {"path": str(ffw_receipt_path.relative_to(ROOT)), "raw_file_sha256": ffw_sha}
ffw_input_csv_sha256 = ffw["input_csv_sha256"]

ml_receipt_path = MOD / "reference/mvp20/data/polyverse_melt_viscosity_model_receipt.v1.json"
ml, ml_sha = load_json(ml_receipt_path)
out["files_examined"]["ml_model_receipt"] = {"path": str(ml_receipt_path.relative_to(ROOT)), "raw_file_sha256": ml_sha}
ml_dataset_csv_sha256 = ml["dataset_local_csv_sha256"]
ml_dataset_csv_path = ml["dataset_local_csv_path"]

acq_path = MOD / "reference/mvp20/manifests/polyverse_melt_viscosity.acquisition-receipt.json"
acq, acq_sha = load_json(acq_path)
out["files_examined"]["acquisition_receipt"] = {"path": str(acq_path.relative_to(ROOT)), "raw_file_sha256": acq_sha}

mani_path = MOD / "reference/mvp20/manifests/polyverse_melt_viscosity.json"
mani, mani_sha = load_json(mani_path)
out["files_examined"]["normalized_dataset_manifest"] = {"path": str(mani_path.relative_to(ROOT)), "raw_file_sha256": mani_sha}

rights_path = MOD / "reference/mvp20/quarantine/feedback_v2/exclusions/polyverse_melt_viscosity-3cd923b4d67399f9.rights.json"
rights, rights_sha = load_json(rights_path)
out["files_examined"]["rights_decision"] = {"path": str(rights_path.relative_to(ROOT)), "raw_file_sha256": rights_sha}

fire1_ckpt_path = MOD / "evidence/phase0/repairs/R-C04/attempts/cluster-bootstrap-data-audit-v1/cluster-bootstrap-data-audit-v1-receipt.v1.dsse.json"
fire1_env, fire1_env_sha = load_json(fire1_ckpt_path)
out["files_examined"]["fire1_checkpoint_receipt"] = {"path": str(fire1_ckpt_path.relative_to(ROOT)), "raw_file_sha256": fire1_env_sha}
import base64
fire1_body = json.loads(base64.b64decode(fire1_env["signature"]["payload"]))
fire1_human_action_needed = fire1_body["human_action_needed"]
fire1_no_rights_review_claim_present = ("no rights review" in fire1_human_action_needed.lower())

def sha_eq(a, b):
    return a == b

checks = {
    "ffw_input_csv_sha256": ffw_input_csv_sha256,
    "ml_dataset_local_csv_sha256": ml_dataset_csv_sha256,
    "acquisition_receipt_raw_sha256": acq["sha256"],
    "acquisition_receipt_quarantined_flag": acq["quarantined"],
    "manifest_raw_sha256": mani["raw_sha256"],
    "manifest_quarantined_flag": mani["quarantined"],
    "manifest_rights_class": mani["rights_class"],
    "rights_decision_rights_class": rights["decision"]["rights_class"],
    "rights_decision_promotion_eligible": rights["decision"]["promotion_eligible"],
    "rights_decision_basis": rights["decision"]["basis"],
    "rights_decision_license": rights["decision"]["license"],
}

all_four_hashes_equal = (
    sha_eq(ffw_input_csv_sha256, ml_dataset_csv_sha256)
    and sha_eq(ffw_input_csv_sha256, acq["sha256"])
    and sha_eq(ffw_input_csv_sha256, mani["raw_sha256"])
)

fire1_claim_refuted_by_hash_evidence = (
    all_four_hashes_equal
    and acq["quarantined"] is True
    and mani["quarantined"] is True
    and mani["rights_class"] == "CONTEXT_ONLY"
    and "quarantine all derivatives" in rights["decision"]["basis"].lower()
)

# positive control on the comparison logic itself: plant a mismatched hash
# and confirm the equality check correctly reports False
planted_mismatch_sha = "0" * 64
positive_control_fires = not sha_eq(ffw_input_csv_sha256, planted_mismatch_sha)

out["checks"] = checks
out["conclusion"] = {
    "ffw_b3_and_ml_b4_fit_against_byte_identical_input_csv": all_four_hashes_equal,
    "that_input_csv_is_the_quarantined_raw_object": acq["quarantined"] is True and mani["quarantined"] is True,
    "quarantine_basis_text": rights["decision"]["basis"],
    "quarantine_covers_derivatives_not_just_raw_file": "quarantine all derivatives" in rights["decision"]["basis"].lower(),
    "fire1_human_action_needed_text": fire1_human_action_needed,
    "fire1_asserted_no_rights_review_needed": fire1_no_rights_review_claim_present,
    "fire1_claim_refuted_by_hash_evidence": fire1_claim_refuted_by_hash_evidence,
    "reasoning": (
        "Both signed lineage artifacts for R-C04's target claim -- the FFW "
        "physical-baseline receipt (input_csv_sha256) and the parent ML B4 "
        "HistGBM model receipt (dataset_local_csv_sha256) -- were fit "
        "against a CSV whose sha256 is byte-identical to the raw_sha256 "
        "recorded in this module's own quarantine acquisition-receipt.json "
        "and normalized-dataset manifest.json for the Polyverse "
        "melt-viscosity dataset (quarantined=true, rights_class="
        "CONTEXT_ONLY). The rights decision's own basis text explicitly "
        "extends the quarantine to 'all derivatives', not just the raw "
        "file. Producing the per-row prediction arrays R-C04's "
        "pre-registered protocol needs (test_row_polymer_id, "
        "test_row_y_true, test_row_y_pred_B3, test_row_y_pred_B4) requires "
        "re-running the identical fitting step against this identical "
        "quarantined-raw-hash CSV and persisting a NEW derivative artifact "
        "-- exactly what 'physically quarantine all derivatives' covers. "
        "Fire 1's checkpoint receipt asserted the opposite ('no rights "
        "review is needed... not the quarantined row-level CSV') without "
        "checking the hash; that assertion is refuted by this comparison. "
        "The correct remediation path is therefore blocked on the same "
        "pending counsel review already flagged by R-A03/mission.md, not "
        "on an unblocked engineering re-run."
    ),
    "positive_control_on_comparison_logic": {
        "planted_defect": "mismatched sha256 (64 zero chars) compared against real ffw_input_csv_sha256",
        "how_planted": "substituted the real hash string with '0'*64 in one operand of the equality check",
        "detected": positive_control_fires,
        "evidence": f"sha_eq(real, planted_zero_hash) == {sha_eq(ffw_input_csv_sha256, planted_mismatch_sha)}; comparison correctly reports mismatch",
    },
}

body = json.dumps(out, indent=2, sort_keys=True).encode()
outpath = Path(sys.argv[1]) if len(sys.argv) > 1 else (Path(__file__).parent / "diagnostic.canonical.json")
outpath.write_bytes(body)
print("WROTE", outpath, "sha256", sha(body))
