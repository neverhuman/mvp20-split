"""Pure accepted-shape snapshots; no database/peer authorization claim."""

import pytest
from amphora_knowledge.authoring.canonical import digest


def changed(snapshot, **updates):
    content = snapshot.content.model_copy(
        update={"revision": snapshot.content.revision + 1, **updates}
    )
    reference = snapshot.reference.model_copy(
        update={"revision": content.revision, "sha256": digest(content)}
    )
    return snapshot.model_copy(update={"reference": reference, "content": content})


@pytest.fixture
def snapshot(graph_fixture):
    return graph_fixture.state.apply(graph_fixture.proposal, None).to_snapshot()


@pytest.fixture
def chain(snapshot):
    left, middle = snapshot.content.entities
    right = left.model_copy(
        update={
            "reference": left.reference.model_copy(update={"entity_id": "C"}),
            "label": "C",
        }
    )
    edge = snapshot.content.assertions[0]
    second = edge.model_copy(
        update={
            "reference": edge.reference.model_copy(update={"assertion_id": "second"}),
            "subject": middle.reference,
            "object": right.reference,
        }
    )
    return changed(snapshot, entities=(left, middle, right), assertions=(edge, second))
