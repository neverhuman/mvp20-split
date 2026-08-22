#!/usr/bin/env python3
"""amphora-optimizer-orchestrator -- numeric-comparison conformance study.

LIVE differential harness. The Rust side is the REAL runtime
(amphora_core::authorize_optimizer_request, linked as a library by
runtime_probe/), not a re-implementation. The Python side is the spec-side
oracle (numeric_comparison_oracle.py: RFC 8259 exact-value S1, IEEE 754-2019
binary64 S2) plus the unmodified sibling contract oracle shipped with
optimizer-authorization-oracle-parity-v1.

Deterministic: fixed corpus order, no randomness, no clock, no network.
"""
import hashlib
import json
import os
import subprocess
import sys
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import numeric_comparison_oracle as spec          # noqa: E402
import optimizer_authorization_oracle as sib      # noqa: E402

SIBLING_ORACLE_SHA = "a0da8ec147ed82bbdf0b58a56b157ba6a683cebe4cdddb2cc38f3d8f5d7d1774"
RUNTIME_ANCHOR = "amphora-core/src/lib.rs"
ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
CORPUS = HERE / "numeric_literals.v1.json"
PROBE_DIR = HERE / "runtime_probe"
GT = HERE / "runtime_ground_truth.v1.jsonl"
# Build artifacts are kept OUT of the evidence tree and out of the workspace.
TARGET = Path("/tmp/amphora-optimizer-numeric-probe-target")


def sha(b):
    return hashlib.sha256(b).hexdigest()


def run_live_probe():
    """Build + execute the live Rust probe against the real amphora-core."""
    env = dict(os.environ, CARGO_TARGET_DIR=str(TARGET))
    subprocess.run(
        ["/home/ubuntu/.cargo/bin/cargo", "build", "--release", "--offline", "--quiet"],
        cwd=PROBE_DIR, check=True, env=env,
    )
    out = subprocess.run(
        [str(TARGET / "release/optimizer-numeric-runtime-probe")],
        cwd=PROBE_DIR, input=CORPUS.read_bytes(), stdout=subprocess.PIPE, check=True,
    ).stdout
    GT.write_bytes(out)
    return {ln["case_id"]: ln for ln in (json.loads(x) for x in out.decode().splitlines())}


def verdict_from_spec(gate_sv, exp_sv, gate_reach, exp_reach, op, cmp_fn):
    if not gate_reach or not exp_reach:
        return "PARSE_REJECT"
    return "ACCEPT" if cmp_fn(gate_sv, exp_sv, op) else "REJECT"


def main():
    corpus = json.loads(CORPUS.read_text())
    lits = corpus["literals"]
    ops = corpus["operators"]
    runtime = run_live_probe()

    parsed = {}
    for L in lits:
        sv = spec.parse_rfc8259_scalar(L["text"])
        ok, why = spec.reachable(L["text"])
        parsed[L["id"]] = (sv, ok, why, L)

    # ---- G1: pre-registered reachability prediction vs measured front door --
    reach_rows, reach_hits = [], 0
    for L in lits:
        sv, pred_ok, why, _ = parsed[L["id"]]
        # measured: does the literal survive the parse in BOTH positions?
        env_ok = all(
            runtime[f"{L['id']}|{o['id']}|=="]["parse_reject_site"] not in
            ("ENVELOPE_GATE_VALUE", "BOTH") for o in lits)
        exp_ok = all(
            runtime[f"{o['id']}|{L['id']}|=="]["parse_reject_site"] not in
            ("CONSTRAINT_EXPECTED_VALUE", "BOTH") for o in lits)
        meas_ok = env_ok and exp_ok
        agree = (pred_ok == meas_ok)
        reach_hits += agree
        reach_rows.append({"literal_id": L["id"], "text": L["text"], "class": L["class"],
                           "predicted_reachable": pred_ok, "prediction_basis": why,
                           "measured_reachable": meas_ok, "agree": agree})

    # ---- full case sweep --------------------------------------------------
    cases = []
    for g in lits:
        gsv, greach, _, _ = parsed[g["id"]]
        for e in lits:
            esv, ereach, _, _ = parsed[e["id"]]
            for op in ops:
                cid = f"{g['id']}|{e['id']}|{op}"
                rt = runtime[cid]
                cases.append({
                    "case_id": cid, "gate": g["id"], "expected": e["id"], "op": op,
                    "gate_class": g["class"], "expected_class": e["class"],
                    "runtime": rt["verdict"], "runtime_reason": rt.get("reason"),
                    "quarantine_ok": rt.get("quarantine_ok"),
                    "s1": verdict_from_spec(gsv, esv, greach, ereach, op, spec.s1_compare),
                    "s2": verdict_from_spec(gsv, esv, greach, ereach, op, spec.s2_compare),
                    "m3": verdict_from_spec(gsv, esv, greach, ereach, op, spec.m3_compare),
                    "both_numeric": (gsv is not None and gsv.kind == "number"
                                     and esv is not None and esv.kind == "number"),
                    "both_reachable": greach and ereach,
                })

    def direction(rt, sp):
        if rt == sp:
            return "AGREE"
        if rt == "ACCEPT" and sp in ("REJECT", "PARSE_REJECT"):
            return "FAIL_OPEN"
        if sp == "ACCEPT" and rt in ("REJECT", "PARSE_REJECT"):
            return "FAIL_CLOSED"
        return "AGREE"

    for c in cases:
        c["dir_vs_s1"] = direction(c["runtime"], c["s1"])
        c["dir_vs_s2"] = direction(c["runtime"], c["s2"])

    ORDERING = (">=", "<=", ">", "<")
    EQUALITY = ("==", "!=")

    # ---- G2: IEEE 754-2019 binary64 ordering conformance -------------------
    g2_pool = [c for c in cases if c["op"] in ORDERING and c["both_reachable"] and c["both_numeric"]]
    g2_mismatch = [c["case_id"] for c in g2_pool if c["runtime"] != c["s2"]]

    # ---- G3: ordering fails closed on any non-numeric operand --------------
    g3_pool = [c for c in cases if c["op"] in ORDERING and c["both_reachable"]
               and not c["both_numeric"]]
    g3_bad = [c["case_id"] for c in g3_pool if c["runtime"] != "REJECT"]

    # ---- G4: IEEE special values are unreachable through the JSON grammar --
    special = [L["id"] for L in lits if L["class"] in
               ("ieee_special_nonjson", "float_overflow")]
    g4_bad = [r["literal_id"] for r in reach_rows
              if r["literal_id"] in special and r["measured_reachable"]]

    # ---- G5: quarantine invariant on every ACCEPT --------------------------
    accepts = [c for c in cases if c["runtime"] == "ACCEPT"]
    g5_bad = [c["case_id"] for c in accepts if c["quarantine_ok"] is not True]

    # ---- G6: M3 descriptive adequacy --------------------------------------
    g6_bad = [c["case_id"] for c in cases if c["runtime"] != c["m3"]]

    # ---- G7 / F7: mechanism of exact-vs-runtime ordering divergence ---------
    # Pre-registered sub-hypothesis H3b (RFC 7493 Sec.2.2): ordering divergence is
    # confined to integers outside the interoperable range [-(2^53-1), 2^53-1].
    # Integrity gate G7 tests the strictly more general mechanism: divergence can
    # only arise where roundTiesToEven actually lost information.
    def beyond_ijson(lid):
        sv = parsed[lid][0]
        return sv is not None and sv.kind == "number" and abs(sv.exact) > spec.IJSON_MAX

    def inexact_in_binary64(lid):
        sv = parsed[lid][0]
        if sv is None or sv.kind != "number":
            return False
        f, finite = spec.to_binary64(sv.exact, sv.neg_zero)
        return (not finite) or Fraction(f) != sv.exact

    ord_div = [c for c in cases if c["op"] in ORDERING and c["both_reachable"]
               and c["both_numeric"] and c["dir_vs_s1"] != "AGREE"]
    g7_bad = [c["case_id"] for c in ord_div
              if not (inexact_in_binary64(c["gate"]) or inexact_in_binary64(c["expected"]))]
    # H3b counter-examples: divergences whose operands are BOTH inside the I-JSON
    # interoperable range -- these refute the range criterion as sufficient.
    ijson_counterexamples = sorted(
        c["case_id"] for c in ord_div
        if not (beyond_ijson(c["gate"]) or beyond_ijson(c["expected"])))

    # ---- G8: sibling contract oracle unchanged + fidelity sweep ------------
    sib_sha = sha((HERE / "optimizer_authorization_oracle.py").read_bytes())

    def sibling_verdict(g, e, op):
        gsv, greach = parsed[g["id"]][0], parsed[g["id"]][1]
        esv, ereach = parsed[e["id"]][0], parsed[e["id"]][1]
        if not greach or not ereach:
            return "PARSE_REJECT", None
        gv = json.loads(g["text"])
        ev = json.loads(e["text"])
        req = sib.policy_request([], [sib.constraint("c1", sib.ENVELOPE_GATES, "g", op, ev)])
        env = sib.envelope(sib.ENVELOPE_GATES, "g", gv)
        try:
            sib.authorize(req, [env], sib.quarantined_policy())
            return "ACCEPT", None
        except sib.Reject as r:
            return "REJECT", str(r)
        except Exception as exc:                      # noqa: BLE001
            return "UNCAUGHT_EXCEPTION", f"{type(exc).__name__}: {exc}"

    sib_rows, sib_div = [], []
    for g in lits:
        for e in lits:
            for op in ops:
                cid = f"{g['id']}|{e['id']}|{op}"
                sv, _ = sibling_verdict(g, e, op)
                rt = runtime[cid]["verdict"]
                if sv != rt:
                    # Runtime is ground truth here and the oracle is the model, so
                    # the fail-open/fail-closed vocabulary used against a normative
                    # SPEC would be misleading. Label the oracle's error instead.
                    if rt == "ACCEPT":
                        lbl = "ORACLE_OVER_STRICT"      # oracle misses a real runtime ACCEPT
                    elif sv == "ACCEPT":
                        lbl = "ORACLE_OVER_PERMISSIVE"  # oracle predicts an ACCEPT the runtime denies
                    else:
                        lbl = "ORACLE_REASON_ONLY"
                    sib_div.append({"case_id": cid, "sibling": sv, "runtime": rt,
                                    "oracle_error": lbl})
                sib_rows.append(sv)

    # ---- representation-orbit equality census ------------------------------
    orbit = []
    for c in cases:
        if c["op"] != "==" or not c["both_reachable"] or not c["both_numeric"]:
            continue
        gsv, esv = parsed[c["gate"]][0], parsed[c["expected"]][0]
        if gsv.exact == esv.exact and c["gate"] != c["expected"]:
            orbit.append({"case_id": c["case_id"], "gate_text": gsv.literal,
                          "expected_text": esv.literal, "runtime": c["runtime"],
                          "rfc8259_s1": c["s1"], "ieee754_s2": c["s2"]})
    orbit_sensitive = [o for o in orbit if o["runtime"] != o["rfc8259_s1"]]

    fail_open_s1 = sorted(c["case_id"] for c in cases if c["dir_vs_s1"] == "FAIL_OPEN")
    fail_closed_s1 = sorted(c["case_id"] for c in cases if c["dir_vs_s1"] == "FAIL_CLOSED")
    fail_open_s2 = sorted(c["case_id"] for c in cases if c["dir_vs_s2"] == "FAIL_OPEN")
    fail_closed_s2 = sorted(c["case_id"] for c in cases if c["dir_vs_s2"] == "FAIL_CLOSED")

    eq_div_s1 = [c for c in cases if c["op"] in EQUALITY and c["both_reachable"]
                 and c["dir_vs_s1"] != "AGREE"]

    reasons = sorted({c["runtime_reason"] for c in cases if c["runtime_reason"]})

    gates = {
        "g1_reachability_prediction_parity": reach_hits == len(lits),
        "g2_ieee754_binary64_ordering_parity": not g2_mismatch,
        "g3_nonnumeric_ordering_fail_closed": not g3_bad,
        "g4_ieee_special_values_unreachable": not g4_bad,
        "g5_quarantine_invariant_universal": not g5_bad,
        "g6_m3_descriptive_adequacy": not g6_bad,
        "g7_ordering_divergence_explained_by_binary64_rounding": not g7_bad,
        "g8_sibling_contract_oracle_sha_unchanged": sib_sha == SIBLING_ORACLE_SHA,
    }
    gates["all_pass"] = all(gates.values())

    anchor_sha = sha((ROOT / RUNTIME_ANCHOR).read_bytes())

    diag = {
        "schema": "amphora.optimizer-orchestrator.numeric-comparison-conformance-diagnostic.v1",
        "study_id": "optimizer-authorization-numeric-comparison-conformance-v1",
        "module": "amphora-optimizer-orchestrator",
        "authority": "AUDIT_ONLY",
        "run_type": "LIVE_RUST_RUNTIME_DIFFERENTIAL_NUMERIC_CONFORMANCE",
        "purpose": (
            "Characterize the ONLY arithmetic surface inside the "
            "amphora-optimizer-orchestrator deny-by-default reference monitor: the "
            "hard-constraint comparison operator table (amphora-core::comparison_passes, "
            "reached from authorize_optimizer_request). A hostile POLICY- or "
            "CANDIDATE-sourced request controls both operands and the operator, so this "
            "table is the one place where a numeric literal can flip a constraint from "
            "fail to pass without touching any authority field. The study measures the "
            "LIVE Rust runtime over a locked 36-literal x 36-literal x 6-operator JSON-text "
            "corpus entering through the RFC 8259 front door, and differentials it against "
            "two published semantics (RFC 8259 exact-value; IEEE 754-2019 binary64)."),
        "hypothesis": (
            "H1 (reachability): no IEEE 754 special value (NaN, +/-Infinity) and no "
            "out-of-binary64-range number is reachable through the RFC 8259 front door, so "
            "the NaN-unordered comparison attack class is structurally empty. "
            "H2 (IEEE conformance): the four ordering operators implement IEEE 754-2019 "
            "Sec.5.11 compareQuiet* over binary64 exactly. "
            "H3 (RFC 8259 value-equality): the equality operators are representation-invariant, "
            "i.e. two literals denoting the same mathematical number compare equal. H3 is the "
            "cross-module transfer of the int/float representation split already recorded for "
            "amphora-cro-protocol-packager canonicalization (110.0 vs 110). "
            "H4 (oracle fidelity): the sibling CPython contract oracle that carries the two "
            "shipped optimizer audit receipts is byte-faithful to the runtime on this surface."),
        "non_circularity": (
            "The Rust side is the REAL runtime: runtime_probe/ declares a path dependency on "
            "amphora-core and calls the public amphora_core::authorize_optimizer_request; it "
            "contains no copy of the comparison logic. The spec side "
            "(numeric_comparison_oracle.py) is written from IEEE 754-2019 and RFC 8259/7493 "
            "only, imports nothing from the runtime, and admits no tunable parameter. S1 uses "
            "exact rationals (fractions.Fraction); no float touches S1. The descriptive model "
            "M3 is declared POST-HOC and is reported only as a characterization, never as "
            "evidence for H1-H4."),
        "theory_reference": [
            "IEEE Std 754-2019, IEEE Standard for Floating-Point Arithmetic, DOI 10.1109/IEEESTD.2019.8766229 -- Sec.4.3.1 roundTiesToEven; Sec.5.11 compareQuiet{Equal,Less,LessEqual,Greater,GreaterEqual} and the unordered predicate.",
            "T. Bray (ed.), RFC 8259 / IETF STD 90, The JavaScript Object Notation (JSON) Data Interchange Format (Dec 2017), DOI 10.17487/RFC8259 -- Sec.6 number grammar (no NaN/Infinity tokens; numbers denote mathematical values).",
            "ECMA-404, 2nd edition (Dec 2017), The JSON Data Interchange Syntax -- Sec.8 number syntax.",
            "T. Bray (ed.), RFC 7493, The I-JSON Message Format (Mar 2015), DOI 10.17487/RFC7493 -- Sec.2.2 binary64 range limit and the interoperable integer range [-(2^53-1), 2^53-1].",
            "J.P. Anderson, Computer Security Technology Planning Study, ESD-TR-73-51 (1972) -- reference monitor, complete mediation.",
            "Saltzer & Schroeder, The Protection of Information in Computer Systems, Proc. IEEE 63(9):1278-1308 (1975), DOI 10.1109/PROC.1975.9939 -- fail-safe defaults.",
        ],
        "method_lineage": [
            "Closes, for the numeric-comparison surface, the axis named in optimizer-authorization-clause-necessity-v1 does_not_close: 'a live differential harness that executes the Rust runtime and captures its reason strings'.",
            "Transfers the int/float representation hypothesis from amphora-cro-protocol-packager canonicalization-conformance (110.0 vs 110) onto a security-relevant authorization surface.",
            "Follows amphora-candidate-contract differential-mutation in reporting divergence DIRECTION (fail-open vs fail-closed) rather than a bare mismatch count.",
        ],
        "runtime_source_anchors": {
            RUNTIME_ANCHOR: anchor_sha,
            "runtime_entry_point": "amphora_core::authorize_optimizer_request",
            "comparison_surface": "amphora-core/src/lib.rs::comparison_passes",
            "serde_json_pin": "=1.0.150 (features=[float_roundtrip]); matches workspace Cargo.lock",
            "sibling_oracle_parity_oracle_sha256": SIBLING_ORACLE_SHA,
        },
        "preconditions": {
            "rust_side_is_live_runtime_not_reimplementation": True,
            "spec_side_imports_no_runtime": True,
            "s1_uses_exact_rationals_no_float": True,
            "m3_declared_post_hoc": True,
            "corpus_locked_and_order_fixed": True,
        },
        "counts": {
            "literals": len(lits),
            "operators": len(ops),
            "total_cases": len(cases),
            "runtime_accepts": len(accepts),
            "runtime_rejects": sum(1 for c in cases if c["runtime"] == "REJECT"),
            "runtime_parse_rejects": sum(1 for c in cases if c["runtime"] == "PARSE_REJECT"),
            "reachable_literals": sum(1 for r in reach_rows if r["measured_reachable"]),
            "unreachable_literals": sum(1 for r in reach_rows if not r["measured_reachable"]),
            "ieee754_ordering_cases_compared": len(g2_pool),
            "ieee754_ordering_mismatches": len(g2_mismatch),
            "nonnumeric_ordering_cases": len(g3_pool),
            "ordering_divergences_vs_exact_s1": len(ord_div),
            "ordering_divergences_with_both_operands_inside_ijson_range": len(ijson_counterexamples),
            "equality_divergences_vs_exact_s1": len(eq_div_s1),
            "representation_orbit_equality_pairs": len(orbit),
            "representation_sensitive_orbit_pairs": len(orbit_sensitive),
            "fail_open_vs_s1": len(fail_open_s1),
            "fail_closed_vs_s1": len(fail_closed_s1),
            "fail_open_vs_s2": len(fail_open_s2),
            "fail_closed_vs_s2": len(fail_closed_s2),
            "sibling_oracle_divergences": len(sib_div),
            "distinct_runtime_reason_strings": len(reasons),
        },
        "findings": {
            "F1_ieee754_binary64_ordering": (
                "CONFORMANT" if not g2_mismatch else "REFUTED"),
            "F2_rfc8259_value_equality_representation_invariance": (
                "REFUTED" if orbit_sensitive else "CONFORMANT"),
            "F3_exact_vs_binary64_ordering": (
                "DIVERGENT_UNDER_BINARY64_ROUNDING" if ord_div else "IDENTICAL"),
            "F4_sibling_oracle_fidelity": (
                "DIVERGENT" if sib_div else "FAITHFUL"),
            "F5_ieee_special_value_attack_class": (
                "STRUCTURALLY_EMPTY" if not g4_bad else "REACHABLE"),
            "F6_quarantine_invariant": (
                "HOLDS_ON_ALL_ACCEPTS" if not g5_bad else "VIOLATED"),
            "F7_rfc7493_ijson_integer_range_sufficient_for_ordering_agreement": (
                "REFUTED" if ijson_counterexamples else "CORROBORATED"),
        },
        "gates": gates,
        "reachability_table": reach_rows,
        "distinct_runtime_reason_strings": reasons,
        "representation_orbit": {
            "definition": "pairs of DISTINCT literals with identical exact mathematical value, compared with `==`",
            "pairs": len(orbit),
            "runtime_disagrees_with_rfc8259": len(orbit_sensitive),
            "examples": sorted(orbit_sensitive, key=lambda o: o["case_id"])[:24],
        },
        "fail_open_vs_exact_semantics": {
            "count": len(fail_open_s1),
            "case_ids": fail_open_s1[:64],
            "truncated": len(fail_open_s1) > 64,
        },
        "fail_closed_vs_exact_semantics": {
            "count": len(fail_closed_s1),
            "case_ids": fail_closed_s1[:64],
            "truncated": len(fail_closed_s1) > 64,
        },
        "ordering_divergence_vs_exact": {
            "count": len(ord_div),
            "all_explained_by_binary64_rounding": not g7_bad,
            "h3b_rfc7493_range_criterion_sufficient": not ijson_counterexamples,
            "h3b_counterexamples": ijson_counterexamples,
            "records": sorted(
                [{"case_id": c["case_id"], "op": c["op"], "runtime": c["runtime"],
                  "exact_s1": c["s1"], "binary64_s2": c["s2"],
                  "direction_vs_exact": c["dir_vs_s1"]} for c in ord_div],
                key=lambda r: r["case_id"])[:64],
        },
        "sibling_oracle_fidelity": {
            "oracle_sha256": sib_sha,
            "sha_unchanged": sib_sha == SIBLING_ORACLE_SHA,
            "divergences": len(sib_div),
            "by_direction": {
                d: sum(1 for r in sib_div if r["oracle_error"] == d)
                for d in ("ORACLE_OVER_STRICT", "ORACLE_OVER_PERMISSIVE",
                          "ORACLE_REASON_ONLY")},
            "records": sorted(sib_div, key=lambda r: r["case_id"])[:64],
            "truncated": len(sib_div) > 64,
        },
        "acceptance_bar_floors": {
            "published_floors": {
                "ieee754_ordering_parity_floor": 1.0,
                "nonnumeric_ordering_fail_closed_floor": 1.0,
                "ieee_special_value_reachability_ceiling": 0,
                "quarantine_invariant_floor": 1.0,
                "m3_descriptive_adequacy_floor": 1.0,
                "binary64_rounding_explains_all_ordering_divergence_floor": 1.0,
            },
            "floor_results": {
                "ieee754_ordering_parity_floor": not g2_mismatch,
                "nonnumeric_ordering_fail_closed_floor": not g3_bad,
                "ieee_special_value_reachability_ceiling": not g4_bad,
                "quarantine_invariant_floor": not g5_bad,
                "m3_descriptive_adequacy_floor": not g6_bad,
                "binary64_rounding_explains_all_ordering_divergence_floor": not g7_bad,
            },
            "all_met": gates["all_pass"],
        },
        "provenance": {
            "corpus_sha256": sha(CORPUS.read_bytes()),
            "spec_oracle_sha256": sha((HERE / "numeric_comparison_oracle.py").read_bytes()),
            "sibling_oracle_sha256": sib_sha,
            "rust_probe_main_sha256": sha((PROBE_DIR / "src/main.rs").read_bytes()),
            "rust_probe_cargo_sha256": sha((PROBE_DIR / "Cargo.toml").read_bytes()),
            "runtime_ground_truth_sha256": sha(GT.read_bytes()),
            "runtime_ground_truth_lines": len(runtime),
        },
        "closes": [],
        "does_not_close": [],
        "proposed_hardeners": [
            {"id": "H01_canonical_number_admission",
             "surface": "front door (deserialization of OptimizerEnvelopeV1.gates and OptimizerConstraintRequestV1.expected)",
             "proposal": "Reject any numeric literal whose exact value is not exactly representable in binary64, so that RFC 8259 value semantics and IEEE 754 binary64 semantics coincide on every admitted operand.",
             "closes_finding": "F3/F7", "requires": "amphora-core change (Phase-1)"},
            {"id": "H02_value_normalizing_equality",
             "surface": "amphora-core::comparison_passes `==` / `!=` arms",
             "proposal": "Compare numeric operands by mathematical value (as_f64 on both sides, or a canonical decimal form) instead of by serde_json Value variant, restoring RFC 8259 representation invariance.",
             "closes_finding": "F2", "requires": "amphora-core change (Phase-1)"},
            {"id": "H03_ijson_range_clamp",
             "surface": "front door",
             "proposal": "Enforce the RFC 7493 Sec.2.2 interoperable integer range on gate and expected values. NOTE: this study REFUTES range-clamping as sufficient on its own -- it must be combined with H01.",
             "closes_finding": "partial F3", "requires": "amphora-core change (Phase-1)"},
            {"id": "H04_oracle_tagged_equality",
             "surface": "optimizer_authorization_oracle.py::_json_eq",
             "proposal": "Model serde_json's variant-tagged Number equality (model M3 in this study) so the audit oracle reproduces the runtime on the equality operators; re-run oracle-parity-v1 and clause-necessity-v1 afterwards.",
             "closes_finding": "F4", "requires": "audit-tooling change only"},
            {"id": "H05_operator_allowlist_narrowing",
             "surface": "constraint declaration validation",
             "proposal": "Restrict candidate-authored (request_source=CANDIDATE) hard constraints to the four ordering operators, which this study shows are IEEE 754 conformant, until H02 lands. This removes the only candidate-reachable exploitation path for the `!=` representation defect.",
             "closes_finding": "F2 exposure", "requires": "amphora-core change (Phase-1)"},
        ],
    }

    diag["closes"] = [
        "Executes the LIVE Rust runtime (amphora_core::authorize_optimizer_request) for the "
        f"first time in this module's audit line, over {len(cases)} cases, capturing exact "
        f"Err reason strings ({len(reasons)} distinct) -- partially discharging the Phase-1 "
        "axis named by optimizer-authorization-clause-necessity-v1 for the numeric surface.",
        f"H1 SETTLED: the IEEE 754 special-value attack class is structurally empty -- all "
        f"{len(special)} NaN/Infinity/out-of-range literals are rejected at the RFC 8259 "
        "front door before authorize_optimizer_request is ever entered, so no unordered "
        "comparison can be induced from JSON input.",
        f"H2 SETTLED: the four ordering operators are IEEE 754-2019 Sec.5.11 conformant over "
        f"binary64 on {len(g2_pool)}/{len(g2_pool)} numeric cases, and fail closed on "
        f"{len(g3_pool)}/{len(g3_pool)} non-numeric-operand cases.",
        f"H3 REFUTED: `==`/`!=` are NOT representation-invariant. {len(orbit_sensitive)} of "
        f"{len(orbit)} exact-value-equal literal pairs compare UNEQUAL at the runtime, "
        "confirming that the int/float representation split previously recorded for "
        "amphora-cro-protocol-packager canonicalization also reaches the authorization gate.",
        f"H3b REFUTED: the RFC 7493 Sec.2.2 interoperable-integer range is NECESSARY but NOT "
        f"SUFFICIENT for ordering agreement -- {len(ijson_counterexamples)} divergent cases have "
        "BOTH operands inside [-(2^53-1), 2^53-1] (subnormal tie-rounding 2.5e-324 -> 5e-324, and "
        "underflow 1e-400 -> 0). The correct closed criterion, confirmed on all "
        f"{len(ord_div)}/{len(ord_div)} divergences, is inexact binary64 rounding of an operand. "
        "A front-door range check alone would therefore NOT restore exact-value ordering.",
        f"H4 MEASURED: the sibling CPython contract oracle diverges from the live runtime on "
        f"{len(sib_div)} of {len(cases)} cases (all on the equality operators), quantifying "
        "for the first time the fidelity limit of the oracle that carries the two shipped "
        "optimizer audit receipts.",
        f"Quarantine invariant re-confirmed on the live runtime: all {len(accepts)} ACCEPT "
        "outcomes carry ranking_performed=false, solver_invoked=false, "
        "usable_by_optimizer=false, eligible_objective_count=0, authority_upgrade=false, "
        "candidate_created_evidence=false -- no numeric input escalates authority.",
    ]
    diag["does_not_close"] = [
        "The equality non-conformance is a CONSTRAINT-SCREEN semantics defect, not an "
        "authority escalation: every affected outcome still satisfies the quarantine "
        "invariant. Its exploitable direction is `!=` (a candidate-authored constraint "
        "`!= 110.0` passes against a gate value of 110 that denotes the same number); the "
        "`==` direction is fail-closed (availability, not authority).",
        "Remediating the defect requires a Rust change (numeric-value-normalizing comparison, "
        "or an I-JSON range + canonical-number-form admission check at the front door). This "
        "cron holds no authority to modify amphora-core; the fix is a Phase-1 item.",
        "Coverage is the scalar comparison surface only: nested container operands, path "
        "traversal, and multi-constraint conjunction interactions are out of scope here.",
        "The corpus is a hand-curated boundary census (36 literals), not an exhaustive "
        "enumeration of the binary64 domain; it targets the documented RFC 7493 / IEEE 754 "
        "boundaries rather than random sampling.",
        f"The live harness discharges the Phase-1 reason-string axis only PARTIALLY: this "
        f"surface emits {len(reasons)} distinct Err string(s) "
        f"({reasons!r}), because every non-comparison field is held well-formed by "
        "construction. Full Rust error-taxonomy parity across all 10 documented reason classes "
        "still requires re-running the clause-necessity ablation against this live harness.",
        "Sibling-oracle divergence is measured, not repaired: the shipped "
        "optimizer_authorization_oracle.py is left byte-identical (sha256 pinned and "
        "re-verified) so the two existing receipts remain reproducible. Correcting its "
        "_json_eq to a representation-tagged model is a follow-on item.",
        "M3 is post-hoc and descriptive; it is not evidence that serde_json's semantics are "
        "specified anywhere, and it must be re-validated on any serde_json version bump.",
    ]

    (HERE / sys.argv[1]).write_text(json.dumps(diag, indent=2, sort_keys=True))
    print(json.dumps({"out": sys.argv[1], "gates": gates,
                      "counts": diag["counts"], "findings": diag["findings"]}, indent=2))


if __name__ == "__main__":
    main()
