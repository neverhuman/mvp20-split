#!/usr/bin/env python3
"""amphora-candidate-contract :: score-envelope-optimizer-admission-v1

THIRD ARTIFACT (prediction declarer).  Builds the typed score-envelope corpus and
declares, PER CASE, the LAYER and the two ORACLE PREDICTIONS *from module semantics
alone* -- before either oracle is executed.  Neither oracle is consulted here.

Oracle A (declarative) = amphora-candidate-contract/schemas/score-envelope.schema.json
Oracle B (runtime)     = compiled Rust amphora-core optimizer admission path
                         (rank_candidates -> optimizer_envelopes -> authorize_optimizer_request)

Coating scope: every positive/base case is a real two-part marine anti-corrosion
epoxy-amine (DGEBA + IPDA) score envelope shape.

AUDIT_ONLY.  Writes only into the corpus directory given as argv[1].
"""
import hashlib
import json
import shutil
import sys
from copy import deepcopy
from pathlib import Path

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MODULE = ROOT / "amphora-candidate-contract"
FIXTURES = MODULE / "fixtures"

# amphora_core::phase0::REQUIRED_ZERO_AUTHORITY_CLAIM_LOCKS (10)
LOCKS = [
    "no_ranking_authority",
    "no_optimizer_authority",
    "no_release_authority",
    "no_qualification_authority",
    "no_patentability_authority",
    "fto_not_performed",
    "no_procurement_authority",
    "no_regulatory_authority",
    "no_safety_authority",
    "no_product_performance_authority",
]

# score-envelope.schema.json top-level "required" (18)
SCHEMA_REQUIRED = [
    "module_id", "module_version", "candidate_id", "status", "authority_tier",
    "score_0_1", "objective_values", "metrics", "gates", "uncertainty",
    "claim_locks", "missing_inputs", "explanations", "source_refs",
    "usable_by_optimizer", "evidence_scope", "score_semantics", "schema_version",
]

# Of the 18, the subset the Rust admission path ALSO dereferences.  Declared from
# reading amphora-core/src/lib.rs::optimizer_envelopes + authorize_optimizer_request.
RUNTIME_ALSO_REQUIRED = [
    "module_id", "status", "authority_tier", "objective_values", "gates",
    "claim_locks", "usable_by_optimizer", "metrics",
]
SCHEMA_ONLY_REQUIRED = [k for k in SCHEMA_REQUIRED if k not in RUNTIME_ALSO_REQUIRED]

# metrics.allOf[0] then.required -- the conditional provenance gate (15 clauses).
# "model_receipt_schema" is the TRIGGER key; the other 14 are the OBLIGATIONS.
GATE_TRIGGER = "model_receipt_schema"
GATE_OBLIGATIONS = [
    "model_id", "model_receipt_hash", "formula_hash", "input_hash",
    "ingredient_catalog_hash", "ingredient_catalog_source_hash",
    "normalization_version", "prediction_status", "primary_prediction",
    "solver_use", "model_readiness_status", "authority_receipt",
    "score_content_hash", "claim_boundary",
]
H64A = "a" * 64
H64B = "b" * 64


def model_card():
    return {
        "kpi_name": "epoxy_amine_stoichiometric_index",
        "unit": "amine_H_per_epoxide",
        "direction": "context",
        "model_authority": "REAL_ARITHMETIC",
        "dataset_ids": ["fixtures/canonical_formulation_candidate.json"],
        "dataset_checksums": {"fixtures/canonical_formulation_candidate.json": H64A},
        "validation_bar": "deterministic dimensioned arithmetic; no wet-lab claim",
        "current_status": "SCORED",
        "current_pass": True,
        "can_optimize": False,
        "model_readiness_status": "NOT_PROVEN",
        "solver_use": "AUDIT_ONLY",
        "product_claim_ready": False,
    }


def base():
    """Fully-conformant QUARANTINED marine epoxy-amine score envelope.

    Predicted ACCEPT by both oracles: it satisfies every schema requirement AND
    every runtime admission requirement (registered module, zero authority, zero
    objectives, full 10-lock set, solver_use within the audit ceiling)."""
    return {
        "module_id": "amphora-molecule-property",
        "module_version": "0.1.0",
        "candidate_id": "DGEBA-n0-IPDA-marine-primer-001",
        "status": "SCORED",
        "authority_tier": "EVIDENCE_ONLY",
        "score_0_1": 0.0,
        "objective_values": {},
        "metrics": {
            "model_card": model_card(),
            "solver_use": "AUDIT_ONLY",
            "authority_receipt": {
                "ranking_eligible": False,
                "authority_tier": "EVIDENCE_ONLY",
                "issued_by": "amphora-model-card-authority",
            },
            "eew_g_per_eq": 172.0,
            "ahew_g_per_eq": 42.6,
        },
        "gates": {"stoichiometric_index_in_envelope": True},
        "uncertainty": {"stoichiometric_index_abs": 0.05},
        "claim_locks": {k: True for k in LOCKS},
        "missing_inputs": [],
        "explanations": [
            "DGEBA(n=0)/IPDA amine-H:epoxide index from dimensioned arithmetic; audit only."
        ],
        "source_refs": ["fixtures/canonical_formulation_candidate.json"],
        "usable_by_optimizer": False,
        "evidence_scope": "formulation",
        "score_semantics": "EVIDENCE_ONLY",
        "schema_version": "amphora.score-envelope.v1",
    }


def with_gate():
    """BASE + the full 15-clause provenance gate populated (trigger + 14 obligations)."""
    env = base()
    m = env["metrics"]
    m[GATE_TRIGGER] = "amphora.model-output.v1"
    m["model_id"] = "stoichiometric-index-v1"
    m["model_receipt_hash"] = H64A
    m["formula_hash"] = H64B
    m["input_hash"] = H64A
    m["ingredient_catalog_hash"] = H64B
    m["ingredient_catalog_source_hash"] = H64A
    m["normalization_version"] = "norm-v1"
    m["prediction_status"] = "IN_DOMAIN"
    m["primary_prediction"] = {
        "value": 1.02, "unit": "amine_H_per_epoxide",
        "lower_95": 0.97, "upper_95": 1.07,
    }
    m["model_readiness_status"] = "NOT_PROVEN"
    m["score_content_hash"] = H64B
    m["claim_boundary"] = "R&D audit only; no product performance claim"
    return env


CASES = []


def add(case_id, layer, schema_pred, runtime_pred, note, env, reasons=None):
    CASES.append({
        "case_id": case_id,
        "layer": layer,
        "schema_prediction": schema_pred,
        "runtime_prediction": runtime_pred,
        "note": note,
        "runtime_reject_reasons_predicted": reasons or [],
        "_env": env,
    })


# ---------------------------------------------------------------- L1 CORE_PARITY_ACCEPT
add("P01_base_conformant", "CORE_PARITY", "ACCEPT", "ADMIT",
    "Fully-conformant quarantined DGEBA/IPDA envelope.", base())

e = base(); e["metrics"]["hansen_ra_mpa_half"] = 1.19
add("P02_extra_metrics_keys", "CORE_PARITY", "ACCEPT", "ADMIT",
    "metrics.additionalProperties=true; runtime ignores unknown metrics keys.", e)

e = base(); e["authority_tier"] = "ROADMAP"; e["score_semantics"] = "ROADMAP"
add("P03_roadmap_tier", "CORE_PARITY", "ACCEPT", "ADMIT",
    "ROADMAP is in the schema enum and is not in the runtime escalation blocklist.", e)

e = base(); e["metrics"]["solver_use"] = "DISABLED"
add("P04_solver_disabled", "CORE_PARITY", "ACCEPT", "ADMIT",
    "solver_use=DISABLED is within the runtime ceiling set.", e)

e = base(); e["metrics"]["solver_use"] = "CONSTRAINT_ONLY"
add("P05_solver_constraint_only", "CORE_PARITY", "ACCEPT", "ADMIT",
    "solver_use=CONSTRAINT_ONLY is the top of the runtime ceiling set.", e)

e = base(); e["status"] = "FAILED_GATES"; e["score_semantics"] = "AUDIT_CONSTRAINT"
add("P06_failed_gates_status", "CORE_PARITY", "ACCEPT", "ADMIT",
    "status is only status-checked by the runtime when a hard constraint targets the "
    "module; with no constraints both oracles accept.", e)

# ------------------------------------------------- L2 CORE_PARITY_REJECT (shared requirements)
for key in RUNTIME_ALSO_REQUIRED:
    e = base(); e.pop(key)
    add(f"R01_missing_{key}", "CORE_PARITY", "REJECT", "REJECT",
        f"'{key}' is required by the schema AND dereferenced by the runtime admission path.",
        e, [f"{key} absent"])

for tier in ["RANKING", "OPTIMIZER", "PRODUCTION"]:
    e = base(); e["authority_tier"] = tier
    add(f"R02_escalated_tier_{tier}", "CORE_PARITY", "REJECT", "REJECT",
        "Escalated authority tier: outside the schema enum AND on the runtime blocklist "
        "(defence in depth -- both deciders agree).", e, ["authority escalation"])

# --------------------------------------- L3 RUNTIME_SUPERSET :: provenance gate is opt-in
e = base(); e["metrics"].pop("solver_use")
add("S01_drop_metrics_solver_use", "RUNTIME_SUPERSET_PROVENANCE", "ACCEPT", "REJECT",
    "Runtime unconditionally dereferences /metrics/solver_use; the schema requires it "
    "ONLY when metrics.model_receipt_schema is present.", e, ["solver_use is absent"])

e = base(); e["metrics"].pop("authority_receipt")
add("S02_drop_authority_receipt", "RUNTIME_SUPERSET_PROVENANCE", "ACCEPT", "REJECT",
    "Runtime unconditionally dereferences /metrics/authority_receipt/ranking_eligible.",
    e, ["ranking lock is absent"])

e = base(); e["metrics"]["authority_receipt"].pop("ranking_eligible")
add("S03_drop_ranking_eligible", "RUNTIME_SUPERSET_PROVENANCE", "ACCEPT", "REJECT",
    "authority_receipt present but the ranking lock inside it is unconstrained by the schema.",
    e, ["ranking lock is absent"])

e = base(); e["metrics"]["authority_receipt"] = None
add("S04_null_authority_receipt", "RUNTIME_SUPERSET_PROVENANCE", "ACCEPT", "REJECT",
    "Schema types authority_receipt as ['object','null']; null satisfies the schema and "
    "destroys the runtime ranking lock.", e, ["ranking lock is absent"])

# ------------------------------- L4 RUNTIME_SUPERSET :: zero-authority quarantine is runtime-only
e = base(); e["usable_by_optimizer"] = True
add("E01_usable_by_optimizer_true", "RUNTIME_SUPERSET_ESCALATION", "ACCEPT", "REJECT",
    "Schema types usable_by_optimizer as a free boolean; the runtime fails closed on true.",
    e, ["optimizer escalation"])

e = base(); e["objective_values"] = {"stoichiometric_index": 1.02}
add("E02_nonempty_objective_values", "RUNTIME_SUPERSET_ESCALATION", "ACCEPT", "REJECT",
    "Schema types objective_values as a free object; the runtime fails closed on non-empty.",
    e, ["score escalation"])

e = base(); e["metrics"]["authority_receipt"]["ranking_eligible"] = True
add("E03_ranking_eligible_true", "RUNTIME_SUPERSET_ESCALATION", "ACCEPT", "REJECT",
    "Ranking lock released; schema has no opinion.", e, ["ranking escalation"])

for lock in LOCKS:
    e = base(); e["claim_locks"].pop(lock)
    add(f"E04_missing_lock_{lock}", "RUNTIME_SUPERSET_ESCALATION", "ACCEPT", "REJECT",
        f"Zero-authority claim lock '{lock}' absent; schema types claim_locks as a free object.",
        e, ["lock escalation"])

e = base(); e["claim_locks"]["no_release_authority"] = False
add("E05_lock_set_false", "RUNTIME_SUPERSET_ESCALATION", "ACCEPT", "REJECT",
    "Zero-authority lock explicitly released to false.", e, ["lock escalation"])

for su in ["OBJECTIVE", "R&D_OBJECTIVE"]:
    e = base(); e["metrics"]["solver_use"] = su
    add(f"E06_solver_use_{su.replace('&', 'and')}", "RUNTIME_SUPERSET_ESCALATION",
        "ACCEPT", "REJECT",
        f"solver_use={su} is INSIDE the schema enum but ABOVE the runtime ceiling set "
        "{DISABLED, AUDIT_ONLY, CONSTRAINT_ONLY}.", e, ["solver escalation"])

# ---------------------------------------------------- L5 SCHEMA_SUPERSET (schema stricter)
for key in SCHEMA_ONLY_REQUIRED:
    e = base(); e.pop(key)
    add(f"C01_missing_{key}", "SCHEMA_SUPERSET", "REJECT", "ADMIT",
        f"'{key}' is schema-required but never dereferenced by the runtime admission path.",
        e)

e = base(); e["score_0_1"] = 1.5
add("C02_score_above_one", "SCHEMA_SUPERSET", "REJECT", "ADMIT",
    "score_0_1 maximum=1 is schema-only.", e)

e = base(); e["score_0_1"] = -0.1
add("C03_score_below_zero", "SCHEMA_SUPERSET", "REJECT", "ADMIT",
    "score_0_1 minimum=0 is schema-only.", e)

e = base(); e["status"] = "PARTIALLY_SCORED"
add("C04_status_off_enum", "SCHEMA_SUPERSET", "REJECT", "ADMIT",
    "status enum is schema-only when no hard constraint targets the module.", e)

e = base(); e["score_semantics"] = "RANKING"
add("C05_score_semantics_off_enum", "SCHEMA_SUPERSET", "REJECT", "ADMIT",
    "score_semantics enum is schema-only.", e)

e = base(); e["evidence_scope"] = ""
add("C06_empty_evidence_scope", "SCHEMA_SUPERSET", "REJECT", "ADMIT",
    "evidence_scope minLength=1 is schema-only.", e)

e = base(); e["metrics"]["model_card"].pop("kpi_name")
add("C07_model_card_missing_kpi_name", "SCHEMA_SUPERSET", "REJECT", "ADMIT",
    "model_card.required is schema-only; the runtime never reads the model card.", e)

e = base(); e["metrics"].pop("model_card")
add("C08_drop_model_card", "SCHEMA_SUPERSET", "REJECT", "ADMIT",
    "metrics.required=[model_card] is schema-only.", e)

e = base(); e["metrics"]["input_hash"] = "zz"
add("C09_bad_hash_pattern", "SCHEMA_SUPERSET", "REJECT", "ADMIT",
    "The 64-hex pattern on metrics hash fields is schema-only.", e)

# -------------------------- L6 CONDITIONAL GATE :: clause necessity + fail-open escape hatch
add("G00_gate_fully_populated", "CONDITIONAL_GATE", "ACCEPT", "ADMIT",
    "Trigger + all 14 obligations present: the provenance gate is satisfied.", with_gate())

for ob in GATE_OBLIGATIONS:
    e = with_gate(); e["metrics"].pop(ob)
    pred_rt = "REJECT" if ob in ("solver_use", "authority_receipt") else "ADMIT"
    reasons = []
    if ob == "solver_use":
        reasons = ["solver_use is absent"]
    if ob == "authority_receipt":
        reasons = ["ranking lock is absent"]
    add(f"G01_ablate_{ob}", "CONDITIONAL_GATE", "REJECT", pred_rt,
        f"Necessity ablation: with the trigger present, dropping obligation '{ob}' must be "
        "rejected by the schema (clause is load-bearing).", e, reasons)

e = with_gate(); e["metrics"].pop(GATE_TRIGGER)
add("G02_escape_hatch_drop_trigger", "CONDITIONAL_GATE", "ACCEPT", "ADMIT",
    "FAIL-OPEN: deleting the single trigger key model_receipt_schema discharges all 14 "
    "provenance obligations at once; the schema still accepts.", e)

e = base()
e["metrics"]["model_id"] = "unpinned-heuristic"
e["metrics"]["prediction_status"] = "IN_DOMAIN"
e["metrics"]["primary_prediction"] = {
    "value": 0.87, "unit": "normalized_0_1", "lower_95": None, "upper_95": None,
}
e["score_0_1"] = 0.87
add("G03_escape_hatch_bare_prediction", "CONDITIONAL_GATE", "ACCEPT", "ADMIT",
    "FAIL-OPEN, realistic form: a numeric primary_prediction with NO model_receipt_hash, "
    "formula_hash, input_hash, catalog hashes, normalization_version, score_content_hash, "
    "claim_boundary or authority_receipt binding is schema-valid, because the entire "
    "provenance gate is opt-in on a key the emitter controls.", e)

# ------------------------------------------------------- L7 EMPIRICAL (shipped fixtures)
FIXTURE_NAMES = sorted(p.name for p in FIXTURES.glob("score_*.json"))
FIXTURE_SHA = {}
for name in FIXTURE_NAMES:
    raw = (FIXTURES / name).read_bytes()
    FIXTURE_SHA[name] = hashlib.sha256(raw).hexdigest()
    env = json.loads(raw)
    stem = name[:-5]
    add(f"F01_shipped_{stem}", "EMPIRICAL_SHIPPED", "ACCEPT", "REJECT",
        "Shipped module fixture, verbatim.", env,
        ["module_id unregistered", "solver_use is absent", "ranking lock is absent"])
    rep = deepcopy(env)
    rep["module_id"] = "amphora-molecule-property"
    add(f"F02_registered_{stem}", "EMPIRICAL_SHIPPED", "ACCEPT", "REJECT",
        "Same fixture with module_id repaired to a registered module -- localizes that the "
        "runtime refusal is NOT merely module registration.", rep,
        ["solver_use is absent", "ranking lock is absent"])


def main():
    out = Path(sys.argv[1])
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    manifest = {"cases": [], "layer_counts": {}, "fixture_sha256": FIXTURE_SHA}
    seen = set()
    for c in sorted(CASES, key=lambda x: x["case_id"]):
        assert c["case_id"] not in seen, c["case_id"]
        seen.add(c["case_id"])
        payload = json.dumps(c["_env"], indent=2, sort_keys=True).encode()
        (out / (c["case_id"] + ".json")).write_bytes(payload)
        row = {k: v for k, v in c.items() if k != "_env"}
        row["case_sha256"] = hashlib.sha256(payload).hexdigest()
        manifest["cases"].append(row)
        manifest["layer_counts"][c["layer"]] = manifest["layer_counts"].get(c["layer"], 0) + 1
    manifest["n_cases"] = len(manifest["cases"])
    manifest["schema_required_keys"] = SCHEMA_REQUIRED
    manifest["runtime_also_required_keys"] = RUNTIME_ALSO_REQUIRED
    manifest["schema_only_required_keys"] = SCHEMA_ONLY_REQUIRED
    manifest["conditional_gate"] = {
        "trigger_key": GATE_TRIGGER,
        "obligation_keys": GATE_OBLIGATIONS,
        "n_clauses": 1 + len(GATE_OBLIGATIONS),
    }
    manifest["required_zero_authority_claim_locks"] = LOCKS
    (out / "_corpus_manifest.json").write_bytes(
        json.dumps(manifest, indent=2, sort_keys=True).encode())
    print("cases", manifest["n_cases"])
    for k in sorted(manifest["layer_counts"]):
        print(" ", k, manifest["layer_counts"][k])


if __name__ == "__main__":
    main()
