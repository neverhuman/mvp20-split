# Amphora | Specification reconciliation and traceability

All three complete attachments were read. `specification_register.json` retains exact byte/line fingerprints. Raw attachment text and private file links are excluded from Git. Section ranges below identify user-supplied requirements; they do not grant authority to execute a workflow. The task ledger is the canonical implementation sequence.

## Claim vocabulary crosswalk

Source IDs are local to each draft. Equal C-numbers do not imply equal meanings. Canonical IDs preserve stable semantics across outputs.

| Canonical claim | SPEC-A claim | SPEC-B contribution | SPEC-C claim |
|---|---|---|---|
| CLM-GRAPH-01 | C01 | N01 | C01, graph roles in section 5 |
| CLM-RUNTIME-01 | C02 | N02 | C01/C06 acceptance mechanism |
| CLM-AGENT-01 | C03 | N03 | C02 |
| CLM-KNOW-01 | C04 | N01/N09 | C03 |
| CLM-REPLACE-01 | C05 | N04 | C06 |
| CLM-SEARCH-01 | C06 | N07 | C04 |
| CLM-REUSE-01 | C07 | N06/N09 | C05 |
| CLM-PLGA-01 | C08 | N05 | C07 |
| CLM-PLGA-02 / 03 | C09 | N05 / section 5 | C07 / section 8 |
| CLM-VERIFY-01 | C10 | sections 8 / 14 | sections 9 / 10 |
| CLM-BUDGET-01 | C11 | N03 | C02 / section 6.3 |
| CLM-UI-01 | C12 includes bounded proof | N08 | C08 |
| CLM-ROADMAP-01 | sections 13 / 14 | section 15 | sections 15 / 18 |
| METRIC-{learner}-{arm} | complete stage-2 table | exact JSON selectors | twelve-cell table plus ten contrasts |

Example IDs C-PLGA-001, C-SYS-004 and SCI-PLGA-COHORT are authoring examples, mapped to the semantic IDs above. They are not separate approved claims. All 26 current records remain internal candidates pending release-owner review.

## Proposed filename and ownership crosswalk

| Source alternative | One canonical later output | Current status |
|---|---|---|
| docs/diligence/README.md; dated README.md; START_HERE.md | v2/docs/Diligence/2026-10-18/00_START_HERE.md | Planned investor entry |
| INVESTOR_TECHNICAL_BRIEF.md; executive_brief.md | 01_TECHNICAL_INVESTMENT_BRIEF.md | Planned two-page investor brief |
| SYSTEMS_TECHNICAL_NOTE.md; architecture_note.md | 02_SYSTEMS_WHITEPAPER.md | Planned systems note |
| PLGA_RESEARCH_NOTE.md | 03_PLGA_RESEARCH_GUIDE.md | Planned reading wrapper; original paper unchanged |
| REVIEWER_GUIDE.md; reviewer_verification.md; evidence_index.md | 04_EVIDENCE_INDEX.md plus COMMANDS.md / exported VERIFY.md | Later investor index; current tooling commands implemented |
| walkthrough.md; optional recording | 05_WALKTHROUGH.md | Planned storyboard; video optional after core |
| next validation / milestones / FAQ outline | 06_NEXT_VALIDATION.md; optional FAQ | Planned scientific/value protocols |
| build_packet.py; build_package.py; verify_diligence.py | v2/dev/diligence/cli.py for current internal scope | Implemented; investor release mode remains DD-063 |
| tests inside new module versus dev/tests/diligence | v2/dev/tests/diligence | Existing dev owner; no overlapping registration |

The current WORKPLAN.md and its review PDF describe these deliverables; they do not substitute for the future investor prose.

## Section-level requirement mapping

Each heading is mapped to canonical tasks or an explicit source/estimate interpretation. The complete read ranges remain in the register.

### SPEC-A

Source: Amphora_Investor_Technical_Diligence_Master_Engineering_Spec_2026-10-18.md; 1097 lines; SHA-256 `847fab0c586fadec0b994dc954fec27dd82f3bae727d5fcac3796129f53f2bfc`.

| Source lines | Requirement heading | Canonical disposition |
|---|---|---|
| 10-23 | 1. The decision | F / DD-001..010; D / DD-035..047 |
| 24-36 | 1.1 Exact communication objective | F / DD-001..010; D / DD-035..047 |
| 37-48 | 1.2 Completion contract | F / DD-001..010; D / DD-035..047 |
| 49-50 | 2. Review basis and checks already performed | F / DD-001..007; Q / DD-071..074 |
| 51-58 | 2.1 Material inspected | F / DD-001..007; Q / DD-071..074 |
| 59-73 | 2.2 Verification executed during this review | F / DD-001..007; Q / DD-071..074 |
| 74-87 | 2.3 A concrete portability improvement established in this review | F / DD-001..007; Q / DD-071..074 |
| 88-89 | 3. Investor narrative and document hierarchy | D / DD-035..047 |
| 90-105 | 3.1 Recommended opening | D / DD-035..047 |
| 106-115 | 3.2 Three levels of reading | D / DD-035..047 |
| 116-128 | 3.3 Keep four evidence classes explicit | D / DD-035..047 |
| 129-147 | 4. Ranked technical highlights | C / DD-025..034 |
| 148-295 | 5. Claim inventory: wording, proof, and scope | C / DD-025..034 |
| 296-297 | 6. Explain the architecture clearly | D / DD-038..042; B / DD-051..053 |
| 298-317 | 6.1 The useful conceptual figure | D / DD-038..042; B / DD-051..053 |
| 318-332 | 6.2 Service responsibility table | D / DD-038..042; B / DD-051..053 |
| 333-344 | 6.3 Four technical mechanisms worth explaining | D / DD-038..042; B / DD-051..053 |
| 345-346 | 7. Machine learning and modeling: the strongest correct presentation | F / DD-006; C / DD-030; D / DD-043 |
| 347-356 | 7.1 Separate the three uses of computation | F / DD-006; C / DD-030; D / DD-043 |
| 357-370 | 7.2 What is interesting about the PLGA method | F / DD-006; C / DD-030; D / DD-043 |
| 371-389 | 7.3 Scientific facts available for use | F / DD-006; C / DD-030; D / DD-043 |
| 390-410 | 7.4 Result presentation | F / DD-006; C / DD-030; D / DD-043 |
| 411-418 | 7.5 What to say about generality | F / DD-006; C / DD-030; D / DD-043 |
| 419-523 | 8. External deliverables: exact content requirements | D / DD-035..047; P / DD-059..070 |
| 524-525 | 9. The walkthrough: one clear story, exact provenance | DD-045; optional DD-082 |
| 526-539 | 9.1 Recommended sequence | DD-045; optional DD-082 |
| 540-549 | 9.2 Capture rules | DD-045; optional DD-082 |
| 550-555 | 9.3 Optional second proof clip | DD-045; optional DD-082 |
| 556-559 | 10. Claims and evidence compilation | T / DD-011..024; P / DD-061..070 |
| 560-588 | 10.1 Suggested files | T / DD-011..024; P / DD-061..070 |
| 589-622 | 10.2 Claim record | T / DD-011..024; P / DD-061..070 |
| 623-641 | 10.3 Evidence record | T / DD-011..024; P / DD-061..070 |
| 642-666 | 10.4 Builder behavior | T / DD-011..024; P / DD-061..070 |
| 667-674 | 10.5 Package manifest and integrity | T / DD-011..024; P / DD-061..070 |
| 675-690 | 10.6 Fail-closed behavior | T / DD-011..024; P / DD-061..070 |
| 691-692 | 11. Portable historical evidence export | DD-007, DD-012, DD-013, DD-020 |
| 693-717 | 11.1 Minimum algorithm | DD-007, DD-012, DD-013, DD-020 |
| 718-727 | 11.2 Why this is worth doing today | DD-007, DD-012, DD-013, DD-020 |
| 728-746 | 11.3 Required tests for this addition | DD-007, DD-012, DD-013, DD-020 |
| 747-788 | 12. Visual specification | B / DD-048..058 |
| 789-808 | 13. Same-day additions: ranked by value and feasibility | N / DD-082..093 |
| 809-823 | 13.1 Optional software proof: a compact recovery vignette | N / DD-082..093 |
| 824-831 | 13.2 Optional scientific replay | N / DD-082..093 |
| 832-846 | 13.3 Optional protocol: the next scientific study | N / DD-082..093 |
| 847-867 | 14. File-by-file repository work | DD-003, DD-004, DD-079 |
| 868-876 | 14.1 Respect the existing operating boundaries | DD-003, DD-004, DD-079 |
| 877-880 | 15. Delivery schedule for today | WORKPLAN section 7; estimates remain unmeasured |
| 881-895 | 15.1 One-owner critical path | WORKPLAN section 7; estimates remain unmeasured |
| 896-907 | 15.2 Three-hour minimum | WORKPLAN section 7; estimates remain unmeasured |
| 908-913 | 15.3 Cut rules | WORKPLAN section 7; estimates remain unmeasured |
| 914-963 | 16. Engineering tickets and exit gates | All canonical task cards; no duplicate TD tracker |
| 964-965 | 17. Release verification and editorial acceptance | Q / DD-071..081 |
| 966-975 | 17.1 Scientific and numerical gates | Q / DD-071..081 |
| 976-984 | 17.2 Systems evidence gates | Q / DD-071..081 |
| 985-993 | 17.3 Document quality gates | Q / DD-071..081 |
| 994-1004 | 17.4 Bundle and source-attribution gates | Q / DD-071..081 |
| 1005-1010 | 17.5 Ten-minute reader test | Q / DD-071..081 |
| 1011-1030 | 18. Credited foundations and differentiation | DD-032, DD-042, DD-093 |
| 1031-1034 | 19. Canonical source map for implementation | source_lock.json and claims.json |
| 1035-1053 | 19.1 Entry points and scientific evidence | source_lock.json and claims.json |
| 1054-1080 | 19.2 Platform implementation and proof | source_lock.json and claims.json |
| 1081-1092 | 19.3 Instructions and plan context | source_lock.json and claims.json |
| 1093-1097 | 20. Final handoff instruction to the implementing engineer | Current local delivery and HANDOFF |

### SPEC-B

Source: Amphora_Investor_Diligence_Master_Engineering_Spec_2026-10-18.md; 1035 lines; SHA-256 `3e82eab88097ea926c9ee8780edd220d85229bc7da7965eaf1019204ffcc092a`.

| Source lines | Requirement heading | Canonical disposition |
|---|---|---|
| 11-28 | 1. The decision | WORKPLAN sections 1..3 |
| 29-34 | 1.1 External editorial policy | WORKPLAN sections 1..3 |
| 35-47 | 2. Review performed and evidence basis | F / DD-001..007; Q / DD-071..074 |
| 48-68 | 2.1 Checks executed for this review | F / DD-001..007; Q / DD-071..074 |
| 69-80 | 2.2 Evidence vocabulary to use throughout the package | F / DD-001..007; Q / DD-071..074 |
| 81-82 | 3. The investor narrative and reading order | D / DD-035..047 |
| 83-101 | 3.1 Positioning | D / DD-035..047 |
| 102-111 | 3.2 Three reader routes | D / DD-035..047 |
| 112-117 | 3.3 Copy-ready opening paragraph | D / DD-035..047 |
| 118-130 | 3.4 Proof cards | D / DD-035..047 |
| 131-136 | 4. Novelty and differentiation priorities | C / DD-025..029; D / DD-038..042 |
| 137-150 | 4.1 Ranked contribution map | C / DD-025..029; D / DD-038..042 |
| 151-169 | 4.2 N01: graph-native research, explained precisely | C / DD-025..029; D / DD-038..042 |
| 170-186 | 4.3 N02: an accepted result has a concrete protocol | C / DD-025..029; D / DD-038..042 |
| 187-206 | 4.4 N03: controlled agent workflows | C / DD-025..029; D / DD-038..042 |
| 207-223 | 4.5 N04: replaceability is a proof case, not an adjective | C / DD-025..029; D / DD-038..042 |
| 224-233 | 4.6 N06: context-aware reuse | C / DD-025..029; D / DD-038..042 |
| 234-239 | 4.7 Search and modeling distinction | C / DD-025..029; D / DD-038..042 |
| 240-253 | 4.8 Technical defensibility: what can accumulate value | C / DD-025..029; D / DD-038..042 |
| 254-257 | 5. Scientific case study: exact content contract | DD-006, DD-014, DD-030, DD-043, DD-055 |
| 258-263 | 5.1 Approved study definition | DD-006, DD-014, DD-030, DD-043, DD-055 |
| 264-283 | 5.2 Numerical facts available for the note | DD-006, DD-014, DD-030, DD-043, DD-055 |
| 284-293 | 5.3 Metric definition | DD-006, DD-014, DD-030, DD-043, DD-055 |
| 294-312 | 5.4 Complete stage-2 matrix | DD-006, DD-014, DD-030, DD-043, DD-055 |
| 313-328 | 5.5 Modeling details that deserve space | DD-006, DD-014, DD-030, DD-043, DD-055 |
| 329-334 | 5.6 Why this paper belongs in diligence | DD-006, DD-014, DD-030, DD-043, DD-055 |
| 335-338 | 6. Related work and defensible contribution language | DD-032, DD-042, DD-093 |
| 339-352 | 6.1 Minimum reference set | DD-032, DD-042, DD-093 |
| 353-365 | 6.2 Claim wording rules | DD-032, DD-042, DD-093 |
| 366-369 | 7. Same-day deliverable set | D / DD-035..047; DECISIONS content-root map |
| 370-418 | 7.1 Proposed repository layout | D / DD-035..047; DECISIONS content-root map |
| 419-430 | 7.2 Deliverable specifications | D / DD-035..047; DECISIONS content-root map |
| 431-447 | 7.3 Systems technical note outline | D / DD-035..047; DECISIONS content-root map |
| 448-451 | 8. Claim compiler and evidence ledger | T / DD-011..024; C / DD-025..034 |
| 452-464 | 8.1 Inputs and responsibilities | T / DD-011..024; C / DD-025..034 |
| 465-514 | 8.2 Claim record | T / DD-011..024; C / DD-025..034 |
| 515-533 | 8.3 Exact PLGA selectors to support | T / DD-011..024; C / DD-025..034 |
| 534-547 | 8.4 Platform-case summaries | T / DD-011..024; C / DD-025..034 |
| 548-557 | 8.5 Determinism and failure behavior | T / DD-011..024; C / DD-025..034 |
| 558-569 | 8.6 Proposed CLI contract | T / DD-011..024; C / DD-025..034 |
| 570-592 | 8.7 Test ownership | T / DD-011..024; C / DD-025..034 |
| 593-596 | 9. Figure specifications | B / DD-051..056 |
| 597-618 | 9.1 Figure A: three graph roles and accepted execution | B / DD-051..056 |
| 619-629 | 9.2 Figure B: acceptance and recovery | B / DD-051..056 |
| 630-643 | 9.3 Figure C: complete PLGA matrix | B / DD-051..056 |
| 644-649 | 9.4 Figure D: reconstructed evaluator proof | B / DD-051..056 |
| 650-653 | 9.5 Figure data sidecars | B / DD-051..056 |
| 654-667 | 10. Presentation, layout, and wording | B / DD-048..058; Q / DD-075 |
| 668-675 | 10.1 Screenshots | B / DD-048..058; Q / DD-075 |
| 676-679 | 11. Work packages and same-day execution schedule | All tasks; WORKPLAN section 7 |
| 680-693 | 11.1 Six-hour full package | All tasks; WORKPLAN section 7 |
| 694-705 | 11.2 Two-hour fallback | All tasks; WORKPLAN section 7 |
| 706-776 | 11.3 Work-package details | All tasks; WORKPLAN section 7 |
| 777-778 | 12. High-value additions that fit today | N / DD-082..093 |
| 779-791 | 12.1 Ranked additions | N / DD-082..093 |
| 792-804 | 12.2 Optional current-source software witness | N / DD-082..093 |
| 805-817 | 12.3 Optional walkthrough script | N / DD-082..093 |
| 818-831 | 12.4 A sensible additional white-paper title | N / DD-082..093 |
| 832-849 | 13. Reviewer guide and FAQ content | DD-044, DD-046, DD-083 |
| 850-851 | 14. Reproduction and verification procedures | DD-016..019; DD-074, DD-085 |
| 852-871 | 14.1 Existing no-training verification | DD-016..019; DD-074, DD-085 |
| 872-885 | 14.2 Full reproduction | DD-016..019; DD-074, DD-085 |
| 886-891 | 14.3 Paper handling | DD-016..019; DD-074, DD-085 |
| 892-908 | 15. Next evidence milestones | DD-046; N / DD-087..092 |
| 909-910 | 16. Repository and data handling | DD-003, DD-031, DD-059, DD-072 |
| 911-919 | 16.1 Code and operational boundaries | DD-003, DD-031, DD-059, DD-072 |
| 920-929 | 16.2 Source attribution and package allowlist | DD-003, DD-031, DD-059, DD-072 |
| 930-933 | 17. Release acceptance gate | Q / DD-071..081; P / DD-068..070 |
| 934-944 | 17.1 Claims and scientific consistency | Q / DD-071..081; P / DD-068..070 |
| 945-955 | 17.2 Evidence and reproducibility | Q / DD-071..081; P / DD-068..070 |
| 956-965 | 17.3 Rendering and usability | Q / DD-071..081; P / DD-068..070 |
| 966-974 | 17.4 Packaging | Q / DD-071..081; P / DD-068..070 |
| 975-978 | 17.5 Go/no-go rule | Q / DD-071..081; P / DD-068..070 |
| 979-1018 | 18. Traceability map for the implementing agent | source_lock.json; REPOSITORY_RECONCILIATION |
| 1019-1024 | 18.1 Status reconciliation rule | source_lock.json; REPOSITORY_RECONCILIATION |
| 1025-1030 | 19. Agent handoff instruction | Current bounded scope; HANDOFF |
| 1031-1035 | 20. Final delivery criteria | WORKPLAN sections 1 and 14 |

### SPEC-C

Source: Amphora_Investor_Technical_Diligence_Master_Spec_2026-10-18.md; 999 lines; SHA-256 `bc145f22eb834920b2878be996d47628d778d7f20e699c175c560496578f3592`.

| Source lines | Requirement heading | Canonical disposition |
|---|---|---|
| 8-19 | 1. The decision | WORKPLAN sections 1..3; D / DD-035..044 |
| 20-32 | 1.1 Required release today | WORKPLAN sections 1..3; D / DD-035..044 |
| 33-50 | 1.2 The investor-facing thesis | WORKPLAN sections 1..3; D / DD-035..044 |
| 51-56 | 2. What this review established | DD-001..007, DD-071..074 |
| 57-70 | 2.1 Checks actually performed in this review | DD-001..007, DD-071..074 |
| 71-82 | 2.2 Evidence authority | DD-001..007, DD-071..074 |
| 83-99 | 3. Novelty and differentiation map | C / DD-025..034; semantic claim crosswalk |
| 100-115 | 4. Claim discipline without defensive writing | DD-014, DD-033, DD-061..062 |
| 116-129 | 4.1 Examples of approved, useful copy | DD-014, DD-033, DD-061..062 |
| 130-131 | 5. Architecture dossier: executable research and one acceptance owner | DD-025, DD-028, DD-038..039 |
| 132-150 | 5.1 C01: executable, versioned pathways | DD-025, DD-028, DD-038..039 |
| 151-162 | 5.2 The two graphs and derived lineage | DD-025, DD-028, DD-038..039 |
| 163-174 | 5.3 C06: modularity shown through replacement | DD-025, DD-028, DD-038..039 |
| 175-176 | 6. Agent workflow dossier: model proposals remain attributable | DD-026, DD-040 |
| 177-190 | 6.1 C02: from proposal to accepted effect | DD-026, DD-040 |
| 191-200 | 6.2 Selected supervision is an especially useful technical example | DD-026, DD-040 |
| 201-206 | 6.3 Budget accounting is part of the architecture | DD-026, DD-040 |
| 207-212 | 6.4 Demonstrated workflow to feature | DD-026, DD-040 |
| 213-214 | 7. Evidence, modeling, and search dossiers | DD-027, DD-029, DD-041 |
| 215-222 | 7.1 C03: scientific memory with reproducible meaning | DD-027, DD-029, DD-041 |
| 223-236 | 7.2 C05: evidence reuse depends on context and producer proof | DD-027, DD-029, DD-041 |
| 237-247 | 7.3 C04: search is an explicit process | DD-027, DD-029, DD-041 |
| 248-257 | 7.4 A complete, useful engineering benchmark already exists | DD-027, DD-029, DD-041 |
| 258-263 | 7.5 Representation provenance is more informative today than a new importance plot | DD-027, DD-029, DD-041 |
| 264-265 | 8. Scientific dossier: make the PLGA contribution clear | DD-006, DD-030, DD-043, DD-054..055 |
| 266-297 | 8.1 What to feature | DD-006, DD-030, DD-043, DD-054..055 |
| 298-329 | 8.2 Complete stage-2 comparison | DD-006, DD-030, DD-043, DD-054..055 |
| 330-337 | 8.3 The unusually inspectable feature boundary | DD-006, DD-030, DD-043, DD-054..055 |
| 338-343 | 8.4 Compute and reproducibility | DD-006, DD-030, DD-043, DD-054..055 |
| 344-349 | 8.5 Preserve the paper's role | DD-006, DD-030, DD-043, DD-054..055 |
| 350-351 | 9. Highest-value same-day code addition: portable verification | T / DD-011..024; P / DD-063..069 |
| 352-392 | 9.1 Outcome | T / DD-011..024; P / DD-063..069 |
| 393-452 | 9.2 A concrete portability item already characterized | T / DD-011..024; P / DD-063..069 |
| 453-465 | 9.3 Keep verification meanings distinct | T / DD-011..024; P / DD-063..069 |
| 466-483 | 9.4 Proposed implementation modules | T / DD-011..024; P / DD-063..069 |
| 484-498 | 9.5 CLI behavior and failure semantics | T / DD-011..024; P / DD-063..069 |
| 499-519 | 9.6 Meaningful tests for the addition | T / DD-011..024; P / DD-063..069 |
| 520-521 | 10. Claim ledger and evidence index | claims.json; DD-014 and C / DD-025..034 |
| 522-562 | 10.1 A machine-readable source of technical assertions | claims.json; DD-014 and C / DD-025..034 |
| 563-568 | 10.2 Internal versus external material | claims.json; DD-014 and C / DD-025..034 |
| 569-574 | 10.3 Counts and summary generation | claims.json; DD-014 and C / DD-025..034 |
| 575-592 | 11. Exact deliverables and repository work | D / DD-035..047; DD-079 |
| 593-600 | 11.1 Navigation changes | D / DD-035..047; DD-079 |
| 601-606 | 11.2 Scope control | D / DD-035..047; DD-079 |
| 607-625 | 12. The new architecture paper: page-by-page specification | DD-038..042, DD-057 |
| 626-637 | 12.1 The abstract should describe the implemented contribution | DD-038..042, DD-057 |
| 638-657 | 12.2 Useful compact architecture figure | DD-038..042, DD-057 |
| 658-659 | 13. Executive brief and visual design | B / DD-048..058 |
| 660-669 | 13.1 Page one | B / DD-048..058 |
| 670-673 | 13.2 Page two | B / DD-048..058 |
| 674-688 | 13.3 Figure set | B / DD-048..058 |
| 689-696 | 13.4 Typography and export | B / DD-048..058 |
| 697-698 | 14. Five-minute walkthrough and reviewer routes | DD-035, DD-045, DD-082 |
| 699-714 | 14.1 Walkthrough script | DD-035, DD-045, DD-082 |
| 715-722 | 14.2 Reading routes | DD-035, DD-045, DD-082 |
| 723-740 | 15. Additional wins ranked for today's time budget | N / DD-082..093 |
| 741-746 | 15.1 Work to reserve for subsequent milestones | N / DD-082..093 |
| 747-750 | 16. Same-day execution schedule | WORKPLAN section 7; estimates not promises |
| 751-765 | 16.1 Recommended six-hour core release | WORKPLAN section 7; estimates not promises |
| 766-771 | 16.2 If fewer than three hours remain | WORKPLAN section 7; estimates not promises |
| 772-775 | 16.3 Scope cut order | WORKPLAN section 7; estimates not promises |
| 776-777 | 17. Release engineering and acceptance | P / DD-059..070; Q / DD-071..081 |
| 778-789 | 17.1 Package construction | P / DD-059..070; Q / DD-071..081 |
| 790-797 | 17.2 Export boundaries | P / DD-059..070; Q / DD-071..081 |
| 798-815 | 17.3 Required acceptance matrix | P / DD-059..070; Q / DD-071..081 |
| 816-847 | 17.4 Existing commands to retain | P / DD-059..070; Q / DD-071..081 |
| 848-869 | 18. Investor questions the package should answer | DD-044, DD-046, DD-083, DD-088 |
| 870-882 | 18.1 Metrics for the next value study | DD-044, DD-046, DD-083, DD-088 |
| 883-884 | 19. Implementation handoff | Current local scope; HANDOFF |
| 885-900 | 19.1 First implementation task | Current local scope; HANDOFF |
| 901-906 | 19.2 Definition of done today | Current local scope; HANDOFF |
| 907-999 | 20. Immutable source register | source_lock.json and source roles |

## Reconciled acceptance choices

The default verifier adopts SPEC-C's Python 3.12 standard-library/exit-code contract; source and capsule checks remain distinct. SPEC-A/C's fixed per-file reconstruction map is stronger than a generic newline retry and is retained. All drafts require complete scientific context; no fallback may select only favorable results. SPEC-B's explicit primary-reference set and SPEC-A's provenance/workflow reference leads become DD-032/DD-042 review inputs; this plan does not claim to have refreshed new external literature.

Same-day schedules differ. The plan uses elapsed allocations and a bounded minimum, with unmeasured effort ranges and explicit cuts. Optional scientific replay, new actual-owner witness, recording and future deployment/model integration are follow-on tasks, not authority for execution.
