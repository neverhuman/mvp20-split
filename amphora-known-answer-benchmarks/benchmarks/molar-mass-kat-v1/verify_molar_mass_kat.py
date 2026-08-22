"""Independent exact-rational verifier for the standard-atomic-weight / molar-mass
Known-Answer Test battery.

Re-derives every pinned molar mass and equivalent weight in
molar_mass_kat_vectors.v1.json from the EXACT rational IUPAC 2021 conventional /
abridged standard atomic weights (IUPAC CIAAW 2021; Meija et al., Pure Appl. Chem.
2016, 88(3):265-291, DOI 10.1515/pac-2015-0305, as updated 2021), using
fractions.Fraction only -- no floating-point arithmetic enters the pass/fail gate,
so the report is byte-stable across replays by construction.

An atomic-weight identity ("exact" mode) vector PASSES iff the raw pinned atomic
weight in this verifier's exact-rational table equals the pinned IUPAC published
value (typo/regression guard). A derived molar-mass / equivalent-weight vector
PASSES iff round_half_up(exact_rational_sum, decimals) equals the pinned expected,
where the sum uses ONLY the pinned atomic weights and integer atom counts (and an
integer functionality divisor for equivalent weights), never a published molar
mass -> non-circular. A fail-closed hostile vector PASSES iff its wrong value does
NOT equal the exact-rounded correct answer re-derived from the real atomic weights.

AUDIT_ONLY. Limited-sanity known-answer evidence. No candidate-performance claim.
Primary methodology: FIPS 140-3 Sec 7.4 Known-Answer Test (2019); IUPAC CIAAW 2021.
"""
import sys, json, hashlib, re
from fractions import Fraction as F
from pathlib import Path

VEC = Path(sys.argv[1])
OUT = Path(sys.argv[2])

# ---- exact rational IUPAC 2021 standard atomic weights (g/mol) ----------------
AW = {
    "H":  F(1008, 1000),    # 1.008  (conventional)
    "C":  F(12011, 1000),   # 12.011 (conventional)
    "N":  F(14007, 1000),   # 14.007 (conventional)
    "O":  F(15999, 1000),   # 15.999 (conventional)
    "Cl": F(3545, 100),     # 35.45  (conventional)
    "S":  F(3206, 100),     # 32.06  (conventional)
    "Zn": F(6538, 100),     # 65.38  (abridged)
    "Ti": F(47867, 1000),   # 47.867 (abridged)
}


def PF(s):
    """Exact Fraction from a decimal/scientific string (no float)."""
    s = str(s).strip()
    if "e" in s or "E" in s:
        m, exp = re.split("[eE]", s); exp = int(exp)
    else:
        m, exp = s, 0
    neg = m.startswith("-")
    if neg: m = m[1:]
    if "." in m:
        whole, frac = m.split("."); digits = whole + frac; scale = len(frac)
    else:
        digits, scale = m, 0
    val = F(int(digits or "0"), 10**scale)
    val = val * 10**exp if exp >= 0 else val / 10**(-exp)
    return -val if neg else val


def round_half_up(frac, d):
    scale = 10**d
    n = frac * scale
    floor = n.numerator // n.denominator
    if n - floor >= F(1, 2):
        floor += 1
    return F(floor, scale)


def fmt(frac, d):
    scale = 10**d
    n = frac * scale
    floor = n.numerator // n.denominator
    if n - floor >= F(1, 2):
        floor += 1
    sign = "-" if floor < 0 else ""
    floor = abs(floor)
    if d == 0:
        return f"{sign}{floor}"
    whole, frac_part = divmod(floor, scale)
    return f"{sign}{whole}.{str(frac_part).zfill(d)}"


def molar_mass(formula):
    """Exact rational molar mass from the pinned atomic-weight table."""
    tot = F(0)
    for el, n in formula.items():
        tot += AW[el] * int(n)
    return tot


data = json.loads(VEC.read_text())
vec_sha = hashlib.sha256(VEC.read_bytes()).hexdigest()

pos_results, n_pos_pass = [], 0
for v in data["positive_vectors"]:
    vid = v["id"]
    if v["mode"] == "exact":                      # atomic-weight identity
        derived = AW[v["element"]]
        expected = PF(v["expected"])
        ok = derived == expected
        derived_str = v["expected"] if ok else f"{derived.numerator}/{derived.denominator}"
        pinned_str = str(v["expected"])
    else:                                          # derived molar mass / equiv weight
        d = v["decimals"]
        divisor = int(v.get("divisor", 1))
        derived = molar_mass(v["formula"]) / divisor
        expected = PF(str(v["expected"]))
        ok = round_half_up(derived, d) == expected
        derived_str = fmt(derived, d)
        pinned_str = fmt(expected, d)
    n_pos_pass += ok
    pos_results.append({
        "id": vid, "quantity": v.get("name", v.get("element")), "unit": v["unit"],
        "mode": v["mode"], "pinned_expected": pinned_str,
        "independently_derived": derived_str,
        "exact_rational": f"{derived.numerator}/{derived.denominator}",
        "match": bool(ok),
    })

trap_results, n_trap_pass = [], 0
for h in data["fail_closed_hostile_vectors"]:
    hid = h["id"]
    d = h["decimals"]
    divisor = int(h.get("correct_divisor", 1))
    correct = molar_mass(h["formula"]) / divisor      # re-derived from REAL atomic weights, correct functionality
    wrong = PF(str(h["wrong_value"]))
    flagged = round_half_up(wrong, d) != round_half_up(correct, d)
    # sanity: the pinned correct_expected must equal the exact-rounded correct answer
    correct_matches_pin = round_half_up(correct, d) == PF(str(h["correct_expected"]))
    n_trap_pass += flagged
    trap_results.append({
        "id": hid, "wrong_value": h["wrong_value"],
        "correct_exact": fmt(correct, d),
        "correct_expected_pin_consistent": bool(correct_matches_pin),
        "abs_error": fmt(abs(wrong - correct), d),
        "correctly_flagged": bool(flagged),
    })

n_pos, n_trap = len(pos_results), len(trap_results)
all_trap_pins_ok = all(t["correct_expected_pin_consistent"] for t in trap_results)

# cross-check: DGEBA EEW re-derives to the portfolio DGEBA EEW-series anchor 170.21
dgeba_eew = molar_mass({"C": 21, "H": 24, "O": 4}) / 2
report = {
    "schema": "amphora.known-answer.molar-mass-kat-report.v1",
    "vector_set_id": data["vector_set_id"],
    "module_id": data["module_id"],
    "authority": "AUDIT_ONLY",
    "methodology": "FIPS 140-3 Sec 7.4 Known-Answer Test (2019); IUPAC CIAAW 2021 "
                   "standard atomic weights (Meija et al., Pure Appl. Chem. 2016, "
                   "88(3):265-291, DOI 10.1515/pac-2015-0305). Exact rational molar-mass "
                   "re-derivation from the pinned atomic-weight table; float-free gate.",
    "vectors_file_sha256": vec_sha,
    "n_positive": n_pos, "n_positive_pass": n_pos_pass,
    "n_fail_closed": n_trap, "n_fail_closed_correctly_flagged": n_trap_pass,
    "positive_pass_rate": fmt(F(n_pos_pass, n_pos), 6),
    "fail_closed_flag_rate": fmt(F(n_trap_pass, n_trap), 6),
    "all_positive_exact": n_pos_pass == n_pos,
    "all_traps_rejected": n_trap_pass == n_trap,
    "all_trap_correct_pins_consistent": all_trap_pins_ok,
    "aggregate_status": "PASS" if (n_pos_pass == n_pos and n_trap_pass == n_trap
                                   and all_trap_pins_ok) else "FAIL",
    "positive_results": pos_results,
    "fail_closed_results": trap_results,
    "cross_check_portfolio_constants": {
        "note": "The DGEBA (n=0) epoxide equivalent weight EEW = M(C21H24O4)/2 is re-derived "
                "here as an EXACT rational sum of the IUPAC 2021 atomic weights, independent "
                "of any published EEW. It reproduces the amphora-molecule-property DGEBA "
                "EEW-series anchor EEW(0) = 170.21 g/eq to 2 decimals, corroborating that "
                "module non-circularly and locking the atomic-weight table that the "
                "portfolio's EEW/AHEW, mix-ratio, VOC and pigment arithmetic depend on. A "
                "future edit to a pinned atomic weight is caught as a known-answer regression.",
        "dgeba_eew_g_per_eq": fmt(dgeba_eew, 2),
        "dgeba_eew_series_module_anchor_g_per_eq": 170.21,
        "dgeba_eew_cross_check_matches_to_2_decimals": fmt(dgeba_eew, 2) == "170.21",
    },
    "authority_ceiling": "LIMITED_SANITY",
    "scientific_claim": "Deterministic molar-mass arithmetic over the IUPAC 2021 standard "
                        "atomic weights reproduces the published molar masses of the coating "
                        "molecules and their theoretical epoxide/amine equivalent weights; "
                        "regressions to integer nucleon counts, legacy atomic-weight roundings, "
                        "monoisotopic masses, or wrong functionality are detected. NOT a "
                        "candidate performance or qualification claim.",
}
OUT.write_text(json.dumps(report, indent=2, sort_keys=True))
print("REPORT_SHA256", hashlib.sha256(OUT.read_bytes()).hexdigest())
print("AGG", report["aggregate_status"], "pos", f"{n_pos_pass}/{n_pos}", "traps", f"{n_trap_pass}/{n_trap}")
print("DGEBA_EEW_XCHECK", report["cross_check_portfolio_constants"]["dgeba_eew_cross_check_matches_to_2_decimals"])
print("TRAP_PINS_OK", all_trap_pins_ok)
