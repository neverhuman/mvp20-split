# Reconstructed synthetic numeric evaluator

Owner: BP-09.04. Release0.4.0; B2/B3 live replacement and rejection gates passed.
Independent rebuild/audit evidence is tracked in the owning plan. Design: [Search](../../docs/Architecture/Campaigns/Search.md).

Source verification2026-10-07:38tests pass9.92s;134/135statements,25/26branches,
99% aggregate. Kernel/adapter/metadata100%; module-entry line/branch is exercised
by subprocess CLI tests but not attributed to this coverage run. Fresh installed
and Linux image qualification remains independently recorded in the plan evidence.

This separate package reconstructs the original evaluator from its README, public
schemas/metadata and acceptance fixtures. The private original kernel and adapter
are not inputs. Public metadata and original tests are reused explicitly; arithmetic,
applicability checks, adapter and CLI are independently implemented. The old package,
release0.3 and image remain intact. Same capability ID, new immutable release/image;
this is an engineering replacement, not a scientific improvement.

`domain.py` owns PolicyBinding and SyntheticProblem. Two required Artifact inputs,
parameters and policy, produce one EvaluationObservation result. The fixed
synthetic-quadratic-v1 policy requires 1..32 finite dimensionless genes in
[-1000000,1000000], proposed candidates, candidate-derived ev- identities, unique
cost/distance objectives in requested order, exact evaluator release/image and
actual policy Artifact identity/schema/hash/size/bytes. Undeclared context rejects.
cost=sum(x*x), distance=sum((x-1)*(x-1)); no hard constraints, violation0,
quality synthetic. Provenance preserves request scope, canonical request hash and
the actual policy reference. Requests and observations use public search DTOs.

`metadata.py` owns public schema/policy bytes and image-bound descriptor.
`adapter.py` binds one image per process and rejects rebinding. Named safe input
rejection is invalid_synthetic_objective_input. The aggregate input/output bound
is262144bytes. `__main__.py` exposes describe --image-sha256, schema --kind,
policy, compute --image-sha256 --policy-file, and worker --config. Offline compute
emits canonical bytes without newline; malformed input returns2 with no stdout
and closed invalid_synthetic_input_or_configuration stderr. Offline computation
does not prove an Artifact exists or is authorized.

The public multi-input SDK owns authenticated transport, claims/fences, leases,
provisional publication and completion. Runtime alone accepts execution; Data owns
bytes. No database, search selection, graph control, provider calls, scientific
promotion, molecular model, synthesis or lab behavior is implemented here. Pure
kernel has no I/O; configured worker performs one invocation with explicit local
credentials. No ambient credential discovery or hidden retry loop.

Tests are scoped to tests/kernel, tests/cli and tests/worker. Original acceptance
fixtures plus independent boundary cases must pass. Replacement requires a fresh
wheel closure without the old evaluator/search implementation, nonroot offline
Linux image probes and actual restored Runtime/Data/Registry execution. Cutover
occurs between campaigns; old observations/receipts/hashes stay unchanged. A new
release cannot relabel old fitness. Failure and stale-worker proof remains BP-09.04
B3; independent installation/integration and drift audit remain V1.

Reviewed2026-10-07 10:22:26: actual restored cutover completed15invocations/6evaluations/3checkpoints
with immutable original/corrected/blocked histories and browser readbacks. Wrong0.3/image
claims receive no eligible work; actual expired fence1 is superseded by Linux fence2,
and late completion rejects stale_attempt while the run remains active. Same policy
bytes under another Artifact identity produce terminal invalid_synthetic_objective_input.
Evidence: [reconstruction](../../docs/Audits/Evidence/BP-09-Deployment/Evaluator_Reconstruction.json).
Two earlier process faults remain retained and unresolved; successful cutover does not
prove operational soak or eliminate intermittent transport/worker failures.
