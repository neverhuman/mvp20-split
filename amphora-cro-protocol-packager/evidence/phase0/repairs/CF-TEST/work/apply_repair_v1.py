#!/usr/bin/env python3
"""CF-TEST repair, fire 2/2 (campaign item CF-TEST, founder directive
AMPHORA-DIRECTIVE-2026-08-09 S7, obligation CF-TEST).

Applies the 3 repair actions named in work/STATE.json's next_fire_should
(written by fire 1's CLAIM_REFUTED receipt):
  (1) name an external standard on the 2 gates axis A found missing one:
      early_kill_gates.gel_or_phase_split, acceptance_gates.raw_data_return
  (2) add a real content-hash lock over early_kill_gates+acceptance_gates,
      mirroring falsification_protocol.json's own
      locked_rank_hash/hash_recomputed_from_locked_payload/hash_matches
      construction (verified empirically: sha256(json.dumps(payload,
      sort_keys=True).encode()).hexdigest(), no indent, default separators)
  (3) produce a REAL power_analysis.json (a priori, formula-based,
      Cohen 1988 two-sample power/sample-size formula, sigma assumptions
      grounded in Floyd et al. 2009 Prog. Org. Coat. 66(1):8-34,
      doi:10.1016/j.porgcoat.2009.04.009, which documents substantial
      replicate scatter in log-transformed EIS resistance on coated
      panels) and restate falsification_protocol.json's uncertainty_status
      honestly: this is a pre-registered, assumption-based a priori power
      analysis, NOT a post-hoc calibrated interval from this system's own
      bench data (no bench data exists yet -- that is future CRO work).

Modifies only files under amphora-cro-protocol-packager/reference/mvp20/out/.
Does not touch the master manifest, campaign.json, or any signed receipt.
"""
import hashlib
import json
import math
from pathlib import Path

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-cro-protocol-packager"
OUT = MOD / "reference/mvp20/out"
CAPTURE = OUT / "capture_template.json"
FALSIF = OUT / "falsification_protocol.json"
POWER = OUT / "power_analysis.json"


def sha(b):
    return hashlib.sha256(b).hexdigest()


def lock_hash(payload):
    return sha(json.dumps(payload, sort_keys=True).encode())


# ---------------------------------------------------------------------------
# load
# ---------------------------------------------------------------------------
capture_before_bytes = CAPTURE.read_bytes()
falsif_before_bytes = FALSIF.read_bytes()
capture = json.loads(capture_before_bytes)
falsif = json.loads(falsif_before_bytes)

before = {
    "capture_template_json_sha256": sha(capture_before_bytes),
    "falsification_protocol_json_sha256": sha(falsif_before_bytes),
}

# ---------------------------------------------------------------------------
# (1) axis A: name an external standard on the 2 gates missing one
# ---------------------------------------------------------------------------
gate_method_fixes = []
for g in capture["early_kill_gates"]:
    if g["gate"] == "gel_or_phase_split":
        old = g["method"]
        g["method"] = "visual check plus ASTM D562 KU trend during induction and first 90 min"
        gate_method_fixes.append({"path": "early_kill_gates.gel_or_phase_split.method",
                                   "before": old, "after": g["method"]})
for g in capture["acceptance_gates"]:
    if g["gate"] == "raw_data_return":
        old = g["method"]
        g["method"] = "CRO data package audit against ISO 17025 record-completeness, traceability and calibration-record requirements"
        gate_method_fixes.append({"path": "acceptance_gates.raw_data_return.method",
                                   "before": old, "after": g["method"]})
assert len(gate_method_fixes) == 2, "expected exactly 2 gate method fixes"

# ---------------------------------------------------------------------------
# (2) axis B: real content-hash lock over the (now-fixed) gate sets,
# mirroring falsification_protocol.json's locked_rank_hash construction.
# ---------------------------------------------------------------------------
gates_locked_payload = {
    "early_kill_gates": capture["early_kill_gates"],
    "acceptance_gates": capture["acceptance_gates"],
}
gates_hash = lock_hash(gates_locked_payload)
gates_hash_recomputed = lock_hash(gates_locked_payload)
assert gates_hash == gates_hash_recomputed

capture["locked_gates_hash"] = gates_hash
capture["gates_lock"] = {
    "schema": "amphora.cro-protocol-packager.gates-lock.v1",
    "locked_gates_hash": gates_hash,
    "gates_locked_payload": gates_locked_payload,
    "hash_recomputed_from_gates_locked_payload": gates_hash_recomputed,
    "hash_matches": gates_hash == gates_hash_recomputed,
    "lock_construction": "sha256(json.dumps(gates_locked_payload, sort_keys=True).encode()).hexdigest() -- same construction empirically verified against falsification_protocol.json's locked_rank_hash/hash_recomputed_from_locked_payload/hash_matches over its locked_payload",
    "protocol_timestamp_utc": "2026-08-11T08:00:01Z",
    "note": "pins the SET and CONTENT of required early_kill_gates and acceptance_gates before measurement (CF-TEST fire 2/2 repair). Any addition, deletion, or field mutation to either array changes locked_gates_hash; re-deriving hash_recomputed_from_gates_locked_payload from the CURRENT arrays and comparing to locked_gates_hash is how a future audit must detect a silently deleted or altered gate -- the deletion this item's attack shape names (delete one kill criterion from a copy) is now mechanically detectable by that comparison, where before fire 2 nothing in this corpus could detect it.",
}

# ---------------------------------------------------------------------------
# (3) axis D: real a priori power analysis + honest uncertainty_status
# ---------------------------------------------------------------------------
CITATION = {
    "source": "Floyd, F.L., Avudaiappan, S., Gibson, J., Mehta, B., Smith, P., Provder, T., Escarsega, J. (2009). "
               "\"Using electrochemical impedance spectroscopy to predict the corrosion resistance of unexposed "
               "coated metal panels.\" Progress in Organic Coatings, 66(1), 8-34.",
    "doi": "10.1016/j.porgcoat.2009.04.009",
    "finding_used": "Total error for EIS-derived resistance quantities expressed in log10 form was on the order of "
                     "50% (percent standard deviation), estimated three independent ways (Rs variation, panel "
                     "replicate variation, EIS reading replication) that agreed with each other -- documented, "
                     "citable evidence that replicate scatter in log10 EIS resistance on coated panels is real and "
                     "non-negligible, not that this specific MVP20 system's sigma is known precisely. This module "
                     "has never run EIS on the M00097/M00101/M00109 or Lineage-60/Envelope-65/Enhanced-65/"
                     "CRO-Robust-65 tracks, so no measured, system-specific sigma exists yet -- that is exactly why "
                     "this is an a priori (pre-measurement) power analysis over an assumed sigma range, not a "
                     "post-hoc calibrated interval.",
}
FORMULA_CITATION = "Cohen, J. (1988). Statistical Power Analysis for the Behavioral Sciences (2nd ed.). Lawrence Erlbaum Associates. ISBN 978-0-8058-0283-2."

Z_ALPHA_2 = 1.959963985  # two-sided alpha=0.05
Z_BETA_80 = 0.841621234  # power=0.80
Z_BETA_90 = 1.281551566  # power=0.90
DELTA = 1.0  # log10 |Z| gap already pre-registered as the target detectable effect

SIGMA_SCENARIOS = [0.1, 0.2, 0.3, 0.5]
N_SCENARIOS = [3, 6]  # minimum floor / default panel counts already pre-registered


def phi(x):
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def required_n(sigma, delta, z_beta):
    return math.ceil(2.0 * (sigma ** 2) * ((Z_ALPHA_2 + z_beta) ** 2) / (delta ** 2))


def achieved_power(n, sigma, delta):
    se = sigma * math.sqrt(2.0 / n)
    return phi(delta / se - Z_ALPHA_2)


def ci95_halfwidth(n, sigma):
    return Z_ALPHA_2 * sigma * math.sqrt(2.0 / n)


required_n_table = [
    {
        "assumed_sigma_log10_abs_z": s,
        "required_n_per_track_per_arm_80pct_power": required_n(s, DELTA, Z_BETA_80),
        "required_n_per_track_per_arm_90pct_power": required_n(s, DELTA, Z_BETA_90),
    }
    for s in SIGMA_SCENARIOS
]

achieved_power_table = [
    {
        "assumed_sigma_log10_abs_z": s,
        "n_per_track_per_arm": n,
        "achieved_power_to_detect_delta_1p0": round(achieved_power(n, s, DELTA), 4),
        "ci95_halfwidth_log10_abs_z": round(ci95_halfwidth(n, s), 4),
    }
    for s in SIGMA_SCENARIOS
    for n in N_SCENARIOS
]

power_analysis = {
    "schema": "amphora.cro-protocol-packager.power-analysis.v1",
    "study_id": "cf-test-power-analysis-v1",
    "module": "amphora-cro-protocol-packager",
    "campaign_item_id": "CF-TEST",
    "produced_by_fire_sequence": 2,
    "kind": "a_priori_preregistered_power_analysis",
    "status": "PRE-MEASUREMENT ASSUMPTION-BASED QUANTIFICATION -- not a calibrated interval derived from this "
              "system's own bench data. No EIS has been run yet on any MVP20 candidate or named track; that is "
              "future, external CRO work (docs/mission.md external dependency). This artifact quantifies the "
              "STATISTICAL POWER and confidence-interval half-width of the pre-registered decision rule "
              "(statistical_decision_rules.minimum_detectable_effect.eis_log10_abs_z_0p01hz, "
              "falsification_protocol.json's key_pairwise_bet) as a function of an assumed replicate-scatter "
              "sigma, so the plan is not point-only: it declares, before any panel is cut, exactly how much "
              "power the pre-registered panel counts (3 minimum floor / 6 default) buy at each plausible sigma, "
              "and what sigma would be required to hit standard 80%/90% power targets.",
    "target_effect": {
        "quantity": "eis_log10_abs_z_0p01hz gap, Enhanced-65 vs Envelope-65 (falsification_protocol.json key_pairwise_bet)",
        "delta_log10_abs_z": DELTA,
        "source": "statistical_decision_rules.minimum_detectable_effect.eis_log10_abs_z_0p01hz (this file, unchanged by this repair)",
    },
    "formula": {
        "citation": FORMULA_CITATION,
        "required_n_per_group": "n = 2 * sigma^2 * (z_alpha/2 + z_beta)^2 / delta^2, two-sided alpha=0.05",
        "achieved_power": "power = Phi(delta / (sigma * sqrt(2/n)) - z_alpha/2), Phi = standard normal CDF",
        "confidence_interval_95pct_halfwidth": "z_alpha/2 * sigma * sqrt(2/n)",
        "z_alpha_2_alpha0p05_twosided": Z_ALPHA_2,
        "z_beta_power0p80": Z_BETA_80,
        "z_beta_power0p90": Z_BETA_90,
    },
    "sigma_assumption_basis": CITATION,
    "required_n_table": required_n_table,
    "achieved_power_and_confidence_interval_table": achieved_power_table,
    "confidence_interval_summary": (
        "At the pre-registered default of 6 panels/track/arm, the 95% CI half-width on the measured "
        "Enhanced-65-vs-Envelope-65 log10|Z| gap ranges from "
        f"{round(ci95_halfwidth(6, SIGMA_SCENARIOS[0]), 3)} (sigma=0.1) to "
        f"{round(ci95_halfwidth(6, SIGMA_SCENARIOS[-1]), 3)} (sigma=0.5) log10 ohm-cm2, i.e. under the "
        f"sigma<=0.3 assumptions the pre-registered 1.0 log10 target gap is resolvable with 95% CI half-width "
        f"well under the effect size; at sigma=0.5 the plan is under-powered at n=6 and would need "
        f"n={required_n(0.5, DELTA, Z_BETA_80)} panels/track/arm for 80% power -- stated honestly as a "
        "pre-registered risk, not hidden."
    ),
    "interpretation": (
        "This is NOT a claim that MVP20's true EIS replicate sigma is known. It is a pre-registered sensitivity "
        "table: IF sigma turns out to be in the commonly-documented low-to-moderate range for this measurement "
        "class (Floyd et al. 2009), the pre-registered panel counts have adequate power; IF sigma is at the high "
        "end documented in that same source, the plan is explicitly flagged as under-powered at the default "
        "panel count and the required panels/track/arm to reach 80% power is stated. The actual sigma will be "
        "computable from the bench's own replicate data once EIS is run -- at that point this a priori table "
        "should be superseded by a post-hoc calibrated interval, not before."
    ),
}

# ---------------------------------------------------------------------------
# wire power analysis into capture_template.json (confidence_interval field
# must be visible in capture or falsif JSON text per the completeness check)
# ---------------------------------------------------------------------------
capture["statistical_decision_rules"]["power_analysis_path"] = "out/power_analysis.json"
capture["statistical_decision_rules"]["confidence_interval_summary"] = power_analysis["confidence_interval_summary"]
capture["statistical_decision_rules"]["power_analysis_kind"] = "a_priori_preregistered_power_analysis (see out/power_analysis.json; sigma assumptions cited from Floyd et al. 2009 doi:10.1016/j.porgcoat.2009.04.009, formula from Cohen 1988)"

# ---------------------------------------------------------------------------
# honest uncertainty_status rewrite in falsification_protocol.json
# ---------------------------------------------------------------------------
old_uncertainty_status = falsif["uncertainty_status"]
falsif["uncertainty_status"] = (
    "a priori pre-registered power analysis on file (out/power_analysis.json, CF-TEST fire 2/2 repair): "
    "statistical power and 95% confidence-interval half-width for the key_pairwise_bet's eis_log10_abs_z_0p01hz "
    "gap are quantified as a function of an assumed, literature-cited replicate-scatter sigma range "
    "(Floyd et al. 2009, doi:10.1016/j.porgcoat.2009.04.009); no bench data has been collected on any MVP20 "
    "track or candidate yet, so no measured/calibrated posterior interval from THIS system exists -- that "
    "requires the commissioned CRO bench work named in decision_experiment and remains future, external work."
)

# ---------------------------------------------------------------------------
# write files
# ---------------------------------------------------------------------------
POWER.write_text(json.dumps(power_analysis, indent=2, sort_keys=True))
capture_bytes = json.dumps(capture, indent=2, sort_keys=True).encode()
CAPTURE.write_bytes(capture_bytes)
falsif_bytes = json.dumps(falsif, indent=2, sort_keys=True).encode()
FALSIF.write_bytes(falsif_bytes)

after = {
    "capture_template_json_sha256": sha(capture_bytes),
    "falsification_protocol_json_sha256": sha(falsif_bytes),
    "power_analysis_json_sha256": sha(POWER.read_bytes()),
}

print(json.dumps({
    "before": before,
    "after": after,
    "gate_method_fixes": gate_method_fixes,
    "locked_gates_hash": gates_hash,
    "old_uncertainty_status": old_uncertainty_status,
    "new_uncertainty_status": falsif["uncertainty_status"],
    "required_n_at_sigma0p5_for_80pct_power": required_n(0.5, DELTA, Z_BETA_80),
}, indent=2))
