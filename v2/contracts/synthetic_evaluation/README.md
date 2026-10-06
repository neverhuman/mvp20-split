# Synthetic evaluation receipt transport

- Owner: BP-08.03/B2.03b.ii; version0.1.0; verified 2026-10-06 14:45:50; 54 scoped checks. Tool kernel/adapter/capability/profile coverage100%; CLI tested in subprocess, not counted in parent coverage.

SyntheticEvaluationReceipt carries engineering-only authority, scope, exact input-byte and declared canonical digests, full evaluation method pins and one bounded integer synthetic-digest-score. Core and Evaluation Identity public DTOs are its dependencies. It supplies neither authenticated origin, permission to reuse, measured fitness nor canonical equivalence. Runtime accepted-producer evidence and current Data reads must bind the output to the declared input/tool; Research owns all reuse decisions. Wire tests own strict shape/range checks; tool tests own calculation. Replacement must preserve published schema bytes or version the boundary.
