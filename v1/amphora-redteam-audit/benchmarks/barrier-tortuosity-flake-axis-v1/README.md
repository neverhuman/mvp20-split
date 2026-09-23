# barrier-tortuosity-flake-axis-v1 (AUDIT_ONLY)

Autonomous red-team increment (xbabe2, 2026-07-26). Signed with the LOCAL_DEVELOPMENT_AUDIT_ONLY
key (`local-9028773f49591193`), **not** a trust-anchored phase0 key. Promotes nothing;
modifies no existing receipt and not the master manifest (still **66 receipts / 11 modules**).

## (A) Phase-0 honesty red-team — recomputed LIVE this run

Read directly from the live governance files (`module-manifest.json` + the 29
`phase0/benchmark/benchmark-lock.v1.json` + the signed receipts manifest):

- **29 / 29** modules carry `scientific_readiness == UNVALIDATED`.
- **0 / 29** modules are `ranking_eligible`.
- **29 / 29** live benchmark-locks set `scientific_success_required_for_phase0 = false`.
- Manifest steady at **66 receipts / 11 modules**.

**Verdict: "FULL Phase-0" is REFUTED.** Phase-0 is a *governance* gate (byte-stable
benchmark + rights-qualified data + two trust-anchored signatures), **not** a count of
scientifically validated coating models. Do not present a Phase-0 count to founders as
validated capabilities.

## (B) NEW axis — composite-barrier flake tortuosity engine

Opened the **lamellar/flake-pigment barrier-improvement** axis, untouched by all 66
receipts (the only prior "Nielsen" hit is the unrelated *1969 crosslink-Tg* relation; the
FFV axis reasoned about the neat matrix, never platelet tortuosity). This is the defining
physics of marine **glass-flake / MIO / graphene** anti-corrosion primers and directly
serves the currently UNVALIDATED/SHADOW module **amphora-barrier-corrosion-score**.

Parameter-free models, transcribed **verbatim** from open-access review PMC7569879
(Eqs. 18-22); primary refs Nielsen 1967 / Cussler-Aris 1988 / Bharadwaj 2001 / Maxwell 1873:

- Nielsen (dilute, phi<0.01):   `tau = 1 + a*phi/2`,  `Pr = (1-phi)/tau`
- Cussler-Aris (semidilute):    `tau = 1 + (2/3)a*phi + (a*phi)^2/9 = (1 + a*phi/3)^2`
- Bharadwaj (orientation S):    `Pr = (1-phi)/[1 + ((2/3)a*phi + (a*phi)^2/9)*(2/3)(S+1/2)]`,
  S=1 perpendicular (max tortuosity), S=0 random, S=-1/2 parallel (no tortuosity)

where phi = filler volume fraction, a = aspect ratio (length/thickness >=1), Pr = P_composite/P_matrix.

### Non-circular known-answer battery — **11 / 11 PASS**

Checks the engine against results derived **independently** of the tortuous-path argument:

- **KA2** Nielsen(a=1) == **Maxwell 1873** dilute-sphere limit `(1-phi)/(1+phi/2)` — exact (max diff 0.0; phi=0.2 -> 0.8/1.1 = 0.72727...)
- **KA3** Cussler tau == exact perfect square `(1+a*phi/3)^2`
- **KA4/KA5** Bharadwaj reduces exactly to Cussler at S=1 and to pure volume-exclusion `(1-phi)` at S=-1/2
- **KA1** dilute Pr->1; **KA6** orientation-factor endpoints (1, 1/3, 0)
- **KA7/KA8** strict monotonicity in phi and a; **KA9** physical bounds (0<Pr<=1, tau>=1, BIF>=1)
- **KA10** Cussler tau > Nielsen tau (exact sign); **KA11** negative control — tortuosity contributes a large non-trivial barrier improvement beyond volume exclusion.

### Reference-nominal illustration (NOT a measured dataset)

Engine output for literature-typical geometry: glass-flake (a=50, phi=0.15) -> BIF ~ 5.6-14x;
MIO (a=10, phi=0.20) -> 2.5-3.5x; nanoclay (a=200, phi=0.03) -> 4-9x; GNP (a=500, phi=0.01) -> 3.5-7x.
Consistent with reported marine glass-flake permeability reductions. BIF is a **transport
ratio, not a corrosion or service-life claim**; measured EIS remains required (module lock).

## Verdict

`ENGINE_READY__KNOWN_ANSWER_VALIDATED__PRECISION_EXTERNAL_VALIDATION_DATA_RIGHTS_BLOCKED`

**Blocker (same rights wall as every prior axis):** no rights-clean, in-marine-epoxy-scope
dataset of independently-measured (phi, effective aspect ratio, neat+filled permeability) was
obtainable this session; a same-formula fit to out-of-scope (PE/membrane) data would be
circular and scope-violating.

**Founder ask:** a rights-clean (CC-BY or owned) set of >=8 epoxy(-amine) coating specimens,
each with independently-measured filler volume fraction, effective in-film aspect ratio
(SEM/PSD), and measured O2/H2O permeability of neat and filled film -> enables non-circular
precision validation, model selection (Nielsen vs Cussler vs Bharadwaj), and an
orientation-parameter S fit.

## Reproduce

```
python3 barrier_tortuosity_audit.py diagnostic.canonical.json
python3 barrier_tortuosity_audit.py diagnostic.runB.json
sha256sum diagnostic.canonical.json diagnostic.runB.json   # identical -> two-replay PASS
python3 sign_barrier_tortuosity.py                          # DSSE Ed25519, AUDIT_ONLY key
```

- two-replay diagnostic sha256: `6b660fee1c4045490c7aa50a73cfdffd6a5a7d637b5bc0be488e3ff8457809c0`
- harness sha256: `a417ed98bce4432afc84c53baf7a2abeb1da694101eca2412f8f5fc585914b3a`
- receipt body sha256: `a5c6d314e3c996c3ec4e9a14ab4d01b01e53fd5c6baf6291251a7859815611ed`
- DSSE_VERIFY = PASS - authority LOCAL_DEVELOPMENT_AUDIT_ONLY - trust_anchored_in_phase0_store = false
