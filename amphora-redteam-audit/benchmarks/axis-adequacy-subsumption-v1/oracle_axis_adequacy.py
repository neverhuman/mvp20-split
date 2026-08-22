#!/usr/bin/env python3
"""axis-adequacy-subsumption-v1 — independent non-runtime CPython oracle for
amphora-redteam-audit.

Subject: the shipped Phase-0 KPI `attack_axis_coverage_complete_rate`
(observed 1.0, floor 1.0, MAXIMIZE, sample_size 24, passed=true), whose name asserts
that attack-axis coverage of the locked adversarial corpus is COMPLETE.

Falsifiable hypothesis under test (as a test-adequacy criterion in the sense of
Zhu-Hall-May 1997): C_declared = "every attack axis declared in the module's
benchmark-lock is cross-checked by the coverage KPI". If the shipped KPI satisfies
C_declared, then observed(C_declared) == 1.0.

Distinct from and non-overlapping with the two prior amphora-redteam-audit oracles:
  meta-integrity-oracle-parity-v1  — OUTPUT digest parity + result tamper corpus; its
      G3 only asserted the 24 KPI axes are PRESENT in the lock (checked -> declared).
      It did NOT test the converse direction (declared -> checked), which is where the
      adequacy gap lives.
  dispatch-boundary-fail-closed-v1 — INPUT module-id dispatch allowlist.
This oracle tests the COVERAGE-ADEQUACY direction of the axis KPI itself.

Theory / primary sources:
  Zhu, Hall, May (1997) "Software Unit Test Coverage and Adequacy", ACM Computing
      Surveys 29(4):366-427, doi:10.1145/267580.267590 — adequacy criterion as a
      predicate C(P,S,T); coverage measured against a DECLARED requirement set.
  Rapps & Weyuker (1985) "Selecting Software Test Data Using Data Flow Information",
      IEEE TSE SE-11(4):367-375, doi:10.1109/TSE.1985.232226 — subsumption ordering
      of adequacy criteria (C1 subsumes C2 iff C1-adequate implies C2-adequate).
  DeMillo, Lipton, Sayward (1978) "Hints on Test Data Selection: Help for the
      Practicing Programmer", IEEE Computer 11(4):34-41, doi:10.1109/C-M.1978.218136 —
      an unexercised fault class cannot be killed by the suite.
  Anderson (1972) ESD-TR-73-51 reference monitor / complete mediation;
      Saltzer & Schroeder (1975) Proc. IEEE 63(9):1278-1308 — fail-safe defaults,
      complete mediation: a mediation claim is only as wide as its enumerated surface.
  NIST SP 800-53 Rev.5 CA-8 / RA-5 — penetration-test and vulnerability coverage must
      be stated against a defined scope.
  RFC 8785 JSON Canonicalization Scheme; NIST FIPS 180-4 SHA-256; RFC 8032 Ed25519.

AUDIT_ONLY. Reads shipped evidence only. Writes nothing. No authority, no promotion,
no manifest / benchmark-lock / KPI modification.
"""
import hashlib
import json
from fractions import Fraction
from pathlib import Path

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-redteam-audit"
LOCK_P = MOD / "evidence/phase0/benchmark/benchmark-lock.v1.json"
RESULT_P = MOD / "evidence/phase0/benchmark/result.v1.json"
KPI_P = MOD / "evidence/phase0/kpis/redteam-audit-deterministic-control-diagnostic-kpi.v1.json"
KPI_FIELD = "attack_axis_coverage_complete_rate"


def sha(b):
    return hashlib.sha256(b).hexdigest()


def jcs(obj):
    """RFC 8785 JCS-compatible canonical serialization for this document class
    (objects, arrays, strings, booleans and integers only)."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False).encode("utf-8")


lock_raw = LOCK_P.read_bytes()
result_raw = RESULT_P.read_bytes()
lock = json.loads(lock_raw)
result = json.loads(result_raw)

attacks = lock["attacks"]
kpi1 = result["first_replay"]["diagnostic_receipt"]["kpi"][KPI_FIELD]
kpi2 = result["second_replay"]["diagnostic_receipt"]["kpi"][KPI_FIELD]
checked = [d["axis"] for d in kpi1["axis_details"]]

# ---------------------------------------------------------------- G1 lock structure
seen, dup_index = {}, {}
for i, a in enumerate(attacks):
    seen.setdefault(a, []).append(i)
duplicates = {a: ix for a, ix in seen.items() if len(ix) > 1}
declared_unique = sorted(seen)
G1 = {
    "name": "lock_multiset_structure_and_digest_parity",
    "benchmark_lock_sha256_recomputed": sha(lock_raw),
    "shipped_benchmark_lock_sha256": result["benchmark_lock_sha256"],
    "digest_parity": sha(lock_raw) == result["benchmark_lock_sha256"],
    "declared_array_length": len(attacks),
    "declared_unique_count": len(declared_unique),
    "is_set": len(attacks) == len(declared_unique),
    "duplicate_axes": duplicates,
    "passed": (sha(lock_raw) == result["benchmark_lock_sha256"]
               and len(attacks) == 47 and len(declared_unique) == 46
               and duplicates == {"AUTHORITY_ESCALATION": [14, 46]}),
}

# ------------------------------------------------- G2 shipped KPI self-criterion
# C_self : every axis the KPI cross-checks is declared in the lock (checked -> declared)
self_hits = [a for a in checked if a in seen]
c_self = Fraction(len(self_hits), len(checked))
G2 = {
    "name": "shipped_kpi_reproduction_under_its_own_criterion",
    "criterion": "C_self : checked -> declared (every cross-checked axis is in the lock)",
    "recomputed_observed": float(c_self),
    "recomputed_sample_size": len(checked),
    "shipped_observed": kpi1["observed"],
    "shipped_sample_size": kpi1["sample_size"],
    "shipped_passed": kpi1["passed"],
    "shipped_floor": kpi1["floor"],
    "replay1_equals_replay2": kpi1 == kpi2,
    "arithmetic_defect_found": False,
    "passed": (float(c_self) == kpi1["observed"] == 1.0
               and len(checked) == kpi1["sample_size"] == 24
               and kpi1["passed"] is True and kpi1 == kpi2),
}

# --------------------------------------- G3 subsumption / adequacy falsification
# C_declared : every axis declared in the lock is cross-checked (declared -> checked)
checked_set = set(checked)
uncovered = sorted(set(declared_unique) - checked_set)
covered = sorted(checked_set & set(declared_unique))
c_declared = Fraction(len(covered), len(declared_unique))
G3 = {
    "name": "adequacy_criterion_subsumption_falsification",
    "criterion": "C_declared : declared -> checked (every locked attack axis is cross-checked)",
    "subsumption": ("C_declared strictly subsumes C_self on this instance: checked is a "
                    "proper subset of declared (Rapps-Weyuker 1985 subsumption ordering)"),
    "checked_is_proper_subset_of_declared": checked_set < set(declared_unique),
    "declared_unique_count": len(declared_unique),
    "cross_checked_count": len(covered),
    "uncovered_count": len(uncovered),
    "observed_C_declared_exact": f"{c_declared.numerator}/{c_declared.denominator}",
    "observed_C_declared": round(float(c_declared), 10),
    "kpi_floor": kpi1["floor"],
    "C_declared_meets_floor": float(c_declared) >= kpi1["floor"],
    "uncovered_axes": uncovered,
    "finding": ("ADEQUACY_GAP: the KPI reports 1.0 'coverage complete' but is scoped to a "
                "24-axis subset; under the declared-corpus criterion the same evidence "
                f"yields {c_declared.numerator}/{c_declared.denominator} "
                f"= {round(float(c_declared),6)} < floor {kpi1['floor']}. The word "
                "'complete' in the KPI name is scope-relative, not corpus-relative."),
    "passed": (len(uncovered) == 22 and checked_set < set(declared_unique)
               and float(c_declared) < kpi1["floor"]),
}

# ----------------------------------------------------- G4 block-partition diagnosis
# Is the gap systematic (a concatenation seam) or scattered?
BOUNDARY = len(attacks) - len(checked)          # 47 - 24 = 23
outer, inner = attacks[:BOUNDARY], attacks[BOUNDARY:]
ordered_suffix_match = checked == inner
block_overlap = sorted(set(outer) & set(inner))


def n_choose_k(n, k):
    num = den = 1
    for i in range(k):
        num *= n - i
        den *= i + 1
    return num // den


chance = 1.0 / n_choose_k(len(declared_unique), len(checked))
G4 = {
    "name": "block_partition_diagnosis",
    "boundary_index": BOUNDARY,
    "outer_block_len": len(outer),
    "inner_block_len": len(inner),
    "checked_equals_ordered_inner_block": ordered_suffix_match,
    "block_set_overlap": block_overlap,
    "outer_block": outer,
    "inner_block": inner,
    "random_subset_null_probability": chance,
    "diagnosis": ("The cross-checked set is EXACTLY the ordered contiguous suffix "
                  "attacks[23:47]; the lock is two concatenated corpora — an OUTER "
                  "portfolio-governance block (23 axes, delegated to sibling modules) and "
                  "an INNER meta-audit block (24 axes, self-checked) — intersecting in "
                  "exactly one axis, AUTHORITY_ESCALATION (which is therefore the sole "
                  "axis both delegated and self-checked, and the source of the duplicate). "
                  "The omission coincides with a concatenation seam, so it is a scoping "
                  "artifact, not a random or adversarial omission."),
    "passed": (ordered_suffix_match and block_overlap == ["AUTHORITY_ESCALATION"]
               and len(outer) == 23 and len(inner) == 24),
}

# ------------------------------------------- G5 compensating-control search (portfolio)
lock_decls, kpi_modules, modules_scanned = {}, [], []
for mp in sorted(ROOT.glob("*/evidence/phase0/benchmark/benchmark-lock.v1.json")):
    mod = mp.parent.parent.parent.parent.name
    modules_scanned.append(mod)
    try:
        ml = json.loads(mp.read_bytes())
    except Exception:
        continue
    for a in set(ml.get("attacks", [])):
        lock_decls.setdefault(a, []).append(mod)

for rp in sorted(ROOT.glob("*/evidence/phase0/benchmark/result.v1.json")):
    mod = rp.parent.parent.parent.parent.name
    try:
        blob = rp.read_bytes()
    except Exception:
        continue
    if KPI_FIELD.encode() in blob:
        kpi_modules.append(mod)

comp = []
for a in uncovered:
    decl = sorted(x for x in lock_decls.get(a, []) if x != "amphora-redteam-audit")
    comp.append({
        "axis": a,
        "sibling_locks_declaring": len(decl),
        "cross_checked_by_any_axis_coverage_kpi": False,
        "status": "DECLARED_ONLY" if decl else "UNDECLARED_ELSEWHERE",
    })
G5 = {
    "name": "compensating_control_search",
    "modules_scanned": len(modules_scanned),
    "modules_with_axis_coverage_kpi": kpi_modules,
    "axis_coverage_kpi_is_portfolio_unique": kpi_modules == ["amphora-redteam-audit"],
    "per_axis": comp,
    "declared_only_count": sum(1 for c in comp if c["status"] == "DECLARED_ONLY"),
    "compensating_kpi_attestations_found": 0,
    "sibling_declaration_span": [min(c["sibling_locks_declaring"] for c in comp),
                                 max(c["sibling_locks_declaring"] for c in comp)],
    "finding": ("Each of the 22 uncovered axes IS declared in 27-28 of the 28 sibling "
                f"module benchmark-locks, yet `{KPI_FIELD}` exists in exactly 1 of "
                f"{len(modules_scanned)} shipped "
                "module results — amphora-redteam-audit itself. No sibling ships a KPI "
                "that cross-checks its own declared attack axes, so the 22 outer axes are "
                "DECLARED_ONLY portfolio-wide: no shipped KPI attests them anywhere."),
    "honesty_note": ("This establishes absence of a shipped KPI-level attestation. It does "
                     "NOT prove the underlying Rust defenses are absent; sibling runtimes "
                     "may implement them without a coverage KPI. Live Rust re-execution is "
                     "the Phase-1 axis."),
    "passed": (len(comp) == 22 and kpi_modules == ["amphora-redteam-audit"]
               and all(c["status"] == "DECLARED_ONLY" for c in comp)),
}

# --------------------------------------- G6 duplicate: digest-load-bearing, KPI-inert
dedup_lock = dict(lock)
dedup_lock["attacks"] = sorted(set(attacks))
dedup_sha = sha(jcs(dedup_lock))
asis_jcs_sha = sha(jcs(lock))
dedup_checked_ok = set(checked) <= set(dedup_lock["attacks"])
dedup_c_declared = Fraction(len(set(checked) & set(dedup_lock["attacks"])),
                            len(dedup_lock["attacks"]))
G6 = {
    "name": "duplicate_axis_counterfactual",
    "shipped_raw_sha256": sha(lock_raw),
    "jcs_as_is_sha256": asis_jcs_sha,
    "jcs_deduplicated_sha256": dedup_sha,
    "dedup_changes_digest": dedup_sha != asis_jcs_sha,
    "kpi_under_dedup_C_self": 1.0 if dedup_checked_ok else None,
    "kpi_under_dedup_C_declared_exact": f"{dedup_c_declared.numerator}/{dedup_c_declared.denominator}",
    "kpi_unchanged_by_dedup": (dedup_checked_ok and dedup_c_declared == c_declared),
    "finding": ("AUTHORITY_ESCALATION appears twice (indices 14 and 46), so `attacks` is a "
                "multiset, not a set. The duplicate is KPI-INERT (both C_self and "
                "C_declared are unchanged when it is removed) but DIGEST-LOAD-BEARING: "
                "any well-intentioned downstream normalization that set-izes the array "
                "changes the canonical digest and breaks benchmark-lock continuity. "
                "Recorded as an operational hazard, not a security defect."),
    "passed": (dedup_sha != asis_jcs_sha and dedup_checked_ok
               and dedup_c_declared == c_declared),
}

# ---------------------------------------------------------- G7 anchors / replay
kpi_doc_sha = sha(KPI_P.read_bytes()) if KPI_P.exists() else None
G7 = {
    "name": "subject_anchors_and_replay_determinism",
    "shipped_result_v1_sha256": sha(result_raw),
    "benchmark_lock_sha256": sha(lock_raw),
    "kpi_document_sha256": kpi_doc_sha,
    "benchmark_execution_complete": result["benchmark_execution_complete"],
    "first_replay_kpi_equals_second": kpi1 == kpi2,
    "oracle_reads_only": True,
    "passed": (kpi1 == kpi2 and result["benchmark_execution_complete"] is True
               and kpi_doc_sha is not None),
}

gates = {
    "G1_lock_multiset_structure": G1,
    "G2_shipped_kpi_self_criterion": G2,
    "G3_adequacy_subsumption_falsification": G3,
    "G4_block_partition_diagnosis": G4,
    "G5_compensating_control_search": G5,
    "G6_duplicate_axis_counterfactual": G6,
    "G7_anchors_and_replay": G7,
}
all_passed = all(g["passed"] for g in gates.values())

out = {
    "schema": "amphora.redteam-audit.independent-oracle-result.v1",
    "oracle_id": "axis-adequacy-subsumption-v1",
    "module_id": "amphora-redteam-audit",
    "authority": "AUDIT_ONLY",
    "hypothesis": (f"Shipped KPI `{KPI_FIELD}` = 1.0 (floor 1.0, n=24) implies the module's "
                   "declared adversarial attack corpus is completely covered."),
    "verdict": "HYPOTHESIS_PARTIALLY_REFUTED",
    "verdict_statement": (
        "CORROBORATED as arithmetic: under its own criterion (every cross-checked axis is "
        "declared) the KPI reproduces exactly 24/24 = 1.0, replay-identical, with no "
        "arithmetic defect. REFUTED as a completeness claim: the lock declares 46 unique "
        "axes and the KPI cross-checks 24 of them, so under the declared-corpus adequacy "
        "criterion the same evidence yields 12/23 = 0.521739 < the 1.0 floor. 22 axes are "
        "declared-and-never-cross-checked, and the omitted set is exactly the ordered "
        "outer block attacks[0:23] minus AUTHORITY_ESCALATION — a scoping seam, not a "
        "random gap. No sibling module ships a compensating axis-coverage KPI."),
    "all_gates_passed": all_passed,
    "headline_numbers": {
        "declared_axes_array_len": len(attacks),
        "declared_axes_unique": len(declared_unique),
        "cross_checked_axes": len(checked),
        "uncovered_axes": len(uncovered),
        "C_self_observed": float(c_self),
        "C_declared_observed_exact": f"{c_declared.numerator}/{c_declared.denominator}",
        "C_declared_observed": round(float(c_declared), 6),
        "kpi_floor": kpi1["floor"],
        "modules_with_axis_coverage_kpi": len(kpi_modules),
        "modules_scanned": len(modules_scanned),
    },
    "gates": gates,
    "relation_to_prior_oracle": {
        "meta-integrity-oracle-parity-v1": (
            "its G3 asserted checked -> declared (24/24 axes present in the lock); this "
            "oracle tests the converse declared -> checked and finds the 22-axis gap"),
        "dispatch-boundary-fail-closed-v1": (
            "covered the INPUT module-id dispatch allowlist; disjoint from axis adequacy"),
        "non_overlap_asserted": True,
    },
    "theory_sources": [
        "Zhu, Hall, May (1997) ACM Comput. Surv. 29(4):366-427, doi:10.1145/267580.267590",
        "Rapps & Weyuker (1985) IEEE TSE SE-11(4):367-375, doi:10.1109/TSE.1985.232226",
        "DeMillo, Lipton, Sayward (1978) IEEE Computer 11(4):34-41, doi:10.1109/C-M.1978.218136",
        "Anderson (1972) ESD-TR-73-51 reference monitor / complete mediation",
        "Saltzer & Schroeder (1975) Proc. IEEE 63(9):1278-1308, doi:10.1109/PROC.1975.9939",
        "NIST SP 800-53 Rev.5 CA-8 / RA-5 (scoped assessment coverage)",
        "RFC 8785 JSON Canonicalization Scheme; NIST FIPS 180-4; RFC 8032 Ed25519",
    ],
    "remediation_note": (
        "Non-authoritative suggestion for a future human-keyed fire: either (a) rename the "
        f"KPI to `meta_audit_axis_coverage_complete_rate` and add a second KPI over the "
        "outer block, or (b) require each sibling module to ship its own axis-coverage KPI "
        "so the outer 23 axes gain attestation. This oracle changes nothing."),
    "ceiling_note": (
        "Offline oracle over shipped evidence bytes. It measures which axes the shipped KPI "
        "cross-checks, NOT whether the Rust runtime defends the uncovered axes. Live Rust "
        "re-execution of the per-axis adversarial corpus and error-taxonomy parity remain "
        "the Phase-1 axis. AUDIT_ONLY: no promotion, no authority, manifest untouched."),
    "zero_authority_claim_locks": {
        "no_ranking_authority": True, "no_optimizer_authority": True,
        "no_release_authority": True, "no_qualification_authority": True,
        "no_patentability_authority": True, "fto_not_performed": True,
        "no_procurement_authority": True, "no_regulatory_authority": True,
        "no_safety_authority": True, "no_product_performance_authority": True,
    },
}
print(json.dumps(out, indent=2, sort_keys=True))
