#!/usr/bin/env python3
"""barrier-water-uptake-hydrophilicity-ccby-v1 -- AUDIT_ONLY red-team increment.

Two deliverables, one deterministic two-replay byte-stable diagnostic.

(A) PHASE-0 HONESTY RED-TEAM, recomputed LIVE from on-host governance state,
    directly answering the founder question "do we actually have FULL Phase-0?".
    Recomputed from config/program/phase0-decision-report.v2.json,
    module-manifest.json, and all 29 */evidence/phase0/benchmark/benchmark-lock
    files. Findings are computed, not asserted:
      * scientific_readiness == VALIDATED for 0 / 29 modules.
      * The 10 PHASE_0 modules are 7 NOT_APPLICABLE (governance/infra: no science
        object) + 3 LOCKED_INTERNAL (internal ceiling, not externally validated).
      * scientific_success_required_for_phase0 == false in ALL 29 benchmark-locks
        -> "Phase-0" is a GOVERNANCE gate, NOT a validated-science gate.
    Conclusion: "FULL Phase-0" does NOT mean "validated science"; this autonomous
    AUDIT_ONLY cron cannot promote any module (promotion needs two distinct
    trusted-human-key signatures it does not hold).

(B) A REAL NEW SCIENCE INCREMENT on the #1 marine-coating mission gap: the
    BARRIER-WATER axis (equilibrium water uptake of the cured film -- the driver
    of osmotic blistering and cathodic disbondment). We test the natural a-priori
    hypothesis "more hydrophilic (H-bonding) groups -> more water uptake" against
    real, rights-clean, protocol-controlled data and report an HONEST result.

    IN-SCOPE DATA (CC BY 4.0, already rights-established in-tree): three DGEBA
    networks cured with structurally different diamines under one immersion
    protocol, from Polymers 2024, 16(1):67 (doi 10.3390/polym16010067 =
    PMC10780492): equilibrium water uptake Q -- EP-CYDM 0.16 %, EP-DDS 1.7 %,
    EP-8CH2DA 2.0 %.

    A-PRIORI DESCRIPTORS (parameter-free, computed from stoichiometric cured
    network composition; NO fit to the water data -> non-circular):
      1. secondary-hydroxyl concentration  c_OH  [mol/kg]      (hydrophilicity)
      2. total polar-atom (O+N) concentration [mol/kg]         (hydrophilicity)
      3. flexible aliphatic -CH2- count in amine backbone      (free-volume proxy)

    HONEST FINDING: both hydrophilicity descriptors ANTI-correlate with the
    measured within-family uptake (Spearman rho = -0.5): the cycloaliphatic CYDM
    network, which has the HIGHEST hydroxyl density, has the LOWEST uptake. The
    controlling variable within one resin family is amine-backbone free volume /
    crosslink density (rigid cycloaliphatic packs tightest -> lowest; flexible
    octamethylene -> highest), which a static group-density descriptor omits.
    The free-volume proxy alone (rho = +0.5) captures the extreme but not the
    sulfone-polar DDS, so with n = 3 and >=2 competing physical effects the
    correct model is underdetermined. CROSS-CLASS POSITIVE CONTROL (canonical
    polymer physical constants, rank-only, NO coating claim): across polymer
    classes spanning >3 orders of magnitude of water uptake the same
    hydrophilicity (Hansen delta_h) descriptor DOES rank uptake (Spearman ~ 1),
    so the engine is valid at coarse resolution -- it is the WITHIN-family,
    design-relevant resolution that is model-and-data co-limited.

    VERDICT: the barrier-water-uptake axis cannot be promoted; a-priori
    group-density hydrophilicity is REFUTED for within-DGEBA-amine ranking and
    is free-volume-and-data co-limited (needs a validated free-volume/crosslink
    descriptor + protocol-controlled n>=~10) -- the same wall as network Tg.

HONESTY POSTURE: promotes nothing; signs no phase0 evaluation/review; modifies no
existing receipt, the manifest, or any of the 66 signed receipts. Deterministic,
two-replay byte-stable.
"""
import hashlib
import json
import math
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]


def sha(b):
    return hashlib.sha256(b).hexdigest()


def rnd(x, n=6):
    if isinstance(x, float):
        if math.isnan(x) or math.isinf(x):
            return None
        return round(x, n)
    if isinstance(x, dict):
        return {k: rnd(v, n) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [rnd(v, n) for v in x]
    return x


# --------------------------------------------------------------------------
# Spearman rank correlation (average ranks for ties), pure-python deterministic
# --------------------------------------------------------------------------
def _rank(vals):
    order = sorted(range(len(vals)), key=lambda i: vals[i])
    ranks = [0.0] * len(vals)
    i = 0
    while i < len(vals):
        j = i
        while j + 1 < len(vals) and vals[order[j + 1]] == vals[order[i]]:
            j += 1
        avg = (i + j) / 2.0 + 1.0  # 1-based average rank
        for k in range(i, j + 1):
            ranks[order[k]] = avg
        i = j + 1
    return ranks


def spearman(x, y):
    n = len(x)
    rx, ry = _rank(x), _rank(y)
    mx = sum(rx) / n
    my = sum(ry) / n
    cov = sum((rx[i] - mx) * (ry[i] - my) for i in range(n))
    vx = math.sqrt(sum((v - mx) ** 2 for v in rx))
    vy = math.sqrt(sum((v - my) ** 2 for v in ry))
    if vx == 0 or vy == 0:
        return 0.0
    return cov / (vx * vy)


# --------------------------------------------------------------------------
# (A) PHASE-0 HONESTY RED-TEAM -- recomputed live from on-host governance state
# --------------------------------------------------------------------------
def phase0_redteam():
    rep_path = REPO / "config/program/phase0-decision-report.v2.json"
    man_path = REPO / "module-manifest.json"
    rep_bytes = rep_path.read_bytes()
    man_bytes = man_path.read_bytes()
    rep = json.loads(rep_bytes)
    man = json.loads(man_bytes)

    mods = rep["modules"]
    by_phase = {}
    readiness = {}
    for m in mods:
        by_phase.setdefault(m["phase"], []).append(m)
        readiness[m["scientific_readiness"]] = readiness.get(m["scientific_readiness"], 0) + 1
    phase0 = sorted(by_phase.get("PHASE_0", []), key=lambda m: m["module_id"])

    def readiness_hist(ms):
        h = {}
        for m in ms:
            h[m["scientific_readiness"]] = h.get(m["scientific_readiness"], 0) + 1
        return dict(sorted(h.items()))

    # manifest-side readiness (independent artifact) -- must also show 0 VALIDATED
    man_readiness = {}
    for m in man["modules"]:
        man_readiness[m["scientific_readiness"]] = man_readiness.get(m["scientific_readiness"], 0) + 1

    # scan all 29 canonical benchmark-locks for the governance flag
    ssr_true = ssr_false = 0
    for lock in sorted(REPO.glob("*/evidence/phase0/benchmark/benchmark-lock.v1.json")):
        d = json.loads(lock.read_bytes())
        v = d.get("scientific_success_required_for_phase0", "ABSENT")
        if v is True:
            ssr_true += 1
        elif v is False:
            ssr_false += 1

    return {
        "inputs": {
            "phase0_decision_report_v2_sha256": sha(rep_bytes),
            "module_manifest_sha256": sha(man_bytes),
            "n_benchmark_locks_scanned": ssr_true + ssr_false,
        },
        "live_counts": {
            "module_count": rep.get("module_count"),
            "phase0_count": rep.get("phase0_count"),
            "pre_phase0_count": rep.get("pre_phase0_count"),
            "status": rep.get("status"),
        },
        "scientific_readiness_all_modules_decision_report": dict(sorted(readiness.items())),
        "scientific_readiness_all_modules_module_manifest": dict(sorted(man_readiness.items())),
        "n_modules_scientifically_VALIDATED": readiness.get("VALIDATED", 0),
        "phase0_modules_readiness_breakdown": readiness_hist(phase0),
        "benchmark_lock_governance": {
            "scientific_success_required_for_phase0__true": ssr_true,
            "scientific_success_required_for_phase0__false": ssr_false,
            "interpretation": (
                "Phase-0 is a GOVERNANCE gate: no benchmark-lock in the portfolio makes "
                "scientific success a precondition for Phase-0. 'FULL Phase-0' therefore "
                "does NOT mean 'validated science'."),
        },
        "founder_answer_do_we_have_full_phase0": (
            "NO in the scientific sense. 0 of 29 modules are scientific_readiness==VALIDATED; "
            "the 10 modules the report labels PHASE_0 are 7 NOT_APPLICABLE (pure "
            "governance/infra) + 3 LOCKED_INTERNAL (internal ceiling, not externally "
            "validated), and every one of the 29 benchmark-locks sets "
            "scientific_success_required_for_phase0=false. This autonomous AUDIT_ONLY cron "
            "cannot promote any module: promotion is derived only from a module-local "
            "movement event carrying two distinct trusted-human-key signatures, which it "
            "does not hold and must not forge."),
    }


# --------------------------------------------------------------------------
# (B) BARRIER-WATER-UPTAKE ENGINE
# --------------------------------------------------------------------------
# Atomic weights (IUPAC standard, embedded for byte-stability)
AW = {"C": 12.011, "H": 1.008, "N": 14.007, "O": 15.999, "S": 32.06}


def mw(formula):
    return sum(AW[el] * n for el, n in formula.items())


# DGEBA (bisphenol-A diglycidyl ether) C21H24O4; pure difunctional epoxide.
DGEBA = {"C": 21, "H": 24, "O": 4}
DGEBA_MW = mw(DGEBA)  # ~340.42; 2 epoxides -> 2 secondary -OH on cure; 2 aryl ether O.

# In-scope CC BY 4.0 dataset: three DGEBA + diamine networks, one immersion
# protocol. Polymers 2024, 16(1):67 (doi 10.3390/polym16010067 = PMC10780492).
# Q = measured equilibrium water uptake (wt %). Each diamine has 4 active N-H,
# so the stoichiometric cured repeat = 2 DGEBA + 1 diamine (4 epoxides consumed).
SYSTEMS = [
    # id, diamine formula, diamine type, flexible aliphatic -CH2- in N..N backbone, Q_meas_pct
    ("EP-DDS",    {"C": 12, "H": 12, "N": 2, "O": 2, "S": 1}, "aromatic",      0, 1.7),   # 4,4'-diaminodiphenylsulfone
    ("EP-CYDM",   {"C": 8,  "H": 18, "N": 2},                 "cycloaliphatic", 2, 0.16),  # 1,3-bis(aminomethyl)cyclohexane
    ("EP-8CH2DA", {"C": 8,  "H": 20, "N": 2},                 "aliphatic",      8, 2.0),   # 1,8-diaminooctane (octamethylenediamine)
]


def barrier_water_engine():
    rows = []
    for sid, dia, dtype, flex_ch2, q in SYSTEMS:
        dia_mw = mw(dia)
        repeat_mass_g = 2 * DGEBA_MW + dia_mw        # g per (2 DGEBA + 1 diamine)
        repeat_mass_kg = repeat_mass_g / 1000.0
        n_OH = 4                                     # 4 epoxides -> 4 secondary -OH
        # polar atoms (O + N): DGEBA contributes 4 O each (2 ether + 2 that become -OH);
        # diamine contributes its own O (sulfone) + N.
        n_polar = 2 * DGEBA["O"] + dia.get("O", 0) + dia.get("N", 0)
        c_OH = n_OH / repeat_mass_kg                 # mol/kg  (hydrophilicity)
        c_polar = n_polar / repeat_mass_kg           # mol/kg  (hydrophilicity)
        rows.append({
            "system": sid, "amine_type": dtype,
            "diamine_MW": dia_mw, "repeat_mass_g_per_2DGEBA_plus_diamine": repeat_mass_g,
            "n_secondary_OH": n_OH, "n_polar_atoms_O_plus_N": n_polar,
            "c_OH_mol_per_kg": c_OH, "c_polar_mol_per_kg": c_polar,
            "flexible_aliphatic_CH2_in_amine": flex_ch2,
            "Q_water_uptake_meas_pct": q,
        })

    q = [r["Q_water_uptake_meas_pct"] for r in rows]
    rho_cOH = spearman([r["c_OH_mol_per_kg"] for r in rows], q)
    rho_cpolar = spearman([r["c_polar_mol_per_kg"] for r in rows], q)
    rho_flex = spearman([r["flexible_aliphatic_CH2_in_amine"] for r in rows], q)

    VALIDATION_BAR = 0.9  # rank-validation threshold used elsewhere in the portfolio
    hydrophilicity_refuted = (rho_cOH < 0.0) and (rho_cpolar < 0.0)

    inscope = {
        "data_source": ("Polymers 2024, 16(1):67 (doi 10.3390/polym16010067 = PMC10780492), "
                        "CC BY 4.0, already rights-established in-tree. Equilibrium water "
                        "uptake Q of DGEBA cured with three structurally different diamines "
                        "under one immersion protocol."),
        "n_systems": len(rows),
        "rows": rows,
        "measured_uptake_order_low_to_high": "EP-CYDM 0.16% < EP-DDS 1.7% < EP-8CH2DA 2.0%",
        "spearman_vs_measured_uptake": {
            "c_OH_hydrophilicity": rho_cOH,
            "c_polar_hydrophilicity": rho_cpolar,
            "flexible_CH2_free_volume_proxy": rho_flex,
        },
        "validation_bar_spearman": VALIDATION_BAR,
        "hydrophilicity_group_density_REFUTED_within_family": hydrophilicity_refuted,
        "mechanism": (
            "Within a single DGEBA-amine resin family the two parameter-free hydrophilicity "
            "descriptors ANTI-correlate with uptake (rho=-0.5): the cycloaliphatic CYDM "
            "network has the HIGHEST hydroxyl density yet the LOWEST uptake. The controlling "
            "variable is amine-backbone free volume / crosslink density -- rigid cycloaliphatic "
            "CYDM packs tightest (0.16%), flexible octamethylene 8CH2DA opens the most free "
            "volume (2.0%), rigid aromatic-sulfone DDS is intermediate (1.7%). The free-volume "
            "proxy alone (rho=+0.5) captures the extreme but not the polar-sulfone DDS, so with "
            "n=3 and >=2 competing effects the model is underdetermined (not statistically "
            "significant at n=3 either way)."),
    }

    # CROSS-CLASS POSITIVE CONTROL -- canonical polymer physical constants, rank-only.
    # Representative handbook Hansen hydrogen-bonding parameter delta_h (MPa^0.5) and
    # typical equilibrium water uptake (wt %). Used ONLY to show the hydrophilicity
    # engine ranks uptake across polymer CLASSES; makes NO coating-performance claim.
    CROSS_CLASS = [
        ("PTFE",    0.0,  0.01),
        ("PS",      2.8,  0.05),
        ("PMMA",    7.5,  0.4),
        ("PA6",    12.0,  9.5),
        ("PVOH",   26.0, 40.0),
    ]
    cc_dh = [c[1] for c in CROSS_CLASS]
    cc_wu = [c[2] for c in CROSS_CLASS]
    rho_cross = spearman(cc_dh, cc_wu)
    cross_control = {
        "note": ("Canonical polymer physical constants (representative handbook values), "
                 "rank-only positive control. NO coating-performance claim; the in-scope "
                 "scientific claim is the DGEBA-amine within-family result above."),
        "rows": [{"polymer": p, "delta_h_MPa_half": dh, "typ_water_uptake_pct": wu}
                 for p, dh, wu in CROSS_CLASS],
        "spearman_delta_h_vs_uptake": rho_cross,
        "engine_valid_cross_class": rho_cross >= VALIDATION_BAR,
    }

    verdict = (
        "BARRIER_WATER_UPTAKE__HYDROPHILICITY_RANK_VALID_CROSS_CLASS__"
        "WITHIN_DGEBA_AMINE_GROUP_DENSITY_REFUTED_FREE_VOLUME_AND_DATA_CO_LIMITED: "
        "a-priori hydrophilic-group density (c_OH, c_polar) ranks equilibrium water uptake "
        "across polymer classes (cross-class Spearman %.2f) but ANTI-correlates within the "
        "in-scope DGEBA-amine family (Spearman %.2f, n=3), where free volume / crosslink "
        "density dominates. The barrier-water axis cannot be promoted; it needs a validated "
        "free-volume/crosslink descriptor plus protocol-controlled n>=~10 -- the same wall "
        "as network Tg." % (rho_cross, rho_cOH))

    return {
        "theory": (
            "Equilibrium water uptake of a polymer film is set by the balance of (i) "
            "hydrophilic H-bonding-group affinity (well captured across polymer classes by "
            "the Hansen hydrogen-bonding parameter delta_h / polar-group concentration) and "
            "(ii) accessible free volume / crosslink density that hosts sorbed and clustered "
            "water. This is the barrier property governing marine osmotic blistering and "
            "cathodic disbondment."),
        "in_scope_dgeba_amine": inscope,
        "cross_class_positive_control": cross_control,
        "verdict": verdict,
    }


def main(out_path):
    diag = {
        "schema": "amphora.redteam-audit.barrier-water-uptake-hydrophilicity.diagnostic.v1",
        "authority": "AUDIT_ONLY",
        "target_module": "amphora-barrier-corrosion-score",
        "target_capability": "equilibrium water uptake / barrier-water transport of the cured film",
        "target_kpi_id": "barrier-water-uptake-hydrophilicity-rank-v1",
        "predecessor": "owk-adhesion-and-phase0-redteam-v1",
        "phase0_reconciliation_redteam": phase0_redteam(),
        "barrier_water_uptake_engine": barrier_water_engine(),
        "coating_application": (
            "Marine two-part epoxy-amine anti-corrosion films: equilibrium water uptake is "
            "the primary driver of osmotic blistering and cathodic-disbondment kinetics. This "
            "increment establishes the physics engine and, more importantly, RED-TEAMS the "
            "naive a-priori model against real CC BY 4.0 protocol-controlled data, proving the "
            "axis is not promotable yet and stating exactly what it needs."),
        "does_not": [
            "promote any module or authority tier",
            "modify the manifest or any of the 66 signed receipts",
            "sign any phase0 evaluation or review receipt",
            "make any coating-performance or service-life claim",
            "claim statistical significance at n=3",
        ],
    }
    diag = rnd(diag, 6)
    body = json.dumps(diag, indent=2, sort_keys=True).encode()
    Path(out_path).write_bytes(body)
    print("WROTE", out_path)
    print("diagnostic_sha256", sha(body))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "diagnostic.canonical.json")
