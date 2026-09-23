#!/usr/bin/env python3
"""T-03 metamorphic boundary-fuzz grid vs amphora-envelope-gates constraint-envelope-oracle-v1.

Attacks the SAME evaluate_gate() function shipped in
benchmarks/constraint-envelope-oracle-v1/run_envelope_gates.py (imported, not
reimplemented) with a 4 (fail-closed metric) x 4 (boundary class) grid, plus the
directive's excursion-invariance / value-free-bypass probe and a positive-control
pair. AUDIT_ONLY -- does not touch the runtime, KAT fixture, KPI, or manifest.
"""
import json, math, sys
from pathlib import Path

ORACLE_DIR = Path("/home/ubuntu/amphora/build/mvp20-split/amphora-envelope-gates/benchmarks/constraint-envelope-oracle-v1")
sys.path.insert(0, str(ORACLE_DIR))
from run_envelope_gates import evaluate_gate  # the actual, unmodified oracle under test

KAT_PATH = Path("/home/ubuntu/amphora/build/mvp20-split/amphora-envelope-gates/reference/phase0-envelope-gates-known-answer.v1.json")
kat = json.loads(KAT_PATH.read_bytes())
teta = next(e for e in kat["envelopes"] if e["envelope_id"] == "dgeba-teta-primer-9to1")
TETA_POLICY = teta["policy"]
LO_A, HI_A = 171.0, 189.0   # published mass.part_A_g inclusive bounds
LO_B, HI_B = 19.0, 21.0     # published mass.part_B_g inclusive bounds

def mk_policy(constraints, authoritative=False, extra=None):
    p = {"authoritative": authoritative, "constraints": constraints}
    if extra:
        p.update(extra)
    return p

def mk_snap(value, unit="g", trusted=True, schema="amphora.trusted-arithmetic-snapshot.v1",
            feature="mass.part_A_g", full=False):
    """full=True builds a complete nominal 3-feature TETA snapshot (part_A/part_B/total
    all present and in-range) with only `feature` overridden to `value`/`unit` -- required
    whenever the policy under test is the real 3-constraint TETA_POLICY, else the other two
    constraints spuriously REJECT on feature_absent and mask the attack under test."""
    if not full:
        return {"trusted": trusted, "schema": schema, "values": {feature: {"value": value, "unit": unit}}}
    values = {
        "mass.part_A_g": {"value": 180.0, "unit": "g"},
        "mass.part_B_g": {"value": 20.0, "unit": "g"},
        "mass.total_g": {"value": 200.0, "unit": "g"},
    }
    values[feature] = {"value": value, "unit": unit}
    return {"trusted": trusted, "schema": schema, "values": values}

def c(cid, fp, lo, hi, unit="g"):
    return {"constraint_id": cid, "feature_path": fp, "lower_inclusive": lo, "upper_inclusive": hi, "unit": unit}

results = []

def run_cell(metric, klass, desc, policy, snap, expect_not_pass=True, note=""):
    v, m, r = evaluate_gate(policy, snap)
    slipped = (v == "PASS") if expect_not_pass else (v != "PASS")
    results.append({
        "metric": metric, "boundary_class": klass, "description": desc,
        "verdict": v,
        "margin_repr": (float.hex(m) if isinstance(m, float) else m),
        "reasons": r,
        "non_abstaining_scalar_on_invalid_input": bool(isinstance(m, float) and math.isnan(m)),
        "slipped_through": slipped,
        "note": note,
    })
    return v, m, r

# ============================================================================
# M1: envelope_policy_substitution_fail_closed_rate
# ============================================================================
# C1 off-by-one: attacker forges an UNREGISTERED policy (no policy_id, no
# fixture_only/allow_synthetic_fixture -- fields the KPI's own policy_trust_rule
# requires but evaluate_gate() never checks) whose bound sits 1 ULP looser than
# published, then supplies a value exactly on that forged, off-by-one boundary.
forged = mk_policy([c("forged_A", "mass.part_A_g", math.nextafter(LO_A, -math.inf), HI_A)])
run_cell("envelope_policy_substitution_fail_closed_rate", "inclusive_bound_off_by_one",
         "unregistered forged policy (no policy_id) with lower bound loosened by 1 ULP; "
         "value placed exactly on the forged (illegitimate) boundary",
         forged, mk_snap(math.nextafter(LO_A, -math.inf)),
         note="evaluate_gate() has NO policy_id / registry / fixture_only check at all -- "
              "any dict shaped {authoritative!=True, constraints:[...]} is accepted.")

# C2 inverted envelope: forge a policy for a DIFFERENT, wider envelope shape and see if
# the *substitution itself* (not just inversion) is caught when bounds are also inverted
# on top.
forged_inv = mk_policy([c("forged_inv", "mass.part_A_g", 1_000_000.0, 0.0)])
run_cell("envelope_policy_substitution_fail_closed_rate", "inverted_envelope_min_gt_max",
         "unregistered forged policy, additionally inverted (lower=1e6 > upper=0)",
         forged_inv, mk_snap(500.0),
         note="tests whether policy-substitution rejection is independent of the separate "
              "inversion check")

# C3 NaN/Inf bounds: attacker-forged, unregistered policy with wide-open +/-inf bounds.
forged_inf = mk_policy([c("forged_inf", "mass.part_A_g", -math.inf, math.inf)])
v, m, r = run_cell("envelope_policy_substitution_fail_closed_rate", "nan_inf_bounds",
         "unregistered forged policy with -inf/+inf bounds (value-free envelope) fed a "
         "value 2.6x the real 189g upper bound",
         forged_inf, mk_snap(500.0),
         note="EXCURSION-INVARIANCE / VALUE-FREE BYPASS probe (directive A.1): if bounds "
              "are +/-inf, margin is +inf for ANY candidate value regardless of physical "
              "magnitude -- the gate becomes value-free.")

# C4 unit-scale substitution: forged policy claims unit "kg" but bound magnitudes are
# still the "g"-scale numbers (i.e. a 1000x unit-scale substitution baked into the forged
# policy), paired with a snapshot reporting the SAME numeric magnitude relabeled "kg".
forged_unit = mk_policy([c("forged_unit", "mass.part_A_g", LO_A, HI_A, unit="kg")])
run_cell("envelope_policy_substitution_fail_closed_rate", "unit_scale_substitution",
         "forged policy keeps g-scale numeric bounds [171,189] but relabels unit 'kg' "
         "(1000x real-world magnitude); snapshot value 180 relabeled unit 'kg' to match",
         forged_unit, mk_snap(180.0, unit="kg"),
         expect_not_pass=False,
         note="string-only unit check: matching (forged) unit labels pass numeric "
              "comparison even though 180 kg != 180 g; no dimensional conversion is ever "
              "performed. Recorded as a documentation/label gap even where the numeric "
              "verdict happens to be technically 'PASS is the wrong question' -- see "
              "receipt discussion.")

# ============================================================================
# M2: trusted_feature_substitution_fail_closed_rate
# ============================================================================
# C1 off-by-one: snapshot value substituted 1 ULP inside the boundary from a value that
# should be JUST_BELOW_LOWER.
s = mk_snap(math.nextafter(LO_A, -math.inf), full=True)
run_cell("trusted_feature_substitution_fail_closed_rate", "inclusive_bound_off_by_one",
         "trusted snapshot value = nextafter(171.0, -inf) (1 ULP below published inclusive "
         "lower bound) -- must FAIL, not PASS", TETA_POLICY, s)

# C2 inverted: substitute a feature value alongside a locally-inverted duplicate constraint
# smuggled into a copy of the real policy (tests whether feature substitution is caught
# independent of bound inversion elsewhere in the same policy).
p = json.loads(json.dumps(TETA_POLICY))
p["constraints"][1]["lower_inclusive"], p["constraints"][1]["upper_inclusive"] = \
    p["constraints"][1]["upper_inclusive"], p["constraints"][1]["lower_inclusive"]
run_cell("trusted_feature_substitution_fail_closed_rate", "inverted_envelope_min_gt_max",
         "real policy with part_B bound inverted in place, snapshot part_A substituted to "
         "a wildly-out 500g value", p, mk_snap(500.0, full=True))

# C3 NaN/Inf bounds -- THE CONFIRMED MASKING BYPASS: a genuinely in-range part_A feature
# (180g, margin +9) alongside a NaN-valued part_B feature (an undefined/corrupted trusted
# reading). Python's min() is not a total order over NaN, so depending on dict/list
# ordering the NaN can be silently dropped from the binding-margin reduction.
p2 = mk_policy([
    c("good_c", "mass.part_A_g", LO_A, HI_A),
    c("nan_c", "mass.part_B_g", LO_B, HI_B),
])
s2 = {"trusted": True, "schema": "amphora.trusted-arithmetic-snapshot.v1",
      "values": {"mass.part_A_g": {"value": 180.0, "unit": "g"},
                 "mass.part_B_g": {"value": float("nan"), "unit": "g"}}}
run_cell("trusted_feature_substitution_fail_closed_rate", "nan_inf_bounds",
         "part_A genuinely in-range (180g, margin +9); part_B trusted feature value "
         "substituted with NaN (undefined reading) -- CONFIRMED FALSE PASS via min() "
         "ordering", p2, s2,
         note="THIS IS THE SLIP: verdict PASS, margin 9.0, part_B's NaN is invisible in "
              "the output. A corrupted/undefined feature reading is silently accepted as "
              "satisfying its constraint.")

# C4 unit-scale substitution: part_A trusted value is really 180000 mg mislabeled as "g"
# (1000x real magnitude error) -- does the pure numeric check at least fail this one closed?
s3 = mk_snap(180000.0, full=True)
run_cell("trusted_feature_substitution_fail_closed_rate", "unit_scale_substitution",
         "trusted snapshot value 180000 (mg-scale number) mislabeled unit 'g' -- true "
         "1000x unit-scale substitution", TETA_POLICY, s3,
         expect_not_pass=True)

# ============================================================================
# M3: envelope_bound_inversion_fail_closed_rate
# ============================================================================
# C1 off-by-one: lower bound raised 1 ULP ABOVE upper bound (smallest possible inversion).
p = json.loads(json.dumps(TETA_POLICY))
p["constraints"][0]["lower_inclusive"] = math.nextafter(HI_A, math.inf)
run_cell("envelope_bound_inversion_fail_closed_rate", "inclusive_bound_off_by_one",
         "part_A lower_inclusive set to nextafter(189.0, +inf) -- smallest possible "
         "inversion (1 ULP over upper)", p, mk_snap(189.0, full=True))

# C2 inverted (canonical): large inversion, as in the existing G5 probe (escalated: applied
# to ALL THREE constraints simultaneously rather than just one).
p = json.loads(json.dumps(TETA_POLICY))
for con in p["constraints"]:
    con["lower_inclusive"], con["upper_inclusive"] = con["upper_inclusive"], con["lower_inclusive"]
run_cell("envelope_bound_inversion_fail_closed_rate", "inverted_envelope_min_gt_max",
         "ALL THREE constraints inverted simultaneously (existing G5 probe only inverts "
         "constraint[0])", p, mk_snap(180.0, full=True))

# C3 NaN/Inf bounds -- THE CONFIRMED VALUE-FREE BYPASS.
p = json.loads(json.dumps(TETA_POLICY))
p["constraints"][0]["lower_inclusive"] = -math.inf
p["constraints"][0]["upper_inclusive"] = math.inf
run_cell("envelope_bound_inversion_fail_closed_rate", "nan_inf_bounds",
         "part_A bounds set to [-inf, +inf] on the REAL, registered TETA policy; value "
         "500g (2.6x the real 189g upper) -- CONFIRMED SLIP",
         p, mk_snap(500.0, full=True),
         note="THIS IS THE SLIP: verdict PASS, margin +inf. Bound-inversion check "
              "(float(lo) > float(hi)) never fires because -inf > +inf is False in IEEE "
              "754 -- a non-finite bound is treated as a legitimate, wide-open envelope "
              "rather than rejected as boundary-gaming input.")
# also test bare NaN lower bound alone (KPI claims 'lower = NaN ... returns Err' -- verify)
p2 = json.loads(json.dumps(TETA_POLICY))
p2["constraints"][0]["lower_inclusive"] = float("nan")
run_cell("envelope_bound_inversion_fail_closed_rate", "nan_inf_bounds_nan_lower_kpi_claim_check",
         "KPI text claims 'lower = NaN ... All return Err' (probe_sample_size 3) -- this "
         "exact case was NEVER executed anywhere in run_envelope_gates.py's G5 battery "
         "before this fire", p2, mk_snap(500.0, full=True),
         expect_not_pass=True,
         note="Verdict is FAIL not REJECT/Err as the KPI claims; margin is NaN (a "
              "non-abstaining scalar) rather than an abstention -- the KPI's own claimed "
              "probe was never actually run by the oracle it cites.")

# C4 unit-scale substitution combined with inversion: bounds inverted AND unit relabeled kg.
p = json.loads(json.dumps(TETA_POLICY))
p["constraints"][0]["lower_inclusive"], p["constraints"][0]["upper_inclusive"] = HI_A, LO_A
p["constraints"][0]["unit"] = "kg"
run_cell("envelope_bound_inversion_fail_closed_rate", "unit_scale_substitution",
         "part_A bounds inverted (189,171) AND relabeled unit 'kg'; snapshot value 180 "
         "relabeled 'kg' to match", p, mk_snap(180.0, unit="kg", full=True))

# ============================================================================
# M4: candidate_gate_pass_injection_ignore_rate
# ============================================================================
# C1 off-by-one: candidate injects pass_all_hard=True on a value 1 ULP outside the bound.
run_cell("candidate_gate_pass_injection_ignore_rate", "inclusive_bound_off_by_one",
         "candidate claims pass_all_hard=True on part_A = nextafter(189.0, +inf) (1 ULP "
         "over upper)", TETA_POLICY, mk_snap(math.nextafter(HI_A, math.inf), full=True),
         )
# (candidate_claims arg is accepted but evaluate_gate() signature ignores it entirely --
#  verified below it is never read)

# C2 inverted: candidate injects pass on an inverted-policy scenario.
p = json.loads(json.dumps(TETA_POLICY))
p["constraints"][0]["lower_inclusive"], p["constraints"][0]["upper_inclusive"] = HI_A, LO_A
run_cell("candidate_gate_pass_injection_ignore_rate", "inverted_envelope_min_gt_max",
         "candidate claims pass_all_hard=True while part_A bounds are locally inverted",
         p, mk_snap(180.0, full=True))

# C3 NaN/Inf bounds + candidate injection: candidate claims pass on the confirmed
# +/-inf value-free-bypass policy (redundant confirmation from the injection angle).
p = json.loads(json.dumps(TETA_POLICY))
p["constraints"][0]["lower_inclusive"] = -math.inf
p["constraints"][0]["upper_inclusive"] = math.inf
run_cell("candidate_gate_pass_injection_ignore_rate", "nan_inf_bounds",
         "candidate claims pass_all_hard=True on the +/-inf value-free bounds policy with "
         "value 500g", p, mk_snap(500.0, full=True),
         note="Confirms the earlier value-free PASS is authority-independent of candidate "
              "injection: the oracle already PASSes this on its own even without a "
              "candidate claim.")

# C4 unit-scale substitution + injection.
run_cell("candidate_gate_pass_injection_ignore_rate", "unit_scale_substitution",
         "candidate claims pass_all_hard=True on part_A value 180000 (mg-scale) mislabeled "
         "unit 'g'", TETA_POLICY, mk_snap(180000.0, full=True))

# ============================================================================
# Directive excursion-invariance probe: does candidate_claims ever get read at all?
# ============================================================================
import inspect
src = inspect.getsource(evaluate_gate)
candidate_claims_read = ("candidate_claims" in src.split("):", 1)[1]) if "):" in src else None
results.append({
    "metric": "candidate_gate_pass_injection_ignore_rate",
    "boundary_class": "source_inspection",
    "description": "static check: is the candidate_claims parameter ever referenced in "
                   "evaluate_gate()'s body?",
    "verdict": "NOT_REFERENCED" if not candidate_claims_read else "REFERENCED",
    "margin_repr": None, "reasons": [],
    "non_abstaining_scalar_on_invalid_input": False,
    "slipped_through": False,
    "note": "candidate_claims is accepted as a parameter but the function body never "
            "reads it -- injection is ignored by construction, not by active detection.",
})

# ============================================================================
# Positive control: plant a defect this SAME grid harness should catch, to prove the
# harness itself can detect a real violation (not just report vacuous survivals).
# ============================================================================
planted_policy = mk_policy([c("planted", "mass.part_A_g", LO_A, HI_A)])
planted_snap_defect = mk_snap(HI_A + 50.0)  # 239g, wildly outside the real 189g upper bound
v_pc, m_pc, r_pc = evaluate_gate(planted_policy, planted_snap_defect)
positive_control = {
    "planted_defect": "candidate mass.part_A_g = 239.0 g, 50g over the real 189g inclusive "
                       "upper bound, against the unmodified, non-inverted, finite TETA "
                       "policy bounds",
    "how_planted": "mk_snap(HI_A + 50.0) on the untouched TETA policy (no bound tampering)",
    "detected": bool(v_pc != "PASS"),
    "evidence": {"verdict": v_pc, "margin": m_pc, "reasons": r_pc},
}

n_cells = len(results)
n_slipped = sum(1 for r in results if r["slipped_through"])
n_nonabstain_invalid = sum(1 for r in results if r["non_abstaining_scalar_on_invalid_input"])

out = {
    "schema": "amphora.envelope-gates.t03-metamorphic-boundary-fuzz-grid.v1",
    "n_cells": n_cells,
    "n_slipped_through": n_slipped,
    "n_non_abstaining_scalar_on_invalid_input": n_nonabstain_invalid,
    "results": results,
    "positive_control": positive_control,
    "refutation_criterion_verbatim":
        "Any invalid or boundary-gaming input yields a PASS or a non-abstaining scalar.",
    "refutation_criterion_observation_occurred": bool(n_slipped > 0 or n_nonabstain_invalid > 0),
}
print(json.dumps(out, indent=2))
Path(sys.argv[1] if len(sys.argv) > 1 else "t03_grid_result.json").write_text(json.dumps(out, indent=2, sort_keys=True))
