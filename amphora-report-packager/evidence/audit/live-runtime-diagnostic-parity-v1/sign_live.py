#!/usr/bin/env python3
"""DSSE-Ed25519-sign the amphora-report-packager live-runtime-diagnostic-parity-v1
AUDIT_ONLY receipt. AUDIT_ONLY: signs an audit receipt under evidence/audit/;
does NOT sign a phase0 evaluation/review, does NOT promote authority, does NOT
flip scientific_readiness, does NOT modify the portfolio manifest (66 receipts
/ 11 modules), the module-manifest.json, any locked dataset, or a signed
Phase-0 KPI. Derived key_id cross-checked vs pinned trust store."""
import base64
import hashlib
import json
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
BENCH = ROOT / "amphora-report-packager/evidence/audit/live-runtime-diagnostic-parity-v1"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
REVIEWER_SEED = SEED_DIR / "internal-reviewer.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"


def sha(b):
    return hashlib.sha256(b).hexdigest()


def pae(t, body):
    return (
        b"DSSEv1 "
        + str(len(t)).encode()
        + b" "
        + t.encode()
        + b" "
        + str(len(body)).encode()
        + b" "
        + body
    )


def load_seed(p):
    raw = p.read_bytes().strip()
    if len(raw) == 64:
        try:
            return bytes.fromhex(raw.decode())
        except Exception:
            pass
    return raw[:32]


canon = (BENCH / "diagnostic.canonical.json").read_bytes()
runB = (BENCH / "diagnostic.runB.json").read_bytes()
assert canon == runB, "two-replay bytes differ"
diag_sha = sha(canon)
diag = json.loads(canon)
oracle_sha = sha((BENCH / "report_packager_live_oracle.py").read_bytes())
runner_sha = sha((BENCH / "run_live_parity.py").read_bytes())
ground_truth_sha = sha((BENCH / "runtime_ground_truth.v1.json").read_bytes())
manifest_sha = sha((ROOT / "module-manifest.json").read_bytes())

assert diag["gates"]["all_pass"], "diagnostic gates failed; refusing to sign"
assert (
    diag["ground_truth"]["probe_stdout_sha256_run_a"]
    == diag["ground_truth"]["probe_stdout_sha256_run_b"]
), "probe two-replay failed"

eval_sk = Ed25519PrivateKey.from_private_bytes(load_seed(EVAL_SEED))
eval_pub = eval_sk.public_key().public_bytes_raw()
eval_pub_hex = eval_pub.hex()
eval_key_id = f"phase0-evaluator-{sha(eval_pub)}"
rev_sk = Ed25519PrivateKey.from_private_bytes(load_seed(REVIEWER_SEED))
rev_pub_hex = rev_sk.public_key().public_bytes_raw().hex()
rev_key_id = f"phase0-internal-reviewer-{sha(bytes.fromhex(rev_pub_hex))}"
trust = json.loads(TRUST.read_text())
tbr = {k.get("role"): k for k in trust["keys"]}
eval_pin = eval_key_id == tbr.get("PHASE0_EVALUATOR", {}).get("key_id")
rev_pin = rev_key_id == tbr.get("PHASE0_INTERNAL_REVIEWER", {}).get("key_id")

g = diag["gates"]
g1 = diag["g1_live_diagnostic"]
g2 = diag["g2_live_evaluation"]
g3 = diag["g3_live_mediation"]
g4 = diag["g4_descriptor_projection"]

body_obj = {
    "schema": "amphora.report-packager.live-runtime-diagnostic-parity-receipt.v1",
    "study_id": diag["study_id"],
    "authority": "AUDIT_ONLY",
    "run_type": diag["run_type"],
    "module": "amphora-report-packager",
    "promotes_authority": False,
    "flips_scientific_readiness": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "modifies_manifest": False,
    "modifies_module_manifest": False,
    "modifies_locked_dataset": False,
    "modifies_signed_phase0_kpi": False,
    "claim": diag["closes"],
    "purpose": diag["purpose"],
    "hypothesis": diag["hypothesis"],
    "verdict": diag["verdict"],
    "non_circularity": diag["non_circularity"],
    "theory_reference": diag["theory_reference"],
    "runtime_source_anchors": diag["runtime_source_anchors"],
    "results": {
        "all_gates_passed": g["all_pass"],
        "g0_two_replay_byte_stability": g["g0_two_replay_byte_stability"],
        # G1 live diagnostic parity
        "g1_live_diagnostic_oracle_parity": g["g1_live_diagnostic_oracle_parity"],
        "g1_canonical_parity_byte_exact": g1["canonical_parity_byte_exact"],
        "g1_result_digest_match": g1["result_digest_match"],
        "g1_result_digest": g1["result_digest_live"],
        "g1_live_passed": g1["live_passed"],
        "g1_positive_control_count": g1["positive_control_count"],
        "g1_negative_control_count": g1["negative_control_count"],
        "g1_outcome_labels": g1["outcome_labels"],
        "g1_fixture_sha256_match": g1["fixture_sha256_match"],
        # G2 live KPI evaluation parity
        "g2_live_evaluation_oracle_parity": g["g2_live_evaluation_oracle_parity"],
        "g2_canonical_parity_byte_exact": g2["canonical_parity_byte_exact"],
        "g2_status": g2["status_live"],
        "g2_context_invariant_live": g2["context_invariant_live"],
        "g2_generated_document_count": g2["generated_document_count_live"],
        "g2_release_gates_all_false_live": g2["release_gates_all_false_live"],
        "g2_artifact_hash_parity": g2["artifact_hash_parity"],
        # G3 live mediation deny paths
        "g3_live_mediation_fail_closed": g["g3_live_mediation_fail_closed"],
        "g3_deny_paths_tested": g3["deny_paths_tested"],
        "g3_deny_paths_fail_closed_with_display_parity": g3[
            "deny_paths_fail_closed_with_display_parity"
        ],
        # G4 descriptor projection
        "g4_descriptor_projection_parity": g["g4_descriptor_projection_parity"],
        "g4_canonical_parity_byte_exact": g4["canonical_parity_byte_exact"],
        "g4_authority_ceiling_evidence_only": g4["authority_ceiling_evidence_only"],
        "g4_ranking_eligible_false": g4["ranking_eligible_false"],
    },
    "gates": g,
    "closes": diag["closes"],
    "does_not_close": diag["does_not_close"],
    "provenance": {
        "module_manifest_sha256": manifest_sha,
        "oracle_sha256": oracle_sha,
        "runner_sha256": runner_sha,
        "probe_stdout_sha256": ground_truth_sha,
        "probe_main_rs_sha256": diag["runtime_source_anchors"]["probe_main_rs_sha256"],
        "probe_cargo_toml_sha256": diag["runtime_source_anchors"][
            "probe_cargo_toml_sha256"
        ],
        "fixture_sha256": diag["runtime_source_anchors"]["fixture_sha256"],
        "assurance_lib_rs_sha256": diag["runtime_source_anchors"][
            "assurance_lib_rs_sha256"
        ],
        "assurance_diagnostics_rs_sha256": diag["runtime_source_anchors"][
            "assurance_diagnostics_rs_sha256"
        ],
        "core_capability_rs_sha256": diag["runtime_source_anchors"][
            "core_capability_rs_sha256"
        ],
        "core_phase0_rs_sha256": diag["runtime_source_anchors"][
            "core_phase0_rs_sha256"
        ],
    },
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "canonical_diagnostic_sha256": diag_sha,
        "runB_diagnostic_sha256": sha(runB),
        "byte_identical": canon == runB,
        "probe_two_replay_stdout_sha256": diag["ground_truth"][
            "probe_stdout_sha256_run_a"
        ],
        "oracle_sha256": oracle_sha,
    },
    "signing_key": {
        "role": "PHASE0_EVALUATOR",
        "key_id": eval_key_id,
        "public_key_hex": eval_pub_hex,
        "used_for": "AUDIT_ONLY audit receipt under evidence/audit/",
        "signs_phase0_evaluation_or_review": False,
        "derives_pinned_trust_store_key_id": bool(eval_pin),
    },
    "reviewer_reference": {
        "role": "PHASE0_INTERNAL_REVIEWER",
        "key_id": rev_key_id,
        "public_key_hex": rev_pub_hex,
        "derives_pinned_trust_store_key_id": bool(rev_pin),
        "reviewer_signature_present": False,
        "note": "Reviewer key referenced for provenance only; no independent human review performed.",
    },
    "prior_receipts_in_module": [
        "amphora-report-packager-banned-claim-lint-parity-v1 (claim TEXT lint, static)",
        "amphora-report-packager-gate-lattice-completeness-v1 (release DECISION algebra, static)",
        "amphora-report-packager-render-claim-lock-preservation-v1 (packaging MAP projection, static)",
    ],
    "distinct_axis": (
        "FIRST live Rust harness for this module: the compiled runtime is "
        "EXECUTED (real Ed25519 verify, real NFKC lint, real stable_hash, "
        "real mediation deny paths, real KPI quarantine) and compared "
        "byte-for-byte against an independent CPython oracle -- closing the "
        "source-equals-behavior gap every prior receipt disclaimed."
    ),
}
body = json.dumps(body_obj, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.report-packager-live-runtime-diagnostic-parity+json"
sig = eval_sk.sign(pae(ptype, body))
envelope = {
    "payload": base64.standard_b64encode(body).decode(),
    "payloadType": ptype,
    "signatures": [{"keyid": eval_key_id, "sig": base64.standard_b64encode(sig).decode()}],
}
receipt = {
    "evaluator_key_id": eval_key_id,
    "evaluator_public_key_hex": eval_pub_hex,
    "reviewer_public_key_hex": rev_pub_hex,
    "signature": envelope,
}
out = BENCH / "live-runtime-diagnostic-parity-receipt.v1.dsse.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True))
Ed25519PublicKey.from_public_bytes(eval_pub).verify(
    base64.standard_b64decode(envelope["signatures"][0]["sig"]),
    pae(ptype, base64.standard_b64decode(envelope["payload"])),
)
print("WROTE", out)
print("evaluator_key_id", eval_key_id)
print("eval_derives_pinned_trust_key", eval_pin)
print("reviewer_derives_pinned_trust_key", rev_pin)
print("all_gates_passed", g["all_pass"])
print("verdict", diag["verdict"])
print("two_replay_sha256", diag_sha)
print("envelope_sha256", sha(out.read_bytes()))
print("signature_verified", True)
