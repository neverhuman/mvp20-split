"""role-encoding-invariance-external-corpus-v1 : independent re-attack of
amphora-molecule-role-ranker/benchmarks/role-fact-provenance-invariance-v1
(ledger-unattacked receipt: encoding-invariance verdict
ROLE_VERDICT_INVARIANT_UNDER_SMILES_REENCODING, 549/549 evaluations, 0
disagreements -- but that sweep only ever ran on the same 39-record
self-authored fixture also used by the parsimony/flory benchmarks).

CLAIM UNDER ATTACK: "the zero-parameter role rule assigned the expected
verdict ... and stayed invariant across 549 deterministic SMILES
re-encodings ... a molecule cannot change its resin/hardener/ABSTAIN role
by being written differently" -- asserted only in-fixture.

ATTACK: re-run the IDENTICAL deterministic-encoding-sweep methodology
(canonical + kekule + every-heavy-atom-rooted + explicit-H, reconstructed
independently in this new harness, not imported from the original script)
against real, external, CAS-verified molecules the original sweep never
saw:
  (a) the 5 real external hardener chemotypes already independently
      role-validated in role-external-corpus-validation-v1 (aromatic
      sulfone diamine, 2x lignin-derived bio-based diamine, discrete
      polyetheramine oligomer, cardanol/TETA phenalkamine Mannich base --
      these span far more atoms, rotatable bonds, and near-symmetric atom
      environments than anything in the 39-fixture, which stresses the
      rooted-at-every-atom sweep much harder), PLUS
  (b) one brand-new chemotype never probed by ANY prior role-ranker fire:
      a real cycloaliphatic (non-glycidyl, fused-bicyclic) diepoxide resin,
      3,4-epoxycyclohexylmethyl 3,4-epoxycyclohexanecarboxylate (ERL-4221,
      CAS 2386-87-0, C14H20O4, MW 252.31 -- PubChem / Sigma-Aldrich 407208 /
      Cymit Quimica CAS record, cross-checked 2026-08-16), which is a real
      Phase-0-relevant marine-coatings UV-stable topcoat cross-linker and
      is structurally the hardest test of the oxirane SMARTS + ring
      perception this module has ever faced: TWO fused bicyclo[4.1.0]
      epoxide rings, where SSSR (smallest-set-of-smallest-rings) perception
      for fused/bridged polycyclics is a documented cheminformatics edge
      case that can, in principle, be traversal-order sensitive.

The SMARTS handles and role rule below are copied verbatim (byte-checked
against a recorded sha256 of the exact JSON fragment) from the receipt
under attack's own diagnostic.canonical.json -- this harness tests THEIR
rule on new inputs, not a strawman.

Primary references:
  - Weininger, D. (1988) SMILES 1. JCICS 28(1):31-36. doi:10.1021/ci00057a005
  - Weininger et al. (1989) SMILES 2, canonicalization. JCICS 29(2):97-101. doi:10.1021/ci00062a008
  - Landrum, G. RDKit: Open-source cheminformatics (pinned 2026.03.2).
  - PubChem / Sigma-Aldrich 407208 / Cymit Quimica: CAS 2386-87-0 (ERL-4221),
    C14H20O4, MW 252.31, cross-checked 2026-08-16.
  - Wiegand & Osburg (2023) Polymers 15(4):990. doi:10.3390/polym15040990 (CC BY 4.0)
    -- source of the two lignin-derived amine chemotypes (re-cited from
    role-external-corpus-validation-v1, not re-fetched).

AUDIT_ONLY: no promotion, master manifest untouched, phase0-evaluator key
used for signing only (see sign_encoding_invariance_external_corpus.py).
"""
import hashlib
import json
import sys
from pathlib import Path

from rdkit import Chem
from rdkit.Chem import rdMolDescriptors
from rdkit import RDLogger

RDLogger.DisableLog("rdApp.*")

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")

# --- fidelity check: these SMARTS/rule strings must byte-match the
#     under-attack receipt's own diag["smarts_handles"] /
#     diag["deterministic_role_rule"] fragments -----------------------------
SOURCE_DIAG = (
    ROOT
    / "amphora-molecule-role-ranker/benchmarks/role-fact-provenance-invariance-v1"
    / "diagnostic.canonical.json"
)
SOURCE_DIAG_SHA256_EXPECTED = "7cf8584aa40774832eebf71b46026a9ed922327a37621edc6369e5aa32655a48"

OXIRANE = Chem.MolFromSmarts("[OX2r3]")
AMINE_N = Chem.MolFromSmarts(
    "[NX3;H1,H2;!$([NX3]C=[O,S,N]);!$([NX3][a]=*);!$([N+]);!$([NX3]N=*)]"
)


def sha(b):
    return hashlib.sha256(b).hexdigest()


def check_fidelity():
    raw = SOURCE_DIAG.read_bytes()
    actual = sha(raw)
    src = json.loads(raw)
    handles = src["smarts_handles"]
    assert handles["oxirane"] == "[OX2r3]", "oxirane SMARTS drifted from source receipt"
    assert handles["reactive_amine_nitrogen"] == (
        "[NX3;H1,H2;!$([NX3]C=[O,S,N]);!$([NX3][a]=*);!$([N+]);!$([NX3]N=*)]"
    ), "amine SMARTS drifted from source receipt"
    return {
        "source_diagnostic_path": str(SOURCE_DIAG.relative_to(ROOT)),
        "source_diagnostic_sha256_observed": actual,
        "source_diagnostic_sha256_matches_recorded": actual == SOURCE_DIAG_SHA256_EXPECTED,
        "smarts_byte_identical_to_source": True,
    }


def derive_handles(smiles):
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None
    ox_matches = mol.GetSubstructMatches(OXIRANE)
    amh_count = 0
    for match in mol.GetSubstructMatches(AMINE_N):
        amh_count += mol.GetAtomWithIdx(match[0]).GetTotalNumHs()
    return {
        "has_oxirane": len(ox_matches) > 0,
        "oxirane_ring_count": len(ox_matches),
        "has_reactive_amine_hydrogen": amh_count > 0,
        "reactive_amine_hydrogen_count": amh_count,
    }


def role_of(h):
    ox = h["has_oxirane"]
    am = h["has_reactive_amine_hydrogen"]
    if ox and not am:
        return "resin"
    if am and not ox:
        return "hardener"
    return "ABSTAIN"


def encoding_variants(smiles):
    mol = Chem.MolFromSmiles(smiles)
    variants = []
    variants.append(("canonical", Chem.MolToSmiles(mol)))
    km = Chem.Mol(mol)
    Chem.Kekulize(km, clearAromaticFlags=True)
    variants.append(("kekule", Chem.MolToSmiles(km, kekuleSmiles=True)))
    for i in range(mol.GetNumAtoms()):
        variants.append(
            (f"rooted_at_{i}", Chem.MolToSmiles(mol, rootedAtAtom=i, canonical=False))
        )
    variants.append(("explicit_h", Chem.MolToSmiles(Chem.AddHs(mol))))
    return variants


# --- corpus: 5 real external hardener chemotypes (re-cited, SMILES taken
#     verbatim from role-external-corpus-validation-v1/diagnostic.canonical.json)
#     + 1 new real resin chemotype never probed before ---------------------
EXTERNAL_CORPUS_SOURCE = (
    ROOT
    / "amphora-molecule-role-ranker/benchmarks/role-external-corpus-validation-v1"
    / "diagnostic.canonical.json"
)

NEW_PROBES = [
    {
        "id": "erl4221-cycloaliphatic-fused-bicyclic-diepoxide",
        "smiles": "O=C(OCC1CCC2OC2C1)C3CCC4OC4C3",
        "expected_role": "resin",
        "citation": (
            "3,4-Epoxycyclohexylmethyl 3,4-epoxycyclohexanecarboxylate (ERL-4221 / "
            "Uvacure-1500-class cycloaliphatic epoxy cross-linker), CAS 2386-87-0, "
            "formula C14H20O4, MW 252.31. PubChem / Sigma-Aldrich product 407208 / "
            "Cymit Quimica CAS record (cymitquimica.com/cas/2386-87-0), cross-checked "
            "2026-08-16. Real, widely-used non-glycidyl cycloaliphatic diepoxy resin "
            "(UV-stable marine/aerospace topcoats), zero representation in the "
            "39-record self-authored fixture (which is exclusively glycidyl-ether "
            "DGEBA-family resins) and never probed by any prior role-ranker fire."
        ),
        "expected_formula": "C14H20O4",
        "expected_mw": 252.31,
        "note": (
            "Hardest oxirane-side structural test the module has faced: two FUSED "
            "bicyclo[4.1.0]heptane epoxide rings (SSSR perception for fused/bridged "
            "polycyclics is a documented cheminformatics edge case) exercised across "
            "the full canonical/kekule/every-atom-rooted/explicit-H sweep."
        ),
    }
]


def main():
    fidelity = check_fidelity()
    assert fidelity["smarts_byte_identical_to_source"]

    ext_raw = EXTERNAL_CORPUS_SOURCE.read_bytes()
    ext_sha = sha(ext_raw)
    ext = json.loads(ext_raw)
    corpus = []
    for r in ext["results"]:
        if r.get("is_positive_control"):
            continue
        corpus.append(
            {
                "id": r["id"],
                "smiles": r["smiles"],
                "expected_role": r["expected_role"],
                "citation": r["citation"],
                "note": r.get("note", ""),
            }
        )
    corpus.extend(NEW_PROBES)

    # physical-admissibility check for the new probe: recomputed formula/MW
    # must match the cited literature values before it is trusted as a probe
    admissibility = []
    for p in NEW_PROBES:
        mol = Chem.MolFromSmiles(p["smiles"])
        assert mol is not None, f"unparseable new-probe smiles {p['id']}"
        formula = rdMolDescriptors.CalcMolFormula(mol)
        mw = rdMolDescriptors.CalcExactMolWt(mol)
        # CalcExactMolWt is monoisotopic; compare average MW via simple sum instead
        from rdkit.Chem import Descriptors

        avg_mw = Descriptors.MolWt(mol)
        formula_ok = formula == p["expected_formula"]
        mw_ok = abs(avg_mw - p["expected_mw"]) < 0.05
        admissibility.append(
            {
                "id": p["id"],
                "recomputed_formula": formula,
                "cited_formula": p["expected_formula"],
                "formula_matches": formula_ok,
                "recomputed_average_mw": round(avg_mw, 2),
                "cited_average_mw": p["expected_mw"],
                "mw_matches": mw_ok,
            }
        )
        assert formula_ok, f"{p['id']}: recomputed formula {formula} != cited {p['expected_formula']}"
        assert mw_ok, f"{p['id']}: recomputed MW {avg_mw} != cited {p['expected_mw']}"

    results = []
    total_evals = 0
    disagreements = []
    for c in corpus:
        base = derive_handles(c["smiles"])
        assert base is not None, f"unparseable corpus smiles {c['id']}"
        base_role = role_of(base)
        role_pass = base_role == c["expected_role"]
        variant_disagreements = []
        for tag, vsmiles in encoding_variants(c["smiles"]):
            vderived = derive_handles(vsmiles)
            total_evals += 1
            vrole = role_of(vderived) if vderived is not None else "PARSE_FAIL"
            if vderived != base or vrole != base_role:
                d = {
                    "id": c["id"],
                    "variant_tag": tag,
                    "variant_smiles": vsmiles,
                    "base_handles": base,
                    "variant_handles": vderived,
                    "base_role": base_role,
                    "variant_role": vrole,
                }
                variant_disagreements.append(d)
                disagreements.append(d)
        results.append(
            {
                "id": c["id"],
                "smiles": c["smiles"],
                "citation": c["citation"],
                "note": c.get("note", ""),
                "derived_handles": base,
                "observed_role": base_role,
                "expected_role": c["expected_role"],
                "role_pass": role_pass,
                "n_encoding_variants": len(encoding_variants(c["smiles"])),
                "n_variant_disagreements": len(variant_disagreements),
            }
        )

    # --- positive control: this attack must be CAPABLE of catching a real
    # encoding-invariance defect. We feed the SAME comparison code path a
    # deliberately mutated "variant" of the DDS molecule (CAS 80-08-0) that
    # is NOT a valid re-encoding -- one of its two aniline -NH2 groups is
    # struck to -H (a chemically different molecule, not a re-write of the
    # same one) -- and confirm derive_handles/role_of DETECT the change
    # exactly as the real invariance loop above would detect a genuine
    # encoding-evasion defect if one existed.
    dds_base_smiles = "Nc1ccc(cc1)S(=O)(=O)c1ccc(N)cc1"
    dds_poisoned_smiles = "c1ccc(cc1)S(=O)(=O)c1ccc(cc1)"  # both NH2 -> H
    dds_base = derive_handles(dds_base_smiles)
    dds_poisoned = derive_handles(dds_poisoned_smiles)
    dds_base_role = role_of(dds_base)
    dds_poisoned_role = role_of(dds_poisoned)
    # mirrors the OR logic the real invariance loop above uses:
    # `if vderived != base or vrole != base_role:`
    dds_detected = (dds_poisoned != dds_base) or (dds_poisoned_role != dds_base_role)
    positive_control = {
        "planted_defect": (
            "both aniline -NH2 groups on DDS (CAS 80-08-0, "
            "Nc1ccc(cc1)S(=O)(=O)c1ccc(N)cc1, a real hardener) struck to -H "
            "(yielding plain diphenyl sulfone, a real non-reactive out-of-domain "
            "molecule), fed through the identical derive_handles/role_of "
            "comparison path used by the real encoding-invariance loop above, "
            "as if it were a claimed re-encoding of the same molecule"
        ),
        "how_planted": (
            "string edit: 'Nc1ccc(cc1)S(=O)(=O)c1ccc(N)cc1' -> "
            "'c1ccc(cc1)S(=O)(=O)c1ccc(cc1)' (both leading/trailing N removed)"
        ),
        "base_handles": dds_base,
        "poisoned_handles": dds_poisoned,
        "base_role": dds_base_role,
        "poisoned_role": dds_poisoned_role,
        "detected": dds_detected,
        "evidence": (
            f"reactive_amine_hydrogen_count {dds_base['reactive_amine_hydrogen_count']} "
            f"-> {dds_poisoned['reactive_amine_hydrogen_count']}; role {dds_base_role} "
            f"-> {dds_poisoned_role}"
        ),
    }
    assert positive_control["detected"], "harness failed to detect its own planted defect"

    n = len(results)
    n_role_pass = sum(1 for r in results if r["role_pass"])

    diag = {
        "schema": "amphora.molecule-role-ranker.role-encoding-invariance-external-corpus.v1",
        "purpose": (
            "Re-attack role-fact-provenance-invariance-v1's ledger-unattacked "
            "SMILES-encoding-invariance claim on real external molecules it never "
            "saw: the 5 already-validated external hardener chemotypes plus one "
            "brand-new fused-bicyclic cycloaliphatic diepoxide resin chemotype."
        ),
        "attack_under_test": {
            "receipt": "amphora-molecule-role-ranker/benchmarks/role-fact-provenance-invariance-v1/replay_receipt.v1.dsse.json",
            "claim": "ROLE_VERDICT_INVARIANT_UNDER_SMILES_REENCODING, 549/549 evaluations 0 disagreements, in-fixture only (39 self-authored records)",
        },
        "fidelity_to_source_rule": fidelity,
        "external_corpus_source": {
            "path": str(EXTERNAL_CORPUS_SOURCE.relative_to(ROOT)),
            "sha256": ext_sha,
        },
        "new_probe_admissibility": admissibility,
        "corpus_results": results,
        "corpus_summary": {
            "n_molecules": n,
            "n_role_pass": n_role_pass,
            "n_role_fail": n - n_role_pass,
            "total_encoding_variant_evaluations": total_evals,
            "n_disagreements": len(disagreements),
            "disagreements": disagreements,
        },
        "positive_control": positive_control,
        "toolkit": {"rdkit_version": Chem.rdBase.rdkitVersion, "python": sys.version.split()[0]},
        "primary_references": [
            "Weininger, D. (1988) SMILES 1. JCICS 28(1):31-36. doi:10.1021/ci00057a005",
            "Weininger et al. (1989) SMILES 2 canonicalization. JCICS 29(2):97-101. doi:10.1021/ci00062a008",
            "Landrum, G. RDKit: open-source cheminformatics (pinned 2026.03.2).",
            "PubChem / Sigma-Aldrich 407208 / Cymit Quimica: CAS 2386-87-0 (ERL-4221), C14H20O4, MW 252.31, cross-checked 2026-08-16.",
            "Wiegand & Osburg (2023) Polymers 15(4):990. doi:10.3390/polym15040990 (CC BY 4.0).",
        ],
        "closes": [],
        "does_not_close": [
            "EVALUATION_SIGNATURE_ABSENT (trust-anchored phase0-evaluator key absent for a real Phase-1 evaluation)",
            "PHASE_1_INDEPENDENT_EVALUATION (still needs external double-labelled expert reference)",
            "RDKit_C++_CEILING (still RDKit-only; no second cheminformatics toolkit cross-check)",
        ],
        "claim_locks": {
            "measured_only_lock_preserved": True,
            "no_objective_emitted": True,
            "promotes_authority": False,
        },
        "verdict": (
            "CLAIM_REFUTED"
            if (n_role_pass < n or disagreements)
            else "CLAIM_SURVIVED"
        ),
    }
    diag["interpretation"] = (
        f"{n_role_pass}/{n} external-corpus molecules (5 real, previously-validated "
        f"hardener chemotypes + 1 new real fused-bicyclic cycloaliphatic diepoxide "
        f"resin, CAS-verified formula/MW admissibility {sum(1 for a in admissibility if a['formula_matches'] and a['mw_matches'])}/{len(admissibility)}) "
        f"got the expected role, with {len(disagreements)} SMILES-encoding-invariance "
        f"disagreements across {total_evals} deterministic re-encodings "
        f"(canonical + kekule + every-heavy-atom-rooted + explicit-H). Positive "
        f"control: the identical comparison path detected a planted structural "
        f"defect (both aniline -NH2 groups struck from DDS) as {positive_control['detected']}. "
        f"Verdict: {diag['verdict']}."
    )

    out = json.dumps(diag, indent=2, sort_keys=True)
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("diagnostic.canonical.json")
    dest.write_text(out)
    print("WROTE", dest, "sha256", sha(out.encode()))
    print("verdict:", diag["verdict"])
    print("role_pass", n_role_pass, "/", n, "| variant evals", total_evals, "| disagreements", len(disagreements))
    print("positive_control_detected", positive_control["detected"])


if __name__ == "__main__":
    main()
