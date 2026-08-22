# RETRACTION INDEX - amphora-evidence-intake-validator

Append-only index of superseded claims. Entries record what was retracted/superseded, by what, and when. Original artifacts are never modified or deleted.

## V1-REAL-EIV - real in-tree DSSE corpus generalization claim (2026-08-04)

Scope note: the shipped n=3 synthetic-fixture KPI (`evidence/phase0/kpis/evidence-intake-validator-host-receipt-integrity-kpi.v1.json`) is NOT modified, deleted, or scientifically wrong for its stated population and is not retracted. What is superseded is the implicit generalization that its 1.0 positive_scenarios_scored_rate holds beyond that n=3 synthetic population.

| claim | refuted-by receipt path | superseded-by | date |
|---|---|---|---|
| The receipt-integrity validators 1.0 rates hold on the real in-tree DSSE corpus, not just on n=3 synthetic fixtures | `amphora-evidence-intake-validator/evidence/phase0/repairs/V1-REAL-EIV/done/v1-real-eiv-superseding-kpi.v1.dsse.json` (n=66 real manifest-indexed receipts, honestly-derived host verification: positive_scenarios_scored_rate=0.0, not 1.0, because none of the 66 receipts signing identity (toolkit-reviewer-cbe8c0fd...) is anchored in `config/phase0-trust-store.v1.json`) | same receipt (V1-REAL-EIV superseding KPI) | 2026-08-04 |

## T-04 - "no adversarial verdict" claim retired (2026-08-05)

Scope note: the shipped n=3+14+3 synthetic-fixture KPI (`evidence/phase0/kpis/evidence-intake-validator-host-receipt-integrity-kpi.v1.json`) is NOT modified, deleted, or scientifically wrong for its stated synthetic population and is not retracted. What is superseded is the module-level claim that it "has never received an adversarial verdict."

| claim | refuted-by receipt path | superseded-by | date |
|---|---|---|---|
| amphora-evidence-intake-validator has never received an adversarial verdict; its constructive SIGNED_RECEIPT-era receipts are untested claims | `amphora-evidence-intake-validator/evidence/phase0/repairs/T-04/done/t04-adversarial-forgery-done.v1.dsse.json` (7/7 forgery-family cases across all 5 named forgery classes admitted by the live predicate; 3/4 founder T2-04 directive categories admitted; live `amphora_core::verify_dsse` correctly rejects every one) | same receipt (T-04 adversarial forgery done-receipt) | 2026-08-05 |
