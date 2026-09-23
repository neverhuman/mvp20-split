# network-tg-feasibility-v4 — protocol-curation feasibility red-team (AUDIT_ONLY)

**Authority:** `AUDIT_ONLY` · signed with `local-9028773f49591193`
(`LOCAL_DEVELOPMENT_AUDIT_ONLY`, NOT a trust-anchored phase0 key).
**Promotes nothing.** Manifest stays 66 receipts / 11 modules; 0/29 modules
`scientific_readiness=VALIDATED`. No existing receipt/manifest touched.

Target gap: `amphora-molecule-property` glass_transition of DGEBA + amine
marine networks — the highest-value UNVALIDATED scientific gap in the portfolio.

## Why this run exists

v3 (signed) built backbone rigidity `B` (1-axis LOO Tg MAE **35.73 °C**).
crosslink-density-v1 (signed) built the a-priori Flory crosslink density `n_x`
and showed the 2-axis LOO **overfits** at n=7 (**48.96 °C**), concluding "acquire
n≥12." This run tests whether that is *sufficient* and reaches a sharper answer.

## New findings (both deterministic, two-replay byte-stable)

1. **Cure-state protocol sensitivity (page-verified CC-BY, this run).** The *same*
   amine's Tg shifts **27–46 °C** purely with cure state — IPDA full-cure 158 vs
   cold-cure 112; DDS post-cured ~208 vs the hot-cure reference 181 (MDPI Polymers
   2023 15(4)990 = PMC9962791, CC BY). These cold-cure values are recorded as
   evidence and **deliberately NOT merged** into the protocol-consistent set.

2. **Gate-feasibility proof.** The G2 target (LOO MAE ≤25 °C) sits **above** the
   ~8.6 °C same-protocol inter-lab floor (DDS 220/200/204) but **below** the
   27–46 °C cross-cure-state scatter of one amine. ⇒ the ≤25 °C gate is achievable
   **only** on a protocol-controlled dataset; naive open-literature aggregation
   (which mixes cure states) can *never* reach it, regardless of model quality.

3. **Model structural ceiling.** The linear `B+n_x` model already has ~26 °C
   in-sample RMSE (R²=0.55) at n=7 — essentially *at* the gate. More data
   de-leverages the LOO but cannot cross ≤25 °C without a **steric/side-group
   descriptor** (IPDA gem-dimethyl; DDS sulfone) or a nonlinear model.

4. **Honest acquisition log.** Every rights-clean source tried this run and why it
   was rejected (protocol mismatch / non-discrete phenalkamine / Tg0-not-cured /
   MDPI 403 / Wiley 402). **0 new points merged.**

## Verdict

`PROTOCOL_CURATION_AND_MODEL_CO_LIMITED` — network-Tg is blocked by
protocol-consistent data **curation** PLUS one more descriptor, **not** by
governance. Concrete spec: ≥5 additional fully-post-cured DGEBA + **discrete**-amine
Tg points under ONE declared cure protocol + ONE DSC rate (n≥12, ideally ~20,
spanning functionality f=4..6 × stiffness) AND a third steric descriptor.

## Reproduce

```
python3 network_tg_v4_audit.py diagnostic.canonical.json   # writes canonical
python3 network_tg_v4_audit.py diagnostic.runB.json         # two-replay
sha256sum diagnostic.canonical.json diagnostic.runB.json    # must match
python3 sign_network_tg_v4.py                               # DSSE Ed25519 sign
```

- canonical diagnostic SHA-256: `97e4ada7dc27591205a7cecf026ff25f2befe55af3ff8bcc866245b408db5e5d`
- two-replay gate: **PASS** · signature verify: **PASS** · rdkit 2026.03.2
- cross-checks: reproduces v3 `B` LOO 35.730624 and crosslink-v1 2-axis LOO 48.96 exactly.
