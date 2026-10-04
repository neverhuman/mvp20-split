"""Installed owner process probe; URL secrets arrive only through environment."""

import hashlib
import json
import os
import sys
from pathlib import Path

from amphora_agent_planning.access import Principal
from amphora_agent_planning.context import AttemptBinding, RequestSnapshot
from amphora_agent_planning.persistence.journal import PlanningJournal
from amphora_agent_planning.providers import FixtureProvider, observe
from amphora_contracts_core import Scope
from amphora_contracts_planning import reference_proposal_schema
from sqlalchemy import create_engine


def main():
    stage, project = sys.argv[1:]
    raw = json.loads((Path(__file__).parents[1] / "context/fixtures/request.json").read_bytes())
    scope = Scope(tenant_id="planning-installed", project_id=project)
    def rescope(value):
        if isinstance(value, dict):
            if set(value) == {"tenant_id", "project_id"}:
                value.update(scope.model_dump())
            for child in value.values():
                rescope(child)
        elif isinstance(value, list):
            for child in value:
                rescope(child)
    rescope(raw)
    raw["context"]["output_schema"] = reference_proposal_schema().model_dump(mode="json")
    request = RequestSnapshot.from_bytes(json.dumps(raw).encode(), actor_id="fixture", scope=scope)
    principal = Principal("fixture", scope, frozenset({"record_requests", "record_attempts", "read_attempts"}))
    first, second = AttemptBinding(request, 1), AttemptBinding(request, 2)
    engine = create_engine(os.environ["AMPHORA_TEST_PLANNING_SERVICE_URL"],
                           connect_args={"options": "-c statement_timeout=5000"})
    journal = PlanningJournal(engine)
    try:
        if stage == "prepare":
            journal.register(principal, request)
            assert journal.begin_attempt(principal, first).observation is None
        else:
            assert journal.read_request(principal, request.document().reference) == request
            if stage == "interrupted":
                assert journal.read_attempt(principal, first.reference()).observation is None
                journal.record(principal, first, observe(first, FixtureProvider("interrupted")))
                journal.begin_attempt(principal, second)
            elif stage == "finish":
                assert journal.read_attempt(principal, second.reference()).observation is None
                result = observe(second, FixtureProvider("proposal"))
                assert journal.record(principal, second, result) == journal.record(principal, second, result)
            elif stage != "replay":
                raise ValueError("unknown_probe_stage")
        attempts = []
        for binding in (first, second):
            stored = journal.read_attempt(principal, binding.reference())
            if stored is None:
                attempts.append(None)
            elif stored.observation is None:
                attempts.append({"ordinal": binding.ordinal, "status": "pending"})
            else:
                wire = stored.observation.document()
                attempts.append({"ordinal": binding.ordinal, "status": wire.status,
                    "record_sha256": hashlib.sha256(stored.observation.canonical).hexdigest(),
                    "capture_sha256": stored.observation.capture.sha256, "usage": wire.usage.model_dump(mode="json")})
        print(json.dumps({"pid": os.getpid(), "request_sha256": request.sha256, "attempts": attempts}))
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
