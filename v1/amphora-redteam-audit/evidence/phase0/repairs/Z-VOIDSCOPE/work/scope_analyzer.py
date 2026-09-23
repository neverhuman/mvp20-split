#!/usr/bin/env python3
"""Static-dependency analyzer for the 9 module diagnostics dispatched by
deterministic_control_diagnostic() in amphora-assurance-capabilities/src/diagnostics.rs.

For each dispatched diagnostic function, determines whether its ACCEPT/REJECT
decision for at least one of its own generated fixture cases is routed through
a call to real, externally-sourced or production data (embedded include_bytes!
fixture JSON via strict_json(), an Ed25519 .verify() call, or an imported
production function from amphora_core / amphora_formulation_capabilities).

This mechanizes the distinction the Y-VOIDCORPUS finding (2026-08-15) drew by
hand for exactly one function (redteam_diagnostic): a function whose pass/fail
outcome is a hardcoded/self-referential constant, independent of any external
or production-code-derived value, cannot ever be moved by a real defect.

Usage: python3 scope_analyzer.py <path-to-diagnostics.rs> [--mutate NAME]
  --mutate NAME: apply a textual positive-control mutation to function NAME
                 before analysis (see MUTATIONS below), to prove the detector
                 fires on a planted defect of the kind it exists to catch.
"""
import json
import sys

DIAGNOSTIC_FNS = [
    "evidence_intake_diagnostic",
    "source_ledger_diagnostic",
    "report_packager_diagnostic",
    "redteam_diagnostic",
    "formulation_arithmetic_diagnostic",
    "formulation_universe_diagnostic",
    "envelope_gates_diagnostic",
    "cro_protocol_packager_diagnostic",
    "optimizer_orchestrator_diagnostic",
]

EXTERNAL_DEPENDENCY_MARKERS = [
    "strict_json(",
    "evidence_fixture_accepted(",
    "source_control_accepted(",
    "report_fixture_accepted(",
    "protocol_fixture_accepted(",
    "validate_formulation_mass(",
    "validate_formulation_universe(",
    "evaluate_envelope_policy(",
    "authorize_optimizer_request(",
    ".verify(",
]

MODULE_ID_OF_FN = {
    "evidence_intake_diagnostic": "amphora-evidence-intake-validator",
    "source_ledger_diagnostic": "amphora-source-ledger",
    "report_packager_diagnostic": "amphora-report-packager",
    "redteam_diagnostic": "amphora-redteam-audit",
    "formulation_arithmetic_diagnostic": "amphora-formulation-arithmetic",
    "formulation_universe_diagnostic": "amphora-formulation-universe",
    "envelope_gates_diagnostic": "amphora-envelope-gates",
    "cro_protocol_packager_diagnostic": "amphora-cro-protocol-packager",
    "optimizer_orchestrator_diagnostic": "amphora-optimizer-orchestrator",
}


def extract_function_body(source, fn_name):
    """Return (start_idx, end_idx, body_text) for `fn fn_name(...) ... { ... }`,
    brace-matched while skipping braces inside string literals."""
    needle = f"fn {fn_name}("
    start = source.index(needle)
    brace_open = source.index("{", start)
    depth = 0
    i = brace_open
    in_string = False
    escape = False
    while i < len(source):
        ch = source[i]
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
        else:
            if ch == '"':
                in_string = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return start, i + 1, source[start:i + 1]
        i += 1
    raise ValueError(f"unbalanced braces scanning {fn_name}")


MUTATIONS = {
    # Positive control: strip formulation_arithmetic_diagnostic's real
    # dependency on validate_formulation_mass/arithmetic_candidate (which
    # takes the per-case mutated ArithmeticFixture as input) and replace the
    # per-case decision with a hardcoded literal disconnected from the fixture,
    # exactly the shape of redteam_diagnostic's `let granted = false;`.
    "formulation_arithmetic_diagnostic": {
        "find": (
            "        let result = arithmetic_candidate(fixture)\n"
            "            .and_then(|candidate| validate_formulation_mass(&candidate));\n"
            "        let accepted = result.as_ref().is_ok_and(|result| {\n"
            "            result.status == \"UNVALIDATED\"\n"
            "                && result.part_a_mass_g.is_some()\n"
            "                && result.part_b_mass_g.is_some()\n"
            "                && result.total_mass_g.is_some()\n"
            "                && result.objective_values.is_empty()\n"
            "                && !result.ranking_eligible\n"
            "                && !result.usable_by_optimizer\n"
            "                && !result.candidate_created_evidence\n"
            "                && !result.authority_upgrade\n"
            "                && !result.unresolved_legacy_data_accessed\n"
            "        });\n"
        ),
        "replace": (
            "        let result: Result<Value, String> = Ok(json!({}));\n"
            "        let accepted = true;\n"
        ),
    },
}


def analyze(source):
    report = {}
    for fn in DIAGNOSTIC_FNS:
        _, _, body = extract_function_body(source, fn)
        hits = sorted(m for m in EXTERNAL_DEPENDENCY_MARKERS if m in body)
        report[fn] = {
            "module_id": MODULE_ID_OF_FN[fn],
            "body_char_len": len(body),
            "external_dependency_markers_found": hits,
            "has_external_dependency": len(hits) > 0,
        }
    return report


def main():
    path = sys.argv[1]
    mutate = None
    if "--mutate" in sys.argv:
        mutate = sys.argv[sys.argv.index("--mutate") + 1]
    source = open(path, encoding="utf-8").read()
    if mutate:
        if mutate not in MUTATIONS:
            print(f"no mutation defined for {mutate}", file=sys.stderr)
            sys.exit(2)
        start, end, body = extract_function_body(source, mutate)
        m = MUTATIONS[mutate]
        if m["find"] not in body:
            print(f"mutation anchor text not found in {mutate} -- source has drifted", file=sys.stderr)
            sys.exit(3)
        mutated_body = body.replace(m["find"], m["replace"], 1)
        source = source[:start] + mutated_body + source[end:]
    report = analyze(source)
    tautological = sorted(fn for fn, r in report.items() if not r["has_external_dependency"])
    out = {
        "schema": "amphora.redteam-audit.diagnostic-tautology-scope-scan.v1",
        "analyzed_path": path,
        "mutated_function": mutate,
        "diagnostic_fn_count": len(DIAGNOSTIC_FNS),
        "per_function": report,
        "tautological_fn_names": tautological,
        "tautological_count": len(tautological),
    }
    print(json.dumps(out, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
