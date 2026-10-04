"""Independent radius, history, continuation and exact-context read oracles."""

import pytest
from amphora_contracts_knowledge import (
    AssertionRetraction,
    GraphAssertionSelection,
    GraphEntitySearchRequest,
    GraphEntitySelection,
    GraphNeighborhoodRequest,
    GraphObjectRequest,
    GraphViewPosition,
)
from amphora_knowledge.authoring.canonical import KnowledgeError
from amphora_knowledge.exploration.projection import GraphExploration, bounded

from .conftest import changed


def search(snapshot, **values):
    return GraphEntitySearchRequest(
        wire_version="1", revision=snapshot.reference, **values
    )


def neighborhood(snapshot, **values):
    return GraphNeighborhoodRequest(
        wire_version="1",
        revision=snapshot.reference,
        focus=snapshot.content.entities[0].reference,
        **values,
    )


def test_literal_search_stable_pages_and_complete_query_fingerprint(chain):
    view = GraphExploration(chain)
    request = search(chain, limit=1)
    first = view.search(request)
    assert first.total == 3 and [r.label for r in first.entities] == ["A"]
    second = view.search(request.model_copy(update={"position": first.next_position}))
    third = view.search(request.model_copy(update={"position": second.next_position}))
    assert [r.label for r in second.entities + third.entities] == ["B", "C"]
    assert third.next_position is None
    assert first.query_sha256 == second.query_sha256 == third.query_sha256
    assert view.search(search(chain, text="A")).total == 1
    assert view.search(search(chain, text="a")).total == 0
    assert view.search(search(chain, text=".*")).total == 0
    assert view.search(search(chain, entity_type="absent")).entities == ()
    for update in (
        {"text": "B"},
        {"limit": 2},
        {"history": "retained"},
        {"entity_type": "absent"},
    ):
        with pytest.raises(KnowledgeError, match="position_query"):
            view.search(
                request.model_copy(update={"position": first.next_position, **update})
            )


@pytest.mark.parametrize(
    "radius,entities,assertions",
    [
        (0, ["A"], []),
        (1, ["A", "B"], ["claim"]),
        (2, ["A", "B", "C"], ["claim", "second"]),
    ],
)
def test_exact_induced_radius_keeps_assertion_direction(
    chain, radius, entities, assertions
):
    result = GraphExploration(chain).neighborhood(neighborhood(chain, radius=radius))
    assert [r.reference.entity_id for r in result.entities] == entities
    assert [r.reference.assertion_id for r in result.assertions] == assertions
    assert result.next_position is None and result.unresolved_entities == ()
    reverse = neighborhood(chain, radius=1).model_copy(
        update={"focus": chain.content.entities[-1].reference}
    )
    edge = GraphExploration(chain).neighborhood(reverse).assertions[0]
    assert edge.subject.entity_id == "B" and edge.object.entity_id == "C"


def test_independent_page_lanes_expose_missing_endpoints_without_invented_nodes(chain):
    view = GraphExploration(chain)
    request = neighborhood(chain, radius=2, entity_limit=1, assertion_limit=1)
    pages = []
    while True:
        page = view.neighborhood(request)
        pages.append(page)
        if page.next_position is None:
            break
        request = request.model_copy(update={"position": page.next_position})
    assert len(pages) == 3
    assert [r.label for page in pages for r in page.entities] == ["A", "B", "C"]
    assert [r.reference.assertion_id for page in pages for r in page.assertions] == [
        "claim",
        "second",
    ]
    assert [r.entity_id for r in pages[0].unresolved_entities] == ["B"]
    assert [r.entity_id for r in pages[1].unresolved_entities] == ["C"]
    assert pages[2].assertions == () and pages[2].unresolved_entities == ()
    assert all((p.entity_total, p.assertion_total) == (3, 2) for p in pages)


def test_entity_context_revision_does_not_rewrite_old_assertion_endpoint(snapshot):
    left, right = snapshot.content.entities
    successor = left.model_copy(
        update={
            "reference": left.reference.model_copy(update={"revision": 2}),
            "supersedes": left.reference,
        }
    )
    revision = changed(snapshot, entities=(left, successor, right))
    view = GraphExploration(revision)
    assert [
        r.reference.revision for r in view.search(search(revision, text="A")).entities
    ] == [2]
    assert [
        r.reference.revision
        for r in view.search(search(revision, text="A", history="retained")).entities
    ] == [1, 2]
    old = view.neighborhood(neighborhood(revision))
    assert old.assertions[0].subject == left.reference
    assert old.entities[0].reference == left.reference and not old.entities[0].is_latest
    new = view.neighborhood(
        neighborhood(revision).model_copy(update={"focus": successor.reference})
    )
    assert new.assertions == () and new.entity_total == 1
    assert (
        GraphExploration(snapshot)
        .search(search(snapshot, text="A"))
        .entities[0]
        .reference
        == left.reference
    )


def test_corrected_and_retracted_assertions_remain_explicit_in_history(snapshot):
    old = snapshot.content.assertions[0]
    new = old.model_copy(
        update={
            "reference": old.reference.model_copy(update={"revision": 2}),
            "supersedes": old.reference,
            "polarity": "negated",
            "posture": "unresolved",
        }
    )
    revision = changed(
        snapshot,
        assertions=(old, new),
        retractions=(
            AssertionRetraction(assertion=new.reference, change_id="retract"),
        ),
    )
    view = GraphExploration(revision)
    assert view.neighborhood(neighborhood(revision)).assertions == ()
    retained = view.neighborhood(neighborhood(revision, history="retained"))
    assert [
        (a.reference.revision, a.is_latest, a.retracted) for a in retained.assertions
    ] == [(1, False, False), (2, True, True)]
    request = GraphObjectRequest(
        wire_version="1",
        revision=revision.reference,
        selection=GraphAssertionSelection(kind="assertion", reference=new.reference),
    )
    detail = view.detail(request)
    assert detail.detail.record == new and detail.detail.retracted
    assert detail.detail.record.grounding == old.grounding


def test_detail_catalog_and_invalid_revision_or_position(snapshot):
    view = GraphExploration(snapshot)
    catalog = view.catalog()
    assert (
        catalog.revision == snapshot.reference
        and catalog.limits.response_bytes == 1048576
    )
    assert [v.view_id for v in catalog.views] == [
        "entity_search",
        "neighborhood",
        "object_detail",
    ]
    request = GraphObjectRequest(
        wire_version="1",
        revision=snapshot.reference,
        selection=GraphEntitySelection(
            kind="entity", reference=snapshot.content.entities[0].reference
        ),
    )
    assert view.detail(request).detail.record == snapshot.content.entities[0]
    wrong = snapshot.reference.model_copy(update={"sha256": "0" * 64})
    for operation, query in [(view.search, search(snapshot)), (view.detail, request)]:
        with pytest.raises(KnowledgeError, match="query_revision"):
            operation(query.model_copy(update={"revision": wrong}))
    first = view.search(search(snapshot, limit=1))
    for offset in (3,):
        position = first.next_position.model_copy(update={"entity_offset": offset})
        with pytest.raises(KnowledgeError, match="position_bound"):
            view.search(search(snapshot, limit=1, position=position))
    position = first.next_position.model_copy(update={"assertion_offset": 1})
    with pytest.raises(KnowledgeError, match="search_position"):
        view.search(search(snapshot, limit=1, position=position))
    with pytest.raises(KnowledgeError, match="position_query"):
        view.search(
            search(
                snapshot,
                position=GraphViewPosition(
                    query_sha256="0" * 64, entity_offset=0, assertion_offset=0
                ),
            )
        )
    with pytest.raises(KnowledgeError, match="search_request"):
        view.search(neighborhood(snapshot))
    with pytest.raises(KnowledgeError, match="neighborhood_request"):
        view.neighborhood(search(snapshot))
    with pytest.raises(KnowledgeError, match="object_request"):
        view.detail(search(snapshot))


def test_response_byte_ceiling_is_independent_of_dto_cardinality(snapshot):
    entity = snapshot.content.entities[0].model_copy(update={"label": "界" * 512})
    oversized = snapshot.model_copy(
        update={
            "content": snapshot.content.model_copy(
                update={"entities": (entity,) * 4096}
            )
        }
    )
    with pytest.raises(KnowledgeError, match="response_bound"):
        bounded(oversized)
