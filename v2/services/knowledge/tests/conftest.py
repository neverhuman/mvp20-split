import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from amphora_contracts_knowledge import DomainVocabulary, GraphChangeProposal
from amphora_knowledge.authoring.policy import StructuralPolicy
from amphora_knowledge.authoring.state import GraphState
from amphora_knowledge.authoring.vocabulary import Vocabulary


@pytest.fixture
def graph_fixture():
    case = json.loads((Path(__file__).parent / "fixtures/initial.json").read_text(encoding="utf-8"))
    vocabulary = Vocabulary(DomainVocabulary.model_validate_json(json.dumps(case["vocabulary"])))
    policy = StructuralPolicy()
    raw = case["proposal"]
    raw["vocabulary"] = vocabulary.reference.model_dump(mode="json")
    raw["policy"] = policy.reference.model_dump(mode="json")
    proposal = GraphChangeProposal.model_validate_json(json.dumps(raw))
    state = GraphState(proposal.graph, vocabulary, policy)
    return SimpleNamespace(state=state, proposal=proposal, vocabulary=vocabulary, policy=policy)
