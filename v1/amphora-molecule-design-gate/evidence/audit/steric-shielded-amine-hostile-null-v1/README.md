# amphora-molecule-design-gate :: steric-shielded-amine-hostile-null-v1

**AUDIT_ONLY / falsification attack (ROTATION mode, 2026-08-15).** Does not
modify the live Rust runtime, the fixture, any locked dataset, the portfolio
manifest, or any signed Phase-0 KPI. Runs the REAL production code path
(`amphora_molecule_capabilities::design_gate_result` via
`capability(DESIGN_GATE_ID).evaluate_authorized`, invoked through the REAL
pinned RDKit C++ 2026.03.2 FFI — not a Python oracle, not synthetic facts).

## Claim under attack

`evidence/phase0/kpis/design-gate-structural-applicability-kpi.v1.json`
(observed 1.0 on all 7 metrics, sample n=42) and `docs/mission.md`'s primary
KPI ("negative-control rejection ... Zero silent acceptance of malformed,
unsupported, or unauthorized inputs ... every supplier TDS embeds the same
accept/reject filter before quoting mix ratios").

## Mechanism gap

`amphora-rdkit-ffi/src/bridge.cc::count_reactive_amine_hydrogens` (SHA-256
`7ce7798c9d0769307c704f4be0572f2333184261dd559630ebf7493df31c332a`) counts a
non-aromatic, formally-neutral nitrogen's attached H as a reactive amine
hydrogen unless a neighbor atom is a carbonyl carbon, sulfonyl sulfur, or
(non-cyanamide) amidine/guanidine carbon. Every existing exclusion clause —
including the six-clause refined predicate proposed by the module's own prior
`evidence/audit/nitrogen-nucleophilicity-authenticity-v1` finding — is
**electronic** (conjugation, formal charge, adjacency to an electron-
withdrawing group). None is **steric**. The 2,2,6,6-tetramethylpiperidine
motif underlying every commercial Hindered Amine Light Stabilizer (HALS)
carries a formally neutral, non-aromatic, non-conjugated secondary-amine N-H
with no disqualifying neighbor — it passes every clause — yet the four methyl
groups flanking the ring nitrogen sterically block electrophilic approach.
This is precisely why 2,2,6,6-tetramethylpiperidine and its N-H derivatives
are used to synthesize the persistent TEMPO nitroxide radical rather than
behaving as ordinary secondary-amine nucleophiles (Gugumus, "Possible
mechanisms of light stabilisation in polyolefins by HALS", Polymer
Degradation and Stability 40(2):167-215 (1993); Rabek, "Polymer
Photodegradation: Mechanisms and Experimental Methods" Ch. 3 (Chapman & Hall,
1995)). No supplier TDS for a HALS product publishes an amine value or AHEW,
and none markets it as an epoxy hardener; it is sold exclusively as a UV
light stabilizer, commonly post-added to marine topcoats at 0.5-2 wt%.

## Attack and result — CLAIM_REFUTED

Live RDKit FFI + live `design_gate_result`, 4 probes, real named/cited
molecules, declared role = `hardener`, `n_refutations=2/4`:

| id | citation | N-H count | observed | mechanistic expectation | match |
|---|---|---|---|---|---|
| `temp-2266-tetramethylpiperidine` | 2,2,6,6-tetramethylpiperidine (TEMP, CAS 768-66-1) | 1 | **SCORED** (role_appropriate_reactivity=true) | FAILED_GATES | **NO** |
| `tinuvin770-hals-diester` | bis(2,2,6,6-tetramethyl-4-piperidyl) sebacate (Tinuvin 770, BASF, CAS 52829-07-9) — real marine-topcoat UV stabilizer | 2 | **SCORED** (role_appropriate_reactivity=true) | FAILED_GATES | **NO** |
| `tinuvin292-hals-tertiary-control` | Tinuvin 292 (N-methylated tertiary analog, CAS 41556-26-7) | 0 | FAILED_GATES (`missing_role_appropriate_reactive_group`) | FAILED_GATES | yes |
| `piperidine-unhindered-secondary-amine-control` | piperidine (CAS 110-89-4) | 1 | SCORED | SCORED | yes |

The tertiary-amine control (Tinuvin 292) correctly fails via the pre-existing
tertiary-amine exclusion — the same mechanism already validated on BDMA in
campaign item T-08 — isolating that the failure is specific to the free-N-H
HALS grade. The unhindered secondary-amine control (piperidine) correctly
passes, showing the gate is not simply over-strict. Formula and structure for
every real named molecule (TEMP C9H19N, Tinuvin 770 C28H52N2O4, Tinuvin 292
C30H56N2O4) were independently confirmed by the live RDKit FFI parse against
the published formula.

**Tinuvin 770 is a real, named, currently-marketed marine-coating UV
stabilizer that the production `design_gate_result` path will admit as a
valid stoichiometric hardener if declared with `role: "hardener"`,
contradicting both the KPI's "every supplier TDS embeds the same
accept/reject filter" theory statement and the mission.md primary KPI's
"zero silent acceptance of ... unauthorized inputs" claim.**

This is a distinct physical mechanism from the previously-found electronic
gaps (protonation, thioamide, sulfonamide, guanidine/amidine — see
`nitrogen-nucleophilicity-authenticity-v1`) and is not closed by that prior
finding's proposed six-clause fix, which does not include a steric term.

## Reproducibility

- `work/harness/src/main.rs` (SHA-256
  `2ca172d579f98ffca51bc0180e1f02081c99040bb9caa40da803fcd5f20d0496`) — Rust
  harness calling the live production entry points directly, RDKit backend
  `2026.03.2` exact-version match confirmed (`backend_status()`)
- `work/harness/run_output.json` == `diagnostic.canonical.json` ==
  `diagnostic.runB.json`, byte-identical two-replay, SHA-256
  `61691488ecda52a873255592762f8eb03da9ad514a095c7540bb0c63cc7181f9`
- Per-probe `per_call_two_replay_byte_stable: true` on all 4 probes
  (independent double-invocation of `evaluate_authorized` per candidate)
- `steric-shielded-amine-hostile-null-receipt.v1.dsse.json` — DSSE
  PAE+Ed25519, `PHASE0_EVALUATOR` key, trust-store-pinned

## Not closed by this fire

Wiring a steric-shielding predicate into
`amphora-rdkit-ffi/src/bridge.cc::count_reactive_amine_hydrogens` (e.g. an
alpha,alpha'-disubstitution / Tolman-cone-angle-style neighbor-count clause
on the amine carbon substituents) and adding fixture records for the HALS
class is unresolved Phase-1 work, filed as a proposed followup, not attempted
here per module scope (`src/lib.rs` mutation requires a dedicated repair item
with its own re-attack per the repair-mode protocol).
