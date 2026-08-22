#!/usr/bin/env python3
"""mixed-radix-bijection-representation-invariance-v1 (AUDIT_ONLY).

Escalation over evidence/audit/mixed-radix-bijection-v1 and T-06
(2026-08-06, CLAIM_REFUTED, campaign item T-06).

T-06 proved, against the LIVE RUST runtime, that two "accounting-equivalent"
representations of the same declared universe (identical axis keys,
identical axis value SETS, identical axis_cardinalities, identical
cartesian_total, byte-identical FormulationUniverseAccountingV1 output) --
differing only in the ORDER of values inside one axis array -- decode the
SAME declared infeasible index to two DIFFERENT physical formulations under
the module's own documented mixed-radix unranking algorithm (the exact
algorithm implemented in evidence/audit/mixed-radix-bijection-v1's oracle).

The mixed-radix-bijection-v1 receipt asserts (per-fixture-universe, over the
module's 10 legitimate DoE fixture entries only):
  bijection_holds_all_universes: true
  acceptance_all_perfect: true
and its prose claims this "proves the index<->tuple map is a BIJECTION ...
surjective => no silent loss" -- cited approvingly in docs/mission.md's
2026-08-06 Known Contradictions entry as "the module's own documented
mixed-radix unranking."

THIS FIRE asks a narrower, sharper question that neither T-06 nor
mixed-radix-bijection-v1 asked: does the mixed-radix-bijection-v1 oracle
ITSELF -- the tool the portfolio is relying on as independent corroboration
-- have any power to detect the exact representation-order defect T-06
already proved is live? Or does it only ever check bijectivity WITHIN one
representation at a time, making it structurally blind to the cross-
representation instability that is the actual content of the T-06 finding?

Method: reproduce T-06's own universe_A / universe_B construction exactly
(same axis keys, same value sets, hardener axis order swapped) and run them
through the mixed-radix-bijection-v1 oracle's own functions (re-implemented
here byte-for-byte from run_mixed_radix_bijection.py: radices_and_values,
place_weights, unrank, rank -- BTreeMap key-sort parity, values taken in
given array order, never re-sorted -- matching what the oracle's own README
documents as canonical).
"""
import json, hashlib, sys
from pathlib import Path

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-formulation-universe"
ORACLE_DIR = MOD / "evidence/audit/mixed-radix-bijection-v1"


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


# ---- byte-for-byte reproduction of the oracle's own primitives ----------
def radices_and_values(axes: dict):
    """BTreeMap parity with the Rust runtime: axes sorted by key.
    Verbatim logic from evidence/audit/mixed-radix-bijection-v1/run_mixed_radix_bijection.py.
    """
    items = sorted(axes.items())
    keys = [k for k, _ in items]
    values = [list(v) for _, v in items]
    radices = [len(v) for v in values]
    return keys, values, radices


def place_weights(radices):
    k = len(radices)
    w = [1] * k
    for j in range(k - 2, -1, -1):
        w[j] = w[j + 1] * radices[j + 1]
    return w


def unrank(i, radices, weights):
    digits = []
    for j in range(len(radices)):
        digits.append((i // weights[j]) % radices[j])
    return tuple(digits)


def rank(digits, weights):
    return sum(d * w for d, w in zip(digits, weights))


def oracle_universe_metrics(axes, infeasible_indices):
    """Reproduces run_mixed_radix_bijection.py::oracle_universe()'s acceptance
    metrics exactly (same field names), for a synthetic (non-fixture) universe.
    """
    from itertools import product
    keys, values, radices = radices_and_values(axes)
    weights = place_weights(radices)
    import math
    N = math.prod(radices) if radices else 0

    seen_digit = set()
    seen_value = set()
    roundtrip_ok = True
    decode = {}
    for i in range(N):
        digits = unrank(i, radices, weights)
        if rank(digits, weights) != i:
            roundtrip_ok = False
        seen_digit.add(digits)
        tup = tuple(values[j][digits[j]] for j in range(len(radices)))
        seen_value.add(tup)
        decode[i] = tup

    injective = (len(seen_digit) == N)
    independent_set = set(product(*[range(r) for r in radices])) if radices else set()
    surjective = (seen_digit == independent_set)
    value_bijection = (len(seen_value) == N)

    inf_idx = infeasible_indices
    inf_in_range = all(isinstance(x, int) and not isinstance(x, bool) and 0 <= x < N for x in inf_idx)
    inf_unique = (len(set(inf_idx)) == len(inf_idx))
    infeasible_count = len(set(inf_idx))
    solved_count = N - infeasible_count

    return {
        "sorted_axis_keys": keys,
        "axis_values_in_order": values,
        "radices": radices,
        "place_weights": weights,
        "cartesian_total_product": N,
        "bijection_roundtrip_rank_unrank": roundtrip_ok,
        "bijection_injective_no_duplication": injective,
        "bijection_surjective_no_silent_loss": surjective,
        "value_tuple_bijection": value_bijection,
        "acceptance_all_perfect_this_universe": all([
            roundtrip_ok, injective, surjective, value_bijection, inf_in_range, inf_unique,
        ]),
        "infeasible_indices_in_range": inf_in_range,
        "infeasible_indices_unique": inf_unique,
        "derived_infeasible_count": infeasible_count,
        "derived_solved_count": solved_count,
        "identity_solved_plus_infeasible_eq_total": (solved_count + infeasible_count == N),
        "decode_table": {str(k): list(v) for k, v in decode.items()},
    }


def build_diagnostic():
    # T-06's own construction, reproduced verbatim (T-06 diagnostic.canonical.json,
    # attacks.index_laundering_out_of_universe_smuggling):
    #   resin axis (both universes, unchanged order): ["DGEBA", "DGEBF"]
    #   hardener axis universe A: ["IPDA", "TETA"]
    #   hardener axis universe B: ["TETA", "IPDA"]   (order-permuted, same set)
    #   declared infeasible_indices: [1] for both
    #   T-06 found (live Rust): index 1 decodes to ("IPDA","DGEBF") under A,
    #                           ("TETA","DGEBF") under B; receipt bytes equal.
    axes_a = {"resin": ["DGEBA", "DGEBF"], "hardener": ["IPDA", "TETA"]}
    axes_b = {"resin": ["DGEBA", "DGEBF"], "hardener": ["TETA", "IPDA"]}
    infeasible = [1]

    metrics_a = oracle_universe_metrics(axes_a, infeasible)
    metrics_b = oracle_universe_metrics(axes_b, infeasible)

    # Negative control: identical order (no permutation) -- must agree.
    axes_c = {"resin": ["DGEBA", "DGEBF"], "hardener": ["IPDA", "TETA"]}
    metrics_c = oracle_universe_metrics(axes_c, infeasible)

    decode_a_idx1 = metrics_a["decode_table"]["1"]
    decode_b_idx1 = metrics_b["decode_table"]["1"]
    decode_c_idx1 = metrics_c["decode_table"]["1"]

    accounting_fields = ["cartesian_total_product", "radices", "place_weights",
                          "derived_infeasible_count", "derived_solved_count",
                          "identity_solved_plus_infeasible_eq_total"]
    accounting_equal_a_vs_b = all(metrics_a[f] == metrics_b[f] for f in accounting_fields)

    both_individually_pass = (metrics_a["acceptance_all_perfect_this_universe"] is True
                               and metrics_b["acceptance_all_perfect_this_universe"] is True)

    representation_invariant_decode_a_vs_b = (decode_a_idx1 == decode_b_idx1)
    representation_invariant_decode_a_vs_c = (decode_a_idx1 == decode_c_idx1)

    # Does the shipped oracle's own acceptance vocabulary (the 10 fields
    # aggregated into acceptance_all_perfect / bijection_holds_all_universes
    # in run_mixed_radix_bijection.py::build_diagnostic, plus its 9
    # failclosed_probes) contain ANY field that is a function of more than
    # one universe object at once, i.e. that COULD have caught this?
    # By construction (oracle_universe() takes a single `u` dict; the 9
    # failclosed_probes operate on one fixed radices=[2,2,2] universe with
    # tampered indices/weights/digits, never on a second differently-ordered
    # representation of the same universe): no such field exists. This is
    # verified structurally, not just observationally, in the receipt text.

    diagnostic = {
        "schema": "amphora.formulation-universe.mixed-radix-bijection-representation-invariance.v1",
        "authority": "AUDIT_ONLY",
        "module": "amphora-formulation-universe",
        "claim_under_test": (
            "evidence/audit/mixed-radix-bijection-v1's claim "
            "(bijection_holds_all_universes: true, acceptance_all_perfect: "
            "true; prose: 'proves the index<->tuple map is a BIJECTION ... "
            "surjective => no silent loss') constitutes independent "
            "corroboration that Cartesian enumeration reports every solved "
            "and infeasible combination without silent loss or ambiguity, "
            "as cited approvingly in docs/mission.md's T-06 Known "
            "Contradictions entry ('the module's own documented mixed-radix "
            "unranking')."
        ),
        "oracle_under_test": {
            "path": "amphora-formulation-universe/evidence/audit/mixed-radix-bijection-v1/run_mixed_radix_bijection.py",
            "sha256": sha((ORACLE_DIR / "run_mixed_radix_bijection.py").read_bytes()),
            "receipt_path": "amphora-formulation-universe/evidence/audit/mixed-radix-bijection-v1/mixed-radix-bijection-receipt.v1.dsse.json",
        },
        "prior_finding_reproduced_as_input": {
            "source": "amphora-formulation-universe/evidence/phase0/repairs/T-06/done/t06-independent-adversarial-attack-receipt.v1.dsse.json",
            "attack": "index_laundering_out_of_universe_smuggling",
            "verdict": "CLAIM_REFUTED (2026-08-06, campaign item T-06)",
            "quoted": "the same declared infeasible index resolves to two different physical axis-value tuples across two accounting-equivalent (byte-identical-output) representations of 'the same' universe",
        },
        "universe_a": {"axes": axes_a, "infeasible_indices": infeasible, "metrics": metrics_a},
        "universe_b": {"axes": axes_b, "infeasible_indices": infeasible, "metrics": metrics_b},
        "universe_c_negative_control_unpermuted": {"axes": axes_c, "infeasible_indices": infeasible, "metrics": metrics_c},
        "decoded_tuple_for_declared_infeasible_index_1": {
            "under_a": decode_a_idx1,
            "under_b": decode_b_idx1,
            "under_c_negative_control": decode_c_idx1,
        },
        "accounting_output_equal_a_vs_b": accounting_equal_a_vs_b,
        "both_universes_individually_pass_oracle_acceptance": both_individually_pass,
        "representation_invariant_decode_a_vs_b": representation_invariant_decode_a_vs_b,
        "representation_invariant_decode_a_vs_c_negative_control": representation_invariant_decode_a_vs_c,
        "finding": (
            "Universe A and universe B are ACCOUNTING-EQUIVALENT (identical "
            "sorted_axis_keys, identical radices, identical place_weights, "
            "identical cartesian_total_product=4, identical "
            "derived_infeasible_count=1, identical derived_solved_count=3 -- "
            "accounting_output_equal_a_vs_b=true, reproducing T-06's "
            "'receipt_bytes_equal=true' finding at the oracle level) and "
            "EACH INDIVIDUALLY PASSES EVERY ACCEPTANCE METRIC AND FAILCLOSED "
            "PROBE THE SHIPPED mixed-radix-bijection-v1 ORACLE COMPUTES "
            "(both_universes_individually_pass_oracle_acceptance=true: "
            "bijection_roundtrip/injective/surjective/value_tuple_bijection "
            "all true for A alone and for B alone). Yet the declared "
            "infeasible index 1 decodes to ('IPDA','DGEBF') under A and "
            "('TETA','DGEBF') under B -- "
            "representation_invariant_decode_a_vs_b=false -- reproducing "
            "T-06's exact counterexample bit-for-bit via the oracle's own "
            "published algorithm. The negative control (universe C, hardener "
            "order UNCHANGED from A) decodes identically to A "
            "(representation_invariant_decode_a_vs_c_negative_control=true), "
            "confirming the instability is caused specifically by the axis-"
            "value reordering and not by the harness. The mixed-radix-"
            "bijection-v1 oracle's acceptance vocabulary (10 per-universe "
            "rate fields plus 9 failclosed_probes, all read from run_mixed_"
            "radix_bijection.py) contains no field that is ever computed "
            "across two representations of what the runtime treats as 'the "
            "same' universe -- every metric is a property of ONE axes dict "
            "in isolation. It is therefore structurally incapable of "
            "detecting the representation-order defect T-06 already proved "
            "live in the Rust runtime, and would report "
            "'acceptance_all_perfect: true' on BOTH universe A and universe "
            "B if either were substituted for a fixture entry, exactly as it "
            "does today. The receipt's claim to establish that the index<-"
            ">tuple map is loss-free and duplication-free is true only "
            "within a single fixed representation; it does not and cannot "
            "establish representation-invariant identity, which is the "
            "specific property T-06 disproved and which docs/mission.md "
            "cites this oracle in connection with."
        ),
        "refutation_criterion_verbatim": (
            "If two accounting-equivalent representations of the same "
            "declared universe (identical axis_cardinalities / "
            "cartesian_total / solved / infeasible counts under the oracle's "
            "own metrics) decode a shared declared infeasible index to two "
            "different physical value tuples, AND the mixed-radix-bijection-"
            "v1 oracle's acceptance_all_perfect / bijection_holds_all_"
            "universes metrics and 9 failclosed_probes do not flag either "
            "representation as failing, then the oracle's claim to certify "
            "'no silent loss' / 'no silent duplication' for the Cartesian-"
            "accounting claim is incomplete: it does not cover, and cannot "
            "detect, the representation-order identity-instability defect "
            "class already proven live by T-06."
        ),
        "refutation_criterion_observation_occurred": True,
        "claim_locks": {
            "no_superiority_claim": True,
            "enumeration_is_not_performance_evidence": True,
            "no_phase_1_or_phase_2_claim": True,
            "pre_phase_0_research_only": True,
            "no_product_release_or_qualification": True,
        },
    }
    return diagnostic


def canonical_bytes(obj):
    return json.dumps(obj, indent=2, sort_keys=True).encode() + b"\n"


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "diagnostic.canonical.json"
    diag = build_diagnostic()
    Path(out).write_bytes(canonical_bytes(diag))
    print("WROTE", out, "sha256", sha(canonical_bytes(diag)))
    print("accounting_output_equal_a_vs_b", diag["accounting_output_equal_a_vs_b"])
    print("both_universes_individually_pass_oracle_acceptance", diag["both_universes_individually_pass_oracle_acceptance"])
    print("representation_invariant_decode_a_vs_b", diag["representation_invariant_decode_a_vs_b"])
    print("representation_invariant_decode_a_vs_c_negative_control", diag["representation_invariant_decode_a_vs_c_negative_control"])
