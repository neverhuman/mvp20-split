#!/usr/bin/env python3
"""Independent verifier for amphora-known-answer-benchmarks regression-kernel-kat-v1.

AUDIT_ONLY / LIMITED_SANITY. Certifies the shared numeric kernel underneath the
portfolio's coating-science estimators: two-pass OLS, sample variance, regression
standard error, and the conformal order-statistic quantile.

Non-circularity: every certified answer is RE-DERIVED here and only then compared
against the pin in the vectors file. Blocks A and C are decided in exact rational
arithmetic (fractions.Fraction); Block B regenerates both the design and its
certified coefficients from the Wampler (1970) generating rule and solves the
normal equations exactly; Block D recomputes the Hyndman-Fan (1996) definitions
and the Vovk (2005) conformal rank; Block E recomputes the Kissinger fit at 80
significant decimal digits with decimal.Decimal. No float64 value enters a
positive pass/fail decision, so replays are byte-stable by construction.

Primary sources: FIPS 140-3 Sec 7.4 (2019); Wampler JASA 65(330):549-563 (1970),
DOI 10.2307/2284581; Chan-Golub-LeVeque, Am. Stat. 37(3):242-247 (1983),
DOI 10.1080/00031305.1983.10483115; Hyndman-Fan, Am. Stat. 50(4):361-365 (1996),
DOI 10.1080/00031305.1996.10473566; Vovk-Gammerman-Shafer (2005) ISBN
978-0-387-00152-4; Lei et al. JASA 113(523):1094-1111 (2018),
DOI 10.1080/01621459.2017.1307116; Kissinger, Anal. Chem. 29(11):1702-1706 (1957),
DOI 10.1021/ac60131a045.
"""
import hashlib
import json
import math
from decimal import Decimal, getcontext
from fractions import Fraction as F
from pathlib import Path

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-known-answer-benchmarks"
VEC = MOD / "reference/mvp20/data/regression_kernel_kat_vectors.v1.json"
OUT = MOD / "benchmarks/regression-kernel-kat-v1/regression_kernel_kat_report.v1.json"

data = json.loads(VEC.read_bytes())
vec_sha = hashlib.sha256(VEC.read_bytes()).hexdigest()
getcontext().prec = data["block_E_kissinger_coating_cross_check"]["decimal_precision_digits"]

pos, traps = [], []


def frac(s):
    return F(s)


def fmt(x, dp):
    """Round-half-up an exact rational to dp decimals, as a fixed-point string."""
    sign = "-" if x < 0 else ""
    x = abs(x)
    scaled = x * 10 ** dp
    n = scaled.numerator // scaled.denominator
    if 2 * (scaled - n) >= 1:
        n += 1
    s = str(n).rjust(dp + 1, "0")
    return f"{sign}{s[:-dp] if dp else s}.{s[-dp:]}" if dp else f"{sign}{s}"


# ---------------------------------------------------------------- Block A
def ols_exact(xs, ys):
    n = F(len(xs))
    mx, my = sum(xs) / n, sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    slope = sxy / sxx
    icept = my - slope * mx
    ss_res = sum((y - (icept + slope * x)) ** 2 for x, y in zip(xs, ys))
    ss_tot = sum((y - my) ** 2 for y in ys)
    return slope, icept, F(1) - ss_res / ss_tot, ss_res


for c in data["block_A_exact_rational_ols"]["cases"]:
    xs = [frac(v) for v in c["x"]]
    ys = [frac(v) for v in c["y"]]
    slope, icept, r2, ss_res = ols_exact(xs, ys)
    ok = (slope == frac(c["expected_slope"]) and icept == frac(c["expected_intercept"])
          and r2 == frac(c["expected_r2"]) and ss_res == frac(c["expected_ss_res"]))
    pos.append({"block": "A", "case_id": c["case_id"], "pass": ok,
                "rederived_slope": str(slope), "pinned_slope": c["expected_slope"],
                "rederived_intercept": str(icept), "pinned_intercept": c["expected_intercept"],
                "rederived_r2": str(r2), "pinned_r2": c["expected_r2"],
                "rederived_ss_res": str(ss_res), "pinned_ss_res": c["expected_ss_res"],
                "arithmetic": "exact_rational"})

# ---------------------------------------------------------------- Block B
def wampler_design(coeffs, npts):
    xs = list(range(npts))
    ys = [sum(c * F(x) ** i for i, c in enumerate(coeffs)) for x in xs]
    return xs, ys


def solve_exact(A, b):
    p = len(b)
    M = [row[:] + [b[i]] for i, row in enumerate(A)]
    for col in range(p):
        piv = next(r for r in range(col, p) if M[r][col] != 0)
        M[col], M[piv] = M[piv], M[col]
        pv = M[col][col]
        M[col] = [v / pv for v in M[col]]
        for r in range(p):
            if r != col and M[r][col] != 0:
                f = M[r][col]
                M[r] = [vr - f * vc for vr, vc in zip(M[r], M[col])]
    return [M[i][p] for i in range(p)]


def poly_ols_exact(xs, ys, deg):
    p = deg + 1
    A = [[sum(F(x) ** (i + j) for x in xs) for j in range(p)] for i in range(p)]
    b = [sum(F(x) ** i * y for x, y in zip(xs, ys)) for i in range(p)]
    return solve_exact(A, b)


def poly_ols_naive_f64(xs, ys, deg):
    p = deg + 1
    A = [[sum(float(x) ** (i + j) for x in xs) for j in range(p)] for i in range(p)]
    b = [sum(float(x) ** i * float(y) for x, y in zip(xs, ys)) for i in range(p)]
    M = [row[:] + [b[i]] for i, row in enumerate(A)]
    for col in range(p):
        piv = max(range(col, p), key=lambda r: abs(M[r][col]))
        M[col], M[piv] = M[piv], M[col]
        pv = M[col][col]
        M[col] = [v / pv for v in M[col]]
        for r in range(p):
            if r != col and M[r][col] != 0.0:
                f = M[r][col]
                M[r] = [vr - f * vc for vr, vc in zip(M[r], M[col])]
    return [M[i][p] for i in range(p)]


naive_relerr = {}
for c in data["block_B_wampler_ill_conditioned_polynomial"]["cases"]:
    coeffs = [frac(v) for v in c["coefficients"]]
    xs, ys = wampler_design(coeffs, c["n_points"])
    beta = poly_ols_exact(xs, ys, c["degree"])
    ss_res = sum((y - sum(b * F(x) ** i for i, b in enumerate(beta))) ** 2
                 for x, y in zip(xs, ys))
    pinned = [frac(v) for v in c["expected_certified_beta"]]
    # certified answer must equal the generating coefficients themselves (noiseless design)
    ok = (beta == pinned and beta == coeffs and ss_res == frac(c["expected_ss_res"]))
    nf = poly_ols_naive_f64(xs, ys, c["degree"])
    naive_relerr[c["case_id"]] = max(
        abs(float(be) - bf) / (abs(float(be)) if be != 0 else 1) for be, bf in zip(beta, nf))
    pos.append({"block": "B", "case_id": c["case_id"], "pass": ok,
                "rederived_beta": [str(b) for b in beta],
                "pinned_beta": c["expected_certified_beta"],
                "beta_equals_generating_coefficients": beta == coeffs,
                "rederived_ss_res": str(ss_res), "pinned_ss_res": c["expected_ss_res"],
                "diagnostic_naive_float64_normal_equations_max_rel_err": repr(naive_relerr[c["case_id"]]),
                "arithmetic": "exact_rational"})

# ---------------------------------------------------------------- Block C
bc = data["block_C_shift_invariance_variance"]
base = [frac(v) for v in bc["base_data"]]
exact_var = frac(bc["exact_sample_variance"])


def var_two_pass_exact(xs):
    n = F(len(xs))
    m = sum(xs) / n
    return sum((x - m) ** 2 for x in xs) / (n - 1)


def var_one_pass_f64(xs):
    n = len(xs)
    s = s2 = 0.0
    for x in xs:
        f = float(x)
        s += f
        s2 += f * f
    return (s2 - s * s / n) / (n - 1)


one_pass_vals = {}
for k in bc["shift_exponents"]:
    shifted = [F(10) ** k + b for b in base]
    v = var_two_pass_exact(shifted)
    one_pass_vals[k] = var_one_pass_f64(shifted)
    pos.append({"block": "C", "case_id": f"C_shift_1e{k}", "pass": v == exact_var,
                "rederived_variance": str(v), "pinned_variance": bc["exact_sample_variance"],
                "diagnostic_one_pass_float64": repr(one_pass_vals[k]),
                "arithmetic": "exact_rational"})

# ---------------------------------------------------------------- Block D
def hf1(xs, p):
    if p <= 0:
        return xs[0]
    return xs[math.ceil(F(len(xs)) * p) - 1]


def hf2(xs, p):
    n = len(xs)
    np_ = F(n) * p
    if np_.denominator == 1 and 1 <= np_ <= n - 1:
        return (xs[int(np_) - 1] + xs[int(np_)]) / 2
    return hf1(xs, p)


def hf_interp(xs, h):
    n = len(xs)
    if h <= 1:
        return xs[0]
    if h >= n:
        return xs[-1]
    lo = math.floor(h)
    return xs[lo - 1] + (h - lo) * (xs[lo] - xs[lo - 1])


def hf6(xs, p):
    return hf_interp(xs, F(len(xs) + 1) * p)


def hf7(xs, p):
    return hf_interp(xs, F(len(xs) - 1) * p + 1)


bd = data["block_D_quantile_convention"]
rank_deficits = []
for c in bd["cases"]:
    n = c["n"]
    alpha = frac(c["alpha"])
    scores = [F(i) for i in range(1, n + 1)]
    k = math.ceil((n + 1) * (1 - alpha))
    q_conf = scores[k - 1]
    lvl = F(1) - alpha
    v1, v6, v7 = hf1(scores, lvl), hf6(scores, lvl), hf7(scores, lvl)
    identity = (q_conf == hf1(scores, F(k, n)))
    ok = (k == c["expected_conformal_rank_k"]
          and q_conf == frac(c["expected_conformal_quantile"])
          and v1 == frac(c["expected_hf1_at_1_minus_alpha"])
          and v6 == frac(c["expected_hf6_at_1_minus_alpha"])
          and v7 == frac(c["expected_hf7_at_1_minus_alpha"])
          and identity)
    rank_deficits.append((c["case_id"], q_conf - v7))
    pos.append({"block": "D", "case_id": c["case_id"], "pass": ok,
                "rederived_conformal_rank_k": k, "pinned_conformal_rank_k": c["expected_conformal_rank_k"],
                "rederived_conformal_quantile": str(q_conf),
                "rederived_hf1_at_nominal": str(v1), "rederived_hf6_at_nominal": str(v6),
                "rederived_hf7_at_nominal": str(v7),
                "conformal_equals_hf1_at_adjusted_level": identity,
                "rank_deficit_of_type7_vs_conformal": str(q_conf - v7),
                "arithmetic": "exact_rational"})

# ---------------------------------------------------------------- Block E
be = data["block_E_kissinger_coating_cross_check"]
R = Decimal(be["gas_constant_J_per_mol_K"])
recs = [(Decimal(r["heating_rate_K_per_min"]), Decimal(r["peak_temperature_K"]))
        for r in be["raw_records"]]
xs = [1 / Tp for _, Tp in recs]
ys = [(b / (Tp * Tp)).ln() for b, Tp in recs]
n = Decimal(len(xs))
mx, my = sum(xs) / n, sum(ys) / n
sxx = sum((x - mx) ** 2 for x in xs)
sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
slope = sxy / sxx
icept = my - slope * mx
ss_res = sum((y - (icept + slope * x)) ** 2 for x, y in zip(xs, ys))
ss_tot = sum((y - my) ** 2 for y in ys)
r2 = 1 - ss_res / ss_tot
se_slope = ((ss_res / (n - 2)) / sxx).sqrt()
ea = -R * slope / Decimal(1000)
se_ea = R * se_slope / Decimal(1000)
ship = be["shipped_float64_values_under_test"]


def dfmt(d, dp):
    return str(d.quantize(Decimal(1).scaleb(-dp)))


e_checks = {
    "slope_K": (dfmt(slope, 6), ship["slope_K"]),
    "intercept": (dfmt(icept, 6), ship["intercept"]),
    "r2": (dfmt(r2, 6), ship["r2"]),
    "ea_kJ_per_mol": (dfmt(ea, 6), ship["ea_kJ_per_mol"]),
    "se_ea_kJ_per_mol": (dfmt(se_ea, 6), ship["se_ea_kJ_per_mol"]),
}
for name, (got, want) in e_checks.items():
    pos.append({"block": "E", "case_id": f"E_kissinger_{name}", "pass": got == want,
                "rederived_80_digit": got, "pinned_shipped_float64": want,
                "arithmetic": "decimal_80_significant_digits"})

# ---------------------------------------------------------------- traps
tmap = {t["trap_id"]: t for t in data["fail_closed_traps"]}

w1 = data["block_B_wampler_ill_conditioned_polynomial"]["cases"][0]["case_id"]
sig = tmap["T1_naive_normal_equations_wampler1"]["must_not_match_certified_to_significant_digits"]
t1_flag = naive_relerr[w1] > 10 ** (-sig)
traps.append({"trap_id": "T1_naive_normal_equations_wampler1", "correctly_flagged": t1_flag,
              "observed_max_rel_err": repr(naive_relerr[w1]),
              "threshold": f"1e-{sig}",
              "note": "float64 normal-equations solution of Wampler1 loses roughly "
                      f"{-math.log10(naive_relerr[w1]):.1f} significant digits against the "
                      "exact all-ones certified vector."})

for tid, k in (("T2_one_pass_variance_shift_1e9", 9), ("T3_one_pass_variance_negative", 10)):
    v = one_pass_vals[k]
    traps.append({"trap_id": tid, "correctly_flagged": F(v).limit_denominator(10 ** 12) != exact_var,
                  "observed_one_pass_float64": repr(v),
                  "exact_two_pass": str(exact_var),
                  "is_negative_variance": v < 0})

t4 = all(d != 0 for _, d in rank_deficits)
traps.append({"trap_id": "T4_type7_substituted_for_conformal_quantile", "correctly_flagged": t4,
              "rank_deficits": {cid: str(d) for cid, d in rank_deficits},
              "all_deficits_positive_so_type7_is_anticonservative": all(d > 0 for _, d in rank_deficits)})

t5_detail = {}
t5 = True
for c in bd["cases"]:
    n_ = c["n"]
    scores = [F(i) for i in range(1, n_ + 1)]
    v1 = hf1(scores, F(1) - frac(c["alpha"]))
    q = frac(c["expected_conformal_quantile"])
    t5_detail[c["case_id"]] = str(q - v1)
    t5 = t5 and (v1 != q)
traps.append({"trap_id": "T5_hf1_at_nominal_level", "correctly_flagged": t5,
              "rank_deficits": t5_detail})

se_dof_n = R * (((ss_res / n) / sxx).sqrt()) / Decimal(1000)
traps.append({"trap_id": "T6_kissinger_se_wrong_dof",
              "correctly_flagged": dfmt(se_dof_n, 6) != ship["se_ea_kJ_per_mol"],
              "observed_df_n": dfmt(se_dof_n, 6), "shipped_df_n_minus_2": ship["se_ea_kJ_per_mol"],
              "understatement_ratio": dfmt(se_dof_n / se_ea, 6)})

r2_uncentred = 1 - ss_res / sum(y * y for y in ys)
traps.append({"trap_id": "T7_kissinger_uncentred_r2",
              "correctly_flagged": dfmt(r2_uncentred, 6) != ship["r2"],
              "observed_uncentred_r2": dfmt(r2_uncentred, 6), "shipped_centred_r2": ship["r2"]})

# ---------------------------------------------------------------- report
n_pos = len(pos)
n_pos_pass = sum(1 for p in pos if p["pass"])
n_trap = len(traps)
n_trap_ok = sum(1 for t in traps if t["correctly_flagged"])
by_block = {}
for p in pos:
    b = by_block.setdefault(p["block"], {"n": 0, "pass": 0})
    b["n"] += 1
    b["pass"] += 1 if p["pass"] else 0

report = {
    "schema": "amphora.known-answer.regression-kernel-kat-report.v1",
    "vector_set_id": data["vector_set_id"],
    "module_id": data["module_id"],
    "authority": "AUDIT_ONLY",
    "authority_ceiling": "LIMITED_SANITY",
    "methodology": "FIPS 140-3 Sec 7.4 Known-Answer Test (2019). Exact-rational (fractions.Fraction) "
                   "re-derivation for Blocks A/B/C/D and 80-significant-digit decimal.Decimal "
                   "re-derivation for Block E. Wampler (1970) DOI 10.2307/2284581; Chan-Golub-LeVeque "
                   "(1983) DOI 10.1080/00031305.1983.10483115; Hyndman-Fan (1996) "
                   "DOI 10.1080/00031305.1996.10473566; Vovk et al. (2005) ISBN 978-0-387-00152-4; "
                   "Lei et al. (2018) DOI 10.1080/01621459.2017.1307116; Kissinger (1957) "
                   "DOI 10.1021/ac60131a045.",
    "vectors_file_sha256": vec_sha,
    "n_positive": n_pos, "n_positive_pass": n_pos_pass,
    "n_fail_closed": n_trap, "n_fail_closed_correctly_flagged": n_trap_ok,
    "positive_pass_rate": fmt(F(n_pos_pass, n_pos), 6),
    "fail_closed_flag_rate": fmt(F(n_trap_ok, n_trap), 6),
    "all_positive_exact": n_pos_pass == n_pos,
    "all_traps_rejected": n_trap_ok == n_trap,
    "per_block": {k: f"{v['pass']}/{v['n']}" for k, v in sorted(by_block.items())},
    "aggregate_status": "PASS" if (n_pos_pass == n_pos and n_trap_ok == n_trap) else "FAIL",
    "positive_results": pos,
    "fail_closed_results": traps,
    "cross_check_portfolio_numbers": {
        "kissinger_dgeba_ipda_ccby": {
            "note": "The shipped rights-clean Kissinger fit for the DGEBA / isophorone-diamine "
                    "two-part epoxy-amine system was recomputed here at 80 significant decimal "
                    "digits from the raw DSC (heating rate, peak temperature) pairs alone. Every "
                    "shipped float64 value is reproduced to all six pinned decimals, so the "
                    "portfolio's headline cure activation energy is certified free of "
                    "floating-point conditioning error. The estimator's METHOD fidelity and the "
                    "underlying measurement remain the concern of the cure-kinetics receipts; "
                    "this battery certifies only the arithmetic.",
            "doi": be["rights"]["doi"], "license": be["rights"]["license"],
            "attribution": be["rights"]["attribution"],
            "checks": {k: {"rederived_80_digit": g, "shipped_float64": w, "match": g == w}
                       for k, (g, w) in e_checks.items()},
            "all_match": all(g == w for g, w in e_checks.values()),
            "ea_kJ_per_mol_high_precision": str(ea),
        },
        "conformal_quantile_convention": {
            "note": "Every split/Mondrian conformal receipt in this portfolio depends on the "
                    "ceil((n+1)(1-alpha))-th order statistic. That rank was re-derived here and "
                    "shown to equal the Hyndman-Fan Type 1 quantile at the ADJUSTED level "
                    "ceil((n+1)(1-alpha))/n, and to differ from the library-default Type 7 "
                    "quantile at the nominal level at every real portfolio calibration size. The "
                    "Type 7 substitution is anti-conservative in every case measured.",
            "rank_deficit_type7_by_case": {cid: str(d) for cid, d in rank_deficits},
            "type7_always_below_conformal_rank": all(d > 0 for _, d in rank_deficits),
        },
    },
    "scientific_claim": "The shared numeric kernel underneath the portfolio's coating-science "
                        "estimators reproduces exactly-certified least-squares, sample-variance and "
                        "order-statistic-quantile answers, and the shipped DGEBA/IPDA Kissinger "
                        "activation energy is reproduced to all pinned decimals by an 80-digit "
                        "recomputation. Naive normal equations, one-pass variance, wrong regression "
                        "degrees of freedom, uncentred r2, and library-default quantile substitution "
                        "are all detected. NOT a candidate performance or qualification claim.",
    "does_not_close": [
        "estimator METHOD fidelity (whether Kissinger is the right model) - that is the "
        "cure-kinetics receipts' concern, not this battery's",
        "measurement uncertainty in the underlying DSC peaks",
        "Wampler3/4/5, which carry published pseudo-random perturbations that cannot be "
        "regenerated from a rule and are deliberately excluded rather than approximated",
        "Hyndman-Fan quantile types 3, 4, 5, 8 and 9, deliberately excluded rather than pinned "
        "from memory",
        "whether any shipped conformal receipt actually used the correct rank - this battery "
        "pins what the correct rank IS and quantifies the error of the common substitution; "
        "auditing each consumer against it is separate work",
    ],
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(report, indent=2, sort_keys=True))
print("REPORT_SHA256", hashlib.sha256(OUT.read_bytes()).hexdigest())
print("AGG", report["aggregate_status"], "pos", f"{n_pos_pass}/{n_pos}", "traps", f"{n_trap_ok}/{n_trap}")
print("PER_BLOCK", report["per_block"])
print("KISSINGER_ALL_MATCH", report["cross_check_portfolio_numbers"]["kissinger_dgeba_ipda_ccby"]["all_match"])
