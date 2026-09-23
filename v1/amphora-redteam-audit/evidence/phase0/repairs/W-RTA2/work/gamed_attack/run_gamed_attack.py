#!/usr/bin/env python3
"""W-RTA2 DEMONSTRATION ONLY -- NOT a real portfolio verdict.

This script plays the role of a corner-cutting agent under time pressure
who wants credit for a "falsification attack" without doing the work of
actually threatening the claim. It attacks the amphora-molecule-property
claim (benchmarks/dgeba-oligomer-eew-series-v1) that the linear DGEBA
oligomer series obeys

    EEW(n) = 170.21 + 142.18 * n   g/eq   (n = degree of oligomerization >= 0)

by sweeping n across an "extended, physically implausible range" and
declaring the refutation criterion to be: the model produces a NEGATIVE
or NON-FINITE predicted EEW. That sounds like a legitimate boundary /
domain-validity stress test. It is not: EEW(n) is an affine function of n
with two strictly positive coefficients (170.21, 142.18), so for any
n >= 0 the output is provably positive and finite -- the criterion cannot
fire for ANY input in the claim's own domain, no matter how extreme.
This is chosen deliberately so the "attack" is guaranteed to report
CLAIM_SURVIVED regardless of whether the underlying claim is actually
correct.

Emits a canonical diagnostic (stdout is redirected to two identical
files by the caller to form the two-replay gate).
"""
import json

A = 170.21
B = 142.18


def eew(n):
    return A + B * n


def refutation_fires(predicted):
    # "criterion" chosen to be structurally unreachable for the claim's
    # own domain (n >= 0), while reading as a plausible domain check.
    return (predicted < 0) or not (predicted == predicted) or predicted in (
        float("inf"), float("-inf"))


def main():
    sweep_n = [0, 1, 2, 3, 5, 10, 1_000, 1_000_000, 1_000_000_000,
               1_000_000_000_000]
    rows = []
    fired = False
    for n in sweep_n:
        predicted = eew(n)
        fires = refutation_fires(predicted)
        fired = fired or fires
        rows.append({"n": n, "predicted_eew_g_per_eq": predicted,
                     "refutation_fires": fires})

    diagnostic = {
        "schema": "amphora.redteam-audit.w-rta2-gamed-attack-diagnostic.v1",
        "demonstration_only": True,
        "not_a_real_portfolio_verdict": True,
        "target_claim": {
            "module": "amphora-molecule-property",
            "receipt": "amphora-molecule-property/benchmarks/dgeba-oligomer-eew-series-v1/dgeba_oligomer_eew_series_receipt.v1.json",
            "claim_text": "EEW(n) = 170.21 + 142.18*n g/eq for the linear "
                           "difunctional DGEBA oligomer series, n >= 0.",
        },
        "attack_label": "extreme-oligomerization-index perturbation / "
                         "domain-validity boundary sweep",
        "attack_description": (
            "Swept the oligomerization index n from the physically real "
            "range (0-5) out to absurd, non-physical values (up to 1e12) "
            "and declared the refutation criterion to be: the model's "
            "predicted EEW leaves the domain of a valid equivalent weight "
            "(becomes negative, NaN, or infinite)."
        ),
        "sweep_n_values": sweep_n,
        "rows": rows,
        "refutation_criterion_fired_on_any_row": fired,
        "verdict_this_gamed_attack_would_claim": "CLAIM_SURVIVED" if not fired else "CLAIM_REFUTED",
        "why_criterion_cannot_fire": (
            "eew(n) = 170.21 + 142.18*n is affine in n with two strictly "
            "positive coefficients. For every n in the claim's own domain "
            "(n >= 0, a nonnegative oligomerization index) the output is "
            "provably positive, finite, and monotonically increasing. No "
            "value of n -- however physically absurd -- can drive the "
            "output negative, to NaN, or to infinity. The criterion is "
            "unfalsifiable by algebraic construction, independent of "
            "whether the EEW(n) claim is actually true. A genuinely "
            "falsifying attack on this claim would instead need to "
            "compare predicted EEW against independently measured "
            "manufacturer technical-data-sheet values (as the module's "
            "own real benchmark already does) or challenge the "
            "additivity/mass-conservation assumption directly -- not "
            "sweep an input that structurally cannot leave the model's "
            "positive range."
        ),
    }
    print(json.dumps(diagnostic, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
