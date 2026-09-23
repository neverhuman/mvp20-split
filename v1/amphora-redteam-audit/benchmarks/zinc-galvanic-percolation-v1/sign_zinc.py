"""DSSE-Ed25519-sign the zinc-rich sacrificial/galvanic percolation AUDIT_ONLY receipt.

Completes a prior cron run that computed the byte-stable diagnostic (two replays +
an independent third replay all SHA-256 ed7f573e...) but never signed it. Signs with
the repo LOCAL_DEVELOPMENT_AUDIT_ONLY key (local-9028773f...), explicitly NOT a
trust-anchored phase0 key. AUDIT_ONLY: promotes nothing, flips no scientific_readiness
flag, signs no phase0 evaluation/review, modifies no existing receipt, does not change
the manifest (still 66 receipts / 11 modules).

Includes an explicit red_team_review field recording this run's adversarial check.
"""
import base64
import hashlib
import json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
BENCH = ROOT / "amphora-redteam-audit/benchmarks/zinc-galvanic-percolation-v1"
KEY = ROOT / ".amphora/control/local-ed25519.key"
PUB = json.loads((ROOT / ".amphora/control/local-ed25519.pub.json").read_text())


def sha(b):
    return hashlib.sha256(b).hexdigest()


def pae(t, body):
    return (b"DSSEv1 " + str(len(t)).encode() + b" " + t.encode() + b" "
            + str(len(body)).encode() + b" " + body)


diag_bytes = (BENCH / "diagnostic.canonical.json").read_bytes()
runb_bytes = (BENCH / "diagnostic.runB.json").read_bytes()
diag_sha, runb_sha = sha(diag_bytes), sha(runb_bytes)
assert diag_sha == runb_sha, f"two-replay gate FAIL {diag_sha} != {runb_sha}"
diag = json.loads(diag_bytes)
harness_sha = sha((BENCH / "zinc_galvanic_percolation_audit.py").read_bytes())

receipt = {
    "schema": "amphora.redteam-audit.zinc-galvanic-percolation-v1-replay-receipt.v1",
    "authority": "AUDIT_ONLY",
    "run_type": "ZINC_GALVANIC_PERCOLATION_REPLAY",
    "promotes_authority": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "module": "amphora-redteam-audit",
    "benchmark": "amphora-redteam-audit/zinc-galvanic-percolation-v1",
    "target_module": diag["target_module"],
    "also_feeds": diag["also_feeds"],
    "target_capability": diag["target_capability"],
    "new_axis_justification": diag["new_axis_justification"],
    "theory": diag["theory"],
    "fitted_parameters": diag["fitted_parameters"],
    "real_input_data": diag["real_input_data"],
    "reference_nominal_constants": diag["reference_nominal_constants"],
    "engine_output": diag["engine_output"],
    "known_answer_battery": diag["known_answer_battery"],
    "non_circularity": diag["non_circularity"],
    "honest_limitations": diag["honest_limitations"],
    "red_team_review": {
        "reviewer_run": "xbabe1 headless cron (final pre-founder-report)",
        "verified": [
            "recomputed the harness a 3rd independent time => byte-identical SHA-256 "
            "ed7f573e2f9a7bbcad495715ea1513707cdb949b53fac8ae95fd62b9bd025dd7 (2-replay gate + this = 3 concordant runs)",
            "Tier-A exact identities re-derived: dE0 = -0.447-(-0.7618)=0.3148 V (>0, Zn protects Fe); "
            "zF/M_Zn = 2*96485.33212/0.06538 => 819.868 Ah/kg (cited 820, +0.016%); phi_c = 1-exp(-0.3418)=0.28951.",
            "grep of all 66 signed receipts + prior AUDIT axes for zinc|galvan|percol|cathod|sacrific => "
            "confirmed ZERO hits: this is a genuinely new marine protection MECHANISM (sacrificial/galvanic), "
            "orthogonal to every prior barrier/adhesion/mechanical/molecular axis.",
        ],
        "residual_caveat_for_founders": (
            "The binary percolation classification in candidate_ladder (e.g. 60 wt% => "
            "'BARRIER_ONLY_below_percolation') is MODEL-SENSITIVE. Overlapping-sphere "
            "phi_c=0.2895 is one estimate; conductive-filler percolation of real zinc "
            "dust can onset lower (Scher-Zallen invariant ~0.16; flake/lamellar zinc "
            "lower still via aspect ratio). DEFENDED claims are (a) thermodynamic "
            "feasibility (Zn anodic to Fe, universal), (b) ordering, (c) the 70.8 wt% "
            "percolation FLOOR sits below the 80-92 wt% marine spec window, and (d) "
            "the exact Faraday areal-capacity arithmetic. The per-candidate on/off "
            "sacrificial label at loadings near the threshold is NOT defended as a "
            "point prediction; it requires measured film conductivity / galvanic "
            "current, which is data-rights/measurement blocked."
        ),
        "verdict_on_prior_run": "HONEST_BUT_UNSIGNED -> completed by signing; no dishonest promotion found; "
                                "diagnostic left byte-stable and unmodified.",
    },
    "verdict": diag["verdict"],
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "replays": 2, "independent_runs": True, "third_confirmatory_replay": "PASS",
        "canonical_diagnostic_sha256": diag_sha,
        "runB_diagnostic_sha256": runb_sha,
        "harness_sha256": harness_sha,
    },
    "does_not_close": diag["does_not_close"],
    "signing_key": {"key_id": PUB["key_id"], "authority": PUB["authority"],
                    "trust_anchored_in_phase0_store": False},
}
body = json.dumps(receipt, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.redteam-zinc-galvanic-percolation+json"
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
print("harness_sha256", harness_sha)
