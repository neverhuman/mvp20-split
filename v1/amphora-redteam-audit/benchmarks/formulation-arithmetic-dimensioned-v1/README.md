# formulation-arithmetic-dimensioned-v1

**AUDIT_ONLY** red-team + known-answer battery that opens the **dimensioned**
scope of `amphora-formulation-arithmetic`.

## Why this is the highest-value gap
The shipped `amphora-formulation-arithmetic` module sits at authority tier
`REAL_ARITHMETIC` but its Phase-0 known-answer fixture is deliberately
**`MASS_ONLY`** (`dimensioned_property_arithmetic_available: false`) — the live
engine can only *add masses*. It has **zero receipts in the manifest**. Yet this
module is the backbone that converts a molecular prediction into an actual paint
spec. Without volume/PVC/VOC arithmetic there is no bridge from the (validated)
molecular predictors to a formulatable, regulation-compliant coating.

## What this delivers (zero fitted parameters)
A reference engine + correctness proof for the dimensioned properties:

* **Volume solids** (ASTM D2697), **weight solids**
* **PVC** — pigment volume concentration (Asbeck & Van Loo 1949; Patton 1979)
* **VOC g/L** (EPA Method 24 / ASTM D3960) — the legal marine-compliance number
* **Wet-paint density**
* **Stoichiometric mix ratio / PHR** via EEW/AHEW equivalents (composes the
  already-validated EEW/AHEW capability)
* **Λ = PVC / CPVC** reduced-PVC **barrier gate** (composes the Asbeck–Van Loo
  CPVC engine from `cpvc-pigment-formulation-axis-v1`)

Exercised on a **real, rights-clean marine anti-corrosion epoxy-amine primer**
(DGEBA DER 331 + TETA + iron-oxide/zinc-phosphate/barytes/talc/mica +
xylene/n-butanol): VOC **284.1 g/L**, volume solids **0.667**, PVC **0.294**,
CPVC(blend) **0.509**, **Λ = 0.579 < 1 → continuous barrier film** (correct for
an anti-corrosion primer). All 5 physical-sanity bands pass.

## Known-answer battery (9/9 PASS)
Targets fixed by **definition** or by an **external physical constant** — never by
the engine, so the battery is falsifiable and non-circular:

| probe | kind | expected |
|---|---|---|
| VOC of neat xylene coating | EXTERNAL_CONSTANT | = xylene density x 1000 |
| VOC of zero-solvent coating | DEFINITIONAL | 0 g/L |
| volume solids of zero-solvent coating | DEFINITIONAL | 1.0 |
| PVC at equal pigment/binder volumes | DEFINITIONAL | 0.5 |
| PVC at pigment = 3x binder volume | DEFINITIONAL | 0.75 |
| density round-trip rho_wet*V - M | EXACT_IDENTITY | 0 |
| stoichiometric r=1 equivalents match | EXACT_IDENTITY | 0 |
| volume-fraction sum - 1 | EXACT_IDENTITY | 0 |
| mass-balance identity (legacy MASS_ONLY) | EXACT_IDENTITY | 0 |

## Data rights
Load-bearing densities + DGEBA EEW read **live** from in-tree provenance-tracked
`amphora-ingredient-library/.../facts.json` (grades TDS/HANDBOOK/DISTRIBUTOR/
SUPPLIER_GUIDE). Pure-amine (TETA) AHEW/density and per-pigment oil absorption are
**REFERENCE_NOMINAL** public physical constants (flagged), not a measured dataset.

## What this is NOT
* NOT a promotion — signed with `LOCAL_DEVELOPMENT_AUDIT_ONLY` key
  (`local-9028773f...`); flips no `scientific_readiness`, needs 2 trust-anchored
  human keys.
* Does NOT modify the shipped Rust engine (still MASS_ONLY), the existing
  `phase0-formulation-arithmetic-known-answer.v1.json`, any of the 66 signed
  receipts, or the manifest (still 66 receipts / 11 modules).

## Reproduce
```
python3 formulation_dimensioned_audit.py   # writes diagnostic.canonical.json
python3 sign_formulation.py                # DSSE-Ed25519 sign (two-replay gate)
```
Two-replay SHA-256 gate: `539f3e67...` (PASS). Envelope verifies against
`local-ed25519.pub.json`.
