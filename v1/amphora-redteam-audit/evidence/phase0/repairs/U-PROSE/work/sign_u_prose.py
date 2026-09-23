#!/usr/bin/env python3
"""DSSE-Ed25519-sign the amphora-redteam-audit U-PROSE portfolio-wide mission-prose
staleness sweep. AUDIT_ONLY: signs a gap-table receipt under evidence/phase0/repairs/
U-PROSE/done/. Uses the pinned PHASE0_EVALUATOR key, cross-checked against
config/phase0-trust-store.v1.json.
"""
import base64
import hashlib
import json
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
WORK = ROOT / "amphora-redteam-audit/evidence/phase0/repairs/U-PROSE/work"
OUT_DIR = ROOT / "amphora-redteam-audit/evidence/phase0/repairs/U-PROSE/done"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
REVIEWER_SEED = SEED_DIR / "internal-reviewer.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"
FIRE_ID = "20260811T210001-1024037-4d0a503bcfea"


def sha(b):
    return hashlib.sha256(b).hexdigest()


def pae(t, body):
    return (b"DSSEv1 " + str(len(t)).encode() + b" " + t.encode() + b" "
            + str(len(body)).encode() + b" " + body)


def load_seed(p):
    raw = p.read_bytes().strip()
    if len(raw) == 64:
        try:
            return bytes.fromhex(raw.decode())
        except Exception:
            pass
    return raw[:32]


runA_bytes = (WORK / "diagnostic.runA.json").read_bytes()
runB_bytes = (WORK / "diagnostic.runB.json").read_bytes()
byte_identical = runA_bytes == runB_bytes
assert byte_identical, "two-replay bytes differ -- NOT stable, do not sign"
diag = json.loads(runA_bytes)
canon_sha = sha(runA_bytes)

harness_sha = sha((WORK / "run_prose_sweep.py").read_bytes())

eval_sk = Ed25519PrivateKey.from_private_bytes(load_seed(EVAL_SEED))
eval_pub = eval_sk.public_key().public_bytes_raw()
eval_pub_hex = eval_pub.hex()
eval_key_id = f"phase0-evaluator-{sha(eval_pub)}"
rev_sk = Ed25519PrivateKey.from_private_bytes(load_seed(REVIEWER_SEED))
rev_pub_hex = rev_sk.public_key().public_bytes_raw().hex()
rev_key_id = f"phase0-internal-reviewer-{sha(bytes.fromhex(rev_pub_hex))}"
trust = json.loads(TRUST.read_text())
tbr = {k.get("role"): k for k in trust["keys"]}
eval_pin = (eval_key_id == tbr.get("PHASE0_EVALUATOR", {}).get("key_id"))
rev_pin = (rev_key_id == tbr.get("PHASE0_INTERNAL_REVIEWER", {}).get("key_id"))
assert eval_pin, "evaluator key_id does not match pinned trust store"

verdict = diag["verdict"]

body_obj = {
    "schema": "amphora.redteam-audit.mission-prose-staleness-sweep-receipt.v1",
    "receipt_id": "u-prose-mission-prose-staleness-sweep-v1",
    "authority": "AUDIT_ONLY",
    "run_type": "FALSIFICATION_ATTACK",
    "module": "amphora-redteam-audit",
    "campaign_item_id": "U-PROSE",
    "fire_id": FIRE_ID,
    "promotes_authority": False,
    "flips_scientific_readiness": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "modifies_manifest": False,
    "modifies_locked_dataset": False,
    "modifies_signed_phase0_kpi": False,
    "modifies_other_module_files": False,
    "claim_under_attack": diag["claim_under_attack"],
    "attack_description": (
        "Portfolio-wide mission-prose staleness sweep across all 29 docs/mission.md-bearing "
        "modules. Mechanical stage (fully reproducible, re-run live every fire): for each module, "
        "extracted distinguishing numeric tokens from (a) evidence/phase0/kpis/RETRACTION-INDEX.md "
        "table rows' claim column, (b) logs/claims-requiring-retraction.jsonl entries scoped to the "
        "module by file path, and (c) REFUTED logs/falsification-ledger.jsonl verdicts for the "
        "module (claim+attack text, tokens with >=3 significant digits to suppress generic "
        "threshold noise like 0.05/0.90), then checked whether those tokens still appear verbatim "
        "in the module's CURRENT docs/mission.md. This produced 29 mechanical candidate hits across "
        "10 modules (asserted via a hardcoded expected-candidate-module-set check that aborts the "
        "script if the live sweep drifts from what this fire hand-verified). Human-verification "
        "stage: every one of the 29 candidate hits was read in its live mission.md context window "
        "(+/-220 chars) and classified as ADVERTISES_RETRACTED_RESULT / DISCLOSURE_GAP / "
        "ALREADY_REPAIRED / false-positive NO_STALE_CLAIM_DETECTED, with the supporting excerpt "
        "recorded per-module in per_module_table[].evidence. The remaining 19 modules had zero "
        "mechanical candidates (no numeric-token overlap between any tracked refutation and current "
        "mission.md prose) and are recorded NO_STALE_CLAIM_DETECTED. Known limitation, disclosed in "
        "does_not_close: this is a numeric-token sweep; a refutation that is purely qualitative "
        "(no reusable distinguishing number) would not be caught by this method."
    ),
    "n_modules_total": diag["n_modules_total"],
    "modules_covered": diag["modules_covered"],
    "n_modules_with_mechanical_candidates": diag["n_modules_with_mechanical_candidates"],
    "mechanical_candidate_modules": diag["mechanical_candidate_modules"],
    "mechanical_candidates": diag["mechanical_candidates"],
    "per_module_table": diag["per_module_table"],
    "summary_counts": diag["summary_counts"],
    "headline": diag["headline"],
    "verdict": verdict,
    "proposed_followups": diag["proposed_followups"],
    "interpretation": (
        f"{verdict}. {diag['headline']}: amphora-design-rule-score's docs/mission.md carries an "
        "uncaveated 'HONEST INTERPRETATION' headline (B5 HistGBM R2=+0.8555 'crushes every "
        "non-ML baseline') that two 2026-08-01 REFUTED ledger verdicts (campaign C6) and a signed "
        "superseding KPI directly contradict: a leak-free re-baseline collapses that same model to "
        "R2=-0.0469 (below the constant-mean floor) and promotes Guth-Gold 1938 physics to the "
        "strongest leak-free arm. Per this item's own pre-registered rule, any module with a stale "
        "advertised result makes this a CLAIM_REFUTED verdict; that is the honest, useful outcome "
        "and the follow-up is filed in proposed_followups[0]. A second, softer finding "
        "(amphora-molecule-role-ranker, DISCLOSURE_GAP) is filed as proposed_followups[1]: the "
        "module's own RETRACTION-INDEX.md records a refuted generalization inference that its "
        "mission.md prose never mentions, though the raw numbers reported are locally accurate. The "
        "other 7 candidate-bearing modules (amphora-barrier-corrosion-score, "
        "amphora-cure-potlife-gate, amphora-evidence-intake-validator, amphora-molecule-property, "
        "amphora-public-corrosion-benchmark, amphora-solvency-score, amphora-viscosity-score) were "
        "verified ALREADY_REPAIRED: every matched number sits inside an inline retraction/correction "
        "marker in current mission.md. amphora-molecule-generator's single mechanical hit was a "
        "confirmed coincidental digit match (95% locked-target uniqueness figure vs an unrelated "
        "95% CI correction), not a real citation. The remaining 19 modules show no numeric-token "
        "overlap between tracked refutations and current mission.md prose."
    ),
    "does_not_close": [
        "Purely qualitative staleness (a refuted finding with no reusable distinguishing numeric "
        "token) is not detectable by this numeric-token sweep and could exist undetected in any of "
        "the 20 NO_STALE_CLAIM_DETECTED modules.",
        "Whether amphora-design-rule-score's and amphora-molecule-role-ranker's prose gaps get "
        "repaired -- that is out of this AUDIT_ONLY item's scope; proposed_followups[] names the "
        "owner and a proposed done_criterion for each.",
        "Row-level completeness of every module's RETRACTION-INDEX.md against its own REFUTED "
        "ledger verdicts in general (that broader structural check is R-A00's scope, not this "
        "item's, though this fire independently found amphora-design-rule-score's index missing a "
        "row for the C6 finding as a side effect of the prose check).",
    ],
    "reproducibility": {
        "two_replay_sha256_gate": "PASS" if byte_identical else "FAIL",
        "canonical_diagnostic_sha256": canon_sha,
        "runA_diagnostic_sha256": sha(runA_bytes),
        "runB_diagnostic_sha256": sha(runB_bytes),
        "byte_identical": byte_identical,
        "harness_sha256": harness_sha,
        "harness_path": "amphora-redteam-audit/evidence/phase0/repairs/U-PROSE/work/run_prose_sweep.py",
        "ledger_snapshot": diag["ledger_snapshot"],
        "claims_requiring_retraction_snapshot": diag["claims_requiring_retraction_snapshot"],
        "determinism": "pure filesystem read + regex parse over live module trees + a pinned ledger "
                        "and claims-requiring-retraction snapshot at read time, plus a hardcoded "
                        "human-verification table keyed by module and asserted against the live "
                        "candidate-module set; no RNG, no model fitting, no wall-clock embedded in "
                        "the diagnostic body",
    },
    "toolchain": {"python": "3", "note": "stdlib json/hashlib/re/os only"},
    "signing_key": {
        "role": "PHASE0_EVALUATOR", "key_id": eval_key_id, "public_key_hex": eval_pub_hex,
        "used_for": "AUDIT_ONLY audit receipt under evidence/phase0/repairs/U-PROSE/done/",
        "signs_phase0_evaluation_or_review": False,
        "derives_pinned_trust_store_key_id": bool(eval_pin),
    },
    "reviewer_reference": {
        "role": "PHASE0_INTERNAL_REVIEWER", "key_id": rev_key_id, "public_key_hex": rev_pub_hex,
        "derives_pinned_trust_store_key_id": bool(rev_pin), "reviewer_signature_present": False,
        "note": "Reviewer key referenced for provenance only; no independent human review performed.",
    },
}

body = json.dumps(body_obj, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.redteam-audit-u-prose-mission-prose-staleness-sweep+json"
sig = eval_sk.sign(pae(ptype, body))
envelope = {"payload": base64.standard_b64encode(body).decode(), "payloadType": ptype,
            "signatures": [{"keyid": eval_key_id, "sig": base64.standard_b64encode(sig).decode()}]}
receipt = {"evaluator_key_id": eval_key_id, "evaluator_public_key_hex": eval_pub_hex,
           "reviewer_public_key_hex": rev_pub_hex, "signature": envelope}

OUT_DIR.mkdir(parents=True, exist_ok=True)
out = OUT_DIR / "u-prose-mission-prose-staleness-sweep-receipt.v1.dsse.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True))

Ed25519PublicKey.from_public_bytes(eval_pub).verify(
    base64.standard_b64decode(envelope["signatures"][0]["sig"]),
    pae(ptype, base64.standard_b64decode(envelope["payload"])))

print("WROTE", out)
print("verdict", verdict)
print("headline", diag["headline"])
print("evaluator_key_id", eval_key_id)
print("eval_derives_pinned_trust_key", eval_pin)
print("two_replay_sha256", canon_sha)
print("envelope_sha256", sha(out.read_bytes()))
print("signature_verified", True)
