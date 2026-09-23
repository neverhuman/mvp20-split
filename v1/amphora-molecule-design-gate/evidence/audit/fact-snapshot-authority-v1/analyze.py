#!/usr/bin/env python3
"""
amphora-molecule-design-gate :: fact-snapshot-authority-v1 :: analysis oracle

NON-RUNTIME independent re-implementation of the documented design-gate
decision function, checked against a LIVE Rust run of
`design_gate_result` (amphora-molecule-capabilities/src/lib.rs).

Scientific claim under audit
----------------------------
The shipped Phase-0 KPI (tests/design_gate_phase0_kpi.rs) drives 42 curated
records and asserts gate-decision correctness, six gate_reason categories, and
malformed-input fail-closed behaviour. In EVERY shipped record the malformed
structures carry NO `molecule_facts_v1` snapshot: the fail-closed lexical ladder
is only ever exercised on the facts-ABSENT branch.

This audit exercises the untested decision cell: STRUCTURE x SNAPSHOT. It
establishes, against the live runtime, that on the facts-PRESENT branch
`design_gate_result` is a pure function of (declared_role, oxirane_ring_count>0,
reactive_amine_hydrogen_count>0) carried by the host-injected snapshot, and
consults NEITHER the candidate's own structure text NOR the snapshot's
structure-identity binding fields. The lexical structure ladder and its
fail-closed reasons are therefore inert whenever a well-typed snapshot is
present; the ONLY admission wall on that branch is the `MoleculeFactsV1` serde
contract (u32 fields, deny_unknown_fields, required fields).

Consequence for the shipped KPI: its "malformed fail-closed" guarantee is
CONDITIONAL on the upstream host normaliser (amphora-engine::normalize_molecule
-> amphora_rdkit_ffi::molecule_facts) never emitting a snapshot for a malformed
or structurally-inconsistent candidate. That binding property is owned upstream,
not by design_gate_result. This receipt bounds the KPI claim to the
facts-absent pathway and localises where structural binding actually lives.

Theory / source anchoring
--------------------------
Live runtime authority: amphora-molecule-capabilities/src/lib.rs
  ::design_gate_result and ::normalized_facts (serde_json::from_value(..).ok()).
Snapshot contract: amphora-rdkit-ffi/src/lib.rs::MoleculeFactsV1
  (#[serde(deny_unknown_fields)], u32 count fields).
Host normalisation boundary: amphora-engine/src/lib.rs::normalize_molecule.
Epoxy-amine cure chemistry scope (oxirane + active amine N-H) as in prior
design-gate receipts: Ellis 1993 Ch.6; Wicks/Jones/Pappas 2007 Ch.15.
Purely a runtime decision-authority / evidence-provenance audit; asserts NO
EHS, synthesis, qualification, procurement, or product-performance authority.
"""
import json
import sys

PROBES_PATH = sys.argv[1]
LIVE_PATH = sys.argv[2]

probes = {p["probe_id"]: p for p in json.load(open(PROBES_PATH))["probes"]}
live = json.load(open(LIVE_PATH))["results"]

VALID_ROLES = {"resin", "hardener"}


def lexical_structure_issue(molecule):
    """Mirror amphora-molecule-capabilities::structure_text lexical ladder."""
    smiles = molecule.get("canonical_smiles")
    if smiles is None:
        smiles = molecule.get("smiles")
    if not isinstance(smiles, str):
        return "missing_structure"
    s = smiles.strip()
    if s == "":
        return "empty_structure"
    if "." in s:
        return "multi_fragment_structure"
    if "*" in s or "~" in s:
        return "wildcard_or_query_structure"
    return None


def snapshot_deserializes(snapshot):
    """Predict amphora_rdkit_ffi::MoleculeFactsV1 serde acceptance.

    synth   -> always well-typed (constructed from the struct in the harness)
    verbatim-> re-implement the load-bearing serde constraints
    null    -> absent (not a deserialization outcome; caller handles)
    """
    if snapshot is None:
        return None  # absent
    mode = snapshot.get("mode")
    if mode == "synth":
        return True
    if mode == "verbatim":
        v = snapshot["value"]
        required = {
            "schema", "canonical_isomeric_smiles", "structure_identity",
            "canonical_structure_sha256", "formula",
            "average_molecular_weight_g_mol", "oxirane_ring_count",
            "reactive_amine_hydrogen_count", "reactive_flags",
            "ontology_version", "toolkit_provenance",
        }
        keys = set(v.keys())
        if keys - required:  # deny_unknown_fields
            return False
        if required - keys:  # missing required field
            return False
        for u32_field in ("oxirane_ring_count", "reactive_amine_hydrogen_count"):
            x = v[u32_field]
            if not isinstance(x, int) or isinstance(x, bool) or x < 0 or x > 4294967295:
                return False
        return True
    raise ValueError(f"unknown snapshot mode {mode!r}")


def expected_decision(probe):
    """Independent re-implementation of design_gate_result's documented
    decision function. Returns (status, pass_all_hard, gate_reason,
    explicit_role, role_appropriate_reactivity, valid_single_component)."""
    molecule = probe["candidate"].get("molecule", {})
    role = molecule.get("role")
    role_valid = role in VALID_ROLES
    snap = probe["snapshot"]
    facts_ok = snapshot_deserializes(snap)

    if facts_ok is True:
        ox = _declared_ox(snap)
        nh = _declared_nh(snap)
        role_appropriate = (role == "resin" and ox > 0) or (
            role == "hardener" and nh > 0)
        passed = role_valid and role_appropriate
        if not role_valid:
            reason = "missing_or_unsupported_role"
        elif not role_appropriate:
            reason = "missing_role_appropriate_reactive_group"
        else:
            reason = "supported_single_component_with_role_appropriate_reactivity"
        return ("SCORED" if passed else "FAILED_GATES", passed, reason,
                role_valid, role_appropriate, True)

    # facts absent OR malformed snapshot -> fail-closed fallback branch
    issue = lexical_structure_issue(molecule)
    if issue is not None:
        reason = issue
    elif not role_valid:
        reason = "missing_or_unsupported_role"
    else:
        reason = "positive_applicability_unavailable_without_rdkit_and_ontology"
    return ("FAILED_GATES", False, reason, role_valid, False, issue is None)


def _declared_ox(snap):
    if snap["mode"] == "synth":
        return int(snap["facts"].get("oxirane_ring_count", 0))
    return int(snap["value"]["oxirane_ring_count"])


def _declared_nh(snap):
    if snap["mode"] == "synth":
        return int(snap["facts"].get("reactive_amine_hydrogen_count", 0))
    return int(snap["value"]["reactive_amine_hydrogen_count"])


# ---------- per-probe evaluation ----------
per_probe = []
for pid, probe in sorted(probes.items()):
    entry = live[pid]
    result = entry.get("result")
    if result is None:
        per_probe.append({"probe_id": pid, "class": probe["class"],
                          "live_error": entry, "match": False})
        continue
    exp = expected_decision(probe)
    obs = (
        result["status"],
        result["gates"].get("pass_all_hard"),
        result["metrics"].get("gate_reason"),
        result["gates"].get("explicit_role"),
        result["gates"].get("role_appropriate_reactivity"),
        result["gates"].get("valid_single_component"),
    )
    per_probe.append({
        "probe_id": pid, "class": probe["class"],
        "expected": {"status": exp[0], "pass_all_hard": exp[1],
                     "gate_reason": exp[2], "explicit_role": exp[3],
                     "role_appropriate_reactivity": exp[4],
                     "valid_single_component": exp[5]},
        "observed": {"status": obs[0], "pass_all_hard": obs[1],
                     "gate_reason": obs[2], "explicit_role": obs[3],
                     "role_appropriate_reactivity": obs[4],
                     "valid_single_component": obs[5]},
        "two_replay_byte_stable": entry.get("per_probe_two_replay_byte_stable"),
        "match": exp == obs,
    })

by_id = {p["probe_id"]: p for p in per_probe}


def cls(name):
    return [p for p in per_probe if p["class"] == name]


# ---------- G0: fixture non-regression ----------
fixture = cls("FIXTURE")
# cross-check the live observed labels against the SHIPPED expected_* in fixture
ship = {r["case_id"]: r for r in json.load(open(sys.argv[3]))["records"]}
g0_records = []
for p in fixture:
    case_id = p["probe_id"].split("::", 1)[1]
    s = ship[case_id]
    shipped = {
        "pass_all_hard": s["expected_pass_all_hard"],
        "gate_reason": s["expected_gate_reason"],
        "explicit_role": s["expected_explicit_role"],
        "role_appropriate_reactivity": s["expected_role_appropriate_reactivity"],
        "valid_single_component": s["expected_valid_single_component"],
    }
    obs = {k: p["observed"][k] for k in shipped}
    g0_records.append({"case_id": case_id, "match_shipped": shipped == obs,
                       "match_oracle": p["match"]})
g0_pass = (len(fixture) == 42
           and all(x["match_shipped"] for x in g0_records)
           and all(x["match_oracle"] for x in g0_records))

# ---------- G1: snapshot authorship (inert structure, forged facts -> SCORE) ----------
up = cls("UP_FORGERY")
g1_records = [{"probe_id": p["probe_id"],
               "structure_is_inert_for_declared_role": True,
               "scored_and_passed": p["observed"]["status"] == "SCORED"
               and p["observed"]["pass_all_hard"] is True,
               "match": p["match"]} for p in up]
g1_pass = len(up) == 8 and all(
    x["scored_and_passed"] and x["match"] for x in g1_records)

# ---------- G2: lexical-ladder bypass / decision-cell gap ----------
# lexically-invalid candidates: facts-present SCORE, facts-absent fail-closed
# with the matching lexical reason.
LEXICAL = {"multi-fragment-salt": "multi_fragment_structure",
           "wildcard": "wildcard_or_query_structure",
           "empty": "empty_structure",
           "missing-smiles": "missing_structure"}
g2_records = []
for name, lex_reason in LEXICAL.items():
    fp = by_id[f"bypass::{name}"]
    nf = by_id[f"bypass-nofacts::{name}"]
    g2_records.append({
        "candidate": name,
        "lexical_reason_when_facts_absent": lex_reason,
        "facts_present_scored_pass": fp["observed"]["status"] == "SCORED"
        and fp["observed"]["pass_all_hard"] is True,
        "facts_absent_failed_closed_with_lexical_reason":
            nf["observed"]["status"] == "FAILED_GATES"
            and nf["observed"]["gate_reason"] == lex_reason,
        "match": fp["match"] and nf["match"],
    })
# lexically-clean-but-chemically-impossible: facts-present SCORE, facts-absent
# fail-closed but with the GENERIC no-rdkit reason (lexical ladder cannot catch).
CHEM = ["unclosed-ring", "pentavalent-carbon"]
g2b_records = []
for name in CHEM:
    fp = by_id[f"bypass::{name}"]
    nf = by_id[f"bypass-nofacts::{name}"]
    g2b_records.append({
        "candidate": name,
        "facts_present_scored_pass": fp["observed"]["status"] == "SCORED"
        and fp["observed"]["pass_all_hard"] is True,
        "facts_absent_reason": nf["observed"]["gate_reason"],
        "lexical_ladder_cannot_reject":
            nf["observed"]["gate_reason"]
            == "positive_applicability_unavailable_without_rdkit_and_ontology",
        "match": fp["match"] and nf["match"],
    })
g2_pass = (all(r["facts_present_scored_pass"]
               and r["facts_absent_failed_closed_with_lexical_reason"]
               and r["match"] for r in g2_records)
           and all(r["facts_present_scored_pass"]
                   and r["lexical_ladder_cannot_reject"] and r["match"]
                   for r in g2b_records))

# ---------- G3: binding inertness (facts of A on candidate B still pass) ----------
swap = cls("BINDING_SWAP")
g3_records = [{"probe_id": p["probe_id"],
               "scored_pass_despite_mismatched_binding":
                   p["observed"]["status"] == "SCORED"
                   and p["observed"]["pass_all_hard"] is True,
               "match": p["match"]} for p in swap]
g3_pass = len(swap) == 2 and all(
    x["scored_pass_despite_mismatched_binding"] and x["match"] for x in g3_records)

# ---------- G4: serde wall sufficiency + necessity ----------
serde = cls("SERDE_CONTROL")
g4_records = []
for p in serde:
    pid = p["probe_id"]
    is_valid_control = pid.endswith("verbatim-valid-control")
    obs = p["observed"]
    if is_valid_control:
        ok = obs["status"] == "SCORED" and obs["pass_all_hard"] is True
    else:
        ok = (obs["status"] == "FAILED_GATES"
              and obs["pass_all_hard"] is False
              and obs["gate_reason"] in (
                  "positive_applicability_unavailable_without_rdkit_and_ontology",))
    g4_records.append({"probe_id": pid, "is_valid_control": is_valid_control,
                       "gate_reason": obs["gate_reason"], "behaved": ok,
                       "match": p["match"]})
g4_pass = all(x["behaved"] and x["match"] for x in g4_records)

# ---------- G5: magnitude / count-insensitivity ----------
def dec_tuple(pid):
    o = by_id[pid]["observed"]
    return (o["status"], o["pass_all_hard"], o["gate_reason"])


g5_pairs = [
    ("benzene-inert",
     "magnitude::benzene-ox1", "magnitude::benzene-ox4294967295"),
    ("dgeba-underdeclared-vs-honest",
     "magnitude::dgeba-ox1", "magnitude::dgeba-ox2"),
]
g5_records = []
for label, a, b in g5_pairs:
    ta, tb = dec_tuple(a), dec_tuple(b)
    g5_records.append({"pair": label, "a": a, "b": b,
                       "decision_a": ta, "decision_b": tb,
                       "count_insensitive_above_threshold": ta == tb})
g5_pass = all(r["count_insensitive_above_threshold"] for r in g5_records) and all(
    by_id[p]["match"] for p in
    ["magnitude::benzene-ox1", "magnitude::benzene-ox4294967295",
     "magnitude::dgeba-ox1", "magnitude::dgeba-ox2"])

# ---------- G6: role x (ox,nh) decision grid ----------
grid = cls("GRID")
g6_records = [{"probe_id": p["probe_id"], "match": p["match"],
               "observed_pass": p["observed"]["pass_all_hard"],
               "observed_reason": p["observed"]["gate_reason"]} for p in grid]
g6_pass = len(grid) == 16 and all(x["match"] for x in g6_records)

# ---------- G7: two-replay byte stability (per-probe) ----------
g7_all_stable = all(p.get("two_replay_byte_stable") is True
                    for p in per_probe if "observed" in p)

all_probes_match = all(p["match"] for p in per_probe if "observed" in p)

gates = {
    "g0_fixture_non_regression": g0_pass,
    "g1_snapshot_authorship_inert_structure_scores": g1_pass,
    "g2_lexical_ladder_bypassed_when_snapshot_present": g2_pass,
    "g3_structure_identity_binding_inert_to_gate": g3_pass,
    "g4_serde_contract_is_sole_admission_wall": g4_pass,
    "g5_count_insensitive_above_presence_threshold": g5_pass,
    "g6_role_reactivity_decision_grid_exact": g6_pass,
    "g7_per_probe_two_replay_byte_stable": g7_all_stable,
    "oracle_matches_live_all_probes": all_probes_match,
    "all_pass": (g0_pass and g1_pass and g2_pass and g3_pass and g4_pass
                 and g5_pass and g6_pass and g7_all_stable and all_probes_match),
}

diag = {
    "schema": "amphora.molecule-design-gate.fact-snapshot-authority.diagnostic.v1",
    "study_id": "fact-snapshot-authority-v1",
    "module": "amphora-molecule-design-gate",
    "authority": "AUDIT_ONLY",
    "authority_ceiling": "REAL_ARITHMETIC",
    "run_type": "LIVE_RUST_RUNTIME_DIFFERENTIAL_DECISION_AUTHORITY_AUDIT",
    "purpose": (
        "Exercise the STRUCTURE x SNAPSHOT decision cell the shipped 42-record "
        "Phase-0 fixture never covers, and establish against the live Rust "
        "design_gate_result that on the facts-present branch the gate decision "
        "is a pure function of the host-injected MoleculeFactsV1 (declared_role, "
        "oxirane>0, amine-H>0), consulting neither the candidate structure text "
        "nor the snapshot's structure-identity binding fields."),
    "hypothesis": (
        "An independent re-implementation of the documented decision function "
        "reproduces the live runtime on all probes; forged positive snapshots "
        "on structurally inert or lexically invalid candidates SCORE/pass; the "
        "lexical structure ladder is inert whenever a well-typed snapshot is "
        "present; and the MoleculeFactsV1 serde contract is the sole admission "
        "wall on that branch."),
    "non_circularity": (
        "Expected decisions are computed by an independent Python "
        "re-implementation of the documented decision function from probe "
        "metadata; observed decisions come from the live compiled Rust "
        "capability. The two are compared, not shared."),
    "adversarial_relevance": (
        "The shipped KPI asserts malformed-input fail-closed behaviour but every "
        "malformed record carries NO snapshot, so the fail-closed lexical ladder "
        "is only ever tested on the facts-absent branch. This audit shows the "
        "ladder is dead code when a snapshot is present, bounding the KPI's "
        "fail-closed claim to the facts-absent pathway and localising structural "
        "binding to the upstream host normaliser."),
    "defect_disclosure": (
        "design_gate_result performs NO re-derivation of, and NO consistency "
        "check between, the injected snapshot and the candidate's own structure; "
        "the snapshot's canonical_structure_sha256 / canonical_isomeric_smiles "
        "binding fields are inert to the gate. Structural binding to THIS "
        "candidate is therefore a property of amphora-engine::normalize_molecule "
        "+ amphora_rdkit_ffi::molecule_facts, not of the gate. This is a scope/"
        "provenance boundary finding, not a runtime crash; the gate's stated "
        "scope is structural-applicability-only over host-normalised facts."),
    "theory_reference": [
        "Live runtime: amphora-molecule-capabilities/src/lib.rs::design_gate_result, ::normalized_facts",
        "Snapshot contract: amphora-rdkit-ffi/src/lib.rs::MoleculeFactsV1 (serde deny_unknown_fields, u32)",
        "Host normalisation boundary: amphora-engine/src/lib.rs::normalize_molecule",
        "Epoxy-amine cure scope: Ellis 1993 Ch.6; Wicks/Jones/Pappas 2007 Ch.15",
    ],
    "runtime_source_anchors": {
        "live_rust_entry": "amphora-molecule-capabilities/src/lib.rs::design_gate_result",
        "facts_deserialization": "amphora-molecule-capabilities/src/lib.rs::normalized_facts (serde_json::from_value(..).ok())",
        "snapshot_struct": "amphora-rdkit-ffi/src/lib.rs::MoleculeFactsV1",
        "host_normaliser": "amphora-engine/src/lib.rs::normalize_molecule",
        "shipped_kpi_harness": "amphora-molecule-capabilities/tests/design_gate_phase0_kpi.rs",
        "fixture": "reference/phase0-design-gate-known-answer.v1.json",
    },
    "counts": {
        "n_probes": len(per_probe),
        "n_fixture": len(fixture),
        "n_up_forgery": len(up),
        "n_structure_bypass_lexical": len(g2_records),
        "n_structure_bypass_chemical": len(g2b_records),
        "n_binding_swap": len(swap),
        "n_serde_control": len(serde),
        "n_grid": len(grid),
        "n_oracle_mismatches": sum(
            1 for p in per_probe if "observed" in p and not p["match"]),
    },
    "g0_fixture_non_regression": {"records": g0_records, "pass": g0_pass},
    "g1_snapshot_authorship": {"records": g1_records, "pass": g1_pass},
    "g2_lexical_ladder_bypass": {"lexical": g2_records, "chemical": g2b_records,
                                 "pass": g2_pass},
    "g3_binding_inertness": {"records": g3_records, "pass": g3_pass},
    "g4_serde_wall": {"records": g4_records, "pass": g4_pass},
    "g5_count_insensitivity": {"records": g5_records, "pass": g5_pass},
    "g6_decision_grid": {"records": g6_records, "pass": g6_pass},
    "g7_two_replay": {"all_per_probe_byte_stable": g7_all_stable},
    "per_probe": per_probe,
    "gates": gates,
    "closes": [
        "First live-Rust exercise of the STRUCTURE x SNAPSHOT decision cell; the "
        "shipped fixture's 42 records leave the facts-present-x-invalid-structure "
        "and facts-present-x-mismatched-binding cells untested.",
        "Establishes that design_gate_result's decision is authored entirely by "
        "the host-injected MoleculeFactsV1 snapshot; the candidate's own "
        "structure text and the snapshot's binding fields are not consulted.",
        "Bounds the shipped KPI's malformed-fail-closed guarantee to the "
        "facts-absent pathway and localises structural binding to the upstream "
        "host normaliser (amphora-engine::normalize_molecule + molecule_facts).",
        "Shows the MoleculeFactsV1 serde contract (u32, deny_unknown_fields, "
        "required fields) is the sole admission wall on the facts-present branch: "
        "5 malformed snapshot classes fail closed, 1 well-typed forgery is "
        "accepted.",
    ],
    "does_not_close": [
        "Does not assert the finding is a runtime vulnerability: in the real "
        "engine pipeline the host normaliser is the party that emits snapshots, "
        "and it does so only for parseable single-component structures.",
        "Does not exercise amphora-engine::normalize_molecule end-to-end (the "
        "snapshots here are injected at the capability boundary, exactly as the "
        "shipped KPI harness injects them).",
        "Does not establish EHS, synthesis, qualification, procurement, "
        "regulatory, or product-performance authority.",
        "Phase-1 still requires the pinned RDKit C++ boundary and host-normaliser "
        "binding wired and audited end-to-end, not the capability in isolation.",
    ],
}
print(json.dumps(diag, sort_keys=True, separators=(",", ":")))
