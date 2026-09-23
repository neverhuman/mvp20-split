"""Hansen solubility parameter (HSP) estimation for the bigsoldb-v1 baseline.

Why this exists
---------------
amphora-solvency-score's falsifiable hypothesis (docs/mission.md) is that a
measured, group-held-out model "can outperform HSP-only screening". HSP
screening is the incumbent industrial practice for solvent selection in
coatings (Hansen, *Hansen Solubility Parameters: A User's Handbook*, 2nd ed.,
CRC Press 2007). The bigsoldb-v1 benchmark previously compared only against
statistical baselines (global/marginal means), which does NOT test that
hypothesis. This module supplies the incumbent.

Two sources of HSP are used, and they are kept strictly separate:

1. `PUBLISHED_SOLVENT_HSP` - experimental (delta_D, delta_P, delta_H) for
   common solvents, transcribed from Hansen 2nd ed. Appendix A, Table A.1.
   Used for the *solvent* side only.

2. `hvk_hsp()` - Hoftyzer-Van Krevelen group-contribution estimation
   (Van Krevelen & Te Nijenhuis, *Properties of Polymers*, 4th ed., Elsevier
   2009, Sec. 7.2), with Fedors molar volume increments (Fedors,
   Polym. Eng. Sci. 14 (1974) 147). Used for the *solute* side, because
   leave-solute-out evaluation requires HSP for molecules with no tabulated
   value - exactly the situation a practitioner faces.

        delta_D = sum(F_di) / V
        delta_P = sqrt(sum(F_pi^2)) / V
        delta_H = sqrt(sum(E_hi) / V)

Known-answer validation
-----------------------
The group-contribution path is only trustworthy if it reproduces the
tabulated values. `validate_hvk()` runs `hvk_hsp()` over every solvent in
`PUBLISHED_SOLVENT_HSP` and reports per-component MAE/RMSE against the
published numbers. The caller is expected to gate on this: if the estimator
cannot reproduce published HSP, the HSP baseline is not fit to serve as the
incumbent comparator and the comparison must be withheld rather than
reported. Fail-closed, consistent with the module's Phase-0 policy.

No claim of candidate performance is made here; this is a diagnostic
comparator for a LOCKED_INTERNAL benchmark.
"""

from __future__ import annotations

import math

import numpy as np
from rdkit import Chem, RDLogger

RDLogger.DisableLog("rdApp.*")

# ---------------------------------------------------------------------------
# 1. Published experimental HSP (Hansen 2nd ed., Table A.1), MPa^0.5.
#    name -> (SMILES, delta_D, delta_P, delta_H)
# ---------------------------------------------------------------------------
PUBLISHED_SOLVENT_HSP: dict[str, tuple[str, float, float, float]] = {
    "water": ("O", 15.5, 16.0, 42.3),
    "methanol": ("CO", 15.1, 12.3, 22.3),
    "ethanol": ("CCO", 15.8, 8.8, 19.4),
    "1-propanol": ("CCCO", 16.0, 6.8, 17.4),
    "2-propanol": ("CC(C)O", 15.8, 6.1, 16.4),
    "1-butanol": ("CCCCO", 16.0, 5.7, 15.8),
    "2-butanol": ("CCC(C)O", 15.8, 5.7, 14.5),
    "2-methyl-1-propanol": ("CC(C)CO", 15.1, 5.7, 15.9),
    "tert-butanol": ("CC(C)(C)O", 15.2, 5.1, 14.7),
    "1-pentanol": ("CCCCCO", 15.9, 4.5, 13.9),
    "3-methyl-1-butanol": ("CC(C)CCO", 15.8, 5.2, 13.3),
    "1-hexanol": ("CCCCCCO", 15.9, 5.8, 12.5),
    "1-heptanol": ("CCCCCCCO", 16.0, 5.3, 11.7),
    "1-octanol": ("CCCCCCCCO", 17.0, 3.3, 11.9),
    "1-nonanol": ("CCCCCCCCCO", 17.0, 3.1, 10.4),
    "1-decanol": ("CCCCCCCCCCO", 17.6, 2.7, 10.0),
    "cyclohexanol": ("OC1CCCCC1", 17.4, 4.1, 13.5),
    "benzyl alcohol": ("OCc1ccccc1", 18.4, 6.3, 13.7),
    "phenol": ("Oc1ccccc1", 18.0, 5.9, 14.9),
    "ethylene glycol": ("OCCO", 17.0, 11.0, 26.0),
    "1,2-propanediol": ("CC(O)CO", 16.8, 9.4, 23.3),
    "glycerol": ("OCC(O)CO", 17.4, 12.1, 29.3),
    "diethylene glycol": ("OCCOCCO", 16.6, 12.0, 20.7),
    "2-methoxyethanol": ("COCCO", 16.2, 9.2, 16.4),
    "2-ethoxyethanol": ("CCOCCO", 16.2, 9.2, 14.3),
    "2-butoxyethanol": ("CCCCOCCO", 16.0, 5.1, 12.3),
    "acetone": ("CC(C)=O", 15.5, 10.4, 7.0),
    "2-butanone": ("CCC(C)=O", 16.0, 9.0, 5.1),
    "2-pentanone": ("CCCC(C)=O", 16.0, 7.6, 4.7),
    "3-pentanone": ("CCC(=O)CC", 15.8, 7.6, 4.7),
    "4-methyl-2-pentanone": ("CC(C)CC(C)=O", 15.3, 6.1, 4.1),
    "cyclohexanone": ("O=C1CCCCC1", 17.8, 6.3, 5.1),
    "cyclopentanone": ("O=C1CCCC1", 17.9, 11.9, 5.2),
    "acetophenone": ("CC(=O)c1ccccc1", 18.8, 9.0, 4.0),
    "methyl acetate": ("COC(C)=O", 15.5, 7.2, 7.6),
    "ethyl acetate": ("CCOC(C)=O", 15.8, 5.3, 7.2),
    "propyl acetate": ("CCCOC(C)=O", 15.3, 4.3, 7.6),
    "isopropyl acetate": ("CC(C)OC(C)=O", 15.1, 4.1, 7.6),
    "butyl acetate": ("CCCCOC(C)=O", 15.8, 3.7, 6.3),
    "ethyl lactate": ("CCOC(=O)C(C)O", 16.0, 7.6, 12.5),
    "propylene carbonate": ("CC1COC(=O)O1", 20.0, 18.0, 4.1),
    "formic acid": ("OC=O", 14.3, 11.9, 16.6),
    "acetic acid": ("CC(O)=O", 14.5, 8.0, 13.5),
    "acetonitrile": ("CC#N", 15.3, 18.0, 6.1),
    "propionitrile": ("CCC#N", 15.3, 14.3, 5.5),
    "benzonitrile": ("N#Cc1ccccc1", 17.4, 9.0, 3.3),
    "nitromethane": ("C[N+](=O)[O-]", 15.8, 18.8, 5.1),
    "nitrobenzene": ("O=[N+]([O-])c1ccccc1", 20.0, 8.6, 4.1),
    "dimethyl sulfoxide": ("CS(C)=O", 18.4, 16.4, 10.2),
    "sulfolane": ("O=S1(=O)CCCC1", 20.3, 18.2, 10.9),
    "N,N-dimethylformamide": ("CN(C)C=O", 17.4, 13.7, 11.3),
    "N,N-dimethylacetamide": ("CN(C)C(C)=O", 16.8, 11.5, 10.2),
    "N-methyl-2-pyrrolidone": ("CN1CCCC1=O", 18.0, 12.3, 7.2),
    "tetrahydrofuran": ("C1CCOC1", 16.8, 5.7, 8.0),
    "1,4-dioxane": ("C1COCCO1", 17.5, 1.8, 9.0),
    "diethyl ether": ("CCOCC", 14.5, 2.9, 5.1),
    "methyl tert-butyl ether": ("COC(C)(C)C", 14.8, 4.3, 5.0),
    "1,2-dimethoxyethane": ("COCCOC", 15.4, 5.4, 7.4),
    "anisole": ("COc1ccccc1", 17.8, 4.1, 6.7),
    "dichloromethane": ("ClCCl", 18.2, 6.3, 6.1),
    "chloroform": ("ClC(Cl)Cl", 17.8, 3.1, 5.7),
    "carbon tetrachloride": ("ClC(Cl)(Cl)Cl", 17.8, 0.0, 0.6),
    "1,2-dichloroethane": ("ClCCCl", 19.0, 7.4, 4.1),
    "trichloroethylene": ("ClC=C(Cl)Cl", 18.0, 3.1, 5.3),
    "tetrachloroethylene": ("ClC(Cl)=C(Cl)Cl", 18.3, 5.7, 0.0),
    "chlorobenzene": ("Clc1ccccc1", 19.0, 4.3, 2.0),
    "benzene": ("c1ccccc1", 18.4, 0.0, 2.0),
    "toluene": ("Cc1ccccc1", 18.0, 1.4, 2.0),
    "ethylbenzene": ("CCc1ccccc1", 17.8, 0.6, 1.4),
    "o-xylene": ("Cc1ccccc1C", 17.8, 1.0, 3.1),
    "m-xylene": ("Cc1cccc(C)c1", 17.6, 1.0, 3.1),
    "p-xylene": ("Cc1ccc(C)cc1", 17.6, 1.0, 3.1),
    "mesitylene": ("Cc1cc(C)cc(C)c1", 18.0, 0.0, 0.6),
    "cumene": ("CC(C)c1ccccc1", 18.1, 1.2, 1.2),
    "styrene": ("C=Cc1ccccc1", 18.6, 1.0, 4.1),
    "1-methylnaphthalene": ("Cc1cccc2ccccc12", 20.6, 0.8, 4.7),
    "n-pentane": ("CCCCC", 14.5, 0.0, 0.0),
    "n-hexane": ("CCCCCC", 14.9, 0.0, 0.0),
    "n-heptane": ("CCCCCCC", 15.3, 0.0, 0.0),
    "n-octane": ("CCCCCCCC", 15.5, 0.0, 0.0),
    "n-decane": ("CCCCCCCCCC", 15.7, 0.0, 0.0),
    "cyclohexane": ("C1CCCCC1", 16.8, 0.0, 0.2),
    "methylcyclohexane": ("CC1CCCCC1", 16.0, 0.0, 1.0),
    "pyridine": ("c1ccncc1", 19.0, 8.8, 5.9),
    "aniline": ("Nc1ccccc1", 19.4, 5.1, 10.2),
    "triethylamine": ("CCN(CC)CC", 15.4, 1.4, 4.1),
    "carbon disulfide": ("S=C=S", 20.5, 0.0, 0.6),
    # added to reach full coverage of the BigSolDB 2.1 solvent set
    "ethyl formate": ("CCOC=O", 15.5, 8.4, 8.4),
    "isobutyl acetate": ("CC(=O)OCC(C)C", 15.1, 3.7, 6.3),
    "n-pentyl acetate": ("CCCCCOC(C)=O", 15.8, 3.3, 6.1),
    "diethylene glycol monoethyl ether": ("CCOCCOCCO", 16.1, 9.2, 12.2),
    "2-propoxyethanol": ("CCCOCCO", 16.0, 8.2, 13.0),
    "dimethyl carbonate": ("COC(=O)OC", 15.5, 3.9, 9.7),
    "propionic acid": ("CCC(=O)O", 14.7, 5.3, 12.4),
    "n-butyric acid": ("CCCC(=O)O", 14.9, 4.1, 10.6),
    "n-dodecane": ("CCCCCCCCCCCC", 16.0, 0.0, 0.0),
    "gamma-butyrolactone": ("O=C1CCCO1", 19.0, 16.6, 7.4),
    "formamide": ("NC=O", 17.2, 26.2, 19.0),
}


def published_hsp_by_canonical_smiles() -> dict[str, tuple[float, float, float]]:
    """Published table re-keyed by RDKit canonical SMILES for dataset joins."""
    out = {}
    for _name, (smi, dd, dp, dh) in PUBLISHED_SOLVENT_HSP.items():
        mol = Chem.MolFromSmiles(smi)
        if mol is not None:
            out[Chem.MolToSmiles(mol)] = (dd, dp, dh)
    return out

# ---------------------------------------------------------------------------
# 2. Group-contribution increments.
#    F_d, F_p in (MJ/m3)^0.5 * cm3/mol ; E_h in J/mol ; V in cm3/mol.
#    HSP increments: Van Krevelen & Te Nijenhuis 4th ed. Sec 7.2 (Hoftyzer-VK).
#    Volume increments: Fedors 1974.
# ---------------------------------------------------------------------------
GROUPS: dict[str, tuple[float, float, float, float]] = {
    #                 F_d     F_p      E_h       V
    "CH3":          (420.0,    0.0,      0.0,  33.5),
    "CH2":          (270.0,    0.0,      0.0,  16.1),
    "CH":           ( 80.0,    0.0,      0.0,  -1.0),
    "C":            (-70.0,    0.0,      0.0, -19.2),
    "=CH2":         (400.0,    0.0,      0.0,  28.5),
    "=CH":          (200.0,    0.0,      0.0,  13.5),
    "=C":           ( 70.0,    0.0,      0.0,  -5.5),
    "#CH":          (285.0,    0.0,      0.0,  27.4),
    "#C":           (140.0,    0.0,      0.0,   6.5),
    "ar_CH":        (240.0,    0.0,      0.0,  13.5),
    "ar_C":         (200.0,    0.0,      0.0,   3.0),
    "ar_N":         (150.0,  400.0,   3000.0,   5.0),
    "OH":           (210.0,  500.0,  20000.0,  10.0),
    "ether_O":      (100.0,  400.0,   3000.0,   3.8),
    "ketone":       (290.0,  770.0,   2000.0,  10.8),
    "aldehyde":     (470.0,  800.0,   4500.0,  22.3),
    "acid":         (530.0,  420.0,  10000.0,  28.5),
    "ester":        (390.0,  490.0,   7000.0,  18.0),
    "amide":        (390.0,  770.0,  12000.0,  18.0),
    "NH2":          (280.0,    0.0,   8400.0,  19.2),
    "NH":           (160.0,  210.0,   3100.0,   4.5),
    "N":            ( 20.0,  800.0,   5000.0,  -9.0),
    "nitrile":      (430.0, 1100.0,   2500.0,  24.0),
    "nitro":        (500.0, 1070.0,   1500.0,  24.0),
    "F":            (220.0,    0.0,      0.0,  18.0),
    "Cl":           (450.0,  550.0,    400.0,  24.0),
    "Br":           (550.0,    0.0,      0.0,  30.0),
    "I":            (600.0,    0.0,      0.0,  31.5),
    "S":            (440.0,    0.0,      0.0,  12.0),
    "SH":           (440.0,    0.0,   1500.0,  28.0),
    "sulfoxide":    (390.0, 1200.0,   6000.0,  20.0),
    "sulfone":      (390.0, 1500.0,   6000.0,  27.0),
    "ring_alicyc":  (190.0,    0.0,      0.0,  16.0),
}

# Composite (multi-atom) functional groups, matched first. `consume` lists the
# indices *within the SMARTS match* that belong to the group itself; context
# atoms (e.g. the carbons flanking a ketone) are deliberately NOT consumed so
# they still get their own skeletal increment in the per-atom pass.
COMPOSITE_SMARTS: list[tuple[str, str, tuple[int, ...]]] = [
    ("acid", "[CX3](=[OX1])[OX2H1]", (0, 1, 2)),
    ("ester", "[CX3](=[OX1])[OX2H0][#6]", (0, 1, 2)),
    ("amide", "[CX3](=[OX1])[NX3]", (0, 1, 2)),
    ("aldehyde", "[CX3H1](=[OX1])[#6]", (0, 1)),
    ("ketone", "[#6][CX3](=[OX1])[#6]", (1, 2)),
    ("nitrile", "[NX1]#[CX2]", (0, 1)),
    ("nitro", "[NX3,NX3+](=[OX1])[OX1,OX1-]", (0, 1, 2)),
    ("sulfone", "[SX4](=[OX1])(=[OX1])", (0, 1, 2)),
    ("sulfoxide", "[SX3](=[OX1])", (0, 1)),
]
_COMPOSITE = [
    (name, Chem.MolFromSmarts(sma), idx) for name, sma, idx in COMPOSITE_SMARTS
]


def group_instances(mol: Chem.Mol) -> list[tuple[str, int]]:
    """Decompose a molecule into (group_name, anchor_atom_index) instances.

    Composite functional groups are matched first and their atoms marked
    consumed; every remaining heavy atom is then classified individually by
    element, aromaticity, hybridisation and attached-hydrogen count. Oxygen
    and nitrogen atoms already inside a composite match are skipped, so a
    carbonyl carbon is never also counted as a plain carbon.

    The anchor index is retained so the symmetry factor (see `hvk_hsp`) can
    identify polar groups that are symmetry-equivalent to one another.
    """
    out: list[tuple[str, int]] = []
    consumed: set[int] = set()

    for name, patt, keep in _COMPOSITE:
        if patt is None:
            continue
        for match in mol.GetSubstructMatches(patt):
            own = tuple(match[i] for i in keep)
            if any(idx in consumed for idx in own):
                continue
            consumed.update(own)
            out.append((name, own[0]))

    for atom in mol.GetAtoms():
        if atom.GetIdx() in consumed:
            continue
        z = atom.GetSymbol()
        nh = atom.GetTotalNumHs()
        if z == "C":
            if atom.GetIsAromatic():
                key = "ar_CH" if nh >= 1 else "ar_C"
            else:
                nd = sum(1 for b in atom.GetBonds()
                         if b.GetBondType() == Chem.BondType.DOUBLE)
                nt = sum(1 for b in atom.GetBonds()
                         if b.GetBondType() == Chem.BondType.TRIPLE)
                if nt:
                    key = "#CH" if nh >= 1 else "#C"
                elif nd:
                    key = {2: "=CH2", 1: "=CH"}.get(nh, "=C")
                else:
                    key = {3: "CH3", 2: "CH2", 1: "CH"}.get(nh, "C")
                    if nh == 0 and atom.GetDegree() <= 1:
                        key = "CH3"  # e.g. methane-like terminal
        elif z == "O":
            if atom.GetIsAromatic():
                key = "ether_O"
            elif nh >= 1:
                key = "OH"
            else:
                key = "ether_O"
        elif z == "N":
            if atom.GetIsAromatic():
                key = "ar_N"
            elif nh >= 2:
                key = "NH2"
            elif nh == 1:
                key = "NH"
            else:
                key = "N"
        elif z == "S":
            key = "SH" if nh >= 1 else "S"
        elif z in ("F", "Cl", "Br", "I"):
            key = z
        else:
            continue  # unsupported element: contributes nothing, flagged below
        out.append((key, atom.GetIdx()))

    # Fedors/HvK ring-closure correction for non-aromatic rings only
    ri = mol.GetRingInfo()
    for ring in ri.AtomRings():
        if not all(mol.GetAtomWithIdx(i).GetIsAromatic() for i in ring):
            out.append(("ring_alicyc", ring[0]))
    return out


def symmetry_factor(k: int) -> float:
    """Van Krevelen's symmetry reduction for k equivalent polar groups.

    Properties of Polymers 4th ed., Sec. 7.2: delta_P must be reduced when
    identical polar groups sit in symmetrical positions, because their bond
    dipoles cancel - by 0.5 for one plane of symmetry, 0.25 for two, and to
    zero for higher symmetry. Without this, CCl4 (published delta_P = 0.0) is
    estimated at 14.3 MPa^0.5 purely from four quadrature-summed C-Cl dipoles.
    """
    if k <= 1:
        return 1.0
    if k == 2:
        return 0.5
    if k == 3:
        return 0.25
    return 0.0


# Below this molar volume the Fedors/HvK parameterisation is outside its fitted
# domain (it is built for organic liquids and polymer repeat units, not for
# water or small inorganics), so estimation abstains instead of guessing.
MIN_MOLAR_VOLUME_CM3 = 20.0


SUPPORTED_ELEMENTS = {"C", "H", "O", "N", "S", "F", "Cl", "Br", "I"}


def hvk_hsp(smiles: str):
    """Return (delta_D, delta_P, delta_H, molar_volume) or None if unsupported.

    Fail-closed: molecules containing elements outside the parameterised set,
    or yielding a non-positive molar volume, return None rather than a guess.
    """
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None
    if any(a.GetSymbol() not in SUPPORTED_ELEMENTS for a in mol.GetAtoms()):
        return None
    if any(a.GetFormalCharge() != 0 for a in mol.GetAtoms()):
        # charged species (salts, zwitterions) are outside HSP's regime
        if not mol.GetSubstructMatches(Chem.MolFromSmarts("[NX3+](=O)[O-]")):
            return None

    inst = group_instances(mol)
    if not inst:
        return None

    # Symmetry classes: atoms that are topologically equivalent share a rank
    # when ties are left unbroken.
    ranks = list(Chem.CanonicalRankAtoms(mol, breakTies=False))

    fd = eh = vol = 0.0
    # (group, symmetry class) -> [F_p of that group, how many are equivalent]
    polar: dict[tuple[str, int], list] = {}
    for key, anchor in inst:
        p = GROUPS.get(key)
        if p is None:
            return None
        fd += p[0]
        eh += p[2]
        vol += p[3]
        if p[1] > 0.0:
            slot = polar.setdefault((key, ranks[anchor]), [p[1], 0])
            slot[1] += 1

    if vol < MIN_MOLAR_VOLUME_CM3:
        return None

    fp_sq = sum(k * (fp**2) * (symmetry_factor(k) ** 2) for fp, k in polar.values())
    return (fd / vol, math.sqrt(fp_sq) / vol, math.sqrt(max(eh, 0.0) / vol), vol)


def ra(d1, p1, h1, d2, p2, h2) -> float:
    """Hansen distance Ra (MPa^0.5). Hansen 2nd ed. Eq. 2.9."""
    return math.sqrt(4.0 * (d1 - d2) ** 2 + (p1 - p2) ** 2 + (h1 - h2) ** 2)


def validate_hvk() -> dict:
    """Known-answer test: HvK estimates vs published Hansen Table A.1 values."""
    rows = []
    for name, (smi, dd, dp, dh) in PUBLISHED_SOLVENT_HSP.items():
        est = hvk_hsp(smi)
        if est is None:
            rows.append({"solvent": name, "status": "UNSUPPORTED"})
            continue
        rows.append({
            "solvent": name,
            "status": "OK",
            "published": [dd, dp, dh],
            "estimated": [round(est[0], 2), round(est[1], 2), round(est[2], 2)],
            "abs_err": [round(abs(est[0] - dd), 2),
                        round(abs(est[1] - dp), 2),
                        round(abs(est[2] - dh), 2)],
            "molar_volume_cm3_mol": round(est[3], 1),
        })
    ok = [r for r in rows if r["status"] == "OK"]
    err = np.array([r["abs_err"] for r in ok], dtype=float)
    pub = np.array([r["published"] for r in ok], dtype=float)
    est = np.array([r["estimated"] for r in ok], dtype=float)
    comp = ["delta_D", "delta_P", "delta_H"]
    summary = {
        "n_published_solvents": len(PUBLISHED_SOLVENT_HSP),
        "n_estimable": len(ok),
        "n_unsupported": len(rows) - len(ok),
        "reference": "Hansen 2nd ed. Table A.1 (experimental)",
        "estimator": "Hoftyzer-Van Krevelen groups + Fedors molar volume",
        "per_component": {
            c: {
                "mae": float(np.mean(err[:, i])),
                "rmse": float(np.sqrt(np.mean(err[:, i] ** 2))),
                "pearson_r": float(np.corrcoef(pub[:, i], est[:, i])[0, 1]),
                "published_range": [float(pub[:, i].min()), float(pub[:, i].max())],
            }
            for i, c in enumerate(comp)
        },
        "ra_to_published_self_mae": float(np.mean([
            ra(*est[k], *pub[k]) for k in range(len(ok))
        ])),
    }
    return {"summary": summary, "rows": rows}


if __name__ == "__main__":
    import json
    out = validate_hvk()
    print(json.dumps(out["summary"], indent=2))
    worst = sorted(
        [r for r in out["rows"] if r["status"] == "OK"],
        key=lambda r: -sum(r["abs_err"]),
    )[:12]
    print("\nworst 12 by total absolute error:")
    for r in worst:
        print(f"  {r['solvent']:28} pub={r['published']} est={r['estimated']} "
              f"err={r['abs_err']} V={r['molar_volume_cm3_mol']}")
    print("\nunsupported:", [r["solvent"] for r in out["rows"]
                             if r["status"] != "OK"])
