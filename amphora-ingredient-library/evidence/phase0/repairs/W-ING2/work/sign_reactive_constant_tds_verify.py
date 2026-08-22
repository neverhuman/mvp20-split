#!/usr/bin/env python3
"""DSSE-Ed25519-sign the amphora-ingredient-library reactive-constant-tds-
verification-v1 AUDIT_ONLY superseding KPI receipt (campaign item W-ING2).
AUDIT_ONLY: does NOT promote authority, does NOT flip scientific_readiness,
does NOT modify the portfolio manifest (66 receipts / 11 modules),
module-manifest.json, any locked dataset. It DOES supersede (never rewrite)
hardener-tds-verified-constants-kpi.v1.json by extending its scope from
hardener densities to the reactive constants (resin EEW + remaining
hardener AHEW/amine-value). Derived key_id cross-checked vs pinned trust
store."""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-ingredient-library"
WORK = MOD / "evidence/phase0/repairs/W-ING2/work"
DONE = MOD / "evidence/phase0/repairs/W-ING2/done"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
REVIEWER_SEED = SEED_DIR / "internal-reviewer.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"

PRIOR_KPI = MOD / "evidence/phase0/kpis/hardener-tds-verified-constants-kpi.v1.json"


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


canon = (WORK / "diagnostic.canonical.json").read_bytes()
runB = (WORK / "diagnostic.runB.json").read_bytes()
assert canon == runB, "two-replay bytes differ"
diag_sha = sha(canon)
diag = json.loads(canon)
oracle_sha = sha((WORK / "run_reactive_constant_tds_verify.py").read_bytes())
manifest_sha = sha((ROOT / "module-manifest.json").read_bytes())
facts_sha = diag["inputs"]["facts_json_sha256"]
positive_control = json.loads((WORK / "positive_control.json").read_bytes())

prior_kpi_bytes = PRIOR_KPI.read_bytes()
prior_kpi_sha = sha(prior_kpi_bytes)

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

body_obj = {
    "schema": "amphora.ingredient-library.reactive-constant-tds-verification-receipt.v1",
    "authority": "AUDIT_ONLY",
    "run_type": diag["run_type"],
    "module": "amphora-ingredient-library",
    "campaign_item_id": "W-ING2",
    "promotes_authority": False, "flips_scientific_readiness": False,
    "human_review_performed": False,
    "modifies_manifest": False, "modifies_module_manifest": False,
    "modifies_locked_dataset": False, "modifies_signed_phase0_kpi": False,
    "purpose": diag["purpose"],
    "hypothesis": diag["hypothesis"],
    "non_circularity": diag["non_circularity"],
    "theory_reference": diag["theory_reference"],
    "licence_position": diag["licence_position"],
    "results": {
        "headline": diag["headline"],
        "new_gap_closed": diag["checkA_coverage_gap"]["new_gap_closed_by_this_receipt"],
        "n_new_gap_closed": diag["checkA_coverage_gap"]["n_new_gap_closed"],
        "n_total_comparisons": diag["checkB_external_tds_reverification"]["n_total_comparisons"],
        "n_within_gate": diag["checkB_external_tds_reverification"]["n_within_gate"],
        "all_within_gate": diag["checkB_external_tds_reverification"]["all_within_gate"],
        "failing_comparisons": diag["checkB_external_tds_reverification"]["failing_comparisons"],
        "n_independent_source_comparisons": diag["checkB_external_tds_reverification"]["n_independent_source_comparisons"],
        "n_transcription_fidelity_comparisons": diag["checkB_external_tds_reverification"]["n_transcription_fidelity_comparisons"],
        "n_search_snippet_citations": diag["checkB_external_tds_reverification"]["n_search_snippet_citations"],
        "per_comparison": diag["checkB_external_tds_reverification"]["per_comparison"],
        "regional_grade_and_conservative_rule": diag["checkC_regional_grade_and_conservative_rule"],
    },
    "closes": diag["closes"],
    "does_not_close": diag["does_not_close"],
    "supersedes": {
        "superseded_kpi_id": "amphora-ingredient-library-phase0-hardener-tds-verified-constants-v1",
        "superseded_kpi_path": "evidence/phase0/kpis/hardener-tds-verified-constants-kpi.v1.json",
        "superseded_kpi_sha256": prior_kpi_sha,
        "superseded_kpi_deleted_or_modified": False,
        "reason": "hardener-tds-verified-constants-kpi.v1 (W-ING1, SURVIVED 2026-08-05) "
                  "was scoped to hardener DENSITY plus 5 AHEW/amine-value facts checked "
                  "only as a byproduct; the module's claim under attack in W-ING2 is that "
                  "EVERY load-bearing constant is externally verified, not just densities. "
                  "This receipt is not a correction of a wrong prior value -- every prior "
                  "W-ING1 comparison still holds -- it is a scope EXTENSION: it adds live "
                  "external verification for the 7 load-bearing reactive constants (4 resin "
                  "EEW, 3 remaining hardener AHEW) plus 2 non-load-bearing amine-value "
                  "facts that W-ING1 never reached, so it supersedes W-ING1's KPI as the "
                  "module's current external-verification headline.",
    },
    "positive_control": {
        "planted_defect": "Two independent defects planted into IN-MEMORY COPIES of this "
                          "receipt's own real comparison data (real signed diagnostic and "
                          "facts.json on disk never touched): (A) external_ref_value field "
                          "corruption on the real resin.dgeba_828.eew row (188.5 -> 205.0, "
                          "simulating a transcription misread of the same source PDF); "
                          "(B) digit-insert/decimal-slip/transpose mutation demo on the "
                          "hardener.versamid_115.ahew catalog value (198.0 -> 1980.0 / 19.8 "
                          "/ 189.0) against the fixed live external reference (198.0).",
        "how_planted": positive_control,
        "detected": bool(
            positive_control["defect_a_field_corruption"]["detected"]
            and positive_control["defect_b_mutation_demo"]["detected"]
        ),
        "evidence": "defect_a: pct_deviation=%.4f%% (gate=3.0%%) -> within_gate=%s "
                    "(correctly flagged False). defect_b: mutations digit_insert/"
                    "decimal_slip/transpose all flagged=True vs baseline flagged=False -- "
                    "same within_gate predicate this receipt's real checkB uses caught "
                    "both planted-defect kinds." % (
                        positive_control["defect_a_field_corruption"]["defect_pct_deviation"],
                        positive_control["defect_a_field_corruption"]["defect_within_gate"],
                    ),
    },
    "provenance": {
        "facts_json_sha256": facts_sha,
        "module_manifest_sha256": manifest_sha,
        "oracle_sha256": oracle_sha,
        "prior_kpi_sha256_at_supersession_time": prior_kpi_sha,
    },
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "canonical_diagnostic_sha256": diag_sha,
        "runB_diagnostic_sha256": sha(runB),
        "byte_identical": canon == runB,
    },
    "signing_key": {
        "role": "PHASE0_EVALUATOR", "key_id": eval_key_id, "public_key_hex": eval_pub_hex,
        "used_for": "AUDIT_ONLY repair receipt under evidence/phase0/repairs/W-ING2/done/",
        "signs_phase0_evaluation_or_review": False,
        "derives_pinned_trust_store_key_id": bool(eval_pin)},
    "reviewer_reference": {
        "role": "PHASE0_INTERNAL_REVIEWER", "key_id": rev_key_id, "public_key_hex": rev_pub_hex,
        "derives_pinned_trust_store_key_id": bool(rev_pin), "reviewer_signature_present": False,
        "note": "Reviewer key referenced for provenance only; no independent human review performed."},
}
body = json.dumps(body_obj, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.ingredient-library-reactive-constant-tds-verification-receipt.v1+json"
sig = eval_sk.sign(pae(ptype, body))
envelope = {"payload": base64.standard_b64encode(body).decode(), "payloadType": ptype,
            "signatures": [{"keyid": eval_key_id, "sig": base64.standard_b64encode(sig).decode()}]}
receipt = {"evaluator_key_id": eval_key_id, "evaluator_public_key_hex": eval_pub_hex,
           "reviewer_public_key_hex": rev_pub_hex, "signature": envelope}
DONE.mkdir(parents=True, exist_ok=True)
out = DONE / "reactive-constant-tds-verified-superseding-kpi.v1.dsse.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True))
Ed25519PublicKey.from_public_bytes(eval_pub).verify(
    base64.standard_b64decode(envelope["signatures"][0]["sig"]),
    pae(ptype, base64.standard_b64decode(envelope["payload"])))
print("WROTE", out)
print("evaluator_key_id", eval_key_id)
print("eval_derives_pinned_trust_key", eval_pin)
print("reviewer_derives_pinned_trust_key", rev_pin)
print("two_replay_sha256", diag_sha)
print("prior_kpi_sha256", prior_kpi_sha)
print("envelope_sha256", sha(out.read_bytes()))
print("signature_verified", True)
