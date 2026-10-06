"""Read original measured results in an isolated process; no provider calls or writes."""

import json
import os
from pathlib import Path

from amphora_agent_planning.evaluation_execution import EvaluationRunner
from openai_evaluation_bundle import ROOT, load_bundle
from run_openai_evaluation import report
from sqlalchemy import create_engine


def verify(output):
    engine = create_engine(os.environ["EVALUATION_READ_SQL"], connect_args={"options": "-c statement_timeout=5000 -c default_transaction_read_only=on"})
    try:
        snapshots = {}
        for version in ("v1", "v2", "v3", "v4", "v5"):
            principal, protocol, batch, provider = load_bundle(None, ROOT.with_name("openai-engineering-" + version))
            runner = EvaluationRunner(engine, provider, adapter_revision=provider.revision, timeout_seconds=60)
            value = report(runner, principal, protocol, batch)
            value.pop("timestamp_local")
            snapshots[version] = value
        assert snapshots["v1"]["status"] == "pending"
        assert snapshots["v1"]["unknown_usage"] == 2
        assert all(not snapshots[v]["passed"] for v in ("v1", "v2", "v3", "v4"))
        assert snapshots["v5"]["passed"] and snapshots["v5"]["status"] == "complete"
        assert sum(s["reported_estimated_usd_nanodollars"] for s in snapshots.values()) == 298267500
        assert sum(s["reserved_usd_nanodollars"] for s in snapshots.values()) == 1658880000
        Path(output).write_text(json.dumps(snapshots, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    finally:
        engine.dispose()
