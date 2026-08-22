#!/usr/bin/env python3
"""AUDIT_ONLY multicomponent-constraint polytope oracle for
amphora-formulation-universe.

Claim under test
----------------
The prior simplex-mixture-geometry increment certified box-bounded mixture
regions (sum(x)=1, l <= x <= u) and honestly reported that the Snee-Marquardt
1974 over-generation caveat did NOT fire: with box-only bounds every screened
McLean-Anderson candidate is necessarily an extreme point, and the MA candidate
set is vertex-complete. Real coating windows are NOT box-only: a pigment
volume concentration (PVC) band (Asbeck & Van Loo 1949) and an
amine-H:epoxide stoichiometric-ratio band (Lee & Neville 1967) are RATIO
constraints that linearize to multicomponent linear constraints on the weight
fractions. This oracle implements the published multicomponent-constraint
mixture geometry (Snee 1979; Piepel 1988 CONVRT/CONAEV) and tests

  H0: the McLean-Anderson candidate set remains vertex-complete once
      multicomponent linear constraints are added.

Published baselines
-------------------
  Snee, R.D. (1979) Experimental designs for mixture systems with
      multicomponent constraints, Commun. Stat. Theory Methods A8(4):303-326,
      doi:10.1080/03610927908827762 -- extreme vertices of linearly
      constrained mixture regions.
  Piepel, G.F. (1988) Programs for generating extreme vertices and centroids
      of linearly constrained experimental regions, J. Qual. Technol.
      20(2):125-136, doi:10.1080/00224065.1988.11979094 -- CONVRT vertex /
      CONAEV centroid definitions (face centroid = average of the vertices on
      the face).
  Snee, R.D. & Marquardt, D.W. (1974) Extreme vertices designs for linear
      mixture models, Technometrics 16(3):399-408,
      doi:10.1080/00401706.1974.10489209 -- inadequacy of bound-only
      candidate generation under linear mixture constraints.
  Motzkin, Raiffa, Thompson & Thrall (1953) The Double Description Method,
      Annals of Math. Studies 28, ISBN 978-0-691-07935-6 -- sequential
      half-space cutting; independent vertex-enumeration parity path.
  McLean, R.A. & Anderson, V.L. (1966) Technometrics 8(3):447-454,
      doi:10.1080/00401706.1966.10490377 -- bound-only candidate generator
      under test.
  Asbeck, W.K. & Van Loo, M. (1949) Ind. Eng. Chem. 41(7):1470-1475,
      doi:10.1021/ie50475a042 -- pigment volume concentration.
  Lee, H. & Neville, K. (1967) Handbook of Epoxy Resins, McGraw-Hill,
      ISBN 978-0-07-036997-9 -- amine-H:epoxide stoichiometric index.
  Cornell, J.A. (2002) Experiments with Mixtures, 3rd ed., Wiley,
      ISBN 0-471-07916-2 -- ratio constraints on mixture components.

Authority: AUDIT_ONLY. Pure exact-rational arithmetic (fractions.Fraction);
no floating-point in any decision, no randomness, no network, no dependency on
the live Rust engine. Does not promote authority, does not flip
scientific_readiness, does not modify the portfolio manifest (66 receipts / 11
modules), any locked dataset, or the signed Phase-0 KPI.
"""

import hashlib
import itertools
import json
import sys
from fractions import Fraction
from pathlib import Path

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MODULE = ROOT / "amphora-formulation-universe"
ANCHORS = MODULE / ("reference/mvp20/data/"
                    "formulation_multicomponent_constraint_anchors.v1.json")

# ---------------------------------------------------------------- utilities


def F(s):
    """Exact Fraction from a decimal string (never from float)."""
    if not isinstance(s, str):
        raise TypeError("numeric constants must be decimal strings")
    t = s.strip().lower()
    if t in ("nan", "inf", "-inf", "+inf", ""):
        raise ValueError("non-finite constant")
    return Fraction(s)


def fs(x):
    return f"{x.numerator}/{x.denominator}"


def vecs(v):
    return [fs(c) for c in v]


def dot(a, x):
    return sum(ai * xi for ai, xi in zip(a, x))


def solve_square(M, rhs):
    """Solve the square rational system M x = rhs; None if singular."""
    n = len(M)
    a = [list(M[r]) + [rhs[r]] for r in range(n)]
    for c in range(n):
        piv = None
        for r in range(c, n):
            if a[r][c] != 0:
                piv = r
                break
        if piv is None:
            return None
        a[c], a[piv] = a[piv], a[c]
        inv = Fraction(1) / a[c][c]
        a[c] = [v * inv for v in a[c]]
        for r in range(n):
            if r != c and a[r][c] != 0:
                f = a[r][c]
                a[r] = [vr - f * vc for vr, vc in zip(a[r], a[c])]
    return [a[r][n] for r in range(n)]


def rank_exact(rows):
    """Exact rational row rank."""
    if not rows:
        return 0
    a = [list(r) for r in rows]
    m, n = len(a), len(a[0])
    rank = 0
    col = 0
    for col in range(n):
        piv = None
        for r in range(rank, m):
            if a[r][col] != 0:
                piv = r
                break
        if piv is None:
            continue
        a[rank], a[piv] = a[piv], a[rank]
        inv = Fraction(1) / a[rank][col]
        a[rank] = [v * inv for v in a[rank]]
        for r in range(m):
            if r != rank and a[r][col] != 0:
                f = a[r][col]
                a[r] = [vr - f * vc for vr, vc in zip(a[r], a[rank])]
        rank += 1
        if rank == m:
            break
    return rank


# ------------------------------------------------------ region validation


class RegionError(ValueError):
    pass


def build_region(spec):
    """Fail-closed validation + linearization of a constrained region.

    Returns dict with: q, components, lo, up, cons (list of (a, b, tag) with
    a.x <= b), band_tags (tags of multicomponent rows), pvc/stoich closures
    for ratio evaluation.
    """
    comps = spec.get("components")
    lower = spec.get("lower")
    upper = spec.get("upper")
    if not isinstance(comps, list) or not isinstance(lower, list) \
            or not isinstance(upper, list):
        raise RegionError("components/lower/upper must be lists")
    q = len(comps)
    if q < 2:
        raise RegionError("a mixture region requires q >= 2 components")
    if len(set(comps)) != q:
        raise RegionError("duplicate component name")
    if len(lower) != q or len(upper) != q:
        raise RegionError("bound vector length mismatch")
    try:
        lo = [F(s) for s in lower]
        up = [F(s) for s in upper]
    except (TypeError, ValueError) as e:
        raise RegionError(f"bad bound: {e}")
    for i in range(q):
        if lo[i] < 0:
            raise RegionError("negative lower bound")
        if up[i] > 1:
            raise RegionError("upper bound exceeds unity")
        if lo[i] > up[i]:
            raise RegionError("lower bound exceeds upper bound")
    if sum(lo) > 1:
        raise RegionError("inconsistent region: sum(lower) > 1")
    if sum(up) < 1:
        raise RegionError("inconsistent region: sum(upper) < 1")

    cons = []
    for i in range(q):
        a = [Fraction(0)] * q
        a[i] = Fraction(-1)
        cons.append((tuple(a), -lo[i], f"lower:{comps[i]}"))
        a = [Fraction(0)] * q
        a[i] = Fraction(1)
        cons.append((tuple(a), up[i], f"upper:{comps[i]}"))

    band_tags = []
    ratio_forms = []

    dens = spec.get("densities")
    pvc = spec.get("pvc_band")
    stoich = spec.get("stoich")

    if pvc is not None:
        if not isinstance(dens, dict):
            raise RegionError("pvc_band requires densities")
        pigs = spec.get("pigment_components")
        binds = spec.get("binder_components")
        if not isinstance(pigs, list) or not pigs:
            raise RegionError("pvc_band requires non-empty pigment_components")
        if not isinstance(binds, list) or not binds:
            raise RegionError("pvc_band requires non-empty binder_components")
        for c in pigs + binds:
            if c not in comps:
                raise RegionError(f"unknown component in PVC role list: {c}")
        if set(pigs) & set(binds):
            raise RegionError("component assigned to both pigment and binder")
        rho = {}
        for c in set(pigs) | set(binds):
            r = F(dens.get(c))
            if r <= 0:
                raise RegionError("density must be strictly positive")
            rho[c] = r
        L = F(pvc["lower"])
        U = F(pvc["upper"])
        if not (0 <= L <= U < 1):
            raise RegionError("PVC band must satisfy 0 <= lower <= upper < 1")
        # Denominator D = sum over pigment+binder of x_i/rho_i must be
        # strictly positive everywhere: require at least one member with a
        # strictly positive lower bound.
        if not any(lo[comps.index(c)] > 0 for c in pigs + binds):
            raise RegionError("PVC denominator may vanish: no pigment/binder "
                              "component has a strictly positive lower bound")
        nvec = [Fraction(0)] * q
        dvec = [Fraction(0)] * q
        for c in pigs:
            nvec[comps.index(c)] = Fraction(1) / rho[c]
        for c in pigs + binds:
            dvec[comps.index(c)] = Fraction(1) / rho[c]
        a_lo = tuple(L * dvec[i] - nvec[i] for i in range(q))
        a_up = tuple(nvec[i] - U * dvec[i] for i in range(q))
        cons.append((a_lo, Fraction(0), "pvc:lower"))
        cons.append((a_up, Fraction(0), "pvc:upper"))
        band_tags += ["pvc:lower", "pvc:upper"]
        ratio_forms.append(("pvc", tuple(nvec), tuple(dvec), L, U))

    if stoich is not None:
        ep = stoich.get("epoxy_component")
        am = stoich.get("amine_component")
        if ep not in comps or am not in comps or ep == am:
            raise RegionError("stoich requires distinct epoxy/amine components")
        eew = F(stoich["eew"])
        ahew = F(stoich["ahew"])
        if eew <= 0 or ahew <= 0:
            raise RegionError("EEW/AHEW must be strictly positive")
        L = F(stoich["band"]["lower"])
        U = F(stoich["band"]["upper"])
        if not (0 < L <= U):
            raise RegionError("stoich band must satisfy 0 < lower <= upper")
        if lo[comps.index(ep)] <= 0:
            raise RegionError("stoich denominator may vanish: epoxy component "
                              "lower bound must be strictly positive")
        nvec = [Fraction(0)] * q
        dvec = [Fraction(0)] * q
        nvec[comps.index(am)] = Fraction(1) / ahew
        dvec[comps.index(ep)] = Fraction(1) / eew
        a_lo = tuple(L * dvec[i] - nvec[i] for i in range(q))
        a_up = tuple(nvec[i] - U * dvec[i] for i in range(q))
        cons.append((a_lo, Fraction(0), "stoich:lower"))
        cons.append((a_up, Fraction(0), "stoich:upper"))
        band_tags += ["stoich:lower", "stoich:upper"]
        ratio_forms.append(("stoich", tuple(nvec), tuple(dvec), L, U))

    region = {"q": q, "components": comps, "lo": lo, "up": up, "cons": cons,
              "band_tags": band_tags, "ratio_forms": ratio_forms}

    # Emptiness is fail-closed: a bounded non-empty polytope has a vertex.
    if not brute_force_vertices(region):
        raise RegionError("empty constrained region")
    return region


def feasible(x, region):
    return sum(x) == 1 and all(dot(a, x) <= b for a, b, _ in region["cons"])


def active_rows(x, region):
    return [a for a, b, _ in region["cons"] if dot(a, x) == b]


def is_extreme(x, region):
    q = region["q"]
    rows = [tuple([Fraction(1)] * q)] + active_rows(x, region)
    return rank_exact(rows) == q


# --------------------------------------------- vertex enumeration, 2 paths


def brute_force_vertices(region):
    """Basic-feasible-solution enumeration: every vertex solves sum(x)=1 plus
    q-1 active inequality rows of full rank (Snee 1979 sec. 3 geometry)."""
    q = region["q"]
    cons = region["cons"]
    ones = tuple([Fraction(1)] * q)
    verts = set()
    for S in itertools.combinations(range(len(cons)), q - 1):
        M = [ones] + [list(cons[i][0]) for i in S]
        rhs = [Fraction(1)] + [cons[i][1] for i in S]
        x = solve_square(M, rhs)
        if x is None:
            continue
        x = tuple(x)
        if feasible(x, region):
            verts.add(x)
    return sorted(verts)


def dd_vertices(region):
    """Independent path: Motzkin et al. 1953 sequential half-space cutting
    starting from the unit-simplex vertex set, exact screening after each cut."""
    q = region["q"]
    V = []
    for i in range(q):
        v = [Fraction(0)] * q
        v[i] = Fraction(1)
        V.append(tuple(v))
    V = sorted(set(V))

    # implicit nonnegativity of the starting simplex
    processed = []
    for i in range(q):
        a = [Fraction(0)] * q
        a[i] = Fraction(-1)
        processed.append((tuple(a), Fraction(0), f"nonneg:{i}"))

    sub = {"q": q, "cons": processed}

    def feas_sub(x):
        return sum(x) == 1 and all(dot(a, x) <= b for a, b, _ in sub["cons"])

    def extreme_sub(x):
        rows = [tuple([Fraction(1)] * q)]
        rows += [a for a, b, _ in sub["cons"] if dot(a, x) == b]
        return rank_exact(rows) == q

    for (a, b, tag) in region["cons"]:
        g = lambda x, a=a, b=b: dot(a, x) - b
        Vp = [v for v in V if g(v) > 0]
        V0 = [v for v in V if g(v) == 0]
        Vm = [v for v in V if g(v) < 0]
        new = set(V0) | set(Vm)
        for p in Vp:
            for n in Vm:
                gp, gn = g(p), g(n)
                t = gn / (gn - gp)
                z = tuple(n[k] + t * (p[k] - n[k]) for k in range(q))
                new.add(z)
        sub["cons"] = sub["cons"] + [(a, b, tag)]
        V = sorted(z for z in new if feas_sub(z) and extreme_sub(z))
    return sorted(V)


def mclean_anderson_box(region):
    """McLean & Anderson 1966 bound-only candidate generator (the generator
    under test): q-1 components at declared bounds, last by difference,
    screened only against the box bounds."""
    q = region["q"]
    lo, up = region["lo"], region["up"]
    raw = set()
    for k in range(q):
        others = [i for i in range(q) if i != k]
        for assign in itertools.product((0, 1), repeat=q - 1):
            x = [None] * q
            for pos, i in enumerate(others):
                x[i] = up[i] if assign[pos] else lo[i]
            x[k] = 1 - sum(x[i] for i in others)
            if lo[k] <= x[k] <= up[k]:
                raw.add(tuple(x))
    def box_vertex(x):
        active = sum(1 for i in range(q) if x[i] == lo[i] or x[i] == up[i])
        return active >= q - 1
    screened = {x for x in raw if box_vertex(x)}
    return sorted(raw), sorted(screened)


# ------------------------------------------------------------------ gates


def eval_ratio(nvec, dvec, x):
    return dot(nvec, x) / dot(dvec, x)


def region_test_points(region, verts, m=6):
    """Deterministic test set: box-feasible {q,m} lattice points, the region
    vertices, and all vertex-pair midpoints (hits band boundaries exactly)."""
    q = region["q"]
    lo, up = region["lo"], region["up"]
    pts = set()

    def compositions(mm, qq):
        if qq == 1:
            yield (mm,)
            return
        for first in range(mm + 1):
            for rest in compositions(mm - first, qq - 1):
                yield (first,) + rest

    for c in compositions(m, q):
        x = tuple(Fraction(a, m) for a in c)
        if all(lo[i] <= x[i] <= up[i] for i in range(q)):
            pts.add(x)
    pts |= set(verts)
    for u, v in itertools.combinations(verts, 2):
        pts.add(tuple((ui + vi) / 2 for ui, vi in zip(u, v)))
    return sorted(pts)


def gate_ratio_linearization(regions, verts_by_id):
    """G1: exact equivalence, at every test point, of the published ratio
    definition (Asbeck-Van Loo PVC; Lee-Neville stoichiometric index) and its
    linearized multicomponent half-space pair."""
    cases = []
    ok = True
    for rid, region in regions:
        if not region["ratio_forms"]:
            continue
        pts = region_test_points(region, verts_by_id[rid])
        for kind, nvec, dvec, L, U in region["ratio_forms"]:
            rows = [(a, b) for a, b, tag in region["cons"]
                    if tag.startswith(kind + ":")]
            n_pts = 0
            n_boundary = 0
            equiv = True
            denom_pos = True
            for x in pts:
                D = dot(dvec, x)
                if D <= 0:
                    denom_pos = False
                    continue
                r = dot(nvec, x) / D
                in_band = (L <= r <= U)
                lin_ok = all(dot(a, x) <= b for a, b in rows)
                if in_band != lin_ok:
                    equiv = False
                if r == L or r == U:
                    n_boundary += 1
                n_pts += 1
            agree = equiv and denom_pos and n_pts > 0
            ok &= agree
            cases.append({"region_id": rid, "ratio": kind,
                          "band": [fs(L), fs(U)],
                          "test_points": n_pts,
                          "points_exactly_on_band_boundary": n_boundary,
                          "denominator_positive_everywhere": denom_pos,
                          "exact_equivalence": equiv, "agree": agree})
    return {"gate_id": "G1_ratio_band_linearization_exact_equivalence",
            "source": ("Asbeck & Van Loo 1949 doi:10.1021/ie50475a042 (PVC); "
                       "Lee & Neville 1967 ISBN 978-0-07-036997-9 (stoich); "
                       "Cornell 2002 ISBN 0-471-07916-2 (ratio constraints)"),
            "cases": cases, "pass": ok}


def gate_dual_method_parity(regions, verts_by_id):
    """G2: brute-force basic-feasible-solution enumeration == sequential
    double description, per region; every vertex feasible, extreme, distinct."""
    cases = []
    ok = True
    for rid, region in regions:
        bf = verts_by_id[rid]
        dd = dd_vertices(region)
        set_equal = bf == dd
        all_feas = all(feasible(v, region) for v in bf)
        all_ext = all(is_extreme(v, region) for v in bf)
        distinct = len(set(bf)) == len(bf)
        agree = set_equal and all_feas and all_ext and distinct and len(bf) > 0
        ok &= agree
        cases.append({"region_id": rid,
                      "brute_force_vertices": len(bf),
                      "double_description_vertices": len(dd),
                      "set_equal": set_equal,
                      "all_feasible": all_feas,
                      "all_extreme_rank_certified": all_ext,
                      "all_distinct": distinct,
                      "agree": agree})
    return {"gate_id": "G2_dual_method_vertex_enumeration_parity",
            "source": ("Snee 1979 doi:10.1080/03610927908827762 (basic "
                       "feasible solutions); Motzkin et al. 1953 "
                       "ISBN 978-0-691-07935-6 (double description)"),
            "cases": cases, "pass": ok}


def gate_mclean_anderson_inadequacy(regions, verts_by_id):
    """G3: H0 = 'the McLean-Anderson bound-only candidate set remains
    vertex-complete under multicomponent constraints' (the caveat that could
    NOT fire in the box-only increment). Refuted if any true vertex is
    missing from the MA candidate set; every missing vertex must have a band
    row active."""
    cases = []
    ok = True
    total_missing = 0
    regions_refuting = 0
    for rid, region in regions:
        V = set(verts_by_id[rid])
        raw, screened = mclean_anderson_box(region)
        ma_feasible = [x for x in screened if feasible(x, region)]
        ma_cut_by_bands = [x for x in screened if not feasible(x, region)]
        # every band-feasible MA box-vertex must still be a true vertex
        ma_all_extreme = all(x in V for x in ma_feasible)
        missing = sorted(V - set(ma_feasible))
        missing_all_band_active = all(
            any(dot(a, x) == b for a, b, tag in region["cons"]
                if tag in region["band_tags"])
            for x in missing)
        refutes = len(missing) > 0
        if refutes:
            regions_refuting += 1
        total_missing += len(missing)
        agree = ma_all_extreme and missing_all_band_active
        ok &= agree
        cases.append({"region_id": rid,
                      "true_vertices": len(V),
                      "ma_raw_candidates": len(raw),
                      "ma_box_screened": len(screened),
                      "ma_band_feasible": len(ma_feasible),
                      "ma_box_vertices_cut_off_by_bands": len(ma_cut_by_bands),
                      "true_vertices_missing_from_ma": len(missing),
                      "missing_vertices_all_have_band_row_active":
                          missing_all_band_active,
                      "ma_feasible_all_remain_extreme": ma_all_extreme,
                      "h0_vertex_completeness_refuted_here": refutes,
                      "agree": agree})
    h0_refuted = regions_refuting > 0
    return {"gate_id": "G3_mclean_anderson_vertex_completeness_h0",
            "source": ("Snee & Marquardt 1974 doi:10.1080/00401706.1974."
                       "10489209; McLean & Anderson 1966 doi:10.1080/00401706."
                       "1966.10490377"),
            "h0": ("MA bound-only candidate generation remains vertex-complete "
                   "under multicomponent linear constraints"),
            "h0_refuted": h0_refuted,
            "regions_refuting_h0": regions_refuting,
            "total_true_vertices_missing_from_ma": total_missing,
            "cases": cases, "pass": ok and h0_refuted}


def gate_conaev_centroids(regions, verts_by_id):
    """G4: Piepel 1988 CONAEV centroid conformance. Face centroid = average of
    the vertices on the face: lies exactly on the face hyperplane and is
    feasible. Overall centroid = average of all vertices: feasible, and
    strictly interior to every constraint not active at all vertices."""
    cases = []
    ok = True
    for rid, region in regions:
        V = verts_by_id[rid]
        q = region["q"]
        c = tuple(sum(v[i] for v in V) / len(V) for i in range(q))
        c_feas = feasible(c, region)
        strict_ok = True
        face_cases = 0
        face_ok = True
        for a, b, tag in region["cons"]:
            on = [v for v in V if dot(a, v) == b]
            if len(on) == len(V):
                continue  # active at every vertex (degenerate band): skip strictness
            if dot(a, c) >= b:
                strict_ok = False
            if on:
                fc = tuple(sum(v[i] for v in on) / len(on) for i in range(q))
                face_cases += 1
                if dot(a, fc) != b or not feasible(fc, region):
                    face_ok = False
        agree = c_feas and strict_ok and face_ok
        ok &= agree
        cases.append({"region_id": rid,
                      "overall_centroid": vecs(c),
                      "overall_centroid_feasible": c_feas,
                      "overall_centroid_strictly_interior_to_nondegenerate_faces":
                          strict_ok,
                      "faces_with_vertices": face_cases,
                      "face_centroids_on_hyperplane_and_feasible": face_ok,
                      "agree": agree})
    return {"gate_id": "G4_piepel_conaev_centroid_conformance",
            "source": "Piepel 1988 doi:10.1080/00224065.1988.11979094",
            "cases": cases, "pass": ok}


def gate_dimension_and_box_comparison(regions, verts_by_id, anchors):
    """G5: exact affine dimension of each vertex set vs the declared expected
    dimension; quantified vertex-count change vs the box-only relaxation
    (continuity with the prior simplex-mixture-geometry increment)."""
    cases = []
    ok = True
    for (rid, region), spec in zip(regions, anchors["regions"]):
        V = verts_by_id[rid]
        q = region["q"]
        v0 = V[0]
        diffs = [tuple(v[i] - v0[i] for i in range(q)) for v in V[1:]]
        dim = rank_exact(diffs) if diffs else 0
        box_region = {"q": q, "components": region["components"],
                      "lo": region["lo"], "up": region["up"],
                      "cons": [c for c in region["cons"]
                               if c[2] not in region["band_tags"]],
                      "band_tags": [], "ratio_forms": []}
        box_V = brute_force_vertices(box_region)
        band_active_verts = sum(
            1 for v in V
            if any(dot(a, v) == b for a, b, tag in region["cons"]
                   if tag in region["band_tags"]))
        agree = (dim == spec["expected_dim"]) and len(box_V) > 0
        ok &= agree
        cases.append({"region_id": rid,
                      "affine_dimension_exact": dim,
                      "expected_dim": spec["expected_dim"],
                      "box_only_vertices": len(box_V),
                      "constrained_vertices": len(V),
                      "vertices_with_band_row_active": band_active_verts,
                      "agree": agree})
    return {"gate_id": "G5_affine_dimension_and_box_relaxation_comparison",
            "source": ("Snee 1979 doi:10.1080/03610927908827762; prior "
                       "increment simplex-mixture-geometry-v1 (box-only)"),
            "cases": cases, "pass": ok}


# -------------------------------------------------------- fail-closed probes


def failclosed_probes():
    base = {
        "components": ["dgeba_resin", "amine_hardener", "talc_filler"],
        "lower": ["0.45", "0.10", "0.10"],
        "upper": ["0.70", "0.30", "0.40"],
        "densities": {"dgeba_resin": "1.16", "amine_hardener": "0.95",
                      "talc_filler": "2.75"},
        "binder_components": ["dgeba_resin", "amine_hardener"],
        "pigment_components": ["talc_filler"],
        "pvc_band": {"lower": "0.10", "upper": "0.20"},
        "stoich": {"epoxy_component": "dgeba_resin",
                   "amine_component": "amine_hardener",
                   "eew": "190.0", "ahew": "43.0",
                   "band": {"lower": "0.95", "upper": "1.05"}},
    }

    def variant(**kw):
        import copy
        s = copy.deepcopy(base)
        for k, v in kw.items():
            path = k.split("__")
            tgt = s
            for p in path[:-1]:
                tgt = tgt[p]
            tgt[path[-1]] = v
        return s

    specs = [
        ("pvc_band_inverted", variant(pvc_band={"lower": "0.20",
                                                "upper": "0.10"})),
        ("pvc_band_empties_region", variant(pvc_band={"lower": "0.90",
                                                      "upper": "0.95"})),
        ("stoich_band_empties_region",
         variant(stoich__band={"lower": "9.0", "upper": "9.5"})),
        ("stoich_band_zero_lower",
         variant(stoich__band={"lower": "0", "upper": "1.05"})),
        ("zero_density", variant(densities__talc_filler="0")),
        ("negative_density", variant(densities__talc_filler="-2.75")),
        ("float_density_not_string", variant(densities__talc_filler=2.75)),
        ("nan_ahew", variant(stoich__ahew="NaN")),
        ("zero_eew", variant(stoich__eew="0")),
        ("unknown_pigment_component",
         variant(pigment_components=["zinc_dust"])),
        ("component_in_both_roles",
         variant(pigment_components=["talc_filler", "dgeba_resin"])),
        ("epoxy_lower_bound_zero_denominator",
         variant(lower=["0", "0.10", "0.10"], upper=["0.70", "0.30", "0.90"])),
        ("empty_pigment_list", variant(pigment_components=[])),
        ("nonnumeric_band", variant(pvc_band={"lower": "abc",
                                              "upper": "0.20"})),
    ]
    out = []
    for pid, s in specs:
        try:
            build_region(s)
            rejected, detail = False, "ACCEPTED (leak)"
        except (RegionError, ValueError, TypeError) as e:
            rejected, detail = True, f"{type(e).__name__}: {e}"
        out.append({"probe_id": pid, "expected": "REJECT",
                    "rejected": rejected, "detail": detail})
    return out


# ----------------------------------------------------------------- driver


def main(out_path):
    anchors_bytes = ANCHORS.read_bytes()
    anchors = json.loads(anchors_bytes)
    anchors_sha = hashlib.sha256(anchors_bytes).hexdigest()

    regions = []
    for spec in anchors["regions"]:
        regions.append((spec["region_id"], build_region(spec)))
    verts_by_id = {rid: brute_force_vertices(r) for rid, r in regions}

    gates = [
        gate_ratio_linearization(regions, verts_by_id),
        gate_dual_method_parity(regions, verts_by_id),
        gate_mclean_anderson_inadequacy(regions, verts_by_id),
        gate_conaev_centroids(regions, verts_by_id),
        gate_dimension_and_box_comparison(regions, verts_by_id, anchors),
    ]
    probes = failclosed_probes()
    gates_pass = sum(1 for g in gates if g["pass"])
    probe_pass = sum(1 for p in probes if p["rejected"])

    g3 = gates[2]
    g5 = gates[4]

    diag = {
        "schema": ("amphora.formulation-universe."
                   "multicomponent-constraint-polytope-diagnostic.v1"),
        "module": "amphora-formulation-universe",
        "authority": "AUDIT_ONLY",
        "axis": "THEORY",
        "toolkit": {"python": ".".join(str(x) for x in sys.version_info[:3]),
                    "arithmetic": ("exact rational (fractions.Fraction); "
                                   "no float in any decision"),
                    "randomness": "none", "network": "none"},
        "anchor_dataset": {
            "path": ("amphora-formulation-universe/reference/mvp20/data/"
                     "formulation_multicomponent_constraint_anchors.v1.json"),
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
            "ratio_band_linearization_exact": gates[0]["pass"],
            "dual_method_vertex_parity": gates[1]["pass"],
            "snee_marquardt_h0_vertex_completeness_refuted": g3["h0_refuted"],
            "regions_refuting_h0": g3["regions_refuting_h0"],
            "total_true_vertices_missing_from_ma":
                g3["total_true_vertices_missing_from_ma"],
            "conaev_centroid_conformance": gates[3]["pass"],
            "affine_dimensions_all_as_declared": g5["pass"],
            "regions_evaluated": len(regions),
            "total_constrained_vertices": sum(len(v)
                                              for v in verts_by_id.values()),
        },
        "acceptance_all_perfect": (gates_pass == len(gates)
                                   and probe_pass == len(probes)),
        "interpretation": (
            "Real coating windows add multicomponent linear constraints (PVC "
            "band, amine-H:epoxide stoichiometric band) to the box-bounded "
            "mixture simplex. Both ratio bands linearize exactly to "
            "half-space pairs, and the constrained region's extreme-vertex "
            "set is certified by two independent published enumeration paths "
            "in exact rational arithmetic. The Snee-Marquardt caveat that "
            "honestly could NOT fire in the box-only increment now fires: the "
            "McLean-Anderson bound-only candidate set is vertex-incomplete "
            "the moment a band constraint binds, with every missing vertex "
            "lying on a band facet. Piepel 1988 CONAEV centroid identities "
            "hold exactly, and the degenerate 1:1 stoichiometry region "
            "collapses to the declared lower affine dimension."),
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
          "h0_refuted", g3["h0_refuted"],
          "acceptance_all_perfect", diag["acceptance_all_perfect"])


if __name__ == "__main__":
    main(sys.argv[1])
