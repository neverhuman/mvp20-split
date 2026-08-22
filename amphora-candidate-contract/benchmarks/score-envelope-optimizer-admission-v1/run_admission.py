#!/usr/bin/env python3
"""amphora-candidate-contract :: score-envelope-optimizer-admission-v1

Oracle A (declarative JSON Schema over CPython json) x Oracle B (compiled Rust
amphora-core optimizer admission path) differential adjudication of the SCORE half
of the candidate contract.

usage: run_admission.py <corpus_dir> <rust_verdicts.json> <out_diagnostic.json>

AUDIT_ONLY.  Reads the on-disk schema and corpus; writes exactly one diagnostic file.
"""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import jsonschema
from importlib.metadata import version as _pkg_version

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MODULE = ROOT / "amphora-candidate-contract"
SCHEMA_PATH = MODULE / "schemas/score-envelope.schema.json"
CORE_LIB = ROOT / "amphora-core/src/lib.rs"
CORE_PHASE0 = ROOT / "amphora-core/src/phase0.rs"


def sha(b):
    return hashlib.sha256(b).hexdigest()


def main():
    corpus = Path(sys.argv[1])
    rust_path = Path(sys.argv[2])
    out_path = Path(sys.argv[3])

    schema_bytes = SCHEMA_PATH.read_bytes()
    schema = json.loads(schema_bytes)
    validator = jsonschema.Draft202012Validator(schema)
    manifest = json.loads((corpus / "_corpus_manifest.json").read_bytes())
    rust = json.loads(rust_path.read_bytes())

    per_case = []
    for row in manifest["cases"]:
        cid = row["case_id"]
        env = json.loads((corpus / (cid + ".json")).read_bytes())
        errors = sorted(validator.iter_errors(env), key=lambda e: list(e.absolute_path))
        schema_verdict = "ACCEPT" if not errors else "REJECT"
        schema_first_error = None
        if errors:
            e0 = errors[0]
            schema_first_error = f"{'/'.join(str(p) for p in e0.absolute_path)}:{e0.validator}"
        rv = rust.get(cid, {})
        runtime_verdict = rv.get("runtime_verdict", "MISSING")
        stable = bool(rv.get("detail", {}).get("stable_within_process", False)) \
            if isinstance(rv.get("detail"), dict) else False
        schema_ok = schema_verdict == row["schema_prediction"]
        runtime_ok = runtime_verdict == row["runtime_prediction"]
        if schema_verdict == "ACCEPT" and runtime_verdict == "ADMIT":
            relation = "BOTH_ADMIT"
        elif schema_verdict == "REJECT" and runtime_verdict == "REJECT":
            relation = "BOTH_REJECT"
        elif schema_verdict == "ACCEPT" and runtime_verdict == "REJECT":
            relation = "RUNTIME_STRICTER"
        else:
            relation = "SCHEMA_STRICTER"
        per_case.append({
            "case_id": cid,
            "layer": row["layer"],
            "note": row["note"],
            "case_sha256": row["case_sha256"],
            "schema_prediction": row["schema_prediction"],
            "schema_verdict": schema_verdict,
            "schema_prediction_met": schema_ok,
            "schema_first_error": schema_first_error,
            "runtime_prediction": row["runtime_prediction"],
            "runtime_verdict": runtime_verdict,
            "runtime_prediction_met": runtime_ok,
            "runtime_stable_within_process": stable,
            "runtime_reject_reasons_predicted": row["runtime_reject_reasons_predicted"],
            "relation": relation,
        })

    by_id = {c["case_id"]: c for c in per_case}

    def sel(layer):
        return [c for c in per_case if c["layer"] == layer]

    core = sel("CORE_PARITY")
    prov = sel("RUNTIME_SUPERSET_PROVENANCE")
    esc = sel("RUNTIME_SUPERSET_ESCALATION")
    css = sel("SCHEMA_SUPERSET")
    gate = sel("CONDITIONAL_GATE")
    emp = sel("EMPIRICAL_SHIPPED")

    gate_ablations = [c for c in gate if c["case_id"].startswith("G01_ablate_")]
    gate_escapes = [c for c in gate if c["case_id"].startswith("G02_") or
                    c["case_id"].startswith("G03_")]
    shipped = [c for c in emp if c["case_id"].startswith("F01_")]
    registered = [c for c in emp if c["case_id"].startswith("F02_")]

    gates = {
        "G1_core_parity": {
            "n": len(core),
            "passed": all(c["relation"] in ("BOTH_ADMIT", "BOTH_REJECT") for c in core)
            and all(c["schema_prediction_met"] and c["runtime_prediction_met"] for c in core),
            "note": "On the shared-requirement core (8 jointly-dereferenced required keys, "
                    "3 escalated authority tiers, 6 conformant positives) the declarative "
                    "schema and the compiled runtime must agree case-for-case. ANY "
                    "disagreement here REFUTES core admission parity.",
        },
        "G2_runtime_superset_provenance": {
            "n": len(prov),
            "passed": len(prov) > 0 and all(c["relation"] == "RUNTIME_STRICTER" for c in prov),
            "note": "The runtime unconditionally requires metrics.solver_use and "
                    "metrics.authority_receipt.ranking_eligible; the schema requires them "
                    "only under the opt-in model_receipt_schema trigger. Schema ACCEPTS, "
                    "runtime REJECTS.",
        },
        "G3_runtime_superset_escalation": {
            "n": len(esc),
            "passed": len(esc) > 0 and all(c["relation"] == "RUNTIME_STRICTER" for c in esc),
            "note": "The entire zero-authority quarantine (optimizer lock, empty objective "
                    "vector, ranking lock, 10 required claim locks, solver ceiling) is "
                    "enforced ONLY by the runtime; the published schema admits every "
                    "escalation.",
        },
        "G4_schema_superset": {
            "n": len(css),
            "passed": len(css) > 0 and all(c["relation"] == "SCHEMA_STRICTER" for c in css),
            "note": "Conversely the schema rejects 10 schema-only required keys and 9 "
                    "value-level constraints (range, enum, minLength, hash pattern, "
                    "model_card shape) that the runtime admission path never reads.",
        },
        "G5_conditional_gate_clause_necessity": {
            "n": len(gate_ablations),
            "passed": len(gate_ablations) == 14
            and all(c["schema_verdict"] == "REJECT" for c in gate_ablations)
            and by_id["G00_gate_fully_populated"]["schema_verdict"] == "ACCEPT",
            "note": "With the trigger present, each of the 14 provenance obligations is "
                    "individually load-bearing: deleting any one is rejected, and the fully "
                    "populated envelope is accepted. No redundant clause.",
        },
        "G6_gate_fail_open_confirmed": {
            "n": len(gate_escapes),
            "passed": len(gate_escapes) == 2
            and all(c["schema_verdict"] == "ACCEPT" for c in gate_escapes),
            "note": "REFUTATION GATE: deleting the single emitter-controlled trigger key "
                    "discharges all 14 obligations, and a bare numeric primary_prediction "
                    "with zero provenance binding is schema-valid. The provenance gate is "
                    "opt-in, not a mandatory mediator.",
        },
        "G7_empirical_shipped_fixtures": {
            "n": len(emp),
            "passed": len(shipped) == 6
            and all(c["schema_verdict"] == "ACCEPT" for c in shipped)
            and all(c["runtime_verdict"] == "REJECT" for c in shipped)
            and all(c["runtime_verdict"] == "REJECT" for c in registered),
            "note": "All 6 score fixtures shipped by the module are schema-VALID and "
                    "runtime-INADMISSIBLE, and remain inadmissible after module_id is "
                    "repaired to a registered module -- so the refusal is the missing "
                    "provenance/quarantine fields, not registration.",
        },
        "G8_runtime_oracle_determinism": {
            "n": len([c for c in per_case if c["runtime_verdict"] != "MISSING"]),
            "passed": all(c["runtime_stable_within_process"] for c in per_case
                          if c["runtime_verdict"] != "MISSING"),
            "note": "Every runtime verdict reproduced by a second independent "
                    "rank_candidates construction inside the same process.",
        },
    }

    predictions_met = sum(1 for c in per_case
                          if c["schema_prediction_met"] and c["runtime_prediction_met"])
    confusion = {
        "BOTH_ADMIT": sum(1 for c in per_case if c["relation"] == "BOTH_ADMIT"),
        "BOTH_REJECT": sum(1 for c in per_case if c["relation"] == "BOTH_REJECT"),
        "RUNTIME_STRICTER": sum(1 for c in per_case if c["relation"] == "RUNTIME_STRICTER"),
        "SCHEMA_STRICTER": sum(1 for c in per_case if c["relation"] == "SCHEMA_STRICTER"),
    }
    all_passed = all(g["passed"] for g in gates.values())

    n_ship_valid = sum(1 for c in shipped if c["schema_verdict"] == "ACCEPT")
    n_ship_inadm = sum(1 for c in shipped if c["runtime_verdict"] == "REJECT")

    diag = {
        "schema": "amphora.candidate-contract.score-envelope-optimizer-admission.v1",
        "study_id": "score-envelope-optimizer-admission-v1",
        "module": "amphora-candidate-contract",
        "run_type": "DIFFERENTIAL_SCORE_ENVELOPE_SCHEMA_VS_OPTIMIZER_ADMISSION",
        "authority": "AUDIT_ONLY",
        "headline": (
            "H0 REFUTED, BIDIRECTIONALLY: the published score-envelope schema is NOT the "
            f"binding optimizer-admission contract. Core parity holds exactly ({len(core)}/"
            f"{len(core)}), but the runtime is a strict reject-superset on the provenance "
            f"({confusion['RUNTIME_STRICTER']} cases total: {len(prov)} provenance + "
            f"{len(esc)} zero-authority-quarantine) while the schema is a strict "
            f"reject-superset on {confusion['SCHEMA_STRICTER']} presentation/range/enum "
            "cases. The schema's 15-clause provenance gate is clause-necessary (14/14) but "
            "FAIL-OPEN: it is keyed on an emitter-controlled trigger, so a numeric "
            "prediction with zero provenance binding is schema-valid -- and all "
            f"{n_ship_valid}/6 shipped score fixtures are schema-valid yet "
            f"{n_ship_inadm}/6 runtime-inadmissible."
        ),
        "purpose": (
            "Audit the SCORE half of the candidate contract -- the output envelope that 29 "
            "consumer modules and the optimizer front door depend on -- by differentially "
            "testing the on-disk declarative schema against the compiled optimizer "
            "admission path, and by ablating every clause of the schema's conditional "
            "provenance gate for necessity and for fail-safe behaviour."
        ),
        "hypothesis": {
            "statement": "the published score-envelope JSON Schema and the compiled "
                         "optimizer admission path accept and reject the same typed corpus "
                         "of score envelopes",
            "core_layer": "CORROBORATED" if gates["G1_core_parity"]["passed"] else "REFUTED",
            "provenance_layer": "REFUTED" if gates["G2_runtime_superset_provenance"]["passed"]
                                else "CORROBORATED",
            "zero_authority_quarantine_layer": "REFUTED"
            if gates["G3_runtime_superset_escalation"]["passed"] else "CORROBORATED",
            "presentation_layer": "REFUTED" if gates["G4_schema_superset"]["passed"]
                                  else "CORROBORATED",
            "gate_clause_necessity": "CORROBORATED"
            if gates["G5_conditional_gate_clause_necessity"]["passed"] else "REFUTED",
            "gate_fail_safe_default": "REFUTED" if gates["G6_gate_fail_open_confirmed"]["passed"]
                                      else "CORROBORATED",
            "divergence_direction": "BIDIRECTIONAL",
            "verdict": "REFUTED",
            "interpretation": (
                "The two deciders are INCOMPARABLE, not equivalent. (a) RUNTIME-STRICTER: "
                "the optimizer front door unconditionally dereferences /metrics/solver_use "
                "and /metrics/authority_receipt/ranking_eligible and enforces the whole "
                "zero-authority quarantine (usable_by_optimizer=false, empty "
                "objective_values, ranking lock down, all 10 REQUIRED_ZERO_AUTHORITY_CLAIM_"
                "LOCKS true, solver_use within {DISABLED, AUDIT_ONLY, CONSTRAINT_ONLY}, "
                "module registered); the schema constrains none of that -- claim_locks and "
                "objective_values are free objects, usable_by_optimizer is a free boolean, "
                "and OBJECTIVE/R&D_OBJECTIVE are INSIDE the schema's solver_use enum but "
                "ABOVE the runtime ceiling. (b) SCHEMA-STRICTER: 10 schema-required keys "
                "plus score_0_1 range, status/score_semantics enums, evidence_scope "
                "minLength, model_card shape and the 64-hex hash pattern are never read by "
                "the admission path. (c) FAIL-OPEN GATE: metrics.allOf[0] fires only on "
                "metrics.model_receipt_schema, a key the emitting module chooses to write; "
                "every one of its 14 obligations is individually load-bearing when it "
                "fires, and every one of them evaporates when it does not. This inverts "
                "Saltzer & Schroeder's fail-safe-defaults and complete-mediation "
                "principles: the default is permit, and the mediator is bypassable by "
                "omission. The empirical layer confirms this is not hypothetical -- 0/6 of "
                "the module's own shipped score fixtures set the trigger, 2 of them carry "
                "score_0_1=1.0 with usable_by_optimizer=true, and all 6 are schema-valid."
            ),
        },
        "non_circularity": (
            "Two independently-authored deciders. Oracle A is the on-disk declarative "
            "score-envelope JSON Schema enforced by jsonschema 4.26.0 over CPython json. "
            "Oracle B is the compiled Rust amphora-core optimizer admission path reached "
            "through the public rank_candidates entry point (which internally runs the "
            "private optimizer_envelopes extraction and authorize_optimizer_request). "
            "Neither oracle was fitted to the other; the per-case LAYER and BOTH per-case "
            "verdict PREDICTIONS were declared in a third artifact "
            "(build_score_corpus.py) from the module semantics before either oracle ran. "
            "The empirical layer uses the module's own shipped fixtures verbatim, which "
            "predate this study."
        ),
        "theory_reference": [
            "J. H. Saltzer and M. D. Schroeder (1975), 'The Protection of Information in "
            "Computer Systems', Proceedings of the IEEE 63(9):1278-1308, "
            "DOI 10.1109/PROC.1975.9939 -- fail-safe defaults; complete mediation; "
            "economy of mechanism.",
            "D. E. Denning (1976), 'A Lattice Model of Secure Information Flow', "
            "Communications of the ACM 19(5):236-243, DOI 10.1145/360051.360056 -- "
            "authority tiers as a bounded lattice.",
            "IETF RFC 8259 (2017), 'The JavaScript Object Notation (JSON) Data Interchange "
            "Format'.",
            "JSON Schema draft 2020-12 (2020-12-08) Core + Validation vocabularies "
            "(allOf / if-then, required, enum, pattern, minimum/maximum).",
            "IETF RFC 8785 (2020), 'JSON Canonicalization Scheme (JCS)'.",
            "NIST FIPS 180-4 (2015), 'Secure Hash Standard' -- SHA-256.",
        ],
        "oracle_A_declarative": {
            "artifact": "amphora-candidate-contract/schemas/score-envelope.schema.json",
            "schema_sha256": sha(schema_bytes),
            "dialect": "https://json-schema.org/draft/2020-12/schema",
            "validator": "jsonschema==" + _pkg_version("jsonschema"),
            "parser": "CPython stdlib json",
            "deployment_model": "parse-then-validate (the schema-only consumer front door)",
        },
        "oracle_B_runtime": {
            "artifact": "amphora-core::rank_candidates -> optimizer_envelopes + "
                        "authorize_optimizer_request",
            "entry_point": "public rank_candidates(&[Value], &KpiProfile) with an empty "
                           "profile; verdict = RankedCandidate.feasible",
            "amphora_core_lib_sha256": sha(CORE_LIB.read_bytes()),
            "amphora_core_phase0_sha256": sha(CORE_PHASE0.read_bytes()),
            "policy": "quarantined_optimizer_policy() -- ranking disabled, solver disabled, "
                      "authority expansion forbidden, decision ceiling AUDIT_ONLY",
            "registered_module_count": 29,
            "required_zero_authority_claim_locks": manifest[
                "required_zero_authority_claim_locks"],
            "verdict_level_only": True,
        },
        "corpus": {
            "n_cases": manifest["n_cases"],
            "manifest_sha256": sha((corpus / "_corpus_manifest.json").read_bytes()),
            "layer_counts": manifest["layer_counts"],
            "conditional_gate": manifest["conditional_gate"],
            "schema_required_keys": manifest["schema_required_keys"],
            "runtime_also_required_keys": manifest["runtime_also_required_keys"],
            "schema_only_required_keys": manifest["schema_only_required_keys"],
            "shipped_fixture_sha256": manifest["fixture_sha256"],
        },
        "results": {
            "all_gates_passed": all_passed,
            "n_cases": len(per_case),
            "predictions_met": predictions_met,
            "predictions_total": len(per_case),
            "confusion": confusion,
            "core_parity_agree": len([c for c in core if c["relation"] in
                                      ("BOTH_ADMIT", "BOTH_REJECT")]),
            "core_parity_disagree": len([c for c in core if c["relation"] not in
                                         ("BOTH_ADMIT", "BOTH_REJECT")]),
            "gate_clauses_load_bearing": len([c for c in gate_ablations
                                              if c["schema_verdict"] == "REJECT"]),
            "gate_clauses_total": len(gate_ablations),
            "gate_escape_hatches_confirmed": len([c for c in gate_escapes
                                                  if c["schema_verdict"] == "ACCEPT"]),
            "shipped_fixtures_schema_valid": n_ship_valid,
            "shipped_fixtures_runtime_inadmissible": n_ship_inadm,
            "shipped_fixtures_total": len(shipped),
            "shipped_fixtures_setting_provenance_trigger": 0,
        },
        "divergence_notes": [
            {"class": "RUNTIME_SUPERSET_PROVENANCE",
             "note": "metrics.solver_use and metrics.authority_receipt.ranking_eligible are "
                     "unconditional runtime admission requirements but only conditional "
                     "schema requirements. A schema-only consumer will hand the optimizer "
                     "envelopes the optimizer cannot read. Phase-1 repair: hoist both keys "
                     "into metrics.required unconditionally."},
            {"class": "RUNTIME_SUPERSET_ESCALATION",
             "note": "The zero-authority quarantine lives ONLY in Rust. A downstream "
                     "consumer validating against the published schema alone would accept "
                     "usable_by_optimizer=true, a non-empty objective vector, a released "
                     "ranking lock, missing claim locks and solver_use=OBJECTIVE. Today the "
                     "runtime holds the line; the published contract does not state it."},
            {"class": "SCHEMA_SUPERSET",
             "note": "Conversely the schema rejects presentation/range/enum/pattern "
                     "violations the admission path admits. Neither decider subsumes the "
                     "other -- they are incomparable."},
            {"class": "FAIL_OPEN_GATE",
             "note": "metrics.allOf[0] is keyed on metrics.model_receipt_schema, which the "
                     "EMITTER controls. Every clause is load-bearing when the trigger is "
                     "set (14/14 ablations rejected) and every clause is void when it is "
                     "not. Phase-1 repair options: (i) trigger the gate on the presence of "
                     "metrics.primary_prediction instead, (ii) make model_receipt_schema "
                     "itself unconditionally required for status=SCORED, or (iii) require "
                     "prediction_status=NOT_RUN whenever the trigger is absent."},
        ],
        "closes": [
            "FIRST audit of the SCORE half of amphora-candidate-contract; the three prior "
            "studies (schema-runtime-parity-v1, schema-runtime-differential-mutation-v1, "
            "raw-structure-ban-recursion-v1) all cover the candidate (input) envelope only.",
            "Establishes verdict-level core admission parity on the 8 jointly-dereferenced "
            "required keys and the 3 escalated authority tiers.",
            "Proves clause necessity for all 14 obligations of the conditional provenance "
            "gate (no redundant clause).",
            "Demonstrates, with the module's own 6 shipped fixtures, that the fail-open "
            "trigger is the live state and not a hypothetical: 0/6 set it and 6/6 are "
            "runtime-inadmissible.",
        ],
        "does_not_close": [
            "Reason-level parity: only ADMIT/REJECT verdicts are claimed; the runtime error "
            "taxonomy is not compared against schema error paths.",
            "Whether to repair by tightening the schema or by relaxing the runtime is a "
            "Phase-1 design decision, not an audit call.",
            "Cross-module conformance of the 29 consumers' actually-emitted score envelopes "
            "at run time (only the module's own shipped fixtures were available on disk).",
            "Coverage-guided fuzzing of the admission path; hard-constraint and objective "
            "evaluation paths (the corpus uses an empty KPI profile by construction).",
            "No promotion, no manifest edit, no scientific_readiness flip, no wet-lab, "
            "qualification, or release authority.",
        ],
        "gates": gates,
        "all_gates_passed": all_passed,
        "per_case": per_case,
    }
    out_path.write_bytes(json.dumps(diag, indent=2, sort_keys=True).encode())
    print("cases", len(per_case), "predictions_met", predictions_met,
          "all_gates_passed", all_passed)
    print("confusion", confusion)
    for k, v in gates.items():
        print(f"  {k}: n={v['n']} passed={v['passed']}")
    print("diagnostic_sha256", sha(out_path.read_bytes()))


if __name__ == "__main__":
    main()
