# Supervisor intake tests

Owns original public wrapper/Planning request binding and atomic SQL request/command/receipt recording. Run `python -m pytest -c v2/dev/pyproject.toml v2/services/agent_planning/tests/supervision_intake`. SQL cases require AMPHORA_TEST_POSTGRES=1 and the retained labeled fixture; run serially. Planning0.70 applies forward planning0015; never run older migrators afterward.

Public contract fixtures provide literal byte compatibility; no private Runtime imports. Tests cover rollback, exact replay, read-only recovery, conflicting wrappers/commands, scoped grants, existing PlanningJournal compatibility, competing connections and no provider attempt. HTTP and independently installed exchange remain B1.04 successor units.


Verified 2026-10-05 20:04:57: B2.01b.iv current Runtime0.33/Planning0.75 actual materialization-target exchange passed11 process stages,6 hosts,2 lost replies and original/replacement recovery. Four isolated installs668 cases;40/30 old migration files unchanged. No provider call, SQL reset or execution-winner claim. All owned processes closed. Evidence: docs/Audits/Evidence/BP-07-Supervisor/Checkpoint_Owners.json (relative to v2).
