"""Independent exact-rational verifier for the unit-conversion Known-Answer Test battery.

Re-derives every pinned expected value in unit_conversion_kat_vectors.v1.json from
the EXACT rational SI/US defining constants (NIST SP 811 2008; NIST HB 44; the
1959 international yard-and-pound agreement; BIPM SI), using fractions.Fraction
only -- no floating-point arithmetic enters the pass/fail gate, so the report is
byte-stable across replays by construction. A positive vector PASSES iff
round_half_up(exact_rational, decimals) equals the pinned expected value. A
fail-closed hostile vector PASSES iff its wrong factor/value does NOT equal the
exact-rounded correct answer (i.e. the trap is correctly rejected).

AUDIT_ONLY. Limited-sanity known-answer evidence. No candidate-performance claim.
Primary methodology: FIPS 140-3 Sec 7.4 Known-Answer Test (2019); NIST SP 811 (2008).
"""
import sys, json, hashlib
from fractions import Fraction as F
from pathlib import Path

VEC = Path(sys.argv[1])
OUT = Path(sys.argv[2])

# ---- exact rational defining constants ---------------------------------------
IN_M   = F(254, 10000)          # 1 inch = 0.0254 m (exact)
GAL_L  = 231 * IN_M**3 * 1000   # 1 US gal = 231 in^3, expressed in litres (exact)
LB_KG  = F(45359237, 10**8)     # 1 lb = 0.45359237 kg (exact)
FT_M   = F(3048, 10000)         # 1 ft = 0.3048 m (exact)
K_OFF  = F(27315, 100)          # 273.15 (exact)
MIL_UM = F(254, 10)             # 1 mil = 25.4 um (exact)
IMP_L  = F(454609, 100000)      # 1 Imperial gal = 4.54609 L (exact, trap only)

def round_half_up(frac, d):
    scale = 10**d
    n = frac * scale
    floor = n.numerator // n.denominator      # floor (values here are positive)
    if n - floor >= F(1, 2):
        floor += 1
    return F(floor, scale)

def fmt(frac, d):
    # exact fixed-decimal string via the same half-up rounding, no float
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

# id -> exact derivation from raw constants (independent of the pinned value)
DERIV = {
    "DENS-GML-TO-LBGAL":            lambda: GAL_L / LB_KG,
    "VOC-LBGAL-TO-GL":             lambda: LB_KG * 1000 / GAL_L,
    "VOC-2P8-LBGAL-TO-GL":         lambda: F(28, 10) * LB_KG * 1000 / GAL_L,
    "DFT-1MIL-TO-UM":              lambda: MIL_UM,
    "DFT-5MIL-TO-UM":              lambda: 5 * MIL_UM,
    "DFT-100UM-TO-MIL":            lambda: F(100) / MIL_UM,
    "COVERAGE-1MIL-100VS-FT2GAL":  lambda: F(231000) / 144,
    "COVERAGE-1UM-100VS-M2L":      lambda: F(1000),
    "COVERAGE-1604-FT2GAL-TO-M2L": lambda: (F(231000) / 144) * FT_M**2 / GAL_L,
    "TEMP-25C-TO-K":               lambda: F(25) + K_OFF,
    "TEMP-25C-TO-F":               lambda: F(25) * F(9, 5) + 32,
    "MASS-1LB-TO-KG":              lambda: LB_KG,
    "VOL-1GAL-TO-L":               lambda: GAL_L,
    "AREA-1FT2-TO-M2":             lambda: FT_M**2,
}
# independent exact correct answer for each hostile trap
TRAP_CORRECT = {
    "TRAP-WATER-833":    lambda: GAL_L / LB_KG,
    "TRAP-IMPERIAL-GAL": lambda: GAL_L / LB_KG,
    "TRAP-MIL-AS-MM":    lambda: MIL_UM,
}

data = json.loads(VEC.read_text())
vec_sha = hashlib.sha256(VEC.read_bytes()).hexdigest()

pos_results, n_pos_pass = [], 0
for v in data["positive_vectors"]:
    vid, d = v["id"], v["decimals"]
    derived = DERIV[vid]()
    derived_str = fmt(derived, d)
    expected_str = f"{v['expected']:.{d}f}"
    ok = round_half_up(derived, d) == F(expected_str)
    n_pos_pass += ok
    pos_results.append({
        "id": vid, "input": v["input"], "input_unit": v["input_unit"],
        "output_unit": v["output_unit"], "decimals": d,
        "pinned_expected": expected_str, "independently_derived": derived_str,
        "exact_rational": f"{derived.numerator}/{derived.denominator}",
        "match": bool(ok),
    })

trap_results, n_trap_pass = [], 0
for h in data["fail_closed_hostile_vectors"]:
    hid, d = h["id"], 6
    correct = TRAP_CORRECT[hid]()
    wrong = h.get("wrong_factor", h.get("wrong_value"))
    correct_rounded = round_half_up(correct, d)
    flagged = round_half_up(F(str(wrong)), d) != correct_rounded    # trap rejected?
    n_trap_pass += flagged
    trap_results.append({
        "id": hid, "wrong_value": wrong,
        "correct_exact": fmt(correct, d),
        "abs_error": fmt(abs(F(str(wrong)) - correct), 6),
        "correctly_flagged": bool(flagged),
    })

n_pos, n_trap = len(pos_results), len(trap_results)
report = {
    "schema": "amphora.known-answer.unit-conversion-kat-report.v1",
    "vector_set_id": data["vector_set_id"],
    "module_id": data["module_id"],
    "authority": "AUDIT_ONLY",
    "methodology": "FIPS 140-3 Sec 7.4 Known-Answer Test (2019); NIST SP 811 (2008); "
                   "NIST HB 44; 1959 international yard-and-pound; BIPM SI. Exact rational "
                   "re-derivation; float-free gate.",
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
    "cross_check_existing_arith_controls": {
        "note": "The two live MIL-DTL-24441 F-160 lb/gal controls in this module "
                "(8.22 and 10.24 lb/gal) imply g/mL densities via the NIST-exact factor "
                "8.345404; this battery locks that factor so a future edit to the "
                "conversion constant is caught as a known-answer regression.",
        "F160_compA_lbgal": 8.22, "F160_compA_implied_gml": fmt(F("8.22") / (GAL_L / LB_KG), 6),
        "F160_compB_lbgal": 10.24, "F160_compB_implied_gml": fmt(F("10.24") / (GAL_L / LB_KG), 6),
    },
    "authority_ceiling": "LIMITED_SANITY",
    "scientific_claim": "Deterministic unit-conversion arithmetic reproduces exact "
                        "primary-source defining constants; regressions in the conversion "
                        "factors are detected. NOT a candidate performance or qualification claim.",
}
OUT.write_text(json.dumps(report, indent=2, sort_keys=True))
print("REPORT_SHA256", hashlib.sha256(OUT.read_bytes()).hexdigest())
print("AGG", report["aggregate_status"], "pos", f"{n_pos_pass}/{n_pos}", "traps", f"{n_trap_pass}/{n_trap}")
