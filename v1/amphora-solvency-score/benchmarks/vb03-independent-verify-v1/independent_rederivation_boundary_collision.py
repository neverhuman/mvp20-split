#!/usr/bin/env python3
"""Independent V-B03 verify attack against R-B03 corrected instrument.

Attacks:
  A. Independent re-derivation of Fedors delta_total for the 4 anchors from
     PUBLISHED Fedors 1974 group tables (typed in independently here, not
     imported from the instrument), cross-checked against both the
     instrument's computed value AND the Hansen 2007 Table A.1 reference.
  B. Adjacent-stress pathological-group search: enumerate combinations of
     negative-volume groups (CH, quaternary C, aromatic_C_subst, vinyl_C)
     with small positive-volume padding to find any combination that
     produces sum_V strictly between 0 and EPS_VOLUME_CM3 that ALSO clears
     gate (b) due to a floating point boundary bug, or any RETURNED value
     that is actually out-of-envelope (gate ordering bug).
  D. Greedy-claim order stress: molecules where two different groups could
     plausibly compete for the same atoms (e.g. amide vs ester+amine
     collision, thioether vs aromatic S) to check the "first-match-wins"
     priority does not silently misassign a group in a way that produces
     a wrong-but-in-envelope value (undetectable by the envelope gate).
"""
import sys, json, math, random
sys.path.insert(0, "/home/ubuntu/amphora/build/mvp20-split/amphora-solvency-score/benchmarks/flory-hansen-corrected-v1")
import compute_group_contribution as gc

results = {}

def independent_fedors(E_sum, V_sum):
    return math.sqrt(E_sum / V_sum)

anchors_independent = {}

E = 4710.0 + 5*(31940.0/6.0) + 1*(31940.0/6.0)
V = 33.5 + 5*15.066667 + 1*(-3.933333)
anchors_independent["toluene"] = independent_fedors(E, V)

E = 4710.0 + 4940.0 + 29800.0
V = 33.5 + 16.1 + 10.0
anchors_independent["ethanol"] = independent_fedors(E, V)

E = 4710.0*2 + 17370.0
V = 33.5*2 + 10.8
anchors_independent["acetone"] = independent_fedors(E, V)

E = 29800.0*2
V = 10.0*2
anchors_independent["water"] = independent_fedors(E, V)

ref_handbook = {
    "toluene": 18.165, "ethanol": 26.52, "acetone": 19.94, "water": 47.81,
}
tol = {"toluene": 0.10, "ethanol": 0.10, "acetone": 0.10, "water": 0.15}

attack_a = {}
for name, val in anchors_independent.items():
    inst = gc.compute(gc.ANCHORS[name]["smiles"])["values"]["fedors_delta_total"]
    ref = ref_handbook[name]
    rel_to_handbook = abs(val - ref) / ref
    rel_to_instrument = abs(val - inst) / inst
    attack_a[name] = {
        "independent_recompute_delta_total": round(val, 4),
        "instrument_delta_total": round(inst, 4),
        "handbook_reference": ref,
        "rel_err_independent_vs_handbook": round(rel_to_handbook, 4),
        "rel_err_independent_vs_instrument": round(rel_to_instrument, 6),
        "tol": tol[name],
        "PASS_vs_handbook": rel_to_handbook <= tol[name],
        "PASS_matches_instrument_exactly": rel_to_instrument < 1e-9,
    }
results["attack_a_independent_rederivation"] = attack_a

neg_groups = ["CH", "C_quaternary", "aromatic_C_subst", "vinyl_C"]
pos_groups = ["CH3", "CH2", "hydroxyl", "ether_O", "aromatic_CH"]
boundary_hits = []
out_of_envelope_leak = []
rng = random.Random(20260805)
for trial in range(20000):
    g = {}
    for _ in range(rng.randint(1, 6)):
        name = rng.choice(neg_groups + pos_groups)
        g[name] = g.get(name, 0) + 1
    if not g:
        continue
    r = gc.compute_from_groups(g)
    V = r["sum_V_cm3_mol"]
    if 0.0 < V < gc.EPS_VOLUME_CM3 and r["fedors_status"] != gc.ABSTAINED_VOLUME_FLOOR:
        boundary_hits.append({"groups": g, "V": V, "status": r["fedors_status"]})
    for k, v in r["values"].items():
        lo, hi = (0.0, gc.ENVELOPE_MAX) if k in ("hansen_delta_p", "hansen_delta_h") else (gc.ENVELOPE_MIN, gc.ENVELOPE_MAX)
        if not (lo <= v <= hi):
            out_of_envelope_leak.append({"groups": g, "key": k, "value": v})
results["attack_b_boundary_search"] = {
    "n_trials": 20000,
    "seed": 20260805,
    "volume_floor_gate_bypassed": len(boundary_hits),
    "out_of_envelope_value_leaked_past_gate_c": len(out_of_envelope_leak),
    "boundary_hits_sample": boundary_hits[:5],
    "leak_sample": out_of_envelope_leak[:5],
}

collision_smiles = [
    ("amide_vs_ester_amine", "CC(=O)NCC(=O)OC"),
    ("thioether_vs_aromatic_S", "c1ccc(SC)cc1"),
    ("secondary_amide_vs_tertiary_amine", "CN(C)C(C)=O"),
    ("nitrile_vs_amine", "N#CCCN"),
    ("carboxylic_acid_vs_ester_diacid", "OC(=O)CCC(=O)OC"),
    ("pyridine_vs_pyrrole_fused", "c1ccc2[nH]ccc2n1"),
    ("isocyanate_vs_amide", "O=C=NCCC(=O)N"),
    ("guanidine_like_multi_N", "NC(=N)NC(=N)N"),
]
attack_d = {}
for label, smi in collision_smiles:
    r = gc.compute(smi)
    attack_d[label] = {
        "smiles": smi,
        "groups": r.get("groups"),
        "fedors_status": r["fedors_status"],
        "hansen_status": r["hansen_status"],
        "values": r["values"],
    }
results["attack_d_greedy_claim_collisions"] = attack_d

json.dump(results, open("/tmp/vb03_attack_ab_d.json", "w"), indent=2)
print("WROTE /tmp/vb03_attack_ab_d.json")
print(json.dumps(results["attack_a_independent_rederivation"], indent=2))
print(json.dumps(results["attack_b_boundary_search"], indent=2)[:2000])
print(json.dumps(results["attack_d_greedy_claim_collisions"], indent=2)[:4000])
