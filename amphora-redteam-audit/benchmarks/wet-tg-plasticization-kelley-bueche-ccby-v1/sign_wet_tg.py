"""DSSE-Ed25519-sign the wet-Tg water-plasticization AUDIT_ONLY receipt.
Signs the canonical diagnostic whose bytes reproduced identically across two runs
(two-replay SHA gate = PASS), using the repo LOCAL_DEVELOPMENT_AUDIT_ONLY key
(local-9028773f...), explicitly NOT a trust-anchored phase0 key. AUDIT_ONLY:
promotes nothing, signs no phase0 evaluation/review receipt, modifies no existing
receipt or manifest.
"""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
BENCH = ROOT / "amphora-redteam-audit/benchmarks/wet-tg-plasticization-kelley-bueche-ccby-v1"
KEY = ROOT / ".amphora/control/local-ed25519.key"
PUB = json.loads((ROOT / ".amphora/control/local-ed25519.pub.json").read_text())

def sha(b): return hashlib.sha256(b).hexdigest()
def pae(t, body): return b"DSSEv1 " + str(len(t)).encode() + b" " + t.encode() + b" " + str(len(body)).encode() + b" " + body

diag_bytes = (BENCH / "diagnostic.canonical.json").read_bytes()
runb_bytes = (BENCH / "diagnostic.runB.json").read_bytes()
diag_sha, runb_sha = sha(diag_bytes), sha(runb_bytes)
assert diag_sha == runb_sha, f"two-replay gate FAIL {diag_sha} != {runb_sha}"
diag = json.loads(diag_bytes)
harness_sha = sha((BENCH / "wet_tg_plasticization_audit.py").read_bytes())

receipt = {
    "schema": "amphora.redteam-audit.wet-tg-plasticization-kelley-bueche-ccby-v1-replay-receipt.v1",
    "authority": "AUDIT_ONLY",
    "run_type": "WET_TG_WATER_PLASTICIZATION_CCBY_REPLAY",
    "promotes_authority": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "module": "amphora-redteam-audit",
    "benchmark": "amphora-redteam-audit/wet-tg-plasticization-kelley-bueche-ccby-v1",
    "target_module": diag["target_module"],
    "target_capability": diag["target_capability"],
    "theory": diag["theory"],
    "dataset": diag["dataset"],
    "rights": diag["dataset"]["rights"],
    "parameter_free_engines": diag["parameter_free_engines"],
    "empirical_plasticization_slope": diag["empirical_plasticization_slope"],
    "effective_tg_water_diagnostic": diag["effective_tg_water_diagnostic"],
    "hypothesis_test": diag["hypothesis_test"],
    "validity_gates": diag["validity_gates"],
    "verdict": diag["verdict"],
    "illustrative_in_scope_deployment": diag["illustrative_in_scope_deployment"],
    "marine_relevance": diag["marine_relevance"],
    "phase0_reconciliation_redteam": diag["phase0_reconciliation_redteam"],
    "non_circularity": ("The parameter-free Fox / Kelley-Bueche predictions consume only "
                        "(dry Tg, water mass fraction, a literature Tg_water constant, densities). "
                        "The MEASURED wet Tg is never an input; it is only the validation target. "
                        "The refutation of a-priori magnitude is therefore genuine, not circular."),
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "replays": 2, "independent_runs": True,
        "canonical_diagnostic_sha256": diag_sha,
        "runB_diagnostic_sha256": runb_sha,
        "harness_sha256": harness_sha,
    },
    "does_not_close": [
        "does NOT promote amphora-molecule-property to PHASE_0: phase-0 is a governance "
        "state (scientific_success_required_for_phase0=false on all 29 locks) and requires "
        "two trust-anchored phase0 signatures this key cannot supply",
        "does NOT change the Phase-0 count (still 10; all infra + solvency)",
        "does NOT claim a validated a-priori wet-Tg MAGNITUDE (explicitly REFUTED here)",
        "does NOT assert wet-lab measurement, product qualification, or superiority",
    ],
    "does_not": diag["does_not"],
    "signing_key": {"key_id": PUB["key_id"], "authority": PUB["authority"],
                    "trust_anchored_in_phase0_store": False},
}
body = json.dumps(receipt, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.redteam-wet-tg-plasticization-kelley-bueche-ccby+json"
sk = Ed25519PrivateKey.from_private_bytes(KEY.read_bytes())
sig = sk.sign(pae(ptype, body))
envelope = {"payload": base64.standard_b64encode(body).decode(), "payloadType": ptype,
            "signatures": [{"keyid": PUB["key_id"], "sig": base64.standard_b64encode(sig).decode()}]}
out = BENCH / "replay_receipt.v1.dsse.json"
out.write_text(json.dumps(envelope, indent=2, sort_keys=True))
print("WROTE", out)
print("receipt_body_sha256", sha(body))
print("envelope_sha256", sha(out.read_bytes()))
print("two_replay_sha256", diag_sha)
