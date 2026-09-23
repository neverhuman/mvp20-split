"""DSSE-Ed25519-sign the rights-integrity audit receipt.

Signs the canonical diagnostic whose bytes reproduced identically across two
independent executions (two-replay SHA gate = PASS). Signs with the repo
LOCAL_DEVELOPMENT_AUDIT_ONLY key (local-9028773f...), explicitly NOT a
trust-anchored phase0 key. It records an integrity finding; it modifies no
existing receipt and promotes nothing.
"""
import base64
import hashlib
import json
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

ROOT = Path(".")
BENCH = Path("amphora-redteam-audit/benchmarks/rights-integrity-v1")
KEY = Path(".amphora/control/local-ed25519.key")
PUB = json.loads(Path(".amphora/control/local-ed25519.pub.json").read_text())
CANONICAL_SHA = "130707cd8c1884807995e2f745fa1dffd6aa707badfec0b39972e94fb9b3023d"


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
harness_sha = sha((BENCH / "rights_integrity_audit.py").read_bytes())

receipt = {
    "schema": "amphora.redteam-audit.rights-integrity-v1-replay-receipt.v1",
    "authority": "AUDIT_ONLY",
    "run_type": "RIGHTS_INTEGRITY_AUDIT_REPLAY",
    "promotes_authority": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "module": "amphora-redteam-audit",
    "benchmark": "amphora-redteam-audit/rights-integrity-v1",
    "purpose": (
        "Machine-checkable red-team of the '66 signed scientific receipts' "
        "headline. Applies the tree's own rights ledger "
        "(feedback/v2/reports/rights-report.json, schema rights-decision.v2) to "
        "every manifest-indexed receipt and flags those that derive a scored KPI "
        "from data classed CONTEXT_ONLY. Fixed on-disk facts only; the "
        "positive-vs-diagnostic headline call is an explicit, contestable "
        "constant in the harness."),
    "rights_ledger": diag["rights_ledger"],
    "program_self_knowledge_license_labels": diag["program_self_knowledge_license_labels"],
    "manifest_audited": diag["manifest_audited"],
    "headline_result": diag["verdict"],
    "findings": diag["findings"],
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "replays": 2, "independent_runs": True,
        "canonical_diagnostic_sha256": CANONICAL_SHA,
        "runB_diagnostic_sha256": runb_sha,
        "harness_sha256": harness_sha,
    },
    "does_not_close": [
        "EVALUATION_SIGNATURE_ABSENT (trust-anchored phase0 keys not used here)",
        "does not itself remediate the flagged receipts (governance action)",
    ],
    "does_not": diag["does_not"],
    "signing_key": {"key_id": PUB["key_id"], "authority": PUB["authority"],
                    "trust_anchored_in_phase0_store": False},
}
body = json.dumps(receipt, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.redteam-rights-integrity+json"
sk = Ed25519PrivateKey.from_private_bytes(KEY.read_bytes())
sig = sk.sign(pae(ptype, body))
envelope = {"payload": base64.standard_b64encode(body).decode(), "payloadType": ptype,
            "signatures": [{"keyid": PUB["key_id"], "sig": base64.standard_b64encode(sig).decode()}]}
out = BENCH / "replay_receipt.v1.dsse.json"
out.write_text(json.dumps(envelope, indent=2, sort_keys=True))
print("WROTE", out)
print("receipt_body_sha256", sha(body))
print("envelope_sha256", sha(out.read_bytes()))
