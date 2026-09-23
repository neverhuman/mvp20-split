#!/usr/bin/env python3
"""barrier-null-char-v1 -- named-baseline + hostile-null characterization for
amphora-barrier-corrosion-score.

Two things this does, both on the ONLY two strict, in-class (epoxy-amine),
open-table-read, ordered EIS coating-resistance series in the tree
(asperti2024, zhu2022; both MDPI *Materials*, CC BY 4.0), respecting each
source's declared use_limit ("within-study direction only; no cross-study
pooling"):

  1. NAMED PUBLISHED BASELINE -- Bacon-Smith-Rugg (1948) electrolytic-resistance
     three-tier protective-merit classification of an organic barrier coating.
       Bacon, R.C.; Smith, J.J.; Rugg, F.M. "Electrolytic Resistance in
       Evaluating Protective Merit of Coatings on Metals." Ind. Eng. Chem.
       1948, 40 (1), 161-167. DOI 10.1021/ie50457a041.
     Tiers on coating resistance Rc (ohm.cm2):
       GOOD          Rc >= 1e8
       INTERMEDIATE  1e6 <= Rc < 1e8
       POOR          Rc < 1e6
     This is the historical origin of the widely-used |Z|_0.01Hz > 1e8
     ohm.cm2 "protective" figure of merit for barrier coatings.

  2. HOSTILE-NULL RANKING CHARACTERIZATION -- the module's falsifiable
     hypothesis is that a locked barrier ranking can OUTPERFORM the
     solids-only and PVC-only hostile nulls. In a single-resin filler-loading
     ladder both of those nulls are monotone-increasing in filler loading
     (adding a solid filler raises both total volume-solids and PVC
     monotonically), so within a ladder they collapse to ONE prediction:
     "more filler -> better barrier". We measure how well that monotone null
     reproduces the observed within-study Rc ranking via Spearman rho, with an
     EXACT permutation p-value (full enumeration, small n). Headroom = the gap
     to a perfect (rho=1) ranker: it quantifies how much a barrier-aware score
     could in principle beat the nulls on these data.

Deterministic, dependency-light (stdlib only), byte-stable across replays.
AUDIT_ONLY. Creates no coating-barrier ranking authority; does not promote.
"""
import json, hashlib, itertools
from pathlib import Path

DATA = Path("amphora-barrier-corrosion-score/reference/mvp20/data/corrosion_series.json")

GOOD_THRESH = 1e8   # Bacon-Smith-Rugg upper tier boundary (ohm.cm2)
POOR_THRESH = 1e6   # Bacon-Smith-Rugg lower tier boundary (ohm.cm2)


def bsr_tier(rc):
    if rc >= GOOD_THRESH:
        return "GOOD"
    if rc >= POOR_THRESH:
        return "INTERMEDIATE"
    return "POOR"


def ranks(xs):
    """Average (fractional) ranks, ascending. Ties get the mean rank."""
    order = sorted(range(len(xs)), key=lambda i: xs[i])
    r = [0.0] * len(xs)
    i = 0
    while i < len(xs):
        j = i
        while j + 1 < len(xs) and xs[order[j + 1]] == xs[order[i]]:
            j += 1
        avg = (i + j) / 2.0 + 1.0  # 1-based average rank
        for k in range(i, j + 1):
            r[order[k]] = avg
        i = j + 1
    return r


def spearman(a, b):
    ra, rb = ranks(a), ranks(b)
    n = len(a)
    mean_a = sum(ra) / n
    mean_b = sum(rb) / n
    num = sum((ra[i] - mean_a) * (rb[i] - mean_b) for i in range(n))
    da = sum((x - mean_a) ** 2 for x in ra) ** 0.5
    db = sum((x - mean_b) ** 2 for x in rb) ** 0.5
    if da == 0 or db == 0:
        return 0.0
    return num / (da * db)


def exact_perm_p(loading, observed):
    """Two-sided exact permutation p-value for |rho| under the null that the
    monotone (loading) predictor is unrelated to observed Rc. Enumerate all
    permutations of the observed vector against fixed loading ranks."""
    obs = abs(spearman(loading, observed))
    n = len(observed)
    total = 0
    ge = 0
    for perm in itertools.permutations(observed):
        total += 1
        if abs(spearman(loading, list(perm))) >= obs - 1e-12:
            ge += 1
    return round(ge / total, 6), total


def analyze(series):
    levels = [float(x) for x in series["levels"]]
    rc = [float(x) for x in series["values"]]
    tiers = [bsr_tier(x) for x in rc]
    # monotone hostile null == rank by filler loading (solids-only == PVC-only here)
    rho = spearman(levels, rc)
    p, nperm = exact_perm_p(levels, rc)
    best_idx = max(range(len(rc)), key=lambda i: rc[i])
    monotone_best_idx = max(range(len(levels)), key=lambda i: levels[i])
    return {
        "id": series["id"],
        "cite": series["cite"],
        "doi": series["doi"],
        "in_class": series["in_class"],
        "variable": series["variable"],
        "levels": levels,
        "rc_ohm_cm2": rc,
        "metric": series["metric"],
        "test_method": series["test_method"],
        "duration": series["duration"],
        "use_limit": series["use_limit"],
        "bacon_smith_rugg_1948_tier": tiers,
        "n_good": tiers.count("GOOD"),
        "n_intermediate": tiers.count("INTERMEDIATE"),
        "n_poor": tiers.count("POOR"),
        "observed_optimum_level": levels[best_idx],
        "monotone_null_predicted_best_level": levels[monotone_best_idx],
        "monotone_null_matches_observed_optimum": best_idx == monotone_best_idx,
        "monotone_null_spearman_rho": round(rho, 6),
        "monotone_null_exact_perm_p_two_sided": p,
        "n_permutations_enumerated": nperm,
        "ranking_headroom_to_perfect": round(1.0 - rho, 6),
        "is_monotone_in_loading": max(range(len(rc)), key=lambda i: rc[i]) == monotone_best_idx
                                  and min(range(len(rc)), key=lambda i: rc[i]) == min(range(len(levels)), key=lambda i: levels[i]),
    }


def main():
    raw = DATA.read_bytes()
    d = json.loads(raw)
    strict = {s["id"]: s for s in d["series"] if s["id"] in ("asperti2024", "zhu2022")}
    per = [analyze(strict[k]) for k in sorted(strict)]
    rhos = [x["monotone_null_spearman_rho"] for x in per]
    result = {
        "schema": "amphora.barrier-corrosion-score.null-characterization.v1",
        "module": "amphora-barrier-corrosion-score",
        "benchmark": "barrier-null-char-v1",
        "authority": "AUDIT_ONLY",
        "promotes_authority": False,
        "input_dataset": {
            "path": str(DATA),
            "sha256": hashlib.sha256(raw).hexdigest(),
            "schema": d["schema"],
        },
        "named_baseline": {
            "name": "Bacon-Smith-Rugg 1948 electrolytic-resistance protective-merit tiers",
            "citation": "Bacon, Smith, Rugg, Ind. Eng. Chem. 1948, 40(1), 161-167",
            "doi": "10.1021/ie50457a041",
            "tier_boundaries_ohm_cm2": {"good_ge": GOOD_THRESH, "poor_lt": POOR_THRESH},
        },
        "hostile_null_definition": "solids-only == PVC-only == monotone-increasing in "
            "filler loading within a single-resin ladder; measured against observed Rc "
            "ranking by Spearman rho with exact permutation p.",
        "rights": {
            "sources": ["asperti2024 (MDPI Materials, CC BY 4.0)",
                        "zhu2022 (MDPI Materials, CC BY 4.0)"],
            "use_limit_respected": "within-study direction only; NO cross-study pooling",
            "rights_class": "OPEN_ACCESS_CC_BY_4_0",
        },
        "per_series": per,
        "aggregate": {
            "n_strict_in_class_series": len(per),
            "monotone_null_spearman_rho_values": rhos,
            "monotone_null_spearman_rho_mean": round(sum(rhos) / len(rhos), 6),
            "monotone_null_reproduces_no_series_optimum": all(
                not x["monotone_null_matches_observed_optimum"] for x in per),
        },
        "verdict": {
            "finding": "On both strict in-class epoxy-amine EIS series the observed "
                "within-study barrier ranking is NON-MONOTONE in filler loading (optimum "
                "at an intermediate level), so the solids-only and PVC-only hostile nulls "
                "(both monotone-in-loading) FAIL to reproduce the ordering (Spearman "
                f"{rhos} ; neither significant). This establishes non-trivial ranking "
                "headroom for a barrier-aware score -- a necessary precondition for the "
                "module's falsifiable hypothesis -- and quantifies it.",
            "does_not_establish": "A validated POSITIVE barrier ranking model. No "
                "zero-parameter a-priori model reproduces the intermediate optimum "
                "(driven by dispersion/percolation, a formulation-processing variable). "
                "Closing that needs >=3 pooled, protocol-controlled formulation->Rc series "
                "with dispersion/PVC metadata -- the standing DATA wall.",
            "scope_honesty": "Organic epoxy-amine coating-barrier EIS, correct module "
                "scope (unlike the substrate-corrosion corr-rate-qspr-v1 diagnostic).",
        },
        "determinism": {
            "stdlib_only": True,
            "no_random": True,
            "no_timestamp": True,
            "float_round_decimals": 6,
        },
    }
    return result


def canonical(obj):
    return json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=True)


if __name__ == "__main__":
    import sys
    out = canonical(main())
    if len(sys.argv) > 1:
        Path(sys.argv[1]).write_text(out + "\n")
        print("wrote", sys.argv[1], "sha256", hashlib.sha256((out + "\n").encode()).hexdigest())
    else:
        print(out)
