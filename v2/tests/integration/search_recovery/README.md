# Search recovery acceptance

Owner BP-08.05. This is test infrastructure, never a production scheduler or
checkpoint authority. Public-controller integration imports only public contracts,
uses actual owner HTTP, and passes credentials through environment variables.
Tool/domain unit oracles may import the search package's public exports.

manifest.py binds exact Artifact bytes/schema/scope/specification and checks
complete checkpoint-chain equivalence across independent runs. It excludes only
the run-specific previous Artifact identity from comparison after validating each
chain. It does not validate intrinsic numerical semantics or authorize a restore;
CheckpointSnapshot and Runtime retain those responsibilities. Changed evaluator,
seed/operator/implementation pins cannot resume an old checkpoint. The supported
format is checkpoint-v1; unsupported versions/corrupt data reject, never reseed.

The initial manifest tests cover exact bytes, hashes, shape, scope, canonical
encoding, specification revision, pending membership and random-stream recovery.
Actual partial-evaluation interruption, rebuilt adapter transport and correction
successors are the next bounded tasks. Exact replay is asserted on the same
declared profile; no arbitrary cross-hardware or scientific claim follows.

B1.01 verified 2026-10-06 19:12:48:84manifest/checkpoint/step-context/boundary checks14.12s; manifest59statements6branches100%. All evidence-helper branches covered; this is not intrinsic-kernel or process coverage. Source-level same-profile restore and changed-original rejection are separate assertions against public search domain objects.

B1.02 verified 2026-10-06 19:18:08: independent rebuilt_adapter.py uses only documented public search exports, contracts and SDK; no production adapter/private Runtime imports.28workspace checks11.78s and11isolated checks6.51s passed in a fresh numeric0.5 closure with noSQL/owner implementations. All four operations and independent first RNG draw/one-member rank oracles pass. Parent adapter52/77statements18/24branches; CLI subprocess coverage is not attributed, worker transport and oversized-output guard remain uncovered. This test companion is not the qualified production image; source SHA is retained and actual transport remains B1.03.

B1.03 actual HTTP verified 2026-10-06 19:27:13: baseline15attempts/15accepted and interrupted16attempts/15accepted; all six checkpoint states equivalent and108unique retention reservations confirmed across both runs. One evaluator result is accepted before worker2 is killed after actual Data finalization. Fresh Runtime restarts; retry uses next fence, identical orphan/result bytes and a stale completion rejects without changing prior accepted history. Both runs use the reconstructed test companion from the start with declared fixture image identity; no claim it matches the prior production image. Controller has public contracts only, noSQL/private owners. Driver dev/verify_partial_search_recovery.py reuses pinned isolated installations and runs only against explicitly opted-in owned PostgreSQL. Evidence Partial_Evaluation_Recovery.json. No new source-coverage percentage is inferred from these processes.

B2.01 verified 2026-10-06 19:30:18: correction.py records an explicit new search revision from the declared seed, with prior checkpoint/selection hash and next immutable specification/evaluator. It is synthetic test evidence, not a production grant. All unrelated spec fields remain fixed in this fixture policy; no fitness reuse or resume is allowed across changed evaluator pins.29correction/manifest checks4.27s, correction39/39statements and2/2branches. Actual successor admission remains B2.02.
