# Numeric graph public-owner acceptance

Status: B2.02 passed 2026-10-06 11:51:04 (America/Chicago); B3 interruption/replacement next.

Run `dev/verify_numeric_graph.py --output <new-retained-directory>` with explicit owned PostgreSQL opt-in. It installs Runtime, Artifact, numeric tool, synthetic evaluator and SDK controller independently from each locked public closure. Controller has no Runtime/Artifact/tool implementation or SQL imports. Public host/HTTP helpers are reused; old acceptance fixtures are not changed.

The graph uses declared test image identities; this proves Windows wheel processes and real HTTP/persistence only. Linux image builds/Registry deployment remain V1. Each numerical operation is a separate standalone worker mode. Two evaluator worker processes run concurrently with explicit parameters and policy inputs. Runtime owns graph progression, Artifact owns publication and protection. Scope/tokens are fresh; workers receive only their token, never SQL credentials. Token values are neither configuration nor evidence.

Evidence checks accepted generation0/1/2, exact final RNG counter, policy provenance, final carried-value digest, completion count/budget settlement, original admission replay and confirmed retention reservations. Real bytes are re-read through the Artifact API. Numeric math/failure oracles remain the focused transaction and tool suites. Process interruption/replacement remains B3. Services close after a run; history and Artifact storage are preserved in the output directory.

Observed run a9599726324f445c964173fa08c7b1c4:15 accepted tool invocations,6 evaluations,54 confirmed reservations, generations0/1/2, finalcounter26. Exact admission replay and final carried-value hash passed. Retained local evidence `.test-results/numeric-http-20261006a/http/evidence.json`; compact committed evidence under docs/Audits/Evidence/BP-08-Search/Actual_HTTP.json.
