"""V-A12a escalation: adjacent-stress probe of role-reactivity-ratio-substitution-effect-v1.

R-A12 reinstated this benchmark's SURVIVED verdict (H2 direction rule holds under
Girard-Reydet 1995 r=k2/k1 in {0.65,0.45}). Those ratios were measured for AROMATIC
diamines (MDA/MDEA/MCDEA r=0.65, DDS r=0.45) but the benchmark's eligible hardener
set is aliphatic/cycloaliphatic (IPDA, PACM, MXDA) -- a chemotype mismatch the
benchmark's own does_not_close list does not flag. Aliphatic secondary amines are
frequently MORE nucleophilic than primary amines (alkyl inductive electron donation
increases basicity/nucleophilicity, opposite of the aromatic EWG-dominated case), i.e.
a plausible r=k2/k1 > 1 (positive kinetic substitution effect) regime for exactly the
hardeners this benchmark actually tests. This escalation probes r in {1.0(control
already validated), 1.54(=1/0.65, the aromatic-negative-effect mirrored positive),
2.0, 3.0} with FRESH seeds (distinct salt "escalate_v_a12a", never used by the
committed script's "validate"/"attack" salts) to see whether the pre-registered
falsification criterion (starved sol strictly > rich sol) still holds outside the
narrow negative-r regime the repair re-verified.

Imports the committed, unmodified run_reactivity_ratio.py module's functions
(mc_sol_fraction, sha) -- does not edit that file.
"""
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

REPO = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD_PATH = REPO / "amphora-molecule-role-ranker/benchmarks/role-reactivity-ratio-substitution-effect-v1/run_reactivity_ratio.py"
MOD_SHA256 = "3eeacaa08e5913b0a4a1c34afc2726fe40eb1f1e051f80f1c49fe907083e6fe8"

import os
os.chdir(REPO)

assert hashlib.sha256(MOD_PATH.read_bytes()).hexdigest() == MOD_SHA256, "committed script hash mismatch -- refuse to escalate against an unverified script"

spec = importlib.util.spec_from_file_location("run_reactivity_ratio_committed", MOD_PATH)
rr = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rr)

FIX = rr.FIX
fix = json.loads(FIX.read_bytes())
recs = {r["record_id"]: r for r in fix["records"]}


def gof(rid):
    return recs[rid]["facts"]["reactive_amine_hydrogen_count"]


def mof(rid):
    return recs[rid]["facts"]["average_molecular_weight_g_mol"]


def fof(rid):
    return recs[rid]["facts"]["oxirane_ring_count"]


f_resin = fof(rr.CANONICAL_RESIN)
m_resin = mof(rr.CANONICAL_RESIN)
r_starved = rr.r6(1.0 / rr.OFFSET_C)
r_rich = rr.r6(rr.OFFSET_C)

# re-derive eligible hardeners exactly as the committed script does (all-primary sites)
from rdkit import Chem
eligible_hardeners = []
for rid in rr.CANDIDATE_HARDENERS:
    smi = recs[rid]["smiles"]
    mol = Chem.MolFromSmiles(smi)
    n_matches = mol.GetSubstructMatches(rr.REACTIVE_AMINE_N)
    h_per_site = [mol.GetAtomWithIdx(m[0]).GetTotalNumHs() for m in n_matches]
    if all(h == 2 for h in h_per_site):
        eligible_hardeners.append(rid)

ESCALATION_RATIOS = {
    "positive_mirror_of_girard_reydet_0p65": rr.r6(1.0 / 0.65),   # 1.538...
    "positive_mirror_of_girard_reydet_0p45": rr.r6(1.0 / 0.45),   # 2.222...
    "extreme_positive_stress_r3": 3.0,
    "extreme_positive_stress_r10": 10.0,
}

rows = []
reversals = []
n_tests = 0
for rid_h in eligible_hardeners:
    g = gof(rid_h)
    m_h = mof(rid_h)
    n_b_starved = int(round(rr.N_RESIN_MOLECULES * f_resin * r_starved / g))
    n_b_rich = int(round(rr.N_RESIN_MOLECULES * f_resin * r_rich / g))
    for r_name, r_ratio in ESCALATION_RATIOS.items():
        seed_s = rr.seed_for("escalate_v_a12a", rid_h, r_name, "starved")
        seed_r = rr.seed_for("escalate_v_a12a", rid_h, r_name, "rich")
        mc_s = rr.mc_sol_fraction(rr.N_RESIN_MOLECULES, f_resin, m_resin, n_b_starved, g, m_h,
                                   r_starved, r_ratio, seed_s)
        mc_r = rr.mc_sol_fraction(rr.N_RESIN_MOLECULES, f_resin, m_resin, n_b_rich, g, m_h,
                                   r_rich, r_ratio, seed_r)
        s_pct, r_pct = 100.0 * mc_s["sol_fraction"], 100.0 * mc_r["sol_fraction"]
        holds = s_pct > r_pct
        n_tests += 1
        if not holds:
            reversals.append({"hardener": rid_h, "r_name": r_name, "r_ratio": r_ratio,
                               "starved_pct": rr.r6(s_pct), "rich_pct": rr.r6(r_pct)})
        rows.append({"hardener": rid_h, "r_name": r_name, "r_ratio": r_ratio,
                      "starved_pct": rr.r6(s_pct), "rich_pct": rr.r6(r_pct),
                      "direction_holds": bool(holds),
                      "seed_starved": seed_s, "seed_rich": seed_r})

result = {
    "escalation": "positive_kinetic_substitution_effect_adjacent_stress",
    "rationale": (
        "Original R-A12-reinstated benchmark tested only r=k2/k1 in {0.65,0.45} "
        "(Girard-Reydet 1995, measured for AROMATIC diamines) applied to ALIPHATIC "
        "eligible hardeners (IPDA/PACM/MXDA). This probes plausible r>1 regimes "
        "(secondary aliphatic amine more nucleophilic than primary) with fresh "
        "seeds never used by the committed script."),
    "committed_script_sha256_verified": MOD_SHA256,
    "eligible_hardeners": eligible_hardeners,
    "ratios_tested": ESCALATION_RATIOS,
    "n_tests": n_tests,
    "n_reversals": len(reversals),
    "reversals": reversals,
    "rows": rows,
    "verdict": "H2_REFUTED_UNDER_POSITIVE_SUBSTITUTION_STRESS" if reversals else "H2_SURVIVED_UNDER_POSITIVE_SUBSTITUTION_STRESS",
}
out_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/tmp/va12a_escalation_result.json")
out_path.write_text(json.dumps(result, indent=2, sort_keys=True))
print("WROTE", out_path)
print("verdict", result["verdict"])
print("n_tests", n_tests, "n_reversals", len(reversals))
print(json.dumps(reversals, indent=2))
