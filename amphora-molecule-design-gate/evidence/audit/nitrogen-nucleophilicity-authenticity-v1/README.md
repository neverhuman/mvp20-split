# amphora-molecule-design-gate :: nitrogen-nucleophilicity-authenticity-v1

**AUDIT_ONLY.** Mechanism-grounded adversarial audit of the design gate's
`reactive_amine_hydrogen_count` semantics. Does not modify the live Rust
runtime, the fixture, any locked dataset, the portfolio manifest, or any signed
Phase-0 KPI.

## Finding

The shipped rule counts attached H on any nitrogen that is merely
(non-aromatic AND non-amide). The published epoxy-cure mechanism requires a
**neutral amine lone pair** to open the oxirane (Shechter/Wynstra/Kurkjy 1956;
Rozenberg 1986; Ellis 1993 Ch.2/6). The shipped rule therefore admits formal
N-H that cannot react, and it gets the **sign of the protonation effect wrong**:

| hardener | refined (mechanism-correct) | shipped baseline |
|---|---|---|
| DETA, 0→3 protons | 5 → 3 → 1 → 0 | 5 → 6 → 7 → 8 |
| IPDA / MPDA / HMDA / MXDA, 0→2 protons | 4 → 2 → 0 | 4 → 5 → 6 |

Mono-protonated DETA scores **6** shipped amine hydrogens versus neutral
DETA's 5 — deactivating a nitrogen *increases* the gate's reactivity count.
21 hostile probes over 8 mechanism classes: 14 over-admit under the shipped
rule (45 excess formal H total) and **11 fully non-nucleophilic species
gate-ACCEPT as hardeners**.

## Refined predicate (6 clauses, irredundant)

A nitrogen contributes epoxide-reactive amine hydrogens iff it is not
ring-aromatic, **not formally charged**, carries **no formal double/triple
bond**, and is bonded to no carbonyl carbon, **thiocarbonyl carbon**, or
**sulfonyl/sulfinyl sulfur**. (Bold = the four new clauses.)

## Gates (11/11 pass)

- **G0/G1** non-regression: baseline and refined both reproduce 37/37 declared
  facts and 42/42 shipped gate labels. No signed Phase-0 result is disturbed.
- **G2** 21/21 hostile probes match hand-derived mechanistic expectation.
- **G2B** protonation monotonicity: refined strictly decreasing, baseline
  strictly increasing, on 5 ladders / 16 rungs → `WRONG_SIGN`.
- **G3** all 11 gate-level evasions closed with
  `missing_role_appropriate_reactive_group`.
- **G4** all 6 clauses necessary under single-clause ablation (2/3/7/2/2/3
  probes re-admitted).
- **G5** all 6 clauses inert on the shipped corpus (0/37 records changed) →
  refinement is a pure specificity tightening.
- **G6** 9/9 real published hardeners absent from the fixture re-derive their
  hand-declared amine functionality: DDS (4, AHEW 62.08), adipic dihydrazide
  (4, 43.55), amidoamine (2), AEP (3, 43.07), DEAPA (2), bis(3-aminopropyl)-
  piperazine (4), AEEA (3, 34.72), polyoxypropylenediamine model dimer (4),
  TMD (4, 39.57). DDS and ADH are the specificity controls for the sulfonyl
  and carbonyl clauses.
- **G7** refined dominates both shipped counting methods (per-atom 7/21,
  SMARTS 16/21, refined 21/21); the two baseline methods diverge on 9 probes,
  bounding the prior receipt's G4 two-method-invariance claim to the in-scope
  corpus.

Salt/dot forms (DETA·2HCl, MXDA·2HCl) fail closed on the separate lexical
single-component layer.

## Files

- `design_gate_nucleophilicity_oracle.py` — oracle (RDKit 2026.03.2)
- `diagnostic.canonical.json` / `diagnostic.runB.json` — byte-identical
  two-replay, sha256 `3cb73f4934573a135e0ed65d9f7d35058b9fca54ada82efb36d4a634a8a2ba9e`
- `nitrogen-nucleophilicity-authenticity-receipt.v1.dsse.json` — DSSE
  PAE+Ed25519, PHASE0_EVALUATOR key, trust-store-pinned
- `sign_nucleophilicity.py` — signer

## Phase-1 requirement

Wiring the six-clause predicate into
`amphora-molecule-capabilities/src/lib.rs::design_gate_result` behind the
pinned RDKit C++ boundary, plus fixture records for the charged / imine /
thioamide / sulfonamide classes. Deliberately unresolved: alpha-heteroatom
amines (hydrazine N-N, hydroxylamine N-O) are ADMITTED, since the literature
supports their nucleophilicity; delocalised amidine/guanidine/dicyandiamide
N-H is excluded from the probe set as mechanistically ambiguous.
