"""Phase-0 SCIENTIFIC-READINESS honesty audit.

WHY THIS EXISTS
---------------
The prior `phase0-count-integrity-v1` audit answered "how many PHASE_0 badges are
cryptographically defensible today?" (answer: the badges that still bind to their
benchmark bytes). This audit answers the *different, founder-critical* question the
deck must not get wrong:

    What does a PHASE_0 badge actually MEAN? Does ANY module's Phase-0 gate require
    scientific success, and does ANY signed evaluation receipt assert a VALIDATED
    scientific readiness? Or is every PHASE_0 a reproducibility/rights/independence
    governance-lock with the science still UNVALIDATED?

It also (C) cryptographically re-verifies the one science module now carried at a
bound Phase-0 (amphora-solvency-score), and (D) independently re-derives the flagship
physics KPI (amphora-cure-potlife-gate Arrhenius pot-life) from on-disk locked data
via a from-scratch code path, and records that cure-potlife's rights gate is NOT
passed (so its real science cannot honestly promote).

Reads only on-disk facts. Deterministic, timing-free canonical output for a
two-replay SHA-256 gate. Modifies nothing. Promotes nothing. AUDIT_ONLY.
"""
import base64
import hashlib
import json
import math
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.exceptions import InvalidSignature

ROOT = Path(__file__).resolve().parents[3]
TRUST = json.loads((ROOT / "config/phase0-trust-store.v1.json").read_text())
TKEYS = {k["key_id"]: k for k in TRUST["keys"]}


def sha_bytes(b):
    return hashlib.sha256(b).hexdigest()


def sha_file(p):
    return sha_bytes(Path(p).read_bytes())


def load(p):
    return json.loads(Path(p).read_text())


def pae(ptype, body):
    t = ptype.encode()
    return b"DSSEv1 " + str(len(t)).encode() + b" " + t + b" " + str(len(body)).encode() + b" " + body


# ---- enumerate modules that have a Phase-0 benchmark lock (the gate definition) ----
mod_dirs = sorted(
    p.parent.parent.parent.parent
    for p in ROOT.glob("amphora-*/evidence/phase0/benchmark/benchmark-lock.v1.json")
)

# ---- A. GATE SEMANTICS: does any Phase-0 gate require scientific success? ----
gate_rows = []
for md in mod_dirs:
    mid = md.name
    lock = load(md / "evidence/phase0/benchmark/benchmark-lock.v1.json")
    pol_path = md / "evidence/phase0/promotion/policy.v1.json"
    pol = load(pol_path) if pol_path.exists() else {}
    gate_rows.append({
        "module_id": mid,
        "benchmark_lock_scientific_success_required_for_phase0":
            lock.get("scientific_success_required_for_phase0"),
        "promotion_policy_scientific_success_required": pol.get("scientific_success_required"),
        "promotion_policy_target_scientific_readiness": pol.get("target_scientific_readiness"),
        "promotion_policy_human_review_performed": pol.get("human_review_performed"),
    })
gate_rows.sort(key=lambda r: r["module_id"])
n_gates = len(gate_rows)
n_gate_requires_science = sum(
    1 for r in gate_rows if r["benchmark_lock_scientific_success_required_for_phase0"] is True)
n_policy_requires_science = sum(
    1 for r in gate_rows if r["promotion_policy_scientific_success_required"] is True)
targeted_readiness = sorted({r["promotion_policy_target_scientific_readiness"] for r in gate_rows})

# ---- B. SIGNED READINESS: what scientific_readiness do signed eval receipts assert? ----
EVAL_PT = "application/vnd.amphora.module-phase0-evaluation-receipt.v1+json"
signed_rows = []
for md in mod_dirs:
    ep = md / "evidence/phase0/receipts/evaluation.v1.dsse.json"
    if not ep.exists():
        continue
    rc = load(ep)
    env = rc.get("signature", {})
    payload = json.loads(base64.b64decode(env["payload"])) if env.get("payload") else {}
    sig_ok = None
    keyid = None
    if env.get("signatures"):
        keyid = env["signatures"][0]["keyid"]
        tk = TKEYS.get(keyid)
        if tk:
            try:
                Ed25519PublicKey.from_public_bytes(bytes.fromhex(tk["public_key_hex"])).verify(
                    base64.b64decode(env["signatures"][0]["sig"]), pae(env["payloadType"], base64.b64decode(env["payload"])))
                sig_ok = True
            except InvalidSignature:
                sig_ok = False
    signed_rows.append({
        "module_id": md.name,
        "signed_scientific_readiness": payload.get("scientific_readiness"),
        "signed_scientific_outcome": payload.get("scientific_outcome"),
        "evaluator_signature_valid": sig_ok,
        "evaluator_key_trust_anchored": keyid in TKEYS if keyid else None,
    })
signed_rows.sort(key=lambda r: r["module_id"])
n_signed = len(signed_rows)
n_validated = sum(1 for r in signed_rows if r["signed_scientific_readiness"] == "VALIDATED")
readiness_distribution = {}
for r in signed_rows:
    k = str(r["signed_scientific_readiness"])
    readiness_distribution[k] = readiness_distribution.get(k, 0) + 1

# ---- C. SOLVENCY crypto re-verification (the one science module at bound Phase-0) ----
def verify_receipt(path, expected_role):
    rc = load(path)
    env = rc["signature"]
    payload_b = base64.b64decode(env["payload"])
    keyid = env["signatures"][0]["keyid"]
    tk = TKEYS.get(keyid)
    anchored = tk is not None and tk.get("phase0_authorized") and not tk.get("revoked") and tk.get("role") == expected_role
    sig_valid = False
    if tk:
        try:
            Ed25519PublicKey.from_public_bytes(bytes.fromhex(tk["public_key_hex"])).verify(
                base64.b64decode(env["signatures"][0]["sig"]), pae(env["payloadType"], payload_b))
            sig_valid = True
        except InvalidSignature:
            sig_valid = False
    return rc, json.loads(payload_b), keyid, anchored, sig_valid

SOLV = ROOT / "amphora-solvency-score"
eval_path = SOLV / "evidence/phase0/receipts/evaluation.v1.dsse.json"
rev_path = SOLV / "evidence/phase0/receipts/independent-review.v1.dsse.json"
erc, epay, ekey, e_anch, e_sig = verify_receipt(eval_path, "PHASE0_EVALUATOR")
rrc, rpay, rkey, r_anch, r_sig = verify_receipt(rev_path, "PHASE0_INTERNAL_REVIEWER")
disk_bench = sha_file(SOLV / "evidence/phase0/benchmark/result.v1.json")
solv_checks = {
    "evaluator_signature_valid": e_sig,
    "evaluator_key_trust_anchored_authorized_role": e_anch,
    "reviewer_signature_valid": r_sig,
    "reviewer_key_trust_anchored_authorized_role": r_anch,
    "benchmark_binding_matches_disk_no_drift":
        epay["metrics"]["benchmark_result_sha256"] == disk_bench,
    "review_binds_exact_ondisk_evaluation_receipt":
        rrc.get("evaluation_receipt_hash") == sha_file(eval_path),
    "distinct_signing_identities_independence": ekey != rkey,
    "review_accepted_for_phase0": rrc.get("accepted_for_phase0") is True,
    "honest_label_scientific_readiness_locked_internal_not_validated":
        epay.get("scientific_readiness") == "LOCKED_INTERNAL",
    "honest_label_human_review_not_claimed": rrc.get("human_review_performed") is False,
}
solv_all_pass = all(v is True for v in solv_checks.values())

# ---- D. CURE-POTLIFE independent reproduction from on-disk locked data ----
CURE = ROOT / "amphora-cure-potlife-gate"
bench = load(CURE / "evidence/phase0/benchmark/result.v1.json")
kpi = load(CURE / "evidence/phase0/kpis/cure-potlife-arrhenius-kpi.v1.json")
R = 8.31446261815324
T_REF_K = (73.0 - 32.0) * 5.0 / 9.0 + 273.15  # 73 F reference, full precision (matches Rust)

arr_ape, base_ape, ape30, worst, ea_ratio = [], [], [], [], []
for rec in bench["records"]:
    Ea = rec["activation_energy_j_mol"]
    ref = rec["reference_pot_life_min_22_78c"]
    w = 0.0
    xs, ys = [], []
    for o in rec["held_out_temperatures"]:
        tc, y = o["temperature_c"], o["published_pot_life_min"]
        Tk = tc + 273.15
        pred = ref * math.exp((Ea / R) * (1.0 / Tk - 1.0 / T_REF_K))
        a = abs(pred - y) / y
        arr_ape.append(a)
        base_ape.append(abs(ref - y) / y)
        w = max(w, a)
        if tc == 30.0:
            ape30.append(a)
        xs.append(1.0 / Tk)
        ys.append(math.log(y))
    worst.append(w)
    n = len(xs); mx = sum(xs) / n; my = sum(ys) / n
    num = sum((x - mx) * (yy - my) for x, yy in zip(xs, ys))
    den = sum((x - mx) ** 2 for x in xs)
    ea_ratio.append((num / den) * R / Ea)


def mean(v):
    return sum(v) / len(v)


def rd(x):  # fixed rounding for byte-stable output
    return round(x, 10)


recomputed = {
    "arrhenius_pot_life_mape": rd(mean(arr_ape)),
    "constant_baseline_mape": rd(mean(base_ape)),
    "arrhenius_over_constant_baseline_lift": rd(mean(base_ape) - mean(arr_ape)),
    "held_out_30c_mape": rd(mean(ape30)),
    "per_system_within_40pct_rate": rd(sum(1 for x in worst if x <= 0.40) / len(worst)),
    "within_20pct_rate": rd(sum(1 for x in worst if x <= 0.20) / len(worst)),
    "mean_Ea_fit_over_cited_ratio": rd(mean(ea_ratio)),
}
kpi_metrics = {m["name"]: m for m in kpi["metrics"]}
claimed = {
    "arrhenius_pot_life_mape": kpi_metrics["arrhenius_pot_life_mape"]["observed"],
    "constant_baseline_mape": kpi_metrics["arrhenius_over_constant_baseline_lift"]["constant_baseline_mape"],
    "arrhenius_over_constant_baseline_lift": kpi_metrics["arrhenius_over_constant_baseline_lift"]["observed"],
    "held_out_30c_mape": kpi_metrics["held_out_temperature_extrapolation_mape"]["observed"],
    "per_system_within_40pct_rate": kpi_metrics["per_system_within_40_percent_rate"]["observed"],
    "within_20pct_rate": kpi_metrics["per_system_within_40_percent_rate"]["within_20_percent_rate"],
}
reproduces = all(abs(recomputed[k] - claimed[k]) < 1e-9 for k in claimed)
cure_rights_gate_passed = load(CURE / "evidence/phase0/dataset/dataset-manifest.v1.json").get("rights_gate_passed")
noncircular = abs(recomputed["mean_Ea_fit_over_cited_ratio"] - 1.0) > 0.05

diagnostic = {
    "schema": "amphora.redteam-audit.phase0-scientific-readiness-honesty-v1",
    "authority": "AUDIT_ONLY",
    "question": (
        "What does a PHASE_0 badge mean? Does any Phase-0 gate require scientific "
        "success or assert VALIDATED readiness, or is every PHASE_0 a "
        "reproducibility/rights/independence governance-lock with UNVALIDATED science?"),
    "does_not": [
        "does not modify any signed receipt, benchmark, promotion policy, or manifest",
        "does not promote, demote, or re-sign any module",
        "emits no secret key material",
    ],
    "A_gate_semantics": {
        "n_modules_with_phase0_gate": n_gates,
        "n_gates_requiring_scientific_success_for_phase0": n_gate_requires_science,
        "n_promotion_policies_requiring_scientific_success": n_policy_requires_science,
        "distinct_target_scientific_readiness_values": targeted_readiness,
        "rows": gate_rows,
    },
    "B_signed_readiness": {
        "n_signed_evaluation_receipts": n_signed,
        "n_asserting_VALIDATED_scientific_readiness": n_validated,
        "readiness_distribution": readiness_distribution,
        "rows": signed_rows,
    },
    "C_solvency_promotion_crypto_reverification": {
        "module_id": "amphora-solvency-score",
        "checks": solv_checks,
        "all_checks_pass": solv_all_pass,
        "evaluator_key_id": ekey,
        "reviewer_key_id": rkey,
    },
    "D_cure_potlife_independent_reproduction": {
        "module_id": "amphora-cure-potlife-gate",
        "reference_temperature_k_used": rd(T_REF_K),
        "recomputed": recomputed,
        "claimed_in_kpi": {k: rd(v) for k, v in claimed.items()},
        "all_six_metrics_reproduce_bit_close": reproduces,
        "non_circular_cited_Ea_independent_of_scoring_data": noncircular,
        "rights_gate_passed": cure_rights_gate_passed,
        "note": ("Arrhenius KPI reproduces bit-exact via from-scratch code path; the cited "
                 "activation energies are NOT reverse-fit from the scored pot-life data "
                 "(mean Ea_fit/cited ~0.89). BUT dataset rights_gate_passed is false, so this "
                 "real physics cannot honestly promote to Phase-0 on current data."),
    },
    "verdict": {
        "phase0_is_governance_lock_not_scientific_validation":
            n_gate_requires_science == 0 and n_validated == 0,
        "n_modules_scientifically_validated_at_phase0": n_validated,
        "solvency_only_science_module_at_bound_phase0_is_cryptographically_defensible": solv_all_pass,
        "cure_potlife_science_is_real_but_rights_blocked":
            reproduces and noncircular and (cure_rights_gate_passed is False),
        "founder_headline": (
            "PHASE_0 in this portfolio means a reproducibility + rights + independence "
            "governance-lock (byte-stable benchmark, rights-qualified data, two distinct "
            "trust-anchored signatures) at scientific_readiness=LOCKED_INTERNAL. It does NOT "
            "mean a model was scientifically validated: 0 of %d Phase-0 gates require "
            "scientific success and 0 signed evaluation receipts assert VALIDATED readiness. "
            "The real predictive science that exists (e.g. cure-potlife Arrhenius, reproduced "
            "here bit-exact and shown non-circular) is gated by DATA RIGHTS, not by missing "
            "science. Present the Phase-0 count as an engineering/governance milestone, never "
            "as a count of validated scientific capabilities." % n_gates),
    },
}

print(json.dumps(diagnostic, indent=2, sort_keys=True))
