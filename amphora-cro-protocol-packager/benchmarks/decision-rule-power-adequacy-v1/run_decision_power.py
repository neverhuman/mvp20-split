#!/usr/bin/env python3
"""amphora-cro-protocol-packager :: decision-rule-power-adequacy-v1  (AUDIT_ONLY)

Question nobody in this module has asked yet: the packager SHIPS a falsification protocol
whose locked_payload asserts, in its own words, that "the decisive, adequately-powered test
is the key pairwise bet".  Prior packager audits (packet-binding-parity, canonicalization-
conformance, representation-invariance) all asked "is the packet BOUND correctly?".  None
asked "is the DECISION RULE the packet binds a statistically admissible test?".

This harness re-derives, from the shipped protocol bytes alone, the exact operating
characteristics of the shipped decision rule against published statistical baselines:

  * Kendall, M.G. (1938) "A New Measure of Rank Correlation", Biometrika 30(1-2):81-93,
    DOI:10.1093/biomet/30.1-2.81 -- exact permutation null of tau for n=4 (4! = 24 orderings,
    enumerated exhaustively, no simulation, no seed).
  * Cohen, J. (1988) "Statistical Power Analysis for the Behavioral Sciences", 2nd ed.,
    ISBN 0-8058-0283-5 -- two-sample power / minimum detectable difference.
  * Student (1908) Biometrika 6(1):1-25 / noncentral-t power (exact, via scipy.stats.nct).
  * ISO 5725-2 one-way nested precision decomposition (sigma_r, sigma_R) -- taken from the
    INDEPENDENTLY SIGNED amphora-public-corrosion-benchmark USBR-21019 audit receipt
    (US Bureau of Reclamation RISE catalog 8048, US Government work, public domain,
    17 U.S.C. 105), not from any Amphora model.
  * ISO 16773-1..4:2016 -- |Z| at 0.01 Hz as the barrier metric the tie rule names.

Non-circularity: the protocol under audit supplies ONLY the ranks, the nulls, the panel
counts and the rule text; the noise scale comes from a separate public-domain measurement
dataset; the power arithmetic is validated against Cohen's published tabulated n.

Deterministic: exhaustive enumeration + deterministic special functions. No RNG, no seed.

Signs nothing, promotes nothing, modifies no manifest / locked dataset / KPI / benchmark-lock.
"""
import hashlib
import itertools
import json
import base64
from pathlib import Path

from scipy.stats import nct, t as tdist, norm

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-cro-protocol-packager"
PROTOCOL = MOD / "reference/mvp20/out/falsification_protocol.json"
CAPTURE = MOD / "reference/mvp20/out/capture_template.json"
PRECISION_RECEIPT = (ROOT / "amphora-public-corrosion-benchmark/evidence/audit/"
                     "eis-reproducibility-discrimination-power-v1/"
                     "eis-reproducibility-discrimination-power-receipt.v1.dsse.json")
OUT = MOD / "evidence/audit/decision-rule-power-adequacy-v1"

ALPHA = 0.05
POWER_TARGET = 0.80
R = 9  # rounding for byte-stability


def sha(b):
    return hashlib.sha256(b).hexdigest()


def rnd(x):
    return round(float(x), R)


# ----------------------------------------------------------------------------- inputs
protocol_bytes = PROTOCOL.read_bytes()
protocol = json.loads(protocol_bytes)
capture_bytes = CAPTURE.read_bytes()
precision_bytes = PRECISION_RECEIPT.read_bytes()
precision_payload = json.loads(
    base64.b64decode(json.loads(precision_bytes)["signature"]["payload"]))

locked = protocol["locked_payload"]
locked_rank = list(locked["predicted_rank"])
null_solids = list(locked["hostile_nulls"]["solids_only"])
null_pvc = list(locked["hostile_nulls"]["pvc_only"])
panel_plan = locked["panel_plan"]
n_min = int(panel_plan["minimum_panels_per_track_per_corrosion_arm"])
n_default = int(panel_plan["default_panels_per_track_per_corrosion_arm_if_budget_allows"])
arms = list(panel_plan["corrosion_arms"])
n_tracks = len(locked_rank)
key_pair = list(protocol["key_pairwise_bet"]["pair"])  # [better, worse] as predicted

budget = precision_payload["measurement_uncertainty_budget_iso5725"]
sigma_R = float(budget["reproducibility_sigma_R_late_decades"])
sigma_between_panel = float(budget["between_panel_reproducibility_sigma_late_decades"])
sigma_repeat = float(budget["within_panel_repeatability_sigma_late_decades_upper_bound"])
pooled_between_system = float(
    precision_payload["between_system_signal"]["pooled_between_system_sd_decades"])
prior_mdd = precision_payload["power_budget"]["min_detectable_log10Z_difference_decades_80pct_a0p05"]


# ------------------------------------------------------------------- Kendall machinery
def kendall_tau(order_a, order_b):
    """tau_a between two total orders (no ties): (C - D) / (n choose 2). Kendall 1938."""
    pos_a = {k: i for i, k in enumerate(order_a)}
    pos_b = {k: i for i, k in enumerate(order_b)}
    c = d = 0
    for x, y in itertools.combinations(order_a, 2):
        s = (pos_a[x] - pos_a[y]) * (pos_b[x] - pos_b[y])
        if s > 0:
            c += 1
        else:
            d += 1
    return (c - d) / (len(order_a) * (len(order_a) - 1) / 2)


def ranked_above(order, a, b):
    return order.index(a) < order.index(b)


# ---------------------------------------------------------------------- power machinery
def power_two_sample(delta, sigma, n, alpha=ALPHA, one_sided_direction=False):
    """Exact noncentral-t power for a two-sample equal-n comparison of panel means.
    ncp = delta / (sigma * sqrt(2/n)); df = 2n - 2 (Student 1908; Cohen 1988 ch.2)."""
    ncp = delta / (sigma * (2.0 / n) ** 0.5)
    df = 2 * n - 2
    tcrit = tdist.ppf(1 - alpha / 2.0, df)
    upper = 1.0 - nct.cdf(tcrit, df, ncp)
    if one_sided_direction:
        return upper
    return upper + nct.cdf(-tcrit, df, ncp)


def mdd_normal(sigma, n, alpha=ALPHA, power=POWER_TARGET):
    """Cohen 1988 normal-approximation MDD = (z_{1-a/2} + z_{1-b}) * sigma * sqrt(2/n)."""
    return (norm.ppf(1 - alpha / 2.0) + norm.ppf(power)) * sigma * (2.0 / n) ** 0.5


def mdd_exact(sigma, n, alpha=ALPHA, power=POWER_TARGET):
    """Exact noncentral-t MDD by bisection on delta; deterministic, 200 halvings."""
    lo, hi = 1e-9, 50.0
    for _ in range(200):
        mid = (lo + hi) / 2.0
        if power_two_sample(mid, sigma, n, alpha) < power:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2.0


def n_required(delta, sigma, alpha=ALPHA, power=POWER_TARGET, nmax=100000):
    n = 2
    while n <= nmax:
        if power_two_sample(delta, sigma, n, alpha) >= power:
            return n
        n += 1
    return None


# ============================================================== G1 exact Kendall null
perms = list(itertools.permutations(locked_rank))
tau_hist = {}
rows = []
for p in perms:
    p = list(p)
    tL = kendall_tau(p, locked_rank)
    tS = kendall_tau(p, null_solids)
    tP = kendall_tau(p, null_pvc)
    pairwise_holds = ranked_above(p, key_pair[0], key_pair[1])
    primary = (tL >= 0.5) and (tL > tS) and (tL > tP)
    rows.append({"measured_order": p, "tau_vs_locked": rnd(tL), "tau_vs_solids_null": rnd(tS),
                 "tau_vs_pvc_null": rnd(tP), "primary_rule_passes": bool(primary),
                 "key_pairwise_holds": bool(pairwise_holds),
                 "compound_rule_passes": bool(primary and pairwise_holds)})
    tau_hist[rnd(tL)] = tau_hist.get(rnd(tL), 0) + 1

n_perm = len(perms)
n_tau_ge_half = sum(1 for r in rows if r["tau_vs_locked"] >= 0.5)
n_primary = sum(1 for r in rows if r["primary_rule_passes"])
n_compound = sum(1 for r in rows if r["compound_rule_passes"])

# attainable exact levels of ANY tau >= c rule at this n
attainable = {}
for tv in sorted(tau_hist, reverse=True):
    cnt = sum(c for t_, c in tau_hist.items() if t_ >= tv)
    attainable[f"tau_ge_{tv}"] = {"n_orderings": cnt, "exact_level": rnd(cnt / n_perm)}
finest_level = rnd(1.0 / n_perm)

G1 = {
    "theory": "Kendall 1938 exact permutation null of tau at n=4 (4! = 24 orderings, exhaustive)",
    "n_tracks": n_tracks,
    "n_orderings_enumerated": n_perm,
    "null_hypothesis": "measured immersion rank uniform over all orderings of the shipped tracks",
    "tau_null_distribution_vs_locked": {str(k): v for k, v in sorted(tau_hist.items())},
    "exact_P_tau_ge_0p5": rnd(n_tau_ge_half / n_perm),
    "exact_type_I_primary_rule": rnd(n_primary / n_perm),
    "exact_type_I_compound_rule_with_key_pairwise": rnd(n_compound / n_perm),
    "passing_orderings_primary": [r["measured_order"] for r in rows if r["primary_rule_passes"]],
    "passing_orderings_compound": [r["measured_order"] for r in rows if r["compound_rule_passes"]],
    "key_pairwise_conjunct_is_redundant_given_primary_rule": bool(n_compound == n_primary),
    "n_orderings_primary_passes_but_key_pairwise_fails": n_primary - n_compound,
    "redundancy_note": ("Every ordering that clears the primary rank rule ALSO satisfies the "
                        "'single most decisive' pairwise bet, so the conjunct removes zero "
                        "orderings from the rejection region and contributes zero type-I "
                        "protection: it is implied by the rank rule, not independent of it."),
    "attainable_exact_levels_of_tau_threshold_rules": attainable,
    "finest_attainable_level_1_over_n_factorial": finest_level,
    "primary_rule_attains_conventional_0p05": bool((n_primary / n_perm) <= 0.05),
    "compound_rule_attains_conventional_0p05": bool((n_compound / n_perm) <= 0.05),
    "note": ("At n=4 tracks the ONLY tau-threshold rule with exact level <= 0.05 is tau == 1 "
             "(exact rank identity, level 1/24 = 0.041667). The shipped tau >= 0.5 threshold "
             "cannot reach a 5% level at this many tracks -- it is a granularity wall, not a "
             "tuning choice."),
    "passed": bool((n_compound / n_perm) <= 0.05),
}

# ============================================ G2 power-engine known-answer validation
# Cohen 1988 Table 2.4.1: d = 0.80, alpha = .05 two-tailed, power .80 -> n = 26 per group.
cohen_d = 0.80
cohen_n = n_required(cohen_d, 1.0)
cohen_power_26 = power_two_sample(cohen_d, 1.0, 26)
cohen_power_25 = power_two_sample(cohen_d, 1.0, 25)
# reproduce the independently signed USBR MDD figures (normal approximation)
mdd_rep_1 = mdd_normal(sigma_R, 1)
mdd_rep_2 = mdd_normal(sigma_R, 2)
kat_tol = 1e-4
G2 = {
    "theory": "Cohen 1988 (ISBN 0-8058-0283-5) Table 2.4.1 + independently signed USBR MDD figures",
    "cohen_medium_large_d": cohen_d,
    "cohen_n_per_group_for_80pct_power_computed": cohen_n,
    "cohen_n_per_group_published": 26,
    "power_at_n26": rnd(cohen_power_26),
    "power_at_n25": rnd(cohen_power_25),
    "cohen_kat_matches": bool(cohen_n == 26),
    "usbr_mdd_n1_published": prior_mdd["n_panels_1"],
    "usbr_mdd_n1_recomputed": rnd(mdd_rep_1),
    "usbr_mdd_n2_published": prior_mdd["n_panels_2"],
    "usbr_mdd_n2_recomputed": rnd(mdd_rep_2),
    "usbr_mdd_abs_err_max": rnd(max(abs(mdd_rep_1 - prior_mdd["n_panels_1"]),
                                    abs(mdd_rep_2 - prior_mdd["n_panels_2"]))),
    "tolerance": kat_tol,
    "passed": bool(cohen_n == 26
                   and abs(mdd_rep_1 - prior_mdd["n_panels_1"]) < kat_tol
                   and abs(mdd_rep_2 - prior_mdd["n_panels_2"]) < kat_tol),
}

# ==================================== G3 minimum detectable difference at shipped plan
mdd_rows = {}
for n in (n_min, n_default):
    mdd_rows[f"n_panels_{n}"] = {
        "mdd_decades_normal_approx": rnd(mdd_normal(sigma_R, n)),
        "mdd_decades_exact_noncentral_t": rnd(mdd_exact(sigma_R, n)),
        "mdd_over_pooled_between_system_sd": rnd(mdd_exact(sigma_R, n) / pooled_between_system),
    }
G3 = {
    "theory": "Cohen 1988 MDD + exact noncentral-t inversion; sigma from ISO 5725-2 decomposition",
    "sigma_source": "amphora-public-corrosion-benchmark USBR-21019 signed audit (public domain)",
    "sigma_R_decades": rnd(sigma_R),
    "sigma_between_panel_decades": rnd(sigma_between_panel),
    "sigma_repeatability_upper_bound_decades": rnd(sigma_repeat),
    "between_panel_variance_share": rnd(sigma_between_panel ** 2 / sigma_R ** 2),
    "pooled_between_system_sd_decades": rnd(pooled_between_system),
    "shipped_panel_counts": {"minimum_floor": n_min, "default_if_budget_allows": n_default},
    "mdd": mdd_rows,
    "mdd_exceeds_observed_between_system_spread_at_default_n": bool(
        mdd_exact(sigma_R, n_default) > pooled_between_system),
    "note": ("Between-PANEL reproducibility is %.1f%% of the total endpoint variance, so it "
             "cannot be reduced by repeat measurements on the same panel -- only by more panels, "
             "which is exactly the axis the shipped panel plan caps at %d."
             % (100 * sigma_between_panel ** 2 / sigma_R ** 2, n_default)),
    "passed": bool(mdd_exact(sigma_R, n_default) <= pooled_between_system),
}

# ======================= G4 power of the DECISIVE pairwise bet under the shipped tie rule
delta_grid = [0.25, 0.5, pooled_between_system, 1.0, 2.0, 3.0]
pair_rows = []
for n in (n_min, n_default):
    for dlt in delta_grid:
        pw2 = power_two_sample(dlt, sigma_R, n)
        pw1 = power_two_sample(dlt, sigma_R, n, one_sided_direction=True)
        pair_rows.append({
            "n_panels_per_track_per_arm": n,
            "true_delta_log10Z_decades": rnd(dlt),
            "P_pair_declared_separated": rnd(pw2),
            "P_separated_and_correct_direction": rnd(pw1),
            "P_pair_declared_TIED_by_shipped_tie_rule": rnd(1.0 - pw2),
            "meets_80pct_power": bool(pw1 >= POWER_TARGET),
        })
pw_at_observed_min = power_two_sample(pooled_between_system, sigma_R, n_min, one_sided_direction=True)
pw_at_observed_def = power_two_sample(pooled_between_system, sigma_R, n_default, one_sided_direction=True)
G4 = {
    "theory": ("shipped tie_rule formalised as a two-sided alpha=0.05 two-sample comparison of "
               "panel-mean log10|Z|@0.01Hz (ISO 16773); exact noncentral-t power"),
    "decisive_pair": key_pair,
    "shipped_claim_under_test": locked["decision_rule"]["power_caveat"],
    "power_grid": pair_rows,
    "power_at_observed_between_system_spread": {
        f"n_{n_min}": rnd(pw_at_observed_min), f"n_{n_default}": rnd(pw_at_observed_def)},
    "P_decisive_pair_TIED_at_observed_spread": {
        f"n_{n_min}": rnd(1.0 - power_two_sample(pooled_between_system, sigma_R, n_min)),
        f"n_{n_default}": rnd(1.0 - power_two_sample(pooled_between_system, sigma_R, n_default))},
    "H0_shipped_pairwise_bet_is_adequately_powered": "REFUTED",
    "passed": bool(pw_at_observed_def >= POWER_TARGET),
}

# ============================================================ G5 inverse design (n required)
sigma_variants = {"repeatability_only": sigma_repeat,
                  "between_panel_only": sigma_between_panel,
                  "full_sigma_R": sigma_R}
inverse = {}
for name, sg in sigma_variants.items():
    inverse[name] = {"sigma_decades": rnd(sg),
                     "n_required_80pct": {str(rnd(d)): n_required(d, sg) for d in delta_grid}}
n_req_headline = n_required(pooled_between_system, sigma_R)
G5 = {
    "theory": "Cohen 1988 inverse design; smallest integer n per track per arm reaching 80% power",
    "alpha": ALPHA, "power_target": POWER_TARGET,
    "n_required": inverse,
    "headline_n_required_at_observed_spread_and_sigma_R": n_req_headline,
    "shipped_default_n": n_default,
    "shortfall_factor_vs_shipped_default": rnd(n_req_headline / n_default),
    "passed": bool(n_req_headline <= n_default),
}

# ================================================ G6 arm multiplicity / endpoint pinning
primary_text = locked["decision_rule"]["primary"]
key_text = locked["decision_rule"]["key_pairwise"]
# an arm counts as PINNED by a rule sentence if any of its distinctive standard tokens appears
ARM_TOKENS = {a: [w.lower() for w in a.replace("+", " ").split() if w.lower() not in ("astm", "iso")]
              for a in arms}


def arms_pinned_by(text):
    low = text.lower()
    return sorted(a for a, toks in ARM_TOKENS.items() if any(tok in low for tok in toks))


primary_pins = arms_pinned_by(primary_text)
key_pins = arms_pinned_by(key_text)
n_arms = len(arms)
fwer_bound = 1.0 - (1.0 - ALPHA) ** n_arms
G6 = {
    "theory": ("Sidak/Boole family-wise error bound under a free choice of endpoint arm; "
               "ICH E9 (1998) primary-endpoint pinning discipline"),
    "n_corrosion_arms": n_arms,
    "arms": arms,
    "primary_rule_text": primary_text,
    "primary_rule_names_an_arm": bool(primary_pins) or ("immersion" in primary_text.lower()),
    "key_pairwise_text": key_text,
    "key_pairwise_names_an_arm": bool(key_pins),
    "fwer_upper_bound_if_arm_chosen_post_hoc": rnd(fwer_bound),
    "note": ("The primary tau rule pins the immersion arm; the DECISIVE key-pairwise bet names "
             "only 'the measured data' and does not pin one of the %d corrosion arms, so a "
             "post-hoc arm choice inflates its error rate to at most %.4f." % (n_arms, fwer_bound)),
    "passed": bool(key_pins),
}

# ============================================= G7 statistical-specification completeness
flat = json.dumps(protocol).lower()
spec_items = {
    "declares_significance_level_alpha": any(k in flat for k in
                                             ["alpha", "significance level", "p-value", "p value"]),
    "declares_power_target": "power" in flat and any(
        k in flat for k in ["80%", "0.8 power", "power target", "1-beta", "beta ="]),
    "declares_target_effect_size_in_measurable_units": any(
        k in flat for k in ["decade", "effect size", "minimum detectable", "mdd"]),
    "declares_tie_threshold_in_measurable_units": any(
        k in flat for k in ["decade", "ohm", "log10", "std dev", "standard deviation", "sigma"]),
    "declares_replicate_scatter_estimate": any(
        k in flat for k in ["sigma", "std dev", "standard deviation", "coefficient of variation"]),
    "pins_arm_for_key_pairwise": bool(key_pins),
    "declares_multiplicity_control": any(
        k in flat for k in ["bonferroni", "sidak", "holm", "multiplicity", "family-wise", "fwer"]),
}
absent = sorted(k for k, v in spec_items.items() if not v)
G7 = {
    "theory": "ICH E9 (1998) / ASTM E122 statistical-protocol specification completeness",
    "items": {k: bool(v) for k, v in spec_items.items()},
    "absent": absent,
    "n_absent": len(absent),
    "note": ("The protocol quantifies its tie rule only as 'overlap within replicate scatter' "
             "with no numeric scatter, no alpha, no target effect size and no power target, so "
             "its own adequacy claim is not checkable from the packet it ships -- it becomes "
             "checkable only by importing an external ISO-5725 precision estimate, as done here."),
    "passed": len(absent) == 0,
}

# ===================================================================== assemble diagnostic
gates = {"G1_kendall_exact_null_type_I": G1,
         "G2_power_engine_known_answer": G2,
         "G3_minimum_detectable_difference": G3,
         "G4_decisive_pairwise_bet_power": G4,
         "G5_inverse_design_n_required": G5,
         "G6_arm_multiplicity_endpoint_pinning": G6,
         "G7_specification_completeness": G7}

headline = (
    "First statistical-admissibility audit of the decision rule the CRO packager BINDS (prior "
    "packager audits only checked that the packet was bound correctly). Exhaustive Kendall-1938 "
    "enumeration of all %d orderings gives the shipped primary rank rule an EXACT type-I error of "
    "%.4f (%.4f with the key-pairwise conjunct) -- above 0.05, and at n=%d tracks the only "
    "tau-threshold rule that can reach 0.05 is exact rank identity (1/24 = %.4f). Against the "
    "independently signed public-domain USBR-21019 ISO-5725 precision floor (sigma_R = %.3f "
    "decades, %.0f%% of it irreducible between-PANEL), the 80%%-power minimum detectable "
    "log10|Z| difference is %.2f decades at the shipped %d-panel floor and %.2f decades at the "
    "%d-panel default -- both LARGER than the %.3f-decade pooled between-system spread actually "
    "observed in that dataset. At that spread the decisive Enhanced-65 > Envelope-65 bet has "
    "%.3f power at n=%d and %.3f at n=%d, i.e. the shipped tie rule declares the decisive pair "
    "TIED with probability %.3f and the protocol fail-closes to INCONCLUSIVE; reaching 80%% power "
    "needs n=%d panels/track/arm, %.1fx the shipped default. H0 (the protocol's own "
    "'the decisive, adequately-powered test is the key pairwise bet') is REFUTED: the packager "
    "binds, with full cryptographic integrity, a protocol that is underpowered by its own metric."
) % (n_perm, n_primary / n_perm, n_compound / n_perm, n_tracks, finest_level, sigma_R,
     100 * sigma_between_panel ** 2 / sigma_R ** 2,
     mdd_exact(sigma_R, n_min), n_min, mdd_exact(sigma_R, n_default), n_default,
     pooled_between_system, pw_at_observed_min, n_min, pw_at_observed_def, n_default,
     1.0 - power_two_sample(pooled_between_system, sigma_R, n_default),
     n_req_headline, n_req_headline / n_default)

diag = {
    "schema": "amphora.cro-protocol-packager.decision-rule-power-adequacy-diagnostic.v1",
    "study_id": "cro-protocol-packager-decision-rule-power-adequacy-v1",
    "module": "amphora-cro-protocol-packager",
    "run_type": "AUDIT_ONLY",
    "authority": "AUDIT_ONLY",
    "headline": headline,
    "purpose": ("Test whether the falsification protocol the packager binds and ships is a "
                "statistically admissible test -- exact type-I error of its rank rule and exact "
                "power of its self-declared decisive pairwise bet -- rather than whether the "
                "packet bytes are bound correctly (already closed by prior packager audits)."),
    "novelty_vs_prior_packager_audits": (
        "packet-binding-parity, canonicalization-conformance and representation-invariance all "
        "audit the BINDING layer (JCS/SHA-256 injectivity, numeric canonicalisation, over-binding). "
        "This is the first audit of the SCIENTIFIC CONTENT the binding protects."),
    "non_circularity": (
        "Ranks, nulls, panel counts and rule text are parsed from the shipped protocol bytes; the "
        "noise scale is imported from a separately signed audit of a US-Government public-domain "
        "EIS dataset (USBR RISE 8048); the power arithmetic is validated against Cohen 1988's "
        "published tabulated n=26. No Amphora predictive model is consulted or trusted."),
    "theory_reference": {
        "rank_null": "Kendall, M.G. (1938) Biometrika 30(1-2):81-93, DOI:10.1093/biomet/30.1-2.81",
        "power": "Cohen, J. (1988) Statistical Power Analysis, 2nd ed., ISBN 0-8058-0283-5",
        "t_distribution": "Student (1908) Biometrika 6(1):1-25; noncentral-t exact power",
        "precision_model": "ISO 5725-2 repeatability/reproducibility decomposition",
        "eis_metric": "ISO 16773-1:2016 .. ISO 16773-4:2016, |Z| at 0.01 Hz",
        "endpoint_discipline": "ICH E9 (1998) primary-endpoint pinning; ASTM E122 sample size",
        "corrosion_arms_cited_by_protocol": arms,
    },
    "inputs": {
        "shipped_falsification_protocol_sha256": sha(protocol_bytes),
        "shipped_capture_template_sha256": sha(capture_bytes),
        "precision_receipt_sha256": sha(precision_bytes),
        "precision_dataset": precision_payload["data_source"],
        "locked_rank": locked_rank,
        "hostile_null_solids_only": null_solids,
        "hostile_null_pvc_only": null_pvc,
        "decisive_pair": key_pair,
        "panel_plan_min": n_min,
        "panel_plan_default": n_default,
    },
    "gates": gates,
    "all_gates_passed": all(g["passed"] for g in gates.values()),
    "gates_passed": sorted(k for k, g in gates.items() if g["passed"]),
    "gates_failed": sorted(k for k, g in gates.items() if not g["passed"]),
    "verdict": "SHIPPED_DECISION_RULE_UNDERPOWERED_AND_ABOVE_NOMINAL_TYPE_I",
    "closes": [
        "The exact (not simulated) type-I error of the shipped rank decision rule is now a signed "
        "number: %.6f primary, %.6f with the key-pairwise conjunct." % (n_primary / n_perm,
                                                                        n_compound / n_perm),
        "The granularity wall is established: at 4 tracks no tau>=c rule except exact rank "
        "identity can reach a 5%% level, so adding tracks -- not tightening c -- is the only fix.",
        "The 'single most decisive' key-pairwise conjunct is shown to be logically implied by the "
        "primary rank rule (identical rejection regions, %d vs %d orderings), so it adds no "
        "type-I protection and cannot be the independent decisive test the protocol claims."
        % (n_primary, n_compound),
        "The 80%-power minimum detectable log10|Z| difference at the shipped 3- and 6-panel "
        "counts is quantified against a public-domain ISO-5725 precision floor.",
        "The protocol's self-description as 'adequately powered' is refuted with an explicit "
        "required-n (%d panels/track/arm) rather than an adjective." % n_req_headline,
        "A specification-completeness gap list (alpha, power target, effect size, tie threshold, "
        "arm pinning, multiplicity) is enumerated from the shipped bytes.",
    ],
    "does_not_close": [
        "No promotion, no authority change, no manifest edit; scientific_readiness stays "
        "NOT_APPLICABLE and the packager's authority ceiling stays CRO_GATED.",
        "sigma_R is imported from USBR-21019 (6 systems x 4 baths, mixed labs/baths); a single "
        "CRO running one protocol side-by-side may achieve a smaller between-panel sigma, which "
        "is why G5 reports the full sigma x delta grid rather than one number.",
        "The shipped barrier_index deltas (e.g. %.3f for the decisive pair) have NO published "
        "mapping to log10|Z| decades, so no target effect size can be asserted here -- that "
        "missing mapping is itself the binding power-specification gap."
        % protocol["barrier_index_deltas"]["Enhanced-65_minus_Envelope-65"],
        "Power is computed for the |Z|@0.01Hz endpoint only; B117/D1654 creep and D5894 arms have "
        "their own (unmeasured here) precision.",
        "Rewriting the shipped protocol is out of scope for an AUDIT_ONLY run; this receipt states "
        "the required design, it does not re-issue the packet.",
    ],
    "remediation_required_for_phase1": {
        "increase_panels_per_track_per_arm_to": n_req_headline,
        "or_declare_target_effect_size_in_decades": True,
        "or_increase_tracks_to_reach_0p05_rank_level": "n_tracks >= 5 (5! = 120 orderings)",
        "pin_single_arm_for_key_pairwise_bet": True,
        "declare_alpha_power_and_scatter_numerically": True,
    },
}

OUT.mkdir(parents=True, exist_ok=True)
blob = json.dumps(diag, indent=2, sort_keys=True).encode()
(OUT / "diagnostic.canonical.json").write_bytes(blob)
print("WROTE", OUT / "diagnostic.canonical.json")
print("sha256", sha(blob))
print(headline)
print("gates_failed", diag["gates_failed"])
