#!/usr/bin/env python3
"""amphora-source-ledger query-traceability-referential-integrity-v1 oracle.

AUDIT_ONLY. Independently re-parses the raw source ledger JSON
(reference/mvp20/data/source_records.json) and tests whether the ledger's
provenance graph (record -> query -> declared source target) satisfies the
classical relational-integrity constraints:

  - entity integrity (Codd 1970): primary keys unique and non-empty for
    records, queries, and declared targets;
  - referential integrity (Date 1981): every foreign-key reference
    (record.query_ids[i]) resolves to an existing query tuple;
  - traceability completeness (H0a): every record carries >=1 query_id;
  - load-bearing completeness (H0b): every ledger query is referenced by
    >=1 record;
  - target-linkage determinability (H0c): every declared source_target is
    mechanically resolvable to >=1 query under a stated syntactic rule.

Deterministic: pure set/count arithmetic over sorted iteration; no RNG, no
wall-clock reads. Two-replay byte-stability is enforced by the signer.

Usage: python3 source_ledger_query_traceability_oracle.py <out_path>
"""
import copy
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
LEDGER = ROOT / "amphora-source-ledger/reference/mvp20/data/source_records.json"

# Pinned anchors. The ledger byte hash is pinned at audit time; the registry
# size (162), query-ledger size (17) and target-list size (19) reproduce the
# "162-record registry" anchored in the previously signed
# dual-source-independence-common-cause-v1 receipt for this module.
PINNED_LEDGER_SHA256 = (
    "87174e555bdf31cd30d7d13da2dedb5cc6c14af33586fdd3981d97c0409da26c")
PINNED_N_RECORDS = 162
PINNED_N_QUERIES = 17
PINNED_N_TARGETS = 19

AUDIT_DATE = "2026-07-31"


def sha(b):
    return hashlib.sha256(b).hexdigest()


def norm(s):
    """Normalization for the syntactic target<->query linkage rule."""
    return " ".join(re.sub(r"[^a-z0-9]+", " ", s.lower()).split())


def analyze(ledger):
    """Pure integrity analysis of one ledger object. Returns a dict of
    measured integrity facts; no gate logic here."""
    records = ledger["records"]
    queries = ledger["source_query_ledger"]
    targets = ledger["source_targets"]

    record_ids = [r.get("id", "") for r in records]
    query_ids = [q.get("id", "") for q in queries]

    def dup(xs):
        seen, dups = set(), set()
        for x in xs:
            if x in seen:
                dups.add(x)
            seen.add(x)
        return sorted(dups)

    entity = {
        "record_id_duplicates": dup(record_ids),
        "query_id_duplicates": dup(query_ids),
        "target_duplicates": dup(targets),
        "empty_record_ids": sum(1 for x in record_ids if not x),
        "empty_query_ids": sum(1 for x in query_ids if not x),
        "empty_targets": sum(1 for x in targets if not x),
    }

    qid_set = set(query_ids)
    total_refs = 0
    dangling = []
    missing_field = []
    orphan_records = []
    referenced = set()
    for r in records:
        rid = r.get("id", "")
        if "query_ids" not in r:
            missing_field.append(rid)
            continue
        refs = r["query_ids"]
        total_refs += len(refs)
        for q in refs:
            if q not in qid_set:
                dangling.append({"record_id": rid, "query_id": q})
            else:
                referenced.add(q)
        if not refs:
            orphan_records.append({"record_id": rid, "kind": r.get("kind", "")})

    orphan_queries = sorted(qid_set - referenced)
    orphan_query_register = [
        {"query_id": q["id"], "target": q["target"]}
        for q in queries if q["id"] in orphan_queries]

    # Syntactic target<->query linkage: bidirectional normalized containment.
    # The ledger schema defines NO key linking source_targets to queries or
    # records, so this syntactic rule is the strongest mechanical linkage
    # available; its failures measure schema-level underdetermination.
    adjacency = []
    for t in targets:
        nt = norm(t)
        hits = sorted(
            q["id"] for q in queries
            if nt in norm(q["target"]) or norm(q["target"]) in nt)
        adjacency.append({"target": t, "matched_query_ids": hits})
    unmatched_targets = [a["target"] for a in adjacency
                         if not a["matched_query_ids"]]

    orphan_by_kind = {}
    for o in orphan_records:
        orphan_by_kind[o["kind"]] = orphan_by_kind.get(o["kind"], 0) + 1

    return {
        "n_records": len(records),
        "n_queries": len(queries),
        "n_targets": len(targets),
        "entity": entity,
        "total_query_refs": total_refs,
        "dangling_refs": dangling,
        "records_missing_query_ids_field": missing_field,
        "orphan_records": sorted(orphan_records, key=lambda o: o["record_id"]),
        "orphan_records_by_kind": orphan_by_kind,
        "orphan_queries": orphan_query_register,
        "target_query_adjacency": adjacency,
        "unmatched_targets": unmatched_targets,
        "query_ids_in_required_record_fields":
            "query_ids" in ledger.get("required_record_fields", []),
    }


def entity_ok(a):
    e = a["entity"]
    return (not e["record_id_duplicates"] and not e["query_id_duplicates"]
            and not e["target_duplicates"] and e["empty_record_ids"] == 0
            and e["empty_query_ids"] == 0 and e["empty_targets"] == 0)


def run_probes(ledger, base):
    """Eight structural mutants; each must flip the named integrity fact in
    the expected direction (fail-closed / kill test)."""
    probes = []

    def probe(name, mutate, killed_fn, expectation):
        m = copy.deepcopy(ledger)
        mutate(m)
        a = analyze(m)
        probes.append({
            "probe": name,
            "expectation": expectation,
            "killed": bool(killed_fn(a)),
        })

    probe("m1_dangling_query_ref",
          lambda m: m["records"][0]["query_ids"].append("Q-999"),
          lambda a: len(a["dangling_refs"]) == 1,
          "one dangling foreign-key reference detected")
    probe("m2_duplicate_record_id",
          lambda m: m["records"].__setitem__(
              1, {**m["records"][1], "id": m["records"][0]["id"]}),
          lambda a: len(a["entity"]["record_id_duplicates"]) == 1,
          "record primary-key duplicate detected")
    probe("m3_duplicate_query_id",
          lambda m: m["source_query_ledger"].append(
              dict(m["source_query_ledger"][0])),
          lambda a: len(a["entity"]["query_id_duplicates"]) == 1,
          "query primary-key duplicate detected")
    probe("m4_delete_referenced_query",
          lambda m: m["source_query_ledger"].__delitem__(
              [i for i, q in enumerate(m["source_query_ledger"])
               if q["id"] == "Q-016"][0]),
          lambda a: len(a["dangling_refs"]) == 32,
          "deleting Q-016 exposes its 32 references as dangling")
    probe("m5_blank_record_id",
          lambda m: m["records"][2].__setitem__("id", ""),
          lambda a: a["entity"]["empty_record_ids"] == 1,
          "empty record primary key detected")
    probe("m6_drop_query_ids_field",
          lambda m: m["records"][3].pop("query_ids"),
          lambda a: len(a["records_missing_query_ids_field"]) == 1,
          "required query_ids field removal detected")
    probe("m7_orphan_query_injection",
          lambda m: m["source_query_ledger"].append(
              {"id": "Q-099", "target": "injected orphan"}),
          lambda a: len(a["orphan_queries"]) ==
          len(base["orphan_queries"]) + 1,
          "injected never-referenced query counted as orphan")
    probe("m8_strand_query_by_record_removal",
          lambda m: m.__setitem__(
              "records",
              [r for r in m["records"] if "Q-004" not in r["query_ids"]]),
          lambda a: len(a["orphan_queries"]) ==
          len(base["orphan_queries"]) + 1,
          "removing both Q-004 referrers strands Q-004 as orphan")
    return probes


def main(out_path):
    raw = LEDGER.read_bytes()
    ledger_sha = sha(raw)
    ledger = json.loads(raw)
    base = analyze(ledger)
    probes = run_probes(ledger, base)

    anchors = {
        "ledger_sha256_matches_pin": ledger_sha == PINNED_LEDGER_SHA256,
        "n_records_matches_pin": base["n_records"] == PINNED_N_RECORDS,
        "n_queries_matches_pin": base["n_queries"] == PINNED_N_QUERIES,
        "n_targets_matches_pin": base["n_targets"] == PINNED_N_TARGETS,
    }
    n_orphan_records = len(base["orphan_records"])
    n_orphan_queries = len(base["orphan_queries"])
    n_matched_targets = sum(
        1 for a in base["target_query_adjacency"] if a["matched_query_ids"])

    h0a_holds = n_orphan_records == 0
    h0b_holds = n_orphan_queries == 0
    h0c_holds = len(base["unmatched_targets"]) == 0
    entity_holds = entity_ok(base)
    referential_holds = (len(base["dangling_refs"]) == 0
                         and not base["records_missing_query_ids_field"])
    probes_ok = all(p["killed"] for p in probes)

    counts = {
        "g0_anchors": len(anchors),
        "g0_anchors_matched": sum(anchors.values()),
        "g1_record_id_duplicates": len(base["entity"]["record_id_duplicates"]),
        "g1_query_id_duplicates": len(base["entity"]["query_id_duplicates"]),
        "g1_target_duplicates": len(base["entity"]["target_duplicates"]),
        "g1_empty_keys": (base["entity"]["empty_record_ids"]
                          + base["entity"]["empty_query_ids"]
                          + base["entity"]["empty_targets"]),
        "g2_total_foreign_key_refs": base["total_query_refs"],
        "g2_dangling_refs": len(base["dangling_refs"]),
        "g2_records_missing_query_ids_field":
            len(base["records_missing_query_ids_field"]),
        "g3_records": base["n_records"],
        "g3_query_orphan_records": n_orphan_records,
        "g4_queries": base["n_queries"],
        "g4_record_orphan_queries": n_orphan_queries,
        "g5_targets": base["n_targets"],
        "g5_targets_syntactically_matched": n_matched_targets,
        "g5_targets_unmatched": len(base["unmatched_targets"]),
        "g6_probes": len(probes),
        "g6_probes_killed": sum(1 for p in probes if p["killed"]),
    }
    derived_metrics = {
        "query_orphan_record_fraction": round(
            n_orphan_records / base["n_records"], 6),
        "record_orphan_query_fraction": round(
            n_orphan_queries / base["n_queries"], 6),
        "target_syntactic_resolvability_fraction": round(
            n_matched_targets / base["n_targets"], 6),
        "referential_integrity_violation_rate": round(
            len(base["dangling_refs"]) / base["total_query_refs"], 6),
    }
    gates = {
        "g0_anchors_reproduced": all(anchors.values()),
        "g6_probes_behaved_as_specified": probes_ok,
        "g_verdict_determinate": True,
        "all_pass": all(anchors.values()) and probes_ok,
    }
    derived_gates = {
        "entity_integrity_holds": entity_holds,
        "referential_integrity_holds": referential_holds,
        "h0a_record_query_traceability_holds": h0a_holds,
        "h0b_query_load_bearing_holds": h0b_holds,
        "h0c_target_linkage_determinable": h0c_holds,
        "target_key_defined_in_schema": False,
        "query_ids_listed_as_required_field":
            base["query_ids_in_required_record_fields"],
        "h0_refuted": not (h0a_holds and h0b_holds and h0c_holds),
    }

    diag = {
        "schema": ("amphora.source-ledger."
                   "query-traceability-referential-integrity-diagnostic.v1"),
        "study_id": "source-ledger-query-traceability-referential-integrity-v1",
        "module": "amphora-source-ledger",
        "audit_date": AUDIT_DATE,
        "authority": "AUDIT_ONLY",
        "run_type": "offline_relational_integrity_audit",
        "purpose": (
            "Test whether the 162-record source ledger's provenance graph "
            "(record -> query -> declared source target) is complete and "
            "referentially sound, i.e. whether every ledger record can be "
            "mechanically traced back to the search query that produced it "
            "and every declared acquisition target is mechanically served."),
        "hypothesis": (
            "H0 (implied by the ledger's own schema, which lists query_ids "
            "among required_record_fields and publishes source_targets as "
            "the acquisition contract): (H0a) every record carries >=1 "
            "query_id; (H0b) every query in source_query_ledger is "
            "referenced by >=1 record; (H0c) every declared source_target "
            "is mechanically resolvable to >=1 query."),
        "theory_reference": [
            {"name": "Codd 1970 (entity integrity, relational model)",
             "citation": ("E.F. Codd, 'A Relational Model of Data for Large "
                          "Shared Data Banks', Communications of the ACM "
                          "13(6):377-387, 1970"),
             "doi": "10.1145/362384.362685"},
            {"name": "Date 1981 (referential integrity)",
             "citation": ("C.J. Date, 'Referential Integrity', Proceedings "
                          "of the 7th International Conference on Very "
                          "Large Data Bases (VLDB), pp. 2-12, 1981")},
        ],
        "non_circularity": (
            "The oracle re-parses the raw ledger JSON bytes directly and "
            "implements Codd/Date integrity checks from scratch in CPython; "
            "it calls no module code and reads no module-derived report. "
            "Registry-size anchors (162 records) reproduce the figure "
            "pinned in the previously signed "
            "dual-source-independence-common-cause-v1 receipt; the ledger "
            "byte hash is pinned in this oracle's source, which is itself "
            "hash-bound into the receipt."),
        "preconditions": {
            "ledger_path": str(LEDGER.relative_to(ROOT)),
            "ledger_sha256": ledger_sha,
            "pinned_ledger_sha256": PINNED_LEDGER_SHA256,
        },
        "method_parameters": {
            "normalization_rule": ("lowercase; replace [^a-z0-9]+ with "
                                   "single space; strip"),
            "target_linkage_rule": ("bidirectional normalized substring "
                                    "containment between source_target and "
                                    "query.target free text (schema defines "
                                    "no key, so syntactic containment is "
                                    "the strongest mechanical linkage "
                                    "available)"),
            "probe_count": len(probes),
            "randomness": "none (pure set/count arithmetic)",
        },
        "counts": counts,
        "derived_metrics": derived_metrics,
        "gates": gates,
        "derived_gates": derived_gates,
        "evidence": {
            "anchors": anchors,
            "entity_integrity": base["entity"],
            "orphan_record_register": base["orphan_records"],
            "orphan_records_by_kind": base["orphan_records_by_kind"],
            "orphan_query_register": base["orphan_queries"],
            "target_query_adjacency": base["target_query_adjacency"],
            "unmatched_targets": base["unmatched_targets"],
            "probe_register": probes,
        },
        "closes": (
            "Establishes that the source ledger's key discipline is sound "
            "but its provenance graph is incomplete on all three "
            "completeness axes. Entity integrity (Codd 1970) HOLDS: 0 "
            "duplicate and 0 empty primary keys across 162 record ids, 17 "
            "query ids, and 19 target strings. Referential integrity (Date "
            "1981) HOLDS: 0/129 query_id foreign-key references dangle and "
            "no record omits the required query_ids field. H0 REFUTED on "
            "completeness: (H0a) 34/162 records (21.0%) carry an empty "
            "query_ids list and are therefore query-orphans with no "
            "mechanical acquisition provenance (17 authority, 8 supplier, "
            "5 patent, 4 literature); (H0b) 5/17 queries (Q-002, Q-003, "
            "Q-011, Q-012, Q-013) are referenced by zero records, so the "
            "work they represent is not load-bearing for any ledger entry; "
            "(H0c) the schema defines no key linking source_targets to "
            "queries or records, and the strongest syntactic rule "
            "(bidirectional normalized containment) resolves only 4/19 "
            "declared targets, so target coverage is emitter-asserted "
            "rather than machine-checkable. All 8 structural mutation "
            "probes (dangling ref, duplicate/blank keys, referenced-query "
            "deletion, required-field removal, orphan injection/stranding) "
            "were killed by the oracle."),
        "does_not_close": (
            "Does NOT establish that any orphan record's content is wrong "
            "or that its source is unreliable: 17/34 query-orphans are "
            "kind=authority anchors (e.g. SRC-QPL-24441, SRC-MIL-DTL-"
            "24441D) that were plausibly hand-entered rather than "
            "query-discovered; the finding is that the ledger cannot "
            "distinguish 'hand-entered by design' from 'provenance lost'. "
            "Does NOT establish that orphan queries were wasted effort, "
            "only that no record credits them. Does NOT evaluate URL "
            "liveness, license terms, or numeric content. Does NOT change "
            "the runtime's shipped verdicts, does NOT promote authority, "
            "does NOT flip scientific_readiness, and does NOT modify the "
            "portfolio receipts manifest (66 receipts / 11 modules)."),
        "phase1_exit_criterion_impact": (
            "A Phase-1 provenance claim over this ledger requires three "
            "schema repairs: (1) a provenance_class field on each record "
            "({query_derived, hand_entered_authority, ...}) so an empty "
            "query_ids list is either justified or a defect; (2) target "
            "ids plus a query.target_ids foreign key so target coverage "
            "becomes a checkable referential constraint instead of free "
            "text; (3) a disposition field on each query so "
            "never-referenced queries are either closed as unproductive or "
            "flagged as unharvested work."),
    }

    Path(out_path).write_text(json.dumps(diag, indent=2, sort_keys=True) + "\n")
    return diag


if __name__ == "__main__":
    d = main(sys.argv[1])
    print("study_id:", d["study_id"])
    print("gates:", json.dumps(d["gates"], sort_keys=True))
    print("counts:", json.dumps(d["counts"], sort_keys=True))
    print("derived_metrics:", json.dumps(d["derived_metrics"], sort_keys=True))
    print("derived_gates:", json.dumps(d["derived_gates"], sort_keys=True))
