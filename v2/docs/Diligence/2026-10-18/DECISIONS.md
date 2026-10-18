# Amphora | Build decisions

| Decision | Selected contract | Reason and consequence |
|---|---|---|
| Content owner | `v2/docs/Diligence/2026-10-18/` | Active v2 docs; one canonical tree. SPEC-B's alternative filenames map here. |
| Plan authority | `task_ledger.json`; generated task/progress projections | One status source. Existing engine trackers retain their own authority and percentages. |
| Current delivery | Detailed plan + tested local tooling + review PDF | Does not activate the whole investor release or attachment-described execution. |
| Source pin | `9c3018dcdd17f40be27fc3c6dc7057d2d7cb05bc` | Exact Git blobs are distinct from current documentation overlays and old execution releases. |
| Core runtime | Python 3.12 standard library | No renderer/scientific-training dependencies in baseline capsule. |
| Arithmetic | Explicit optional NumPy 1.26.4 | Requested missing dependency fails distinctly; no auto-install or downgraded success. |
| PDF | Current workplan: ReportLab + embedded local fonts; future note: shared LaTeX template | Separate content validation from renderer. Record actual toolchain, not presumed byte determinism. |
| Rust | No new Rust component | No v2 Cargo manifest inspected; hashing/registries need no second build system. Future measured kernels may justify it. |
| Brand | Declarative navy/teal/amber tokens | Shared type/layout/color rules. Immutable historical receipts are not rebranded. |
| Historical transport | 12 fixed source/transform/historical pin entries | 11 LF-to-CRLF, browser identity. No fallback, JSON rewrite or repin. |
| Existing checker reuse | Exact four-file acceptance checker closure | Preserve semantic gates, limitations and profile. No hash-only substitute. |
| Internal capsule | Implemented witness, explicitly not investor-qualified | Exact historical records can contain original host/path/legacy context. Do not infer external disclosure approval. |
| Investor payload | Later separately approved allowlist and release gate | Redaction creates new derivatives and cannot retain original-pin assertions. |
| Source/capsule tiers | Source reruns dependency guard; capsule reports it as not rerun | Omitted source cannot be rescanned by an evidence-only export. |
| Tests | `v2/dev/tests/diligence/`, existing dev owner | No overlapping test owner; scoped coverage and behavior mapping live in module README. |
| External literature | Future primary-source check for added detail | Attachments' reference assertions are inputs; no new competitor/patent investigation is claimed. |
| Distribution | Local branch and private review files | No new public push, messages, invites or sharing changes. |

The exact receipt inclusion choice remains DD-060. Either the original selected records clear disclosure unchanged, or a smaller profile uses clearly labeled derivative summaries and states which original assertions are unavailable. The current builder cannot be used to bypass that choice: its manifest and output explicitly remain `internal_engineering` with `release_qualified=false`.

## Version 2 superseding scope

The user now authorizes public push of the revised critical review as a branch and draft PR, with no merge. V2 findings and five investment tracks supersede V1 preparation percentages and the local-only publication scope. Original science, data terms and historical pins remain unchanged; raw attachments remain excluded. The current source/policy/verifier must be acquired from the reviewed revision, with investor/scientific/commercial/rights decisions still unmet.
