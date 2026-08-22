#!/usr/bin/env python3
"""AUDIT_ONLY mixture-geometry oracle for amphora-formulation-universe.

Claim under test
----------------
The module's Phase-0 capability is *Cartesian* (mixed-radix factorial)
accounting over categorical/level axes. A coating formulation is physically a
MIXTURE: component weight fractions are closed (sum(x) = 1) with per-component
lower/upper bounds. The feasible set is therefore a bounded convex polytope
inside the (q-1)-simplex, NOT a Cartesian box. This oracle implements the
published mixture-design geometry and quantifies the mismatch.

Published baselines
-------------------
  Scheffe 1958, JRSS-B 20(2):344-360, doi:10.1111/j.2517-6161.1958.tb00299.x
      simplex-lattice {q,m}; |{q,m}| = C(q+m-1, m); canonical polynomial;
      saturation of {q,m} for the degree-m canonical polynomial.
  Scheffe 1963, JRSS-B 25(2):235-263, doi:10.1111/j.2517-6161.1963.tb00506.x
      simplex-centroid design; 2^q - 1 points.
  McLean & Anderson 1966, Technometrics 8(3):447-454,
      doi:10.1080/00401706.1966.10490377 -- extreme-vertices generator.
  Snee & Marquardt 1974, Technometrics 16(3):399-408,
      doi:10.1080/00401706.1974.10489209 -- McLean-Anderson over-generation.
  Piepel 1983, Technometrics 25(1):97-101,
      doi:10.1080/00401706.1983.10487825 -- consistency + implied bounds.
  Motzkin, Raiffa, Thompson & Thrall 1953, "The Double Description Method",
      Annals of Math. Studies 28, ISBN 978-0-691-07935-6 -- independent
      vertex-enumeration path used as the parity oracle.
  Cornell 2002, "Experiments with Mixtures" 3rd ed., ISBN 0-471-07916-2.

Authority: AUDIT_ONLY. Pure exact-rational arithmetic (fractions.Fraction);
no floating-point in any decision, no randomness, no network, no dependency on
the live Rust engine. Does not promote authority, does not flip
scientific_readiness, does not modify the portfolio manifest (66 receipts / 11
modules), any locked dataset, or the signed Phase-0 KPI.
"""

import itertools
import json
import math
import sys
from fractions import Fraction
from pathlib import Path

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MODULE = ROOT / "amphora-formulation-universe"
ANCHORS = MODULE / "reference/mvp20/data/formulation_mixture_region_anchors.v1.json"

# ---------------------------------------------------------------- utilities

def F(s):
    """Exact Fraction from a decimal string (never from float)."""
    if not isinstance(s, str):
        raise TypeError("bounds must be decimal strings")
    return Fraction(s)


def fs(x):
    """Canonical string form of an exact rational."""
    return f"{x.numerator}/{x.denominator}"


def vecs(v):
    return [fs(c) for c in v]


def comb(n, k):
    return math.comb(n, k)


def det_exact(mat):
    """Exact rational determinant by fraction-free-free Gaussian elimination."""
    n = len(mat)
    a = [row[:] for row in mat]
    det = Fraction(1)
    for c in range(n):
        piv = None
        for r in range(c, n):
            if a[r][c] != 0:
                piv = r
                break
        if piv is None:
            return Fraction(0)
        if piv != c:
            a[c], a[piv] = a[piv], a[c]
            det = -det
        det *= a[c][c]
        inv = Fraction(1) / a[c][c]
        for r in range(c + 1, n):
            if a[r][c] == 0:
                continue
            f = a[r][c] * inv
            for k in range(c, n):
                a[r][k] -= f * a[c][k]
    return det


# ------------------------------------------------- Scheffe simplex designs

def compositions(m, q):
    """All weak compositions of integer m into q parts, lexicographic."""
    if q == 1:
        yield (m,)
        return
    for first in range(m + 1):
        for rest in compositions(m - first, q - 1):
            yield (first,) + rest


def simplex_lattice(q, m):
    """Scheffe 1958 {q,m} simplex-lattice points as exact rationals."""
    if q < 2:
        raise ValueError("simplex-lattice requires q >= 2 components")
    if m < 1:
        raise ValueError("simplex-lattice requires degree m >= 1")
    pts = [tuple(Fraction(a, m) for a in c) for c in compositions(m, q)]
    return sorted(pts)


def simplex_centroid(q):
    """Scheffe 1963 simplex-centroid points as exact rationals."""
    if q < 2:
        raise ValueError("simplex-centroid requires q >= 2 components")
    pts = []
    idx = range(q)
    for r in range(1, q + 1):
        for S in itertools.combinations(idx, r):
            v = [Fraction(0)] * q
            for i in S:
                v[i] = Fraction(1, r)
            pts.append(tuple(v))
    return sorted(pts)


def canonical_terms(q, degree):
    """Scheffe canonical polynomial term list (as callables on x)."""
    terms = []
    for i in range(q):
        terms.append(("linear", (i,)))
    if degree >= 2:
        for i, j in itertools.combinations(range(q), 2):
            terms.append(("quad", (i, j)))
    if degree == 3:
        for i, j in itertools.combinations(range(q), 2):
            terms.append(("delta", (i, j)))
        for i, j, k in itertools.combinations(range(q), 3):
            terms.append(("ternary", (i, j, k)))
    return terms


def term_value(term, x):
    kind, idx = term
    if kind == "linear":
        return x[idx[0]]
    if kind == "quad":
        return x[idx[0]] * x[idx[1]]
    if kind == "delta":
        return x[idx[0]] * x[idx[1]] * (x[idx[0]] - x[idx[1]])
    if kind == "ternary":
        return x[idx[0]] * x[idx[1]] * x[idx[2]]
    raise ValueError(kind)


def special_cubic_term_count(q):
    return q + comb(q, 2) + comb(q, 3)


# ------------------------------------------- constrained mixture polytope

class BoundError(ValueError):
    pass


def validate_region(components, lower, upper):
    """Fail-closed validation of a constrained mixture region (Piepel 1983)."""
    if not isinstance(components, list) or not isinstance(lower, list) \
       or not isinstance(upper, list):
        raise BoundError("components/lower/upper must be lists")
    q = len(components)
    if q < 2:
        raise BoundError("a mixture region requires q >= 2 components")
    if len(lower) != q or len(upper) != q:
        raise BoundError("bound vector length mismatch")
    if len(set(components)) != q:
        raise BoundError("duplicate component name")
    lo, up = [], []
    for s in lower + upper:
        if not isinstance(s, str):
            raise BoundError("bounds must be decimal strings")
        t = s.strip().lower()
        if t in ("nan", "inf", "-inf", "+inf", ""):
            raise BoundError("non-finite bound")
        try:
            Fraction(s)
        except Exception:
            raise BoundError("non-numeric bound")
    lo = [F(s) for s in lower]
    up = [F(s) for s in upper]
    for i in range(q):
        if lo[i] < 0:
            raise BoundError("negative lower bound")
        if up[i] > 1:
            raise BoundError("upper bound exceeds unity")
        if lo[i] > up[i]:
            raise BoundError("lower bound exceeds upper bound")
    if sum(lo) > 1:
        raise BoundError("inconsistent region: sum(lower) > 1")
    if sum(up) < 1:
        raise BoundError("inconsistent region: sum(upper) < 1")
    return lo, up


def implied_bounds(lo, up):
    """Piepel 1983 implied (consistent) bounds."""
    q = len(lo)
    su, sl = sum(up), sum(lo)
    li = [max(lo[i], 1 - (su - up[i])) for i in range(q)]
    ui = [min(up[i], 1 - (sl - lo[i])) for i in range(q)]
    return li, ui


def is_vertex(x, lo, up):
    """A point of {x: sum(x)=1, lo<=x<=up} is an extreme point iff at least
    q-1 coordinates sit on a declared bound (the free face then has dim <= 0)."""
    q = len(x)
    active = sum(1 for i in range(q) if x[i] == lo[i] or x[i] == up[i])
    return active >= q - 1


def feasible(x, lo, up):
    return all(lo[i] <= x[i] <= up[i] for i in range(len(x))) and sum(x) == 1


def mclean_anderson(lo, up):
    """McLean & Anderson 1966 extreme-vertices generator: put q-1 components at
    bound levels, fill the remaining component by difference, discard
    out-of-bound fills. Returns (raw_candidates, screened_vertices)."""
    q = len(lo)
    raw = set()
    for k in range(q):                       # component filled by difference
        others = [i for i in range(q) if i != k]
        for assign in itertools.product((0, 1), repeat=q - 1):
            x = [None] * q
            for pos, i in enumerate(others):
                x[i] = up[i] if assign[pos] else lo[i]
            x[k] = 1 - sum(x[i] for i in others)
            if lo[k] <= x[k] <= up[k]:
                raw.add(tuple(x))
    screened = {x for x in raw if is_vertex(x, lo, up)}
    return sorted(raw), sorted(screened)


def double_description(lo, up):
    """Independent vertex enumeration (Motzkin et al. 1953): start from the
    vertices of the unit simplex and cut with one box half-space at a time."""
    q = len(lo)
    cur_lo = [Fraction(0)] * q
    cur_up = [Fraction(1)] * q
    V = []
    for i in range(q):
        v = [Fraction(0)] * q
        v[i] = Fraction(1)
        V.append(tuple(v))
    V = sorted(set(V))

    cuts = []
    for i in range(q):
        if lo[i] > 0:
            cuts.append((i, "lower", lo[i]))
        if up[i] < 1:
            cuts.append((i, "upper", up[i]))

    for (i, side, b) in cuts:
        # signed constraint value g(x) <= 0
        if side == "upper":
            g = lambda x, i=i, b=b: x[i] - b
        else:
            g = lambda x, i=i, b=b: b - x[i]
        Vp = [v for v in V if g(v) > 0]
        V0 = [v for v in V if g(v) == 0]
        Vm = [v for v in V if g(v) < 0]
        new = set(V0) | set(Vm)
        for p in Vp:
            for n in Vm:
                gp, gn = g(p), g(n)
                t = gn / (gn - gp)            # in (0,1)
                z = tuple(n[k] + t * (p[k] - n[k]) for k in range(q))
                new.add(z)
        if side == "upper":
            cur_up[i] = min(cur_up[i], b)
        else:
            cur_lo[i] = max(cur_lo[i], b)
        V = sorted(z for z in new
                   if all(cur_lo[k] <= z[k] <= cur_up[k] for k in range(q))
                   and sum(z) == 1
                   and is_vertex(z, cur_lo, cur_up))
    # final screen against the declared bounds
    return sorted(z for z in V if feasible(z, lo, up) and is_vertex(z, lo, up))


# ----------------------------------------------------------------- gates

def gate_lattice_counts(anchors):
    cases = []
    ok = True
    for a in anchors["closed_form_anchors"]["simplex_lattice_points"]:
        q, m = a["q"], a["m"]
        pts = simplex_lattice(q, m)
        closed = comb(q + m - 1, m)
        distinct = len(set(pts))
        on_simplex = all(sum(p) == 1 for p in pts)
        agree = (len(pts) == closed == distinct == a["expected_points"]) and on_simplex
        ok &= agree
        cases.append({
            "q": q, "m": m,
            "expected_points_anchor": a["expected_points"],
            "closed_form_C(q+m-1,m)": closed,
            "enumerated_points": len(pts),
            "distinct_points": distinct,
            "all_points_close_to_unity": on_simplex,
            "agree": agree,
        })
    return {"gate_id": "G1_scheffe1958_simplex_lattice_point_count",
            "source": "Scheffe 1958 doi:10.1111/j.2517-6161.1958.tb00299.x",
            "cases": cases, "pass": ok}


def gate_saturation():
    cases = []
    ok = True
    for (q, m) in [(3, 1), (4, 1), (5, 1), (3, 2), (4, 2), (5, 2), (6, 2),
                   (3, 3), (4, 3), (5, 3)]:
        pts = simplex_lattice(q, m)
        terms = canonical_terms(q, m)
        square = (len(pts) == len(terms))
        det = None
        nonsingular = False
        if square:
            X = [[term_value(t, x) for t in terms] for x in pts]
            det = det_exact(X)
            nonsingular = (det != 0)
        agree = square and nonsingular
        ok &= agree
        cases.append({
            "q": q, "degree_m": m,
            "lattice_points": len(pts),
            "canonical_terms": len(terms),
            "closed_form_terms_C(q+m-1,m)": comb(q + m - 1, m),
            "model_matrix_square": square,
            "exact_determinant": fs(det) if det is not None else None,
            "nonsingular": nonsingular,
            "saturated": agree,
        })
    return {"gate_id": "G2_scheffe1958_canonical_saturation",
            "claim": ("the {q,m} simplex-lattice is saturated for the degree-m "
                      "Scheffe canonical polynomial: the model matrix is square "
                      "and exactly nonsingular over the rationals"),
            "cases": cases, "pass": ok}


def gate_centroid(anchors):
    cases = []
    ok = True
    for a in anchors["closed_form_anchors"]["simplex_centroid_points"]:
        q = a["q"]
        pts = simplex_centroid(q)
        closed = 2 ** q - 1
        distinct = len(set(pts))
        agree = (len(pts) == closed == distinct == a["expected_points"]
                 and all(sum(p) == 1 for p in pts))
        ok &= agree
        cases.append({"q": q, "expected_points_anchor": a["expected_points"],
                      "closed_form_2^q-1": closed,
                      "enumerated_points": len(pts),
                      "distinct_points": distinct, "agree": agree})
    return {"gate_id": "G3_scheffe1963_simplex_centroid_point_count",
            "source": "Scheffe 1963 doi:10.1111/j.2517-6161.1963.tb00506.x",
            "cases": cases, "pass": ok}


def gate_term_counts(anchors):
    cases = []
    ok = True
    for a in anchors["closed_form_anchors"]["canonical_polynomial_terms"]:
        q, deg = a["q"], a["degree"]
        if deg == "linear":
            n = len(canonical_terms(q, 1))
        elif deg == "quadratic":
            n = len(canonical_terms(q, 2))
        elif deg == "full_cubic":
            n = len(canonical_terms(q, 3))
        elif deg == "special_cubic":
            n = special_cubic_term_count(q)
        agree = (n == a["expected_terms"])
        ok &= agree
        cases.append({"q": q, "degree": deg,
                      "expected_terms_anchor": a["expected_terms"],
                      "enumerated_terms": n, "agree": agree})
    return {"gate_id": "G4_scheffe_canonical_term_count",
            "source": "Scheffe 1958 / Cornell 2002 ISBN 0-471-07916-2",
            "cases": cases, "pass": ok}


def gate_cartesian_closure(anchors):
    """Bridge to the module's existing mixed-radix Cartesian oracle: brute-force
    filter the (m+1)^q Cartesian grid by the closure constraint and show the
    survivors are exactly the Scheffe {q,m} lattice."""
    cases = []
    ok = True
    ceiling = anchors["cartesian_closure_cases"]["module_cardinality_ceiling"]
    for c in anchors["cartesian_closure_cases"]["cases"]:
        q, m = c["q"], c["m"]
        grid_total = (m + 1) ** q
        survivors = 0
        for tup in itertools.product(range(m + 1), repeat=q):
            if sum(tup) == m:
                survivors += 1
        closed = comb(q + m - 1, m)
        lattice = simplex_lattice(q, m)
        agree = (survivors == closed == len(lattice))
        ok &= agree
        frac = Fraction(survivors, grid_total)
        cases.append({
            "q": q, "grid_steps_m": m,
            "cartesian_grid_points": grid_total,
            "closure_feasible_points": survivors,
            "scheffe_lattice_points": len(lattice),
            "closed_form_C(q+m-1,m)": closed,
            "closure_feasible_fraction_exact": fs(frac),
            "closure_feasible_percent": round(float(frac) * 100.0, 6),
            "cartesian_exceeds_module_ceiling": grid_total > ceiling,
            "lattice_exceeds_module_ceiling": closed > ceiling,
            "agree": agree,
        })
    worst = min(cases, key=lambda c: c["closure_feasible_percent"])
    rescued = [c for c in cases if c["cartesian_exceeds_module_ceiling"]
               and not c["lattice_exceeds_module_ceiling"]]
    return {
        "gate_id": "G5_cartesian_closure_waste_vs_scheffe_lattice",
        "claim": ("mixed-radix Cartesian enumeration over q closed composition "
                  "axes is a strict superset of the mixture-feasible set; the "
                  "closure-feasible survivors are exactly the Scheffe {q,m} "
                  "simplex-lattice"),
        "cases": cases,
        "module_cardinality_ceiling": ceiling,
        "worst_case_closure_feasible_percent": worst["closure_feasible_percent"],
        "worst_case": {"q": worst["q"], "m": worst["grid_steps_m"]},
        "cases_where_lattice_fits_ceiling_but_cartesian_does_not": len(rescued),
        "pass": ok,
    }


def gate_extreme_vertices(anchors):
    cases = []
    ok = True
    ma_overgeneration_seen = False
    for r in anchors["coating_mixture_regions"]:
        lo, up = validate_region(r["components"], r["lower"], r["upper"])
        q = len(lo)
        raw, ma = mclean_anderson(lo, up)
        dd = double_description(lo, up)
        parity = (set(ma) == set(dd))
        # Piepel 1983 implied bounds vs the exact attained range over vertices
        li, ui = implied_bounds(lo, up)
        obs_lo = [min(v[i] for v in dd) for i in range(q)]
        obs_up = [max(v[i] for v in dd) for i in range(q)]
        piepel_ok = (obs_lo == li and obs_up == ui)
        tightened_lower = sum(1 for i in range(q) if li[i] > lo[i])
        tightened_upper = sum(1 for i in range(q) if ui[i] < up[i])
        all_feasible = all(feasible(v, lo, up) for v in dd)
        all_extreme = all(is_vertex(v, lo, up) for v in dd)
        distinct = (len(set(dd)) == len(dd))
        agree = parity and piepel_ok and all_feasible and all_extreme and distinct
        ok &= agree
        if len(raw) > len(ma):
            ma_overgeneration_seen = True
        cases.append({
            "region_id": r["region_id"],
            "q": q,
            "components": r["components"],
            "lower": vecs(lo), "upper": vecs(up),
            "sum_lower": fs(sum(lo)), "sum_upper": fs(sum(up)),
            "consistent_piepel1983": True,
            "mclean_anderson_raw_candidates": len(raw),
            "mclean_anderson_screened_vertices": len(ma),
            "mclean_anderson_nonvertex_candidates": len(raw) - len(ma),
            "double_description_vertices": len(dd),
            "method_parity_MA_vs_DD": parity,
            "piepel_implied_lower": vecs(li),
            "piepel_implied_upper": vecs(ui),
            "observed_vertex_range_lower": vecs(obs_lo),
            "observed_vertex_range_upper": vecs(obs_up),
            "piepel_range_identity_holds": piepel_ok,
            "declared_lower_bounds_tightened": tightened_lower,
            "declared_upper_bounds_tightened": tightened_upper,
            "all_vertices_feasible": all_feasible,
            "all_vertices_extreme": all_extreme,
            "vertices_distinct": distinct,
            "vertices": [vecs(v) for v in dd],
            "agree": agree,
        })
    return {
        "gate_id": "G6_extreme_vertices_dual_method_parity_and_piepel_range",
        "sources": ["McLean & Anderson 1966 doi:10.1080/00401706.1966.10490377",
                    "Snee & Marquardt 1974 doi:10.1080/00401706.1974.10489209",
                    "Piepel 1983 doi:10.1080/00401706.1983.10487825",
                    "Motzkin et al. 1953 ISBN 978-0-691-07935-6"],
        "cases": cases,
        "mclean_anderson_overgeneration_observed": ma_overgeneration_seen,
        "mclean_anderson_nonvertex_candidates_total":
            sum(c["mclean_anderson_nonvertex_candidates"] for c in cases),
        "mclean_anderson_overgeneration_corollary": (
            "Not a failed reproduction: with single-component (box) bounds only, "
            "every McLean-Anderson candidate pins q-1 components to a declared "
            "bound and is therefore necessarily an extreme point of "
            "{x: sum(x)=1, l<=x<=u}. The Snee & Marquardt 1974 over-generation "
            "caveat is vacuous for box-only regions and can only bite once "
            "additional multi-component linear constraints (e.g. a "
            "pigment-volume-concentration or amine-hydrogen:epoxide equivalent "
            "ratio band) are imposed. Observed: 0 non-vertex candidates across "
            "all regions, exactly as the corollary predicts."),
        "pass": ok,
    }


# ----------------------------------------------------------- fail-closed

def probe(fn):
    try:
        fn()
    except (BoundError, ValueError, TypeError) as e:
        return True, type(e).__name__ + ": " + str(e)
    return False, "ACCEPTED (leak)"


def failclosed_probes():
    P = []

    def mk(comp, lo, up):
        return lambda: validate_region(comp, lo, up)

    specs = [
        ("sum_lower_exceeds_one",
         mk(["a", "b", "c"], ["0.60", "0.30", "0.20"], ["0.90", "0.50", "0.40"])),
        ("sum_upper_below_one",
         mk(["a", "b", "c"], ["0.10", "0.05", "0.05"], ["0.30", "0.20", "0.20"])),
        ("lower_exceeds_upper",
         mk(["a", "b", "c"], ["0.60", "0.30", "0.05"], ["0.50", "0.40", "0.30"])),
        ("negative_lower_bound",
         mk(["a", "b", "c"], ["-0.10", "0.30", "0.05"], ["0.50", "0.40", "0.30"])),
        ("upper_exceeds_one",
         mk(["a", "b", "c"], ["0.10", "0.30", "0.05"], ["1.20", "0.40", "0.30"])),
        ("single_component_region",
         mk(["a"], ["0.10"], ["1.00"])),
        ("non_numeric_bound",
         mk(["a", "b", "c"], ["low", "0.30", "0.05"], ["0.50", "0.40", "0.30"])),
        ("duplicate_component_name",
         mk(["a", "a", "c"], ["0.10", "0.30", "0.05"], ["0.50", "0.40", "0.30"])),
        ("nan_bound",
         mk(["a", "b", "c"], ["NaN", "0.30", "0.05"], ["0.50", "0.40", "0.30"])),
        ("bound_vector_length_mismatch",
         mk(["a", "b", "c"], ["0.10", "0.30"], ["0.50", "0.40", "0.30"])),
        ("lattice_degree_zero", lambda: simplex_lattice(3, 0)),
        ("lattice_single_component", lambda: simplex_lattice(1, 3)),
    ]
    for pid, fn in specs:
        rejected, detail = probe(fn)
        P.append({"probe_id": pid, "expected": "REJECT",
                  "rejected": rejected, "detail": detail})
    return P


# ---------------------------------------------------------------- driver

def main(out_path):
    anchors_bytes = ANCHORS.read_bytes()
    anchors = json.loads(anchors_bytes)
    import hashlib
    anchors_sha = hashlib.sha256(anchors_bytes).hexdigest()

    gates = [
        gate_lattice_counts(anchors),
        gate_saturation(),
        gate_centroid(anchors),
        gate_term_counts(anchors),
        gate_cartesian_closure(anchors),
        gate_extreme_vertices(anchors),
    ]
    probes = failclosed_probes()
    gates_pass = sum(1 for g in gates if g["pass"])
    probe_pass = sum(1 for p in probes if p["rejected"])

    ev = next(g for g in gates if g["gate_id"].startswith("G6"))
    cc = next(g for g in gates if g["gate_id"].startswith("G5"))

    diag = {
        "schema": "amphora.formulation-universe.simplex-mixture-geometry-diagnostic.v1",
        "module": "amphora-formulation-universe",
        "authority": "AUDIT_ONLY",
        "axis": "THEORY",
        "toolkit": {"python": ".".join(str(x) for x in sys.version_info[:3]),
                    "arithmetic": "exact rational (fractions.Fraction); no float in any decision",
                    "randomness": "none", "network": "none"},
        "anchor_dataset": {
            "path": "amphora-formulation-universe/reference/mvp20/data/formulation_mixture_region_anchors.v1.json",
            "sha256": anchors_sha,
            "license": anchors["rights"]["license"],
            "rights_status": anchors["rights"]["status"],
        },
        "gates": gates,
        "gates_pass": gates_pass,
        "gates_total": len(gates),
        "failclosed_probes": probes,
        "failclosed_probe_pass": probe_pass,
        "failclosed_probe_total": len(probes),
        "headline": {
            "scheffe_lattice_counts_reproduced": gates[0]["pass"],
            "canonical_saturation_exact_nonsingular": gates[1]["pass"],
            "simplex_centroid_counts_reproduced": gates[2]["pass"],
            "canonical_term_counts_reproduced": gates[3]["pass"],
            "cartesian_closure_superset_quantified": gates[4]["pass"],
            "worst_case_closure_feasible_percent": cc["worst_case_closure_feasible_percent"],
            "worst_case_qm": cc["worst_case"],
            "cases_where_lattice_fits_module_ceiling_but_cartesian_does_not":
                cc["cases_where_lattice_fits_ceiling_but_cartesian_does_not"],
            "extreme_vertex_dual_method_parity": gates[5]["pass"],
            "mclean_anderson_nonvertex_candidates_total":
                ev["mclean_anderson_nonvertex_candidates_total"],
            "mclean_anderson_overgeneration_observed":
                ev["mclean_anderson_overgeneration_observed"],
            "regions_evaluated": len(ev["cases"]),
            "total_extreme_vertices": sum(c["double_description_vertices"]
                                          for c in ev["cases"]),
        },
        "acceptance_all_perfect": (gates_pass == len(gates)
                                   and probe_pass == len(probes)),
        "interpretation": (
            "The Phase-0 Cartesian (mixed-radix) universe is the correct model "
            "for CATEGORICAL formulation axes but is a strict, and severely "
            "wasteful, superset once composition axes are closed (sum(x)=1). "
            "Filtering the Cartesian grid by closure reproduces the Scheffe "
            "{q,m} simplex-lattice exactly, so the lattice generator is a "
            "loss-free replacement at a small fraction of the cardinality. For "
            "bounded coating regions the extreme-vertex set is confirmed by two "
            "independent published algorithms and pinned by the Piepel 1983 "
            "implied-bound range identity."),
        "does_not": [
            "promote authority or flip scientific_readiness",
            "modify the portfolio manifest (66 receipts / 11 modules)",
            "modify any locked dataset or the signed Phase-0 KPI",
            "modify the live Rust engine",
        ],
    }
    Path(out_path).write_text(json.dumps(diag, indent=2, sort_keys=True))
    print("WROTE", out_path)
    print("gates", gates_pass, "/", len(gates),
          "probes", probe_pass, "/", len(probes),
          "acceptance_all_perfect", diag["acceptance_all_perfect"])


if __name__ == "__main__":
    main(sys.argv[1])
