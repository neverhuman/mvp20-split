"""DSSE-Ed25519-sign the Hildebrand-vs-Hansen chi baseline receipt for
amphora-solvency-score. Signs the timing-free canonical diagnostic whose bytes
reproduced identically across two independent executions (two-replay SHA-256
gate = PASS). Signs with the repo LOCAL_DEVELOPMENT_AUDIT_ONLY key
(local-9028773f...), NOT the trust-anchored phase0-evaluator key. AUDIT_ONLY:
does not promote the module, does not edit the portfolio manifest, does not
close EVALUATION_SIGNATURE_ABSENT.
"""
import base64
import hashlib
import json
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
BENCH = ROOT / "amphora-solvency-score/benchmarks/hildebrand-vs-hansen-chi-v1"
KEY = ROOT / ".amphora/control/local-ed25519.key"
PUB = json.loads((ROOT / ".amphora/control/local-ed25519.pub.json").read_text())
CANONICAL_SHA = "f47de3e2456e3fca85a98ddcc07b6305f00300e67d9b0bb524d806dae7aab73e"

OUT_RECEIPT = (ROOT / "amphora-solvency-score/reference/mvp20/data/"
               "hildebrand_vs_hansen_chi_baseline_receipt.v1.json")
OUT_KPI = (ROOT / "amphora-solvency-score/evidence/phase0/kpis/"
           "hildebrand-vs-hansen-chi-baseline-v1-kpi.v1.json")


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def pae(t, body):
    return (b"DSSEv1 " + str(len(t)).encode() + b" " + t.encode() + b" "
            + str(len(body)).encode() + b" " + body)


diag_bytes = (BENCH / "diagnostic.canonical.json").read_bytes()
runb_bytes = (BENCH / "diagnostic.runB.json").read_bytes()
diag_sha = sha(diag_bytes)
runb_sha = sha(runb_bytes)
assert diag_sha == CANONICAL_SHA, f"{diag_sha} != {CANONICAL_SHA}"
assert runb_sha == CANONICAL_SHA, f"runB {runb_sha} != {CANONICAL_SHA} (two-replay gate)"
diag = json.loads(diag_bytes)
assert diag["all_gates_pass"] is True, "gates did not all pass"
harness_sha = sha((BENCH / "run_hildebrand.py").read_bytes())

agg = diag["aggregate"]
body_obj = {
    "schema": "amphora.solvency-score.hildebrand-vs-hansen-chi-baseline-receipt.v1",
    "authority": "AUDIT_ONLY",
    "run_type": "PHYSICAL_BASELINE_HEAD_TO_HEAD_REPLAY",
    "promotes_authority": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "edits_portfolio_manifest": False,
    "module": "amphora-solvency-score",
    "benchmark": "amphora-solvency-score/hildebrand-vs-hansen-chi-v1",
    "purpose": (
        "A-priori (unfitted) head-to-head of two published cohesive-energy chi "
        "models on the module's in-tree external-validation corpus (8 published "
        "polymer-solvent chi values, Van Krevelen 1990 Table 7.6 / Bawn 1949 / "
        "Sakurada 1954 / Krigbaum 1959 / Malcolm-Rowlinson 1957): the incumbent "
        "Hansen three-component parameter (dD/dP/dH) versus the single Hildebrand "
        "solubility parameter delta_total. The two models share an identical "
        "entropic term (0.34) and identical prefactor V_s/(RT); ONLY the "
        "cohesive-distance metric differs, so the comparison isolates the value "
        "of resolving cohesion into three components. The prefactor is "
        "back-derived from the already-signed Hansen receipt, reproducing its "
        "chi column byte-exactly (known-answer bind) before the Hildebrand "
        "column is swapped in."),
    "target_property": diag["target_property"],
    "source_receipt": diag["source_receipt"],
    "constants": diag["constants"],
    "headline_result": {
        "hansen_3_component": agg["hansen_3_component"],
        "hildebrand_1_parameter": agg["hildebrand_1_parameter"],
        "mae_ratio_hildebrand_over_hansen": agg["mae_ratio_hildebrand_over_hansen"],
        "water_subset_strong_hbond": diag["water_subset_strong_hbond"],
        "hansen_known_answer_reproduction_exact": True,
        "interpretation": diag["interpretation"],
    },
    "physical_baselines": {
        "incumbent_hansen": ("C. M. Hansen, Hansen Solubility Parameters: A "
                             "User's Handbook, 2nd ed., CRC Press 2007, ISBN "
                             "978-0-8493-7248-3, Eq. 2.9; Van Krevelen & Te "
                             "Nijenhuis, Properties of Polymers, 4th ed., "
                             "Elsevier 1990, Sec. 7.2."),
        "comparator_hildebrand": ("J. H. Hildebrand & R. L. Scott, The "
                                  "Solubility of Nonelectrolytes, 3rd ed., "
                                  "Reinhold 1950 (regular-solution theory); "
                                  "Van Krevelen 1990 Sec. 7.2 Eq. 7.9 "
                                  "(scalar-delta chi)."),
    },
    "gates": diag["gates"],
    "all_gates_pass": diag["all_gates_pass"],
    "fail_closed_rate": diag["fail_closed_rate"],
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "replays": 2,
        "independent_runs": True,
        "canonical_diagnostic_sha256": CANONICAL_SHA,
        "runB_diagnostic_sha256": runb_sha,
        "harness_sha256": harness_sha,
        "source_receipt_sha256": diag["source_receipt"]["sha256"],
    },
    "closes": [],
    "does_not_close": [
        "EVALUATION_SIGNATURE_ABSENT (trust-anchored phase0-evaluator key absent on host)",
        "module promotion to PHASE_0 (requires human dual-identity ceremony keys)",
        "portfolio manifest edit (66 receipts / 11 modules unchanged)",
        "external solubility validation beyond the 8-pair in-tree corpus (the "
        "externally-validated science remains the separate BigSolDB leave-solute-out benchmark)",
    ],
    "claim_locks": {
        "authority_ceiling": "RULE_CITED",
        "scientific_readiness": "LOCKED_INTERNAL",
        "constraint_only": True,
        "no_product_or_optimizer_authority": True,
        "no_wet_lab_or_candidate_performance_claim": True,
    },
    "provenance": {
        "external_chi_data_source": ("Van Krevelen & Te Nijenhuis, Properties of "
                                     "Polymers, 4th ed., Elsevier 1990, Table 7.6; "
                                     "Bawn 1949; Sakurada 1954 J. Polym. Sci.; "
                                     "Krigbaum 1959; Malcolm & Rowlinson 1957 "
                                     "Trans. Faraday Soc. 53:921 -- all via the "
                                     "in-tree hansen_chi_external_validation_8_"
                                     "published_polymer_solvent_pairs receipt."),
        "solvent_hsp_source": "Hansen 2007 Table A.1 (experimental)",
        "scope": ("marine anti-corrosion two-part epoxy-amine coating solvency: "
                  "coating-relevant polymers and solvents (chloroform, water, ethanol)"),
    },
    "signing_key": {"key_id": PUB["key_id"], "authority": PUB["authority"],
                    "trust_anchored_in_phase0_store": False},
}

payload_bytes = json.dumps(body_obj, indent=2, sort_keys=True).encode()
receipt_id = "hildebrand-vs-hansen-chi-baseline-" + sha(payload_bytes)
body_obj["receipt_id"] = receipt_id
payload_bytes = json.dumps(body_obj, indent=2, sort_keys=True).encode()

ptype = "application/vnd.amphora.hildebrand-vs-hansen-chi-baseline-receipt.v1+json"
sk = Ed25519PrivateKey.from_private_bytes(KEY.read_bytes())
sig = sk.sign(pae(ptype, payload_bytes))
envelope = {
    "payload": base64.standard_b64encode(payload_bytes).decode(),
    "payloadType": ptype,
    "signatures": [{"keyid": PUB["key_id"],
                    "sig": base64.standard_b64encode(sig).decode()}],
}

receipt = dict(body_obj)
receipt["signature"] = envelope
OUT_RECEIPT.write_text(json.dumps(receipt, indent=2, sort_keys=True))

kpi = {
    "schema": "amphora.solvency-score.phase0-kpi.hildebrand-vs-hansen-chi-baseline.v1",
    "authority": "AUDIT_ONLY",
    "module": "amphora-solvency-score",
    "receipt_id": receipt_id,
    "receipt_path": str(OUT_RECEIPT),
    "receipt_sha256": None,
    "kpis": {
        "hansen_mae_chi_units": agg["hansen_3_component"]["mae_chi_units"],
        "hansen_pearson_r": agg["hansen_3_component"]["pearson_r"],
        "hildebrand_mae_chi_units": agg["hildebrand_1_parameter"]["mae_chi_units"],
        "hildebrand_pearson_r": agg["hildebrand_1_parameter"]["pearson_r"],
        "mae_ratio_hildebrand_over_hansen": agg["mae_ratio_hildebrand_over_hansen"],
        "water_subset_hansen_mae": diag["water_subset_strong_hbond"]["hansen_mae"],
        "water_subset_hildebrand_mae": diag["water_subset_strong_hbond"]["hildebrand_mae"],
        "fail_closed_rate": diag["fail_closed_rate"],
        "all_gates_pass": diag["all_gates_pass"],
    },
    "two_replay_sha256_gate": "PASS",
    "canonical_diagnostic_sha256": CANONICAL_SHA,
}
OUT_KPI.write_text(json.dumps(kpi, indent=2, sort_keys=True))
kpi["receipt_sha256"] = sha(OUT_RECEIPT.read_bytes())
OUT_KPI.write_text(json.dumps(kpi, indent=2, sort_keys=True))

print("WROTE_RECEIPT", OUT_RECEIPT)
print("WROTE_KPI", OUT_KPI)
print("receipt_id", receipt_id)
print("payload_sha256", sha(payload_bytes))
print("receipt_file_sha256", sha(OUT_RECEIPT.read_bytes()))
print("signature_len_keys", len(envelope))
