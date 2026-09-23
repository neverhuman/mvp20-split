"""DSSE-Ed25519-sign the cure-potlife Arrhenius verification audit receipt.

Signs the canonical diagnostic whose bytes reproduced identically across two
independent executions (two-replay SHA gate = PASS). Signs with the repo
LOCAL_DEVELOPMENT_AUDIT_ONLY key (local-9028773f...), explicitly NOT a
trust-anchored phase0 key. This is an AUDIT_ONLY red-team verification; it
promotes nothing, signs no phase0 evaluation/review receipt, and modifies no
existing receipt or manifest.
"""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

BENCH = Path("amphora-redteam-audit/benchmarks/cure-potlife-arrhenius-verification-v1")
KEY = Path(".amphora/control/local-ed25519.key")
PUB = json.loads(Path(".amphora/control/local-ed25519.pub.json").read_text())
CANONICAL_SHA = "3b7eadb1401d27346389adb16b9698e90523a1cfc74e5866a14b8366fc3ae758"

def sha(b): return hashlib.sha256(b).hexdigest()
def pae(t, body): return b"DSSEv1 " + str(len(t)).encode() + b" " + t.encode() + b" " + str(len(body)).encode() + b" " + body

diag_bytes = (BENCH / "diagnostic.canonical.json").read_bytes()
runb_bytes = (BENCH / "diagnostic.runB.json").read_bytes()
diag_sha, runb_sha = sha(diag_bytes), sha(runb_bytes)
assert diag_sha == CANONICAL_SHA, f"{diag_sha} != {CANONICAL_SHA}"
assert runb_sha == CANONICAL_SHA, f"runB {runb_sha} != {CANONICAL_SHA} (two-replay gate)"
diag = json.loads(diag_bytes)
harness_sha = sha((BENCH / "cure_potlife_arrhenius_verification_audit.py").read_bytes())

receipt = {
    "schema": "amphora.redteam-audit.cure-potlife-arrhenius-verification-v1-replay-receipt.v1",
    "authority": "AUDIT_ONLY",
    "run_type": "CURE_POTLIFE_ARRHENIUS_SCIENCE_VERIFICATION_REPLAY",
    "promotes_authority": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "module": "amphora-redteam-audit",
    "benchmark": "amphora-redteam-audit/cure-potlife-arrhenius-verification-v1",
    "target_module": "amphora-cure-potlife-gate",
    "target_kpi_id": diag["target_kpi_id"],
    "purpose": (
        "Independent (Python-stdlib) red-team reverification of the "
        "amphora-cure-potlife-gate Phase-0 Arrhenius pot-life KPI on a code path "
        "disjoint from the Rust (ed25519-dalek/serde_jcs) benchmark. Recomputes all "
        "six KPI metrics from the raw known-answer fixture, checks they reproduce the "
        "values attested in the signed KPI file, proves the physics is NON-CIRCULAR "
        "(pot-life-derived apparent Ea differs systematically from the independently "
        "cited calorimetric Ea), and reconfirms the on-disk result/fixture bindings."),
    "theory": diag["theory"],
    "headline_result": diag["headline"],
    "independent_recompute": diag["independent_recompute"],
    "attested_in_signed_kpi": diag["attested_in_signed_kpi"],
    "all_metrics_reproduce": diag["all_metrics_reproduce"],
    "acceptance_gates": diag["acceptance_gates"],
    "all_acceptance_gates_pass": diag["all_acceptance_gates_pass"],
    "non_circularity": diag["non_circularity"],
    "binding": diag["binding"],
    "bindings_intact": diag["bindings_intact"],
    "rust_first_replay": diag["rust_first_replay"],
    "phase0_status": diag["phase0_status"],
    "honest_limitations": diag["honest_limitations"],
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "replays": 2, "independent_runs": True,
        "code_path_independence": "Rust (ed25519-dalek/serde_jcs) first replay + Python-stdlib second replay",
        "canonical_diagnostic_sha256": CANONICAL_SHA,
        "runB_diagnostic_sha256": runb_sha,
        "harness_sha256": harness_sha,
    },
    "does_not_close": [
        "does NOT promote amphora-cure-potlife-gate to PHASE_0: the two trust-anchored "
        "signatures (PHASE0_EVALUATOR evaluation.v1.dsse.json + PHASE0_INTERNAL_REVIEWER "
        "independent-review) are absent; those service keys are intentionally not in-repo",
        "does NOT change the defensible Phase-0 count, which remains 9 (all infrastructure)",
        "does NOT assert wet-lab measurement, product qualification, or superiority",
    ],
    "does_not": diag["does_not"],
    "signing_key": {"key_id": PUB["key_id"], "authority": PUB["authority"],
                    "trust_anchored_in_phase0_store": False},
}
body = json.dumps(receipt, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.redteam-cure-potlife-arrhenius-verification+json"
sk = Ed25519PrivateKey.from_private_bytes(KEY.read_bytes())
sig = sk.sign(pae(ptype, body))
envelope = {"payload": base64.standard_b64encode(body).decode(), "payloadType": ptype,
            "signatures": [{"keyid": PUB["key_id"], "sig": base64.standard_b64encode(sig).decode()}]}
out = BENCH / "replay_receipt.v1.dsse.json"
out.write_text(json.dumps(envelope, indent=2, sort_keys=True))
print("WROTE", out)
print("receipt_body_sha256", sha(body))
print("envelope_sha256", sha(out.read_bytes()))
