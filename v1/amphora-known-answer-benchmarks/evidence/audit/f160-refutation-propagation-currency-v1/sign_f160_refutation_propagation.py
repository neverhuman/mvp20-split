#!/usr/bin/env python3
"""DSSE-Ed25519-sign the amphora-known-answer-benchmarks f160-refutation-propagation-currency-v1
AUDIT_ONLY receipt. AUDIT_ONLY: signs an audit receipt under evidence/audit/; does NOT sign a
phase0 evaluation/review, does NOT promote authority, does NOT flip scientific_readiness, does
NOT modify the portfolio manifest, module-manifest.json, docs/mission.md,
control_by_control_receipt.v1.json, or any signed Phase-0 KPI. Derived key_id cross-checked vs
pinned trust store."""
import base64, hashlib, json, subprocess
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-known-answer-benchmarks"
AUDIT = MOD / "evidence/audit/f160-refutation-propagation-currency-v1"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
REVIEWER_SEED = SEED_DIR / "internal-reviewer.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"

VERIFIER = AUDIT / "verify_f160_refutation_propagation.py"
REPORT = AUDIT / "f160_refutation_propagation_report.v1.json"
CONTROL_RECEIPT = MOD / "reference/mvp20/out/control_by_control_receipt.v1.json"
MIL_RECOVERY = MOD / "reference/mvp20/out/mil_recovery.json"
REF_CARDS = MOD / "reference/mvp20/out/known_reference_cards.json"
ARITH_AUDIT = MOD / "reference/mvp20/out/arithmetic_audit.json"
MISSION = MOD / "docs/mission.md"
CAP_PROFILE = MOD / "docs/capability-profile.json"
RETRACTION_INDEX = MOD / "evidence/phase0/kpis/RETRACTION-INDEX.md"
PRIOR_RECEIPT = MOD / "evidence/audit/f160-density-source-conflict-credit-violation-v1/receipt.v1.dsse.json"


def sha(b): return hashlib.sha256(b).hexdigest()


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


report = json.loads(REPORT.read_bytes())
assert report["verdict"]["overall"] == "REFUTED", "report did not REFUTE"

# Two-replay: re-run the verifier fresh into its own scratch /tmp path and confirm byte-stable report.
replay = subprocess.run(
    ["python3", str(VERIFIER)], cwd=str(AUDIT), capture_output=True, text=True
)
assert replay.returncode == 0, replay.stderr
replay_report = json.loads(Path("/tmp/f160_refutation_propagation_report.v1.json").read_bytes())
assert replay_report == report, "replay report differs from checked-in report -- not byte-stable"
replay_b_sha = sha(json.dumps(replay_report, indent=2, sort_keys=True).encode())
report_sha = sha(REPORT.read_bytes())
assert replay_b_sha == report_sha, f"replay hash {replay_b_sha} != checked-in {report_sha}"

verifier_sha = sha(VERIFIER.read_bytes())
manifest_sha = sha((ROOT / "module-manifest.json").read_bytes())
mission_sha = sha(MISSION.read_bytes())
control_receipt_sha = sha(CONTROL_RECEIPT.read_bytes())
mil_recovery_sha = sha(MIL_RECOVERY.read_bytes())
ref_cards_sha = sha(REF_CARDS.read_bytes())
arith_audit_sha = sha(ARITH_AUDIT.read_bytes())
cap_profile_sha = sha(CAP_PROFILE.read_bytes())
retraction_index_sha = sha(RETRACTION_INDEX.read_bytes())
prior_receipt_sha = sha(PRIOR_RECEIPT.read_bytes())

eval_sk = Ed25519PrivateKey.from_private_bytes(load_seed(EVAL_SEED))
eval_pub = eval_sk.public_key().public_bytes_raw()
eval_pub_hex = eval_pub.hex()
eval_key_id = f"phase0-evaluator-{sha(eval_pub)}"
rev_sk = Ed25519PrivateKey.from_private_bytes(load_seed(REVIEWER_SEED))
rev_pub = rev_sk.public_key().public_bytes_raw()
rev_pub_hex = rev_pub.hex()
rev_key_id = f"phase0-internal-reviewer-{sha(rev_pub)}"

eval_pin = rev_pin = False
if TRUST.exists():
    trust = json.loads(TRUST.read_text())
    tbr = {k.get("role"): k for k in trust.get("keys", [])}
    eval_pin = (eval_key_id == tbr.get("PHASE0_EVALUATOR", {}).get("key_id"))
    rev_pin = (rev_key_id == tbr.get("PHASE0_INTERNAL_REVIEWER", {}).get("key_id"))

body_obj = {
    "schema": "amphora.known-answer-benchmarks.f160-refutation-propagation-currency-receipt.v1",
    "receipt_id": "f160-refutation-propagation-currency-v1",
    "module_id": "amphora-known-answer-benchmarks",
    "authority": "AUDIT_ONLY",
    "authority_ceiling": "LIMITED_SANITY",
    "decision_use_ceiling": "AUDIT_ONLY",
    "attacked_claim": report["attacked_claim"],
    "hypothesis_advanced": "Known answers expose arithmetic, unit, and applicability regressions (module mission); this audit extends that to whether the module's own prior signed known-answer findings stay live and are not silently outrun by unchanged consumer documentation.",
    "falsification_criterion": report["falsification_criterion"],
    "prior_refuting_receipt": report["prior_refuting_receipt"],
    "independent_rederivation_from_scratch": report["independent_rederivation_from_scratch"],
    "counterfactual_kpi_impact_rederived": report["counterfactual_kpi_impact_rederived"],
    "consumer_surface_propagation_check": report["consumer_surface_propagation_check"],
    "any_propagation_found": report["any_propagation_found"],
    "byte_identity_vs_attack_time": report["byte_identity_vs_attack_time"],
    "zero_repair_action_taken": report["zero_repair_action_taken"],
    "does_not_close": report["does_not_close"],
    "source_hashes_at_attack_time": {
        "control_by_control_receipt.v1.json": control_receipt_sha,
        "mil_recovery.json": mil_recovery_sha,
        "known_reference_cards.json": ref_cards_sha,
        "arithmetic_audit.json": arith_audit_sha,
        "docs/mission.md": mission_sha,
        "docs/capability-profile.json": cap_profile_sha,
        "evidence/phase0/kpis/RETRACTION-INDEX.md": retraction_index_sha,
        "prior_receipt (f160-density-source-conflict-credit-violation-v1)": prior_receipt_sha,
    },
    "artifacts": {
        "report": {"path": "amphora-known-answer-benchmarks/evidence/audit/f160-refutation-propagation-currency-v1/f160_refutation_propagation_report.v1.json", "sha256": report_sha},
        "verifier": {"path": "amphora-known-answer-benchmarks/evidence/audit/f160-refutation-propagation-currency-v1/verify_f160_refutation_propagation.py", "sha256": verifier_sha},
    },
    "provenance": {"module_manifest_sha256": manifest_sha},
    "two_replay_gate": {
        "replays": 2, "byte_stable": True,
        "replay_a_report_sha256": report_sha, "replay_b_report_sha256": replay_b_sha,
    },
    "edits_portfolio_manifest": False,
    "flips_front_matter": False,
    "promotes_authority": False,
    "human_dual_identity_ceremony_performed": False,
    "signing_key": {
        "authority": "AUDIT_ONLY", "role": "PHASE0_EVALUATOR", "key_id": eval_key_id,
        "public_key_hex": eval_pub_hex,
        "note": "phase0-evaluator seed used for AUDIT_ONLY signing only; no dual-identity ceremony",
        "used_for": "AUDIT_ONLY audit receipt under evidence/audit/",
        "signs_phase0_evaluation_or_review": False,
        "trust_anchored_in_phase0_promotion_store": bool(eval_pin),
    },
    "reviewer_reference": {
        "role": "PHASE0_INTERNAL_REVIEWER", "key_id": rev_key_id, "public_key_hex": rev_pub_hex,
        "derives_pinned_trust_store_key_id": bool(rev_pin), "reviewer_signature_present": False,
        "note": "Reviewer key referenced for provenance only; no independent human review performed.",
    },
    "verdict": "REFUTED",
}
body = json.dumps(body_obj, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.known-answer-benchmarks-f160-refutation-propagation-currency-receipt.v1+json"
sig = eval_sk.sign(pae(ptype, body))
envelope = {"payload": base64.standard_b64encode(body).decode(), "payloadType": ptype,
            "signatures": [{"keyid": eval_key_id, "sig": base64.standard_b64encode(sig).decode()}]}
receipt = {"evaluator_key_id": eval_key_id, "evaluator_public_key_hex": eval_pub_hex,
           "reviewer_public_key_hex": rev_pub_hex, "signature": envelope}
for k in ("schema", "receipt_id", "module_id", "authority", "authority_ceiling"):
    receipt[k] = body_obj[k]
AUDIT.mkdir(parents=True, exist_ok=True)
out = AUDIT / "receipt.v1.dsse.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True))
Ed25519PublicKey.from_public_bytes(eval_pub).verify(
    base64.standard_b64decode(envelope["signatures"][0]["sig"]),
    pae(ptype, base64.standard_b64decode(envelope["payload"])))
print("WROTE", out)
print("evaluator_key_id", eval_key_id)
print("eval_derives_pinned_trust_key", eval_pin)
print("reviewer_derives_pinned_trust_key", rev_pin)
print("report_sha256", report_sha)
print("envelope_sha256", sha(out.read_bytes()))
print("signature_len", len(receipt["signature"]["signatures"][0]["sig"]))
print("signature_verified", True)
