# dielectric-constant-onsager-ccby-v1 (AUDIT_ONLY)

**Target:** `amphora-molecule-property` capability `static_relative_permittivity (eps_s)`
**Authority:** AUDIT_ONLY — promotes nothing, modifies no signed receipt/manifest (stays 66/11).

## What this is
First rights-clean, a-priori validation of a **static dielectric constant (relative
permittivity, eps_s)** predictor for coating-formulation solvents, via the **Onsager
(1936) reaction-field equation** — the polar-liquid member of the Clausius-Mossotti /
Debye family. It closes the electromagnetic-response pair: the signed
`refractive-index-lorentz-lorenz-ccby-v1` audit predicts the **electronic/optical** term
(n² = eps_infinity); this adds the **orientational dipole** term to reach the
**zero-frequency** eps_s.

## Why it matters (coating IP scope)
eps_s governs (a) the low-frequency **film capacitance** read by EIS and the
**Brasher–Kingsbury** moisture-uptake relation for marine anti-corrosion coatings, and
(b) **solvent polarity** for pigment wetting/dispersion and polar-additive solvency in
the two-part epoxy-amine formulation.

## Theory (zero fitted parameters, non-circular)
Onsager: (eps_s − n²)(2 eps_s + n²) / [eps_s (n²+2)²] = (N_A ρ/M) μ² / (9 eps0 kB T).
With s = n², A = (N_A ρ/M) μ²/(9 eps0 kB T): `eps_s = (B + sqrt(B² + 8 s²))/4`,
`B = s + A(s+2)²`. The dipole moment μ is an independent tabulated physical constant,
not fitted to eps_s. Two paths: **physics** (s from measured n_D) and **a-priori**
(s from Lorentz–Lorenz n, same Eisenlohr atomic refractions as the RI audit).

## Data (rights-clean)
26 pure liquids spanning epoxy-amine thinner chemistries. eps_s and μ are tabulated
non-copyrightable physical constants (CRC Handbook; McClellan dipole tables),
cross-checked vs the facts in en.wikipedia.org/wiki/Solvent (CC BY-SA). M, ρ_20C, n_D20
are the identical constants used by the signed refractive-index & Parachor audits.

## Result (verdict: `RANK_VALIDATED_IN_DOMAIN__MAGNITUDE_APPROXIMATE`)
CORE in-domain = 19 non-associating solvents (physics path):
- **Spearman rank(eps) = 0.995** → rank VALIDATED_IN_DOMAIN
- **MAPE = 8.1%** (median 5.8%), within ±15% = 15/19 → magnitude APPROXIMATE
- lift over electronic-only (eps=n²) baseline **80.2%**; over mean-eps null **92.9%**
Domain boundaries behave exactly as the physics predicts (declared a-priori, not fitted):
- BOUNDARY strongly-dipolar aprotic (DMF, MeCN): MAPE 15% (orientational correlation g≠1;
  MeCN antiparallel g<1 over-predicts, DMF high-μ under-predicts).
- ASSOC H-bonded (water + C1–C4 alcohols): MAPE 64%, severe under-prediction
  (Kirkwood g>1) — Onsager fails where theory says it must (water eps_pred ≈29 vs 78.4).

## Honest limitation
Magnitude carries a **systematic** component: aliphatic ketones (MEK/MIBK/acetone −12…−20%)
and chloroalkanes (chloroform −18%) under-predict; chlorobenzene over-predicts (+24%) —
the 4 core points outside ±15%. Cause: gas-phase μ vs liquid effective moment + weak
short-range dipolar ordering omitted by the g=1 cavity. Rank is unaffected.

## Reproducibility
Two-replay SHA-256 gate = PASS. canonical diagnostic sha256
`3aebaa39b89a530314cae34a94ac124bd4526b451f4c46e8d98af1fbb7a629a7`.
DSSE Ed25519 signature (local AUDIT_ONLY key `local-9028773f…`) SIGNATURE_VERIFY=PASS.
Run: `python3 dielectric_onsager_audit.py`; sign: `python3 sign_dielectric_onsager.py`.
