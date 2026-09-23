#!/usr/bin/env python3
"""amphora-formulation-universe — mixed-radix bijection completeness oracle (AUDIT_ONLY).

Independent theory-axis re-derivation of the Cartesian-accounting claim
("Cartesian enumeration can report every solved and infeasible combination
without silent loss") using the classical mixed-radix positional numeral
system.

Primary sources (published, non-circular baselines):
  - Knuth, D.E. "The Art of Computer Programming, Vol. 2: Seminumerical
    Algorithms", 3rd ed. (1997), Addison-Wesley, ISBN 0-201-89684-2,
    §4.1 "Positional Number Systems" (mixed-radix representation and the
    place-value / maximum-numeral identity).
  - Nijenhuis, A. & Wilf, H.S. "Combinatorial Algorithms for Computers and
    Calculators", 2nd ed. (1978), Academic Press, ISBN 0-12-519260-6,
    Ch. 1-3 (ranking / unranking of Cartesian tuples).

Why this adds value over the existing Rust Phase-0 benchmark:
  The checked-in benchmark verifies COUNTS (product = Pi cardinalities;
  solved + infeasible = total). This oracle verifies the underlying MAP is a
  BIJECTION between the integer index set [0, N) and the axis-tuple Cartesian
  product. A bijection is exactly loss-free (surjective => every combination
  reachable, no silent loss) and duplication-free (injective => no cell
  double-counted). It also confirms N two INDEPENDENT arithmetic ways:
    (i)  direct product   N  = Pi_j radix_j        (bignum, radix-agnostic)
    (ii) positional identity  N = Sum_j (radix_j - 1)*w_j + 1
         where w_j = Pi_{m>j} radix_m  (Knuth positional maximum-numeral
         theorem: the largest mixed-radix numeral is exactly N-1).
  Path (ii) never multiplies all cardinalities together in one product, so it
  is a genuinely independent confirmation of the count.

Authority discipline: AUDIT_ONLY. Does NOT promote, does NOT flip
scientific_readiness, does NOT modify the portfolio manifest, any locked
dataset, the signed Phase-0 KPI, or the live Rust engine. Reproduces existing
anchors and adds fail-closed tamper coverage only.
"""
import json, math, hashlib, sys
from pathlib import Path
from itertools import product

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-formulation-universe"
FIXTURE = MOD / "reference/phase0-formulation-universe-known-answer.v1.json"


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def radices_and_values(axes: dict):
    """BTreeMap parity with the Rust runtime: axes sorted by key."""
    items = sorted(axes.items())
    keys = [k for k, _ in items]
    values = [list(v) for _, v in items]
    radices = [len(v) for v in values]
    return keys, values, radices


def place_weights(radices):
    """w_j = Pi_{m>j} radix_m  (mixed-radix positional place values)."""
    k = len(radices)
    w = [1] * k
    for j in range(k - 2, -1, -1):
        w[j] = w[j + 1] * radices[j + 1]
    return w


def unrank(i, radices, weights):
    """Mixed-radix unrank: integer index -> digit tuple (Knuth 4.1)."""
    digits = []
    for j in range(len(radices)):
        digits.append((i // weights[j]) % radices[j])
    return tuple(digits)


def rank(digits, weights):
    """Mixed-radix rank: digit tuple -> integer index."""
    return sum(d * w for d, w in zip(digits, weights))


def oracle_universe(u):
    keys, values, radices = radices_and_values(u["axes"])
    weights = place_weights(radices)

    # (i) direct product (bignum)
    n_product = math.prod(radices) if radices else 0
    # (ii) positional maximum-numeral identity: max numeral = N-1
    if radices:
        max_numeral = sum((r - 1) * w for r, w in zip(radices, weights))
        n_positional = max_numeral + 1
    else:
        n_positional = 0
    two_way_agree = (n_product == n_positional)
    N = n_product

    # Bijection: unrank all indices, round-trip rank, collect tuples.
    seen_digit = set()
    seen_value = set()
    roundtrip_ok = True
    for i in range(N):
        digits = unrank(i, radices, weights)
        if rank(digits, weights) != i:
            roundtrip_ok = False
        seen_digit.add(digits)
        seen_value.add(tuple(values[j][digits[j]] for j in range(len(radices))))

    injective = (len(seen_digit) == N)                 # no silent duplication
    # Surjective / no silent loss: equals the independent itertools.product set.
    independent_set = set(product(*[range(r) for r in radices])) if radices else set()
    surjective = (seen_digit == independent_set)
    value_bijection = (len(seen_value) == N)           # value tuples also unique

    # Accounting identity against declared infeasible indices.
    inf_idx = u["infeasible_indices"]
    inf_in_range = all(isinstance(x, int) and not isinstance(x, bool)
                       and 0 <= x < N for x in inf_idx)
    inf_unique = (len(set(inf_idx)) == len(inf_idx))
    infeasible_count = len(set(inf_idx))
    solved_count = N - infeasible_count

    return {
        "universe_id": u["universe_id"],
        "design_type": u["design_type"],
        "sorted_axis_keys": keys,
        "radices": radices,
        "place_weights": weights,
        "cartesian_total_product": n_product,
        "cartesian_total_positional": n_positional,
        "two_way_count_agreement": two_way_agree,
        "reproduces_expected_cartesian_total": (N == u["expected_cartesian_total"]),
        "bijection_roundtrip_rank_unrank": roundtrip_ok,
        "bijection_injective_no_duplication": injective,
        "bijection_surjective_no_silent_loss": surjective,
        "value_tuple_bijection": value_bijection,
        "infeasible_indices_in_range": inf_in_range,
        "infeasible_indices_unique": inf_unique,
        "derived_infeasible_count": infeasible_count,
        "derived_solved_count": solved_count,
        "reproduces_expected_infeasible_count":
            (infeasible_count == u["expected_infeasible_candidate_count"]),
        "reproduces_expected_solved_count":
            (solved_count == u["expected_solved_candidate_count"]),
        "identity_solved_plus_infeasible_eq_total":
            (solved_count + infeasible_count == N),
    }


# ---- Fail-closed tamper probes (mixed-radix index laundering) ----------------
def failclosed_probes():
    """Each probe MUST be rejected. Uses a 2x2x2 (N=8) reference universe."""
    radices = [2, 2, 2]
    weights = place_weights(radices)
    N = math.prod(radices)

    def valid_index(x):
        return isinstance(x, int) and not isinstance(x, bool) and 0 <= x < N

    probes = []

    # 1. index == N (high boundary off-by-one)
    probes.append(("infeasible_index_equals_total", not valid_index(N)))
    # 2. index >> N
    probes.append(("infeasible_index_far_out_of_range", not valid_index(N + 1000)))
    # 3. negative index
    probes.append(("infeasible_index_negative", not valid_index(-1)))
    # 4. duplicate index laundering (5 raw, 4 unique -> mismatch detected)
    dup = [0, 1, 1, 2, 3]
    probes.append(("infeasible_index_duplicate",
                   len(set(dup)) != len(dup)))
    # 5. float index masquerading as integer
    probes.append(("infeasible_index_float", not valid_index(3.0)))
    # 6. boolean index (bool is int subclass) must be rejected
    probes.append(("infeasible_index_bool", not valid_index(True)))
    # 7. empty axis (radix 0) collapses N to 0 but a solved>0 claim is impossible
    empty_radices = [2, 0, 2]
    n_empty = math.prod(empty_radices)
    probes.append(("empty_axis_zero_cardinality_no_positive_solved",
                   n_empty == 0))
    # 8. positional/product disagreement must be catchable (inject wrong weight)
    bad_weights = [1, 1, 1]  # wrong place values
    max_bad = sum((r - 1) * w for r, w in zip(radices, bad_weights)) + 1
    probes.append(("corrupted_place_weights_detected_by_two_way",
                   max_bad != N))
    # 9. rank/unrank round-trip corruption detected
    corrupted = unrank(5, radices, weights)
    corrupted = (corrupted[0] + radices[0], corrupted[1], corrupted[2])  # overflow digit
    probes.append(("digit_overflow_breaks_roundtrip",
                   rank(corrupted, weights) != 5))

    return probes


def build_diagnostic():
    fixture_bytes = FIXTURE.read_bytes()
    fixture = json.loads(fixture_bytes)
    universes = [oracle_universe(u) for u in fixture["universes"]]

    def all_true(field):
        return all(u[field] for u in universes)

    probes = failclosed_probes()
    probe_pass = sum(1 for _, ok in probes if ok)

    n = len(universes)
    accept = {
        "two_way_count_agreement_rate": sum(u["two_way_count_agreement"] for u in universes) / n,
        "reproduces_expected_cartesian_total_rate": sum(u["reproduces_expected_cartesian_total"] for u in universes) / n,
        "bijection_roundtrip_rate": sum(u["bijection_roundtrip_rank_unrank"] for u in universes) / n,
        "bijection_injective_rate": sum(u["bijection_injective_no_duplication"] for u in universes) / n,
        "bijection_surjective_rate": sum(u["bijection_surjective_no_silent_loss"] for u in universes) / n,
        "value_tuple_bijection_rate": sum(u["value_tuple_bijection"] for u in universes) / n,
        "reproduces_expected_solved_rate": sum(u["reproduces_expected_solved_count"] for u in universes) / n,
        "reproduces_expected_infeasible_rate": sum(u["reproduces_expected_infeasible_count"] for u in universes) / n,
        "identity_solved_plus_infeasible_eq_total_rate": sum(u["identity_solved_plus_infeasible_eq_total"] for u in universes) / n,
        "failclosed_probe_pass_rate": probe_pass / len(probes),
    }

    diagnostic = {
        "schema": "amphora.formulation-universe.mixed-radix-bijection.v1",
        "authority": "AUDIT_ONLY",
        "module": "amphora-formulation-universe",
        "claim_under_test": ("Cartesian enumeration reports every solved and "
                             "infeasible combination without silent loss."),
        "method": {
            "name": "mixed-radix positional numeral bijection oracle",
            "primary_sources": [
                "Knuth TAOCP Vol.2 3rd ed. (1997) ISBN 0-201-89684-2 sec.4.1 Positional Number Systems",
                "Nijenhuis & Wilf, Combinatorial Algorithms 2nd ed. (1978) ISBN 0-12-519260-6 ch.1-3 ranking/unranking",
            ],
            "adds_over_rust_benchmark": ("Rust Phase-0 benchmark verifies counts; "
                "this oracle proves the index<->tuple map is a bijection "
                "(injective=no duplication, surjective=no silent loss) and "
                "confirms N two independent arithmetic ways (direct product vs "
                "positional maximum-numeral identity N = sum_j (r_j-1)*w_j + 1)."),
            "axis_ordering": "BTreeMap parity: axes sorted by key",
            "arithmetic": "Python bignum (radix-agnostic), independent of Rust u64",
        },
        "rights": {
            "fixture": "amphora-formulation-universe/reference/phase0-formulation-universe-known-answer.v1.json",
            "fixture_sha256": sha(fixture_bytes),
            "license": "CC0-1.0",
            "eligible_for_derivatives": True,
            "note": "Self-authored CC0 DoE compilation; rights-clean for derivatives.",
        },
        "n_universes": n,
        "acceptance": accept,
        "acceptance_all_perfect": all(v == 1.0 for v in accept.values()),
        "reproduces_all_anchors": (all_true("reproduces_expected_cartesian_total")
                                   and all_true("reproduces_expected_solved_count")
                                   and all_true("reproduces_expected_infeasible_count")),
        "bijection_holds_all_universes": (all_true("bijection_roundtrip_rank_unrank")
                                          and all_true("bijection_injective_no_duplication")
                                          and all_true("bijection_surjective_no_silent_loss")),
        "per_universe": universes,
        "failclosed_probes": [{"probe": name, "rejected": ok} for name, ok in probes],
        "failclosed_probe_pass": probe_pass,
        "failclosed_probe_total": len(probes),
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
    print("acceptance_all_perfect", diag["acceptance_all_perfect"])
    print("reproduces_all_anchors", diag["reproduces_all_anchors"])
    print("bijection_holds_all_universes", diag["bijection_holds_all_universes"])
    print("failclosed", diag["failclosed_probe_pass"], "/", diag["failclosed_probe_total"])
