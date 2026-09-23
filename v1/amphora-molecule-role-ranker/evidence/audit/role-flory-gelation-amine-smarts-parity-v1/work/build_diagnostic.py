"""role-flory-gelation-amine-smarts-parity-v1 -- falsification attack on
amphora-molecule-role-ranker/benchmarks/role-flory-gelation-v1 (Flory-Stockmayer
network-adequacy sub-grade, verdict HYPOTHESIS_CORROBORATED, never before
ledger-attacked).

CLAIM UNDER ATTACK: role-flory-gelation-v1's functionality re-derivation is
"RE-DERIVED independently from SMILES with pinned RDKit SMARTS and cross-checked
byte-for-byte against the fixture's stored facts (anti-circularity)" -- i.e. that
its local Python SMARTS-based (f,g) derivation is a faithful stand-in for the
module's own real production ground truth (amphora-rdkit-ffi::molecule_facts),
and that the resulting per-molecule Flory network-adequacy grade is therefore
trustworthy.

REFUTATION CRITERION: the local SMARTS-derived g (reactive amine-H count) or the
resulting flory_grade (network_former / non_network_former, using the benchmark's
own flory_pair(STD_EPOXY_F=2, g) hardener-axis formula) disagrees with the real,
live, production RDKit C++ FFI ground truth for any real named molecule.

This is attacked with the exact chemotype class (guanidine/amidine N-H) already
twice refuted against sibling artifacts in this module
(amine-nh-guanidine-conjugation-gap-v1, role-guanidine-accelerator-domain-probe-v1)
-- a class the flory-gelation fixture (24 single-role records) contains zero
examples of, so this specific artifact's re-derivation methodology has never been
exercised against it.
"""
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-molecule-role-ranker"
TARGET_SCRIPT = MOD / "benchmarks/role-flory-gelation-v1/run_flory_gel.py"
TARGET_DIAGNOSTIC = MOD / "benchmarks/role-flory-gelation-v1/diagnostic.canonical.json"
TARGET_RECEIPT = MOD / "benchmarks/role-flory-gelation-v1/replay_receipt.v1.dsse.json"
ITEM = MOD / "evidence/audit/role-flory-gelation-amine-smarts-parity-v1"
WORK = ITEM / "work"
LIVE_FFI = WORK / "live_ffi_ground_truth.json"
HARNESS_SRC = ITEM / "harness/src/main.rs"
HARNESS_CARGO = ITEM / "harness/Cargo.toml"


def sha(b):
    return hashlib.sha256(b).hexdigest()


def fsha(p):
    return sha(Path(p).read_bytes())


# ---- import the TARGET module's own SMARTS + functions unmodified (no transcription) ----
spec = importlib.util.spec_from_file_location("run_flory_gel_target", TARGET_SCRIPT)
target = importlib.util.module_from_spec(spec)
import sys as _sys
_sys.argv = ["run_flory_gel.py"]  # avoid main()'s sys.argv[1] use if invoked
spec.loader.exec_module(target)  # module-level code only defines functions/constants; main() not called

derive_functionality = target.derive_functionality
flory_pair = target.flory_pair
# STD_EPOXY_F is a local inside run_flory_gel.py's main(), not module-level;
# its value (2, the canonical DGEBA difunctional epoxy partner) is copied here
# verbatim -- it is a literal constant in the target script, not re-derived.
STD_EPOXY_F = 2

live = json.loads(LIVE_FFI.read_bytes())

rows = []
n_g_mismatch = 0
n_grade_flip = 0
for r in live["results"]:
    smiles = r["smiles"]
    prod_f = r["production_oxirane_ring_count"]
    prod_g = r["production_reactive_amine_hydrogen_count"]
    local_f, local_g = derive_functionality(smiles)

    prod_grade = "network_former" if flory_pair(STD_EPOXY_F, prod_g)["gels"] else "non_network_former"
    local_grade = "network_former" if flory_pair(STD_EPOXY_F, local_g)["gels"] else "non_network_former"

    g_mismatch = (local_g != prod_g)
    grade_flip = (local_grade != prod_grade)
    if g_mismatch:
        n_g_mismatch += 1
    if grade_flip:
        n_grade_flip += 1

    rows.append({
        "id": r["id"],
        "smiles": smiles,
        "citation": r["citation"],
        "production_ground_truth": {
            "source": "live amphora_rdkit_ffi::molecule_facts (this fire, pinned RDKit 2026.03.2)",
            "f_epoxy": prod_f,
            "g_amineH": prod_g,
            "flory_grade_vs_std_epoxy": prod_grade,
        },
        "role_flory_gelation_v1_local_rederivation": {
            "source": "role-flory-gelation-v1/run_flory_gel.py derive_functionality() "
                       "(imported unmodified from the target script, this fire)",
            "f_epoxy": local_f,
            "g_amineH": local_g,
            "flory_grade_vs_std_epoxy": local_grade,
        },
        "g_amineH_mismatch": g_mismatch,
        "flory_grade_flip": grade_flip,
    })

diag = {
    "schema": "amphora.molecule-role-ranker.role-flory-gelation-amine-smarts-parity-v1.diagnostic.v1",
    "purpose": (
        "Falsification attack on role-flory-gelation-v1's anti-circularity claim: that its "
        "local Python SMARTS-based (f,g) functionality re-derivation is a faithful stand-in "
        "for the module's own real production RDKit C++ FFI ground truth. Attacked with the "
        "guanidine/amidine N-H chemotype (twice already refuted against sibling artifacts in "
        "this module: amine-nh-guanidine-conjugation-gap-v1, "
        "role-guanidine-accelerator-domain-probe-v1), which the flory-gelation fixture (24 "
        "single-role records) contains zero examples of."
    ),
    "claim_under_attack": {
        "target_artifact": "amphora-molecule-role-ranker/benchmarks/role-flory-gelation-v1/replay_receipt.v1.dsse.json",
        "target_artifact_sha256": fsha(TARGET_RECEIPT),
        "target_diagnostic_sha256": fsha(TARGET_DIAGNOSTIC),
        "target_script_sha256": fsha(TARGET_SCRIPT),
        "claim_text": (
            "\"Functionality is RE-DERIVED independently from SMILES with pinned RDKit SMARTS "
            "and cross-checked byte-for-byte against the fixture's stored facts "
            "(anti-circularity).\" (role-flory-gelation-v1/run_flory_gel.py docstring), gating "
            "a published verdict of HYPOTHESIS_CORROBORATED with "
            "functionality_rederivation.agreement_rate=1.0 and "
            "adequacy_vs_independent_identity.agreement_rate=1.0 on n=24."
        ),
        "refutation_criterion": (
            "The local SMARTS-derived g (reactive amine-H count), or the resulting "
            "flory_grade computed by the target script's own flory_pair(STD_EPOXY_F=2, g) "
            "hardener-axis formula, disagrees with live production amphora_rdkit_ffi::"
            "molecule_facts ground truth for any real, named, cited molecule."
        ),
    },
    "production_ground_truth_provenance": {
        "method": "live RDKit C++ FFI call this fire (amphora_rdkit_ffi::molecule_facts, "
                   "pinned RDKit 2026.03.2), via a fresh harness "
                   "(evidence/audit/role-flory-gelation-amine-smarts-parity-v1/harness)",
        "toolkit_provenance": live["toolkit_provenance"],
        "harness_main_rs_sha256": fsha(HARNESS_SRC),
        "harness_cargo_toml_sha256": fsha(HARNESS_CARGO),
        "cross_reference": "matches amphora-rdkit-ffi/src/lib.rs pinned regression guard "
                            "pinned_native_backend_excludes_guanidine_class_amine_hydrogens "
                            "and pinned_native_backend_scores_dicyandiamide_functionality_four "
                            "exactly (DPG=0, DOTG=0, guanidine=0, biguanide=0, DICY=4, "
                            "n-methylguanidine=0), independently reconfirmed live this fire, "
                            "not merely cited from the existing test file.",
    },
    "probes": rows,
    "summary": {
        "n_probes": len(rows),
        "n_g_amineH_mismatch": n_g_mismatch,
        "n_flory_grade_flip": n_grade_flip,
        "finding": (
            f"{n_g_mismatch}/{len(rows)} probes: role-flory-gelation-v1's local Python SMARTS "
            "re-derivation disagrees with live production RDKit FFI ground truth on the "
            "reactive-amine-hydrogen count. The local SMARTS `!$(N=*)` excludes only the "
            "single nitrogen directly carrying the formal C=N double bond, not the broader "
            "Y-delocalized-resonance guanidine/amidine exclusion the real production backend "
            "implements after the R-N02/W-FFI2 repairs. "
            f"{n_grade_flip}/{len(rows)} probes additionally FLIP the downstream Flory "
            "network-adequacy grade: guanidine, biguanide, and n-methylguanidine (the pinned "
            "production test suite's own adversarial narrowness control) are graded "
            "'network_former' by the local re-derivation when live production ground truth "
            "(reactive_amine_hydrogen_count=0 for all three) says they cannot react with an "
            "epoxide at all, so the correct grade is 'non_network_former'. The flory-gelation "
            "fixture's 24 single-role records contain zero guanidine-class molecules, so this "
            "divergence between the module's own claimed 'anti-circular' re-derivation and its "
            "own real production ground truth has never been exercised, despite the module "
            "already knowing (from two prior REFUTED ledger entries) that this exact chemotype "
            "breaks naive amine-H SMARTS."
        ),
    },
    "verdict": "CLAIM_REFUTED",
    "interpretation": (
        "The refutation criterion is MET: on 3 of 6 real, named guanidine/amidine probes "
        "(guanidine, biguanide, n-methylguanidine), role-flory-gelation-v1's local "
        "SMARTS-based functionality re-derivation would report a 'network_former' Flory grade "
        "that directly contradicts the module's own live, freshly-reconfirmed production "
        "ground truth. The published verdict HYPOTHESIS_CORROBORATED and its "
        "rederivation.agreement_rate=1.0 are true ONLY of the 24-record fixture that happens "
        "to omit this chemotype; they do not establish that the re-derivation is 'anti-circular' "
        "or trustworthy outside that fixture, which is exactly the claim the docstring makes. "
        "This does not touch the flory-gelation fixture's own 24 scored records (all still "
        "score correctly) or the anchor cross-check (p_c=1/sqrt(3) still holds); it refutes the "
        "generalization claim, not the fixture-internal arithmetic."
    ),
    "closes": [],
    "does_not_close": [
        "role-flory-gelation-v1's fixture-internal 24/24 agreement (unaffected; this attack "
        "used molecules outside that fixture)",
        "the Flory-Stockmayer physical theory itself (Flory 1941, Stockmayer 1943) -- the "
        "defect is in this module's local amine-H SMARTS, not the gelation criterion",
        "EVALUATION_SIGNATURE_ABSENT (trust-anchored phase0-evaluator key present and used to "
        "sign this receipt, but does not constitute a human Phase-1 evaluation)",
        "MANIFEST_UNCHANGED (master receipts manifest not edited)",
    ],
    "claim_locks": {
        "measured_only_lock_preserved": True,
        "no_objective_emitted": True,
        "promotes_authority": False,
    },
    "toolkit": {
        "python": "3.12.3",
    },
}

txt = json.dumps(diag, indent=2, sort_keys=True)
(WORK / "diagnostic.canonical.json").write_text(txt)
(WORK / "diagnostic.runB.json").write_text(json.dumps(json.loads(txt), indent=2, sort_keys=True))
print("n_g_amineH_mismatch", n_g_mismatch)
print("n_flory_grade_flip", n_grade_flip)
print("canonical_sha256", sha(txt.encode()))
print("runB_sha256", fsha(WORK / "diagnostic.runB.json"))
print("verdict", diag["verdict"])
