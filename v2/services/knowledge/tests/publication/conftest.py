from dataclasses import replace

import pytest
from amphora_contracts_knowledge import ReasoningPublicationRequest
from amphora_knowledge.publication.identity import PublisherIdentity
from amphora_knowledge.publication.store import PublicationStore

from ..reasoning.conftest import reasoning_case  # noqa: F401
from .test_journal import journal_case  # noqa: F401
from .test_payload import case as payload_case  # noqa: F401


@pytest.fixture
def publication_case(reasoning_case):  # noqa: F811
    c = reasoning_case
    c.workflow.submit(c.principal, c.request)
    c.publication = ReasoningPublicationRequest(wire_version="1", graph=c.request.snapshot.graph,
        publication_id="publish", reasoning_request_id=c.request.request_id)
    c.publisher = PublisherIdentity("data-publisher", "knowledge-synthetic")
    c.principal = replace(c.principal, actions=frozenset({"publish_reasoning"}))
    c.publications = PublicationStore(c.case.engine)
    return c
