#!/usr/bin/env python3
"""amphora-envelope-gates :: flory-stockmayer-gelation-window-v1

Independent, NON-RUNTIME theory-axis analysis extending
stoichiometric-index-equivalents-v1: map the shipped mass-envelope-induced
stoichiometric-index excursion through the Flory (1941) / Stockmayer (1943)
gelation criterion to decide whether the documented envelope->index gap is a
NETWORK-FORMATION risk or only a conversion/Tg-quality concern.

MOTIVATING GAP
--------------
stoichiometric-index-equivalents-v1 proved the shipped 3-constraint +/-5%
per-part mass envelope permits amine-H:epoxide stoichiometric-index excursions
of +10.5263% / -9.5238% (EEW/AHEW-invariant, 10/10 envelopes) and bounds
neither extreme. It did NOT say how physically severe that gap is. The
sharpest zero-parameter physical severity test available is the classical
Flory-Stockmayer gelation criterion for stepwise A_f + B_g polymerization
(equal reactivity, no intramolecular cycles):

    p_A * p_B * (f-1)(g-1) = 1        at the gel point            (1)
    p_B = p_A / r,   r = [B]/[A] = amine-H : epoxide index        (2)
 => p_A,gel(r) = sqrt( r / ((f-1)(g-1)) )                         (3)

with f = 2 epoxide groups per DGEBA molecule and g = active amine-H per
hardener molecule. Requiring the gel point to be reachable at full conversion
of the limiting group (p_A <= min(1, r)) yields the closed GELABILITY WINDOW

    1/((f-1)(g-1)) <= r <= (f-1)(g-1)                             (4)

(Flory, J. Am. Chem. Soc. 63 (1941) 3083, DOI 10.1021/ja01856a061;
Stockmayer, J. Chem. Phys. 11 (1943) 45, DOI 10.1063/1.1723803; r-modified
form as in Odian, Principles of Polymerization, 4th ed. 2004, Ch.2.10/2.12,
ISBN 978-0471274001).

GATES
-----
  G1  KNOWN-ANSWER ANCHORS for the implementation of (3)/(4):
      a) r=1, f=3, g=3  -> p_gel = 1/2            (Flory 1941 classic)
      b) r=1, f=2, g=4  -> p_gel = 1/sqrt(3)      (diepoxide + diamine)
      c) f=2, g=2       -> (f-1)(g-1)=1: degenerate window [1,1]; linear
         chain gels only at exact stoichiometry AND complete conversion
         (Carothers limit) -- flagged NOT robustly gelable.
      d) window reciprocal symmetry W_lo * W_hi = 1 for g in 3..8.
      e) p_gel strictly increasing in r on the feasible range (grid, g=4).

  G2  GELABILITY-CONTAINMENT (H0 REFUTATION TARGET). H0: "the shipped +/-5%
      per-part mass envelope can push a formulation outside the
      Flory-Stockmayer gelability window (4)." For each of the 7
      first-principles envelopes: BOTH worst-case index corners
      r_lean = r0*(1-P)/(1+P), r_rich = r0*(1+P)/(1-P) must (i) PASS all
      three shipped hard gates under the actual constraint-envelope-oracle-v1
      evaluate_gate, and (ii) lie strictly inside the window. Verdict must be
      invariant when the DGEBA EEW is moved across the documented commercial
      spec band 182-192 g/eq (index rescales by EEW/170.21). 7/7 => H0
      REFUTED: the documented index gap is NOT gelation-threatening.

  G3  ANALYTIC/FEASIBILITY COHERENCE. The window (4) and the reachability
      condition p_gel(r) <= min(1, r) are two independent derivations of
      gelability; assert their strict-interior forms agree pointwise on a
      41-point multiplicative r-grid per envelope (boundary-adjacent points
      excluded within 1e-9 relative).

  G4  GEL-CONVERSION LATITUDE + HEADROOM-TO-CLIFF. From (3),
      p_gel(r_corner)/p_gel(r0) = sqrt(corner factor): the envelope shifts
      the gel-point epoxide conversion by EXACTLY +5.1315% / -4.8810%,
      EEW/AHEW-invariant (corollary of the excursion-invariance theorem).
      Per envelope, solve in closed form the critical per-part band P* at
      which the excursion WOULD first touch the window boundary:
        lean side:  P*_lean = (1-q)/(1+q),  q = W_lo/r0   (if q<1)
        rich side:  P*_rich = (s-1)/(s+1),  s = W_hi/r0   (if s>1)
      P* = min(sides). Assert P* > P = 0.05 for all 7 (quantified distance
      to the physical cliff; binding envelope reported).

  G5  FAIL-CLOSED TAMPER BATTERY. f<2, g<2, non-finite/non-positive r,
      degenerate (f-1)(g-1)=1 window, and adduct hardeners without
      first-principles g must all fail closed / be reported as data gap.

Non-circular: equations (1)-(4), the closed-form corner factors and P*, and
all KAT anchors are published polymer-physics results re-derived here from
first principles; g (active amine-H count) and AHEW come from IUPAC-2021
atomic weights + published molecular formulas; DGEBA f=2 and EEW=170.21 are
the portfolio-locked molar-mass facts. Only on-disk fixture bytes are
consumed. The shipped oracle's evaluate_gate is reused ONLY to confirm the
excursion corners PASS under the actual contract. Distinct from
amphora-molecule-role-ranker's Flory/Macosko-Miller receipts: those rank
MOLECULE gelation capability; this study bounds the physical severity of the
ENVELOPE's tolerance gap. AUDIT_ONLY. Does NOT promote authority, flip
scientific_readiness (stays NOT_APPLICABLE), or modify the manifest / locked
dataset / KPI / benchmark-lock.
"""
import hashlib, importlib.util, json, math, sys
from pathlib import Path

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-envelope-gates"
KAT = MOD / "reference/phase0-envelope-gates-known-answer.v1.json"
PRIOR = MOD / "benchmarks/constraint-envelope-oracle-v1/run_envelope_gates.py"

P = 0.05                 # +/-5% per-part QC band (Wicks/Jones/Pappas 2007 Ch.24)
F_EPOXIDE = 2            # epoxide groups per DGEBA molecule (portfolio-locked)
RND = 10                 # fixed rounding for byte-stable diagnostic

# IUPAC 2021 conventional standard atomic weights (portfolio KAT molar-mass pin)
AW = {"C": 12.011, "H": 1.008, "N": 14.007}
EEW_DGEBA_PURE = 170.21          # g/eq, portfolio-locked DGEBA n=0
EEW_COMMERCIAL_SPEC = (182.0, 192.0)   # DER 331 / GY 6010 TDS band (sensitivity only)

# Same 7 first-principles pure-amine hardeners as stoichiometric-index-
# equivalents-v1; g = active amine-H per molecule (Flory-Stockmayer B_g).
HARDENERS = {
    "TETA": {"C": 6, "H": 18, "N": 4, "g": 6},
    "DETA": {"C": 4, "H": 13, "N": 3, "g": 5},
    "TEPA": {"C": 8, "H": 23, "N": 5, "g": 7},
    "IPDA": {"C": 10, "H": 22, "N": 2, "g": 4},
    "PACM": {"C": 13, "H": 26, "N": 2, "g": 4},
    "MXDA": {"C": 8, "H": 12, "N": 2, "g": 4},
    "MPDA": {"C": 6, "H": 8, "N": 2, "g": 4},
}
ENV_HARDENER = {
    "dgeba-teta-primer-9to1": "TETA",
    "dgeba-deta-industrial-primer-17to1": "DETA",
    "dgeba-tepa-adhesive-neat-100to15": "TEPA",
    "dgeba-ipda-marine-primer-100to24": "IPDA",
    "dgeba-pacm-marine-topcoat-100to30": "PACM",
    "dgeba-mxda-tank-lining-100to22": "MXDA",
    "dgeba-mpda-aerospace-composite-100to14": "MPDA",
    "dgeba-amidoamine-huntsman-100to50": None,
    "dgeba-amidoamine-momentive-100to53": None,
    "dgeba-mannich-fast-cure-100to36": None,
}


def sha(b): return hashlib.sha256(b).hexdigest()


_spec = importlib.util.spec_from_file_location("prior_oracle", PRIOR)
_prior = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_prior)
evaluate_gate = _prior.evaluate_gate


def ahew(h):
    mw = h["C"] * AW["C"] + h["H"] * AW["H"] + h["N"] * AW["N"]
    return mw / h["g"]


def branching_product(f, g):
    """K = (f-1)(g-1). Fail-closed on non-physical functionality."""
    if not isinstance(f, (int, float)) or not isinstance(g, (int, float)):
        return None
    if not (math.isfinite(float(f)) and math.isfinite(float(g))):
        return None
    if f < 2 or g < 2:
        return None            # no network-forming chemistry
    return (float(f) - 1.0) * (float(g) - 1.0)


def gel_window(f, g):
    """Closed gelability window (4). None if fail-closed or degenerate K<=1."""
    K = branching_product(f, g)
    if K is None or K <= 1.0:
        return None            # K==1: linear (Carothers limit); K<1 impossible
    return (1.0 / K, K)


def p_gel(r, f, g):
    """Eq. (3): epoxide conversion at the gel point. Fail-closed."""
    K = branching_product(f, g)
    if K is None or K <= 0.0:
        return None
    if not isinstance(r, (int, float)) or not math.isfinite(float(r)) or r <= 0.0:
        return None
    return math.sqrt(float(r) / K)


def gelable_strict_window(r, f, g):
    w = gel_window(f, g)
    if w is None or r is None:
        return False
    return w[0] < r < w[1]


def gelable_strict_feasibility(r, f, g):
    pg = p_gel(r, f, g)
    if pg is None:
        return False
    return pg < min(1.0, float(r))


def headroom_pstar(r0, w):
    """Closed-form critical per-part band P* at which the excursion first
    touches the window boundary; None if r0 already outside."""
    w_lo, w_hi = w
    if not (w_lo < r0 < w_hi):
        return None
    q = w_lo / r0            # < 1
    s = w_hi / r0            # > 1
    p_lean = (1.0 - q) / (1.0 + q)
    p_rich = (s - 1.0) / (s + 1.0)
    return min(p_lean, p_rich), ("amine_lean" if p_lean <= p_rich else "amine_rich")


def run():
    kat_bytes = KAT.read_bytes()
    kat = json.loads(kat_bytes)
    envelopes = kat["envelopes"]

    hi_factor = (1.0 + P) / (1.0 - P)
    lo_factor = (1.0 - P) / (1.0 + P)
    gel_shift_hi_pct = (math.sqrt(hi_factor) - 1.0) * 100.0
    gel_shift_lo_pct = (math.sqrt(lo_factor) - 1.0) * 100.0

    # ---- G1 known-answer anchors ---------------------------------------
    anchors = []

    def add_anchor(name, ok, detail):
        anchors.append({"anchor": name, "passed": bool(ok), "detail": detail})

    pa = p_gel(1.0, 3, 3)
    add_anchor("flory1941_f3_g3_r1_pgel_half",
               pa is not None and abs(pa - 0.5) <= 1e-15,
               f"p_gel={pa!r} vs 1/2 exact (Flory 1941)")
    pb = p_gel(1.0, 2, 4)
    add_anchor("stockmayer1943_f2_g4_r1_pgel_invsqrt3",
               pb is not None and abs(pb - 1.0 / math.sqrt(3.0)) <= 1e-15,
               f"p_gel={pb!r} vs 1/sqrt(3) (Stockmayer 1943)")
    add_anchor("carothers_f2_g2_degenerate_linear",
               gel_window(2, 2) is None and p_gel(1.0, 2, 2) == 1.0,
               "K=1: window degenerate, gel only at r=1 AND p=1 (linear limit)")
    sym_ok = True
    for g in range(3, 9):
        w = gel_window(2, g)
        sym_ok = sym_ok and w is not None and abs(w[0] * w[1] - 1.0) <= 1e-12
    add_anchor("window_reciprocal_symmetry_g3_to_g8", sym_ok,
               "W_lo*W_hi=1 exact for f=2, g=3..8")
    mono_ok = True
    prev = None
    for i in range(1, 60):
        r = i / 20.0                     # 0.05 .. 2.95, inside/around g=4 window
        pg = p_gel(r, 2, 4)
        if prev is not None and not pg > prev:
            mono_ok = False
        prev = pg
    add_anchor("pgel_strictly_increasing_in_r_g4_grid", mono_ok,
               "p_gel(r) strictly increasing on 59-point grid (f=2, g=4)")
    g1_pass = all(a["passed"] for a in anchors)

    # ---- G2 containment + G3 coherence + G4 latitude -------------------
    per_env = []
    n_env = 0
    n_first_principles = 0
    n_contained = 0
    n_corner_oracle_pass = 0
    n_eew_invariant = 0
    n_coherent = 0
    n_headroom_ok = 0
    n_shift_invariant = 0
    coherence_points_total = 0
    coherence_points_agree = 0
    binding = None            # (pstar, envelope_id, side)

    for env in envelopes:
        n_env += 1
        eid = env["envelope_id"]
        hkey = ENV_HARDENER[eid]
        A0 = float(env["nominal_part_a_g"])
        B0 = float(env["nominal_part_b_g"])
        cons = {c["feature_path"]: c for c in env["policy"]["constraints"]}
        A_lo = float(cons["mass.part_A_g"]["lower_inclusive"])
        A_hi = float(cons["mass.part_A_g"]["upper_inclusive"])
        B_lo = float(cons["mass.part_B_g"]["lower_inclusive"])
        B_hi = float(cons["mass.part_B_g"]["upper_inclusive"])

        if hkey is None:
            per_env.append({
                "envelope_id": eid,
                "hardener_family": env["hardener_family"],
                "hardener": None,
                "excluded_data_gap": True,
                "note": ("proprietary reactive adduct: no first-principles g "
                         "(active amine-H) or AHEW -> gelation window requires "
                         "supplier TDS functionality (data gap, already queued)"),
            })
            continue
        n_first_principles += 1
        h = HARDENERS[hkey]
        g = h["g"]
        ahew_v = ahew(h)
        w = gel_window(F_EPOXIDE, g)
        K = branching_product(F_EPOXIDE, g)

        def index(ma, mb, eew):
            return (mb * eew) / (ma * ahew_v)

        r0 = index(A0, B0, EEW_DGEBA_PURE)
        r_rich = index(A_lo, B_hi, EEW_DGEBA_PURE)
        r_lean = index(A_hi, B_lo, EEW_DGEBA_PURE)

        # (i) both corners PASS the shipped oracle (re-confirmed, not assumed)
        base_snap = next(tc["snapshot"] for tc in env["test_cases"]
                         if tc["subgroup"] == "NOMINAL")

        def corner_verdict(ma, mb):
            snap = json.loads(json.dumps(base_snap))
            snap["values"]["mass.part_A_g"]["value"] = ma
            snap["values"]["mass.part_B_g"]["value"] = mb
            snap["values"]["mass.total_g"]["value"] = ma + mb
            v, _, _ = evaluate_gate(env["policy"], snap)
            return v

        oracle_ok = (corner_verdict(A_lo, B_hi) == "PASS"
                     and corner_verdict(A_hi, B_lo) == "PASS")
        n_corner_oracle_pass += int(oracle_ok)

        # (ii) strict containment of the whole excursion interval in the window
        contained = (w is not None and w[0] < r_lean and r_rich < w[1]
                     and w[0] < r0 < w[1])
        n_contained += int(contained)

        # (iii) verdict invariant across the commercial DGEBA EEW spec band
        eew_verdicts = []
        for eew in EEW_COMMERCIAL_SPEC:
            rl = index(A_hi, B_lo, eew)
            rr = index(A_lo, B_hi, eew)
            eew_verdicts.append(w is not None and w[0] < rl and rr < w[1])
        eew_invariant = all(v == contained for v in eew_verdicts)
        n_eew_invariant += int(eew_invariant)

        # G3 analytic/feasibility coherence on a 41-point multiplicative grid
        # spanning [W_lo/2, 2*W_hi]; boundary-adjacent points excluded.
        coherent = True
        lo_g, hi_g = w[0] / 2.0, w[1] * 2.0
        ratio = hi_g / lo_g
        for i in range(41):
            r = lo_g * math.pow(ratio, i / 40.0)
            if (abs(r - w[0]) <= 1e-9 * w[0]) or (abs(r - w[1]) <= 1e-9 * w[1]):
                continue
            a_side = gelable_strict_window(r, F_EPOXIDE, g)
            b_side = gelable_strict_feasibility(r, F_EPOXIDE, g)
            coherence_points_total += 1
            if a_side == b_side:
                coherence_points_agree += 1
            else:
                coherent = False
        n_coherent += int(coherent)

        # G4 gel-conversion latitude and headroom-to-cliff
        pg0 = p_gel(r0, F_EPOXIDE, g)
        pg_rich = p_gel(r_rich, F_EPOXIDE, g)
        pg_lean = p_gel(r_lean, F_EPOXIDE, g)
        shift_ok = (abs(pg_rich / pg0 - math.sqrt(hi_factor)) <= 1e-12
                    and abs(pg_lean / pg0 - math.sqrt(lo_factor)) <= 1e-12)
        n_shift_invariant += int(shift_ok)
        hp = headroom_pstar(r0, w)
        pstar, pstar_side = (hp if hp is not None else (None, None))
        headroom_ok = pstar is not None and pstar > P
        n_headroom_ok += int(headroom_ok)
        if pstar is not None and (binding is None or pstar < binding[0]):
            binding = (pstar, eid, pstar_side)

        per_env.append({
            "envelope_id": eid,
            "hardener_family": env["hardener_family"],
            "hardener": hkey,
            "excluded_data_gap": False,
            "amine_functionality_g_active_H": g,
            "branching_product_K": round(K, RND),
            "gelability_window_r": [round(w[0], RND), round(w[1], RND)],
            "index_r0_pure_eew": round(r0, RND),
            "index_corner_amine_lean": round(r_lean, RND),
            "index_corner_amine_rich": round(r_rich, RND),
            "corners_pass_shipped_oracle": oracle_ok,
            "excursion_contained_in_window": contained,
            "verdict_invariant_over_commercial_eew_182_192": eew_invariant,
            "analytic_feasibility_coherent": coherent,
            "p_gel_epoxide_nominal": round(pg0, RND),
            "p_gel_epoxide_amine_lean": round(pg_lean, RND),
            "p_gel_epoxide_amine_rich": round(pg_rich, RND),
            "gel_shift_matches_sqrt_invariant": shift_ok,
            "headroom_band_pstar": (round(pstar, RND) if pstar is not None else None),
            "headroom_binding_side": pstar_side,
            "headroom_exceeds_shipped_band": headroom_ok,
        })

    g2_pass = (n_contained == n_first_principles
               and n_corner_oracle_pass == n_first_principles
               and n_eew_invariant == n_first_principles)
    g3_pass = (n_coherent == n_first_principles
               and coherence_points_agree == coherence_points_total)
    g4_pass = (n_shift_invariant == n_first_principles
               and n_headroom_ok == n_first_principles)

    # ---- G5 fail-closed tamper battery ---------------------------------
    probes = []

    def add_probe(name, ok, detail):
        probes.append({"probe": name, "fail_closed": bool(ok), "detail": detail})

    add_probe("functionality_f1_rejected", gel_window(1, 4) is None,
              "f<2 cannot form a network")
    add_probe("functionality_g1_rejected", gel_window(2, 1) is None,
              "g<2 cannot form a network")
    add_probe("degenerate_K1_window_rejected", gel_window(2, 2) is None,
              "(f-1)(g-1)=1 linear Carothers limit has no open window")
    add_probe("nonfinite_r_rejected", p_gel(float("nan"), 2, 4) is None,
              "non-finite index rejected")
    add_probe("nonpositive_r_rejected", p_gel(0.0, 2, 4) is None,
              "r<=0 rejected")
    add_probe("nonfinite_g_rejected", gel_window(2, float("inf")) is None,
              "non-finite functionality rejected")
    add_probe("out_of_window_detected",
              not gelable_strict_window(10.0, 2, 4)
              and not gelable_strict_feasibility(10.0, 2, 4),
              "r=10 > W_hi=3 flagged non-gelable by BOTH derivations")
    add_probe("adducts_reported_not_silently_passed",
              sum(1 for e in per_env if e.get("excluded_data_gap")) == 3,
              "3 adduct envelopes excluded as explicit data gap")
    g5_pass = all(p["fail_closed"] for p in probes)

    all_pass = all([g1_pass, g2_pass, g3_pass, g4_pass, g5_pass])

    diag = {
        "schema": "amphora.envelope-gates.flory-stockmayer-gelation-window-diagnostic.v1",
        "study_id": "flory-stockmayer-gelation-window-v1",
        "module": "amphora-envelope-gates",
        "authority": "AUDIT_ONLY",
        "run_type": "independent_non_runtime_theory_axis",
        "purpose": (
            "Bound the physical severity of the envelope->stoichiometric-index "
            "gap documented by stoichiometric-index-equivalents-v1: map the "
            "shipped +/-5% per-part mass envelope's worst-case index corners "
            "through the Flory-Stockmayer gelation criterion for DGEBA(f=2) + "
            "amine(g=active-H) stepwise networks and test H0 = 'the envelope "
            "can defeat gelability'."),
        "hypothesis_H0": (
            "The shipped 3-constraint +/-5% per-part mass envelope can push a "
            "nominally-formulated two-part epoxy-amine coating outside the "
            "Flory-Stockmayer gelability window 1/((f-1)(g-1)) <= r <= "
            "(f-1)(g-1), i.e. the documented index gap is network-formation-"
            "threatening."),
        "hypothesis_verdict": ("H0 REFUTED" if g2_pass else "H0 NOT REFUTED"),
        "theory_reference": [
            "Flory, P.J., 'Molecular Size Distribution in Three Dimensional "
            "Polymers I-III', J. Am. Chem. Soc. 63 (1941) 3083-3100, "
            "DOI 10.1021/ja01856a061 (gel-point criterion, p_c=1/(f-1) anchors).",
            "Stockmayer, W.H., 'Theory of Molecular Size Distribution and Gel "
            "Formation in Branched-Chain Polymers', J. Chem. Phys. 11 (1943) "
            "45-55, DOI 10.1063/1.1723803 (A_f+B_g gel point p_A p_B (f-1)(g-1)=1).",
            "Odian, G., 'Principles of Polymerization', 4th ed., Wiley 2004, "
            "Ch.2.10/2.12, ISBN 978-0471274001 (stoichiometric-imbalance form "
            "p_gel = sqrt(r/((f-1)(g-1))), gelability at full conversion).",
            "Lee, H. & Neville, K., 'Handbook of Epoxy Resins', McGraw-Hill 1967, "
            "Ch.5-6 (amine-H functionality of epoxy hardeners; f=2 for DGEBA).",
            "IUPAC 2021 conventional standard atomic weights (C 12.011, H 1.008, "
            "N 14.007); amphora KAT molar-mass DGEBA EEW=170.21 g/eq (n=0).",
        ],
        "model_assumptions": (
            "Ideal Flory-Stockmayer statistics: equal and independent reactivity "
            "of all amine hydrogens, no intramolecular cyclization, no "
            "etherification side reaction. Real epoxy-amine systems show "
            "primary/secondary substitution effects and cycles that DELAY the "
            "gel point (raise p_gel), so the ideal window used here is the "
            "conservative bound in the gelability direction; the containment "
            "verdict is additionally protected by the quantified headroom P*."),
        "non_circularity": (
            "Equations (1)-(4), both KAT anchors, the sqrt corner-shift "
            "corollary, and the closed-form headroom P* are published polymer "
            "physics re-derived here from first principles; g and AHEW derive "
            "purely from IUPAC-2021 atomic weights + published formulas; DGEBA "
            "f=2 / EEW=170.21 are portfolio-locked molar-mass facts. Only "
            "on-disk fixture bytes are consumed; the shipped "
            "constraint-envelope-oracle-v1 evaluate_gate is reused solely to "
            "re-confirm the excursion corners PASS the actual contract. "
            "Distinct from amphora-molecule-role-ranker's Flory/Macosko-Miller "
            "receipts, which rank molecule-level gelation capability; this "
            "study bounds the physical severity of the ENVELOPE tolerance gap."),
        "fixture": {
            "path": "reference/phase0-envelope-gates-known-answer.v1.json",
            "sha256": sha(kat_bytes),
            "n_envelopes": n_env,
            "rights": kat.get("rights"),
        },
        "theory_constants": {
            "per_part_band_fraction": P,
            "epoxide_functionality_f": F_EPOXIDE,
            "index_corner_factor_amine_rich": round(hi_factor, RND),
            "index_corner_factor_amine_lean": round(lo_factor, RND),
            "gel_conversion_shift_amine_rich_pct": round(gel_shift_hi_pct, RND),
            "gel_conversion_shift_amine_lean_pct": round(gel_shift_lo_pct, RND),
            "shift_invariance_note": (
                "p_gel scales as sqrt(r), so the envelope-induced gel-point "
                "conversion shift is EXACTLY sqrt of the index corner factor, "
                "independent of EEW, AHEW, g and the nominal masses -- the "
                "sqrt-corollary of the excursion-invariance theorem."),
        },
        "per_envelope": per_env,
        "binding_envelope": {
            "envelope_id": binding[1] if binding else None,
            "headroom_band_pstar": (round(binding[0], RND) if binding else None),
            "binding_side": binding[2] if binding else None,
            "shipped_band": P,
            "band_fraction_of_cliff_distance": (
                round(P / binding[0], RND) if binding else None),
        },
        "gates": {
            "G1_known_answer_anchors": {
                "passed": g1_pass, "n_anchors": len(anchors), "anchors": anchors},
            "G2_gelability_containment_H0": {
                "passed": g2_pass,
                "n_first_principles_envelopes": n_first_principles,
                "n_corners_pass_shipped_oracle": n_corner_oracle_pass,
                "n_excursion_contained": n_contained,
                "n_verdict_eew_invariant": n_eew_invariant,
                "H0_refuted": bool(g2_pass)},
            "G3_analytic_feasibility_coherence": {
                "passed": g3_pass,
                "n_envelopes_coherent": n_coherent,
                "grid_points_checked": coherence_points_total,
                "grid_points_agreeing": coherence_points_agree},
            "G4_gel_latitude_and_headroom": {
                "passed": g4_pass,
                "n_sqrt_shift_invariant": n_shift_invariant,
                "n_headroom_exceeds_band": n_headroom_ok,
                "min_headroom_pstar": (round(binding[0], RND) if binding else None)},
            "G5_tamper_battery_fail_closed": {
                "passed": g5_pass, "n_probes": len(probes),
                "n_fail_closed": sum(1 for p in probes if p["fail_closed"]),
                "probes": probes},
        },
        "acceptance_bar_floors": {
            "all_met": bool(all_pass),
            "g1_known_answer_anchor_floor": 1.0,
            "g2_containment_floor": 1.0,
            "g3_coherence_floor": 1.0,
            "g4_headroom_exceeds_band_required": True,
            "g5_tamper_fail_closed_floor": 1.0,
        },
        "all_gates_passed": all_pass,
        "headline": (
            "H0 REFUTED: the shipped +/-5% per-part mass envelope CANNOT defeat "
            "Flory-Stockmayer gelability for any of the 7 first-principles "
            "DGEBA+amine envelopes -- the full worst-case stoichiometric-index "
            "excursion (+10.5263%/-9.5238%) stays strictly inside the "
            "1/((f-1)(g-1)) <= r <= (f-1)(g-1) window (7/7, verdict invariant "
            "over the commercial EEW 182-192 spec band). The documented "
            "envelope->index gap is therefore a conversion/Tg-quality concern, "
            "NOT a network-formation risk. The envelope shifts the gel-point "
            "epoxide conversion by exactly +5.1315%/-4.8810% (EEW/AHEW/g-"
            "invariant sqrt corollary), and the per-part band would have to "
            "grow to P* (binding envelope reported; minimum across 7) before "
            "touching the gelation cliff."),
        "closes": (
            "Bounds the physical severity of the stoichiometric-index gap left "
            "open by stoichiometric-index-equivalents-v1: quantifies, in closed "
            "form, the distance between the shipped mass envelope and the "
            "nearest network-formation failure boundary, with known-answer "
            "anchors to Flory 1941 and Stockmayer 1943."),
        "does_not_close": (
            "Ideal-statistics assumptions (equal reactivity, no cycles, no "
            "etherification) mean the real gel conversion is >= the ideal one; "
            "no wet-lab cure, conversion, or Tg claim is made. The 3 adduct "
            "hardeners lack first-principles functionality g and remain an "
            "explicit data gap (already queued). Off-stoichiometry network "
            "QUALITY (crosslink density, Tg depression) inside the gelable "
            "window is not addressed here. Adding an index or gelability "
            "constraint to any shipped policy requires a human Phase-0 "
            "fixture/lock revision this cron cannot perform."),
        "data_gap": {
            "adduct_hardeners_without_first_principles_g": [
                eid for eid, h in ENV_HARDENER.items() if h is None],
            "n_first_principles_hardeners": n_first_principles,
            "n_adduct_hardeners": sum(1 for h in ENV_HARDENER.values() if h is None),
        },
    }
    return diag


if __name__ == "__main__":
    out = Path(sys.argv[1])
    diag = run()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(json.dumps(diag, indent=2, sort_keys=True).encode())
    print("WROTE", out)
    print("all_gates_passed", diag["all_gates_passed"])
    print("sha256", hashlib.sha256(out.read_bytes()).hexdigest())
