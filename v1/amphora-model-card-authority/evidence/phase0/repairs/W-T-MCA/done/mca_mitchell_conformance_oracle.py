#!/usr/bin/env python3
"""AUDIT_ONLY, non-mutating theory oracle for campaign item W-T-MCA.

Measures the amphora-model-card-authority module's `model_card` artifact
(the CandidateEnvelope-schema `metrics.model_card` object this module owns
completeness for, and the ScoreEnvelope-schema field that names it) against
the published Mitchell et al. 2019 "Model Cards for Model Reporting" schema
(FAT* '19, DOI 10.1145/3287560.3287596) for the first time. Prior to this
receipt the module's own docs never cite this baseline; the claim under
attack ("card completeness is measured against a published model-card
standard") was self-referential.

Grounding is REAL, not hand-typed verdicts:
  - SCHEMA_* is parsed live from amphora-candidate-contract/schemas/score-envelope.schema.json
  - OBSERVED_* is parsed live from the already-captured, previously-signed
    live-runtime ground truth at
    amphora-model-card-authority/evidence/audit/live-runtime-envelope-parity-v1/runtime_ground_truth.v1.json
    (native Rust amphora-engine output, captured under a prior AUDIT_ONLY
    receipt; re-used here, not re-executed, so this oracle stays read-only).
  - MITCHELL_SECTIONS encodes the published schema's 9 top-level sections and,
    for each, the module-specific field name(s) that WOULD have to appear
    (non-null, actually emitted) on model_card for this module's artifact to
    satisfy that section. That mapping is the theory-interpretation step and
    is the only hand-authored part of this oracle; every verdict below it is
    computed, not asserted, from the two parsed inputs above, so a future
    fire that adds e.g. "kpi_name" emission to the runtime will flip R4's
    verdict automatically on re-run.

Two-replay discipline: no wall-clock, no randomness, no filesystem writes
outside the diagnostic outputs; sort_keys=True everywhere for byte stability.
"""
import hashlib
import json
from pathlib import Path

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MODULE = ROOT / "amphora-model-card-authority"
SCHEMA_PATH = ROOT / "amphora-candidate-contract/schemas/score-envelope.schema.json"
GROUND_TRUTH_PATH = MODULE / "evidence/audit/live-runtime-envelope-parity-v1/runtime_ground_truth.v1.json"
MISSION_PATH = MODULE / "docs/mission.md"
ENGINE_PATH = ROOT / "amphora-engine/src/lib.rs"


def sha(b):
    return hashlib.sha256(b).hexdigest()


schema_bytes = SCHEMA_PATH.read_bytes()
schema = json.loads(schema_bytes)
gt_bytes = GROUND_TRUTH_PATH.read_bytes()
gt = json.loads(gt_bytes)
mission_bytes = MISSION_PATH.read_bytes()
mission_text = mission_bytes.decode("utf-8", errors="replace")
engine_bytes = ENGINE_PATH.read_bytes()

# Walk the schema defensively instead of assuming one fixed path so the
# oracle does not silently go blind if the schema is restructured.
def find_model_card_node(obj):
    if isinstance(obj, dict):
        props = obj.get("properties")
        if isinstance(props, dict) and "model_card" in props and isinstance(props["model_card"], dict) \
           and "properties" in props["model_card"]:
            return props["model_card"]
        for v in obj.values():
            found = find_model_card_node(v)
            if found is not None:
                return found
    elif isinstance(obj, list):
        for v in obj:
            found = find_model_card_node(v)
            if found is not None:
                return found
    return None


model_card_node = find_model_card_node(schema)
assert model_card_node is not None, "model_card schema node not found"

SCHEMA_FIELDS = sorted(model_card_node.get("properties", {}).keys())
SCHEMA_REQUIRED = sorted(model_card_node.get("required", []))

# --- observed live runtime field sets ---------------------------------
observed_fieldsets = {}
for case_id, case in gt.get("cases", {}).items():
    env = case.get("envelope")
    if env is None:
        continue
    mc = env.get("metrics", {}).get("model_card")
    if mc is None:
        continue
    observed_fieldsets[case_id] = tuple(sorted(mc.keys()))

distinct_observed_shapes = sorted(set(observed_fieldsets.values()))
OBSERVED_FIELDS = sorted(set().union(*[set(fs) for fs in distinct_observed_shapes])) if distinct_observed_shapes else []
observed_uniform = len(distinct_observed_shapes) == 1

TRAINING_DATA_RATIONALE_STATED = ("training data" in mission_text.lower())

# --- Mitchell et al. 2019 sections, mapped to this module's card fields --
MITCHELL_SECTIONS = [
    {
        "id": "R1-model-details",
        "section": "Model Details",
        "normative_summary": "Basic model provenance: developing person/org, model date, model version, model type, training algorithms/parameters, reference paper/resource, citation details, license, feedback contact.",
        "required_signal_fields": ["model_id", "developer", "model_date", "model_version", "citation", "license", "contact"],
        "applicability": "applies",
    },
    {
        "id": "R2-intended-use",
        "section": "Intended Use",
        "normative_summary": "Primary intended uses, primary intended users, out-of-scope use cases.",
        "required_signal_fields": ["primary_intended_uses", "primary_intended_users", "out_of_scope_use_cases"],
        "adjacent_fields_present_but_not_equivalent": ["model_authority", "solver_use", "product_claim_ready", "model_readiness_status"],
        "applicability": "applies",
    },
    {
        "id": "R3-factors",
        "section": "Factors",
        "normative_summary": "Relevant factors (groups, instrumentation, environment) and evaluation factors used to disaggregate results.",
        "required_signal_fields": ["relevant_factors", "evaluation_factors", "instrumentation", "environment_factors"],
        "applicability": "applies",
    },
    {
        "id": "R4-metrics",
        "section": "Metrics",
        "normative_summary": "Model performance measures, decision thresholds, and variation/uncertainty approaches.",
        "required_signal_fields": ["kpi_name", "unit", "direction", "validation_bar"],
        "applicability": "applies",
    },
    {
        "id": "R5-evaluation-data",
        "section": "Evaluation Data",
        "normative_summary": "Datasets used for evaluation, their motivation, and preprocessing.",
        "required_signal_fields": ["dataset_ids", "dataset_checksums"],
        "applicability": "applies",
    },
    {
        "id": "R6-training-data",
        "section": "Training Data",
        "normative_summary": "Training data distribution/provenance where available, or an explicit statement of why it is omitted.",
        "required_signal_fields": ["training_dataset_ids", "training_provenance_statement"],
        "applicability": "applies_or_requires_stated_rationale",
    },
    {
        "id": "R7-quantitative-analyses",
        "section": "Quantitative Analyses",
        "normative_summary": "Unitary results per factor and intersectional results across factor combinations.",
        "required_signal_fields": ["unitary_result_value", "subgroup_results", "intersectional_results"],
        "applicability": "applies",
    },
    {
        "id": "R8-ethical-considerations",
        "section": "Ethical Considerations",
        "normative_summary": "Sensitive data use, intended-use risks, mitigations, and risks/harms identified during model development.",
        "required_signal_fields": ["ethical_considerations", "known_risks", "misuse_cases"],
        "applicability": "applies",
    },
    {
        "id": "R9-caveats-and-recommendations",
        "section": "Caveats and Recommendations",
        "normative_summary": "Additional testing recommended, ideal evaluation datasets not used, and other caveats a reader of the card needs.",
        "required_signal_fields": ["caveats", "recommendations", "known_limitations"],
        "applicability": "applies",
    },
]


def score_section(sec):
    required = sec["required_signal_fields"]
    present_in_observed = [f for f in required if f in OBSERVED_FIELDS]
    present_in_schema_required = [f for f in required if f in SCHEMA_REQUIRED]
    present_in_schema_any = [f for f in required if f in SCHEMA_FIELDS]

    if sec["applicability"] == "applies_or_requires_stated_rationale" and not present_in_observed:
        if TRAINING_DATA_RATIONALE_STATED:
            verdict = "not_applicable"
        else:
            verdict = "divergent"
    elif len(present_in_observed) == len(required) and len(required) > 0:
        verdict = "conformant"
    else:
        verdict = "divergent"

    return {
        "id": sec["id"],
        "section": sec["section"],
        "normative_summary": sec["normative_summary"],
        "required_signal_fields": required,
        "present_in_observed_runtime": present_in_observed,
        "present_in_schema_required_list": present_in_schema_required,
        "present_in_schema_any_property": present_in_schema_any,
        "n_required": len(required),
        "n_present_observed": len(present_in_observed),
        "verdict": verdict,
    }


requirements_table = [score_section(sec) for sec in MITCHELL_SECTIONS]

n_conformant = sum(1 for r in requirements_table if r["verdict"] == "conformant")
n_divergent = sum(1 for r in requirements_table if r["verdict"] == "divergent")
n_not_applicable = sum(1 for r in requirements_table if r["verdict"] == "not_applicable")

diagnostic = {
    "study_id": "amphora-model-card-authority.mitchell-2019-conformance.v1",
    "run_type": "AUDIT_ONLY_THEORY_MEASUREMENT",
    "purpose": "Measure this module's model_card artifact against a NAMED PUBLISHED model-card baseline for the first time (campaign item W-T-MCA), replacing the prior self-referential (fixture-only) completeness claim.",
    "hypothesis": "H0: the model_card artifact this module owns completeness for satisfies all 9 Mitchell et al. (2019) model-card sections. Refuted if any section scores divergent with zero required-signal fields observed in the live runtime.",
    "non_circularity": "SCHEMA_FIELDS/SCHEMA_REQUIRED are parsed live from amphora-candidate-contract/schemas/score-envelope.schema.json (a dependency this module consumes, not a fixture this module authored for this test). OBSERVED_FIELDS are parsed live from a previously-captured, previously-signed native-Rust runtime ground truth (live-runtime-envelope-parity-v1), not re-derived or re-typed by this oracle.",
    "theory_reference": {
        "baseline_name": "Model Cards for Model Reporting",
        "authors": "Margaret Mitchell, Simone Wu, Andrew Zaldivar, Parker Barnes, Lucy Vasserman, Ben Hutchinson, Elena Spitzer, Inioluwa Deborah Raji, Timnit Gebru",
        "venue": "Proceedings of the Conference on Fairness, Accountability, and Transparency (FAT* '19)",
        "year": 2019,
        "doi": "10.1145/3287560.3287596",
        "pages": "220-229",
        "open_access": True,
        "secondary_baseline_name": "Datasheets for Datasets",
        "secondary_authors": "Timnit Gebru, Jamie Morgenstern, Briana Vecchione, Jennifer Wortman Vaughan, Hanna Wallach, Hal Daume III, Kate Crawford",
        "secondary_venue": "Communications of the ACM, Vol. 64, No. 12",
        "secondary_year": 2021,
        "secondary_doi": "10.1145/3458723",
        "secondary_note": "Cited per this module's docs/mission.md convention that dataset-provenance fields (dataset_ids, dataset_checksums) are the evaluation/training-data analogue this secondary baseline's schema formalizes (motivation, composition, collection, preprocessing, uses, distribution, maintenance); not reproduced verbatim.",
    },
    "runtime_source_anchors": {
        "score_envelope_schema_path": "amphora-candidate-contract/schemas/score-envelope.schema.json",
        "score_envelope_schema_sha256": sha(schema_bytes),
        "runtime_ground_truth_path": "amphora-model-card-authority/evidence/audit/live-runtime-envelope-parity-v1/runtime_ground_truth.v1.json",
        "runtime_ground_truth_sha256": sha(gt_bytes),
        "engine_emission_path": "amphora-engine/src/lib.rs",
        "engine_emission_sha256": sha(engine_bytes),
        "mission_doc_path": "amphora-model-card-authority/docs/mission.md",
        "mission_doc_sha256": sha(mission_bytes),
    },
    "schema_analysis": {
        "model_card_schema_fields": SCHEMA_FIELDS,
        "model_card_schema_required_fields": SCHEMA_REQUIRED,
    },
    "runtime_analysis": {
        "cases_with_envelope": sorted(observed_fieldsets.keys()),
        "n_cases_with_envelope": len(observed_fieldsets),
        "observed_model_card_field_shapes": [list(fs) for fs in distinct_observed_shapes],
        "observed_shape_is_uniform_across_all_cases": observed_uniform,
        "observed_fields_union": OBSERVED_FIELDS,
        "schema_required_fields_never_emitted_by_runtime": sorted(set(SCHEMA_REQUIRED) - set(OBSERVED_FIELDS)),
    },
    "training_data_rationale_stated_in_mission_md": TRAINING_DATA_RATIONALE_STATED,
    "requirements_table": requirements_table,
    "requirements_summary": {
        "n_requirements": len(requirements_table),
        "n_conformant": n_conformant,
        "n_divergent": n_divergent,
        "n_not_applicable": n_not_applicable,
    },
    "gates": {
        "at_least_9_requirements_enumerated": len(requirements_table) >= 9,
        "every_requirement_has_verdict_and_evidence": all(
            r["verdict"] in ("conformant", "divergent", "not_applicable") for r in requirements_table
        ),
        "claim_survives": n_conformant == len(requirements_table),
        "all_gates_pass_bookkeeping_only": True,
    },
    "closes": "W-T-MCA: whether the model_card artifact's completeness is measured against a named published model-card baseline, and what that measurement finds.",
    "does_not_close": [
        "Does not close the amphora-model-card-authority authority-lattice-completeness claim (separate receipt, evidence/audit/authority-lattice-completeness-v1, Denning 1976 baseline).",
        "Does not re-derive or re-execute the native Rust runtime; reuses a previously-captured, previously-signed ground truth capture.",
        "Does not promote authority, flip scientific_readiness, or modify the portfolio manifest.",
    ],
    "counts": {
        "n_schema_fields": len(SCHEMA_FIELDS),
        "n_schema_required_fields": len(SCHEMA_REQUIRED),
        "n_observed_fields": len(OBSERVED_FIELDS),
    },
}

canon = json.dumps(diagnostic, indent=2, sort_keys=True).encode()
out_dir = MODULE / "evidence/phase0/repairs/W-T-MCA/done"
out_dir.mkdir(parents=True, exist_ok=True)
(out_dir / "diagnostic.canonical.json").write_bytes(canon)
print("wrote diagnostic.canonical.json", sha(canon))
print("n_conformant", n_conformant, "n_divergent", n_divergent, "n_not_applicable", n_not_applicable)
