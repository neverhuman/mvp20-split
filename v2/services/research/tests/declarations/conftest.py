import json

import pytest
from amphora_contracts_research import EvidenceNeed, ResearchQuestion
from amphora_research.declarations.registration import ACTIONS, DeclarationRegistrar
from amphora_research.transport.access import Principal


@pytest.fixture
def registration(ledger):
    store, scope = ledger
    schema = {"schema_id": "synthetic", "version": "1", "sha256": "a" * 64}
    artifact = {"artifact_id": "unconsumed-context", "scope": scope.model_dump(), "sha256": "b" * 64,
        "media_type": "application/json", "schema_ref": schema, "size_bytes": 2}
    question = ResearchQuestion.model_validate_json(json.dumps({"wire_version": "1",
        "reference": {"scope": scope.model_dump(), "question_id": "q", "revision": 1},
        "objective": "Synthetic comparison", "applicability": artifact,
        "criteria": [{"criterion_id": "c", "description": "Context"}], "supersedes": None}))
    need = EvidenceNeed.model_validate_json(json.dumps({"wire_version": "1",
        "reference": {"scope": scope.model_dump(), "need_id": "n", "revision": 1},
        "question": question.reference.model_dump(mode="json"), "criterion_ids": ["c"],
        "method": schema, "required_context": artifact, "supersedes": None}))
    return DeclarationRegistrar(store), Principal("first-registrant", scope, ACTIONS), question, need
