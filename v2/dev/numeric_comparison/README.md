# Numeric comparison harness

Owner: BP-08.04/B2.01; development evidence only. Protocol v1 is declared in
[protocol.json](protocol.json) before the first benchmark execution. Production
tools retain their own scheduling and numerical boundaries.

This harness compares the existing numeric search tool against a deterministic
midpoint grid on fixed one- and two-dimensional synthetic sphere objectives.
Five seeds, 16 evaluator attempts per arm, population four, fixed operators and
generation ceiling are declared in the protocol. Grid order is lexicographic;
the one-dimensional grid has 16 points and the two-dimensional grid is 4 by 4.
The same installed evaluator CLI, exact policy bytes and evaluator binding serve
both arms. No private tool imports, model calls, network, SQL or production graph
execution are involved. Declared image/Artifact identities are offline fixture
labels, not authenticated Data/Registry evidence.

Every evaluator call is charged before dispatch, including timeout, rejection or
malformed response. No retry occurs. Search retains its native stopping rules;
unused allowance is visible, never padded with invented observations. Baseline
evaluations continue through individual failures. All seeds and both arms are
retained. A pair earns a numeric difference only when both arms actually consume
the full budget without failed observations or search transport errors. Otherwise
it remains incomplete, including any successful intermediate fitness. Missing
fitness is null. Positive difference means lower observed search cost; negative
and tied differences remain visible. Prefix metrics are undefined if no successful
observation exists at any prefix. Descriptive results do not establish statistical
or scientific superiority.

The runner calls the public tool CLIs for seed/requests/collect/vary and evaluator
compute. It saves exact request/result/checkpoint bytes and an append-only attempt
journal to a new output directory. Interrupted runs retain their journal and lack
a completed report; reruns require a new directory. The protocol is copied and
hashed before any tool execution. Finished reports include every declared pair
and software versions. Source changes require requalification; this harness does
not supply Runtime admission, successor lineage, current eligibility, independent
installation or target-host proof. Those remain B2.02/V1.

Run from the repository root with the dev interpreter:
`v2/dev/.venv/Scripts/python.exe -m numeric_comparison --output <new-directory>`
and `PYTHONPATH=Z:/mvp20-split/v2/dev`. Tests are owned by
`dev/tests/numeric_comparison`; no paid calls or credentials are needed.
