#!/usr/bin/env python3
"""AUDIT_ONLY attack on amphora-formulation-arithmetic's flagship signed
Phase-0 KPI (evidence/phase0/kpis/formulation-arithmetic-mass-balance-kpi.v1.json),
specifically the `mass_balance_identity_rate` metric (floor 1.0, observed 1.0,
authority REAL_ARITHMETIC), which the module's mission.md documents as proof
that "Mass conservation is the fundamental invariant of formulation chemistry
... The module reproduces this identity at f64 bit precision across all 15
published formulations."

CLAIM UNDER ATTACK: mass_balance_identity_rate is an empirical, falsifiable
check of the module's mass-conservation arithmetic.

METHOD: faithful, line-cited re-derivation of the live Rust engine
(amphora-formulation-capabilities/src/lib.rs, RecipeObservation, lines ~940-968
and the KPI harness amphora-formulation-capabilities/tests/
formulation_arithmetic_phase0_kpi.rs lines ~120-133), run against the same
15-formulation KAT fixture the signed benchmark uses
(amphora-formulation-arithmetic/reference/phase0-formulation-arithmetic-known-answer.v1.json).

STRUCTURAL PROOF: in the live engine,
    fn total_mass_g(&self) -> f64 { self.part_a_mass_g() + self.part_b_mass_g() }
and the KPI harness's identity check is
    let identity_ok = (a + b).to_bits() == t.to_bits();
where a = out.part_a_mass_g (== recipe.part_a_mass_g()), b = out.part_b_mass_g
(== recipe.part_b_mass_g()), and t = out.total_mass_g (== recipe.total_mass_g()
== recipe.part_a_mass_g() + recipe.part_b_mass_g(), i.e. the SAME two function
calls re-evaluated). Because both sides of the "identity" are literally the
same deterministic pure-function expression evaluated twice against the same
immutable input, (a+b).to_bits() == t.to_bits() is an algebraic tautology: it
is TRUE for every possible implementation of part_a_mass_g()/part_b_mass_g(),
including a badly broken one, as long as total_mass_g() is defined as their
sum. No candidate input, however adversarial, can make this metric observe
less than 1.0.

POSITIVE DEMONSTRATION (not required for a REFUTED verdict, but included for
concreteness): a MUTATED re-derivation that injects a plausible, realistic
Rust bug into part_a_mass_g() -- an off-by-one loop-bound defect that silently
excludes the lexicographically LAST positive-mass ingredient key of part_A
from the summation (e.g. `.iter().rev().skip(1)`), while leaving that
ingredient fully present in `positive_mass_ingredient_ids` (which is built
from the map's keys, not from the sum). This is a genuine mass-conservation
violation: an ingredient the module lists as contributing to the batch is
silently dropped from the reported total. Run against the same 15-formulation
fixture:
  * mass_balance_identity_rate: STILL 15/15 == 1.0 (does not move at all --
    proving the metric cannot detect this defect class, or any defect class,
    by construction)
  * mass_balance_absolute_agreement_rate (the OTHER metric, which compares the
    module's output against the externally-authored published_expected_total_g)
    drops to reveal every fixture where the excluded ingredient carries
    nonzero mass.

CONCLUSION: mass_balance_identity_rate contributes ZERO independent
bug-detection power to the flagship KPI's floor=1.0 gate set. All the real
protective power against a mass-conservation defect in this KPI comes from
mass_balance_absolute_agreement_rate alone. The KPI receipt and mission.md
currently present 7 metrics (identity, agreement, ids, order-drift, injection,
applicability-domain, authority-lock) as if each independently gates the
REAL_ARITHMETIC authority ceiling; one of those seven is definitionally
incapable of failing and should not be counted as evidence.

AUDIT_ONLY. Does not modify the live Rust engine, the locked dataset, the
signed Phase-0 KPI, or the 66/11 manifest.
"""
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MODULE = ROOT / "amphora-formulation-arithmetic"
FIXTURE = MODULE / "reference/phase0-formulation-arithmetic-known-answer.v1.json"
SIGNED_KPI = MODULE / "evidence/phase0/kpis/formulation-arithmetic-mass-balance-kpi.v1.json"
LIB_RS = ROOT / "amphora-formulation-capabilities/src/lib.rs"
KPI_HARNESS = ROOT / "amphora-formulation-capabilities/tests/formulation_arithmetic_phase0_kpi.rs"
OUT = HERE / (sys.argv[1] if len(sys.argv) > 1 else "diagnostic.canonical.json")


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def observe_part(part_obj):
    """Faithful port of amphora-formulation-capabilities/src/lib.rs observe_part:
    positive-mass ingredients only, keyed by ingredient_key, BTreeMap semantics
    (i.e. iteration in sorted-key order); zero-mass entries recorded separately.
    """
    positive = {}
    zero_keys = []
    for key in sorted(part_obj.keys()):
        entry = part_obj[key]
        mass = entry["mass_g"] if isinstance(entry, dict) else entry
        mass = float(mass)
        if mass == 0.0:
            zero_keys.append(key)
        else:
            positive[key] = mass
    return positive, zero_keys


def part_sum(positive, drop_last_key=False):
    """part_a_mass_g()/part_b_mass_g(): sum over sorted BTreeMap values.
    drop_last_key simulates an injected off-by-one defect (skip the
    lexicographically last key) while leaving the key set (used for
    positive_mass_ingredient_ids) untouched.
    """
    keys = sorted(positive.keys())
    if drop_last_key and len(keys) > 1:
        keys = keys[:-1]
    return sum(positive[k] for k in keys)


def evaluate(fixture, bug_in_part_a):
    records = []
    identity_pass = 0
    agreement_pass = 0
    n = len(fixture["formulations"])
    for entry in fixture["formulations"]:
        fid = entry["formulation_id"]
        cand = entry["candidate"]["formulation"]
        expected_t = entry["expected_total_g"]
        part_a_obj = cand["part_A"]
        part_b_obj = cand["part_B"]

        pos_a, zero_a = observe_part(part_a_obj)
        pos_b, zero_b = observe_part(part_b_obj)

        a = part_sum(pos_a, drop_last_key=bug_in_part_a)
        b = part_sum(pos_b, drop_last_key=False)
        # total_mass_g() AS IMPLEMENTED: always part_a_mass_g() + part_b_mass_g(),
        # i.e. it re-derives from the (possibly buggy) part sums -- there is no
        # independent third computation path in the live engine.
        t = a + b

        identity_ok = (a + b) == t  # bit-exact by construction; see docstring
        agreement_ok = abs(t - expected_t) < 1e-9

        dropped_key = None
        dropped_mass = 0.0
        if bug_in_part_a and len(pos_a) > 1:
            last_key = sorted(pos_a.keys())[-1]
            dropped_key = last_key
            dropped_mass = pos_a[last_key]

        if identity_ok:
            identity_pass += 1
        if agreement_ok:
            agreement_pass += 1

        records.append({
            "formulation_id": fid,
            "part_a_mass_g": a,
            "part_b_mass_g": b,
            "total_mass_g": t,
            "expected_total_g": expected_t,
            "identity_ok": identity_ok,
            "agreement_ok": agreement_ok,
            "abs_err_g": abs(t - expected_t),
            "silently_dropped_ingredient_key": dropped_key,
            "silently_dropped_ingredient_mass_g": dropped_mass,
            "dropped_ingredient_still_listed_in_positive_mass_ids": (
                dropped_key is not None and dropped_key in pos_a
            ),
        })
    return {
        "n": n,
        "identity_rate": identity_pass / n,
        "agreement_rate": agreement_pass / n,
        "records": records,
    }


def main():
    fixture = json.loads(FIXTURE.read_text())
    baseline = evaluate(fixture, bug_in_part_a=False)
    mutated = evaluate(fixture, bug_in_part_a=True)

    signed_kpi = json.loads(SIGNED_KPI.read_text())
    signed_metrics = {m["name"]: m for m in signed_kpi["metrics"]}

    n_with_multi_ingredient_part_a = sum(
        1 for r in mutated["records"] if r["silently_dropped_ingredient_key"] is not None
    )
    n_defect_masked_by_zero_dropped_mass = sum(
        1 for r in mutated["records"]
        if r["silently_dropped_ingredient_key"] is not None and r["silently_dropped_ingredient_mass_g"] == 0.0
    )
    total_conserved_mass_hidden_g = sum(
        r["silently_dropped_ingredient_mass_g"] for r in mutated["records"]
    )

    diagnostic = {
        "schema": "amphora.formulation-arithmetic.mass-balance-identity-tautology-audit.v1",
        "module": "amphora-formulation-arithmetic",
        "authority": "AUDIT_ONLY",
        "claim_under_attack": "amphora-formulation-arithmetic/evidence/phase0/kpis/formulation-arithmetic-mass-balance-kpi.v1.json :: mass_balance_identity_rate (floor 1.0, observed 1.0) documented in docs/mission.md as an empirical reproduction of the mass-conservation physical identity",
        "attack": "structural tautology proof + defect-injection re-derivation of RecipeObservation (amphora-formulation-capabilities/src/lib.rs) against the signed KAT fixture (reference/phase0-formulation-arithmetic-known-answer.v1.json)",
        "structural_argument": {
            "source_citation": {
                "file": "amphora-formulation-capabilities/src/lib.rs",
                "total_mass_g_definition": "fn total_mass_g(&self) -> f64 { self.part_a_mass_g() + self.part_b_mass_g() }",
                "lib_rs_sha256": sha(LIB_RS),
            },
            "harness_citation": {
                "file": "amphora-formulation-capabilities/tests/formulation_arithmetic_phase0_kpi.rs",
                "identity_check": "let identity_ok = (a + b).to_bits() == t.to_bits();  // a,b,t all read off the SAME out: FormulationMassDiagnosticV1",
                "harness_sha256": sha(KPI_HARNESS),
            },
            "conclusion": "t is defined as a+b re-evaluated from the same deterministic pure functions used to produce a and b; (a+b).to_bits()==t.to_bits() is an algebraic identity true for ANY implementation of part_a_mass_g()/part_b_mass_g(), correct or buggy, as long as total_mass_g() is their sum. The metric cannot observe a value other than 1.0 for any finite-mass input that reaches this code path.",
        },
        "reimplementation_cross_check": {
            "note": "Faithful Python re-derivation of the unmutated engine reproduces the signed benchmark exactly, establishing this re-derivation is faithful before the defect is injected.",
            "baseline_identity_rate": baseline["identity_rate"],
            "baseline_agreement_rate": baseline["agreement_rate"],
            "signed_kpi_identity_rate": signed_metrics.get("mass_balance_identity_rate", {}).get("observed"),
            "signed_kpi_agreement_rate": signed_metrics.get("mass_balance_absolute_agreement_rate", {}).get("observed"),
            "signed_kpi_sha256": sha(SIGNED_KPI),
            "reimplementation_matches_signed_benchmark": (
                baseline["identity_rate"] == signed_metrics.get("mass_balance_identity_rate", {}).get("observed")
                and baseline["agreement_rate"] == signed_metrics.get("mass_balance_absolute_agreement_rate", {}).get("observed")
            ),
        },
        "defect_injection_demonstration": {
            "injected_defect": "off-by-one loop-bound bug in part_a_mass_g(): silently excludes the lexicographically LAST positive-mass ingredient key of part_A from the sum, while positive_mass_ingredient_ids (built from map keys, not the sum) still lists it -- a realistic Rust iterator-bound mistake (e.g. `.iter().rev().skip(1)`), not a contrived pathological input.",
            "n_fixtures_with_multi_ingredient_part_a": n_with_multi_ingredient_part_a,
            "n_fixtures_where_dropped_ingredient_carried_zero_mass": n_defect_masked_by_zero_dropped_mass,
            "total_conserved_mass_silently_hidden_from_total_g_across_fixtures": total_conserved_mass_hidden_g,
            "mutated_identity_rate": mutated["identity_rate"],
            "mutated_agreement_rate": mutated["agreement_rate"],
            "identity_rate_unchanged_by_defect": mutated["identity_rate"] == baseline["identity_rate"] == 1.0,
            "agreement_rate_detects_defect": mutated["agreement_rate"] < baseline["agreement_rate"],
        },
        "baseline_records": baseline["records"],
        "mutated_records": mutated["records"],
        "finding": (
            "mass_balance_identity_rate is a tautology, not an empirical test: total_mass_g() is defined "
            "as part_a_mass_g()+part_b_mass_g() re-evaluated, so the KPI harness's identity check compares "
            "an expression against itself. A faithful re-derivation of the live engine with a realistic "
            "off-by-one summation defect injected into part_a_mass_g() (dropping the last positive-mass "
            "ingredient from the sum while still listing it as a contributing ingredient) leaves "
            "mass_balance_identity_rate at 1.0/1.0 -- completely unmoved -- while "
            "mass_balance_absolute_agreement_rate (the metric that actually compares against the "
            "externally-authored published_expected_total_g) drops and exposes the defect on every "
            "multi-ingredient part_A fixture with nonzero dropped mass. The flagship, signed Phase-0 KPI "
            "(evidence/phase0/kpis/formulation-arithmetic-mass-balance-kpi.v1.json) and mission.md both "
            "cite mass_balance_identity_rate=1.0 as evidence the module 'reproduces [mass conservation] at "
            "f64 bit precision' -- but this metric could not fail even if the shipped Rust engine silently "
            "dropped an ingredient's mass from every formulation it evaluated. It contributes zero of the "
            "KPI's seven claimed independent gates; mass_balance_absolute_agreement_rate alone carries the "
            "conservation check."
        ),
        "does_not_close": [
            "does not claim the live Rust engine currently HAS this defect -- current mass_balance_absolute_agreement_rate=1.0/15 shows the real, unmutated engine's totals are correct on the 15 KAT fixtures",
            "does not modify the live Rust engine (still MASS_ONLY), any locked dataset, the signed Phase-0 KPI, or the 66/11 manifest",
            "does not evaluate mass_balance_absolute_agreement_rate's own limits (self-authored CC0 fixture, not independently measured batch weighings) -- that metric's ground truth provenance is a separate question from the one attacked here",
        ],
        "proposed_followup": (
            "Either drop mass_balance_identity_rate from the KPI's declared metric count and promotion-gate "
            "narrative, or redefine it to compare against an INDEPENDENT computation path (e.g. sum raw "
            "candidate-JSON ingredient masses directly in the test harness, bypassing RecipeObservation "
            "entirely, rather than reading out.part_a_mass_g/out.part_b_mass_g/out.total_mass_g which all "
            "originate from the same struct construction)."
        ),
        "verdict": "MASS_BALANCE_IDENTITY_RATE_TAUTOLOGICAL__ZERO_DETECTION_POWER",
    }

    OUT.write_text(json.dumps(diagnostic, indent=2, sort_keys=True))
    print("WROTE", OUT)
    print("baseline identity/agreement:", baseline["identity_rate"], baseline["agreement_rate"])
    print("mutated  identity/agreement:", mutated["identity_rate"], mutated["agreement_rate"])
    print("reimplementation_matches_signed_benchmark:",
          diagnostic["reimplementation_cross_check"]["reimplementation_matches_signed_benchmark"])


if __name__ == "__main__":
    main()
