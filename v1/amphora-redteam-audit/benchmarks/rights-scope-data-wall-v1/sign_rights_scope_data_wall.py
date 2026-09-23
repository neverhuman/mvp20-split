"""DSSE-Ed25519-sign the rights-scope-data-wall red-team receipt.

Signs the canonical diagnostic whose bytes reproduced identically across two
independent executions (two-replay SHA gate = PASS), with the repo
LOCAL_DEVELOPMENT_AUDIT_ONLY key (local-9028773f...), explicitly NOT a
trust-anchored phase0 key. Records a red-team finding; modifies no existing
receipt and promotes nothing.
"""
import base64
import hashlib
import json
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

BENCH = Path("amphora-redteam-audit/benchmarks/rights-scope-data-wall-v1")
KEY = Path(".amphora/control/local-ed25519.key")
PUB = json.loads(Path(".amphora/control/local-ed25519.pub.json").read_text())
CANONICAL_SHA = "c43d8d9ed639a2850e850cb9628c03b62217c37cb90e498437cd01e31a3358b2"


def sha(b):
    return hashlib.sha256(b).hexdigest()


def pae(t, body):
    return b"DSSEv1 " + str(len(t)).encode() + b" " + t.encode() + b" " + str(len(body)).encode() + b" " + body


diag_bytes = (BENCH / "diagnostic.canonical.json").read_bytes()
runb_bytes = (BENCH / "diagnostic.runB.json").read_bytes()
diag_sha = sha(diag_bytes)
runb_sha = sha(runb_bytes)
assert diag_sha == CANONICAL_SHA, f"{diag_sha} != {CANONICAL_SHA}"
assert runb_sha == CANONICAL_SHA, f"runB {runb_sha} != {CANONICAL_SHA} (two-replay gate)"
diag = json.loads(diag_bytes)
harness_sha = sha((BENCH / "rights_scope_data_wall_audit.py").read_bytes())

receipt = {
    "schema": "amphora.redteam-audit.rights-scope-data-wall-v1-replay-receipt.v1",
    "authority": "AUDIT_ONLY",
    "run_type": "RIGHTS_SCOPE_DATA_WALL_REDTEAM_REPLAY",
    "promotes_authority": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "module": "amphora-redteam-audit",
    "benchmark": "amphora-redteam-audit/rights-scope-data-wall-v1",
    "purpose": (
        "Machine-checked red-team of the 'FULL Phase-0 science' claim for the founder "
        "report. Establishes from on-disk facts that (1) live Phase-0 count is 10, of "
        "which exactly ONE (amphora-solvency-score) carries a scientific benchmark that "
        "actually PASSED, the rest being NOT_APPLICABLE infrastructure (7) or "
        "LOCKED_INTERNAL governance/known-answer locks (3, incl. process-qc-twin whose "
        "own benchmark scientific_outcome is FAILED); and (2) the reason no NEW in-scope "
        "coating-science module can be honestly promoted from in-tree data is a "
        "STRUCTURAL DATA WALL: the intersection of rights-clean and in-scope-experimental-"
        "coating datasets is empty."),
    "live_phase0_rollup": diag["live_phase0"] | {
        "note": "n_phase0_with_PASSED_scientific_benchmark reads each module's evidence/phase0/benchmark/result.v1.json",
    },
    "pre_phase0_blocker_counts": diag["pre_phase0_blocker_counts"],
    "pre_phase0_blocker_taxonomy": diag["pre_phase0_blocker_taxonomy"],
    "data_wall_rollup": {
        "n_data_objects": diag["data_wall"]["n_data_objects"],
        "n_rights_clean": diag["data_wall"]["n_rights_clean"],
        "n_in_scope_coating_physics": diag["data_wall"]["n_in_scope_coating_physics"],
        "n_rights_clean_AND_in_scope_coating_property":
            diag["data_wall"]["n_rights_clean_AND_in_scope_coating_property"],
        "in_scope_coating_physics_that_is_quarantined_context_only":
            diag["data_wall"]["in_scope_coating_physics_that_is_quarantined_context_only"],
        "rights_clean_dataset_scope_breakdown":
            diag["data_wall"]["rights_clean_dataset_scope_breakdown"],
    },
    "corr_data_bare_metal_proof": diag["corr_data_bare_metal_proof"],
    "headline_result": diag["verdict"],
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "replays": 2, "independent_runs": True,
        "canonical_diagnostic_sha256": CANONICAL_SHA,
        "runB_diagnostic_sha256": runb_sha,
        "harness_sha256": harness_sha,
    },
    "does_not_close": [
        "EVALUATION_SIGNATURE_ABSENT (trust-anchored phase0 keys not used here)",
        "does not remediate the 9 EVALUATION_RESULT_MISMATCH drifted badges (governance action)",
        "does not clear any RIGHTS_OR_LICENSE_INCOMPLETE wall (requires rights-qualified in-scope coating data)",
        "does not acquire, license, or ingest any dataset",
    ],
    "does_not": diag["does_not"],
    "signing_key": {"key_id": PUB["key_id"], "authority": PUB["authority"],
                    "trust_anchored_in_phase0_store": False},
}
body = json.dumps(receipt, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.redteam-rights-scope-data-wall+json"
sk = Ed25519PrivateKey.from_private_bytes(KEY.read_bytes())
sig = sk.sign(pae(ptype, body))
envelope = {"payload": base64.standard_b64encode(body).decode(), "payloadType": ptype,
            "signatures": [{"keyid": PUB["key_id"], "sig": base64.standard_b64encode(sig).decode()}]}
out = BENCH / "replay_receipt.v1.dsse.json"
out.write_text(json.dumps(envelope, indent=2, sort_keys=True))
print("WROTE", out)
print("receipt_body_sha256", sha(body))
print("envelope_sha256", sha(out.read_bytes()))
