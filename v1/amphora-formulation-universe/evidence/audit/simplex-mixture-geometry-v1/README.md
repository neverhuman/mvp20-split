# simplex-mixture-geometry-v1 (AUDIT_ONLY)

Theory-axis oracle for amphora-formulation-universe.

**Claim under test:** the module's Phase-0 capability is *Cartesian* (mixed-radix
factorial) accounting over categorical axes. A coating formulation is physically
a **mixture**: component weight fractions are closed (`sum(x) = 1`) with
per-component bounds, so the feasible set is a convex polytope inside the
(q-1)-simplex, not a Cartesian box. This oracle implements the published mixture
geometry and quantifies the mismatch.

**Baselines (all primary, with DOI/ISBN):**
- Scheffé 1958, JRSS-B 20(2):344-360, doi:10.1111/j.2517-6161.1958.tb00299.x —
  simplex-lattice `{q,m}`, `|{q,m}| = C(q+m-1, m)`, canonical polynomial.
- Scheffé 1963, JRSS-B 25(2):235-263, doi:10.1111/j.2517-6161.1963.tb00506.x —
  simplex-centroid, `2^q - 1` points.
- McLean & Anderson 1966, Technometrics 8(3):447-454,
  doi:10.1080/00401706.1966.10490377 — extreme-vertices generator.
- Snee & Marquardt 1974, Technometrics 16(3):399-408,
  doi:10.1080/00401706.1974.10489209 — MA over-generation caveat.
- Piepel 1983, Technometrics 25(1):97-101, doi:10.1080/00401706.1983.10487825 —
  consistency predicate + implied-bound range identity.
- Motzkin/Raiffa/Thompson/Thrall 1953, Annals of Math. Studies 28,
  ISBN 978-0-691-07935-6 — double description (independent parity oracle).
- Cornell 2002, 3rd ed., ISBN 0-471-07916-2.

**Adds over the prior mixed-radix-bijection oracle:** that oracle proved the
Cartesian index<->tuple map is a bijection (no silent loss/duplication). It says
nothing about closure. This one adds the `sum(x)=1` geometry the Cartesian model
cannot express.

**Gates (6/6 PASS, exact rational arithmetic, no float in any decision):**
- **G1** Scheffé 1958 lattice counts — 13 `(q,m)` cases, brute-force enumeration
  == `C(q+m-1,m)` == anchor, all points close to unity.
- **G2** Saturation — for `(q,m)` in 10 cases the canonical model matrix at the
  `{q,m}` lattice is square and has an **exactly nonzero rational determinant**
  (up to 35x35 for `{5,3}`).
- **G3** Scheffé 1963 centroid counts — 4 cases == `2^q - 1`, all distinct.
- **G4** Canonical term counts — linear/quadratic/special-cubic/full-cubic,
  12 cases.
- **G5** Cartesian-closure waste (bridge to the existing module claim) —
  filtering the `(m+1)^q` mixed-radix grid by closure reproduces the Scheffé
  lattice **exactly** in 8/8 cases. Worst case q=6, m=6: **0.392694 %** of the
  117 649 grid points are closure-feasible. **3 of 8** cases breach
  `MAX_FORMULATION_UNIVERSE_CARDINALITY = 10 000` in Cartesian form while the
  equivalent lattice fits (e.g. q=5,m=10: 161 051 -> 1 001).
- **G6** Extreme vertices on 6 marine epoxy-amine constrained regions —
  McLean-Anderson (screened) == double-description, set-equal in all 6; 52
  vertices total; every vertex feasible, extreme and distinct; Piepel implied
  bounds equal the observed per-component vertex range exactly in all 6
  (3 regions exercise lower tightening, 3 upper, 1 collapses to a single point).

**Honest negative/nuance:** the Snee-Marquardt over-generation caveat did **not**
fire (0 non-vertex MA candidates). This is a corollary, not a miss: with
box-only bounds every MA candidate pins q-1 components to a declared bound and
is therefore necessarily an extreme point. The caveat can only bite once
multi-component linear constraints (PVC band, amine-H:epoxide equivalent band)
are added — that is the natural next increment.

**Fail-closed probes: 12/12 rejected** — `sum(l)>1`, `sum(u)<1`, `l>u`,
negative `l`, `u>1`, q=1 region, non-numeric bound, duplicate component, NaN
bound, bound-length mismatch, lattice m=0, lattice q=1.

**Two-replay:** byte-identical, sha256 `501cde5b...`.

**Authority:** AUDIT_ONLY. Does not promote, flip `scientific_readiness`, edit
the portfolio manifest (66/11), any locked dataset, the signed Phase-0 KPI, or
the live Rust engine. Signed under the Phase-0 evaluator seed
(keyid `3ef6b35c...`), DSSE PAE + Ed25519; envelope sha256 `0213e4ab...`.

Files: `run_simplex_mixture_geometry.py` (harness),
`diagnostic.canonical.json` / `diagnostic.runB.json` (two replays),
`sign_simplex_mixture_geometry.py` (signer),
`simplex-mixture-geometry-receipt.v1.dsse.json` (signed receipt).
New rights-clean anchor dataset:
`reference/mvp20/data/formulation_mixture_region_anchors.v1.json` (CC0-1.0,
sha256 `c47fe301...`).
