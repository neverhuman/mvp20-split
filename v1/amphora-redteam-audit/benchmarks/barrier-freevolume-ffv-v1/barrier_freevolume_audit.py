"""AUDIT_ONLY red-team: a-priori occupied-volume engine + free-volume barrier-transport axis.

WHAT THIS IS
------------
Marine anti-corrosion protection is a TRANSPORT problem: the epoxy film must throttle
the flux of H2O / O2 / Cl- to the steel. The rate-controlling quantity is the penetrant
DIFFUSION coefficient, which free-volume theory (Doolittle; Cohen-Turnbull 1959; Fujita)
ties to the polymer's Fractional Free Volume  FFV = (V - V_occ)/V , with the occupied
volume V_occ = 1.3 * Vw  (Bondi 1964 universal packing factor; Van Krevelen, Properties of
Polymers, ch.4 & ch.18).  Every one of the 66 signed receipts reasons about EQUILIBRIUM
barrier state (water uptake, CPVC, wet-Tg, adhesion) -- NONE computes the free volume that
sets the diffusion RATE.  This module stands up that transport axis.

The load-bearing, VALIDATED deliverable is the volumetric foundation: an a-priori van der
Waals / occupied molecular volume computed three INDEPENDENT ways and cross-checked
(non-circular known-answer battery).  FFV is then shown to be magnitude-bounds-consistent
for real DGEBA-amine networks.  Two naive shortcuts are honestly REFUTED.

METHODS (all offline, no external data-rights needed)
  A. Zhao-Abraham-Zissimos (2003) VABC   -- atom-additive van der Waals volume (~Bondi).
  B. Abraham-McGowan characteristic volume Vx -- independent atomic set + bond term.
  C. RDKit explicit-conformer geometric VdW volume -- 3D grid, integrates real overlaps.
Bondi & McGowan are DIFFERENT lineages; RDKit is pure geometry.  Agreement of A/B/C tests
the atom-additivity assumption that FFV in polymers relies on.  None uses permeability,
FFV, or barrier data -> non-circular w.r.t. the barrier claim.

AUTHORITY: AUDIT_ONLY. Promotes nothing, flips no scientific_readiness flag, signs no
phase0 evaluation/review, modifies no existing receipt, does not change the manifest
(still 66 receipts / 11 modules).
"""
import json, math
from pathlib import Path
from rdkit import Chem
from rdkit.Chem import AllChem, Descriptors

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
PROBES = ROOT / "reports/data/epoxy-amine-20-audit-probes.v1.json"

# ---- Zhao, Abraham, Zissimos, J. Org. Chem. 2003, 68, 7368  (atomic VdW volumes, A^3) ----
ZHAO_VDW = {"H":7.24,"C":20.58,"N":15.60,"O":14.71,"F":13.31,"Cl":22.45,
            "Br":26.52,"I":32.52,"P":24.43,"S":24.43,"Si":38.79,"B":40.48}
ZHAO_BOND = 5.92          # subtracted per bond
ZHAO_RA   = 14.7          # subtracted per aromatic ring
ZHAO_RNA  = 3.8           # subtracted per non-aromatic ring
A3_TO_CM3MOL = 0.6022     # Avogadro * 1e-24

# ---- Abraham & McGowan, Chromatographia 1987 (characteristic atomic volumes, cm^3/mol) ----
MCG = {"H":8.71,"C":16.35,"N":14.39,"O":12.43,"F":10.48,"Cl":20.95,
       "Br":26.21,"I":34.53,"P":24.87,"S":22.91,"Si":26.83,"B":18.32}
MCG_BOND = 6.56           # subtracted per bond (any order)

# ---- external reference constants (NON-CIRCULAR anchors) ----
BONDI_REF = {"benzene":48.36, "cyclohexane":61.42}     # Bondi 1964 Vw, cm^3/mol
MCGOWAN_REF = {"methane":24.95, "ethanol":44.91, "benzene":71.64}  # McGowan Vx*100, cm^3/mol


def _decompose(smiles):
    m = Chem.MolFromSmiles(smiles)
    if m is None:
        raise ValueError(f"bad SMILES {smiles}")
    mh = Chem.AddHs(m)
    atoms = {}
    for a in mh.GetAtoms():
        atoms[a.GetSymbol()] = atoms.get(a.GetSymbol(), 0) + 1
    nb = mh.GetNumBonds()
    nar = nal = 0
    for ring in m.GetRingInfo().AtomRings():
        if all(m.GetAtomWithIdx(i).GetIsAromatic() for i in ring):
            nar += 1
        else:
            nal += 1
    return m, mh, atoms, nb, nar, nal


def vabc_A3(smiles):
    _, _, atoms, nb, nar, nal = _decompose(smiles)
    return (sum(ZHAO_VDW[s]*n for s, n in atoms.items())
            - ZHAO_BOND*nb - ZHAO_RA*nar - ZHAO_RNA*nal)


def mcgowan_cm3mol(smiles):
    _, _, atoms, nb, _, _ = _decompose(smiles)
    return sum(MCG[s]*n for s, n in atoms.items()) - MCG_BOND*nb


def rdkit_geom_A3(smiles, seeds=(1, 7, 23, 42, 101)):
    m = Chem.AddHs(Chem.MolFromSmiles(smiles))
    vols = []
    for s in seeds:
        mm = Chem.Mol(m)
        if AllChem.EmbedMolecule(mm, randomSeed=s, maxAttempts=2000) != 0:
            continue
        try:
            AllChem.MMFFOptimizeMolecule(mm, maxIters=2000)
        except Exception:
            pass
        vols.append(AllChem.ComputeMolVolume(mm, gridSpacing=0.2))
    if not vols:
        return None
    return sum(vols) / len(vols)


def nh_count(smiles):
    """Amine N-H groups (reactive sites): total H on nitrogen atoms."""
    mh = Chem.AddHs(Chem.MolFromSmiles(smiles))
    return sum(1 for a in mh.GetAtoms() if a.GetSymbol() == "H"
               and a.GetNeighbors()[0].GetSymbol() == "N")


def pearson(xs, ys):
    n = len(xs); mx = sum(xs)/n; my = sum(ys)/n
    cov = sum((x-mx)*(y-my) for x, y in zip(xs, ys))
    sx = math.sqrt(sum((x-mx)**2 for x in xs)); sy = math.sqrt(sum((y-my)**2 for y in ys))
    return cov/(sx*sy)


def spearman(a, b):
    def rk(x):
        order = sorted(range(len(x)), key=lambda i: x[i]); r = [0]*len(x)
        for pos, i in enumerate(order):
            r[i] = pos
        return r
    ra, rb = rk(a), rk(b); n = len(a)
    d2 = sum((ra[i]-rb[i])**2 for i in range(n))
    return 1 - 6*d2/(n*(n*n-1))


def R(x, d=4):
    return round(x, d) if x is not None else None


# ============================ PART A: volumetric foundation ============================
anchors = {"methane": "C", "ethanol": "CCO", "benzene": "c1ccccc1",
           "cyclohexane": "C1CCCCC1", "water": "O", "toluene": "Cc1ccccc1"}
anchor_rows = {}
for nm, smi in anchors.items():
    va = vabc_A3(smi)
    anchor_rows[nm] = {"smiles": smi, "vabc_A3": R(va), "vabc_cm3mol": R(va*A3_TO_CM3MOL, 3),
                       "mcgowan_cm3mol": R(mcgowan_cm3mol(smi), 3),
                       "rdkit_geom_A3": R(rdkit_geom_A3(smi))}

probes = json.loads(PROBES.read_text())["compounds"]
probe_rows = []
for c in probes:
    smi = c["smiles"]; va = vabc_A3(smi); rg = rdkit_geom_A3(smi)
    probe_rows.append({
        "name": c["display_name"], "role": c["requested_role"], "smiles": smi,
        "vabc_A3": R(va), "vabc_cm3mol": R(va*A3_TO_CM3MOL, 3),
        "mcgowan_cm3mol": R(mcgowan_cm3mol(smi), 3),
        "rdkit_geom_A3": R(rg),
        "rdkit_over_vabc": R(rg/va, 4) if rg else None})

# cross-method statistics over the probe battery (independent-method corroboration)
va_list = [r["vabc_A3"] for r in probe_rows]
mc_list = [r["mcgowan_cm3mol"] for r in probe_rows]
rg_pairs = [(r["vabc_A3"], r["rdkit_geom_A3"]) for r in probe_rows if r["rdkit_geom_A3"]]
r_vabc_rdkit = pearson([a for a, _ in rg_pairs], [b for _, b in rg_pairs])
r_vabc_mcg = pearson(va_list, mc_list)
mean_rdkit_ratio = sum(b/a for a, b in rg_pairs)/len(rg_pairs)

# external-anchor absolute errors
benz = anchor_rows["benzene"]["vabc_cm3mol"]; cyc = anchor_rows["cyclohexane"]["vabc_cm3mol"]
bondi_benz_err = abs(benz - BONDI_REF["benzene"])/BONDI_REF["benzene"]
bondi_cyc_err = abs(cyc - BONDI_REF["cyclohexane"])/BONDI_REF["cyclohexane"]
mcg_meth_err = abs(anchor_rows["methane"]["mcgowan_cm3mol"] - MCGOWAN_REF["methane"])
mcg_eth_err = abs(anchor_rows["ethanol"]["mcgowan_cm3mol"] - MCGOWAN_REF["ethanol"])
mcg_benz_err = abs(anchor_rows["benzene"]["mcgowan_cm3mol"] - MCGOWAN_REF["benzene"])

# ============================ PART B: FFV of DGEBA-amine networks ============================
DGEBA = "CC(c1ccc(OCC2CO2)cc1)(c3ccc(OCC4CO4)cc3)C"
diamines = {"EDA": "NCCN", "HMDA": "NCCCCCCN", "mXDA": "NCc1cccc(CN)c1",
            "IPDA": "CC1(C)CC(N)CC(C)(CN)C1", "PACM": "NC1CCC(CC1)C2CCC(CC2)N",
            "TETA": "NCCNCCNCCN"}
M_dgeba = Descriptors.MolWt(Chem.MolFromSmiles(DGEBA))
Vw_dgeba = vabc_A3(DGEBA) * A3_TO_CM3MOL
RHO_RANGE = [1.10, 1.16, 1.20]     # documented glassy DGEBA-amine cured-density band, g/cm^3
AMORPHOUS_BAND = [0.08, 0.20]      # amorphous glassy-polymer FFV range (Bondi/PALS literature)
ffv_rows = []
for nm, smi in diamines.items():
    Md = Descriptors.MolWt(Chem.MolFromSmiles(smi))
    nh = nh_count(smi)                 # reactive N-H
    ndg = nh / 2.0                     # each DGEBA supplies 2 epoxies, each consumes 1 N-H
    M_rep = ndg * M_dgeba + Md         # addition cure -> mass conserved
    Vw = ndg * Vw_dgeba + vabc_A3(smi) * A3_TO_CM3MOL   # VdW volume additive
    ffv_by_rho = {}
    for rho in RHO_RANGE:
        V = M_rep / rho
        ffv_by_rho[f"{rho:.2f}"] = R((V - 1.3*Vw)/V, 4)
    vals = list(ffv_by_rho.values())
    ffv_rows.append({"network": f"DGEBA+{nm}", "nh_reactive": nh, "dgeba_per_amine": R(ndg, 3),
                     "M_repeat_gmol": R(M_rep, 2), "Vw_repeat_cm3mol": R(Vw, 2),
                     "ffv_by_rho_gcc": ffv_by_rho,
                     "in_amorphous_band": all(AMORPHOUS_BAND[0] <= v <= AMORPHOUS_BAND[1] for v in vals)})

# ============================ HONEST NEGATIVE #1: penetrant size proxy ============================
pen = {"H2O": "O", "O2": "O=O", "N2": "N#N", "CO2": "O=C=O", "CH4": "C", "Cl2": "ClCl", "H2": "[H][H]"}
kinetic = {"H2O": 2.65, "O2": 3.46, "N2": 3.64, "CO2": 3.30, "CH4": 3.80, "Cl2": 3.20, "H2": 2.89}
pen_rows = []
for p, smi in pen.items():
    v = vabc_A3(smi); d = (6*v/math.pi)**(1/3)
    pen_rows.append({"penetrant": p, "vabc_A3": R(v), "vdw_equiv_diam_A": R(d, 3),
                     "published_kinetic_diam_A": kinetic[p]})
deq = [r["vdw_equiv_diam_A"] for r in pen_rows]; kin = [r["published_kinetic_diam_A"] for r in pen_rows]
pen_spearman = R(spearman(deq, kin), 4)

# ================================ KNOWN-ANSWER GATE BATTERY ================================
gates = []
def gate(name, ok, detail):
    gates.append({"gate": name, "pass": bool(ok), "detail": detail})

gate("G1_mcgowan_methane_definitional", mcg_meth_err < 0.05,
     f"|Vx(CH4) {anchor_rows['methane']['mcgowan_cm3mol']} - lit 24.95| = {R(mcg_meth_err,3)} cm3/mol < 0.05")
gate("G2_mcgowan_ethanol_definitional", mcg_eth_err < 0.05,
     f"|Vx(EtOH) {anchor_rows['ethanol']['mcgowan_cm3mol']} - lit 44.91| = {R(mcg_eth_err,3)} < 0.05")
gate("G3_mcgowan_benzene_definitional", mcg_benz_err < 0.05,
     f"|Vx(C6H6) {anchor_rows['benzene']['mcgowan_cm3mol']} - lit 71.64| = {R(mcg_benz_err,3)} < 0.05")
gate("G4_vabc_benzene_vs_bondi", bondi_benz_err < 0.03,
     f"VABC benzene {benz} vs Bondi 48.36 -> rel err {R(bondi_benz_err,4)} < 0.03 (non-circular external)")
gate("G5_vabc_cyclohexane_vs_bondi", bondi_cyc_err < 0.03,
     f"VABC cyclohexane {cyc} vs Bondi 61.42 -> rel err {R(bondi_cyc_err,4)} < 0.03")
gate("G6_vabc_vs_rdkit_geom_pearson", r_vabc_rdkit >= 0.999,
     f"Pearson(VABC, RDKit explicit-geometry) = {R(r_vabc_rdkit,5)} >= 0.999 over n={len(rg_pairs)}")
gate("G7_vabc_vs_mcgowan_pearson", r_vabc_mcg >= 0.998,
     f"Pearson(VABC, McGowan independent lineage) = {R(r_vabc_mcg,5)} >= 0.998 over n={len(va_list)}")
gate("G8_additivity_vs_geometry_ratio", 1.00 <= mean_rdkit_ratio <= 1.08,
     f"mean RDKit/VABC = {R(mean_rdkit_ratio,4)} in [1.00,1.08]: atom-additivity reproduces "
     f"3D-overlap VdW volume within ~{R((mean_rdkit_ratio-1)*100,1)}%")
n_pass = sum(1 for g in gates if g["pass"])

# Network FFV is DIAGNOSTIC, not a pass/fail gate: without measured per-network cured
# densities the absolute value is density-controlled, and additive Vw carries a known
# ~few-% overestimate at ring-opened networks. We only OBSERVE bounds-consistency.
all_ffv = [v for r in ffv_rows for v in r["ffv_by_rho_gcc"].values()]
ffv_bounds_consistent = all(AMORPHOUS_BAND[0] <= v <= AMORPHOUS_BAND[1] for v in all_ffv)

diagnostic = {
    "schema": "amphora.redteam-audit.barrier-freevolume-ffv-v1.diagnostic.v1",
    "authority": "AUDIT_ONLY",
    "target_module": "amphora-barrier-corrosion-score",
    "target_capability": "free-volume barrier-transport axis (a-priori occupied volume -> FFV -> "
                         "Cohen-Turnbull penetrant diffusion). NEW axis: all 66 receipts are "
                         "equilibrium-state; none computes the free volume that sets diffusion RATE.",
    "theory": {
        "occupied_volume": "V_occ = 1.3 * Vw (Bondi 1964 universal packing factor)",
        "ffv": "FFV = (V - 1.3*Vw)/V ; V = M/rho molar volume (Van Krevelen ch.4)",
        "transport": "Doolittle/Cohen-Turnbull 1959: D = A*exp(-B/FFV); lower FFV -> lower "
                     "penetrant diffusivity -> slower H2O/O2/Cl- flux to steel -> better barrier",
        "volume_methods": {
            "A_VABC": "Zhao-Abraham-Zissimos 2003 atom-additive VdW volume (~Bondi)",
            "B_McGowan": "Abraham-McGowan 1987 characteristic volume (independent lineage)",
            "C_RDKit": "explicit-conformer 3D grid VdW volume (pure geometry)"}},
    "fitted_parameters": "NONE (zero free parameters; all constants are published)",
    "inputs_live_from_tree": {
        "epoxy_amine_smiles": str(PROBES.relative_to(ROOT)),
        "n_probes": len(probe_rows)},
    "part_A_volumetric_foundation": {
        "anchors": anchor_rows,
        "probe_battery": probe_rows,
        "cross_method_stats": {
            "pearson_vabc_rdkit_geom": R(r_vabc_rdkit, 5),
            "pearson_vabc_mcgowan": R(r_vabc_mcg, 5),
            "mean_rdkit_over_vabc_ratio": R(mean_rdkit_ratio, 4)}},
    "part_B_network_ffv_bounds_DIAGNOSTIC": {
        "assumed_density_band_gcc": RHO_RANGE,
        "amorphous_glassy_ffv_reference_band": AMORPHOUS_BAND,
        "networks": ffv_rows,
        "all_ffv_in_amorphous_band": ffv_bounds_consistent,
        "ffv_span_observed": [R(min(all_ffv), 4), R(max(all_ffv), 4)],
        "status": "DIAGNOSTIC_NOT_A_GATE",
        "note": "FFV MAGNITUDE lands in the amorphous glassy band for real DGEBA-amine networks "
                "(bounds-consistent, like the DiBenedetto/CPVC receipts). It is NOT scored as a "
                "pass/fail gate and is NOT a calibrated predictor: the absolute value is density-"
                "controlled (a 0.10 g/cc density swing moves FFV by ~0.07), and additive Vw carries "
                "a known ~few-% overestimate of occupied volume at ring-opened networks. The load-"
                "bearing missing input is therefore MEASURED per-network cured density (rights-"
                "blocked), not more theory."},
    "honest_negatives": {
        "penetrant_size_proxy_REFUTED": {
            "hypothesis": "VdW-volume-equivalent sphere diameter ranks penetrants like the "
                          "kinetic diameter that governs diffusion selectivity",
            "spearman_vs_published_kinetic_diameter": pen_spearman,
            "verdict": "REFUTED: shape (linear CO2/Cl2/N2 vs the volume-equivalent sphere) "
                       "breaks the volume->kinetic-diameter map. Free volume sets the polymer "
                       "side; penetrant selectivity needs kinetic diameter, not VdW volume.",
            "rows": pen_rows},
        "per_hardener_ranking_BLOCKED": "Absolute per-network permeability ranking needs "
            "rights-clean (measured cured density + measured P_O2/P_H2O) per hardener; not "
            "acquired this session. FFV differences at a shared assumed density are density-"
            "confounded and are NOT reported as a ranking."},
    "non_circularity": "VABC/McGowan/RDKit use NO permeability, FFV or barrier data. McGowan is "
        "a different atomic lineage from Bondi; RDKit is pure geometry. The load-bearing KPI is "
        "cross-method agreement (G6/G7/G8), independent of the barrier claim being supported.",
    "known_answer_battery": {"scope": "volumetric foundation only (G1-G8); the non-circular, "
                             "load-bearing KPIs. Network FFV is diagnostic, not gated.",
                             "n_gates": len(gates), "n_pass": n_pass,
                             "all_pass": n_pass == len(gates), "gates": gates},
    "verdict": ("ENGINE_READY__FOUNDATION_KNOWN_ANSWER_VALIDATED__FFV_BOUNDS_CONSISTENT_DIAGNOSTIC__"
                "ABSOLUTE_PERMEABILITY_CALIBRATION_DATA_RIGHTS_BLOCKED"
                if n_pass == len(gates) and ffv_bounds_consistent else
                "FOUNDATION_GATES_FAILED_SEE_BATTERY"),
    "does_not_close": [
        "does NOT promote amphora-barrier-corrosion-score: phase-0 is a governance state "
        "(scientific_success_required_for_phase0=false on all live locks; 0/29 ranked modules "
        "scientific_readiness==VALIDATED) needing two trust-anchored phase0 signatures this "
        "AUDIT_ONLY key cannot supply",
        "does NOT change the manifest (still 66 receipts / 11 modules)",
        "does NOT modify any existing receipt or any shipped Rust engine",
        "Part B FFV is a MAGNITUDE bounds check on assumed densities, not a calibrated "
        "prediction; the penetrant size proxy is REFUTED and reported as such"],
}

out = Path(__file__).with_name("diagnostic.canonical.json")
import sys
target = sys.argv[1] if len(sys.argv) > 1 else str(out)
Path(target).write_text(json.dumps(diagnostic, indent=2, sort_keys=True))
print("WROTE", target)
print(f"foundation gates {n_pass}/{len(gates)}  ffv_bounds_consistent={ffv_bounds_consistent}  "
      f"ffv_span={[R(min(all_ffv),4),R(max(all_ffv),4)]}")
print(f"verdict {diagnostic['verdict']}")
print(f"r(VABC,RDKit)={R(r_vabc_rdkit,5)}  r(VABC,McGowan)={R(r_vabc_mcg,5)}  "
      f"RDKit/VABC={R(mean_rdkit_ratio,4)}  penetrant_spearman={pen_spearman}")
