"""Malformed histories fail closed; merges never silently rewrite evidence."""

import pytest
from amphora_contracts_knowledge import AssertionRetraction, EntityAlias
from amphora_knowledge.authoring.canonical import KnowledgeError
from amphora_knowledge.exploration.projection import GraphExploration

from .conftest import changed
from .test_projection import neighborhood, search


def test_alias_chain_is_metadata_not_a_new_assertion_or_traversal(chain):
    a, b, c = chain.content.entities
    aliases = (
        EntityAlias(source=a.reference, target=b.reference, change_id="merge-a"),
        EntityAlias(source=b.reference, target=c.reference, change_id="merge-b"),
    )
    snapshot = changed(chain, aliases=aliases)
    view = GraphExploration(snapshot)
    assert [r.label for r in view.search(search(snapshot)).entities] == ["C"]
    retained = view.search(search(snapshot, history="retained"))
    assert [r.alias_target for r in retained.entities] == [
        b.reference,
        c.reference,
        None,
    ]
    page = view.neighborhood(neighborhood(snapshot, radius=0))
    assert [r.label for r in page.entities] == ["A"]
    assert page.assertions == () and page.unresolved_entities == (b.reference,)
    page = view.neighborhood(neighborhood(snapshot, radius=1))
    assert [r.label for r in page.entities] == ["A", "B"]
    assert page.assertions[0].subject == a.reference
    assert page.unresolved_entities == (c.reference,)


@pytest.mark.parametrize(
    "mutation,code",
    [
        ("entity_duplicate", "entity_order"),
        ("entity_order", "entity_order"),
        ("entity_gap", "entity_history"),
        ("entity_rename", "entity_identity"),
        ("assertion_duplicate", "assertion_order"),
        ("assertion_gap", "assertion_history"),
        ("endpoint_missing", "entity_missing"),
        ("alias_missing", "alias_member"),
        ("alias_self", "alias_identity"),
        ("alias_duplicate", "alias_source"),
        ("alias_cycle", "alias_cycle"),
        ("retraction_missing", "retraction_member"),
        ("retraction_duplicate", "duplicate_retraction"),
    ],
)
def test_corrupt_snapshot_history_is_not_projected(snapshot, mutation, code):
    a, b = snapshot.content.entities
    edge = snapshot.content.assertions[0]
    alias = EntityAlias(source=a.reference, target=b.reference, change_id="merge")
    retired = AssertionRetraction(assertion=edge.reference, change_id="retire")
    updates = {
        "entity_duplicate": {"entities": (a, a, b)},
        "entity_order": {"entities": (b, a)},
        "entity_gap": {
            "entities": (
                a.model_copy(
                    update={"reference": a.reference.model_copy(update={"revision": 2})}
                ),
                b,
            )
        },
        "entity_rename": {
            "entities": (
                a,
                a.model_copy(
                    update={
                        "reference": a.reference.model_copy(update={"revision": 2}),
                        "supersedes": a.reference,
                        "label": "renamed",
                    }
                ),
                b,
            )
        },
        "assertion_duplicate": {"assertions": (edge, edge)},
        "assertion_gap": {
            "assertions": (
                edge.model_copy(
                    update={
                        "reference": edge.reference.model_copy(update={"revision": 2})
                    }
                ),
            )
        },
        "endpoint_missing": {"entities": (a,)},
        "alias_missing": {
            "aliases": (
                alias.model_copy(
                    update={
                        "target": b.reference.model_copy(update={"entity_id": "absent"})
                    }
                ),
            )
        },
        "alias_self": {"aliases": (alias.model_copy(update={"target": a.reference}),)},
        "alias_duplicate": {"aliases": (alias, alias)},
        "alias_cycle": {
            "aliases": (
                alias,
                EntityAlias(source=b.reference, target=a.reference, change_id="cycle"),
            )
        },
        "retraction_missing": {
            "retractions": (
                retired.model_copy(
                    update={
                        "assertion": edge.reference.model_copy(update={"revision": 2})
                    }
                ),
            )
        },
        "retraction_duplicate": {"retractions": (retired, retired)},
    }[mutation]
    with pytest.raises(KnowledgeError, match=code):
        GraphExploration(changed(snapshot, **updates))


def test_content_digest_and_reference_identity_are_verified(snapshot):
    with pytest.raises(KnowledgeError, match="snapshot_required"):
        GraphExploration(snapshot.content)
    for field, value in [("sha256", "0" * 64), ("revision", 2)]:
        bad = snapshot.model_copy(
            update={"reference": snapshot.reference.model_copy(update={field: value})}
        )
        with pytest.raises(KnowledgeError, match="snapshot_identity"):
            GraphExploration(bad)


def test_dense_graph_paging_covers_every_record_once(snapshot):
    seed = snapshot.content.entities[0]
    entities = tuple(
        seed.model_copy(
            update={
                "reference": seed.reference.model_copy(
                    update={"entity_id": f"node-{i:03}"}
                ),
                "label": f"node-{i:03}",
            }
        )
        for i in range(130)
    )
    edge = snapshot.content.assertions[0]
    assertions = tuple(
        edge.model_copy(
            update={
                "reference": edge.reference.model_copy(
                    update={"assertion_id": f"edge-{i:03}"}
                ),
                "subject": entities[0].reference,
                "object": entities[i + 1].reference,
            }
        )
        for i in range(129)
    )
    dense = changed(snapshot, entities=entities, assertions=assertions)
    view = GraphExploration(dense)
    request = neighborhood(dense, entity_limit=64, assertion_limit=128)
    seen_entities, seen_assertions, sizes = [], [], []
    while True:
        page = view.neighborhood(request)
        sizes.append((len(page.entities), len(page.assertions)))
        seen_entities.extend(r.reference for r in page.entities)
        seen_assertions.extend(r.reference for r in page.assertions)
        assert (page.entity_total, page.assertion_total) == (130, 129)
        if page.next_position is None:
            break
        request = request.model_copy(update={"position": page.next_position})
    assert sizes == [(64, 128), (64, 1), (2, 0)]
    assert seen_entities == [e.reference for e in entities]
    assert seen_assertions == [a.reference for a in assertions]
