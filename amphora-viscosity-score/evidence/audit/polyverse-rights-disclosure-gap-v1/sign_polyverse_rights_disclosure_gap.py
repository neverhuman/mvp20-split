#!/usr/bin/env python3
"""DSSE-Ed25519-sign the amphora-viscosity-score Polyverse rights-disclosure-
gap finding (ROTATION-mode fire). AUDIT_ONLY: does NOT promote the module,
does NOT edit the three Polyverse melt-viscosity Phase-0 KPI receipts or
docs/mission.md, does NOT modify the 66-receipt master manifest, the
portfolio rights-report.json, or the sibling amphora-redteam-audit diagnostic,
does NOT extract or reproduce any row-level data from the quarantined
Polyverse dataset."""
import base64, hashlib, json, subprocess
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-viscosity-score"
EV = MOD / "evidence/audit/polyverse-rights-disclosure-gap-v1"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
REVIEWER_SEED = SEED_DIR / "internal-reviewer.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"


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
assert diag["verdict"] == "REFUTED", f"unexpected verdict {diag['verdict']}"
assert diag["disclosure_gap_confirmed"] is True

# independent 3rd confirmatory replay into a temp path
third = EV / "diagnostic.runC.tmp.json"
subprocess.run(["python3", str(EV / "run_disclosure_gap_audit.py"), str(third)],
               check=True, cwd=str(EV))
third_sha = sha(third.read_bytes())
third.unlink()
assert third_sha == diag_sha, f"3rd replay FAIL {third_sha} != {diag_sha}"

harness_sha = sha((EV / "run_disclosure_gap_audit.py").read_bytes())

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
    "schema": "amphora.viscosity-score.polyverse-rights-disclosure-gap-receipt.v1",
    "receipt_id": "polyverse-rights-disclosure-gap-v1",
    "module_id": "amphora-viscosity-score",
    "authority": "AUDIT_ONLY",
    "authority_ceiling": "EVIDENCE_ONLY",
    "phase": "PRE_PHASE_0",
    "scientific_success_required_for_phase0": False,
    "date": "2026-08-02",
    "fire_id": "20260802T180003-169208-c1eca54b47d0",
    "mode": "ROTATION",
    "promotes_authority": False,
    "flips_scientific_readiness": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "modifies_manifest": False,
    "modifies_mission_md": False,
    "modifies_signed_phase0_kpi": False,
    "modifies_portfolio_rights_report": False,
    "modifies_sibling_redteam_audit": False,
    "derives_from_quarantined_row_data": False,
    "claim_under_attack": diag["claim_under_attack"],
    "attack": (
        "Rights-disclosure-gap audit: cross-referenced amphora-viscosity-"
        "score's own rights-exclusion decision for the Polyverse melt-"
        "viscosity dataset (reference/mvp20/quarantine/feedback_v2/"
        "exclusions/polyverse_melt_viscosity-3cd923b4d67399f9.rights.json: "
        "rights_class=CONTEXT_ONLY, promotion_eligible=false, basis="
        "'Custom license requires counsel; physically quarantine all "
        "derivatives.', license=Georgia Tech Research Corporation General "
        "Public Use License Agreement) and the acquisition/dataset "
        "manifests (quarantined=true) against the portfolio rights-report.json "
        "(independently confirms CONTEXT_ONLY/ineligible), the 66-receipt "
        "master manifest (all 3 Polyverse melt-viscosity receipts indexed "
        "byte-identical as headline KPI evidence), the receipts themselves "
        "(none of the 3 self-declare CONTEXT_ONLY/rights status internally), "
        "and this module's own docs/mission.md (which presents the "
        "conformal+AD and Fox-Flory-Whitten-vs-ML results under 'Empirical "
        "benchmark result' headers, and the R^2=0.944 parent claim, with "
        "zero rights caveat -- no occurrence of 'context_only', 'georgia "
        "tech', 'promotion_eligible', or 'quarantine' anywhere in the file). "
        "A prior sibling audit (amphora-redteam-audit/benchmarks/"
        "rights-integrity-v1) already established the portfolio-level fact "
        "that these receipts lack internal rights self-declaration; this "
        "receipt establishes the narrower, module-owned fact that "
        "amphora-viscosity-score's own mission.md was never amended to "
        "disclose it, i.e. the gap between 'known at the audit layer' and "
        "'disclosed at the point of the claim' remains open specifically "
        "for this module."
    ),
    "refutation_criterion": diag["refutation_criterion"],
    "results": diag["results"],
    "receipt_checks": diag["receipt_checks"],
    "verdict": "REFUTED",
    "verdict_meaning": (
        "REFUTES the implicit claim that this module's docs/mission.md "
        "headline 'Empirical benchmark result' sections for Polyverse "
        "melt-viscosity constitute properly rights-disclosed Phase-0 "
        "evidence. It does NOT refute the underlying numerical findings "
        "(R^2=0.944 source-safe, 0.897 conformal coverage, FFW R^2=0.597 "
        "beating ML R^2=0.454); those may be numerically correct and remain "
        "unaddressed by this audit. The refutation is evidentiary/"
        "governance: the module's own rights ledger already forbids "
        "derivative use of this data pending counsel review, and mission.md "
        "does not say so."
    ),
    "human_action_needed": (
        "1) Counsel review of the Georgia Tech Research Corporation General "
        "Public Use License Agreement to determine whether any of the three "
        "Polyverse melt-viscosity receipts can be promoted to "
        "promotion_eligible=true, or must remain evidence-only/CONTEXT_ONLY "
        "indefinitely. 2) If they remain CONTEXT_ONLY, amend "
        "amphora-viscosity-score/docs/mission.md's two 'Empirical benchmark "
        "result' sections (and the parent R^2=0.944 reference) to disclose "
        "the rights posture, matching the disclosure already present for "
        "the module's other UNRESOLVED-rights datasets (corrosion_series.json, "
        "cure_verification_set.json, facts.json) documented earlier in the "
        "same file."
    ),
    "does_not_close": diag["does_not_close"],
    "provenance": {
        "harness_sha256": {"run_disclosure_gap_audit.py": harness_sha},
        "inputs_sha256": {k: v.get("sha256") for k, v in diag["inputs"].items()},
    },
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "third_confirmatory_replay": "PASS",
        "canonical_diagnostic_sha256": diag_sha,
        "runB_diagnostic_sha256": sha(runB),
        "third_replay_sha256": third_sha,
        "byte_identical": canon == runB,
        "determinism": "pure-python re-derivation from already-in-tree, already-hashed JSON files; no RNG, no network, no wall-clock reads at run time.",
    },
    "signing_key": {
        "role": "PHASE0_EVALUATOR", "key_id": eval_key_id, "public_key_hex": eval_pub_hex,
        "used_for": "AUDIT_ONLY rights-disclosure-gap receipt under evidence/audit/",
        "signs_phase0_evaluation_or_review": False,
        "derives_pinned_trust_store_key_id": bool(eval_pin)},
    "reviewer_reference": {
        "role": "PHASE0_INTERNAL_REVIEWER", "key_id": rev_key_id, "public_key_hex": rev_pub_hex,
        "derives_pinned_trust_store_key_id": bool(rev_pin), "reviewer_signature_present": False,
        "note": "Reviewer key referenced for provenance only; no independent human review performed."},
}
body = json.dumps(body_obj, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.viscosity-score-polyverse-rights-disclosure-gap+json"
sig = eval_sk.sign(pae(ptype, body))
envelope = {"payload": base64.standard_b64encode(body).decode(), "payloadType": ptype,
            "signatures": [{"keyid": eval_key_id, "sig": base64.standard_b64encode(sig).decode()}]}
receipt = {"evaluator_key_id": eval_key_id, "evaluator_public_key_hex": eval_pub_hex,
           "reviewer_public_key_hex": rev_pub_hex, "signature": envelope}
out = EV / "polyverse-rights-disclosure-gap-receipt.v1.dsse.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True))
Ed25519PublicKey.from_public_bytes(eval_pub).verify(
    base64.standard_b64decode(envelope["signatures"][0]["sig"]),
    pae(ptype, base64.standard_b64decode(envelope["payload"])))
print("WROTE", out)
print("evaluator_key_id", eval_key_id)
print("eval_derives_pinned_trust_key", eval_pin)
print("reviewer_derives_pinned_trust_key", rev_pin)
print("two_replay_sha256", diag_sha)
print("receipt_sha256", sha(out.read_bytes()))
print("signature_verified", True)
