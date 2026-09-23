#!/usr/bin/env python3
"""
amphora-cure-potlife-gate  --  Amine-class parsimony / robustness test of the
Arrhenius pot-life temperature-scaling model.

THEORY AXIS (option B).  The signed Phase-0 Arrhenius KPI
(evidence/phase0/kpis/cure-potlife-arrhenius-kpi.v1.json) predicts pot-life at
held-out temperatures with a PER-SYSTEM activation energy Ea (12 tuned constants,
one per hardener).  A skeptic can object that 12 free Ea makes the temperature
scaling look tuned rather than physical.

This harness asks two falsifiable questions using ONLY the already-signed truth
table (12 systems x {10,30,40} C published pot-life, from the signed
benchmark/result.v1.json) plus INDEPENDENT literature amine-class activation
energies:

  Gate A (class-consistency): does every per-system Ea fall inside the
    independently published Ea range for its amine class?
  Gate B (parsimony robustness): if we DISCARD the 12 tuned Ea and use only 5
    amine-class-characteristic Ea constants from the literature, does the
    held-out temperature extrapolation still pass the 0.20 MAPE ceiling?

Arrhenius:  pot_life(T) = pot_life_ref * exp[(Ea/R)*(1/T - 1/T_ref)]
  R = 8.31446261815324 J/(mol.K) (CODATA 2018); T_ref = 295.928 K (22.78 C).

Non-circularity: the class Ea central values and ranges are literature-typical
round constants (Prime in Turi 1997; Kamal & Sourour 1973; Blanco 2005), chosen
deliberately NOT equal to the per-system table means (aromatic 65 vs table-mean
63.67; mannich 46 vs 48; amidoamine 53 vs 53.5).  No value is fit to the 36
held-out points.
"""
import json, hashlib, sys
from pathlib import Path

R = 8.31446261815324
T_REF_K = 295.928  # 22.78 C

# Independent literature amine-class Arrhenius activation energies for DGEBA-amine
# cure (kJ/mol).  central = literature-typical; [lo,hi] = published class spread.
# Sources: Prime R.B. in Turi (ed.) Thermal Characterization of Polymeric
# Materials 2nd ed. 1997 Ch.8; Kamal & Sourour Polym Eng Sci 13:59 (1973);
# Riccardi/Adabbo/Williams J Appl Polym Sci 29:2481 (1984); Blanco et al.
# Polymer 46:7989 (2005).
CLASS_EA_KJ = {
    "aliphatic-polyamine": {"central": 55.0, "lo": 50.0, "hi": 58.0},
    "cycloaliphatic-amine": {"central": 60.0, "lo": 57.0, "hi": 65.0},
    "aromatic-amine":       {"central": 65.0, "lo": 58.0, "hi": 75.0},
    "amidoamine-adduct":    {"central": 53.0, "lo": 48.0, "hi": 58.0},
    "mannich-base":         {"central": 46.0, "lo": 42.0, "hi": 50.0},
}

def predict(ref_min, ea_j_mol, t_c):
    t_k = t_c + 273.15
    return ref_min * pow(2.718281828459045, (ea_j_mol / R) * (1.0 / t_k - 1.0 / T_REF_K))

def main(bench_path):
    bench = json.loads(Path(bench_path).read_text())
    recs = bench["records"]
    per_sys_ape, class_ape = [], []
    per_system_rows = []
    gateA_pass = 0
    for r in recs:
        fam = r["hardener_family"]
        ea_sys = float(r["activation_energy_j_mol"])
        ref = float(r["reference_pot_life_min_22_78c"])
        cl = CLASS_EA_KJ[fam]
        ea_class = cl["central"] * 1000.0
        in_range = (cl["lo"] * 1000.0) <= ea_sys <= (cl["hi"] * 1000.0)
        gateA_pass += 1 if in_range else 0
        sys_apes, cls_apes = [], []
        for h in r["held_out_temperatures"]:
            t_c = float(h["temperature_c"]); y = float(h["published_pot_life_min"])
            p_sys = predict(ref, ea_sys, t_c)
            p_cls = predict(ref, ea_class, t_c)
            a_sys = abs(p_sys - y) / y
            a_cls = abs(p_cls - y) / y
            per_sys_ape.append(a_sys); class_ape.append(a_cls)
            sys_apes.append(a_sys); cls_apes.append(a_cls)
        per_system_rows.append({
            "system_id": r["system_id"], "hardener_family": fam,
            "ea_per_system_kj_mol": round(ea_sys / 1000.0, 6),
            "ea_class_central_kj_mol": round(ea_class / 1000.0, 6),
            "ea_class_range_kj_mol": [cl["lo"], cl["hi"]],
            "per_system_ea_within_class_range": in_range,
            "mape_per_system_ea": round(sum(sys_apes) / len(sys_apes), 10),
            "mape_class_collapsed_ea": round(sum(cls_apes) / len(cls_apes), 10),
        })
    n = len(per_sys_ape)
    mape_sys = sum(per_sys_ape) / n
    mape_cls = sum(class_ape) / n
    ceiling = 0.20
    out = {
        "schema": "amphora.cure-potlife-gate.amine-class-parsimony-diagnostic.v1",
        "gas_constant_j_mol_k": R,
        "reference_temperature_k": T_REF_K,
        "held_out_temperatures_c": [10.0, 30.0, 40.0],
        "n_systems": len(recs),
        "n_held_out_points": n,
        "class_ea_literature_kj_mol": CLASS_EA_KJ,
        "gate_A_class_consistency": {
            "definition": "each per-system Ea lies within its independently published amine-class Ea range",
            "n_pass": gateA_pass, "n_total": len(recs),
            "all_pass": gateA_pass == len(recs),
        },
        "gate_B_parsimony_robustness": {
            "definition": "held-out MAPE using 5 literature class Ea constants (not 12 tuned Ea) stays <= 0.20",
            "mape_per_system_ea": round(mape_sys, 10),
            "mape_class_collapsed_ea": round(mape_cls, 10),
            "ceiling": ceiling,
            "mape_delta_class_minus_persystem": round(mape_cls - mape_sys, 10),
            "class_collapsed_passes_ceiling": mape_cls <= ceiling,
            "ea_degrees_of_freedom_per_system": len(recs),
            "ea_degrees_of_freedom_class": len(CLASS_EA_KJ),
        },
        "per_system": per_system_rows,
    }
    return out

if __name__ == "__main__":
    out = main(sys.argv[1])
    body = json.dumps(out, indent=2, sort_keys=True)
    Path(sys.argv[2]).write_text(body)
    print("SHA256", hashlib.sha256(body.encode()).hexdigest())
