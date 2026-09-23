# tg-density-external-validity-c7-v1

CAMPAIGN C7 attack on `amphora-molecule-property/evidence/phase0/kpis/openpoly-experimental-tg-ml-baseline-kpi.v1.json`'s
compound claim that within-corpus scaffold-safe performance (Tg RF LOSO MAE 51.24 K,
density RF MAE 0.0566 g/cm3) "transfers to out-of-corpus chemistry."

- **Tg**: true cross-corpus test (OpenPoly experimental <-> Polyuniverse Epoxy MD-simulated),
  both directions, RF/Morgan-fp/seed=0. **REFUTED**: 6.66x / 16.60x degradation vs
  apples-to-apples within-corpus MAE; the cross-corpus model is worse than the trivial
  null baseline in both directions (RF cannot extrapolate outside its training Tg range,
  and the two corpora's Tg columns occupy very different numeric ranges).
- **Density**: OpenPoly and Polyuniverse Epoxy both lack a density column; RadonPy PI1070
  is the only rights-cleared polymer-density corpus in this module, so a literal
  cross-corpus swap is impossible (data-availability gap, filed to the acquisition queue).
  Hardest available proxy — leave-polymer-class-out CV on RadonPy's own authentic
  `polymer_class` labels (14 classes, n=1059 pooled) — gives 1.80x degradation,
  **SURVIVED** the pre-registered 2x bar.

Overall fire verdict: **CLAIM_REFUTED** (the compound claim fails for Tg).

Run:
```
python3 compute_external_validity.py   # writes diagnostic.out.json
cp diagnostic.out.json diagnostic.canonical.json   # first replay
python3 compute_external_validity.py
cp diagnostic.out.json diagnostic.runB.json        # second replay
diff diagnostic.canonical.json diagnostic.runB.json  # byte-identical
python3 sign_external_validity.py
```
