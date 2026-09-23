"""DSSE-Ed25519-sign the role-fact-provenance-invariance-v1 replay receipt.

Signs the timing-free diagnostic that reproduced byte-identically across two
independent runs (two-replay SHA gate = PASS) with the repo
LOCAL_DEVELOPMENT_AUDIT_ONLY Ed25519 key (local-9028773f..., NOT the
trust-anchored phase0-evaluator key). AUDIT_ONLY: does NOT promote the module,
does NOT edit the master manifest, does NOT close EVALUATION_SIGNATURE_ABSENT.
"""
import base64
import hashlib
import json
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

BENCH = Path("amphora-molecule-role-ranker/benchmarks/role-fact-provenance-invariance-v1")
KEY = Path(".amphora/control/local-ed25519.key")
PUB = json.loads(Path(".amphora/control/local-ed25519.pub.json").read_text())
CANON_SHA = "7cf8584aa40774832eebf71b46026a9ed922327a37621edc6369e5aa32655a48"


def sha(b):
    return hashlib.sha256(b).hexdigest()


def pae(t, body):
    return (b"DSSEv1 " + str(len(t)).encode() + b" " + t.encode() + b" "
            + str(len(body)).encode() + b" " + body)


cb = (BENCH / "diagnostic.canonical.json").read_bytes()
rb = (BENCH / "diagnostic.runB.json").read_bytes()
assert sha(cb) == CANON_SHA, f"{sha(cb)} != {CANON_SHA}"
assert sha(rb) == CANON_SHA, f"runB {sha(rb)} != {CANON_SHA} (two-replay gate)"
diag = json.loads(cb)
harness_sha = sha((BENCH / "run_fact_provenance_invariance.py").read_bytes())

receipt = {
    "schema": "amphora.molecule-role-ranker.role-fact-provenance-invariance-v1-replay-receipt.v1",
    "authority": "AUDIT_ONLY",
    "run_type": "SCIENCE_VALIDATION_REPLAY",
    "promotes_authority": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "module": "amphora-molecule-role-ranker",
    "benchmark": "amphora-molecule-role-ranker/role-fact-provenance-invariance-v1",
    "purpose": diag["purpose"],
    "primary_references": diag["primary_references"],
    "headline_result": {
        "fact_provenance_parity": diag["fact_provenance_parity"]["records_matching_all_four_handles"],
        "fact_provenance_parity_verdict": diag["fact_provenance_parity"]["verdict"],
        "role_matches_expected": diag["role_verdict_vs_expected"]["records_role_matches_expected"],
        "role_verdict_counts": diag["role_verdict_vs_expected"]["role_verdict_counts"],
        "encoding_invariance_total_evaluations": diag["encoding_invariance"]["total_variant_evaluations"],
        "encoding_invariance_disagreements": len(diag["encoding_invariance"]["disagreements"]),
        "encoding_invariance_verdict": diag["encoding_invariance"]["verdict"],
        "all_hostile_abstained": diag["fail_closed"]["all_hostile_abstained"],
        "verdict": diag["verdict"],
        "interpretation": diag["interpretation"],
    },
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "replays": 2, "independent_runs": True,
        "canonical_diagnostic_sha256": CANON_SHA,
        "runB_diagnostic_sha256": sha(rb),
        "harness_sha256": harness_sha,
        "fixture_sha256": diag["fixture"]["sha256"],
        "rdkit_version": diag["toolkit"]["rdkit_version"],
    },
    "closes": diag["closes"],
    "does_not_close": diag["does_not_close"],
    "phase0_gap_ledger": {
        "EVALUATION_SIGNATURE_ABSENT": "trust-anchored phase0-evaluator private key absent on host (governance, not a build step)",
        "MANIFEST_UNCHANGED": "master receipts manifest (66 receipts / 11 modules) NOT edited; requires human dual-identity Phase-0 ceremony keys",
        "SCOPE": "validates the reactive-function handle provenance + role-verdict encoding invariance on the self-authored CC0 fixture only; Phase-1 needs an external double-labelled expert reference set and a second cheminformatics toolkit cross-check",
        "NEW_FINDING": "all four declared handles were re-derived byte-exact from raw SMILES (39/39 parity), and the zero-parameter role verdict held invariant across 549 deterministic SMILES re-encodings with 0 disagreements, closing an encoding-evasion path the parsimony benchmark left open by trusting the handles",
    },
    "claim_locks": diag["claim_locks"],
    "signing_key": {"key_id": PUB["key_id"], "authority": PUB["authority"],
                    "trust_anchored_in_phase0_store": False},
}
body = json.dumps(receipt, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.molecule-role-ranker-role-fact-provenance-invariance+json"
sk = Ed25519PrivateKey.from_private_bytes(KEY.read_bytes())
sig = sk.sign(pae(ptype, body))
sig_b64 = base64.standard_b64encode(sig).decode()
envelope = {
    "payload": base64.standard_b64encode(body).decode(),
    "payloadType": ptype,
    "signature": sig_b64,
    "signatures": [{"keyid": PUB["key_id"], "sig": sig_b64}],
}
out = BENCH / "replay_receipt.v1.dsse.json"
out.write_text(json.dumps(envelope, indent=2, sort_keys=True))
print("WROTE", out)
print("receipt_body_sha256", sha(body))
print("envelope_sha256", sha(out.read_bytes()))
