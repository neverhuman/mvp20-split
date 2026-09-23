"""DSSE-Ed25519-sign the cure-potlife external-Ea corroboration audit diagnostic.

Signs the canonical diagnostic whose bytes reproduced identically across two
independent executions (two-replay SHA gate = PASS). Signs with the repo
LOCAL_DEVELOPMENT_AUDIT_ONLY key (local-9028773f...), explicitly NOT a
trust-anchored phase0 key. AUDIT_ONLY red-team corroboration study: promotes
nothing, signs no phase0 evaluation/review receipt, modifies no existing
receipt or manifest.
"""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

BENCH = Path("amphora-redteam-audit/benchmarks/cure-potlife-external-ea-corroboration-v1")
KEY = Path(".amphora/control/local-ed25519.key")
PUB = json.loads(Path(".amphora/control/local-ed25519.pub.json").read_text())
CANONICAL_SHA = "db706ae2ab01001d64230c085f12d8afdc2c15dee329f1dbe8d3f3985137de49"

def sha(b): return hashlib.sha256(b).hexdigest()
def pae(t, body): return b"DSSEv1 " + str(len(t)).encode() + b" " + t.encode() + b" " + str(len(body)).encode() + b" " + body

diag_bytes = (BENCH / "diagnostic.canonical.json").read_bytes()
runb_bytes = (BENCH / "diagnostic.runB.json").read_bytes()
assert sha(diag_bytes) == CANONICAL_SHA, sha(diag_bytes)
assert sha(runb_bytes) == CANONICAL_SHA, "two-replay gate FAILED"
diag = json.loads(diag_bytes)
harness_sha = sha((BENCH / "cure_potlife_external_ea_audit.py").read_bytes())

receipt = {
    "schema": "amphora.redteam-audit.cure-potlife-external-ea-corroboration-v1-replay-receipt.v1",
    "authority": "AUDIT_ONLY",
    "run_type": "CURE_POTLIFE_EXTERNAL_EA_CORROBORATION_REDTEAM",
    "promotes_authority": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "module": "amphora-redteam-audit",
    "benchmark": "amphora-redteam-audit/cure-potlife-external-ea-corroboration-v1",
    "target_module": diag["target_module"],
    "target_capability": diag["target_capability"],
    "target_kpi_id": diag["target_kpi_id"],
    "bound_benchmark_result_sha256": diag["bound_benchmark_result_sha256"],
    "purpose": (
        "Independent external-literature corroboration of amphora-cure-potlife-gate's "
        "per-family apparent activation energies. Tests whether the model's 12 "
        "DGEBA-amine Ea (parameterised from one supplier-TDS + cited-calorimetry "
        "lineage) are corroborated by DGEBA-amine cure Ea published in the open, "
        "rights-separate literature -- anchored on a directly-fetched CC-BY "
        "open-access cycloaliphatic (IPDA) cure-kinetics dataset (PMC6473346). "
        "Honest bracketing/ordering corroboration of the PHYSICS; NOT a Phase-0 gate "
        "and NOT a rights-clean pot-life dataset."),
    "theory": diag["theory"],
    "question": diag["question"],
    "corroboration_kpis": diag["corroboration_kpis"],
    "ccby_rights_clean_anchor": diag["ccby_rights_clean_anchor"],
    "out_of_union_envelope_systems": diag["out_of_union_envelope_systems"],
    "independent_literature_union_envelope_kj_mol": diag["independent_literature_union_envelope_kj_mol"],
    "verdict": diag["verdict"],
    "honest_limitations": diag["honest_limitations"],
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "replays": 2, "independent_runs": True,
        "code_path_independence": "single Python harness, two independent executions (honest scope)",
        "canonical_diagnostic_sha256": CANONICAL_SHA,
        "runB_diagnostic_sha256": sha(runb_bytes),
        "harness_sha256": harness_sha,
    },
    "does_not_close": [
        "does NOT promote amphora-cure-potlife-gate (or any module) to PHASE_0",
        "does NOT change the defensible Phase-0 count, which remains 10 (9 infrastructure/"
        "governance + amphora-solvency-score, the sole promoted science module)",
        "does NOT assert rights_gate_passed; cure-potlife source-lock.v2 stays "
        "rights_gate_passed=false / sources=[]",
        "does NOT perform PHASE0_EVALUATOR / PHASE0_INTERNAL_REVIEWER signing "
        "(AUDIT_ONLY key custody only)",
    ],
    "does_not": diag["does_not"],
    "signing_key": {"key_id": PUB["key_id"], "authority": PUB["authority"],
                    "trust_anchored_in_phase0_store": False},
}
body = json.dumps(receipt, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.redteam-cure-potlife-external-ea+json"
sk = Ed25519PrivateKey.from_private_bytes(KEY.read_bytes())
sig = sk.sign(pae(ptype, body))
envelope = {"payload": base64.standard_b64encode(body).decode(), "payloadType": ptype,
            "signatures": [{"keyid": PUB["key_id"], "sig": base64.standard_b64encode(sig).decode()}]}
out = BENCH / "replay_receipt.v1.dsse.json"
out.write_text(json.dumps(envelope, indent=2, sort_keys=True))
print("WROTE", out)
print("receipt_body_sha256", sha(body))
print("envelope_sha256", sha(out.read_bytes()))
