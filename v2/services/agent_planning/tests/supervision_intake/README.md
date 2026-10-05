# Supervisor intake tests

Owns original public wrapper/Planning request binding and atomic SQL request/command/receipt recording. Run `python -m pytest -c v2/dev/pyproject.toml v2/services/agent_planning/tests/supervision_intake`. SQL cases require AMPHORA_TEST_POSTGRES=1 and the retained labeled fixture; run serially. Planning0.70 applies forward planning0015; never run older migrators afterward.

Public contract fixtures provide literal byte compatibility; no private Runtime imports. Tests cover rollback, exact replay, read-only recovery, conflicting wrappers/commands, scoped grants, existing PlanningJournal compatibility, competing connections and no provider attempt. HTTP and independently installed exchange remain B1.04 successor units.
