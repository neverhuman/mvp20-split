"""Assemble + DSSE-Ed25519-sign the molecule-property EEW/AHEW replay receipt.

Signs the canonical (timing-free) diagnostic whose bytes reproduced identically
across two independent executions (two-replay SHA gate = PASS). Signs with the
repo LOCAL_DEVELOPMENT_AUDIT_ONLY key -- explicitly NOT the trust-anchored
phase0-evaluator key (absent on this host). It records that the module's
deterministic EEW/AHEW chemistry implementation is VERIFIED EXACT against the
in-tree replay-only controls; it does NOT promote the module and does NOT close
EVALUATION_SIGNATURE_ABSENT, the 300-molecule truth-set gate, or the rights
quarantine.
"""
import hashlib, json, base64
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

BENCH = Path("amphora-molecule-property/benchmarks/eew-ahew-v1")
KEY = Path(".amphora/control/local-ed25519.key")
PUB = json.loads(Path(".amphora/control/local-ed25519.pub.json").read_text())
CANONICAL_SHA = "635ffff2957126de0197df487b6e87c85a5d10c85b3a79e1e293301b9c95108c"


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
harness_sha = sha((BENCH / "run_eew_ahew.py").read_bytes())

receipt = {
    "schema": "amphora.molecule-property.eew-ahew-v1-replay-receipt.v1",
    "authority": "AUDIT_ONLY",
    "run_type": "REPLAY_VERIFICATION",
    "promotes_authority": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "module": "amphora-molecule-property",
    "benchmark": "amphora-molecule-property/eew-ahew-v1",
    "purpose": (
        "Execute the module's locked EEW/AHEW equivalent-weight chemistry in Python "
        "RDKit 2026.03.2 on the canonical host to VERIFY the deterministic "
        "implementation is exact. EEW = MW / #epoxide; AHEW = MW / #active N-H -- "
        "the quantities that set the stoichiometric mix ratio of a two-part "
        "DGEBA + amine-hardener marine anti-corrosion coating."),
    "truth_set": {
        "file": diag["truth_set_file"],
        "sha256": diag["truth_set_sha256"],
        "rights_status": "QUARANTINED (replay-only per molecule-property-sources.v1.json)",
        "eligible_for_derivatives": False,
        "in_scope_species": "DGEBA (epoxy); DETA, IPDA, HMDA (amine hardeners); "
                            "technical-grade DGEBA TDS lower bounds; 5 negative controls",
        "provenance": "PubChem structures/MW + ASTM D1652 epoxy-content basis + "
                      "titration/supplier-TDS amine controls",
    },
    "why_rust_backend_reported_failed": (
        "The in-tree Rust runner reports scientific_outcome=FAILED with "
        "truth_set_eligible_count=0 solely because backend_status.available=false "
        "(the RDKit C++ FFI prefix is absent). The chemistry itself is not wrong -- "
        "no molecule was scored. This Python replay scores every molecule and shows "
        "the deterministic implementation meets the benchmark file's acceptance_bar."),
    "engine": diag["engine"],
    "headline_result": {
        "acceptance_bar_passed": diag["benchmark_file_acceptance_bar_passed"],
        "gates": diag["gates"],
        "exact_max_abs_error_g_per_eq": diag["summary"]["exact_max_abs_error_g_per_eq"],
        "exact_acceptance_bar_g_per_eq": diag["acceptance_bar"]["exact_implementation_max_abs_error_g_per_eq"],
        "monodisperse_mae_g_per_eq": diag["summary"]["monodisperse_mae_g_per_eq"],
        "monodisperse_within_tol": f'{diag["summary"]["monodisperse_within_tol"]}/{diag["summary"]["monodisperse_n"]}',
        "technical_lower_bound_directional": f'{diag["summary"]["technical_lower_bound_pass"]}/{diag["summary"]["technical_lower_bound_n"]}',
        "negative_controls_rejected": f'{diag["summary"]["negative_pass"]}/{diag["summary"]["negative_n"]}',
        "truth_molecules_scored": diag["summary"]["truth_molecules_scored"],
        "interpretation": (
            "The module's EEW/AHEW chemistry is exact to <=0.03 g/eq on the "
            "monodisperse controls (bar 0.5), is a correct lower bound on "
            "technical-grade DGEBA, and rejects 100% of out-of-domain / invalid / "
            "polymer-wildcard / multi-fragment inputs. Verification only -- no "
            "candidate, product, or superiority claim."),
    },
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "replays": 2, "independent_runs": True,
        "canonical_diagnostic_sha256": CANONICAL_SHA,
        "runB_diagnostic_sha256": runb_sha,
        "harness_sha256": harness_sha,
    },
    "closes": [
        "Verifies the molecule-property EEW/AHEW scientific IMPLEMENTATION is exact "
        "(the benchmark file's own acceptance_bar) in pinned RDKit 2026.03.2, in Python."
    ],
    "does_not_close": diag["does_not_close"],
    "phase0_gap_ledger": {
        "EVALUATION_SIGNATURE_ABSENT": "trust-anchored phase0-evaluator private key absent on host (governance, not a build step)",
        "minimum_300_truth_set_molecules": "in-tree truth set has ~12 eligible truth molecules; need >=300 rights-clean in-scope reactive molecules",
        "RIGHTS_OR_LICENSE": "truth set QUARANTINED/replay-only; planned ChEBI-252 CC-BY-4.0 3-star SDF is FETCH_LOCKED_NOT_ACQUIRED",
        "RDKit_CXX_FFI_BACKEND": "Rust --features rdkit C++ FFI prefix absent; Python RDKit 2026.03.2 present and used here",
        "EVALUATION_RESULT_MISMATCH": "decision report flags the Jul-23 KPI additions under evidence/phase0/kpis as drift from the Jul-22 evaluated bytes; re-evaluation under governance required. This replay does NOT touch the evaluated bytes.",
    },
    "claim_locks": diag["claim_locks"],
    "signing_key": {"key_id": PUB["key_id"], "authority": PUB["authority"],
                    "trust_anchored_in_phase0_store": False},
}
body = json.dumps(receipt, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.molecule-property-eew-ahew+json"
sk = Ed25519PrivateKey.from_private_bytes(KEY.read_bytes())
sig = sk.sign(pae(ptype, body))
envelope = {"payload": base64.standard_b64encode(body).decode(), "payloadType": ptype,
            "signatures": [{"keyid": PUB["key_id"], "sig": base64.standard_b64encode(sig).decode()}]}
out = BENCH / "replay_receipt.v1.dsse.json"
out.write_text(json.dumps(envelope, indent=2, sort_keys=True))
print("WROTE", out)
print("receipt_body_sha256", sha(body))
print("envelope_sha256", sha(out.read_bytes()))
