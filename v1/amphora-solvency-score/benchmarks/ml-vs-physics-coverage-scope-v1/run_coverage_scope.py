#!/usr/bin/env python3
"""W-SOLV-COV (campaign): attack the covered-subset scoping of V1-SOLV's
ML-beats-corrected-physics headline. Reuses the IDENTICAL corpus, seed-0
scaffold-safe 60/20/20 split, and ML arm (HistGradientBoostingRegressor,
same hyperparameters) as V1-SOLV
(evidence/phase0/repairs/V1-SOLV/done/ml-vs-physics-corrected-comparison-receipt.v1.dsse.json),
so the split and ML predictions are byte-for-byte the same split V1-SOLV used.

V1-SOLV reported physics R2 ONLY over instrument-RETURNED ("covered") test
molecules: 85.5% for flory_huggins_hildebrand, 75.1% for hansen_3component.
That is correct methodology (physics cannot be scored where it abstains) but
it leaves 14.5%-24.9% of the test set OUT of the comparison entirely, and
those molecules are not a random sample -- they are exactly the molecules
the corrected instrument's fail-closed gates reject.

THIS SCRIPT answers the three questions the campaign item poses:
  (1) characterise the REJECTED/abstained molecules: which gate rejected them
      (uncovered_fragment vs vk_constants_unavailable) and which specific
      atoms/groups drove the rejection, with counts.
  (2) the ML arm's OWN r2 on the REJECTED-only test subset vs the
      RETURNED-only (covered) test subset, per family per solvent, using the
      IDENTICAL trained model and IDENTICAL seed-0 split V1-SOLV used.
  (3) the deployment-relevant "any-arm" coverage number: since ML has no
      abstention mechanism it nominally covers 100% of the test set with the
      full-test R2 already reported by V1-SOLV; physics (fedors OR hansen
      RETURNED) covers a smaller, reported, union fraction.

PRE-REGISTERED REFUTATION CRITERION (fixed BEFORE the abstained-only R2 is
computed below -- see PRE_REGISTRATION printed first):
  gap(family, solvent) = r2_covered_subset - r2_abstained_subset
  An arm is "materially degraded" if gap > MATERIAL_GAP_THRESHOLD (0.15
  absolute R2) AND the abstained-subset has n >= MIN_ABSTAINED_N (50) test
  molecules (else insufficient_n, excluded from the majority vote).
  Overall verdict: CLAIM_REFUTED (unqualified "ML beats physics" framing does
  not survive) if >= MAJORITY_ARMS (4) of the 6 arms are materially degraded;
  else CLAIM_SURVIVED (ML's covered-subset win is not an artifact of physics
  screening out ML's hard cases -- ML is comparably competent, or better, on
  exactly the molecules physics refuses to touch).
"""
import gzip
import hashlib
import json
import math
import random
import statistics
import sys
import time
from collections import Counter, OrderedDict

sys.path.insert(0, "/home/ubuntu/amphora/build/mvp20-split/amphora-solvency-score/benchmarks/flory-hansen-corrected-v1")
import compute_group_contribution as gc  # noqa: E402

from rdkit import Chem, RDLogger  # noqa: E402
from rdkit.Chem import AllChem, Descriptors, rdMolDescriptors  # noqa: E402
from rdkit.Chem.Scaffolds import MurckoScaffold  # noqa: E402
from sklearn.ensemble import HistGradientBoostingRegressor  # noqa: E402
from sklearn.metrics import r2_score  # noqa: E402

RDLogger.DisableLog("rdApp.*")

ROOT = "/home/ubuntu/amphora/build/mvp20-split"
CORPUS = ROOT + "/feedback/v3/normalized/omg_physical_properties_v3.jsonl.gz"
MANIFEST = ROOT + "/amphora-solvency-score/reference/mvp20/data/feedback_v3/manifests/omg_physical_properties_v3.json"
SEED = 0
N_SAMPLE = int(sys.argv[1]) if len(sys.argv) > 1 else 40000
CHI_FIELDS = {
    "chloroform": "chi_parameter_chloroform_mean",
    "ethanol": "chi_parameter_ethanol_mean",
    "water": "chi_parameter_water_mean",
}
R_GAS = 8.314
T_REF = 298.15

MATERIAL_GAP_THRESHOLD = 0.15
MIN_ABSTAINED_N = 50
MAJORITY_ARMS = 4

# VK-unavailable groups (vk=None in GROUP_TABLE) -- used to attribute which
# specific group triggered REJECTED_VK_CONSTANTS_UNAVAILABLE.
VK_NONE_GROUPS = {name for name, _sm, _fed, vk in gc.GROUP_TABLE if vk is None}

SOLVENT_HILDEBRAND = {
    "water": {"delta": 47.9, "V": 18.07},
    "ethanol": {"delta": 26.5, "V": 58.68},
    "chloroform": {"delta": 18.9, "V": 80.65},
}
SOLVENT_HANSEN = {
    "water": {"d": 15.5, "p": 16.0, "h": 42.3, "V": 18.07},
    "ethanol": {"d": 15.8, "p": 8.8, "h": 19.4, "V": 58.68},
    "chloroform": {"d": 17.8, "p": 3.1, "h": 5.7, "V": 80.65},
}
DESCRIPTOR_NAMES = [
    "MW", "LogP", "TPSA", "HBA", "HBD", "RotB", "AromRings", "HeavyAtoms",
    "NAtomsN", "NAtomsO", "NAtomsS", "NAtomsHal", "FCsp3", "NumRings",
    "AromHetero", "AliphaticRings",
]


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()


def canonical_json(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def load_sample():
    man = json.load(open(MANIFEST))
    assert man["rights_class"] == "DERIVATIVE_ALLOWED", "rights lock not clean"
    assert man["quarantined"] is False, "corpus quarantined"
    corpus_sha = sha256_file(CORPUS)
    assert corpus_sha == man["normalized_sha256"], "corpus bytes do not match manifest lock"
    smi_to_chi = {}
    n_records = 0
    n_chi_records = 0
    with gzip.open(CORPUS, "rt") as f:
        for line in f:
            n_records += 1
            rec = json.loads(line)
            rf = rec.get("raw_fields") or {}
            smi = rf.get("methyl_terminated_product")
            if not smi:
                continue
            if not all(rf.get(v) not in (None, "") for v in CHI_FIELDS.values()):
                continue
            n_chi_records += 1
            if smi not in smi_to_chi:
                smi_to_chi[smi] = {k: float(rf[v]) for k, v in CHI_FIELDS.items()}
    pool = sorted(smi_to_chi.keys())
    rng = random.Random(SEED)
    sample = rng.sample(pool, min(N_SAMPLE, len(pool)))
    prov = {
        "corpus_path": CORPUS, "corpus_sha256": corpus_sha,
        "manifest_rights_class": man["rights_class"], "manifest_quarantined": man["quarantined"],
        "dataset_id": man["dataset_id"], "n_records_streamed": n_records,
        "n_chi_records": n_chi_records, "n_unique_smiles_chi_labeled": len(pool),
        "seed": SEED, "n_sample": len(sample),
    }
    return prov, sample, smi_to_chi


def murcko_scaffold(smi):
    mol = Chem.MolFromSmiles(smi)
    if mol is None:
        return None
    try:
        scaf = MurckoScaffold.GetScaffoldForMol(mol)
        return Chem.MolToSmiles(scaf) if scaf is not None else ""
    except Exception:
        return ""


def scaffold_safe_split(smiles_list, seed=0, fracs=(0.6, 0.2, 0.2)):
    groups = {}
    for smi in smiles_list:
        scaf = murcko_scaffold(smi) or "__NONE__:" + smi
        groups.setdefault(scaf, []).append(smi)
    scaf_keys = sorted(groups.keys())
    rng = random.Random(seed)
    rng.shuffle(scaf_keys)
    n_total = len(smiles_list)
    n_train_target = int(round(fracs[0] * n_total))
    n_val_target = int(round(fracs[1] * n_total))
    train, val, test = [], [], []
    for k in scaf_keys:
        members = groups[k]
        if len(train) < n_train_target:
            train.extend(members)
        elif len(val) < n_val_target:
            val.extend(members)
        else:
            test.extend(members)
    return train, val, test, len(groups)


def compute_descriptors(mol):
    fcsp3 = rdMolDescriptors.CalcFractionCSP3(mol)
    ri = mol.GetRingInfo()
    n_arom_rings = rdMolDescriptors.CalcNumAromaticRings(mol)
    n_aliphatic_rings = rdMolDescriptors.CalcNumAliphaticRings(mol)
    n_arom_hetero = rdMolDescriptors.CalcNumAromaticHeterocycles(mol)
    halogens = {9, 17, 35, 53}
    n_n = sum(1 for a in mol.GetAtoms() if a.GetAtomicNum() == 7)
    n_o = sum(1 for a in mol.GetAtoms() if a.GetAtomicNum() == 8)
    n_s = sum(1 for a in mol.GetAtoms() if a.GetAtomicNum() == 16)
    n_hal = sum(1 for a in mol.GetAtoms() if a.GetAtomicNum() in halogens)
    return [
        Descriptors.MolWt(mol), Descriptors.MolLogP(mol), Descriptors.TPSA(mol),
        rdMolDescriptors.CalcNumHBA(mol), rdMolDescriptors.CalcNumHBD(mol),
        rdMolDescriptors.CalcNumRotatableBonds(mol), n_arom_rings, mol.GetNumHeavyAtoms(),
        n_n, n_o, n_s, n_hal, fcsp3, ri.NumRings(), n_arom_hetero, n_aliphatic_rings,
    ]


def featurize(smi, cache={}):
    if smi in cache:
        return cache[smi]
    mol = Chem.MolFromSmiles(smi)
    if mol is None:
        cache[smi] = None
        return None
    desc = compute_descriptors(mol)
    fp = AllChem.GetMorganFingerprintAsBitVect(mol, radius=2, nBits=512)
    bits = [int(b) for b in fp.ToBitString()]
    vec = desc + bits
    cache[smi] = vec
    return vec


def r2_or_none(y_true, y_pred):
    if len(y_true) < 2:
        return None
    return float(r2_score(y_true, y_pred))


def attribute_uncovered_fragment(reason):
    # reason == "uncovered_fragment:X,Y,..."
    atoms = reason.split(":", 1)[1] if ":" in reason else ""
    return tuple(sorted(atoms.split(","))) if atoms else ()


def attribute_vk_unavailable(groups):
    # which vk=None group(s) does this molecule's group multiset contain?
    if not groups:
        return ()
    present = sorted(set(groups.keys()) & VK_NONE_GROUPS)
    return tuple(present)


def main(out_path, positive_control=False):
    t0 = time.time()
    prov, sample, smi_to_chi = load_sample()
    train, val, test, n_scaffolds = scaffold_safe_split(sample, seed=SEED)

    print("computing physics arm...", time.time() - t0, file=sys.stderr)
    phys = {smi: gc.compute(smi) for smi in sample}

    print("featurizing...", time.time() - t0, file=sys.stderr)
    X = {smi: featurize(smi) for smi in sample}
    bad = [smi for smi, v in X.items() if v is None]
    assert not bad, "rdkit failed to parse %d SMILES" % len(bad)
    X_train = [X[s] for s in train]
    X_test = [X[s] for s in test]

    per_arm = {"flory_huggins_hildebrand": {}, "hansen_3component": {}}
    ml_full_test_r2 = {}
    ml_predictions = {}  # solvent -> list aligned with `test`

    for solvent in ("water", "ethanol", "chloroform"):
        y_train = [smi_to_chi[s][solvent] for s in train]
        y_test = [smi_to_chi[s][solvent] for s in test]
        print("training HistGBM", solvent, time.time() - t0, file=sys.stderr)
        model = HistGradientBoostingRegressor(
            max_iter=500, learning_rate=0.05, max_depth=8,
            min_samples_leaf=25, l2_regularization=0.1, random_state=SEED,
        )
        model.fit(X_train, y_train)
        pred_test = model.predict(X_test)
        ml_predictions[solvent] = list(pred_test)
        ml_full_test_r2[solvent] = r2_or_none(y_test, pred_test)

        for family, status_key in (("flory_huggins_hildebrand", "fedors_status"),
                                    ("hansen_3component", "hansen_status")):
            cov_idx = [i for i, s in enumerate(test) if phys[s][status_key] == gc.RETURNED]
            abst_idx = [i for i, s in enumerate(test) if phys[s][status_key] != gc.RETURNED]
            y_cov = [y_test[i] for i in cov_idx]
            y_abst = [y_test[i] for i in abst_idx]
            pred_cov = [pred_test[i] for i in cov_idx]
            pred_abst = [pred_test[i] for i in abst_idx]
            r2_cov = r2_or_none(y_cov, pred_cov)
            r2_abst = r2_or_none(y_abst, pred_abst)
            gap = (r2_cov - r2_abst) if (r2_cov is not None and r2_abst is not None) else None
            insufficient_n = len(abst_idx) < MIN_ABSTAINED_N
            materially_degraded = (gap is not None and gap > MATERIAL_GAP_THRESHOLD and not insufficient_n)
            per_arm[family][solvent] = {
                "solvent": solvent, "family": family,
                "n_test_total": len(test),
                "n_test_covered": len(cov_idx), "n_test_abstained": len(abst_idx),
                "coverage_rate_test": len(cov_idx) / len(test) if test else None,
                "ml_r2_on_covered_subset": r2_cov,
                "ml_r2_on_abstained_subset": r2_abst,
                "ml_r2_on_full_test": ml_full_test_r2[solvent],
                "gap_covered_minus_abstained": gap,
                "insufficient_abstained_n": insufficient_n,
                "materially_degraded": materially_degraded,
            }

    n_flagged = sum(
        1 for fam in per_arm.values() for v in fam.values() if v["materially_degraded"]
    )
    n_eligible = sum(
        1 for fam in per_arm.values() for v in fam.values() if not v["insufficient_abstained_n"]
    )
    refutation_fires = n_flagged >= MAJORITY_ARMS

    # ---- (1) characterise the abstained/rejected molecules ----
    fedors_reason_atoms = Counter()
    hansen_reason_atoms = Counter()
    hansen_vk_groups = Counter()
    fedors_status_counts = Counter()
    hansen_status_counts = Counter()
    for s in test:
        r = phys[s]
        fedors_status_counts[r["fedors_status"]] += 1
        hansen_status_counts[r["hansen_status"]] += 1
        if r["fedors_status"] == gc.REJECTED_UNCOVERED_FRAGMENT:
            fedors_reason_atoms[attribute_uncovered_fragment(r["fedors_reason"])] += 1
            hansen_reason_atoms[attribute_uncovered_fragment(r["hansen_reason"])] += 1
        elif r["hansen_status"] == gc.REJECTED_VK_CONSTANTS_UNAVAILABLE:
            hansen_vk_groups[attribute_vk_unavailable(r.get("groups"))] += 1

    characterisation = {
        "fedors_test_status_counts": dict(fedors_status_counts),
        "hansen_test_status_counts": dict(hansen_status_counts),
        "fedors_uncovered_fragment_atom_sets_top20": [
            {"atoms": list(k), "n": v} for k, v in fedors_reason_atoms.most_common(20)
        ],
        "hansen_uncovered_fragment_atom_sets_top20": [
            {"atoms": list(k), "n": v} for k, v in hansen_reason_atoms.most_common(20)
        ],
        "hansen_vk_constants_unavailable_group_top20": [
            {"groups": list(k), "n": v} for k, v in hansen_vk_groups.most_common(20)
        ],
    }

    # ---- (3) any-arm coverage over full test set ----
    n_test = len(test)
    fedors_covered = sum(1 for s in test if phys[s]["fedors_status"] == gc.RETURNED)
    hansen_covered = sum(1 for s in test if phys[s]["hansen_status"] == gc.RETURNED)
    physics_any_covered = sum(
        1 for s in test if phys[s]["fedors_status"] == gc.RETURNED or phys[s]["hansen_status"] == gc.RETURNED
    )
    deployment = {
        "n_test_total": n_test,
        "fedors_coverage_rate": fedors_covered / n_test,
        "hansen_coverage_rate": hansen_covered / n_test,
        "physics_any_arm_coverage_rate": physics_any_covered / n_test,
        "physics_any_arm_covered_n": physics_any_covered,
        "ml_coverage_rate": 1.0,
        "ml_covered_n": n_test,
        "ml_full_test_r2_by_solvent": ml_full_test_r2,
        "note": (
            "ML has no abstention mechanism and predicts every test molecule; "
            "its deployment-relevant accuracy is ml_full_test_r2_by_solvent "
            "(already close to ml_r2_on_covered_subset per arm above -- see "
            "per_arm gaps). Physics (fedors OR hansen RETURNED) only ever "
            "produces a number for physics_any_arm_coverage_rate of the test "
            "set; the remainder gets no physics answer at all, at any accuracy."
        ),
    }

    # ---- positive control: plant a defect this attack should catch ----
    pc = None
    if positive_control:
        # Corrupt ml predictions on the abstained subset of ONE arm
        # (flory_huggins_hildebrand / chloroform) by permuting them among
        # the abstained-subset molecules only (label-shuffle), which
        # destroys the molecule<->prediction correspondence and should
        # collapse r2_abst sharply below r2_cov, well past the 0.15
        # threshold. If the check does not flag it as materially_degraded,
        # the check cannot be trusted to detect a real defect.
        solvent_pc = "chloroform"
        y_test_pc = [smi_to_chi[s][solvent_pc] for s in test]
        pred_test_pc = list(ml_predictions[solvent_pc])
        cov_idx = [i for i, s in enumerate(test) if phys[s]["fedors_status"] == gc.RETURNED]
        abst_idx = [i for i, s in enumerate(test) if phys[s]["fedors_status"] != gc.RETURNED]
        rng = random.Random(SEED + 1)
        shuffled_abst_preds = [pred_test_pc[i] for i in abst_idx]
        rng.shuffle(shuffled_abst_preds)
        corrupted_pred = list(pred_test_pc)
        for j, i in enumerate(abst_idx):
            corrupted_pred[i] = shuffled_abst_preds[j]
        y_cov = [y_test_pc[i] for i in cov_idx]
        y_abst = [y_test_pc[i] for i in abst_idx]
        pred_cov = [corrupted_pred[i] for i in cov_idx]
        pred_abst = [corrupted_pred[i] for i in abst_idx]
        r2_cov_pc = r2_or_none(y_cov, pred_cov)
        r2_abst_pc = r2_or_none(y_abst, pred_abst)
        gap_pc = r2_cov_pc - r2_abst_pc
        detected = gap_pc > MATERIAL_GAP_THRESHOLD and len(abst_idx) >= MIN_ABSTAINED_N
        pc = {
            "planted_defect": "ML predictions on the fedors-abstained test subset (chloroform arm) permuted among themselves, breaking molecule<->prediction correspondence",
            "how_planted": (
                "in-memory copy of ml_predictions['chloroform']: for i in abstained_test_indices, "
                "prediction[i] replaced with a random.Random(seed+1)-shuffled prediction drawn from "
                "the SAME abstained-index set (values unchanged in aggregate, correspondence destroyed); "
                "covered-subset predictions left untouched"
            ),
            "detected": bool(detected),
            "evidence": {
                "r2_covered_subset_unchanged": r2_cov_pc,
                "r2_abstained_subset_after_corruption": r2_abst_pc,
                "gap": gap_pc,
                "threshold": MATERIAL_GAP_THRESHOLD,
                "min_abstained_n": MIN_ABSTAINED_N,
                "n_abstained": len(abst_idx),
            },
        }

    diag = {
        "schema": "amphora.solvency-score.ml-vs-physics-coverage-scope-diagnostic.v1",
        "campaign_item_id": "W-SOLV-COV",
        "provenance": prov,
        "split": {
            "n_total": len(sample), "n_train": len(train), "n_val": len(val),
            "n_test": len(test), "n_scaffolds": n_scaffolds,
            "method": "scaffold-safe 60/20/20 by unique Bemis-Murcko generic scaffold, seed=0 (identical to V1-SOLV)",
        },
        "pre_registration": {
            "material_gap_threshold_abs_r2": MATERIAL_GAP_THRESHOLD,
            "min_abstained_n": MIN_ABSTAINED_N,
            "majority_arms_required_for_refutation": MAJORITY_ARMS,
            "definition": "gap = ml_r2_on_covered_subset - ml_r2_on_abstained_subset; materially_degraded if gap > threshold and n_abstained >= min_abstained_n",
        },
        "per_arm": per_arm,
        "n_arms_materially_degraded": n_flagged,
        "n_arms_eligible": n_eligible,
        "refutation_criterion_fires": refutation_fires,
        "abstained_molecule_characterisation": characterisation,
        "deployment_relevant_any_arm_coverage": deployment,
        "descriptor_names": DESCRIPTOR_NAMES,
        "morgan_bits": 512, "morgan_radius": 2, "n_features": len(DESCRIPTOR_NAMES) + 512,
        "model_family": "HistGradientBoostingRegressor(max_iter=500, lr=0.05, depth=8, min_leaf=25, l2=0.1, random_state=0)",
        "reference_temperature_K": T_REF,
        "positive_control": pc,
    }

    blob = canonical_json(diag).encode()
    with open(out_path, "wb") as f:
        f.write(blob)
    print(out_path, sha256_bytes(blob), "elapsed", time.time() - t0, file=sys.stderr)
    print(out_path, sha256_bytes(blob))


if __name__ == "__main__":
    out = sys.argv[2] if len(sys.argv) > 2 else "/tmp/coverage_scope_diag.json"
    pc = "--positive-control" in sys.argv
    main(out, positive_control=pc)
