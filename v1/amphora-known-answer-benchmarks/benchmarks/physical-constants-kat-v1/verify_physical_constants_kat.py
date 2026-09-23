"""Independent exact-rational verifier for the physical-constants Known-Answer Test battery.

Re-derives every pinned expected value in physical_constants_kat_vectors.v1.json from
the EXACT rational SI-2019 defining constants (BIPM SI Brochure 9th ed. 2019; CODATA
2018), using fractions.Fraction only -- no floating-point arithmetic enters the
pass/fail gate, so the report is byte-stable across replays by construction.

Post-2019 SI redefinition, N_A, k_B and e are exact defined integers, so the molar
gas constant R = N_A*k_B and the Faraday constant F = N_A*e are EXACT rational
products. A defining-constant ("exact" mode) vector PASSES iff the reconstructed
exact rational equals the pinned defining value. A derived vector PASSES iff
round_half_up(exact_rational, decimals) equals the pinned expected value -- the
derivation uses ONLY raw defining constants, never the pinned R/F, so it is
non-circular. A fail-closed hostile vector PASSES iff its wrong value does NOT
equal the exact-rounded correct answer (trap correctly rejected).

AUDIT_ONLY. Limited-sanity known-answer evidence. No candidate-performance claim.
Primary methodology: FIPS 140-3 Sec 7.4 Known-Answer Test (2019); CODATA 2018;
BIPM SI Brochure 9th ed. (2019).
"""
import sys, json, hashlib, re
from fractions import Fraction as F
from pathlib import Path

VEC = Path(sys.argv[1])
OUT = Path(sys.argv[2])

# ---- exact rational SI-2019 defining constants -------------------------------
NA  = F(602214076, 10**8) * 10**23    # Avogadro number, exact (SI 2019)
KB  = F(1380649, 10**29)              # Boltzmann constant J/K, exact (SI 2019)
E   = F(1602176634, 10**28)           # elementary charge C, exact (SI 2019)
K0  = F(27315, 100)                   # Celsius->Kelvin offset 273.15, exact
ATM = F(101325)                       # standard atmosphere Pa, exact
MZN = F(6538, 100)                    # Zn standard atomic weight g/mol (IUPAC 2021)
Z_ZN = 2                              # Zn -> Zn2+ + 2e-


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


# id -> exact derivation from RAW constants (independent of the pinned value)
DERIV = {
    "CONST-NA-DEF":          lambda: NA,
    "CONST-KB-DEF":          lambda: KB,
    "CONST-E-DEF":           lambda: E,
    "R-FROM-NA-KB":          lambda: NA * KB,
    "F-FROM-NA-E":           lambda: NA * E,
    "TEMP-0C-TO-K":          lambda: K0,
    "STD-ATM-PA":            lambda: ATM,
    "RT-298P15":             lambda: (NA * KB) * (F(25) + K0),
    "FARADAY-AH-PER-MOL-E":  lambda: (NA * E) / 3600,
    "ZN-SPECIFIC-CHARGE":    lambda: F(1000) * Z_ZN * (NA * E) / (MZN * 3600),
}
# independent exact correct answer for each hostile trap
TRAP_CORRECT = {
    "TRAP-R-PRE2019":  lambda: NA * KB,
    "TRAP-NA-PRE2019": lambda: NA,
    "TRAP-KELVIN-273": lambda: K0,
    "TRAP-F-96500":    lambda: NA * E,
    "TRAP-R-CAL-AS-J": lambda: NA * KB,
}

data = json.loads(VEC.read_text())
vec_sha = hashlib.sha256(VEC.read_bytes()).hexdigest()

pos_results, n_pos_pass = [], 0
for v in data["positive_vectors"]:
    vid = v["id"]
    derived = DERIV[vid]()
    if v["mode"] == "exact":
        expected = PF(v["expected"])
        ok = derived == expected
        derived_str = v["expected"] if ok else f"{derived.numerator}/{derived.denominator}"
        pinned_str = str(v["expected"])
    else:
        d = v["decimals"]
        expected = PF(str(v["expected"]))
        ok = round_half_up(derived, d) == expected
        derived_str = fmt(derived, d)
        pinned_str = fmt(expected, d)
    n_pos_pass += ok
    pos_results.append({
        "id": vid, "quantity": v["quantity"], "unit": v["unit"], "mode": v["mode"],
        "pinned_expected": pinned_str, "independently_derived": derived_str,
        "exact_rational": f"{derived.numerator}/{derived.denominator}",
        "match": bool(ok),
    })

trap_results, n_trap_pass = [], 0
for h in data["fail_closed_hostile_vectors"]:
    hid = h["id"]
    correct = TRAP_CORRECT[hid]()
    wrong = PF(str(h["wrong_value"]))
    if h.get("mode") == "exact":
        flagged = wrong != correct
        correct_str = h["correct_expected"]
        abs_err = f"{abs(wrong - correct).numerator}/{abs(wrong - correct).denominator}"
    else:
        d = h["decimals"]
        flagged = round_half_up(wrong, d) != round_half_up(correct, d)
        correct_str = fmt(correct, d)
        abs_err = fmt(abs(wrong - correct), d)
    n_trap_pass += flagged
    trap_results.append({
        "id": hid, "wrong_value": h["wrong_value"],
        "correct_exact": correct_str, "abs_error": abs_err,
        "correctly_flagged": bool(flagged),
    })

n_pos, n_trap = len(pos_results), len(trap_results)
# cross-check: reproduce the amphora-zinc-galvanic control 819.868 Ah/kg
zn = F(1000) * Z_ZN * (NA * E) / (MZN * 3600)
report = {
    "schema": "amphora.known-answer.physical-constants-kat-report.v1",
    "vector_set_id": data["vector_set_id"],
    "module_id": data["module_id"],
    "authority": "AUDIT_ONLY",
    "methodology": "FIPS 140-3 Sec 7.4 Known-Answer Test (2019); CODATA 2018; BIPM SI "
                   "Brochure 9th ed. (2019); IUPAC 2021 atomic weights. Exact rational "
                   "re-derivation from SI-2019 defining constants; float-free gate.",
    "vectors_file_sha256": vec_sha,
    "n_positive": n_pos, "n_positive_pass": n_pos_pass,
    "n_fail_closed": n_trap, "n_fail_closed_correctly_flagged": n_trap_pass,
    "positive_pass_rate": fmt(F(n_pos_pass, n_pos), 6),
    "fail_closed_flag_rate": fmt(F(n_trap_pass, n_trap), 6),
    "all_positive_exact": n_pos_pass == n_pos,
    "all_traps_rejected": n_trap_pass == n_trap,
    "aggregate_status": "PASS" if (n_pos_pass == n_pos and n_trap_pass == n_trap) else "FAIL",
    "positive_results": pos_results,
    "fail_closed_results": trap_results,
    "cross_check_portfolio_constants": {
        "note": "R = N_A*k_B and F = N_A*e are re-derived here as EXACT rational products "
                "of the SI-2019 defining constants, independent of any pinned value. The "
                "sacrificial-zinc specific charge derives to 819.868 Ah/kg, reproducing the "
                "amphora-zinc-galvanic control to 4 significant figures from F and IUPAC "
                "M_Zn = 65.38 alone; this locks the Faraday and gas constants that the "
                "portfolio's Arrhenius/Kissinger cure-kinetics, Eyring viscosity, and zinc "
                "galvanic modules depend on, so a future edit to R or F is caught as a "
                "known-answer regression.",
        "R_J_per_mol_K": fmt(NA * KB, 9),
        "F_C_per_mol": fmt(NA * E, 6),
        "zinc_specific_charge_Ah_per_kg": fmt(zn, 6),
        "zinc_galvanic_module_control_Ah_per_kg": 819.868,
        "zinc_cross_check_matches_to_4_sig_figs": fmt(zn, 3) == "819.868",
    },
    "authority_ceiling": "LIMITED_SANITY",
    "scientific_claim": "Deterministic physical-constant arithmetic reproduces the exact "
                        "SI-2019 defined constants and their exact derived products (R, F, "
                        "R*T, zinc specific charge); regressions to pre-2019 measured values, "
                        "textbook roundings, or cal/J unit swaps are detected. NOT a candidate "
                        "performance or qualification claim.",
}
OUT.write_text(json.dumps(report, indent=2, sort_keys=True))
print("REPORT_SHA256", hashlib.sha256(OUT.read_bytes()).hexdigest())
print("AGG", report["aggregate_status"], "pos", f"{n_pos_pass}/{n_pos}", "traps", f"{n_trap_pass}/{n_trap}")
print("ZN_XCHECK", report["cross_check_portfolio_constants"]["zinc_cross_check_matches_to_4_sig_figs"])
