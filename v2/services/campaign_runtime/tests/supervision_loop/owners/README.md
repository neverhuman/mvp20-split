# Actual owner integration

`export_demo.py` is the owner-local, no-SQL/no-key fixture compiler used by the local
deployment checkpoint probe. It exports reviewed schema bytes, compiles the bounded
scalar materialization graph and validates its policy/recipe using this installed
Runtime only. It does not start owners, seed stores, call providers or establish
scientific validity. Public orchestration and retained evidence belong to dev helpers.

Select this folder explicitly with both AMPHORA_TEST_POSTGRES=1 and AMPHORA_TEST_OWNER_PROCESSES=1. The owner_processes marker and separate opt-in keep these slower combined scenarios out of routine module SQL runs. They use actual Data, Runtime and Planning HTTP services plus configured worker, graph coordinator and retention delivery processes. The current environment is editable; independent installed acceptance remains V1.

Scenarios: accepted abstention and invalid output followed by bounded repair/fallback; each finishes the scalar materialization graph, preserves original call reservations/deadline, verifies exact public execution reports and immutable replay, and confirms the output Artifact retention through Data's authenticated Runtime callback. Unconfigured notification destinations are outside this proof. Fixture outputs are synthetic and do not establish scientific validity.

Preserve basetemp output directories: Data's retained fixture history refers to their byte stores. Never reuse or delete a previous explicit basetemp on rerun. Owner processes close in ExitStack/finally. Credentials exist only in the subprocess environment; JSON configs carry environment-variable names. Helpers do not import Planning/Data internals or query their business tables; migration is an explicit current Planning owner subprocess, never an older binary or reset.

`test_branches.py` adds delayed scalar selection, deadline fallback with late diagnostic publication, and a different future campaign revision/value. Each runs actual Data/Runtime/Planning processes, demonstrates independent materialization while the supervised node waits, and verifies immutable request/report/winner and output bytes. Planning owns its test-only `supervision_execution/owner_probe.py`; Runtime invokes that subprocess without importing Planning private code or querying its SQL. Barriers are test instrumentation, not production human approval gates.

For isolated replacement, set `AMPHORA_TEST_SUPERVISOR_INSTALLATIONS` to the verified supervisor installation directory and `AMPHORA_TEST_DATA_INSTALLATION` to the isolated Data installation directory. `Installations` checks manifest versions and schema preservation before selecting an executable. Every owner host and worker CLI uses its own wheel environment. At the provider barrier the test replaces all three HTTP hosts on the same ports/configuration/history; Runtime and Planning switch to independently installed replacement environments, while Data restarts its isolated environment. The already-issued provider process may return afterward; replacement workers consume the original history. Evidence records executable paths, process IDs, endpoints and manifest hashes. Without those explicit variables, the existing editable-owner tier remains selected.
