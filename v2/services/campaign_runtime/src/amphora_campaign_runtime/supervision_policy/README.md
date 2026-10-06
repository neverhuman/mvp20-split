# Reviewed supervision policy

Runtime-private pure eligibility boundary for BP-07.04 B2.01c.i. Design: [admitted checkpoint policy](../../../../../docs/Build%20Plans/BP-07/BP-07.04%20Admitted%20checkpoint%20policy.md).

`ReviewedPolicy.bind(plan, record)` validates an exact compiled plan digest and scope, authored target kinds, inline scalar field types and units, bounded limits and unambiguous observation selectors. `from_bytes` requires normalized canonical bytes. The immutable object retains a validated plan and policy bytes; `sha256` identifies those bytes. `rule_for` and `read_paths` resolve authored selectors against concrete activation paths, including ancestor reads in nested execution.

`ScalarRule` owns exact decimal range and finite choice checks. Integer policies require portable integral bounds; number policies accept integer values with matching units. No float arithmetic or implicit unit conversion is used. Existing values need not fall within adjustment bounds: this boundary validates proposed adjustments, not scientific quality or unchanged fallback values.

Records are private DTOs, not public transport. PolicyPins owns append-only SQL pins through the caller transaction. It validates the registered exact supervised admission command, original plan and absence of an existing frontier before insertion. Loading reconstructs canonical bytes and verifies their recorded identity. runtime0022 grants the service SELECT/INSERT only. No network, credentials, provider selection, active-run policy update or execution acceptance occurs here. GraphAdmission integrates the pin atomically before creating the frontier. GraphPass reloads it to guard selected targets before work issuance. Checkpoint creation and ceiling consumption are subsequent gates. Canonical bytes do not confer authority to run a model or accept its result.

Replacement acceptance: module-owned tests must preserve exact range edges, type/unit rejection, plan identity, canonical reconstruction, duplicate rejection and occurrence selection. Run `dev/run_tests.py --module runtime --area supervision_policy` using the development environment; tests live in `tests/supervision_policy`. Public predecessor contracts remain unchanged.

`PolicyCatalog` selects only an exact scope/plan/policy identity, owns reconstructed immutable entries and rejects duplicate policies. Missing selections fail closed; configuration changes do not supply an implicit latest-policy fallback.

Runtime0.47 adds explicit private runtime-supervision-policy.v2 with context_recipe_sha256. Original PolicyRecord v1 remains closed; read_policy dispatches only the two named profiles. New admissions resolve RecipeCatalog before run creation and atomically pin canonical recipe bytes with policy before frontier creation. PolicyPins.load requires matching retained recipe for v2. Existing public admission command bytes and v1 admission behavior remain unchanged.
