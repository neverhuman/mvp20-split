# Red-team memo — network-Tg feasibility does NOT survive independent data; true Phase-0 is 10 (2026-07-25)

**Date:** 2026-07-25 · **Host:** all real work on the canonical Linux host
(`ssh xbabe2:/home/ubuntu/amphora/build/mvp20-split`). **Authority:** AUDIT_ONLY —
promotes nothing, modifies none of the 66 signed receipts, the manifest, or the
signed `network-tg-feasibility-v1` audit. This was the last cron pass before the
founder report.

Task: *"I do NOT believe you that we actually have FULL phase 0. Red-team what we
have… make MEANINGFUL progress on a new phase 0 with real data, real theory, real
model, real KPI, or output a red-team memo explaining why."* Both are delivered.

---

## 1. The "full Phase 0" claim is false. Defensible Phase-0 = **10**.

Re-verified on the canonical host this run:

- **10 defensible Phase-0 modules** = 9 infrastructure / trust-kernel /
  deterministic-control modules **+ `amphora-solvency-score`** (the sole promoted
  *science* module; its signed evaluation + independent-review receipts verify
  against the trust-anchored evaluator/reviewer keys, bundle binding intact).
- **All 29 module front-matters carry `scientific_readiness: UNVALIDATED`.** No
  science module other than solvency has a validated, promoted KPI.
- The old **"16"** headline remains stale/indefensible (7 of the 16 badges fail
  benchmark-binding re-verification — post-signing drift, documented in the
  count-integrity audit). **Do not use 16.**

**Bottom line for founders:** we have 1 promoted coating-science KPI (solvency),
not "full Phase 0." Every other science capability is pre-Phase-0.

## 2. This run's real work — a red-team CORRECTION on the highest-value gap

Network-Tg (glass transition of DGEBA-amine networks) is the highest-value
*unvalidated* coating-science gap. The prior `network-tg-feasibility-v1` audit
(signed) reported encouraging numbers on n=5 single-source Tg (ring-fraction
r=+0.69, LOO MAE ~24–29 °C) and framed it as "one rights-clean dataset away from a
KPI." I **red-teamed that claim by actually acquiring the data.**

**Real data acquired (rights-clean, individually cited, each read from the source
page):** n=5 single-source → **n=9 measurements / 7 unique systems / 4 amine
classes** across **3 independent sources** (May 1988 Ch.6; *Polymers* 2024
**CC BY 4.0** doi:10.3390/polym16010067; Savonnet 2018 / arXiv:1911.08960).
Critically, **DGEBA/DDS is now measured by 3 independent labs: 200 / 204 / 220 °C**
— giving a *measured* inter-lab Tg floor (std 8.6 °C, range 20 °C) instead of an
assumed one.

**Result — the v1 optimism does not survive independent data:**

| structure-only model (non-circular) | leave-one-out MAE |
|---|---|
| ring-atom fraction (v1's best) | **40.5 °C** |
| NULL — just predict the mean Tg | **31.8 °C** |
| incumbent polyuniverse ML | 39.1 °C |
| raw Van Krevelen | 109.1 °C |

The best structure-only model is **worse than a trivial mean-Tg baseline** and does
**not** beat the incumbent ML. Ring-fraction correlation fell from +0.69 (v1) to
+0.46 (n=7). The mechanism is now clear from the data: whole-molecule ring/aromatic
fraction cannot distinguish **backbone-rigid** aromatics (DDS, Tg 208) from
**pendant / CH₂-linked** aromatics (m-XDA, Tg 100) at near-identical aromatic
fraction (108 °C apart), and ring fraction *anti-*predicts across cycloaliphatics
(IPDA 158 at ring 0.5 vs 1,3-BAC 97 at ring 0.6).

**Verdict: network-Tg is FURTHER from Phase-0 than v1 implied.** The v1 "one
dataset away" headline was a small-sample artifact and should not go to founders.
The honest next step is a *topological backbone-rigidity-between-crosslinks*
descriptor validated on n≥12 rights-clean systems — real, scoped future work.

## 3. Why this is progress, not a null result

- It **prevents a dishonest promotion**: a founder deck built on the v1 headline
  would have overstated a capability that fails on independent data. Catching that
  before the deck is the point of a last red-team pass.
- It **converts an assumption into a measurement**: the inter-lab Tg floor
  (~10 °C) is now data, bounding what any Tg model can achieve on literature ground
  truth.
- It **nearly doubles** the rights-clean cited network-Tg set and leaves a clean,
  reproducible, signed foundation (n=9, 3 sources, full provenance) for the next
  attempt with better physics.
- Everything is **signed and two-replay reproducible** (byte-identical `c4fe7cb3…`,
  DSSE Ed25519 verifies against the pinned AUDIT_ONLY key).

## 4. Also corrected this run — cure-potlife is NOT "signatures-only"

The `redteam-cure-potlife` memo framed cure-potlife as blocked "ONLY by the two
trust-anchored signatures." That is incomplete: its Phase-0 **source-lock also
fails the rights gate** — `source-lock.v2.json` has `rights_gate_passed: false`,
`eligible_sources: []` (every source CONTEXT_ONLY / rights-UNRESOLVED /
license-absent). cure-potlife's Arrhenius model is real and externally corroborated,
but its KPI is computed on data that does **not** pass the rights gate. So its
remaining blockers are **BOTH data-rights AND the signing ceremony** — not
signatures alone. State this to founders.

## 5. What did NOT change (authority ceilings sacred)

- No module promoted; defensible Phase-0 stays **10**.
- Manifest unchanged (66 receipts / 11 modules).
- No existing receipt or the signed v1 audit modified.
- New artifacts only: `amphora-redteam-audit/benchmarks/network-tg-feasibility-v2/`
  (harness, two byte-identical diagnostics, signed DSSE receipt) and this memo.

## Artifacts
- `amphora-redteam-audit/benchmarks/network-tg-feasibility-v2/replay_receipt.v1.dsse.json`
  — receipt body SHA `191655c9…`, envelope SHA `1c45715a…`, signature verifies.
- Diagnostic (two-replay PASS): SHA `c4fe7cb366f2fde8f1fb2169ea2795d2ad7465bcf6666ac744159273b3fbea74`.
