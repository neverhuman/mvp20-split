# Backlog

The campaign that drove the autonomous loop is frozen at
`ops/amphora-controller/bootstrap/campaign.json`: **183 items, 135 done,
48 blocked**. "Exhausted" in the runbook means nothing is *pending* — it does not
mean nothing is left. This file is the readable view of what is left, grouped by who can
actually move it.

Each item carries an `id`, `module`, `claim`, `objective`, `done_criterion`, a machine
`done_check`, and a `directive_ref` pinned to a directive document by sha256. Read the item
in the campaign JSON before starting it — the `done_criterion` is the acceptance test.

## Start here — 9 items you can action in software

These are `owner: LOOP` — no external dependency, no lab, no counsel. They are the work a
developer can pick up today.

| Item | Module | Title |
|---|---|---|
| `CF-BOM` | `amphora-cro-protocol-packager` | Formulation & BOM: every raw material, function, loading, source, tier |
| `CF-TIER` | `amphora-cro-protocol-packager` | Per-element evidence tiers: the crosswalk that couples recipe and ledger |
| `DR-FRESH` | `amphora-dataset-recon` | Freshness: every run diffs against the last |
| `CF-PACKET` | `amphora-cro-protocol-packager` | Final assembly through CroProtocolPackageV2, locks intact |
| `R-C01-V` | `amphora-tolerance-robustness` | Independent verify of R-C01 |
| `R-C02-V` | `amphora-cure-potlife-gate` | Independent verify of R-C02 |
| `R-C03-V` | `amphora-molecule-property` | Independent verify of R-C03 |
| `R-C04-V` | `amphora-viscosity-score` | Independent verify of R-C04 |
| `R-C05-V` | `amphora-barrier-corrosion-score` | Independent verify of R-C05 |

`R-C01-V`…`R-C05-V` are independent verifications of already-filed repairs: re-run the
module's own checker against the repaired corpus and sign the result. Signing works on
xbabe1 — the evaluator seed is present there. They are the gentlest
introduction to the evidence workflow, because the checker already exists and the expected
outcome is documented.

`CF-BOM`, `CF-TIER`, and `CF-PACKET` are substantive: they complete the CRO protocol
packager's bill-of-materials, evidence-tier crosswalk, and final assembly through
`CroProtocolPackageV2` with locks intact.

## One candidate first project outside the campaign

- **Bring the showcase to `main`.** `demo/founder-showcase` carries a four-example live TUI
  (see [DEMO.md](DEMO.md)). `R2`/`R3` on that branch have declared breaking effects on
  legacy run archives, so this needs a reviewed decision first — which makes it a good
  exercise in how this project handles a breaking change.

The former T-01B first project is complete: its caller-hash guard landed on `main` as
`acf268f6`.

## Highest scientific value — the roadmap ladder

[`roadmap.md`](roadmap.md) scores every module as
`3D + 3G + 2A + 2L − E − X`. The top of the ladder is
**`amphora-public-corrosion-benchmark` (score 40)**: highest decision value, largest evidence
gap, and the largest downstream leverage, because several other modules are gated behind
whether public corrosion data can support a reproducible external benchmark at all.

## Blocked on people — 13 items

Filed and tracked by the loop, never executed by it. Nothing here is a software task.

| Item | Module | Title |
|---|---|---|
| `DR-RIGHTS` | `amphora-dataset-recon` | Counsel review of every CONDITIONAL disposition |
| `DR-ACQ` | `amphora-dataset-recon` | Execute the next human action on RECOMMENDED entries |
| `CF-EXEC-REVIEW` | `amphora-cro-protocol-packager` | CRO feasibility review of the candidate package |
| `R-D01` | `amphora-barrier-corrosion-score` | USBR ST-19168 rights confirmation |
| `R-D02` | `amphora-public-corrosion-benchmark` | USBR RISE frequency-resolved EIS access |
| `R-D03` | `amphora-viscosity-score` | Reynolds 2024 CC BY-NC-ND counsel review |
| `R-D04` | `amphora-cure-potlife-gate` | Cure fixture rights ratification |
| `R-D05` | `amphora-design-rule-score` | Second-formulator DoE data acquisition |
| `R-D06` | `amphora-molecule-property` | RadonPy upstream + OpenPoly density asks |
| `R-D07` | `amphora-redteam-audit` | HUMAN CEREMONY READY: restore evaluation binding for 8 modules (tool built + tested) |
| `R-D08` | `amphora-formulation-universe` | HUMAN DECISION: merge candidate — claim duplicates amphora-formulation-arithmetic |
| `B-CREDENTIALS` | `amphora-redteam-audit` | B.1 Register the two trusted signer identities (blocks everything) |
| `B-COUNTERPARTIES` | `amphora-redteam-audit` | B.5 Contract the eight independent counterparties |

`B-CREDENTIALS` is worth singling out: it blocks every independent-verification item, because
until two trusted signer identities are registered there is no second party to verify
anything.

## Blocked on bench work — 12 items

External laboratory campaigns. Costed and specified, not startable from a keyboard.

| Item | Module | Title |
|---|---|---|
| `CF-LAB-EXEC` | `amphora-cro-protocol-packager` | Bench execution and candidate-bound data return |
| `LAB-C0` | `amphora-redteam-audit` | C.0 Common transfer path, promotion gate, and kill/hold gate |
| `LAB-C1` | `amphora-formulation-universe` | C.1 Formulation coverage — seed campaign (30 formulations / 3 families) |
| `LAB-C2` | `amphora-barrier-corrosion-score` | C.2 Barrier-corrosion campaign (210 panels / 40 systems, incl. 10 untouched external) |
| `LAB-C3` | `amphora-cure-potlife-gate` | C.3 Cure / pot-life campaign (36 runs: 24 fit + 12 sealed holdouts) |
| `LAB-C4` | `amphora-viscosity-score` | C.4 Viscosity / sag campaign (288 cells, three temperatures) |
| `LAB-C5` | `amphora-solvency-score` | C.5 Solvency / blend calibration campaign |
| `LAB-C6` | `amphora-molecule-property` | C.6 Molecule-property validation + dielectric labels (>=300 eligible structures) |
| `LAB-C7` | `amphora-molecule-role-ranker` | C.7 Molecule-role blinded-label campaign |
| `LAB-C8` | `amphora-design-rule-score` | C.8 Design-rule second-formulator DoE |
| `LAB-C9` | `amphora-redteam-audit` | C.9 Independent chemistry red-team (96 attacks + 32 valid controls) |
| `LAB-C10` | `amphora-process-qc-twin` | C.10 Process-QC prospective pilot (30 batches, seeded failures) |

## Exhausted attempts — 6 items

These hit `max_fires` and stopped. Reopening one requires a reviewed decision and, in most
cases, a change to the approach rather than another attempt at the same one.

| Item | Module | Title |
|---|---|---|
| `W-FFI2` | `amphora-rdkit-ffi` | DICY is categorically zeroed but is a real functionality-4 hardener |
| `V1-KPI-QC` | `amphora-process-qc-twin` | Promote ARL characterization to a KPI; finish the unsigned MR detector run |
| `W-VISC1` | `amphora-viscosity-score` | Sign the honest Krieger-Dougherty data-wall verdict |
| `U-DATA` | `amphora-molecule-property` | Domain-widening data hunt: rights-clean corpora overlapping the epoxy-amine space |
| `W-D-DESIGN` | `amphora-design-rule-score` | Second-formulator scratch-hardness data hunt |
| `W-D-ROLE` | `amphora-molecule-role-ranker` | External validation set for the role rule |

## Other blocked — 8 items

| Item | Module | Title |
|---|---|---|
| `C2` | `amphora-barrier-corrosion-score` | USBR ST-19168 rights-review package — the single unlock for coating-barrier science |
| `C9` | `amphora-viscosity-score` | Krieger-Dougherty / Herschel-Bulkley benchmark — or the honest data wall |
| `R-C04` | `amphora-viscosity-score` | FFW-vs-ML cluster-bootstrap interval disclosure |
| `R-S01` | `amphora-solvency-score` | W7b: fair ML-vs-classical-theory re-run |
| `W-D-KAB` | `amphora-known-answer-benchmarks` | Grow the known-answer control corpus from real published data |
| `W-D-REPORT` | `amphora-report-packager` | Adversarial package corpus from the tree's own artifacts |
| `W-D-EIV` | `amphora-evidence-intake-validator` | Grow the receipt corpus beyond the in-tree set |
| `W-T-ENVGATE` | `amphora-envelope-gates` | Named baseline for envelope-gate correctness |

## Known debt

`cargo run -p xtask -- audit` fails on one module — three stale digests in
`amphora-cro-protocol-packager`'s `evidence/phase0/sources/source-lock.v1.json`, left by the
2026-08-11 CF-TEST/CF-RISK repairs. It is digested into a signed evaluation receipt, so
correcting it needs a supersession record and a re-sign with the evaluator seed. That seed
is now present on xbabe1, so this is **actionable there** rather than blocked — it is a good
first substantial task. See [`../BUILD.md`](../BUILD.md#known-debt).
**Do not "fix" it by editing the hashes.**
