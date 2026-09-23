"""DSSE-Ed25519-sign the blend-viscosity mixing-rule AUDIT_ONLY receipt.

Signs with the repo LOCAL_DEVELOPMENT_AUDIT_ONLY key (local-9028773f...),
explicitly NOT a trust-anchored phase0 key. AUDIT_ONLY: promotes nothing, flips
no scientific_readiness flag, signs no phase0 evaluation/review, modifies no
existing receipt, does not change the manifest (still 66 receipts / 11 modules).
"""
import base64
import hashlib
import json
import subprocess
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
BENCH = ROOT / "amphora-redteam-audit/benchmarks/viscosity-blend-mixing-rule-ccby-v1"
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

# independent 3rd confirmatory replay into a temp path
third = BENCH / "diagnostic.runC.tmp.json"
subprocess.run(["python3", str(BENCH / "viscosity_blend_mixing_audit.py"), str(third)],
               check=True, cwd=str(BENCH))
third_sha = sha(third.read_bytes())
third.unlink()
assert third_sha == diag_sha, f"3rd replay FAIL {third_sha} != {diag_sha}"

diag = json.loads(diag_bytes)
harness_sha = sha((BENCH / "viscosity_blend_mixing_audit.py").read_bytes())

receipt = {
    "schema": "amphora.redteam-audit.viscosity-blend-mixing-rule-ccby-v1-replay-receipt.v1",
    "authority": "AUDIT_ONLY",
    "run_type": "VISCOSITY_BLEND_MIXING_RULE_REPLAY",
    "promotes_authority": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "module": "amphora-redteam-audit",
    "benchmark": "amphora-redteam-audit/viscosity-blend-mixing-rule-ccby-v1",
    "target_module": diag["target_module"],
    "also_feeds": diag["also_feeds"],
    "target_capability": diag["target_capability"],
    "new_axis_justification": diag["new_axis_justification"],
    "theory": diag["theory"],
    "fitted_parameters": diag["fitted_parameters"],
    "dataset": diag["dataset"],
    "kendall_monroe_apriori": diag["kendall_monroe_apriori"],
    "grunberg_nissan_oneparam": diag["grunberg_nissan_oneparam"],
    "per_temperature": diag["per_temperature"],
    "independent_cross_source_data_integrity": diag["independent_cross_source_data_integrity"],
    "known_answer_battery": diag["known_answer_battery"],
    "hypothesis_test": diag["hypothesis_test"],
    "validity_gates": diag["validity_gates"],
    "non_circularity": diag["non_circularity"],
    "honest_limitations": diag["honest_limitations"],
    "red_team_review": {
        "reviewer_run": "xbabe1 headless cron (final pre-founder-report)",
        "verified": [
            "recomputed the harness a 3rd independent time => byte-identical SHA-256 "
            + diag_sha + " (2-replay gate + this = 3 concordant runs)",
            "phase-0 claim RED-TEAMED LIVE: module-manifest.json histogram of "
            "scientific_readiness = {UNVALIDATED: 29}; 0/29 VALIDATED; all 29 "
            "ranking_eligible=false. 'FULL Phase-0' is FALSE as a science claim -- it is a "
            "governance lock (promotion needs 2 trusted human-key sigs), not validated science.",
            "hand-check at x1=0.5051, 298.15 K: Kendall-Monroe ln = 0.5051*ln(0.567) + "
            "0.4949*ln(2.045) = 0.0674 => eta_KM = 1.070 mPa.s vs measured 0.697 => +53.5% "
            "over-prediction; confirms strong negative deviation (H-bond disruption).",
            "independent-source data integrity: pure toluene 0.567 (paper, MDPI CC-BY) vs "
            "0.560 (in-tree CC0 CRC/NIST fixture) = +1.25%; 2-propanol 2.045 vs 2.038 = +0.34%. "
            "Two independent rights-clean sources agree to <1.3% -> data not fabricated.",
            "grep of all 66 signed receipts + prior AUDIT axes for "
            "blend|mixing|Kendall|Grunberg|Refutas => ZERO hits: genuinely new blend-level "
            "axis for amphora-viscosity-score (all prior viscosity work is pure-component "
            "Arrhenius or CONTEXT_ONLY-quarantined polyverse melt).",
        ],
        "residual_caveat_for_founders": (
            "This is a SINGLE binary system (one associating chemistry class). The headline "
            "is an HONEST NEGATIVE: a-priori zero-parameter blend-viscosity prediction "
            "(Kendall-Monroe / log-linear) is NOT trustworthy for alcohol-containing marine "
            "thinners -- it over-predicts by ~10-53% (global MAPE 33.9%). The DEFENDED, useful "
            "claims are (a) rank/composition ordering is preserved (Spearman +1.0 at every T), "
            "(b) a single measured mid-composition datum per associating pair (Grunberg-Nissan "
            "d12) recovers the curve to ~3% MAPE, and (c) d12<0 with the correct temperature "
            "trend. The NON-associating contrast case (where log-linear is expected to pass) "
            "was NOT tested this run -- no rights-clean table was fetchable (ACS/Springer "
            "paywalled). Not promotable; establishes the method and its domain boundary."),
        "verdict_on_prior_run": "NEW_HONEST_INCREMENT -> no dishonest promotion anywhere; "
                                "no prior receipt modified; manifest untouched (66/11).",
    },
    "verdict": diag["verdict"],
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "replays": 2, "independent_runs": True, "third_confirmatory_replay": "PASS",
        "canonical_diagnostic_sha256": diag_sha,
        "runB_diagnostic_sha256": runb_sha,
        "third_replay_sha256": third_sha,
        "harness_sha256": harness_sha,
    },
    "does_not_close": diag["does_not_close"],
    "phase0_reconciliation_redteam": diag["phase0_reconciliation_redteam"],
    "signing_key": {"key_id": PUB["key_id"], "authority": PUB["authority"],
                    "trust_anchored_in_phase0_store": False},
}
body = json.dumps(receipt, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.redteam-viscosity-blend-mixing-rule+json"
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
print("third_replay_sha256", third_sha)
print("harness_sha256", harness_sha)
