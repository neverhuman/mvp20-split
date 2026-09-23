# RETRACTION INDEX — amphora-cure-potlife-gate

## R-A02 (2026-08-03) — mission.md blanket temperature-scaling claim retracted

| claim | refuted-by receipt path | superseded-by | date |
|---|---|---|---|
| docs/mission.md (pre-repair sha256 e8d12fa8d373e548151fa3d93920cd858ba84233c778bdbaf668d13c58ca706d): "The Arrhenius model reproduces published epoxy-amine pot-life temperature-scaling to under 15% error across a 30-degree temperature range (10°C to 40°C)" | evidence/audit/potlife-kpi-envelope-disclosure-gap-v1/potlife-kpi-envelope-disclosure-gap-receipt.v1.dsse.json (per-leg MAPE 10°C 3.445% / 30°C 15.628% / 40°C 25.124%; 40°C breaches the 0.25 KPI ceiling; 12/12 under-prediction at 30/40°C) and evidence/audit/potlife-q10-heuristic-ablation-v1/potlife-q10-heuristic-ablation-receipt.v1.dsse.json (chemistry-blind Q10=2 ties pooled 15.27% vs 14.73% and beats the model on the 30°C and 40°C legs) | evidence/phase0/repairs/R-A02/done/R-A02-repair-receipt.v1.dsse.json + qualified prose now in docs/mission.md | 2026-08-03 |
| implicit claim that the known-answer fixture's CC0-1.0 rights are settled (in-file self-assertion) | evidence/audit/rights-integrity-contradiction-v1/rights-integrity-contradiction-receipt.v1.dsse.json | fixture-rights-under-review note in docs/mission.md + evidence/phase0/repairs/R-A02/done/R-A02-repair-receipt.v1.dsse.json | 2026-08-03 |

## R-C02 (2026-08-12) — pot-life 40C-leg / Q10-ablation ceiling breach repaired

| claim | refuted-by receipt path | superseded-by | date |
|---|---|---|---|
| docs/mission.md (pre-repair sha256 4e4f72c38097eeec63bb9c6de003bf2df7c6d4084d8caf690d508805060c57bc) qualified statement disclosing that the incumbent per-system-Ea Arrhenius model breaches the 0.25 held-out-extrapolation ceiling at 40C (MAPE 25.12%) and loses to a chemistry-blind Q10=2 heuristic on the 30C and 40C legs, with no repair on record | evidence/audit/potlife-q10-heuristic-ablation-v1/potlife-q10-heuristic-ablation-receipt.v1.dsse.json (REFUTED verdict establishing the ceiling breach and the Q10 tie/loss) | evidence/phase0/repairs/R-C02/done/R-C02-repair-receipt.v1.dsse.json (LOSO cross-system bias-corrected Arrhenius: 40C leg MAPE 3.95%, beats Q10 on 3/3 legs) + qualified prose now in docs/mission.md | 2026-08-12 |
