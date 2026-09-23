#!/usr/bin/env python3
"""DSSE-Ed25519-sign the amphora-ingredient-library
yd128-eew-independent-second-source-verification-v1 AUDIT_ONLY receipt.
AUDIT_ONLY: signs an audit receipt under evidence/audit/; does NOT sign a
phase0 evaluation/review, does NOT promote authority, does NOT flip
scientific_readiness, does NOT modify the portfolio manifest, module-manifest.json,
any locked dataset, or a signed Phase-0 KPI.

Includes a REQUIRED positive_control block (SURVIVAL receipt): two
independent defects planted into IN-MEMORY COPIES of this receipt's own real
comparison data only -- the real signed diagnostic and facts.json on disk are
never touched.
  (A) field corruption: resin.dgeba_yd128.density's independent Kukdo-fstatic
      external_ref_value overwritten 1.17 -> 1.05 (simulated transcription
      misread of the same class of source document). Baseline
      pct_deviation=0.0%% (within 3%% gate) -> defect pct_deviation~11.43%%
      (correctly flagged outside gate).
  (B) digit-insert/decimal-slip/transpose mutation series on
      resin.dgeba_yd128.eew catalog value against the fixed independent Kukdo
      external reference midpoint (187.0): all 3 gross mutations flagged,
      baseline not.
"""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
BENCH = ROOT / "amphora-ingredient-library/evidence/audit/yd128-eew-independent-second-source-verification-v1"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
REVIEWER_SEED = SEED_DIR / "internal-reviewer.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"


def sha(b): return hashlib.sha256(b).hexdigest()
def pae(t, body):
    return (b"DSSEv1 " + str(len(t)).encode() + b" " + t.encode() + b" " +
            str(len(body)).encode() + b" " + body)
def load_seed(p):
    raw = p.read_bytes().strip()
    if len(raw) == 64:
        try: return bytes.fromhex(raw.decode())
        except Exception: pass
    return raw[:32]
def pct(cat, ref): return round(100.0 * (cat - ref) / ref, 4)


canon = (BENCH / "diagnostic.canonical.json").read_bytes()
runB = (BENCH / "diagnostic.runB.json").read_bytes()
assert canon == runB, "two-replay bytes differ"
diag_sha = sha(canon)
diag = json.loads(canon)
oracle_sha = sha((BENCH / "run_yd128_independent_verify.py").read_bytes())
manifest_sha = sha((ROOT / "module-manifest.json").read_bytes())
facts_sha = diag["inputs"]["facts_json_sha256"]

eval_sk = Ed25519PrivateKey.from_private_bytes(load_seed(EVAL_SEED))
eval_pub = eval_sk.public_key().public_bytes_raw(); eval_pub_hex = eval_pub.hex()
eval_key_id = f"phase0-evaluator-{sha(eval_pub)}"
rev_sk = Ed25519PrivateKey.from_private_bytes(load_seed(REVIEWER_SEED))
rev_pub_hex = rev_sk.public_key().public_bytes_raw().hex()
rev_key_id = f"phase0-internal-reviewer-{sha(bytes.fromhex(rev_pub_hex))}"
trust = json.loads(TRUST.read_text())
tbr = {k.get("role"): k for k in trust["keys"]}
eval_pin = (eval_key_id == tbr.get("PHASE0_EVALUATOR", {}).get("key_id"))
rev_pin = (rev_key_id == tbr.get("PHASE0_INTERNAL_REVIEWER", {}).get("key_id"))

# ---- positive control: recompute defect A directly from the real
# diagnostic's own baseline row (not trusting a prior narrative number) -----
density_row = next(
    r for r in diag["checkB_independent_source_reverification"]["per_comparison"]
    if r["row_id"] == "resin.dgeba_yd128.density__kukdo_fstatic_independent")
defect_a_ref = 1.05
defect_a_dev = pct(density_row["catalog_value"], defect_a_ref)
defect_a = {
    "target_row_id": density_row["row_id"],
    "how_planted": "in-memory copy: external_ref_value overwritten 1.17 -> 1.05 "
                   "(simulated transcription misread of the same class of "
                   "manufacturer TDS source); real signed diagnostic and "
                   "facts.json on disk never touched",
    "baseline_pct_deviation": density_row["pct_deviation"],
    "baseline_within_gate": density_row["within_gate"],
    "defect_pct_deviation": defect_a_dev,
    "defect_within_gate": bool(abs(defect_a_dev) <= diag["inputs"]["gate_pct"]),
    "detected": bool(density_row["within_gate"] and not (abs(defect_a_dev) <= diag["inputs"]["gate_pct"])),
}

eew_row = next(
    r for r in diag["checkB_independent_source_reverification"]["per_comparison"]
    if r["row_id"] == "resin.dgeba_yd128.eew__kukdo_fstatic_independent")
eew_ref = eew_row["external_ref_value"]
eew_cat = eew_row["catalog_value"]
mutations = [
    ("baseline", eew_cat),
    ("digit_insert_1870", eew_cat * 10.0),
    ("decimal_slip_18.7", eew_cat / 10.0),
    ("transpose_178", 178.0),
]
demo = []
for label, val in mutations:
    d = pct(val, eew_ref)
    demo.append({"mutation": label, "value": round(val, 4),
                 "pct_deviation_vs_kukdo_fstatic": d,
                 "flagged": bool(abs(d) > diag["inputs"]["gate_pct"])})
gross = [d for d in demo if d["mutation"] != "baseline"]
gross_all_flagged = all(d["flagged"] for d in gross)
defect_b = {
    "target_fact_key": "resin.dgeba_yd128.eew",
    "reference": "KUKDO EPOXY YD-128 TDS (fstatic), EEW midpoint 187.0 g/eq",
    "how_planted": "in-memory catalog-value mutations: digit-insert (x10), "
                   "decimal-slip (/10), transpose-digits, vs the fixed live "
                   "Kukdo-fstatic external reference midpoint (187.0)",
    "mutations": demo,
    "all_gross_mutations_flagged": gross_all_flagged,
    "detected": bool(gross_all_flagged),
}

positive_control = {
    "planted_defect": "Two independent defects planted into IN-MEMORY COPIES of "
                      "this receipt's own real comparison data (real signed "
                      "diagnostic and facts.json on disk never touched): (A) "
                      "external_ref_value field corruption on the real "
                      "resin.dgeba_yd128.density independent-source row (1.17 -> "
                      "1.05, simulating a transcription misread of the same "
                      "class of manufacturer TDS source); (B) digit-insert/"
                      "decimal-slip/transpose mutation demo on the "
                      "resin.dgeba_yd128.eew catalog value (187.0 -> 1870.0 / "
                      "18.7 / 178.0) against the fixed live external reference "
                      "midpoint (187.0).",
    "how_planted": {"defect_a_field_corruption": defect_a, "defect_b_mutation_demo": defect_b},
    "detected": bool(defect_a["detected"] and defect_b["detected"]),
    "evidence": (
        "defect_a: pct_deviation=%.4f%% (gate=%.1f%%) -> within_gate=%s "
        "(correctly flagged False). defect_b: mutations digit_insert/decimal_slip/"
        "transpose all flagged=True vs baseline flagged=False -- same within_gate "
        "predicate this receipt's real checkB uses caught both planted-defect kinds."
        % (defect_a_dev, diag["inputs"]["gate_pct"], defect_a["defect_within_gate"])
    ),
}
assert positive_control["detected"], "positive control FAILED to detect a planted defect"

body_obj = {
    "schema": "amphora.ingredient-library.yd128-eew-independent-second-source-verification-receipt.v1",
    "authority": "AUDIT_ONLY",
    "run_type": diag["run_type"],
    "module": "amphora-ingredient-library",
    "promotes_authority": False, "flips_scientific_readiness": False,
    "human_review_performed": False,
    "modifies_manifest": False, "modifies_module_manifest": False,
    "modifies_locked_dataset": False, "modifies_signed_phase0_kpi": False,
    "purpose": diag["purpose"],
    "hypothesis": diag["hypothesis"],
    "non_circularity": diag["non_circularity"],
    "theory_reference": diag["theory_reference"],
    "results": {
        "headline": diag["headline"],
        "gap_closed": diag["checkA_gap_disclosure"]["gap_closed_by_this_receipt"],
        "n_total_comparisons": diag["checkB_independent_source_reverification"]["n_total_comparisons"],
        "n_within_gate": diag["checkB_independent_source_reverification"]["n_within_gate"],
        "all_within_gate": diag["checkB_independent_source_reverification"]["all_within_gate"],
        "failing_comparisons": diag["checkB_independent_source_reverification"]["failing_comparisons"],
        "per_comparison": diag["checkB_independent_source_reverification"]["per_comparison"],
        "checkA_gap_disclosure": diag["checkA_gap_disclosure"],
    },
    "closes": diag["closes"],
    "does_not_close": diag["does_not_close"],
    "positive_control": positive_control,
    "provenance": {
        "facts_json_sha256": facts_sha,
        "module_manifest_sha256": manifest_sha,
        "oracle_sha256": oracle_sha,
    },
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "canonical_diagnostic_sha256": diag_sha,
        "runB_diagnostic_sha256": sha(runB),
        "byte_identical": canon == runB,
    },
    "signing_key": {
        "role": "PHASE0_EVALUATOR", "key_id": eval_key_id, "public_key_hex": eval_pub_hex,
        "used_for": "AUDIT_ONLY audit receipt under evidence/audit/",
        "signs_phase0_evaluation_or_review": False,
        "derives_pinned_trust_store_key_id": bool(eval_pin)},
    "reviewer_reference": {
        "role": "PHASE0_INTERNAL_REVIEWER", "key_id": rev_key_id, "public_key_hex": rev_pub_hex,
        "derives_pinned_trust_store_key_id": bool(rev_pin), "reviewer_signature_present": False,
        "note": "Reviewer key referenced for provenance only; no independent human review performed."},
}
body = json.dumps(body_obj, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.ingredient-library-yd128-eew-independent-second-source-verification-receipt.v1+json"
sig = eval_sk.sign(pae(ptype, body))
envelope = {"payload": base64.standard_b64encode(body).decode(), "payloadType": ptype,
            "signatures": [{"keyid": eval_key_id, "sig": base64.standard_b64encode(sig).decode()}]}
receipt = {"evaluator_key_id": eval_key_id, "evaluator_public_key_hex": eval_pub_hex,
           "reviewer_public_key_hex": rev_pub_hex, "signature": envelope}
out = BENCH / "yd128-eew-independent-second-source-verification-receipt.v1.dsse.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True))
Ed25519PublicKey.from_public_bytes(eval_pub).verify(
    base64.standard_b64decode(envelope["signatures"][0]["sig"]),
    pae(ptype, base64.standard_b64decode(envelope["payload"])))
print("WROTE", out)
print("evaluator_key_id", eval_key_id)
print("eval_derives_pinned_trust_key", eval_pin)
print("reviewer_derives_pinned_trust_key", rev_pin)
print("two_replay_sha256", diag_sha)
print("envelope_sha256", sha(out.read_bytes()))
print("positive_control_detected", positive_control["detected"])
print("signature_verified", True)
