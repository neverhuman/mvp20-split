# viscosity-blend-mixing-rule-ccby-v1  (AUDIT_ONLY)

Blend (mixture) viscosity mixing-rule validation for amphora-viscosity-score.
First component->mixture viscosity science in the portfolio (all prior viscosity
work was pure-component Arrhenius or CONTEXT_ONLY-quarantined polyverse melt).

- Data: toluene (1) + 2-propanol (2), 11 compositions x 5 T (293.15-313.15 K),
  dynamic viscosity mPa.s. Molecules 2024, 29(19):4706, PMC11477799, CC BY 4.0.
  Both solvents are in-scope marine thinners and both are in the module CC0 fixture.
- Theory: Arrhenius/Kendall-Monroe zero-param log-linear mole-fraction mixing;
  Grunberg-Nissan (1949) 1-param interaction; Eyring excess activation (sign).
- Non-circular: KM uses only the two measured pure endpoints per T; the 9 interior
  blends per T (45 total) are the target, never a KM input.

RESULT (honest):
- Kendall-Monroe zero-param a-priori: global MAPE 33.9%, all 45 points over-predict
  -> REFUTED on magnitude (associating aromatic+alcohol, negative deviation).
- Rank/composition ordering preserved: Spearman +1.0 at every temperature.
- Grunberg-Nissan 1-param: residual MAPE 3.0%, d12 = -1.56 (weakens with T).
- Independent cross-source data integrity: pure-component agreement <=1.25% vs the
  in-tree CC0 CRC/NIST fixture.
- Known-answer battery 7/7 PASS.

Reproduce:
  python3 viscosity_blend_mixing_audit.py diagnostic.canonical.json
  python3 sign_viscosity.py   # two-replay + 3rd confirmatory + DSSE Ed25519 sign

Two-replay SHA-256: 4c22eb0cf4447d8d62a109654d26cd8bdb3b3b1dc07bd6c2e4aa9f6fd6a65764
DSSE envelope SHA-256: 8831abe1ab579eed060103f5d8c7c987cf9a2d71ef4de91a85938d2ce58a41d2
AUDIT_ONLY. Promotes nothing. Manifest untouched (66 receipts / 11 modules).
