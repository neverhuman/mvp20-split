"""Declared timeout fallback produces typed missingness rather than fabricated success."""

import copy
import time

from sqlalchemy import text

from .test_execution import advance, observation, start


def test_abstained_wait_can_feed_an_explicit_partial_collection(graph_env):
    def fallback(raw):
        body = raw["body"]
        wait, finish = body["nodes"]
        shape = {"kind": "collection", "item": copy.deepcopy(wait["output"]["value_type"]),
                 "max_items": 1, "missing_slots": True}
        body["outputs"] = [{"name": "results", "value_type": shape}]
        join = {"kind": "join", "node_id": "fallback", "members": [{"member_id": "evidence",
            "source": {"kind": "output", "node_id": wait["node_id"], "port": wait["output"]["name"]}}],
            "policy": {"kind": "partial", "minimum": 0, "close": "all_terminal"},
            "output": {"name": "results", "value_type": shape}}
        finish["outputs"] = [{"port": "results", "source": {"kind": "output", "node_id": "fallback", "port": "results"}}]
        body["nodes"] = [wait, join, finish]
        body["edges"] = [{"source": wait["node_id"], "target": "fallback", "route": "next"},
                         {"source": "fallback", "target": "finish", "route": "next"}]
    f = start(graph_env, timeout=1, on_timeout="abstained", modify=fallback)
    until = time.monotonic() + 5
    while time.monotonic() < until:
        page = advance(f)
        if page.status != "running":
            break
        time.sleep(0.025)
    assert page.status == "completed" and (page.reserved, page.spent) == (0, 0)
    assert observation(f).closure.outcome.status == "abstained"
    with graph_env.env.engine.connect() as conn:
        output = conn.execute(text("SELECT outputs FROM runtime.graph_runs WHERE run_id=:run"), {"run": f.run}).scalar_one()
        assert output[0]["value"]["items"] == [{"kind": "missing", "member_id": "evidence", "reason_code": "wait_deadline_expired"}]
