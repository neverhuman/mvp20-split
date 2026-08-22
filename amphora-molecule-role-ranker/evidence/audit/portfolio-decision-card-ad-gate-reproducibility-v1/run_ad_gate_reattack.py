#!/usr/bin/env python3
"""Independent reproduction attack on the flagship, never-before-attacked KPI
amphora-molecule-role-ranker/evidence/phase0/kpis/portfolio-integrated-candidate-decision-card-v2-5-canonical-epoxy-amines-kpi.v1.json

Claim under attack: metrics honest_out_of_domain_documentation (observed=1.0,
n_candidates_with_zero_ad_gates_passed=3, candidates gated out named as
"IPDA, TETA, DETA") and the applicability-domain Tanimoto-NN gate values
themselves, computed per the KPI's own stated methodology ("Applicability
domain via Tanimoto NN against each predictor's training corpus", citing
Rogers & Hahn 2010 ECFP/Morgan fingerprints).

Method: independently rebuild each of the 5 predictors' REAL training
corpora (property-specific non-null subsets of the SHA-pinned openpoly and
radonpy CSVs the KPI itself cites: openpoly_csv_sha256, radonpy_csv_sha256),
compute standard ECFP4 (RDKit Morgan radius=2, nBits=2048, the RDKit
default -- matching the KPI's own cited Rogers&Hahn 2010 reference) Tanimoto
nearest-neighbor similarity for each of the 5 candidate hardener SMILES
against each predictor's real corpus, and compare to the published AD gate
values.
"""
import gzip
import hashlib
import json
from pathlib import Path

from rdkit import Chem
from rdkit.Chem import AllChem, DataStructs
import rdkit.RDLogger as RDLogger
RDLogger.DisableLog("rdApp.*")

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
KPI_PATH = ROOT / "amphora-molecule-role-ranker/evidence/phase0/kpis/portfolio-integrated-candidate-decision-card-v2-5-canonical-epoxy-amines-kpi.v1.json"
OPENPOLY_JSONL = ROOT / "feedback/v2/normalized/openpoly_properties.jsonl.gz"
RADONPY_JSONL = ROOT / "feedback/v2/normalized/radonpy_pi1070.jsonl.gz"

RADIUS = 2
NBITS = 2048
AD_THRESHOLD = 0.30


def sha256(b):
    return hashlib.sha256(b).hexdigest()


def load_property_subsets(path, smi_field, prop_fields_map):
    """Return dict propname -> set(SMILES) with a non-null value for that
    property, mirroring how a real ML training pipeline would drop rows
    with missing target values (the predictor's REAL training corpus, not
    the full raw CSV)."""
    subsets = {name: set() for name in prop_fields_map}
    all_smiles = set()
    with gzip.open(path, "rt") as f:
        for line in f:
            r = json.loads(line)
            rf = r["raw_fields"]
            s = rf.get(smi_field)
            if not s:
                continue
            all_smiles.add(s)
            for name, fields in prop_fields_map.items():
                if any(rf.get(fl, "").strip() for fl in fields):
                    subsets[name].add(s)
    return all_smiles, subsets


def fp_of(smi):
    m = Chem.MolFromSmiles(smi)
    if m is None:
        return None
    return AllChem.GetMorganFingerprintAsBitVect(m, RADIUS, nBits=NBITS)


def corpus_fps(smi_set):
    out = []
    for s in sorted(smi_set):
        fp = fp_of(s)
        if fp is not None:
            out.append((s, fp))
    return out


def nn_tanimoto(cand_fp, corpus):
    best = 0.0
    best_smi = None
    for s, fp in corpus:
        sim = DataStructs.TanimotoSimilarity(cand_fp, fp)
        if sim > best:
            best = sim
            best_smi = s
    return best, best_smi


def main():
    kpi = json.loads(KPI_PATH.read_text())
    kpi_sha256 = sha256(KPI_PATH.read_bytes())
    fmodel = kpi["fitted_or_physical_model_artifact"]
    cards = {c["candidate_name"]: c for c in fmodel["candidate_cards"]}

    openpoly_all, openpoly_sub = load_property_subsets(
        OPENPOLY_JSONL, "PSMILES",
        {
            "tg": ["Tg (K)"],
            "contact_angle": ["Water Contact Angle (deg)"],
            "dielectric": ["Dielectric Constant Total", "Dielectric Constant Electronic", "Dielectric Constant Ionic"],
            "refractive_index": ["Refractive Index"],
        },
    )
    radonpy_all, radonpy_sub = load_property_subsets(
        RADONPY_JSONL, "smiles",
        {
            "density": ["density"],
            "dielectric": ["static_dielectric_const"],
            "refractive_index": ["refractive_index"],
        },
    )

    corpora = {
        "tg": corpus_fps(openpoly_sub["tg"]),
        "contact_angle": corpus_fps(openpoly_sub["contact_angle"]),
        "density": corpus_fps(radonpy_sub["density"]),
        "dielectric": corpus_fps(openpoly_sub["dielectric"] | radonpy_sub["dielectric"]),
        "refractive_index": corpus_fps(openpoly_sub["refractive_index"] | radonpy_sub["refractive_index"]),
    }
    corpus_sizes = {k: len(v) for k, v in corpora.items()}

    field_map = {
        "tg": "tg_nn_tanimoto",
        "contact_angle": "contact_angle_nn_tanimoto",
        "density": "density_nn_tanimoto",
        "dielectric": "dielectric_nn_tanimoto",
        "refractive_index": "refractive_index_nn_tanimoto",
    }

    per_candidate = {}
    n_exact_matches = 0
    n_total_metrics = 0
    n_gate_flips = 0
    gate_flip_detail = []

    for name, card in cards.items():
        smi = card["smiles"]
        cfp = fp_of(smi)
        published_ad = card["applicability_domain"]
        recomputed = {}
        for predictor, field in field_map.items():
            sim, nn_smi = nn_tanimoto(cfp, corpora[predictor])
            published_val = published_ad[field]
            match = abs(sim - published_val) < 1e-9
            n_total_metrics += 1
            if match:
                n_exact_matches += 1
            pub_pass = published_val >= AD_THRESHOLD
            rec_pass = sim >= AD_THRESHOLD
            if pub_pass != rec_pass:
                n_gate_flips += 1
                gate_flip_detail.append({
                    "candidate": name,
                    "predictor": predictor,
                    "published_value": published_val,
                    "published_gate_pass": pub_pass,
                    "recomputed_value": sim,
                    "recomputed_gate_pass": rec_pass,
                    "recomputed_nn_corpus_member": nn_smi,
                })
            recomputed[predictor] = {
                "published": published_val,
                "recomputed": sim,
                "exact_match": match,
                "published_gate_pass_at_0_30": pub_pass,
                "recomputed_gate_pass_at_0_30": rec_pass,
                "gate_outcome_flipped": pub_pass != rec_pass,
            }
        n_gates_published = published_ad["n_ad_gates_passed_at_threshold_0_30"]
        n_gates_recomputed = sum(1 for v in recomputed.values() if v["recomputed_gate_pass_at_0_30"])
        per_candidate[name] = {
            "smiles": smi,
            "metrics": recomputed,
            "n_ad_gates_passed_published": n_gates_published,
            "n_ad_gates_passed_recomputed": n_gates_recomputed,
            "n_ad_gates_passed_flipped": n_gates_published != n_gates_recomputed,
        }

    n_zero_gate_published = sum(1 for c in per_candidate.values() if c["n_ad_gates_passed_published"] == 0)
    n_zero_gate_recomputed = sum(1 for c in per_candidate.values() if c["n_ad_gates_passed_recomputed"] == 0)
    zero_gate_candidates_published = sorted(k for k, c in per_candidate.items() if c["n_ad_gates_passed_published"] == 0)
    zero_gate_candidates_recomputed = sorted(k for k, c in per_candidate.items() if c["n_ad_gates_passed_recomputed"] == 0)

    honest_oodd_metric = next(m for m in kpi["metrics"] if m["name"] == "honest_out_of_domain_documentation")
    n_zero_metric = next(m for m in kpi["metrics"] if m["name"] == "n_candidates_with_zero_ad_gates_passed") if any(m["name"] == "n_candidates_with_zero_ad_gates_passed" for m in kpi["metrics"]) else None

    published_top_ranked = fmodel["top_ranked_candidate_name"]
    top_ranked_still_passes_all_gates = per_candidate[published_top_ranked]["n_ad_gates_passed_recomputed"] == 5

    verdict = "CLAIM_REFUTED" if n_zero_gate_recomputed != n_zero_gate_published else "CLAIM_SURVIVED"

    out = {
        "schema": "amphora.molecule-role-ranker.decision-card-ad-gate-reproducibility-diagnostic.v1",
        "kpi_under_attack": "amphora-molecule-role-ranker/evidence/phase0/kpis/portfolio-integrated-candidate-decision-card-v2-5-canonical-epoxy-amines-kpi.v1.json",
        "kpi_sha256_at_attack_time": kpi_sha256,
        "method": {
            "fingerprint": f"RDKit Morgan/ECFP radius={RADIUS} nBits={NBITS} (RDKit default folded bit-vector; Rogers & Hahn 2010, matching the KPI's own cited theory reference)",
            "similarity": "Tanimoto (RDKit DataStructs.TanimotoSimilarity)",
            "corpus_construction": "per-predictor REAL training corpus = property-specific non-null-value subset of the SHA-pinned openpoly_properties / radonpy_pi1070 normalized data (feedback/v2/normalized/*.jsonl.gz), matching each predictor's actual training-receipt-declared source (openpoly-only for Tg/contact-angle, radonpy-only for density, openpoly UNION radonpy non-null-per-property for dielectric/refractive-index)",
            "candidate_representation": "raw candidate hardener monomer SMILES exactly as published in the KPI's own fitted_or_physical_model_artifact.candidate_cards[].smiles field",
        },
        "corpus_sizes": corpus_sizes,
        "corpus_source_files": {
            "openpoly_normalized_jsonl_gz": str(OPENPOLY_JSONL.relative_to(ROOT)),
            "openpoly_normalized_sha256": sha256(OPENPOLY_JSONL.read_bytes()),
            "radonpy_normalized_jsonl_gz": str(RADONPY_JSONL.relative_to(ROOT)),
            "radonpy_normalized_sha256": sha256(RADONPY_JSONL.read_bytes()),
            "openpoly_csv_sha256_cited_by_kpi": kpi["openpoly_csv_sha256"],
            "radonpy_csv_sha256_cited_by_kpi": kpi["radonpy_csv_sha256"],
        },
        "per_candidate": per_candidate,
        "summary": {
            "n_total_metrics_checked": n_total_metrics,
            "n_exact_matches": n_exact_matches,
            "n_mismatches": n_total_metrics - n_exact_matches,
            "n_gate_outcome_flips_at_0_30_threshold": n_gate_flips,
            "gate_flip_detail": gate_flip_detail,
            "n_candidates_with_zero_ad_gates_passed_published": n_zero_gate_published,
            "n_candidates_with_zero_ad_gates_passed_recomputed": n_zero_gate_recomputed,
            "zero_gate_candidates_published": zero_gate_candidates_published,
            "zero_gate_candidates_recomputed": zero_gate_candidates_recomputed,
            "published_honest_out_of_domain_documentation_metric": honest_oodd_metric,
            "top_ranked_candidate": published_top_ranked,
            "top_ranked_candidate_still_passes_all_5_gates_under_reattack": top_ranked_still_passes_all_gates,
        },
        "pre_registered_refute_criterion": (
            "Attack fires (REFUTED) iff independent re-derivation of the per-predictor "
            "Tanimoto-NN applicability-domain gate values, using the KPI's own cited "
            "corpora (openpoly_csv_sha256/radonpy_csv_sha256) and cited fingerprint "
            "reference (Rogers & Hahn 2010 ECFP, RDKit default Morgan radius=2/nBits=2048), "
            "changes the gate PASS/FAIL outcome (at the KPI's own published >=0.30 "
            "threshold) for at least one candidate, thereby changing "
            "n_candidates_with_zero_ad_gates_passed or the named "
            "honest_out_of_domain_documentation candidate list."
        ),
        "verdict": verdict,
    }
    return out


if __name__ == "__main__":
    result = main()
    print(json.dumps(result, indent=2, sort_keys=True))
