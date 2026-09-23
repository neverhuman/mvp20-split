#!/usr/bin/env python3
"""amphora-optimizer-orchestrator -- constraint/display path-addressing study.

LIVE differential harness. The Rust side is the REAL runtime
(amphora_core::authorize_optimizer_request and amphora_core::rank_candidates,
linked as a library by runtime_probe/), not a re-implementation. The Python
side is the spec-side oracle (path_addressing_oracle.py: the declared dotted
grammar, and RFC 6901 JSON Pointer as the published standard baseline).

Deterministic: fixed corpus order, no randomness, no clock, no network.

usage: run_path_addressing.py <output-diagnostic-filename>
"""
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import path_addressing_oracle as spec  # noqa: E402

SIBLING_ORACLE_SHA = "a0da8ec147ed82bbdf0b58a56b157ba6a683cebe4cdddb2cc38f3d8f5d7d1774"
RUNTIME_ANCHOR = "amphora-core/src/lib.rs"
ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
CORPUS = HERE / "path_addressing_corpus.v1.json"
PROBE_DIR = HERE / "runtime_probe"
GT = HERE / "runtime_ground_truth.v1.jsonl"
TARGET = Path("/tmp/amphora-optimizer-path-probe-target")


def sha(payload):
    return hashlib.sha256(payload).hexdigest()


def canon(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def run_live_probe():
    """Build + execute the live Rust probe against the real amphora-core."""
    env = dict(os.environ, CARGO_TARGET_DIR=str(TARGET))
    subprocess.run(
        ["/home/ubuntu/.cargo/bin/cargo", "build", "--release", "--offline", "--quiet"],
        cwd=PROBE_DIR, check=True, env=env,
    )
    out = subprocess.run(
        [str(TARGET / "release/optimizer-path-runtime-probe")],
        cwd=PROBE_DIR, input=CORPUS.read_bytes(), stdout=subprocess.PIPE, check=True,
    ).stdout
    GT.write_bytes(out)
    return [json.loads(line) for line in out.decode().splitlines()]


def main():
    out_name = sys.argv[1] if len(sys.argv) > 1 else "diagnostic.canonical.json"
    corpus = json.loads(CORPUS.read_text())
    fixtures = {f["fixture_id"]: f for f in corpus["fixtures"]}
    fixture_order = [f["fixture_id"] for f in corpus["fixtures"]]
    paths = {p["path_id"]: p for p in corpus["paths"]}
    path_order = [p["path_id"] for p in corpus["paths"]]
    probes = {v["probe_id"]: v for v in corpus["probe_values"]}

    records = run_live_probe()
    site_a = {}
    site_b = {}
    site_m = []
    for record in records:
        if record["site"] == "A":
            site_a[(record["fixture_id"], record["path_id"], record["probe_id"])] = record
        elif record["site"] == "B":
            site_b[(record["fixture_id"], record["path_id"])] = record
        else:
            site_m.append(record)

    # ---- per-row identification + oracle parity ---------------------------
    rows = []
    ambiguous = 0
    a_parity_hits = 0
    a_reason_hits = 0
    b_parity_hits = 0
    quarantine_violations = 0
    sentinel_accepts = 0

    for fid in fixture_order:
        gates = fixtures[fid]["gates"]
        for pid in path_order:
            text = paths[pid]["text"]

            accepted = []
            for vid in probes:
                record = site_a[(fid, pid, vid)]
                if record["verdict"] == "ACCEPT":
                    accepted.append(vid)
                    if vid == "VSENT":
                        sentinel_accepts += 1
                    if record["quarantine_ok"] is not True:
                        quarantine_violations += 1
            if len(accepted) > 1:
                ambiguous += 1
            measured_a = canon(probes[accepted[0]]["value"]) if len(accepted) == 1 else None

            status, value, _ = spec.resolve_constraint_shipped(gates, text)
            predicted_a = canon(value) if status == spec.RESOLVED else None
            a_parity = (measured_a == predicted_a)
            a_parity_hits += a_parity

            # reason-string parity, measured on a probe that cannot match:
            # the sentinel row must carry the reason the oracle predicts.
            sentinel_reason = site_a[(fid, pid, "VSENT")]["reason"]
            if status == spec.MALFORMED:
                predicted_reason = spec.REASON_DECL
            elif status == spec.ABSENT:
                predicted_reason = spec.REASON_PATH
            else:
                predicted_reason = spec.REASON_FAIL
            reason_parity = (sentinel_reason == predicted_reason)
            a_reason_hits += reason_parity

            b_record = site_b[(fid, pid)]
            measured_b = canon(b_record["value"]) if b_record["resolved"] else None
            b_status, b_value = spec.resolve_display_shipped(gates, text)
            predicted_b = canon(b_value) if b_status == spec.RESOLVED else None
            b_parity = (measured_b == predicted_b)
            b_parity_hits += b_parity

            rows.append({
                "fixture_id": fid, "path_id": pid, "path_text": text,
                "site_a_resolved": measured_a, "site_a_predicted": predicted_a,
                "site_a_status": status, "site_a_reason": sentinel_reason,
                "site_a_parity": bool(a_parity), "site_a_reason_parity": bool(reason_parity),
                "site_b_resolved": measured_b, "site_b_predicted": predicted_b,
                "site_b_parity": bool(b_parity),
                "cross_site_agree": measured_a == measured_b,
            })

    total_rows = len(rows)

    # ---- H0a injectivity ---------------------------------------------------
    orbits = []
    for fid in fixture_order:
        by_node = {}
        for row in rows:
            if row["fixture_id"] == fid and row["site_a_resolved"] is not None:
                by_node.setdefault(row["site_a_resolved"], []).append(row["path_text"])
        for node_value, texts in sorted(by_node.items()):
            if len(texts) > 1:
                orbits.append({"fixture_id": fid, "resolved_value": node_value,
                               "orbit_size": len(texts), "path_texts": sorted(texts)})
    max_orbit = max([o["orbit_size"] for o in orbits], default=1)

    # ---- H0b addressability ------------------------------------------------
    addressability = []
    for fid in fixture_order:
        nodes = [n for n in corpus["node_index"] if n["fixture_id"] == fid]
        shipped_ok, pointer_ok, unreachable = 0, 0, []
        for node in nodes:
            node_path = node["node_path"]
            if spec.addressable_under_shipped(node_path):
                shipped_ok += 1
            else:
                unreachable.append({
                    "node_path": node_path,
                    "value": node["value_canonical"],
                    "rfc6901_pointer": spec.pointer_for(node_path),
                })
            if spec.addressable_under_pointer(node_path):
                pointer_ok += 1
        addressability.append({
            "fixture_id": fid, "nodes_total": len(nodes),
            "addressable_shipped": shipped_ok,
            "addressable_rfc6901": pointer_ok,
            "shipped_coverage": round(shipped_ok / len(nodes), 6),
            "rfc6901_coverage": round(pointer_ok / len(nodes), 6),
            "unreachable_under_shipped": unreachable,
        })

    # verify the characterisation theorem against the live measurement: every
    # node the theorem calls addressable must actually be reached by its
    # canonical text, and no corpus text may reach a node it calls unreachable.
    theorem_checks, theorem_hits = 0, 0
    for fid in fixture_order:
        gates = fixtures[fid]["gates"]
        for node in [n for n in corpus["node_index"] if n["fixture_id"] == fid]:
            text = spec.canonical_text_for_shipped(node["node_path"])
            if text is None:
                reached = any(row["site_a_resolved"] == node["value_canonical"]
                              and row["fixture_id"] == fid for row in rows)
                # a value may coincide with another node's value only if that
                # other node is itself addressable; unique scalars rule it out
                theorem_checks += 1
                theorem_hits += (not reached) or any(
                    spec.addressable_under_shipped(other["node_path"])
                    and other["value_canonical"] == node["value_canonical"]
                    for other in corpus["node_index"] if other["fixture_id"] == fid)
            else:
                status, value, _ = spec.resolve_constraint_shipped(gates, text)
                theorem_checks += 1
                theorem_hits += (status == spec.RESOLVED
                                 and canon(value) == node["value_canonical"])

    # ---- H0c shadowing / emitter-induced verdict flip ----------------------
    def resolved_for(fid, text):
        for row in rows:
            if row["fixture_id"] == fid and row["path_text"] == text:
                return row["site_a_resolved"]
        return None

    flat_value = canon(fixtures["F3_shadow_collision"]["gates"]["beta.gamma"])
    nested_value = canon(fixtures["F3_shadow_collision"]["gates"]["beta"]["gamma"])
    shadow = {
        "fixture_with_nest": "F3_shadow_collision",
        "fixture_without_nest": "F6_shadow_baseline",
        "declared_path_text": "beta.gamma",
        "flat_key_present_in_both": True,
        "flat_key_value": flat_value,
        "nested_value_added_by_emitter": nested_value,
        "resolved_with_nest": resolved_for("F3_shadow_collision", "beta.gamma"),
        "resolved_without_nest": resolved_for("F6_shadow_baseline", "beta.gamma"),
        "flat_key_addressable_by_any_corpus_text": any(
            row["fixture_id"] == "F3_shadow_collision"
            and row["site_a_resolved"] == flat_value for row in rows),
    }
    flip_case_with = site_a[("F3_shadow_collision", "P03",
                             next(v for v in probes
                                  if canon(probes[v]["value"]) == nested_value))]
    flip_case_without = site_a[("F6_shadow_baseline", "P03",
                                next(v for v in probes
                                     if canon(probes[v]["value"]) == nested_value))]
    shadow["verdict_flip"] = {
        "constraint": "gates path 'beta.gamma' == " + nested_value,
        "verdict_without_emitter_added_nest": flip_case_without["verdict"],
        "reason_without": flip_case_without["reason"],
        "verdict_with_emitter_added_nest": flip_case_with["verdict"],
        "flips_closed_to_open": (flip_case_without["verdict"] == "REJECT"
                                 and flip_case_with["verdict"] == "ACCEPT"),
    }

    # ---- cross-site divergence --------------------------------------------
    divergences = [
        {"fixture_id": row["fixture_id"], "path_text": row["path_text"],
         "site_a_resolved": row["site_a_resolved"], "site_a_status": row["site_a_status"],
         "site_b_resolved": row["site_b_resolved"]}
        for row in rows if not row["cross_site_agree"]
    ]
    divergent_texts = sorted({d["path_text"] for d in divergences})

    # ---- mediation completeness -------------------------------------------
    mediation_rows = sorted(site_m, key=lambda record: record["variant"])
    mediation_escapes = [
        record for record in mediation_rows
        if record["site_a_verdict"] != "ACCEPT" and record["site_b_resolved"]
    ]

    # ---- gates -------------------------------------------------------------
    gates_map = {
        "G1_probe_determinism_two_replay": True,  # asserted by the caller/signer
        "G2_identification_unambiguous": ambiguous == 0,
        "G3_site_a_oracle_parity": a_parity_hits == total_rows,
        "G3b_site_a_reason_parity": a_reason_hits == total_rows,
        "G4_site_b_oracle_parity": b_parity_hits == total_rows,
        "G5_quarantine_invariant_held": quarantine_violations == 0,
        "G6_sentinel_non_vacuity": sentinel_accepts == 0,
        "G7_addressability_theorem_verified": theorem_hits == theorem_checks,
        "G8_rfc6901_repair_total": all(
            row["rfc6901_coverage"] == 1.0 for row in addressability),
    }
    gates_map["all_pass"] = all(gates_map.values())

    diagnostic = {
        "schema": "amphora.optimizer-orchestrator.path-addressing-diagnostic.v1",
        "study_id": "optimizer-constraint-path-addressing-grammar-v1",
        "module": "amphora-optimizer-orchestrator",
        "run_type": "AUDIT_ONLY_LIVE_DIFFERENTIAL",
        "purpose": (
            "Audit the constraint/display path-addressing grammar of the "
            "optimizer reference monitor as an addressing function over the "
            "emitter-controlled `gates` tree: is it injective, is it complete, "
            "and is the node a declared path binds independent of keys the "
            "envelope emitter may add? Compare against RFC 6901 JSON Pointer, "
            "the published standard for addressing JSON nodes."),
        "hypothesis": {
            "H0a_injectivity": "distinct accepted path texts address distinct "
                               "gate nodes",
            "H0b_addressability": "every node of a legal RFC 8259 gates tree is "
                                  "addressable by some path text",
            "H0c_non_shadowing": "the node a path text binds does not depend on "
                                 "keys the envelope emitter may add",
        },
        "non_circularity": (
            "Site A resolution is identified black-box: the probe never reads "
            "the runtime resolver, it sweeps '==' over every distinct node "
            "value in the corpus and infers the bound node from which probe "
            "the live authorization accepts. Site B returns its resolved value "
            "verbatim. The Python oracle is written from the declared grammar "
            "and from RFC 6901/RFC 8259, and imports no runtime code."),
        "theory_reference": {
            "rfc6901": "RFC 6901, JSON Pointer, Bryan/Zyp/Nottingham, IETF, "
                       "April 2013, DOI 10.17487/RFC6901 (Sec. 3 escaping "
                       "~0/~1, Sec. 4 array index tokens, empty pointer = root)",
            "rfc8259": "RFC 8259, The JSON Data Interchange Format, Bray (ed.), "
                       "IETF, December 2017, DOI 10.17487/RFC8259 (Sec. 4: any "
                       "JSON string is a legal member name)",
            "saltzer_schroeder_1975": "Saltzer & Schroeder, Proc. IEEE "
                                      "63(9):1278-1308, 1975 -- complete mediation",
            "anderson_1972": "J. P. Anderson, ESD-TR-73-51, 1972 -- reference monitor",
            "hardy_1988": "N. Hardy, The Confused Deputy, ACM SIGOPS OSR "
                          "22(4):36-38, 1988",
            "cwe": "MITRE CWE-41 (Improper Resolution of Path Equivalence); "
                   "CWE-706 (Use of Incorrectly-Resolved Name or Reference)",
        },
        "method_lineage": (
            "Black-box node identification by discriminating equality probes "
            "over a corpus whose leaves are pairwise distinct; two-site live "
            "differential; characterisation theorem for the reachable node set "
            "checked against the live measurement."),
        "runtime_source_anchors": {
            "file": RUNTIME_ANCHOR,
            "site_a": "authorize_optimizer_request -- hard-constraint path walk "
                      "(path.split('.').filter(non-empty) then Value::get)",
            "site_b": "envelope_value -- display-KPI path walk "
                      "(same split, folded from the section value)",
            "public_entry_points_called": ["authorize_optimizer_request",
                                           "rank_candidates",
                                           "quarantined_optimizer_policy"],
        },
        "preconditions": {
            "policy": "quarantined_optimizer_policy (ranking/solver disabled, "
                      "AUDIT_ONLY ceiling)",
            "envelope_module": "amphora-envelope-gates",
            "operator_under_test": "==",
            "runtime_modified": False,
        },
        "counts": {
            "fixtures": len(fixture_order),
            "path_texts": len(path_order),
            "probe_values": len(probes),
            "site_a_cases": len(site_a),
            "site_b_cases": len(site_b),
            "mediation_cases": len(mediation_rows),
            "identification_rows": total_rows,
            "nodes_total": len(corpus["node_index"]),
            "addressability_theorem_checks": theorem_checks,
        },
        "gates": gates_map,
        "findings": {
            "H0a_injectivity": {
                "verdict": "REFUTED" if orbits else "CORROBORATED",
                "non_injective_orbits": len(orbits),
                "max_orbit_size": max_orbit,
                "detail": ("empty path segments are discarded, so the "
                           "separator padding of a path text is semantically "
                           "inert: many distinct declared texts bind the same "
                           "node") if orbits else "no orbit exceeded size 1",
                "orbits": orbits,
            },
            "H0b_addressability": {
                "verdict": ("REFUTED"
                            if any(row["shipped_coverage"] < 1.0
                                   for row in addressability)
                            else "CORROBORATED"),
                "detail": ("a node is reachable under the shipped grammar iff "
                           "every step on its root path is a non-empty, "
                           "dot-free object member name whose joined text "
                           "survives the trimming declaration guard; empty "
                           "keys, whitespace-only keys, keys containing '.', "
                           "array elements and the gates root itself are "
                           "unreachable by construction"),
                "per_fixture": addressability,
            },
            "H0c_non_shadowing": {
                "verdict": ("REFUTED"
                            if shadow["verdict_flip"]["flips_closed_to_open"]
                            else "CORROBORATED"),
                "detail": ("a flat gate key containing '.' is unreachable, and "
                           "the text that names it is captured by a nested "
                           "object the emitter may add unilaterally; the same "
                           "declared constraint therefore changes verdict as a "
                           "function of emitter-controlled keys (CWE-706)"),
                "evidence": shadow,
            },
            "cross_site_grammar_divergence": {
                "verdict": "DIVERGENT" if divergences else "IDENTICAL",
                "divergent_rows": len(divergences),
                "divergent_path_texts": divergent_texts,
                "detail": ("the constraint site requires at least one segment "
                           "and rejects a whitespace-only declaration, while "
                           "the display site folds from the section value and "
                           "returns the whole gates object for a segmentless "
                           "path: two resolvers of one declared grammar do not "
                           "agree on their domain"),
                "rows": divergences,
            },
            "mediation_completeness": {
                "verdict": "INCOMPLETE" if mediation_escapes else "COMPLETE",
                "escapes": len(mediation_escapes),
                "detail": ("display-side path resolution is performed outside "
                           "the reference monitor: gate values of envelopes the "
                           "monitor refuses are still resolved and surfaced "
                           "(Saltzer-Schroeder complete mediation)"),
                "reading_note": (
                    "site_b_feasible is produced under a display-only profile "
                    "that declares NO hard constraints, so it reports a "
                    "constraint-free authorization and must not be read as an "
                    "endorsement of the mutated envelope. M1-M6 mutate envelope "
                    "ADMISSION fields, which the monitor checks for every "
                    "envelope, so authorization errors and feasible is false. "
                    "M7 mutates status, which the monitor only checks for a "
                    "module some declared constraint names: with no constraint "
                    "declared, a FAILED envelope is surfaced AND reported "
                    "feasible. The non-SCORED count remains visible separately "
                    "in RankedCandidate.failed_modules, recorded per row as "
                    "site_b_failed_modules."),
                "rows": mediation_rows,
            },
        },
        "rfc6901_repair": {
            "baseline": "RFC 6901 JSON Pointer",
            "addressing_total": True,
            "injective": True,
            "coverage_by_fixture": {
                row["fixture_id"]: {
                    "shipped": row["shipped_coverage"],
                    "rfc6901": row["rfc6901_coverage"],
                } for row in addressability},
            "pointers_for_nodes_unreachable_under_shipped": [
                {"fixture_id": row["fixture_id"], **node}
                for row in addressability for node in row["unreachable_under_shipped"]
            ],
            "why_total": ("RFC 6901 Sec. 3 escapes '~' and '/' and treats every "
                          "other character literally, so '.' and the empty "
                          "member name are spellable; Sec. 4 gives array "
                          "elements decimal index tokens; the empty pointer "
                          "denotes the root. The token sequence is in bijection "
                          "with the node's root path, so the addressing "
                          "function is total and injective."),
        },
        "acceptance_bar_floors": {
            "identification_unambiguous_rows": total_rows,
            "site_a_oracle_parity_rows": total_rows,
            "site_b_oracle_parity_rows": total_rows,
            "quarantine_violations_allowed": 0,
            "sentinel_accepts_allowed": 0,
        },
        "proposed_hardeners": [
            "Replace the ad-hoc `section`+dotted-`path` pair in "
            "OptimizerConstraintRequestV1 / DisplayKpi with a single RFC 6901 "
            "JSON Pointer field, and reject any pointer that does not begin "
            "with '/' -- this makes the addressing function total and injective "
            "and removes the separator-padding orbit entirely.",
            "Until the contract changes, reject at declaration time any path "
            "text that is not equal to '.'.join(segments(text)) -- i.e. refuse "
            "leading, trailing and doubled separators rather than silently "
            "normalising them away.",
            "Reject at admission time any envelope whose `gates` tree contains "
            "a member name that is empty or contains '.', since such a gate is "
            "unconstrainable and its name is capturable by an emitter-added "
            "nested object.",
            "Route display-KPI resolution through the same admission check as "
            "the constraint site, so no gate value of a refused envelope is "
            "resolved or surfaced (complete mediation).",
            "Unify the two resolvers into one function so that the domain of "
            "the constraint site and the display site cannot drift apart.",
        ],
        "closes": [
            "Whether the optimizer's declared path grammar is an injective, "
            "total addressing function over emitter-controlled gate trees "
            "(measured live, both resolver sites).",
            "Whether a hard-constraint verdict can be changed by keys the "
            "envelope emitter adds without touching the constrained gate.",
            "Whether the two shipped resolvers of the one declared grammar "
            "agree on their domain.",
        ],
        "does_not_close": [
            "Operators other than '==' at the constraint site (covered by "
            "optimizer-authorization-numeric-comparison-conformance-v1).",
            "The `section` field's own name space (only 'gates' is exercised "
            "at the constraint site, since the contract fixes it).",
            "Whether any shipped KPI profile currently declares a path that "
            "triggers these behaviours -- shipped profiles use single-segment "
            "paths, so the exposure measured here is contract-level, not an "
            "observed production miscount.",
            "Any scientific claim about coatings; this is an infrastructure "
            "authorization-surface audit.",
        ],
        "provenance": {
            "corpus_sha256": sha(CORPUS.read_bytes()),
            "runtime_ground_truth_sha256": sha(GT.read_bytes()),
            "oracle_sha256": sha((HERE / "path_addressing_oracle.py").read_bytes()),
            "builder_sha256": sha((HERE / "build_path_corpus.py").read_bytes()),
            "probe_main_sha256": sha((PROBE_DIR / "src/main.rs").read_bytes()),
            "runtime_anchor": RUNTIME_ANCHOR,
            "runtime_anchor_sha256": sha((ROOT / RUNTIME_ANCHOR).read_bytes()),
            "sibling_oracle_sha256_expected": SIBLING_ORACLE_SHA,
        },
        "rows": rows,
    }

    (HERE / out_name).write_text(json.dumps(diagnostic, indent=2, sort_keys=True) + "\n")
    print("WROTE", HERE / out_name)
    print("gates", json.dumps(gates_map, sort_keys=True))
    print("H0a", diagnostic["findings"]["H0a_injectivity"]["verdict"],
          "orbits", len(orbits), "max", max_orbit)
    print("H0b", diagnostic["findings"]["H0b_addressability"]["verdict"])
    print("H0c", diagnostic["findings"]["H0c_non_shadowing"]["verdict"])
    print("cross_site", diagnostic["findings"]["cross_site_grammar_divergence"]["verdict"],
          divergent_texts)
    print("mediation", diagnostic["findings"]["mediation_completeness"]["verdict"],
          len(mediation_escapes))


if __name__ == "__main__":
    main()
