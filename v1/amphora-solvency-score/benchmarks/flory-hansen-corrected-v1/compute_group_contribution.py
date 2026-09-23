#!/usr/bin/env python3
"""flory-hansen-corrected-v1 -- corrected, committed, tested group-contribution
instrument for Fedors 1974 (Hildebrand delta_total) and Hoftyzer/Van Krevelen
(Hansen delta_d / delta_p / delta_h) solubility parameters.

REPAIR ITEM: R-B03 (repair_mode interactive-2026-08-03).

This instrument supersedes the UNCOMMITTED Python generator behind the two
refuted receipts
  reference/mvp20/data/omg_chi_flory_huggins_physical_baseline_receipt.v1.json
  reference/mvp20/data/omg_chi_hansen_3component_physical_baseline_receipt.v1.json
whose delta values reached 5.155e9 MPa^0.5 (FH) and 5.33e17 MPa^0.5 (Hansen)
via denominator collapse delta = sqrt(sum dE_i / sum dV_i) with sum dV_i -> 0
(W7 audit, evidence/audit/flory-hansen-physical-admissibility-v1/, verdict
CLAIM_REFUTED).

Corrected-instrument guarantees (the three defects W7 root-caused are each
closed by an explicit, tested gate):

  (a) EXPLICIT GROUP COVERAGE. Every heavy atom of the molecule must be
      claimed by exactly one group in the declared lookup table below. Any
      unmatched atom/fragment => molecule REJECTED with
      reason "uncovered_fragment". There is NO silent-zero fallback for
      unknown chemistry (the W7 failure mode: unmatched fragments silently
      contributed dV_i = 0, collapsing the denominator).

  (b) HARD VOLUME FLOOR. Before ANY division, sum dV_i >= EPS_VOLUME_CM3
      (1.0 cm3/mol) is asserted. Fedors CH (-1.0) and quaternary C (-19.2)
      group volumes are negative, so a pathological group multiset can drive
      sum dV_i to ~0 or below; such molecules ABSTAIN with reason
      "volume_floor" and no value is ever computed or returned.

  (c) PER-MOLECULE ADMISSIBILITY ENVELOPE. Envelope [9.6, 59.875] MPa^0.5
      per the W7 audit (Barton 1991 CRC Handbook; Hansen 2007 Handbook 2nd
      ed. Table A.1; [12.0*0.8, 47.9*1.25]). Application map (documented,
      matching the physical meaning of the envelope, which is derived from
      TOTAL solubility-parameter magnitudes):
        - Fedors delta_total          : two-sided  [9.6, 59.875]
        - Hansen delta_total          : two-sided  [9.6, 59.875]
        - Hansen delta_d              : two-sided  [9.6, 59.875]
          (dispersion dominates the total; every real molecule in Hansen
          2007 Table A.1 has delta_d in ~[12, 21])
        - Hansen delta_p, delta_h     : one-sided  [0, 59.875]
          (polar / H-bond components are legitimately ~0 for alkanes --
          Hansen 2007 Table A.1 tabulates delta_p = 0.0 for n-hexane --
          so only the ceiling binds; they are >= 0 by construction)
      Any violation => ABSTAINED with reason "out_of_envelope"; the value is
      NEVER returned.

Method sources (same references the refuted receipts cited):
  - Fedors, R.F. 1974, Polym. Eng. Sci. 14(2):147 -- group E_coh (J/mol) and
    V (cm3/mol); delta_total = sqrt(sum E_i / sum V_i)  [MPa^0.5].
  - Hoftyzer/Van Krevelen 1976; Van Krevelen 1990 "Properties of Polymers"
    Ch. 7 (Table 7.3/7.8) -- F_d (MPa^0.5 cm3/mol), F_p (MPa^0.5 cm3/mol),
    E_h (J/mol):
        delta_d = sum F_d,i / V
        delta_p = sqrt(sum F_p,i^2) / V     (quadratic accumulation)
        delta_h = sqrt(sum E_h,i / V)
    V is taken as the Fedors group-contribution molar volume (documented
    choice; density data are unavailable for hypothetical structures).
  - Aromatic carbon atomic values are the EXACT linear decomposition of the
    published phenyl (31940 J/mol, 71.4 cm3/mol; F_d 1430, F_p 110)
    and phenylene (31940, 52.4; F_d 1270, F_p 110) group values:
        aromatic CH : E 5323.333, V 15.0667 ; F_d 265
        aromatic C  : E 5323.333, V -3.9333 ; F_d 105
    F_p is accumulated as ONE 110-component per aromatic ring (the published
    table assigns F_p per ring-level group, and delta_p sums squares, so a
    per-atom split would be mathematically wrong).
  - Composite groups (amides, water=2xOH) are documented compositions of
    published groups; VK blank table cells are declared zeros (EXPLICIT in
    the table below -- never a silent fallback).
  - Groups with no defensible Hoftyzer/VK constants carry vk=None: Fedors
    delta_total is still computable, but Hansen components are REJECTED with
    reason "vk_constants_unavailable" (never guessed).

Anchor molecules and documented tolerances (Hansen 2007 Table A.1):
  quantity                     reference        tolerance
  Fedors delta_total, toluene/ethanol/acetone   +/-10 % relative
  Fedors delta_total, water                     +/-15 % relative (water is
      the documented worst case for group contribution: strongly associated
      liquid; Hansen 2007 Ch. 1 treats water as exceptional)
  VK delta_d/p/h, toluene/ethanol/acetone       +/-10 % relative when the
      reference value >= 7.5 MPa^0.5, else +/-2.5 MPa^0.5 absolute (group
      contribution is not meaningful at sub-percent absolute precision for
      near-zero components)
  VK components, water                          expected ABSTAINED
      out_of_envelope (2xOH composition overshoots delta_total ceiling --
      the admissibility gate correctly refuses to return it)

Determinism: pure function of the input SMILES; RDKit canonical processing;
patterns applied in fixed declared order; matches sorted; no RNG.
"""
import json
import math
from collections import OrderedDict

from rdkit import Chem
from rdkit import RDLogger

RDLogger.DisableLog("rdApp.*")

SCHEMA = "amphora.solvency-score.flory-hansen-corrected-instrument.v1"

# --- gate (b): hard volume floor, cm3/mol, asserted BEFORE any division ---
EPS_VOLUME_CM3 = 1.0

# --- gate (c): admissibility envelope, MPa^0.5 (W7: [12.0*0.8, 47.9*1.25]) ---
ENVELOPE_MIN = 12.0 * 0.8    # 9.6
ENVELOPE_MAX = 47.9 * 1.25   # 59.875

# statuses
RETURNED = "RETURNED"
ABSTAINED_VOLUME_FLOOR = "ABSTAINED_VOLUME_FLOOR"
ABSTAINED_OUT_OF_ENVELOPE = "ABSTAINED_OUT_OF_ENVELOPE"
ABSTAINED_NONFINITE = "ABSTAINED_NONFINITE"
REJECTED_PARSE_ERROR = "REJECTED_PARSE_ERROR"
REJECTED_UNCOVERED_FRAGMENT = "REJECTED_UNCOVERED_FRAGMENT"
REJECTED_VK_CONSTANTS_UNAVAILABLE = "REJECTED_VK_CONSTANTS_UNAVAILABLE"

# ---------------------------------------------------------------------------
# Group table. Order matters: earlier patterns claim their atoms first; a
# match instance is applied only if ALL its atoms are still unclaimed.
# Each entry: (name, SMARTS, (E_fedors_J_mol, V_fedors_cm3_mol),
#              vk = (F_d, [F_p components], E_h) or None)
# ---------------------------------------------------------------------------
GROUP_TABLE = [
    # acyl-containing multi-atom groups first
    ("carboxylic_acid", "[CX3](=[OX1])[OX2H1]", (27630.0, 28.5),
     (530.0, [420.0], 10000.0)),
    ("ester", "[CX3](=[OX1])[OX2H0]", (18000.0, 18.0),
     (390.0, [490.0], 7000.0)),
    ("amide_primary", "[CX3](=[OX1])[NX3H2]", (41860.0, 17.5),
     (570.0, [770.0], 10400.0)),     # composition CO + NH2 (documented)
    ("amide_secondary", "[CX3](=[OX1])[NX3H1]", (33490.0, 9.5),
     (450.0, [770.0, 210.0], 5100.0)),  # composition CO + NH (documented)
    ("amide_tertiary", "[CX3](=[OX1])[NX3H0]", (29260.0, -7.7),
     (310.0, [770.0, 800.0], 7000.0)),  # composition CO + N< (documented)
    ("isocyanate", "[NX2]=[CX2]=[OX1]", (28460.0, 35.0), None),
    ("aldehyde", "[CX3H1](=[OX1])", (21350.0, 22.3),
     (470.0, [800.0], 4500.0)),
    ("ketone_carbonyl", "[CX3](=[OX1])", (17370.0, 10.8),
     (290.0, [770.0], 2000.0)),
    ("nitrile", "[CX2]#[NX1]", (25530.0, 24.0),
     (430.0, [1100.0], 2500.0)),
    ("nitro_neutral", "[NX3](=[OX1])=[OX1]", (15360.0, 24.0),
     (500.0, [1070.0], 1500.0)),
    ("nitro_charged", "[NX3+](=[OX1])[OX1-]", (15360.0, 24.0),
     (500.0, [1070.0], 1500.0)),
    # water BEFORE hydroxyl ([OX2H2] would otherwise stay uncovered)
    ("water_2xOH", "[OX2H2]", (59600.0, 20.0),
     (420.0, [500.0, 500.0], 40000.0)),   # composition 2 x OH (documented)
    ("hydroxyl", "[OX2H1]", (29800.0, 10.0),
     (210.0, [500.0], 20000.0)),
    ("ether_O", "[OX2H0]", (3350.0, 3.8),
     (100.0, [400.0], 3000.0)),
    ("aromatic_O", "[o]", (3350.0, 3.8),
     (100.0, [400.0], 3000.0)),
    ("amine_primary", "[NX3H2]", (12560.0, 19.2),
     (280.0, [0.0], 8400.0)),
    ("amine_secondary", "[NX3H1]", (8370.0, 4.5),
     (160.0, [210.0], 3100.0)),
    ("amine_tertiary", "[NX3H0]", (4190.0, -9.0),
     (20.0, [800.0], 5000.0)),
    ("aromatic_N_pyridine", "[nX2]", (11720.0, 5.0),
     (20.0, [800.0], 5000.0)),          # VK: N< values (documented approx.)
    ("aromatic_NH_pyrrole", "[nX3H1]", (8370.0, 4.5),
     (160.0, [210.0], 3100.0)),
    ("aromatic_N_subst", "[nX3H0]", (4190.0, -9.0),
     (20.0, [800.0], 5000.0)),
    ("imine_N", "[NX2;$([NX2]=[#6])]", (11720.0, 5.0), None),
    ("thiol_SH", "[SX2H]", (14440.0, 28.5), None),
    ("thioether_S", "[SX2H0]", (14150.0, 12.0),
     (440.0, [0.0], 0.0)),              # VK blanks declared zero (explicit)
    ("aromatic_S", "[s]", (14150.0, 12.0),
     (440.0, [0.0], 0.0)),
    ("fluorine", "[F]", (4190.0, 18.0),
     (220.0, [0.0], 0.0)),              # VK blanks declared zero (explicit)
    ("chlorine", "[Cl]", (11550.0, 24.0),
     (450.0, [550.0], 400.0)),
    ("bromine", "[Br]", (15490.0, 30.0),
     (550.0, [0.0], 0.0)),              # VK blanks declared zero (explicit)
    ("iodine", "[I]", (19050.0, 31.5), None),
    ("alkyne_CH", "[CX2H1;$([CX2H1]#[#6])]", (3850.0, 27.4), None),
    ("alkyne_C", "[CX2H0;$([CX2H0]#[#6])]", (7070.0, 6.5), None),
    # aromatic carbons: exact decomposition of phenyl/phenylene (see header)
    ("aromatic_CH", "[cH1]", (31940.0 / 6.0, 15.066667),
     (265.0, [], 0.0)),
    ("aromatic_C_subst", "[cH0]", (31940.0 / 6.0, -3.933333),
     (105.0, [], 0.0)),
    # aliphatic carbons (acyl carbons were already claimed above)
    ("CH3", "[CX4H3]", (4710.0, 33.5), (420.0, [0.0], 0.0)),
    ("CH2", "[CX4H2]", (4940.0, 16.1), (270.0, [0.0], 0.0)),
    ("CH", "[CX4H1]", (3430.0, -1.0), (80.0, [0.0], 0.0)),
    ("C_quaternary", "[CX4H0]", (1470.0, -19.2), (-70.0, [0.0], 0.0)),
    ("vinyl_CH2", "[CX3H2]", (4310.0, 28.5), (400.0, [0.0], 0.0)),
    ("vinyl_CH", "[CX3H1]", (4310.0, 13.5), (200.0, [0.0], 0.0)),
    ("vinyl_C", "[CX3H0]", (4310.0, -5.5), (70.0, [0.0], 0.0)),
]

# structural (non-atom-claiming) corrections
RING_NONAROMATIC_5PLUS = ("ring_nonaromatic_5plus", (1050.0, 16.0),
                          (190.0, [], 0.0))
RING_NONAROMATIC_3_4 = ("ring_nonaromatic_3_4", (3140.0, 18.0),
                        (190.0, [], 0.0))
AROMATIC_RING_FP = 110.0  # one F_p component per aromatic ring (see header)

_COMPILED = None


def _compiled_table():
    global _COMPILED
    if _COMPILED is None:
        _COMPILED = [(name, Chem.MolFromSmarts(sm), fed, vk)
                     for (name, sm, fed, vk) in GROUP_TABLE]
        for name, patt, _, _ in _COMPILED:
            if patt is None:
                raise RuntimeError("bad SMARTS for group %s" % name)
    return _COMPILED


def assign_groups(smiles):
    """Assign every heavy atom to exactly one group.

    Returns (groups, ring_corrections, n_aromatic_rings, error_reason).
    groups: OrderedDict name -> count. error_reason is None on success,
    else 'parse_error' or 'uncovered_fragment:<detail>'.
    """
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None, None, 0, "parse_error"
    n_heavy = mol.GetNumAtoms()
    claimed = [False] * n_heavy
    groups = OrderedDict()
    for name, patt, _fed, _vk in _compiled_table():
        matches = sorted(mol.GetSubstructMatches(patt))
        for match in matches:
            if any(claimed[i] for i in match):
                continue  # atoms already claimed by a higher-priority group
            for i in match:
                claimed[i] = True
            groups[name] = groups.get(name, 0) + 1
    if not all(claimed):
        unclaimed = [mol.GetAtomWithIdx(i).GetSymbol()
                     for i in range(n_heavy) if not claimed[i]]
        return None, None, 0, "uncovered_fragment:" + ",".join(sorted(set(unclaimed)))
    # ring corrections
    ring_corrections = OrderedDict()
    n_aromatic_rings = 0
    for ring in mol.GetRingInfo().AtomRings():
        if all(mol.GetAtomWithIdx(i).GetIsAromatic() for i in ring):
            n_aromatic_rings += 1
        elif len(ring) >= 5:
            k = RING_NONAROMATIC_5PLUS[0]
            ring_corrections[k] = ring_corrections.get(k, 0) + 1
        else:
            k = RING_NONAROMATIC_3_4[0]
            ring_corrections[k] = ring_corrections.get(k, 0) + 1
    return groups, ring_corrections, n_aromatic_rings, None


def _lookup():
    d = {}
    for name, _sm, fed, vk in GROUP_TABLE:
        d[name] = (fed, vk)
    for name, fed, vk in (RING_NONAROMATIC_5PLUS, RING_NONAROMATIC_3_4):
        d[name] = (fed, vk)
    return d


def compute_from_groups(groups, ring_corrections=None, n_aromatic_rings=0):
    """Core computation from a group multiset. Applies gates (b) and (c).

    Returns dict:
      fedors_status, hansen_status, values (None unless RETURNED for that
      method), sum_V_cm3_mol, reasons.
    NEVER divides before the volume floor is checked; NEVER returns an
    out-of-envelope value.
    """
    table = _lookup()
    ring_corrections = ring_corrections or {}
    all_items = list(groups.items()) + list(ring_corrections.items())

    vk_available = True
    E_fed = 0.0
    V = 0.0
    Fd = 0.0
    Fp_sq = 0.0
    Eh = 0.0
    for name, count in all_items:
        fed, vk = table[name]
        E_fed += fed[0] * count
        V += fed[1] * count
        if vk is None:
            vk_available = False
        else:
            Fd += vk[0] * count
            for comp in vk[1]:
                Fp_sq += (comp * comp) * count
            Eh += vk[2] * count
    Fp_sq += (AROMATIC_RING_FP * AROMATIC_RING_FP) * n_aromatic_rings

    out = {
        "sum_V_cm3_mol": V,
        "fedors_status": None, "hansen_status": None,
        "fedors_reason": None, "hansen_reason": None,
        "values": {},
    }

    # gate (b): hard volume floor BEFORE any division
    if not (V >= EPS_VOLUME_CM3):
        out["fedors_status"] = ABSTAINED_VOLUME_FLOOR
        out["fedors_reason"] = (
            "volume_floor: sum dV_i = %.6g cm3/mol < %.1f" % (V, EPS_VOLUME_CM3))
        out["hansen_status"] = ABSTAINED_VOLUME_FLOOR
        out["hansen_reason"] = out["fedors_reason"]
        return out

    # ---- Fedors delta_total ----
    delta_fed = math.sqrt(max(E_fed, 0.0) / V)
    if not math.isfinite(delta_fed):
        out["fedors_status"] = ABSTAINED_NONFINITE
        out["fedors_reason"] = "nonfinite_value"
    elif not (ENVELOPE_MIN <= delta_fed <= ENVELOPE_MAX):
        out["fedors_status"] = ABSTAINED_OUT_OF_ENVELOPE
        out["fedors_reason"] = (
            "out_of_envelope: fedors_delta_total %.4f not in [%.3f, %.3f]"
            % (delta_fed, ENVELOPE_MIN, ENVELOPE_MAX))
    else:
        out["fedors_status"] = RETURNED
        out["values"]["fedors_delta_total"] = delta_fed

    # ---- Hoftyzer/Van Krevelen delta_d / delta_p / delta_h ----
    if not vk_available:
        out["hansen_status"] = REJECTED_VK_CONSTANTS_UNAVAILABLE
        out["hansen_reason"] = "vk_constants_unavailable"
        return out
    delta_d = Fd / V
    delta_p = math.sqrt(Fp_sq) / V
    delta_h = math.sqrt(max(Eh, 0.0) / V)
    delta_t = math.sqrt(delta_d * delta_d + delta_p * delta_p
                        + delta_h * delta_h)
    if not all(math.isfinite(x) for x in (delta_d, delta_p, delta_h, delta_t)):
        out["hansen_status"] = ABSTAINED_NONFINITE
        out["hansen_reason"] = "nonfinite_value"
        return out
    violations = []
    if not (ENVELOPE_MIN <= delta_d <= ENVELOPE_MAX):
        violations.append("delta_d %.4f not in [%.3f, %.3f]"
                          % (delta_d, ENVELOPE_MIN, ENVELOPE_MAX))
    if not (0.0 <= delta_p <= ENVELOPE_MAX):
        violations.append("delta_p %.4f not in [0, %.3f]"
                          % (delta_p, ENVELOPE_MAX))
    if not (0.0 <= delta_h <= ENVELOPE_MAX):
        violations.append("delta_h %.4f not in [0, %.3f]"
                          % (delta_h, ENVELOPE_MAX))
    if not (ENVELOPE_MIN <= delta_t <= ENVELOPE_MAX):
        violations.append("delta_total %.4f not in [%.3f, %.3f]"
                          % (delta_t, ENVELOPE_MIN, ENVELOPE_MAX))
    if violations:
        out["hansen_status"] = ABSTAINED_OUT_OF_ENVELOPE
        out["hansen_reason"] = "out_of_envelope: " + "; ".join(violations)
    else:
        out["hansen_status"] = RETURNED
        out["values"]["hansen_delta_d"] = delta_d
        out["values"]["hansen_delta_p"] = delta_p
        out["values"]["hansen_delta_h"] = delta_h
        out["values"]["hansen_delta_total"] = delta_t
    return out


def compute(smiles):
    """Full pipeline for one SMILES. Applies gates (a), (b), (c)."""
    groups, ring_corr, n_arom, err = assign_groups(smiles)
    if err == "parse_error":
        return {
            "smiles": smiles,
            "fedors_status": REJECTED_PARSE_ERROR,
            "hansen_status": REJECTED_PARSE_ERROR,
            "fedors_reason": "parse_error", "hansen_reason": "parse_error",
            "values": {}, "groups": None,
        }
    if err is not None:  # gate (a): uncovered fragment -> REJECTED
        return {
            "smiles": smiles,
            "fedors_status": REJECTED_UNCOVERED_FRAGMENT,
            "hansen_status": REJECTED_UNCOVERED_FRAGMENT,
            "fedors_reason": err, "hansen_reason": err,
            "values": {}, "groups": None,
        }
    out = compute_from_groups(groups, ring_corr, n_arom)
    out["smiles"] = smiles
    out["groups"] = dict(groups)
    out["ring_corrections"] = dict(ring_corr)
    out["n_aromatic_rings"] = n_arom
    return out


# --- anchor definitions (Hansen 2007 Handbook 2nd ed. Table A.1) ------------
ANCHORS = {
    "toluene": {"smiles": "Cc1ccccc1",
                "delta_d": 18.0, "delta_p": 1.4, "delta_h": 2.0,
                "delta_total": 18.165, "fedors_rel_tol": 0.10},
    "ethanol": {"smiles": "CCO",
                "delta_d": 15.8, "delta_p": 8.8, "delta_h": 19.4,
                "delta_total": 26.52, "fedors_rel_tol": 0.10},
    "acetone": {"smiles": "CC(C)=O",
                "delta_d": 15.5, "delta_p": 10.4, "delta_h": 7.0,
                "delta_total": 19.94, "fedors_rel_tol": 0.10},
    "water": {"smiles": "O",
              "delta_d": 15.5, "delta_p": 16.0, "delta_h": 42.3,
              "delta_total": 47.81, "fedors_rel_tol": 0.15,
              "hansen_expected_status": ABSTAINED_OUT_OF_ENVELOPE},
}
VK_COMPONENT_REL_TOL = 0.10       # when reference >= 7.5 MPa^0.5
VK_COMPONENT_ABS_TOL = 2.5        # when reference <  7.5 MPa^0.5
VK_COMPONENT_ABS_SWITCH = 7.5


def canonical_json(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


if __name__ == "__main__":
    import sys
    for smi in sys.argv[1:]:
        print(canonical_json(compute(smi)))
