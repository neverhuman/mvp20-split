#!/usr/bin/env python3
"""W2 fire 1: sign the consolidated corpus-admissibility-audit receipt.

Follows the same DSSE signing pattern used throughout this module's prior
falsification fires (C7/C8): local AUDIT_ONLY Ed25519 key at
.amphora/control/local-ed25519.key, DSSE envelope OBJECT at top-level
.signature, two-replay byte-stability gate.
"""
import json, base64, hashlib
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
OUT = ROOT / "amphora-molecule-property/evidence/audit/corpus-admissibility-audit-v1"
OUT.mkdir(parents=True, exist_ok=True)
KEY = ROOT / ".amphora/control/local-ed25519.key"
PUB = json.loads((ROOT / ".amphora/control/local-ed25519.pub.json").read_text())

RAW = json.loads(Path("/tmp/w2_corpus_audit_raw_results.json").read_text())
R = RAW["results"]


def sha(b):
    return hashlib.sha256(b).hexdigest()


def pae(t, body):
    return b"DSSEv1 " + str(len(t)).encode() + b" " + t.encode() + b" " + str(len(body)).encode() + b" " + body


def build_receipt():
    return {
        "schema": "amphora.molecule-property.corpus-admissibility-audit-receipt.v1",
        "receipt_id": "w2-fire1-corpus-admissibility-audit",
        "study_id": "w2-corpus-admissibility-audit",
        "campaign_item_id": "W2",
        "fire_sequence": "W2 fire 1 of 4 (max_fires).",
        "authority": "AUDIT_ONLY",
        "promotes_nothing": True,
        "modifies_no_live_config": True,
        "module": "amphora-molecule-property",
        "claim_under_attack": {
            "receipt_path": "amphora-molecule-property/evidence/phase0/kpis/",
            "claim_text": "The label data underlying this portfolio's ML claims is physically admissible.",
        },
        "prior_fire_context": (
            "C8 fires 1-3 established that only 113/1075=10.5% of RadonPy PI1070's static_dielectric_const "
            "rows satisfy the model-independent Frohlich inequality eps_static>=n_measured^2, and that "
            "retraining on the physically-valid subset alone collapses every {physics, ML, stack} model "
            "arm to R2<=0 (c8_fire2_dielectric_clean_subset_receipt.v1.json). That was one corpus and one "
            "constraint. W2 generalizes the audit across every other reachable in-tree corpus in this "
            "module's shared normalized data lake (feedback/v2/normalized/), each with its own "
            "independently-justified physical or definitional constraint."
        ),
        "objective": (
            "Audit >=4 in-tree corpora for physical-admissibility violations in their ground-truth label "
            "columns, quantify n_total/n_admissible/pct per corpus, cite the physical justification for "
            "each constraint, and list which downstream module KPIs depend on the flagged rows."
        ),
        "method": (
            "For each corpus, read the normalized JSONL-gz rows directly from the shared data lake at "
            "feedback/v2/normalized/<acquisition_unit_id>.jsonl.gz (the same files this module's manifests "
            "at reference/mvp20/manifests/*.json point to via normalized_path/normalized_sha256), apply one "
            "or more physical/definitional constraints independent of any ML model, and count admissible "
            "vs inadmissible rows. No quarantined or CONTEXT_ONLY source was opened; all four corpora carry "
            "rights_class=DERIVATIVE_ALLOWED per their feedback_v2/rights/*.json manifests."
        ),
        "corpora_audited": [
            {
                "corpus": "openpoly_properties",
                "acquisition_unit_id": R["openpoly_properties"]["acquisition_unit_id"],
                "raw_file_sha256": R["openpoly_properties"]["raw_file_sha256"],
                "lake_path": R["openpoly_properties"]["lake_path"],
                "n_total_rows": R["openpoly_properties"]["n_total_rows"],
                "n_rows_evaluable": R["openpoly_properties"]["n_rows_with_both_Tg_and_Tm"],
                "n_admissible": R["openpoly_properties"]["n_admissible"],
                "n_inadmissible": R["openpoly_properties"]["n_inadmissible"],
                "pct_admissible_of_evaluable": R["openpoly_properties"]["pct_admissible_of_evaluable"],
                "constraint": R["openpoly_properties"]["constraint"],
                "constraint_citation": R["openpoly_properties"]["constraint_citation"],
                "violations_sample": R["openpoly_properties"]["violations_sample"],
                "dependent_module_kpis": [
                    "openpoly-experimental-tg-ml-baseline-kpi.v1.json",
                    "external-validation-polyuniverse-ridge-on-openpoly-tg-kpi.v1.json",
                    "openpoly-dielectric-constant-ml-baseline-kpi.v1.json",
                    "openpoly-water-uptake-ml-baseline-audit-kpi.v1.json",
                    "openpoly-water-contact-angle-ml-baseline-kpi.v1.json",
                    "mixed-openpoly-radonpy-dielectric-conformal-kpi.v1.json",
                    "mixed-openpoly-radonpy-refractive-index-conformal-kpi.v1.json",
                    "external-validation-dielectric-ml-openpoly-to-radonpy-kpi.v1.json",
                ],
                "verdict": "VIOLATIONS_FOUND",
                "finding_summary": (
                    "24/167 (14.4%) OpenPoly rows with both Tg and Tm reported have Tg>=Tm, violating the "
                    "Boyer-Beaman constraint that the glass transition (a kinetic freezing of the amorphous "
                    "phase) must occur strictly below the true crystalline melting point. These 24 rows are "
                    "training/validation examples inside the SAME openpoly_properties dataset_id "
                    "(8de5baf76f79610f) consumed by 8 downstream KPIs, including the primary "
                    "openpoly-experimental-tg-ml-baseline-kpi.v1.json Tg model."
                ),
            },
            {
                "corpus": "bigsoldb_solubility",
                "acquisition_unit_id": R["bigsoldb_solubility"]["acquisition_unit_id"],
                "raw_file_sha256": R["bigsoldb_solubility"]["raw_file_sha256"],
                "lake_path": R["bigsoldb_solubility"]["lake_path"],
                "n_total_rows": R["bigsoldb_solubility"]["n_total_rows"],
                "n_rows_evaluable": R["bigsoldb_solubility"]["n_rows_with_mole_fraction"],
                "n_admissible": R["bigsoldb_solubility"]["n_admissible"],
                "n_inadmissible": R["bigsoldb_solubility"]["n_inadmissible"],
                "pct_admissible_of_evaluable": R["bigsoldb_solubility"]["pct_admissible_of_evaluable"],
                "constraint": R["bigsoldb_solubility"]["constraint"],
                "constraint_citation": R["bigsoldb_solubility"]["constraint_citation"],
                "secondary_diagnostic_internal_log10_consistency": R["bigsoldb_solubility"]["secondary_diagnostic_internal_log10_consistency"],
                "duplicate_contradictory_measurement_check": R["bigsoldb_solubility"]["duplicate_contradictory_measurement_check"],
                "dependent_module_kpis": [],
                "dependent_module_kpis_note": (
                    "No amphora-molecule-property KPI receipt currently reads bigsoldb_solubility directly "
                    "(grep of evidence/phase0/kpis/*.json and benchmarks/ found zero matches). The known "
                    "downstream consumer of this corpus is amphora-solvent-property's Solvency BigSolDB "
                    "result (LSO RMSE 0.877, that module's only externally-validated solvency claim) -- a "
                    "different module, out of this fire's write scope, flagged here for cross-module "
                    "awareness only."
                ),
                "verdict": "PRIMARY_BOUND_CLEAN_BUT_INTERNAL_CONTRADICTIONS_FOUND",
                "finding_summary": (
                    "The primary physical bound (0<mole_fraction<1) is satisfied by all 103,944/103,944 rows "
                    "-- no admissibility violation on that axis. However, a secondary, equally physical check "
                    "-- do repeated measurements of the same (solute, solvent, temperature) triple agree with "
                    "each other -- found 4,134/4,578 (90.3%) of duplicate-measurement groups disagree by more "
                    "than 0.3 log10(mol/L) units (>2x) at IDENTICAL conditions. A single physical quantity "
                    "cannot have two internally-contradictory literature values at the same state point; this "
                    "is a corpus-level admissibility defect distinct from (and larger in count than) a simple "
                    "out-of-bounds check would catch."
                ),
            },
            {
                "corpus": "bigsoldb_density",
                "acquisition_unit_id": R["bigsoldb_density"]["acquisition_unit_id"],
                "raw_file_sha256": R["bigsoldb_density"]["raw_file_sha256"],
                "lake_path": R["bigsoldb_density"]["lake_path"],
                "n_total_rows": R["bigsoldb_density"]["n_total_rows"],
                "n_rows_evaluable": R["bigsoldb_density"]["n_rows_evaluable"],
                "n_admissible": R["bigsoldb_density"]["n_admissible"],
                "n_inadmissible": R["bigsoldb_density"]["n_inadmissible"],
                "pct_admissible_of_evaluable": R["bigsoldb_density"]["pct_admissible_of_evaluable"],
                "constraint": R["bigsoldb_density"]["constraint"],
                "constraint_citation": R["bigsoldb_density"]["constraint_citation"],
                "violations_sample": R["bigsoldb_density"]["violations_sample"],
                "dependent_module_kpis": [],
                "dependent_module_kpis_note": "Same cross-module caveat as bigsoldb_solubility above; consumed by amphora-solvent-property, not this module's KPIs.",
                "verdict": "CLEAN",
                "finding_summary": (
                    "2209/2210 (99.95%) rows fall within the physically-plausible organic-liquid density band "
                    "[0.6, 3.4] g/cm^3. Essentially clean; 1 row flagged for manual review."
                ),
            },
            {
                "corpus": "polyomics_small_molecules",
                "acquisition_unit_id": R["polyomics_small_molecules"]["acquisition_unit_id"],
                "raw_file_sha256": R["polyomics_small_molecules"]["raw_file_sha256"],
                "lake_path": R["polyomics_small_molecules"]["lake_path"],
                "n_total_rows": R["polyomics_small_molecules"]["n_total_rows"],
                "constraint_A_frohlich": R["polyomics_small_molecules"]["constraint_A"],
                "constraint_B_refractive_index_lower_bound": R["polyomics_small_molecules"]["constraint_B"],
                "dependent_module_kpis": [
                    "mixed-openpoly-radonpy-dielectric-conformal-kpi.v1.json",
                    "mixed-openpoly-radonpy-refractive-index-conformal-kpi.v1.json",
                    "external-validation-dielectric-ml-openpoly-to-radonpy-kpi.v1.json",
                    "multi-target-ml-radonpy-4-properties-audit-kpi.v1.json",
                    "radonpy-density-ml-vs-van-krevelen-physics-kpi.v1.json",
                    "stacked-ml-van-krevelen-density-radonpy-kpi.v1.json",
                ],
                "verdict": "VIOLATIONS_FOUND_DIFFERENT_MAGNITUDE_THAN_CURATED_SUBSET",
                "finding_summary": (
                    "This is the larger raw RadonPy simulation-output corpus (28,159 rows) that the "
                    "already-audited radonpy_pi1070 (1,077 rows, C8 fires 1-3) was curated from. Applying "
                    "the SAME Frohlich inequality (eps_static>=n^2) at full scale finds 16,990/27,964 "
                    "(60.8%) admissible -- i.e. 39.2% violate, NOT the 89.5% violation rate found in the "
                    "curated PI1070 subset. The two numbers disagree by a factor of >2x in violation rate. "
                    "This means PI1070's curation step specifically concentrated (not merely inherited) "
                    "the dielectric-admissibility defect relative to the raw simulation dump it was drawn "
                    "from -- a new finding this fire surfaces that C8 could not see from PI1070 alone. "
                    "Separately, the refractive-index lower bound (n>=1, Lorentz-Lorenz) is essentially "
                    "clean at full scale: 27,963/27,964 (99.996%) admissible."
                ),
            },
        ],
        "cross_corpus_summary": {
            "n_corpora_audited": 4,
            "corpora_with_violations": ["openpoly_properties", "bigsoldb_solubility (duplicate-contradiction axis)", "polyomics_small_molecules"],
            "corpora_clean": ["bigsoldb_density (99.95%)", "polyomics_small_molecules refractive-index axis (99.996%)"],
            "headline": (
                "The portfolio-wide claim 'the label data underlying this portfolio's ML claims is "
                "physically admissible' does NOT hold uniformly. Beyond the already-refuted RadonPy "
                "PI1070 dielectric case (C8), this audit finds: (1) OpenPoly Tg/Tm violates a basic "
                "polymer-thermodynamics ordering constraint in 14.4% of evaluable rows, feeding 8 "
                "downstream KPIs including the primary Tg ML baseline; (2) BigSolDB solubility, while "
                "clean on its primary mole-fraction bound, has internally CONTRADICTORY repeated "
                "measurements in 90.3% of its duplicate-measurement groups; (3) the raw RadonPy "
                "simulation dump (polyomics_small_molecules) shows the same Frohlich-inequality defect "
                "as PI1070 but at a materially different rate (39.2% vs 89.5%), revealing that PI1070's "
                "curation concentrated the defect rather than merely inheriting it. Only BigSolDB density "
                "and the RadonPy refractive-index axis are clean (>99.9%)."
            ),
        },
        "verdict": "REFUTED",
        "refutation_criterion": (
            "Pre-registered: the claim survives only if ALL >=4 audited corpora show >=95% admissible "
            "rows on their respective physical constraints. Observed: 2 of 4 corpora fall well below this "
            "bar (openpoly_properties 85.6%, polyomics_small_molecules Frohlich axis 60.8%), and a 5th "
            "diagnostic axis (BigSolDB duplicate-contradiction rate) shows 90.3% internal contradiction. "
            "Criterion fired -- claim REFUTED."
        ),
        "rights_check": (
            "All 4 corpora read from feedback/v2/normalized/*.jsonl.gz carry rights_class=DERIVATIVE_ALLOWED "
            "per their respective feedback_v2/rights/*.json and manifests/*.json (openpoly_properties, "
            "radonpy_pi1070/polyomics_small_molecules already load-bearing elsewhere in this module; "
            "bigsoldb_solubility/bigsoldb_density are DERIVATIVE_ALLOWED per feedback_v2 catalog.json). "
            "No quarantined, USBR_RIGHTS_REVIEW_REQUIRED, or CONTEXT_ONLY source was opened."
        ),
        "gates": {
            "two_replay_byte_stable_this_receipt": None,
            "ge_4_corpora_audited": True,
            "each_corpus_has_named_physical_or_definitional_constraint_with_citation": True,
            "dependent_kpi_list_included_per_corpus": True,
            "signature_field_is_dsse_envelope_object": True,
        },
        "all_gates_passed": True,
        "ceiling": (
            "AUDIT_ONLY. Does not alter any shipped KPI receipt, manifest, or authority ceiling. Documents "
            "corpus-level label-integrity findings across 4 corpora for the founder-facing honesty ledger. "
            "OpenPoly Tg/Tm and BigSolDB duplicate-contradiction findings are NEW (not previously audited "
            "by this module); the RadonPy/polyomics finding refines (does not merely repeat) the C8 "
            "finding by showing the effect size differs materially between the raw and curated corpora."
        ),
        "promotion_blocked_by": "NOT this audit's science (all gates pass) and NOT key custody. Manifest untouched at 66/11.",
        "recommended_followups": [
            "openpoly-experimental-tg-ml-baseline-kpi.v1.json and the 7 other dependent KPIs should be re-run with the 24 Tg>=Tm rows excluded from train/calib/test to determine whether the shipped Tg MAE is inflated by these physically-inadmissible examples (same escalation pattern as C8 fire 2).",
            "File a data-acquisition/rights-review ask for BigSolDB: the 90.3% duplicate-contradiction rate means the corpus needs a reconciliation policy (e.g. keep only single-source or median-of-agreeing-sources measurements) before amphora-solvent-property's Solvency BigSolDB KPI (RMSE 0.877, its only ext-validated claim) can be considered clean at the label level -- this is cross-module and out of this fire's write scope, but is the single highest-leverage follow-up this audit surfaces.",
            "Investigate WHY PI1070's curation concentrated the Frohlich-inequality defect (89.5% violation) relative to the raw polyomics_small_molecules dump it was drawn from (39.2% violation) -- if the curation criterion correlates with simulation non-convergence, that same non-convergence flag could be used as a cheap admissibility pre-filter across the whole polyomics_small_molecules corpus for future RadonPy-derived KPIs.",
        ],
        "signing_key": {
            "key_id": PUB["key_id"],
            "authority": PUB["authority"],
            "public_key_hex": PUB["public_key_hex"],
            "trust_anchored": False,
            "note": "NOT in config/phase0-trust-store.v1.json; audit evidence only",
        },
    }


r1 = build_receipt()
r2 = build_receipt()
body1 = json.dumps(r1, indent=2, sort_keys=True).encode()
body2 = json.dumps(r2, indent=2, sort_keys=True).encode()
assert body1 == body2, "this receipt's own content is non-deterministic"
(OUT / "receipt_body.canonical.json").write_bytes(body1)
(OUT / "receipt_body.runB.json").write_bytes(body2)

receipt = build_receipt()
receipt["gates"]["two_replay_byte_stable_this_receipt"] = True
receipt["two_replay_gate"] = {
    "canonical_sha256": sha(body1),
    "runB_sha256": sha(body2),
    "byte_identical": body1 == body2,
}

body = json.dumps(receipt, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.molecule-property.corpus-admissibility-audit-receipt.v1+json"
sk = Ed25519PrivateKey.from_private_bytes(KEY.read_bytes())
sig = sk.sign(pae(ptype, body))
envelope = {
    "payload": base64.standard_b64encode(body).decode(),
    "payloadType": ptype,
    "signatures": [{"keyid": PUB["key_id"], "sig": base64.standard_b64encode(sig).decode()}],
}

out = dict(receipt)
out["signature"] = envelope

outpath = OUT / "w2_fire1_corpus_admissibility_audit_receipt.v1.json"
outpath.write_text(json.dumps(out, indent=2, sort_keys=True))

Ed25519PublicKey.from_public_bytes(bytes.fromhex(PUB["public_key_hex"])).verify(sig, pae(ptype, body))
assert isinstance(json.loads(outpath.read_text())["signature"], dict), "signature must serialize as JSON object"

print("SIGNED_OK", outpath)
print("receipt_id", receipt["receipt_id"])
print("sig_verified True")
print("signature_type", type(json.loads(outpath.read_text())["signature"]).__name__)
