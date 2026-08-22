#!/usr/bin/env python3
"""DSSE-Ed25519-sign the R-C04 fire-2 rights-boundary-audit checkpoint
(CAMPAIGN-mode fire, fire_id 20260812T050001-574491-f43fd01f90c2).
AUDIT_ONLY / repair-checkpoint: does NOT supersede the FFW-vs-ML KPI
(acceptance still not met -- now rights-blocked, not just data-blocked),
does NOT edit any existing signed receipt, docs/mission.md (already
carries the correct rights caveat), or the 66-receipt master manifest,
does NOT open the quarantined Polyverse row-level CSV. Corrects (via a
supersedes block, never a rewrite) the remediation-path characterization
in fire 1's checkpoint receipt."""
import base64
import hashlib
import json
import subprocess
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-viscosity-score"
EV = MOD / "evidence/phase0/repairs/R-C04/attempts/rights-boundary-audit-v1"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
REVIEWER_SEED = SEED_DIR / "internal-reviewer.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"
FIRE_ID = "20260812T050001-574491-f43fd01f90c2"
FIRE1_CKPT = MOD / "evidence/phase0/repairs/R-C04/attempts/cluster-bootstrap-data-audit-v1/cluster-bootstrap-data-audit-v1-receipt.v1.dsse.json"


def sha(b):
    return hashlib.sha256(b).hexdigest()


def pae(t, body):
    return (b"DSSEv1 " + str(len(t)).encode() + b" " + t.encode() + b" " +
            str(len(body)).encode() + b" " + body)


def load_seed(p):
    raw = p.read_bytes().strip()
    if len(raw) == 64:
        try:
            return bytes.fromhex(raw.decode())
        except Exception:
            pass
    return raw[:32]


canon = (EV / "diagnostic.canonical.json").read_bytes()
runB = (EV / "diagnostic.runB.json").read_bytes()
assert canon == runB, "two-replay bytes differ"
diag_sha = sha(canon)
diag = json.loads(canon)
assert diag["conclusion"]["fire1_claim_refuted_by_hash_evidence"] is True

# independent 3rd confirmatory replay into a temp path
third = EV / "diagnostic.runC.tmp.json"
subprocess.run(["python3", str(EV / "run_rights_boundary_audit.py"), str(third)],
               check=True, cwd=str(EV))
third_sha = sha(third.read_bytes())
third.unlink()
assert third_sha == diag_sha, f"3rd replay FAIL {third_sha} != {diag_sha}"

harness_sha = sha((EV / "run_rights_boundary_audit.py").read_bytes())
fire1_ckpt_sha256 = sha(FIRE1_CKPT.read_bytes())

eval_sk = Ed25519PrivateKey.from_private_bytes(load_seed(EVAL_SEED))
eval_pub = eval_sk.public_key().public_bytes_raw()
eval_pub_hex = eval_pub.hex()
eval_key_id = f"phase0-evaluator-{sha(eval_pub)}"
rev_sk = Ed25519PrivateKey.from_private_bytes(load_seed(REVIEWER_SEED))
rev_pub_hex = rev_sk.public_key().public_bytes_raw().hex()
rev_key_id = f"phase0-internal-reviewer-{sha(bytes.fromhex(rev_pub_hex))}"
trust = json.loads(TRUST.read_text()) if TRUST.exists() else {"keys": []}
tbr = {k.get("role"): k for k in trust.get("keys", [])}
eval_pin = (eval_key_id == tbr.get("PHASE0_EVALUATOR", {}).get("key_id"))
rev_pin = (rev_key_id == tbr.get("PHASE0_INTERNAL_REVIEWER", {}).get("key_id"))

body_obj = {
    "schema": "amphora.viscosity-score.r-c04-rights-boundary-audit-checkpoint.v1",
    "receipt_id": "rights-boundary-audit-v1",
    "campaign_item_id": "R-C04",
    "module_id": "amphora-viscosity-score",
    "authority": "AUDIT_ONLY",
    "authority_ceiling": "EVIDENCE_ONLY",
    "phase": "PRE_PHASE_0",
    "mode": "CAMPAIGN",
    "fire_id": FIRE_ID,
    "fire_number_of_max": "2 of 3",
    "date": "2026-08-12",
    "scientific_success_required_for_phase0": False,
    "promotes_authority": False,
    "flips_scientific_readiness": False,
    "modifies_manifest": False,
    "modifies_mission_md": False,
    "modifies_signed_phase0_kpi": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "derives_from_quarantined_row_data": False,
    "repair_status": "in_progress",
    "verdict": "BLOCKED_RIGHTS",
    "objective_under_repair": (
        "R-C04: pre-registered cluster bootstrap (resample the 13 test "
        "polymers with replacement, B=5000, seed=0) of the R2 difference "
        "(FFW_B3 - ML_B4) on the identical seed-0 partition from the KPI, "
        "verified via the conformal_receipt_sha256 cross-link. Report the "
        "CI and supersede the FFW KPI with an honest restatement at "
        "whatever strength the interval supports."
    ),
    "claim_under_attack": (
        "amphora-viscosity-score/evidence/phase0/kpis/"
        "polyverse-melt-viscosity-fox-flory-whitten-physical-baseline-vs-ml-"
        "kpi.v1.json :: headline finding 'best_physical_ffw_baseline_beats_"
        "ml_r2_documented' (physical B3 R^2=+0.5972 beats ML B4 R^2=+0.4536 "
        "by +0.1436)."
    ),
    "why_blocked_rights_not_blocked_data": (
        "Fire 1 (fire_id 20260812T040001-4187595-821716c37e86) established "
        "BLOCKED_DATA: no signed artifact persists the per-row/per-polymer "
        "prediction arrays a cluster bootstrap needs. Its checkpoint "
        "receipt proposed a remediation path in its human_action_needed "
        "field: 're-run the harness... with per-row prediction logging "
        "enabled... no rights review is needed since it derives from the "
        "same already-cleared, non-quarantined model-fitting step, not the "
        "quarantined row-level CSV.' This fire checked that assertion by "
        "hash comparison instead of taking it on faith. Result: it is "
        "false. Both the FFW_B3 receipt's input_csv_sha256 and the parent "
        "ML B4 model receipt's dataset_local_csv_sha256 are byte-identical "
        "(3cd923b4d67399f9c201b06acb282ee82b3a85345e06ff74c0b9d6941265f811) "
        "to the raw_sha256 recorded in this module's own quarantine "
        "acquisition-receipt.json and normalized-dataset manifest.json for "
        "the Polyverse melt-viscosity dataset -- both flagged "
        "quarantined=true, rights_class=CONTEXT_ONLY. The rights decision's "
        "basis text ('Custom license requires counsel; physically "
        "quarantine all derivatives.') explicitly extends the quarantine "
        "beyond the raw file to all derivatives. Re-running the fitting "
        "harness with per-row logging enabled -- the exact remediation "
        "fire 1 proposed -- would necessarily re-consume this identical "
        "quarantined-hash CSV and persist a NEW derivative artifact "
        "(per-row prediction arrays), which is precisely what the "
        "quarantine-all-derivatives basis prohibits pending counsel "
        "review. Forward motion on R-C04's pre-registered protocol is "
        "therefore blocked on the same open counsel-review action already "
        "flagged by the sibling R-A03 repair and disclosed in "
        "docs/mission.md, not on an unblocked engineering re-run as fire "
        "1 characterized it."
    ),
    "attack": (
        "Rights-boundary audit of the remediation path proposed by fire "
        "1's checkpoint. Loaded the FFW_B3 physical-baseline receipt and "
        "the parent ML B4 model receipt and extracted their respective "
        "input-CSV sha256 fields (input_csv_sha256, "
        "dataset_local_csv_sha256). Loaded the module's own quarantine "
        "acquisition-receipt.json, normalized-dataset manifest.json, and "
        "rights.json for the Polyverse melt-viscosity dataset and "
        "extracted their raw_sha256/sha256, quarantined flag, rights_class, "
        "and decision.basis fields. Compared all four hashes for byte "
        "equality and cross-checked the quarantine flags and basis text. "
        "Also decoded fire 1's DSSE payload to extract its literal "
        "human_action_needed text and searched it for the phrase 'no "
        "rights review'. Positive control on the comparison logic itself: "
        "substituted a 64-zero-char mismatched hash for one operand and "
        "confirmed the equality check correctly reports False (detects a "
        "planted mismatch) before trusting its True result on the real "
        "hashes. Reads only already-signed downstream JSON bytes and "
        "quarantine *metadata* (rights.json / acquisition-receipt.json / "
        "manifest.json field values, never the quarantined row payload "
        "itself: quarantine/normalized/polyverse_melt_viscosity.jsonl.gz "
        "and quarantine/raw/objects/3cd923...  were never opened, read, "
        "or parsed by this script)."
    ),
    "hash_evidence": diag["checks"],
    "conclusion": diag["conclusion"],
    "positive_control": {
        "planted_defect": "mismatched sha256 (64 zero chars) substituted for the real ffw_input_csv_sha256 in one operand of the equality check used to detect fire 1's claim as refuted-or-not",
        "how_planted": "in run_rights_boundary_audit.py, computed sha_eq(ffw_input_csv_sha256, '0'*64) alongside the real sha_eq(ffw_input_csv_sha256, ml_dataset_csv_sha256) comparison",
        "detected": diag["conclusion"]["positive_control_on_comparison_logic"]["detected"],
        "evidence": diag["conclusion"]["positive_control_on_comparison_logic"]["evidence"],
        "note": (
            "This is a BLOCKED verdict, which the item does not require a "
            "positive control for (that requirement is specific to "
            "CLAIM_SURVIVED verdicts). Included anyway as a soundness check "
            "on the audit tool's own hash-comparison logic."
        ),
    },
    "supersedes": {
        "superseded_path": str(FIRE1_CKPT.relative_to(ROOT)),
        "superseded_sha256": fire1_ckpt_sha256,
        "superseded_deleted_or_modified": False,
        "reason": (
            "Fire 1's checkpoint remains on disk byte-identical and its "
            "BLOCKED_DATA verdict for that fire is not disputed (at the "
            "time, and still, no per-row arrays exist). What this receipt "
            "corrects is narrower: fire 1's human_action_needed field and "
            "the mirrored data-acquisition-queue.jsonl entry "
            "(fire_id 20260812T040001-4187595-821716c37e86) asserted the "
            "missing per-row arrays could be produced by an engineering "
            "re-run with 'no rights review needed... not the quarantined "
            "row-level CSV'. Hash comparison in this fire shows both "
            "FFW_B3 and ML_B4 were fit directly against the byte-identical "
            "quarantined raw CSV, and the rights decision's basis extends "
            "quarantine to all derivatives -- so that specific remediation "
            "claim was incorrect and is superseded by this receipt's "
            "corrected characterization: the remediation path is "
            "rights-blocked, not merely an unblocked pipeline re-run."
        ),
    },
    "human_action_needed": (
        "Counsel review of the Georgia Tech Research Corporation General "
        "Public Use License Agreement governing the Polyverse "
        "melt-viscosity dataset "
        "(reference/mvp20/quarantine/feedback_v2/exclusions/"
        "polyverse_melt_viscosity-3cd923b4d67399f9.rights.json, "
        "rights_decision_id rights_polyverse_melt_viscosity), specifically "
        "to determine: (1) whether the three ALREADY-SIGNED Polyverse "
        "receipts currently indexed in the 66-receipt master manifest "
        "(model, FFW baseline, conformal+AD) may remain evidence-only as "
        "they are today, and separately (2) whether producing ONE "
        "additional narrow derivative -- signed per-row/per-polymer "
        "actual-vs-predicted arrays for the SAME B3/B4 models already "
        "fit and disclosed, used only to compute an uncertainty interval "
        "around an already-published aggregate statistic, not to train a "
        "new model or extend coverage -- falls inside or outside the "
        "'physically quarantine all derivatives' basis. This is the same "
        "underlying counsel action already flagged pending by R-A03 and "
        "docs/mission.md's standing rights caveat; this receipt narrows "
        "it to the specific R-C04 acceptance-blocking question."
    ),
    "does_not_close": [
        "Does not modify the FFW KPI, the FFW scientific receipt, the "
        "conformal+AD KPI or receipt, docs/mission.md (already correctly "
        "discloses the quarantine-all-derivatives basis), or the "
        "66-receipt master manifest.",
        "Does not edit, delete, or modify fire 1's checkpoint receipt or "
        "the data-acquisition-queue.jsonl line it mirrored -- both remain "
        "byte-identical; this receipt supersedes only the narrower "
        "remediation-path claim within them.",
        "Does not open, parse, or derive any value from the underlying "
        "quarantined Polyverse melt-viscosity row-level CSV or its "
        "quarantine/normalized/*.jsonl.gz form -- reads only rights "
        "metadata field values (flags, hashes, basis text).",
        "Does not assert the B3/B4 R^2 point estimates or the FFW-beats-ML "
        "finding are numerically wrong -- takes no position on the "
        "underlying physics-beats-ML finding, and does not compute any "
        "bootstrap interval.",
        "Does not itself resolve the CONTEXT_ONLY/promotion_eligible=false "
        "rights question -- that remains the pending human/counsel action.",
    ],
    "provenance": {
        "harness_sha256": {"run_rights_boundary_audit.py": harness_sha},
        "inputs_sha256": {k: v["raw_file_sha256"] for k, v in diag["files_examined"].items()},
    },
    "reproducibility": {
        "byte_identical": True,
        "two_replay_sha256_gate": "PASS",
        "third_confirmatory_replay": "PASS",
        "canonical_diagnostic_sha256": diag_sha,
        "runB_diagnostic_sha256": sha(runB),
        "third_replay_sha256": third_sha,
        "determinism": (
            "pure-python re-derivation from already-in-tree, already-hashed "
            "JSON files; no RNG, no network, no wall-clock reads at run "
            "time."
        ),
    },
    "signing_key": {
        "key_id": eval_key_id,
        "public_key_hex": eval_pub_hex,
        "role": "PHASE0_EVALUATOR",
        "signs_phase0_evaluation_or_review": False,
        "derives_pinned_trust_store_key_id": eval_pin,
        "used_for": "AUDIT_ONLY R-C04 checkpoint receipt under evidence/phase0/repairs/R-C04/attempts/",
    },
    "reviewer_reference": {
        "key_id": rev_key_id,
        "public_key_hex": rev_pub_hex,
        "role": "PHASE0_INTERNAL_REVIEWER",
        "derives_pinned_trust_store_key_id": rev_pin,
        "reviewer_signature_present": False,
        "note": "Reviewer key referenced for provenance only; no independent human review performed.",
    },
}
body = json.dumps(body_obj, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.viscosity-score-r-c04-rights-boundary-audit-checkpoint+json"
sig = eval_sk.sign(pae(ptype, body))
sig_b64 = base64.standard_b64encode(sig).decode()
envelope = {
    "evaluator_key_id": eval_key_id,
    "evaluator_public_key_hex": eval_pub_hex,
    "reviewer_public_key_hex": rev_pub_hex,
    "signature": {
        "payload": base64.standard_b64encode(body).decode(),
        "payloadType": ptype,
        "signatures": [{"keyid": eval_key_id, "sig": sig_b64}],
    },
}
out = EV / "rights-boundary-audit-v1-receipt.v1.dsse.json"
out.write_text(json.dumps(envelope, indent=2, sort_keys=True))
print("WROTE", out)
print("receipt_body_sha256", sha(body))
print("envelope_sha256", sha(out.read_bytes()))
