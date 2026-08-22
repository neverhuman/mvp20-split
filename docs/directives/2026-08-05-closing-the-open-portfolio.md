# AMPHORA COATING IP — INTERNAL DIRECTIVE
Closing the Open Portfolio — Adversarial Coverage, Verification Debt, and the Lab-in-the-Loop Program
Prepared 5 August 2026 · Supersedes nothing; operationalizes the 2026-08-04 portfolio status and the 2026-07-19 readiness program
AUDIT-ONLY framing preserved throughout · No promotion, procurement, safety, or product claim is authorized by this document

| How to read this document Section A is machine-consumable: campaign-backlog items in the loop's own T-/V-/X- syntax, ready to append to campaign.json in priority order. Section B is the human and governance directive — the credentialing, ceremony, merge, and rights actions the loop is forbidden from taking. Section C specifies each wet-lab experiment in the lab-in-the-loop program: design, endpoints, method standards, pre-registration, acceptance and kill gates, custody deliverables, and the exact data ask that unblocks it. One principle governs all three: no gate is weakened and no fixture is substituted to make a number move. A refutation is a success, an empty feasible set is a valid answer, and a claim that cannot be independently verified does not count. |
|---|

## Contents
1. Outstanding-issue inventory	3
1.2  Adversarial-coverage gaps — the 12 untested modules	3
1.3  Verification debt	4
1.5  Scientific gaps that only the lab can close	4
Section A — Autonomous-loop campaign block	6
A.1  Wave T2 — first attack on the 12 untested modules	6
A.2  Wave V2 — clear the verification debt	9
A.3  Wave X — data-integrity closeouts	9
Section B — Human and governance directive	10
B.2  Run the R-D07 re-evaluation ceremony	10
B.4  The six data and rights asks	11
Section C — Lab-in-the-loop experiment specifications	12
C.0  Common transfer path, promotion gate, kill/hold gate	12
C.1  Formulation coverage — seed campaign (30 / 3)	12
C.2  Barrier-corrosion campaign (210 panels / 40 systems)	13
C.3  Cure / pot-life campaign (36 runs)	13
C.4  Viscosity / sag campaign (288 cells)	14
C.5  Solvency / blend calibration	14
C.6  Molecule-property validation + dielectric labels (≥300)	15
C.7  Molecule-role blinded-label campaign	16
C.8  Design-rule second-formulator DoE	16
C.9  Independent chemistry red-team (96 + 32)	17
C.10  Process-QC prospective pilot (30 batches)	17
Sequencing and 90-day critical path	18
Appendix — acceptance-signal definitions	18

## 1. Outstanding-issue inventory
Every open item as of the 2026-08-04 pull, grouped by the kind of action that closes it. The right-hand column names the owner class: LOOP (autonomous, Section A), HUMAN (governance/rights, Section B), or LAB (wet-lab experiment, Section C). Items marked LOOP+ can be advanced autonomously but cannot be closed without a downstream human or lab action.
### 1.1 Provenance and governance

| Issue | Detail | Owner / closer |
|---|---|---|
| 17-vs-9 Phase-0 gap | 8 modules declare PHASE_0 but the CLI verifier derives PRE_PHASE_0; all 8 fail the single gate EVALUATION_RESULT_MISMATCH because a test harness overwrote the hash-pinned evidence bytes. Signatures valid; bindings broken; original bytes unrecoverable. | HUMAN — R-D07 dual-identity re-evaluation ceremony (tool built, never run) |
| Credentials absent | The ceremony and every future promotion require two distinct, non-revoked, non-development Ed25519 identities: PHASE0_EVALUATOR and PHASE0_INTERNAL_REVIEWER. The loop deliberately does not hold them. | HUMAN — B.1 |
| Trust-anchor floor | 0 of 186 pre-loop receipts verify against a trust-anchored key; 186 of 258 loop-era do. Remediation is triage, not mass re-signing. External materials must quote the derived number (9), never the declared (17). | HUMAN — B.1 (triage policy) |
| molecule-property not ceremony-restorable | It carries the identical broken binding but has no independent-review receipt and no movement event, so the ceremony's reconcile branch cannot restore it; it needs a full re-evaluation, not a re-bind. | HUMAN + LAB — B.2, C.6 |

### 1.2 Adversarial-coverage gaps
18 modules have been attacked; 12 mission-bearing modules have never met an adversary. Six of the twelve sit inside the Phase-0 binding gap, so their most consequential defect was found by a verifier rather than by a test. Their composite scores measure evidence density, not correctness — an unattacked score above 45 is a liability. Section A.1 writes a bespoke first-attack probe for each.

| Module | Probe | Why it matters / bespoke attack axis |
|---|---|---|
| candidate-contract | T-01 | First gate every candidate passes; test typed-payload override of MW/EEW/AHEW/group counts/identity via alternate encodings and homoglyph keys. |
| cro-protocol-packager | T-02 | In the Phase-0 gap. Attempt to flip execution_authorized, strip one of 8 claim locks, mutate a signed packet post-hoc. |
| envelope-gates | T-03 | Boundary/inclusive-margin gaming: inputs at 0 exactly, off-by-epsilon, NaN/inf; confirm hard-constraint fail-closed. |
| evidence-intake-validator | T-04 | In the Phase-0 gap. Spoofed signature, wrong key, stale receipt, hash mismatch, rights-unresolved intake. |
| formulation-arithmetic | T-05 | Mass-balance/stoichiometric identity attacks: inversion, non-finite, zero-group, unit drift, candidate override. |
| formulation-universe | T-06 | Also the R-D08 merge subject. Declarative-accounting vs real-feasibility conflation; does 'solved' leak into 'feasible'? |
| molecule-design-gate | T-08 | In the Phase-0 gap. Structural-applicability bypass; polymer/wildcard/invalid-valence/multicomponent; mutation attempt. |
| optimizer-orchestrator | T-09 | In the Phase-0 gap. Force a rank / final-aggregate / objective where none is authorized; feed conflicting envelopes. |
| process-qc-twin | T-10 | Adversarial drift masked as sensor noise; re-simulation determinism; also close the live V1-KPI-QC stalls. |
| report-packager | T-12 | In the Phase-0 gap. Claim-lock stripping, legacy-claim injection, quarantine-flag bypass, prohibited-claim scan evasion. |
| run-provenance | T-13 | Hash-chain break, replay divergence, event-chain tamper, Haber–Stornetta root manipulation. |
| source-ledger | T-14 | In the Phase-0 gap. Citation resolve-vs-support attack (source resolves but does not support the claim); rights-quarantine bypass. |

### 1.3 Verification debt
15 of 26 distinct repair items carry no independent verify. An unverified repair is a claim about a defect, not a closed defect. At the observed 3-in-13 verify-refutation rate, roughly three more landed repairs are wrong.
Second-generation repairs unverified. R-A06v2 (molecule-generator difunctional-count relabel) and R-A07v2 (molecule-novelty four-family fingerprint propagation) both landed against verify refutations and have not themselves been checked.
R-B02 unverified. The barrier-corrosion metrics.barrier_index fix landed but has not been independently verified, and the underlying n=3 literature-series problem is unchanged (needs R-D01).
### 1.4 Data-integrity residue and live incidents
sourceability-ehs CID defect. The pinned GHS KPI cites PubChem CIDs for IPDA and m-XDA that resolve to unrelated substances. R-N01 landed but the superseding hazard-card receipt has not; two of five hazard cards carry a live caveat that propagates into the solver-lab P3 demo.
Two live process-qc-twin stalls. Campaign item V1-KPI-QC produced no RUN_SUMMARY on its last two fires (background-wait stall); it has one fire of budget left. Diagnose or split before spending it.
Two corrupt ledger timestamps (residue). Rows for ip-fto-guard and the V-A12b verify carry a leading backslash; the generating defect is fixed, the append-only rows are permanent. Every downstream consumer must strip the prefix.
Schema-flip monitor. RESTORED_SCHEMA_FLIP has never fired; it is the one failure mode invisible to all three verification checks, so the log needs watching, not trusting.
Three unexplained missing fire hours (27 Jul 20:00, 29 Jul 20:00, 30 Jul 07:00). Add a cron-side heartbeat so a future gap is explained rather than merely observed.
### 1.5 Scientific gaps that only the lab can close
The surviving science is real but bounded, and every bound is the same shape: no owned, candidate-bound, wet-lab measurement exists anywhere in the portfolio, and no time-safe split exists. Phase-1 (independent higher-phase validation) is still zero. The lab-in-the-loop program (Section C) is the only route past that line. The specific scientific holes it fills:

| Module / claim | What the lab must supply |
|---|---|
| barrier-corrosion-score | Prospective wet-panel EIS + rust-creep on real coating systems with 10 untouched external systems; frozen KPI (barrier_index) exercised on real data at n well above the FEASIBILITY_FLOOR of 6. |
| cure-potlife-gate | DSC/pot-life across the full temperature range so the 40 °C extrapolation leg (currently 25.1% MAPE, breaching its 0.25 ceiling) is measured, not extrapolated; sealed holdouts to beat the chemistry-blind Q10=2 heuristic. |
| viscosity-score | Multi-temperature rheology + sag on real coatings so Krieger–Dougherty and Herschel–Bulkley — the two models actually implemented — can be benchmarked at all. |
| solvency-score | Owned calibration blends with measured Flory–Huggins χ / Hansen distance so the strongest module can be tested against a fair modern group-contribution method, not only the 1936 single-δ comparator. |
| molecule-property | ≥300 rights-clean eligible structures with measured Tg/density/RI, plus physically-admissible dielectric labels; this is the module the ceremony cannot restore. |
| molecule-role-ranker | Blinded, independently produced role/applicability labels and a held-out prospective candidate set to convert a contract-shaped rule into a validated classifier. |
| design-rule-score | Second-formulator DoE data; n=58 single-formulator is the binding constraint no modelling choice can fix. |
| process-qc-twin | A prospective 30-batch manufacturing pilot with seeded failures for a genuine Phase-1 attempt. |

## Section A — Autonomous-loop campaign block (machine-consumable)
Append these items to campaign.json in the order shown; the launcher's whole scheduling policy is first-pending-item-wins, so order is priority. Keep the backlog non-empty — refill before the pending count reaches single digits. Each item carries a max_fires budget, an explicit done_criteria, and a pre-committed refutation_criterion so a survival means something. The three operating invariants are unchanged: content-hash attribution against a pre-fire snapshot, real Ed25519 DSSE verification against the pinned key, and fire-id ledger binding.
### A.1 Wave T2 — first attack on the 12 untested mission-bearing modules
Each probe is written against the module's own declared claim, not a generic sweep. Six of these modules also sit in the Phase-0 binding gap; where they do, the probe additionally records the EVALUATION_RESULT_MISMATCH state so the attack and the ceremony share one evidence trail. Pre-commit: a fire that finishes materially faster than the 8m55s median is opened for inspection before its verdict is banked.

| T2-01  Typed-payload override injection module: amphora-candidate-contract attack: Submit candidate envelopes that attempt to supply or overwrite molecular_weight, EEW, AHEW, group_count and canonical identity through eight vectors: top-level key, array container, deep nesting, key-case variant, alternate key name, semantic-alt field, string container, and unicode-homoglyph key. done_criteria: All eight vectors rejected or ignored; identity recomputed from host graph; no candidate value reaches a typed downstream field. refutation_criterion: Any single vector causes a candidate-supplied value to be accepted into MoleculeFactsV1 or to survive into an EquivalentBalance. max_fires: 3 |
|---|

| T2-02  Packet authority and claim-lock integrity (Phase-0 gap) module: amphora-cro-protocol-packager attack: Attempt to (a) set execution_authorized:true, (b) strip or null each of the eight mandatory claim locks in turn, (c) mutate a signed CroProtocolPackageV2 by one byte, (d) inject a packet-authored performance/decision threshold. Record the module's EVALUATION_RESULT_MISMATCH state alongside. done_criteria: Status stays DRAFT_FOR_CRO_FEASIBILITY_REVIEW; every mutation invalidates the package; every stripped lock fails closed; no packet-authored threshold is honored. refutation_criterion: Any mutation verifies, any lock is bypassable, or a packet-authored threshold is accepted. max_fires: 3 |
|---|

| T2-03  Inclusive-margin and boundary gaming module: amphora-envelope-gates attack: Feed inputs that land exactly on 0, one ULP inside and outside every inclusive margin, plus NaN/±inf/denormal and unit-swapped values; probe the excursion-invariance theorem for a value-free bypass. done_criteria: Hard-constraint fail-closed on all invalid inputs; inclusive margins enforced deterministically; abstention on undecidable cases, never silent pass. refutation_criterion: Any invalid or boundary-gaming input yields a PASS or a non-abstaining scalar. max_fires: 2 |
|---|

| T2-04  Intake spoofing and rights bypass (Phase-0 gap) module: amphora-evidence-intake-validator attack: Present receipts that are (a) signed by a non-anchored/dev key, (b) structurally valid but hash-mismatched to their artifact, (c) stale/revoked, (d) rights-unresolved or quarantined. Record EVALUATION_RESULT_MISMATCH state. done_criteria: Every spoofed, mismatched, stale, or rights-unresolved receipt is rejected at intake with a typed reason; the pinned trust store is the only accepted anchor. refutation_criterion: Any of the four categories is admitted, or a name-based key check is shown to substitute for signature verification. max_fires: 3 |
|---|

| T2-05  Stoichiometric identity and mass-balance attack module: amphora-formulation-arithmetic attack: Drive EquivalentBalanceV1 with inverted ratios, non-finite inputs, zero-group operands, mixed/incorrect unit provenance, and candidate MW/EEW/AHEW override attempts; check phr = 100·m_h/m_r and n_e = m_r/EEW recompute from host facts only. done_criteria: All override paths absent; zero-group abstains; non-finite and inversion rejected with reason; full record recomputes on revalidation. refutation_criterion: Any candidate-supplied constant enters the balance, or an inverted/non-finite case returns a scalar instead of failing closed. max_fires: 3 |
|---|

| T2-06  Accounting-vs-feasibility conflation (merge evidence) module: amphora-formulation-universe attack: Enumerate the Cartesian space and test whether the DECLARATIVE_ACCOUNTING_ONLY feasibility basis leaks into any downstream feasibility or ranking claim; overlay real dosing/envelope/hazard gates and check the count of genuinely feasible cells is reported distinctly from cardinality. This fire's finding feeds the R-D08 merge decision. done_criteria: Cardinality and feasibility reported as separate quantities; no 'solved' cell is presentable as feasible; identity of every enumerated cell is stable. refutation_criterion: A cardinality count is surfaced as a feasibility claim, or the module asserts any science beyond enumeration (which would also void the merge case). max_fires: 2 |
|---|

| T2-08  Structural-applicability bypass (Phase-0 gap) module: amphora-molecule-design-gate attack: Submit polymers, wildcard atoms, invalid valences, multi-component species, and a chemistry-changing mutation request; attempt to reach a non-fail-closed decision. Record EVALUATION_RESULT_MISMATCH state. done_criteria: Every out-of-domain input fails closed; mutation stays QUARANTINED_NO_STRUCTURE_CHANGE; no structure-changing operation is authorized. refutation_criterion: Any out-of-domain input passes, or a structure-changing mutation is admitted. max_fires: 3 |
|---|

| T2-09  Unauthorized ranking / objective emission (Phase-0 gap) module: amphora-optimizer-orchestrator attack: Feed a full set of typed module envelopes and attempt to induce a RANK, a FINAL AGGREGATE SCORE, or an eligible objective under the signed zero-ranking policy; feed mutually contradictory envelopes and check the policy solver composes rather than averages. Record EVALUATION_RESULT_MISMATCH state. done_criteria: RANK: NONE and FINAL AGGREGATE SCORE: NOT AUTHORIZED under all inputs; solver composes PASS/FAIL/ABSTAIN/NOT_APPLICABLE without averaging; the module remains implementation-free policy enforcement. refutation_criterion: Any input yields a rank, an aggregate score, or an authorized objective; or the solver is shown to average scores. max_fires: 3 |
|---|

| T2-10  Adversarial drift + stall closeout module: amphora-process-qc-twin attack: Run the 128-tamper adversarial process-drift corpus with tampers masked as sensor noise; verify byte-identical re-simulation over the 60 canonical paths. FIRST resolve the two live V1-KPI-QC background-wait stalls (diagnose or split the item) before spending the last budgeted fire. done_criteria: 100% re-simulation determinism; drift/tamper detection on all 128; V1-KPI-QC either lands a verdict or is split into fitting sub-items with a RUN_SUMMARY. refutation_criterion: Any tamper is masked as noise, re-simulation diverges, or the item stalls a third time with no RUN_SUMMARY. max_fires: 3 |
|---|

| T2-12  Claim-lock and quarantine bypass (Phase-0 gap) module: amphora-report-packager attack: Attempt to package a report that (a) strips a claim lock, (b) reintroduces a legacy/retracted claim, (c) evades the prohibited-claim scan via encoding tricks, (d) clears the quarantine flag on quarantined evidence. Record EVALUATION_RESULT_MISMATCH state. done_criteria: Every prohibited claim is caught; quarantine flag cannot be cleared from within a packet; claim-lock binding survives all four vectors. refutation_criterion: Any prohibited claim, legacy claim, or quarantine bypass reaches a packaged report. max_fires: 3 |
|---|

| T2-13  Hash-chain and replay integrity module: amphora-run-provenance attack: Break the Haber–Stornetta hash chain at a mid-point, diverge a replay input/output pair, tamper an event-chain entry, and attempt a root-hash recompute that reconciles a forged history. done_criteria: Any chain break, replay divergence, or event tamper is detected on the next replay; root_hash_recompute_match_rate = 1.000 only for untampered histories. refutation_criterion: A forged or diverged history verifies as intact. max_fires: 2 |
|---|

| T2-14  Resolve-vs-support citation attack (Phase-0 gap) module: amphora-source-ledger attack: Insert citations whose URLs/DOIs resolve and DSSE-verify but do not actually support the claim they are attached to; attempt to bypass rights-quarantine; feed ISO-690-malformed records. Record EVALUATION_RESULT_MISMATCH state. done_criteria: Resolve-and-verify is shown to be insufficient — support is checked at the claim level; quarantined rights cannot be laundered; malformed records rejected. refutation_criterion: A resolving-but-non-supporting citation is accepted as support, or quarantined evidence enters promotion. max_fires: 3 |
|---|

| On the two T-series items not reissued here T-07 (model-card-authority) and T-11 already target modules that have since picked up verdicts (model-card-authority via V1-KPI-MCA, redteam-audit via waves R/V1). Leave them queued for a genuinely adversarial second pass, but they are lower priority than the twelve zero-verdict modules above. |
|---|

### A.2 Wave V2 — clear the verification debt
Fifteen distinct repair items and three second-generation repairs carry no independent verify. Each item below dispatches a separately-authored fire — one that did not write the repair and cannot see its reasoning — pre-committed to CLAIM_REFUTED if no repair receipt exists. Prioritize the second-generation repairs first, because they were born from refutations.
V2-A06v2 — verify molecule-generator R-A06v2 against the active-hydrogen (AHEW) functionality convention the portfolio already uses; re-derive amine_sites/active_nh from raw SMILES; escalate past the repair's own frame.
V2-A07v2 — verify molecule-novelty R-A07v2 by propagating the corrected IPDA structure into all four fingerprint families (maccs_166, atompair_2048, toptorsion_2048, morgan) and diffing against the shipped table.
V2-B02 — verify barrier-corrosion R-B02 (barrier_index now computed) with a from-scratch re-implementation; confirm the metric is non-null on every live path and record that n=3 remains below FEASIBILITY_FLOOR pending R-D01.
One V2-* item per remaining unverified repair (12 more), each a fresh-harness re-derivation with at least one novel probe never in the repair's set. Refutation criterion for all: the repair reproduces numerically but fails a convention, propagation, or sufficiency check the repair did not test.
### A.3 Wave X — data-integrity closeouts
X-EHS-CID — land the superseding sourceability-ehs hazard-card receipt: fresh live PubChem fetch of CAS-correct CIDs for IPDA and m-XDA, re-derive H-statement sets, re-evaluate procurement gates, and clear the caveat that currently propagates into solver-lab P3.
X-LEDGER-TS — ship and prove the parser guard that strips the leading-backslash timestamps for ip-fto-guard and V-A12b; the append-only rows stay, the read path must tolerate them (regression test included).
X-HEARTBEAT — add the cron-side heartbeat that records an attempted fire even when the agent never starts, so the three missing hours (and any future gap) are explained rather than observed.
X-SCHEMA-WATCH — keep the RESTORED_SCHEMA_FLIP autocommit guard under active log review; it is the only failure mode invisible to the three verification checks.
X-SOLVER-P3 — implement solver-lab constraint relaxation with an explicit audit trail (what was relaxed, by whom, under what authority) so an EMPTY_FEASIBLE_SET becomes an actionable answer rather than a dead end — but gated behind X-EHS-CID, since P3's blocking set is provisional until the CID defect is fixed.

## Section B — Human and governance directive
Everything here is an action the loop is forbidden from taking. The ordering is by what stops the most downstream work if left undone.
### B.1 Register the two trusted signer identities (blocks everything)
Mint and prove possession of two distinct, non-revoked, non-development Ed25519 identities: PHASE0_EVALUATOR and PHASE0_INTERNAL_REVIEWER. Neither may be a repository-local or dev key; cross-role reuse is rejected by design.
Add both public keys to config/phase0-trust-store.v1.json and record the addition under the founder-signed master manifest.
Adopt the triage policy for pre-loop receipts: do not mass re-sign. 0 of 186 pre-loop receipts anchor; re-signing history would make the chain look clean while destroying the tamper-evidence distinction. Triage per-receipt; the founder-signed 66-receipt manifest remains the human trust boundary for pre-loop evidence.
Fix external messaging: the quotable Phase-0 count is 9, not 17; scope any 'portfolio' statement to the 17 attacked modules, never the full 40 crates (12 are pure runtime, one — solver-lab — has no mission.md yet).
### B.2 Run the R-D07 re-evaluation ceremony (restores 8 of 9 modules)
The governed path was built and tested (WV-1) and has never been executed. It restores the eight gap modules and closes the 17-vs-9 discrepancy. It cannot restore molecule-property.
portfolio phase0 re-evaluate --module <M> --reason <text> --as-of <ts> --evaluation-key <external> --review <signed> [--dry-run]
Exact four-step procedure per module (from WV-1/work/exact-human-command.json): dry-run to read the target receipt hash → rehearse in a scratch rsync copy to mint the matching review → obtain the fresh independent-review signature from the second identity → issue one governed command in the authoritative tree. The tool refuses unless the module is on the unbound list and its result is live-hash-unbound (doubly enforced), refuses a single signature, refuses a repo-local key, and archives the prior receipt/review/result/movement under evidence/phase0/superseded/<sha>/.
Repairable (8): cro-protocol-packager, evidence-intake-validator, known-answer-benchmarks, molecule-design-gate, optimizer-orchestrator, redteam-audit, report-packager, source-ledger. Each lands PRE_PHASE_0/promotable and is then re-promoted via the existing phase0 promote command.
Not repairable this way: molecule-property — no review receipt, no movement event; route it through the full re-evaluation + the C.6 lab validation instead. Do not let a summary round 8 up to 9.
### B.3 Decide R-D08 — the formulation-universe merge
amphora-formulation-universe has zero ledger verdicts, carries no science of its own, and its entire defensible claim is a strict subset of amphora-formulation-arithmetic's. Merging loses no defensible claim and removes a module from every portfolio count — a smaller honest denominator beats a larger padded one. Hold the decision until T2-06 (Section A.1) runs: if that first attack finds independent value, the merge is withdrawn. Owner: portfolio-shape decision; the loop is forbidden from taking it.
### B.4 The six data and rights asks (each one human action)
Between them they gate most of the portfolio's remaining scientific upside and every one of the Section C experiments. Send them in this order.

| Ask | Action | Unlocks |
|---|---|---|
| R-D01 | Send the prepared USBR ST-19168 RIGHTS-REVIEW-REQUEST to USBR RISE; confirm public-domain under 17 U.S.C. §105. | The entire barrier-corrosion wet-panel campaign (C.2). Critical path — the package is written and signed, it needs a human to send it. |
| R-D02 | File/escalate the USBR RISE request for frequency-resolved raw EIS sweeps (queue #3/#14; rights already verified public-domain). | public-corrosion-benchmark's move from a correctly-stated negative result to a positive one; feeds C.2. |
| R-D03 | Counsel question: does the Reynolds 2024 CC BY-NC-ND licence permit internal, non-distributed, AUDIT_ONLY quantitative benchmarking? | viscosity-score's Krieger–Dougherty benchmark (C.4). This is a rights wall, not a data wall — the loop found the dataset and stopped. |
| R-D04 | Ratify or downgrade the cure fixture's self-asserted CC0 via a signed rights receipt (queue #7). | cure-potlife-gate's structural integrity, independent of the science fix in C.3. |
| R-D05 | Contact PURformance authors re a sibling HTE release, or commission a DoE (queue #8). | design-rule-score — n=58 single-formulator is the binding constraint no model can fix (C.8). |
| R-D06 | Confirm with RadonPy/PI1070 authors whether dielectric trajectories were production-converged; locate an OpenPoly-matched density field (queues #10/#11). | molecule-property dielectric labels (currently 89.5% physically inadmissible) and the second density corpus (C.6). |

### B.5 Contract the counterparties
The lab program needs eight independent roles; none may be collapsed into the portfolio team, and the two signer roles (evaluator, reviewer) must be distinct from each other and from the lab.
Contract laboratory — returns raw, candidate-bound data with custody and deviation records.
Independent evaluator — executes locked analysis and signs results under PHASE0_EVALUATOR.
Independent reviewer — a different trusted signer under PHASE0_INTERNAL_REVIEWER; checks method and claims.
Statistician — owns splits, intervals, and the pre-registered gates.
Chemistry labeling — produces blinded role/applicability labels (for C.7).
Data curation — resolves identity, units, rights, and deduplication.
Counsel — bounds rights, IP, and freedom-to-operate (R-D03, and every rights receipt).
Founder / owner — protects claim ceilings and stops failed campaigns.

## Section C — Lab-in-the-loop experiment specifications
The system cannot train further without owned, candidate-bound, measured evidence. Section C specifies the experiments that produce it. Every experiment is preregistered and hash-locked before a single measurement is taken, returns raw data under custody, and is gated on the common promotion and kill rules in C.0. Spend is justified only if the return is owned, candidate-bound raw evidence with custody, rights, locked analysis, and two independent signatures — a completed campaign promises nothing by itself.
### C.0 Common transfer path, promotion gate, and kill/hold gate
Transfer path (every experiment follows it): candidate-bound draft packet (execution_authorized:false) → external execution at the contract lab (method, custody, deviations) → signed candidate-bound raw return (with uncertainty) → independent review by a distinct signer → policy decision. A packet is a structured question, not an instruction to execute; a fixture is not independent validation; a similarity observation is not novelty.

| Promotion gate — all must hold Raw evidence complete and rights-eligible; custody unbroken. Split and benchmark locks match the pre-registration byte-for-byte. Predefined thresholds pass; uncertainty quantified (conformal + bootstrap, not point-only). Evaluator and reviewer are distinct trusted signers; claim locks intact; exactly one valid movement event exists. |
|---|
| Kill / hold gate — any one stops the campaign Rights failure, custody break, or split leakage. Method mismatch vs the pre-registered protocol, or insufficient sample. Baseline non-superiority, or a confidence interval that crosses the pre-registered floor. Signer conflict, or any pressure to broaden the signed applicability domain. |

On failure, no threshold is weakened and no fixture is substituted. The failure is recorded as a signed negative result and the module does not move. That is the correct outcome, not a setback.
### C.1 — Formulation coverage — the seed campaign (30 formulations / 3 families)

| Objective | Produce the owned, candidate-bound seed set that every other experiment binds to: a rights-clean cohort spanning three epoxy-amine families, selected without reference to model predictions. |
|---|---|
| Design | 30 formulations across 3 families (e.g. DGEBA/aliphatic-amine, DGEBA/cycloaliphatic-amine, DGEBA/aromatic-amine adduct). Seeded maximin selection in descriptor space — no endpoint labels, no model ranks, no predicted-performance selection. Each formulation carries a candidate hash and a signed CRO feasibility packet. |
| Endpoints | None measured here beyond identity, mix ratio (phr from EquivalentBalanceV1), and rights/custody. This is the substrate, not a performance test. |
| Pre-registration | Family definitions, maximin seed, and selection code hash-locked before any candidate is drawn. Splits for downstream experiments are declared here and never re-drawn. |
| Acceptance gate | 30 candidate-bound records with resolved identity, units, and rights; zero selection-by-prediction; byte-stable two-replay of the selection. |
| Kill / hold | Any rights-unresolved ingredient; any evidence of endpoint or model leakage into selection. |
| Deliverables | Signed candidate roster, per-candidate rights receipts, maximin selection receipt, hash manifest. |
| Counterparties | Data curation, counsel, statistician (owns the split declaration). |
| Dependencies | Ingredient-library facts (already load-bearing); no R-D blocker — this can start on credentials (B.1) alone. |

### C.2 — Barrier-corrosion campaign (210 panels / 40 systems, incl. 10 untouched external)

| Objective | Move barrier-corrosion-score toward Phase-1 by exercising its frozen KPI (barrier_index) on real, prospective coated-panel data at n well above its own FEASIBILITY_FLOOR of 6 — the current three literature series (n=3–5) are combinatorially incapable of reaching α=0.05. |
|---|---|
| Design | 210 panels across 40 coating systems; 10 of the 40 are untouched external systems reserved for a held-out generalisation test the model has never seen. Immersion / salt-spray per ASTM B117; electrochemical impedance spectroscopy (EIS \|Z\|) plus rust-creep at day-56 endpoints; frequency-resolved sweeps (unlocked by R-D02). |
| Endpoints | Day-56 EIS \|Z\| at the low-frequency limit, rust-creep from scribe, and the ranked barrier_index the locked KPI actually computes. Environment split by marine/chloride vs not, and a temperature-regime hold-out (calibrate ≤308 K, test >308 K) — both already probed digitally and both moved the right way, so the wet data tests a real, pre-identified stress. |
| Pre-registration | The st19168-preregistered-v1 protocol (exact/MC permutation primary test, fixed-sequence bootstrap superiority gates) is already hash-locked and was stress-tested on pinned-seed synthetic shadow data. Freeze the metallurgical-family GroupKFold partition (17 families) so alloy aliases cannot straddle folds. |
| Acceptance gate | barrier_index computed and non-null on every real-data path; superiority over null-median on the group-safe split with a bootstrap CI excluding zero; conformal coverage ≥ target on the 10 untouched external systems. |
| Kill / hold | n below FEASIBILITY_FLOOR after attrition; CI crosses zero on the group-safe partition; any external system leaks into calibration. |
| Deliverables | Raw EIS spectra and creep images under custody, per-panel candidate binding, signed evaluator analysis, independent reviewer sign-off. |
| Counterparties | Contract corrosion lab, statistician, evaluator, reviewer, counsel (rights). |
| Dependencies | R-D01 (ST-19168 rights confirmation — critical path) and R-D02 (RISE frequency-resolved EIS). C.1 seed set for the internal systems. |

### C.3 — Cure / pot-life campaign (36 runs: 24 fit + 12 sealed holdouts)

| Objective | Replace the extrapolated 40 °C pot-life leg — currently 25.1% MAPE, breaching the module's own 0.25 ceiling with 12/12 systematic under-prediction — with measured data, and settle whether the per-system published Arrhenius Ea is load-bearing against a chemistry-blind Q10=2 heuristic that currently matches it. |
|---|---|
| Design | 36 primary runs: 24 fit runs across ≥4 amine chemistries plus 12 sealed primary holdouts revealed only at analysis. DSC-based reaction-Ea (Kissinger / OFW-Doyle / Starink) with external method comparability against a CC-BY reference (e.g. Lascano 2019 DGEBA+IPDA); pot-life measured directly, not inferred. |
| Endpoints | Reaction Ea per system; pot-life MAPE per temperature leg (10/30/40 °C explicitly); head-to-head vs the Q10=2 acceleration-factor heuristic on the identical truth table; the held-out-temperature-extrapolation MAPE against the 0.25 ceiling. |
| Pre-registration | Falsification criterion locked before reveal: any measured reaction-Ea breaching the held-out-extrapolation (0.25) or per-point (0.40) ceiling, or the Q10=2 heuristic matching/beating the Arrhenius model on ≥2 of 3 legs, refutes the load-bearing claim. |
| Acceptance gate | Arrhenius model beats Q10=2 on all measured legs including 40 °C, within the ceilings, on the sealed holdouts; stratified disclosure (with-phr vs without-phr) reported. |
| Kill / hold | 40 °C leg still breaches 0.25; Q10=2 parity persists on measured data; fixture rights unresolved (R-D04). |
| Deliverables | Raw DSC thermograms, pot-life logs, per-system Ea with uncertainty, sealed-holdout reveal receipt. |
| Counterparties | Contract thermal-analysis lab, evaluator, reviewer, statistician, counsel (R-D04). |
| Dependencies | R-D04 (cure fixture rights ratification). C.1 seed chemistries. |

### C.4 — Viscosity / sag campaign (288 cells, three temperatures)

| Objective | Give viscosity-score any benchmark at all for the two rheology models it actually implements — Krieger–Dougherty and Herschel–Bulkley — which currently cannot be tested for want of data. |
|---|---|
| Design | 288 cells = a factorial over three temperatures × shear conditions × formulation set, measuring apparent viscosity, Krebs units (ASTM D562), and sag (ASTM D4400). Herschel–Bulkley τ0/K/n fitted per cell; Krieger–Dougherty φmax fitted where a pigment/filler η(φ) ladder is available. |
| Endpoints | HB parameter recovery vs the module's exact equation on real data; sag endpoint prediction; multi-temperature apparent-viscosity error. The FFW-physics-beats-ML result (+0.144 R²) is re-tested here on measured data with proper uncertainty (the digital version has none). |
| Pre-registration | A locale/typography data-integrity control is mandatory — the digital campaign found a 13–169× literal-reading trap; the wet protocol pre-registers unit and axis-bound gates before accepting any transcribed comparator. |
| Acceptance gate | HB and KD parameters recovered within pre-registered bounds on ≥ the planned cell count; multi-temperature error quantified with conformal + bootstrap intervals; sag predictions gated on measured monotonic shear-thinning. |
| Kill / hold | No rights-clean η(φ) ladder available and R-D03 returns unfavourable; uncertainty absent; typography trap unresolved. |
| Deliverables | Raw rheograms, Krebs/sag logs, per-cell HB/KD fits with CIs, custody records. |
| Counterparties | Contract rheology lab, evaluator, reviewer, statistician, counsel (R-D03). |
| Dependencies | R-D03 (Reynolds 2024 CC BY-NC-ND counsel review) for the φmax ladder. C.1 formulation set. |

### C.5 — Solvency / blend calibration campaign

| Objective | Convert the portfolio's strongest module (solvency-score, the one the verifier actually derives at Phase-0) from 'beats a 1936 single-δ model' to a candidate-bound result fair against a modern group-contribution method. |
|---|---|
| Design | A preregistered blend campaign on owned calibration blends: measure solubility / phase stability and back out Flory–Huggins χ and Hansen distance for epoxy-amine + thinner/reactive-diluent pairs drawn from the C.1 families. Leave-solute-out CV preserved; duplicate-contradiction excision (the 517 contradictory groups) applied before fitting. |
| Endpoints | Leave-solute-out RMSE on measured blends vs a modern group-contribution baseline (not only Hildebrand single-δ); Hansen δd/δp/δh recovery within the admissible envelope [9.6, 59.9] MPa^0.5; coverage-gated instrument abstentions counted, never zero-filled. |
| Pre-registration | The fair-fight baseline (a named modern group-contribution method) is fixed in advance; the coverage gate and abstention accounting are locked before measurement. |
| Acceptance gate | Measured-blend RMSE beats the modern baseline on the locked split with a bootstrap CI excluding parity; Hansen parameters inside the admissible envelope; degenerate-baseline check passes (no ~1e-35 slope collapse). |
| Kill / hold | Parity with the modern baseline; any Hansen parameter outside the admissible envelope; leakage between calibration and validation blends. |
| Deliverables | Raw solubility/phase data, measured χ and Hansen values with uncertainty, baseline comparison receipt. |
| Counterparties | Contract formulation/analytical lab, evaluator, reviewer, statistician. |
| Dependencies | C.1 seed blends; no external R-D blocker. |

### C.6 — Molecule-property validation + dielectric labels (≥300 eligible structures)

| Objective | Supply the measured labels that let molecule-property — the one module the R-D07 ceremony cannot restore — be re-evaluated on real data, and replace the dielectric arm that currently has NO COMPETENT MODEL (all arms R² ≤ 0 on the physically-valid subset). |
|---|---|
| Design | ≥300 deduplicated, rights-clean eligible structures with exact-toolkit identity/formula/mass reconciliation, carrying measured Tg, density, refractive index, and — critically — physically-admissible dielectric (εr) labels satisfying εr,static ≥ n². Impose a chemically-coherent held-out split (scaffold/source-safe), not the random 60/20/20 that flatters the current numbers. |
| Endpoints | MAE for Tg / density / RI under the coherent split (the honest applicability domain, narrower than the current KPI surface); a dielectric model that beats the test-set mean on the physically-valid subset — currently none exists; cross-corpus transfer (the digital version failed this). |
| Pre-registration | ≥300 eligible-structure floor, exact toolkit reproduction, and the coherent-split definition locked before evaluation; dielectric admissibility filter (εr ≥ n²) applied before any fit. |
| Acceptance gate | Coherent-split MAEs within pre-registered bounds; a dielectric arm with R² > 0 on admissible rows; cross-corpus transfer non-degrading; exact toolkit + identity + mass + rights reconciliation clean. |
| Kill / hold | Fewer than 300 eligible after dedup/rights; dielectric labels still physically inadmissible after R-D06; toolkit drift; cross-corpus collapse. |
| Deliverables | Rights-clean labelled corpus, admissible dielectric label set, coherent-split reconciliation receipt, independent review. |
| Counterparties | Data curation, contract measurement lab (where labels are unavailable), evaluator, reviewer, statistician, counsel. |
| Dependencies | R-D06 (RadonPy production-convergence confirmation + OpenPoly-matched density field). Feeds B.2's full re-evaluation of molecule-property. |

### C.7 — Molecule-role blinded-label campaign

| Objective | Convert molecule-role-ranker's contract-shaped, well-defended-but-unvalidated rule into a validated classifier by giving it an independent, blinded, prospective test set — it currently has none. |
|---|---|
| Design | An independent chemistry-labeling counterparty produces blinded role/applicability labels for a held-out prospective candidate set (resin vs hardener vs accelerator vs null), disjoint from every fixture the module has seen. Includes hostile nulls (tertiary-amine accelerators, latent hardeners) and industrially-dominant guanidine-class accelerators (DPG, DOTG) that a prior refutation exposed as a chemotype gap. |
| Endpoints | Role-classification agreement on the blinded held-out set with a pre-registered numeric threshold (the current agreement rate has none); zero direction-rule reversals under the measured labels (the digital MC survived 0/6 and 0/12 — the wet set must not reverse either). |
| Pre-registration | The numeric agreement threshold and the hostile-null / guanidine coverage are locked before labels are revealed; labels are blinded to the model. |
| Acceptance gate | Agreement above threshold on the blinded set; no reversal of the amine-direction rule; guanidine chemotype covered. |
| Kill / hold | Below-threshold agreement; any direction-rule reversal; label leakage. |
| Deliverables | Blinded label set + provenance, held-out agreement receipt, independent review. |
| Counterparties | Chemistry labeling (independent), evaluator, reviewer, statistician. |
| Dependencies | C.1 candidate set; no external R-D blocker beyond labeler contracting. |

### C.8 — Design-rule second-formulator DoE

| Objective | Break the binding constraint on design-rule-score — n=58 unique observations from a single formulator, which no modelling choice can fix — by acquiring independent second-formulator data. |
|---|---|
| Design | Either secure the sibling PURformance HTE release or commission a designed experiment (DoE) from a second, independent formulator, materially expanding n and adding a cross-formulator generalisation axis. The leak-free dedup partition (first-appearance) is preserved; the physics arm (Guth–Gold, C=0.7111) is the defensible baseline, not the memorised ML arm. |
| Endpoints | Leak-free ΔR² with a bootstrap CI that no longer crosses zero at the new n; cross-formulator transfer; Guth–Gold concordance CI lower bound above chance under a nested train-refit bootstrap. |
| Pre-registration | The dedup first-appearance partition, the Guth–Gold physics baseline, and the CI floor are locked before the new data is fitted. |
| Acceptance gate | ΔR² CI excludes zero at the expanded n; cross-formulator transfer non-degrading; physics-arm concordance holds. |
| Kill / hold | CI still crosses zero; overlap/leakage with the molecule-property training set; single-source data only. |
| Deliverables | Second-formulator raw DoE, expanded-n analysis, cross-formulator receipt. |
| Counterparties | PURformance authors or a second contract formulator, evaluator, reviewer, statistician. |
| Dependencies | R-D05 (sibling HTE release or commissioned DoE). |

### C.9 — Independent chemistry red-team (96 attacks + 32 valid controls)

| Objective | Run the chemistry-specific sealed red-team the digital 24-axis suite does not substitute for: 96 malicious cases plus 32 valid controls across 16 attack families, authored and sealed by the independent reviewer, executed once. |
|---|---|
| Design | 96 planned adversarial chemistry payloads (spoofed identity, unit ambiguity, computed-as-measured, authority escalation, hazard-set omission, resolve-vs-support citations, …) + 32 valid controls, across 16 families; sealed reviewer payloads revealed only at execution. Distinct from the 30,000-negative deterministic corpus already promoted (which is baseline coverage, not chemistry-specific). |
| Endpoints | Silent-malicious-acceptance rate (must be 0); valid-control acceptance (must be 32/32); zero unauthorized rank/objective; zero stripped claim locks; byte-identical clean replay. |
| Pre-registration | The 96/32 payload set is sealed by the reviewer before execution; acceptance criteria locked; the agent that runs it did not author it. |
| Acceptance gate | 0 silent malicious acceptances, 32/32 valid controls accepted, 0 rank/objective emissions, 0 stripped locks, clean two-replay. |
| Kill / hold | Any silent malicious acceptance; any valid control rejected; any lock stripped. |
| Deliverables | Sealed payload manifest, execution ledger, reviewer sign-off, replay receipt. |
| Counterparties | Independent reviewer (authors + seals), evaluator, founder (claim-ceiling guard). |
| Dependencies | Credentials (B.1); runs against the whole tree, so best after A.1/A.2 have hardened the modules. |

### C.10 — Process-QC prospective pilot (30 batches, seeded failures)

| Objective | Give process-qc-twin a genuine Phase-1 attempt — the current claim is byte-stable re-simulation and adversary-drift detection on fixtures, which explicitly does not exercise wet-lab drift. |
|---|---|
| Design | A prospective 30-batch manufacturing pilot with deliberately seeded process failures (shear-history excursions, drift, missingness), measured against the deterministic twin; independent review of the drift-detection calls. Herschel–Bulkley / Cox–Merz constitutive baselines apply. |
| Endpoints | Prospective drift-detection rate on seeded failures (real, not tampered fixtures); false-positive rate on nominal batches; re-simulation determinism against measured shear histories. |
| Pre-registration | The 30-batch design, the seeded-failure set, and the detection thresholds are locked before the pilot runs. |
| Acceptance gate | Seeded failures detected above threshold with a bounded false-positive rate on nominal batches; determinism holds against measured histories. |
| Kill / hold | Missed seeded failures; unbounded false positives; the two live V1-KPI-QC stalls unresolved (see A.3 / T2-10). |
| Deliverables | Batch records, seeded-failure key, detection-call ledger, independent review. |
| Counterparties | Contract manufacturing / pilot line, evaluator, reviewer, statistician. |
| Dependencies | Resolve the process-qc-twin stalls first (T2-10, A.3); no external R-D blocker. |

## Sequencing and 90-day critical path
The dependency structure is strict: credentials gate the ceremony and every signed lab return; the six rights asks each gate one experiment; the loop waves can run in parallel with all of it because they need no human input beyond being appended to the backlog.

| Window | Governance / loop | Lab |
|---|---|---|
| Days 0–14 | B.1 credentials; append Wave T2 + V2 + X to the backlog; run R-D07 ceremony (8 modules); send all six R-D asks; hold R-D08 pending T2-06. | Contract the eight counterparties; C.1 seed campaign begins (needs credentials only). |
| Days 15–45 | Loop clears verification debt (V2) and lands the 12 first-attack probes (T2); X-series closeouts land; molecule-property routed to full re-evaluation. | On rights confirmations: C.3 (cure), C.4 (viscosity), C.5 (solvency), C.6 (property labels), C.7 (role labels) execute; C.2 (barrier) starts once R-D01/R-D02 clear. |
| Days 46–90 | C.9 sealed red-team runs against the hardened tree; promotion ceremonies only for modules that pass their locked gates. | C.2 day-56 endpoints read out; C.8 second-formulator DoE; C.10 process-QC pilot; independent evaluation + review + signed movement per module. |

| The single most important sequencing fact Nothing crosses the Phase-1 line — independent higher-phase validation — until at least one experiment in Section C returns a signed, candidate-bound measurement that passes its locked gate under two distinct trusted signatures. Until then, derived Phase-0 is a provenance statement, not a scientific one, and the honest external number stays at 9 modules, 0 at Phase-1. The lab is not an accelerant on the current trajectory; it is the only thing that changes the trajectory. |
|---|

## Appendix — acceptance-signal definitions
Refutation — a pre-committed, genuinely falsifiable attack could have broken the claim and did. A first-class success.
Survival — the same, but the claim held. Only counts if the attack had a real path to refutation; graded on the specific criterion it withstood.
Independent verify — a separately-authored fire, blind to the repair's reasoning, re-derives from scratch and escalates past the repair's own frame. Pre-committed to CLAIM_REFUTED if the repair receipt is absent.
Derived Phase-0 — the CLI verifier reconstructs the phase from the latest valid module-local movement event with two distinct trusted signatures. A provenance property, not a scientific one.
Phase-1 — a locked external benchmark passes under independent evaluation and review within a signed domain. Currently zero, and only Section C can move it.
Empty feasible set — a valid, honest answer. A solver that always returns a recommendation has learned to satisfy its caller, not its constraints.

Prepared for the founder, 5 August 2026. AUDIT-ONLY throughout: no product qualification, procurement, safety, synthesis, or freedom-to-operate authority is asserted or granted by this document.
