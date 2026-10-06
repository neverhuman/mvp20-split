# Evaluation execution tests

Owner: Planning evaluation_execution. Actual retained PostgreSQL plus deterministic adapter; no live/scientific proof. Run python -m pytest -c dev/pyproject.toml services/agent_planning/tests/evaluation_execution with AMPHORA_TEST_POSTGRES=1 and current Planning>=0.91 migrator. Never reset histories or use older migrations.

Cases cover all repetitions without hidden retry, complete/pending/semantic pass distinctions, original settlement floors, competing steps during a blocked provider, replacement replay, overage before unissued work, owner rejection projection, grants and fixture/live distinction. Recovery/process tests retain failed/unknown attempts rather than replacing them with favorable reruns.
