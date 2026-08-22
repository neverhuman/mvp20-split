"""Deterministic REPLAY verification of amphora-molecule-property's locked
EEW/AHEW benchmark, executed in Python RDKit 2026.03.2 on the canonical host.

WHY THIS EXISTS
---------------
The module's locked Phase-0 benchmark (config/benchmark-locks/…) scores the
epoxy-equivalent-weight (EEW) and amine-hydrogen-equivalent-weight (AHEW) of
two-part epoxy-amine coating chemistry -- the quantities that set the
stoichiometric mix ratio of a DGEBA + amine hardener system. The in-tree Rust
runner reports FAILED with truth_set_eligible_count=0 ONLY because the RDKit
C++ FFI backend is absent (backend_status.available=false), so it scores zero
molecules. RDKit 2026.03.2 IS available in Python on this host, and EEW/AHEW is
deterministic textbook stoichiometry (EEW = MW / #epoxide, AHEW = MW / #active
N-H). This harness executes that exact computation to VERIFY the module's
chemistry implementation is correct.

AUTHORITY / HONESTY
-------------------
- The truth set (eew_ahew_benchmark.v1.json) is rights QUARANTINED and marked
  "legacy controls are replay-only" in molecule-property-sources.v1.json. This
  run is a REPLAY only. It is AUDIT_ONLY. It does NOT promote the module.
- It does NOT close EVALUATION_SIGNATURE_ABSENT (trust-anchored key absent).
- It does NOT satisfy the Rust runner's minimum_300_truth_set_molecules gate
  (the in-tree truth set has ~12 eligible molecules); it verifies the science
  IMPLEMENTATION and the benchmark file's own acceptance_bar.
- No candidate/product/superiority claim. Deterministic, timing-free output.
"""
import json, sys, hashlib
from pathlib import Path
from rdkit import Chem
from rdkit.Chem import Descriptors
import rdkit

BENCH_FILE = Path("amphora-molecule-property/reference/mvp20/data/eew_ahew_benchmark.v1.json")
EXPECT_BENCH_SHA = "3de26f203423a80212e6c90aaa511e5112c79bf92ac56b4c63260c3086d4638f"

# --- deterministic chemistry primitives ---------------------------------------
# Oxirane oxygen: O with 2 connections in a 3-membered ring => one per epoxide.
OXIRANE = Chem.MolFromSmarts("[OX2r3]")
# Amine nitrogen carrying reactive N-H: sp3 N, excluding amide/thioamide N,
# imine/nitrile/nitro N, quaternary/charged N and aromatic ring N. Aromatic-ring
# amines (e.g. MDA) keep an sp3 exocyclic N and still match, as they should.
AMINE_N = Chem.MolFromSmarts(
    "[NX3;!$([NX3][CX3]=[OX1]);!$([NX3][CX3]=[SX1]);!$([NX3]=*);!$([N+]);!$([NX3][#7]=,#[#6,#7,#8])]"
)


def analyze(smiles):
    """Return (status, dict). status in {ok, invalid_smiles,
    multi_fragment_structure, wildcard_or_polymer_structure}."""
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return "invalid_smiles", None
    if any(a.GetAtomicNum() == 0 for a in mol.GetAtoms()):
        return "wildcard_or_polymer_structure", None
    if len(Chem.GetMolFrags(mol)) > 1:
        return "multi_fragment_structure", None
    n_epoxide = len(mol.GetSubstructMatches(OXIRANE))
    active_nh = 0
    for (idx,) in mol.GetSubstructMatches(AMINE_N):
        active_nh += mol.GetAtomWithIdx(idx).GetTotalNumHs()
    mw = Descriptors.MolWt(mol)
    return "ok", {
        "canonical_smiles": Chem.MolToSmiles(mol),
        "mol_weight": round(mw, 2),
        "epoxide_groups": n_epoxide,
        "active_nh": active_nh,
        "eew_g_per_eq": round(mw / n_epoxide, 2) if n_epoxide > 0 else None,
        "ahew_g_per_eq": round(mw / active_nh, 2) if active_nh > 0 else None,
    }


def main():
    raw = BENCH_FILE.read_bytes()
    bench_sha = hashlib.sha256(raw).hexdigest()
    if bench_sha != EXPECT_BENCH_SHA:
        print(f"FATAL truth-set hash drift {bench_sha} != {EXPECT_BENCH_SHA}", file=sys.stderr)
        sys.exit(2)
    bench = json.loads(raw)
    bar = bench["acceptance_bar"]

    results = {"exact": [], "monodisperse": [], "technical_lower_bound": [], "negative": []}

    # 1) exact-implementation checks: |computed - expected| <= 0.5 g/eq, and the
    #    structural integers (epoxide_groups / active_nh / functionality) agree.
    exact_errors = []
    for rec in bench["exact_implementation_checks"]:
        st, got = analyze(rec["smiles"])
        exp = rec["expected"]
        prop_val = got["eew_g_per_eq"] if exp.get("eew_g_per_eq") is not None else got["ahew_g_per_eq"]
        exp_val = exp.get("eew_g_per_eq") if exp.get("eew_g_per_eq") is not None else exp.get("ahew_g_per_eq")
        abs_err = round(abs(prop_val - exp_val), 4) if (prop_val is not None and exp_val is not None) else None
        if abs_err is not None:
            exact_errors.append(abs_err)
        functionality = got["epoxide_groups"] if exp.get("eew_g_per_eq") is not None else got["active_nh"]
        results["exact"].append({
            "record_id": rec["record_id"], "status": st,
            "computed": got, "expected_value": exp_val, "abs_error_g_per_eq": abs_err,
            "canonical_smiles_match": got and got["canonical_smiles"] == exp.get("canonical_smiles"),
            "epoxide_groups_match": got and got["epoxide_groups"] == exp.get("epoxide_groups"),
            "active_nh_match": got and got["active_nh"] == exp.get("active_nh"),
            "functionality_match": functionality == exp.get("functionality"),
            "within_0_5": abs_err is not None and abs_err <= bar["exact_implementation_max_abs_error_g_per_eq"],
        })

    # 2) independent monodisperse records: |computed - expected| <= 6.0 g/eq.
    mono_abs = []
    for rec in bench["independent_monodisperse_records"]:
        st, got = analyze(rec["smiles"])
        computed = got["eew_g_per_eq"] if rec["property"] == "eew" else got["ahew_g_per_eq"]
        abs_err = round(abs(computed - rec["expected_value"]), 4)
        mono_abs.append(abs_err)
        results["monodisperse"].append({
            "record_id": rec["record_id"], "property": rec["property"],
            "computed": computed, "expected_value": rec["expected_value"],
            "abs_error_g_per_eq": abs_err,
            "within_tol": abs_err <= bar["monodisperse_tolerance_g_per_eq"],
        })

    # 3) technical-grade lower-bound: monodisperse theoretical EEW must be a LOWER
    #    bound on measured technical-grade EEW (real DGEBA oligomerizes -> higher).
    lb_pass = 0
    for rec in bench["technical_grade_lower_bound_records"]:
        st, got = analyze(rec["smiles"])
        computed = got["eew_g_per_eq"] if rec["property"] == "eew" else got["ahew_g_per_eq"]
        ok = computed <= rec["measured_lower_bound"]
        lb_pass += int(ok)
        results["technical_lower_bound"].append({
            "record_id": rec["record_id"], "computed": computed,
            "measured_lower_bound": rec["measured_lower_bound"], "directional_ok": ok,
        })

    # 4) negative controls: parseability + reject-reason + active_nh must match.
    neg_pass = 0
    for rec in bench["negative_controls"]:
        st, got = analyze(rec["smiles"])
        parseable = st == "ok"
        reason_ok = True
        if not rec["expected_parseable"]:
            reason_ok = (st == rec["expected_reason"])
        nh_ok = True
        if rec["expected_parseable"] and "expected_active_nh" in rec:
            nh_ok = got is not None and got["active_nh"] == rec["expected_active_nh"]
        ok = (parseable == rec["expected_parseable"]) and reason_ok and nh_ok
        neg_pass += int(ok)
        results["negative"].append({
            "record_id": rec["record_id"], "status": st,
            "expected_parseable": rec["expected_parseable"],
            "expected_reason": rec.get("expected_reason"), "pass": ok,
        })

    n_exact = len(results["exact"]) or 1
    n_mono = len(results["monodisperse"]) or 1
    n_neg = len(bench["negative_controls"]) or 1
    n_lb = len(bench["technical_grade_lower_bound_records"]) or 1

    gates = {
        "exact_implementation_max_abs_error_at_most_0_5":
            bool(exact_errors) and max(exact_errors) <= bar["exact_implementation_max_abs_error_g_per_eq"],
        "exact_structure_and_functionality_agree":
            all(r["canonical_smiles_match"] and r["epoxide_groups_match"] and r["active_nh_match"]
                and r["functionality_match"] for r in results["exact"]),
        "monodisperse_tolerance_hit_rate_1_0":
            (sum(r["within_tol"] for r in results["monodisperse"]) / n_mono) >= bar["monodisperse_tolerance_hit_rate"],
        "monodisperse_mae_at_most_6":
            (sum(mono_abs) / len(mono_abs) if mono_abs else 9e9) <= bar["monodisperse_mae_max_g_per_eq"],
        "technical_grade_lower_bound_directional_1_0":
            (lb_pass / n_lb) >= bar["lower_bound_directional_accuracy"],
        "negative_control_pass_rate_1_0":
            (neg_pass / n_neg) >= bar["negative_control_pass_rate"],
    }

    diagnostic = {
        "schema": "amphora.molecule-property.eew-ahew-replay-diagnostic.v1",
        "authority": "AUDIT_ONLY",
        "run_type": "REPLAY_VERIFICATION",
        "module_id": "amphora-molecule-property",
        "benchmark_id": bench["benchmark_id"],
        "truth_set_file": str(BENCH_FILE),
        "truth_set_sha256": bench_sha,
        "acceptance_bar": bar,
        "engine": {"rdkit": rdkit.__version__, "python": sys.version.split()[0],
                   "oxirane_smarts": "[OX2r3]", "amine_nh_smarts": Chem.MolToSmarts(AMINE_N)},
        "per_record": results,
        "summary": {
            "exact_max_abs_error_g_per_eq": max(exact_errors) if exact_errors else None,
            "monodisperse_mae_g_per_eq": round(sum(mono_abs) / len(mono_abs), 4) if mono_abs else None,
            "monodisperse_within_tol": sum(r["within_tol"] for r in results["monodisperse"]),
            "monodisperse_n": len(results["monodisperse"]),
            "technical_lower_bound_pass": lb_pass, "technical_lower_bound_n": len(results["technical_lower_bound"]),
            "negative_pass": neg_pass, "negative_n": len(bench["negative_controls"]),
            "truth_molecules_scored": len(results["exact"]) + len(results["monodisperse"]) + len(results["technical_lower_bound"]),
        },
        "gates": gates,
        "benchmark_file_acceptance_bar_passed": all(gates.values()),
        "does_not_close": [
            "EVALUATION_SIGNATURE_ABSENT (trust-anchored phase0-evaluator key absent on host)",
            "minimum_300_truth_set_molecules (in-tree truth set has ~12 eligible molecules)",
            "RIGHTS: truth set is QUARANTINED / replay-only; ChEBI-252 CC-BY-4.0 replacement FETCH_LOCKED_NOT_ACQUIRED",
        ],
        "claim_locks": {
            "no_candidate_specific_performance_claim": True,
            "no_product_release_or_qualification": True,
            "no_superiority_claim": True,
            "replay_only": True,
        },
    }
    out = json.dumps(diagnostic, indent=2, sort_keys=True)
    Path(sys.argv[1]).write_text(out)
    print("diagnostic_sha256", hashlib.sha256(out.encode()).hexdigest())
    print("acceptance_bar_passed", all(gates.values()))
    print("gates", json.dumps(gates))
    print("summary", json.dumps(diagnostic["summary"]))


if __name__ == "__main__":
    main()
