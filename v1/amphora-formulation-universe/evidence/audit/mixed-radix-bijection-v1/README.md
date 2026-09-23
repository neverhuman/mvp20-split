# mixed-radix-bijection-v1 (AUDIT_ONLY)

Independent theory-axis oracle for amphora-formulation-universe.

**Claim under test:** "Cartesian enumeration reports every solved and infeasible
combination without silent loss."

**Method:** mixed-radix positional numeral bijection.
- Knuth, TAOCP Vol.2 3rd ed. (1997), ISBN 0-201-89684-2, sec.4.1.
- Nijenhuis & Wilf, Combinatorial Algorithms 2nd ed. (1978), ISBN 0-12-519260-6, ch.1-3.

**Adds over the Rust Phase-0 benchmark:** the checked-in benchmark verifies
COUNTS (product = Pi cardinalities; solved+infeasible=total). This oracle proves
the index<->tuple map is a BIJECTION (injective => no silent duplication;
surjective vs independent itertools.product => no silent loss) and confirms N two
independent arithmetic ways: direct product vs positional maximum-numeral
identity N = sum_j (r_j-1)*w_j + 1. Path (ii) never multiplies all cardinalities
in one product, so it is a genuinely independent count confirmation.

**Result (10 CC0 DoE universes, radices 2..5, N=8..32):**
- acceptance_all_perfect: true (all 10 rates = 1.0)
- reproduces_all_anchors: true (cartesian_total, solved, infeasible)
- bijection_holds_all_universes: true
- fail-closed probes: 9/9 rejected (index==N, >N, negative, duplicate, float,
  bool, empty-axis, corrupted place-weights, digit overflow)
- two-replay: byte-identical (sha256 6bd1562c...)

**Authority:** AUDIT_ONLY. Does not promote, flip scientific_readiness, edit the
portfolio manifest (66/11), any locked dataset, the signed Phase-0 KPI, or the
live Rust engine. Signed under Phase-0 evaluator seed (keyid 3ef6b35c...),
DSSE PAE + Ed25519.

Files: run_mixed_radix_bijection.py (harness), diagnostic.canonical.json /
diagnostic.runB.json (two replays), sign_mixed_radix.py (signer),
mixed-radix-bijection-receipt.v1.dsse.json (signed receipt).
