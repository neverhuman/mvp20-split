# dgeba-oligomer-hydroxyl-value-v1 (AUDIT_ONLY)

Second-signal for amphora-molecule-property adding a **NEW target molecular property** —
the hydroxyl value (hydroxyl number) OHV, mg KOH/g — distinct from the module's prior
EEW/AHEW equivalent-weight work. Independent RDKit-2026.03.2 reference implementation.

Chemistry: the fusion/advancement reaction that converts liquid n=0 DGEBA to higher
oligomers opens one epoxide against one bisphenol-A phenol per step, generating exactly one
**secondary aliphatic** hydroxyl (the 2-hydroxypropylene linker) per repeat unit. A pure
linear DGEBA oligomer of degree n therefore has exactly n titratable hydroxyls and no
phenolic/primary OH (all phenols are etherified). Per ASTM D4274:

    OHV(n) = 56100 * n / (M0 + n*M_repeat)   [mg KOH/g],  56100 = 1000*M(KOH), M(KOH)=56.1056

reusing the additive molar-mass series already locked by dgeba-oligomer-eew-series-v1
(M0 = M(C21H24O4), M_repeat = M(C18H20O3)).

- **G1 monomer anchor**: unadvanced n=0 DGEBA has 0 hydroxyls => OHV(0)=0 exactly.
- **G2 per-oligomer OH count + class**: for each independently RDKit-built oligomer n=0..3,
  total -OH == n AND all n are secondary aliphatic (0 phenolic, 0 primary); OHV series =
  [0, 89.79, 123.42, 141.02] mg KOH/g.
- **G3 monotone / bounded / advancement-consistent**: series monotone increasing, bounded by
  the C18H20O3-repeat asymptote 56100/M_repeat = 197.29 mg KOH/g; the RDKit OH count equals
  the mass-advancement n for every oligomer, so OHV and EEW(n)=170.21+142.18n are two
  independent structural read-outs of ONE advancement state.
- **G4 fail-closed**: bisphenol-A (2 phenolic OH), glycidol (1 primary), neopentyl glycol
  (2 primary), fully-hydrolyzed DGEBA diol (2 primary + 2 secondary) all correctly excluded
  as non-advancement-series members.
- IUPAC-2021 atomic-weight uncertainty <= 0.0046 mg KOH/g on OHV(n=1) => 0.5 bar carries ~110x headroom.

CORROBORATIVE ONLY: asserts no exact OHV for polydisperse commercial grades (composition is
measured, not derived); modifies no live lock. commercial_product_claim_locked=true unchanged.

Sources: Lee & Neville 1967 (Handbook of Epoxy Resins; advancement/secondary-OH); May 1988
(ISBN 0-8247-7690-9); ASTM D4274 (hydroxyl number, 56100 factor); Prohaska et al. Pure Appl.
Chem. 94(5):573 (2022) doi:10.1515/pac-2019-0603 (IUPAC 2021 atomic weights).

Files: compute_dgeba_hydroxyl.py (deterministic), diagnostic.canonical.json +
diagnostic.runB.json (byte-identical two-replay, sha256 935a8ff3…), sign_dgeba_hydroxyl.py,
dgeba_oligomer_hydroxyl_value_receipt.v1.json (DSSE Ed25519, local audit key local-9028773f…,
NOT trust-anchored). Promotes nothing; manifest untouched 66/11.
