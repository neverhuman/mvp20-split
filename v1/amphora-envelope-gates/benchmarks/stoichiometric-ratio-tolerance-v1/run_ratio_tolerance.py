#!/usr/bin/env python3
"""amphora-envelope-gates :: stoichiometric-ratio-tolerance-v1

Independent, NON-RUNTIME theory-axis analysis of the deterministic formulation
envelope-gate contract for two-part epoxy-amine (DGEBA + amine) coatings.

MOTIVATING GAP
--------------
The shipped envelope-gate policy for every one of the 10 known-answer envelopes
constrains three features INDIVIDUALLY -- mass.part_A_g, mass.part_B_g, and
mass.total_g -- each with a symmetric +/-5%-by-mass QC band (verified 10/10 by
constraint-envelope-oracle-v1, gate G3). It does NOT constrain the mixing RATIO
r = m_A / m_B, which is the chemically load-bearing quantity: for a two-part
epoxy-amine, the epoxide:amine-hydrogen stoichiometric balance is proportional
to (m_A/m_B) (Wicks/Jones/Pappas 2007 Ch.25; Ellis 1993 Ch.6; May 1988 "Epoxy
Resins" Ch.4). Independent per-part interval membership does NOT bound the ratio
to the same +/-5%.

This harness derives, from first-principles metrology, the ratio tolerance that
the per-part envelope actually INDUCES, and quantifies the gap:

  G1  re-derive nominal ratio r0 = A0/B0 from fixture bytes; confirm it matches
      the published nominal_ratio_by_mass string for all 10 envelopes;
  G2  interval arithmetic (Moore 1966): the exact worst-case ratio corners of
      r=A/B over independent per-part bands are [A_lo/B_hi, A_hi/B_lo] =
      r0*[(1-p)/(1+p), (1+p)/(1-p)]. For the shipped p=0.05 bands this is a
      ratio excursion of +10.5263% / -9.5238% that is INVARIANT across all 10
      envelopes (independent of r0). Verified per-envelope from the actual
      per-part bounds in the fixture;
  G3  metrology ordering (JCGM 100:2008 GUM, Law of Propagation of Uncertainty):
      the combined relative standard uncertainty of a quotient of two
      independent inputs is the RSS u_r/r = sqrt((u_A/A)^2+(u_B/B)^2). With the
      +/-5% read as standard uncertainties this is 7.0711%. Assert the strict
      ordering GUM-RSS (7.0711%) < first-order linear sum (10.0%) < exact
      interval high-side (10.5263%). The exact quotient excursion EXCEEDS the
      first-order linear estimate because A/B is convex in B (JCGM 100:2008
      5.1.2, F.2.4);
  G4  HEADLINE GAP: for every envelope the (part_A=+5%, part_B=-5%) corner
      passes ALL THREE hard gates under the SAME oracle that scored 50/50 in
      constraint-envelope-oracle-v1, yet its mix ratio is +10.5263% off nominal
      -- a stoichiometric imbalance 2.1x the per-part +/-5% QC intent. Count the
      envelopes exhibiting the gap (expect 10/10);
  G5  fail-closed tamper battery for the ratio computation: division by zero
      part_B, negative mass, NaN, untrusted snapshot, and missing part_B must
      all fail closed (ratio not asserted / gate not PASS).

Non-circular: r=A/B, interval endpoints, and the GUM RSS are first-principles
published metrology (JCGM 100:2008; Moore, "Interval Analysis", 1966), authored
here and applied to on-disk fixture bytes. The prior oracle's evaluate_gate is
imported ONLY to confirm (G4) that the ratio-drifted corner passes under the
actual shipped contract -- that reuse is the point: the gap is real under the
gate as specified. AUDIT_ONLY. Does NOT promote authority, flip
scientific_readiness (stays NOT_APPLICABLE), or modify the manifest / locked
dataset / KPI / benchmark-lock.
"""
import hashlib, importlib.util, json, math
from pathlib import Path

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-envelope-gates"
KAT = MOD / "reference/phase0-envelope-gates-known-answer.v1.json"
PRIOR = MOD / "benchmarks/constraint-envelope-oracle-v1/run_envelope_gates.py"

P = 0.05                 # +/-5% per-part QC band (Wicks/Jones/Pappas 2007 Ch.24)
REL_EPS = 1e-9
RND = 10                 # fixed rounding for byte-stable diagnostic


def sha(b): return hashlib.sha256(b).hexdigest()


# import the SHIPPED-fixture oracle (constraint-envelope-oracle-v1) so the G4
# corner-PASS is judged by the exact same gate logic validated at 50/50.
_spec = importlib.util.spec_from_file_location("prior_oracle", PRIOR)
_prior = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_prior)
evaluate_gate = _prior.evaluate_gate


def ratio(a, b):
    """First-principles mix ratio. Fail-closed on non-finite / non-positive B."""
    if not (isinstance(a, (int, float)) and isinstance(b, (int, float))):
        return None
    a = float(a); b = float(b)
    if not (math.isfinite(a) and math.isfinite(b)):
        return None
    if b <= 0.0:
        return None       # division by zero / non-physical denominator
    return a / b


def run():
    kat_bytes = KAT.read_bytes()
    kat = json.loads(kat_bytes)
    envelopes = kat["envelopes"]

    # exact metrology constants (interval arithmetic + GUM), computed once
    hi_factor = (1.0 + P) / (1.0 - P)        # A_hi/B_lo multiplier on r0
    lo_factor = (1.0 - P) / (1.0 + P)        # A_lo/B_hi multiplier on r0
    hi_excursion_pct = (hi_factor - 1.0) * 100.0     # +10.5263...
    lo_excursion_pct = (lo_factor - 1.0) * 100.0     # -9.5238...
    gum_rss_pct = math.sqrt(P * P + P * P) * 100.0   # 7.0711...  (u_A/A=u_B/B=P)
    first_order_linear_pct = (P + P) * 100.0         # 10.0  (|dA/A|+|dB/B|)

    # ---- G1 nominal ratio re-derivation + consistency -------------------
    n_env = 0
    g1_ok = 0
    per_env = []
    for env in envelopes:
        n_env += 1
        A0 = float(env["nominal_part_a_g"])
        B0 = float(env["nominal_part_b_g"])
        r0 = A0 / B0
        # parse the published "A:B" nominal ratio string and re-derive r0
        a_str, b_str = env["nominal_ratio_by_mass"].split(":")
        r0_from_str = float(a_str) / float(b_str)
        g1_consistent = abs(r0 - r0_from_str) <= REL_EPS * r0

        # per-part bands from the actual fixture constraints
        cons = {c["feature_path"]: c for c in env["policy"]["constraints"]}
        A = cons["mass.part_A_g"]; B = cons["mass.part_B_g"]
        A_lo, A_hi = float(A["lower_inclusive"]), float(A["upper_inclusive"])
        B_lo, B_hi = float(B["lower_inclusive"]), float(B["upper_inclusive"])

        # ---- G2 interval-arithmetic ratio corners -----------------------
        r_hi = A_hi / B_lo                 # exact worst-case high ratio
        r_lo = A_lo / B_hi                 # exact worst-case low ratio
        exc_hi = (r_hi / r0 - 1.0) * 100.0
        exc_lo = (r_lo / r0 - 1.0) * 100.0
        # invariant: excursions equal the r0-independent metrology constants
        g2_hi_ok = abs(exc_hi - hi_excursion_pct) <= 1e-6
        g2_lo_ok = abs(exc_lo - lo_excursion_pct) <= 1e-6

        # ---- G4 gap: (A_hi, B_lo) corner passes all 3 hard gates --------
        base_snap = None
        for tc in env["test_cases"]:
            if tc["subgroup"] == "NOMINAL":
                base_snap = tc["snapshot"]
                break
        # construct the ratio-drifted corner snapshot from the base structure
        corner = json.loads(json.dumps(base_snap))
        corner["values"]["mass.part_A_g"]["value"] = A_hi
        corner["values"]["mass.part_B_g"]["value"] = B_lo
        corner["values"]["mass.total_g"]["value"] = A_hi + B_lo
        verdict, margin, _ = evaluate_gate(env["policy"], corner)
        corner_ratio = ratio(A_hi, B_lo)
        corner_excursion_pct = (corner_ratio / r0 - 1.0) * 100.0
        gap = (verdict == "PASS" and abs(corner_excursion_pct) > P * 100.0)

        env_ok = g1_consistent and g2_hi_ok and g2_lo_ok
        g1_ok += int(g1_consistent)
        per_env.append({
            "envelope_id": env["envelope_id"],
            "hardener_family": env["hardener_family"],
            "nominal_part_a_g": A0, "nominal_part_b_g": B0,
            "nominal_ratio_r0": round(r0, RND),
            "r0_from_published_string": round(r0_from_str, RND),
            "g1_nominal_ratio_consistent": g1_consistent,
            "part_a_band_g": [A_lo, A_hi], "part_b_band_g": [B_lo, B_hi],
            "interval_ratio_low": round(r_lo, RND),
            "interval_ratio_high": round(r_hi, RND),
            "ratio_excursion_low_pct": round(exc_lo, RND),
            "ratio_excursion_high_pct": round(exc_hi, RND),
            "g2_high_matches_invariant": g2_hi_ok,
            "g2_low_matches_invariant": g2_lo_ok,
            "corner_A_hi_B_lo_verdict": verdict,
            "corner_ratio": round(corner_ratio, RND),
            "corner_ratio_excursion_pct": round(corner_excursion_pct, RND),
            "corner_binding_margin": (round(float(margin), RND)
                                      if isinstance(margin, float) else None),
            "g4_gap_exhibited": gap,
            "env_ok": env_ok,
        })

    g1_pass = (g1_ok == n_env)
    g2_pass = all(e["g2_high_matches_invariant"] and e["g2_low_matches_invariant"]
                  for e in per_env)
    # ---- G3 metrology ordering ------------------------------------------
    ordering_ok = (gum_rss_pct < first_order_linear_pct < hi_excursion_pct)
    g3_pass = bool(ordering_ok)
    # ---- G4 gap count ---------------------------------------------------
    n_gap = sum(1 for e in per_env if e["g4_gap_exhibited"])
    g4_pass = (n_gap == n_env)

    # ---- G5 fail-closed tamper battery for the ratio computation --------
    base_env = next(e for e in envelopes if e["envelope_id"] == "dgeba-teta-primer-9to1")
    base_nominal = next(tc for tc in base_env["test_cases"] if tc["subgroup"] == "NOMINAL")
    base_snap = base_nominal["snapshot"]
    A0 = float(base_env["nominal_part_a_g"])
    probes = []

    def add_probe(name, ok, detail):
        probes.append({"probe": name, "fail_closed": bool(ok), "detail": detail})

    # 1. division by zero denominator -> ratio must be None (not asserted)
    add_probe("ratio_zero_part_B", ratio(A0, 0.0) is None, "b<=0 rejected")
    # 2. negative denominator -> None
    add_probe("ratio_negative_part_B", ratio(A0, -10.0) is None, "b<=0 rejected")
    # 3. NaN numerator -> None
    add_probe("ratio_nan_part_A", ratio(float("nan"), 20.0) is None, "non-finite rejected")
    # 4. Infinity numerator -> None
    add_probe("ratio_inf_part_A", ratio(float("inf"), 20.0) is None, "non-finite rejected")
    # 5. untrusted snapshot -> gate must not PASS (delegates to shipped oracle)
    s = json.loads(json.dumps(base_snap)); s["trusted"] = False
    v5, _, _ = evaluate_gate(base_env["policy"], s)
    add_probe("untrusted_snapshot_corner", v5 != "PASS", "oracle rejects untrusted")
    # 6. missing part_B feature -> gate must not PASS
    s = json.loads(json.dumps(base_snap)); del s["values"]["mass.part_B_g"]
    v6, _, _ = evaluate_gate(base_env["policy"], s)
    add_probe("missing_part_B_feature", v6 != "PASS", "oracle rejects absent feature")

    n_probes = len(probes)
    n_fail_closed = sum(1 for p in probes if p["fail_closed"])
    g5_pass = (n_fail_closed == n_probes)

    all_pass = all([g1_pass, g2_pass, g3_pass, g4_pass, g5_pass])

    diag = {
        "schema": "amphora.envelope-gates.stoichiometric-ratio-tolerance-diagnostic.v1",
        "study_id": "stoichiometric-ratio-tolerance-v1",
        "module": "amphora-envelope-gates",
        "authority": "AUDIT_ONLY",
        "run_type": "independent_non_runtime_theory_axis",
        "purpose": (
            "Derive from first-principles metrology the stoichiometric mix-ratio "
            "tolerance INDUCED by the shipped per-part +/-5% mass envelopes, and "
            "quantify the per-part-membership -> ratio-gate gap for two-part "
            "epoxy-amine coatings."),
        "theory_reference": [
            "JCGM 100:2008 (GUM) Evaluation of measurement data -- Guide to the "
            "expression of uncertainty in measurement; Law of Propagation of "
            "Uncertainty, 5.1.2, F.2.4 (quotient of independent inputs).",
            "Moore, R.E., Interval Analysis, Prentice-Hall, 1966 (exact worst-case "
            "endpoints of a quotient over independent intervals).",
            "Wicks, Jones, Pappas, Wicks, 'Organic Coatings: Science and "
            "Technology', 3rd ed., Wiley 2007, Ch.24-25 (two-part epoxy-amine QC "
            "mix tolerance, +/-5% by mass).",
            "Ellis, B. (ed.), 'Chemistry and Technology of Epoxy Resins', Blackie "
            "1993, Ch.6 (stoichiometric amine:epoxide balance).",
            "May, C.A. (ed.), 'Epoxy Resins: Chemistry and Technology', 2nd ed., "
            "Marcel Dekker 1988, Ch.4 (off-stoichiometry effect on network)."],
        "non_circularity": (
            "Ratio r=A/B, interval corners [A_lo/B_hi, A_hi/B_lo], and the GUM RSS "
            "u_r/r=sqrt((u_A/A)^2+(u_B/B)^2) are first-principles published "
            "metrology authored here; only on-disk fixture bytes are consumed. The "
            "shipped constraint-envelope-oracle-v1 evaluate_gate is reused only to "
            "confirm the ratio-drifted corner PASSES under the actual contract."),
        "fixture": {
            "path": "reference/phase0-envelope-gates-known-answer.v1.json",
            "sha256": sha(kat_bytes),
            "n_envelopes": n_env,
            "rights": kat.get("rights"),
        },
        "metrology_constants": {
            "per_part_band_fraction": P,
            "interval_ratio_high_factor": round(hi_factor, RND),
            "interval_ratio_low_factor": round(lo_factor, RND),
            "interval_ratio_high_excursion_pct": round(hi_excursion_pct, RND),
            "interval_ratio_low_excursion_pct": round(lo_excursion_pct, RND),
            "gum_rss_combined_rel_std_uncertainty_pct": round(gum_rss_pct, RND),
            "first_order_linear_sum_pct": round(first_order_linear_pct, RND),
            "excursion_invariant_across_envelopes": True,
            "note": (
                "Excursion is r0-independent: (1+p)/(1-p) and (1-p)/(1+p) do not "
                "depend on the nominal ratio. Exact high-side excursion (10.5263%) "
                "EXCEEDS the first-order linear estimate (10.0%) because A/B is "
                "convex in B (JCGM 100:2008 F.2.4)."),
        },
        "gates": {
            "G1_nominal_ratio_re_derivation": {
                "passed": g1_pass, "n_envelopes": n_env, "n_consistent": g1_ok},
            "G2_interval_ratio_corner_invariant": {
                "passed": g2_pass,
                "high_excursion_pct": round(hi_excursion_pct, RND),
                "low_excursion_pct": round(lo_excursion_pct, RND)},
            "G3_gum_metrology_ordering": {
                "passed": g3_pass,
                "ordering": "GUM_RSS < first_order_linear_sum < interval_high",
                "values_pct": [round(gum_rss_pct, RND),
                               round(first_order_linear_pct, RND),
                               round(hi_excursion_pct, RND)]},
            "G4_per_part_membership_ratio_gap": {
                "passed": g4_pass, "n_envelopes": n_env, "n_gap_exhibited": n_gap,
                "gap_definition": (
                    "(part_A=+5%, part_B=-5%) corner PASSES all three hard gates "
                    "yet mix ratio is +10.5263% off nominal (>+/-5% intent)")},
            "G5_ratio_tamper_battery_fail_closed": {
                "passed": g5_pass, "n_probes": n_probes,
                "n_fail_closed": n_fail_closed, "probes": probes},
        },
        "all_gates_passed": all_pass,
        "headline": (
            "Per-part +/-5% mass envelopes INDUCE a stoichiometric mix-ratio "
            "tolerance of +10.5263%/-9.5238% (exact interval arithmetic; GUM RSS "
            "combined 7.0711%), r0-invariant across all 10 epoxy-amine envelopes. "
            "The (A_hi,B_lo) corner passes all three shipped hard gates while the "
            "mix ratio is 2.1x outside the +/-5% QC intent: the 3-constraint "
            "envelope policy does not bound the chemically load-bearing ratio."),
        "closes": (
            "Quantifies, from published metrology, the exact ratio tolerance the "
            "per-part envelope induces and proves the ratio-gate gap is real under "
            "the shipped contract for all 10 envelopes."),
        "does_not_close": (
            "Does not add a ratio constraint to any policy, does not modify the "
            "runtime, benchmark-lock, locked dataset, KPI, or manifest, and makes "
            "no wet-lab / cure / Tg performance claim. Remediation (an explicit "
            "mass.part_A_g/mass.part_B_g ratio constraint per envelope) requires a "
            "human Phase-0 fixture/lock revision this cron cannot perform."),
        "acceptance_bar_floors": {
            "g1_nominal_ratio_re_derivation_floor": 1.0,
            "g2_interval_corner_invariant_floor": 1.0,
            "g3_metrology_ordering_required": True,
            "g4_gap_demonstrated_all_envelopes": True,
            "g5_ratio_tamper_fail_closed_floor": 1.0,
            "all_met": all_pass,
        },
        "per_envelope": per_env,
    }
    return diag


if __name__ == "__main__":
    d = run()
    out = json.dumps(d, indent=2, sort_keys=True)
    import sys
    if len(sys.argv) > 1:
        Path(sys.argv[1]).write_text(out)
        print("WROTE", sys.argv[1], "sha256", sha(out.encode()))
    else:
        print(out)
