import pytest
from amphora_knowledge.authoring.canonical import KnowledgeError
from amphora_knowledge.authoring.policy import StructuralPolicy
from amphora_knowledge.authoring.vocabulary import Vocabulary


def test_vocabulary_order_is_not_identity_but_content_changes_are(graph_fixture):
    original = graph_fixture.vocabulary
    reversed_order = Vocabulary(original.record.model_copy(update={"predicates": tuple(reversed(original.record.predicates))}))
    assert original.reference == reversed_order.reference
    predicate = original.record.predicates[0].model_copy(update={"description": "Different declared meaning"})
    changed = Vocabulary(original.record.model_copy(update={"predicates": (predicate, *original.record.predicates[1:])}))
    assert original.reference.sha256 != changed.reference.sha256


@pytest.mark.parametrize("which", ["types", "predicates", "endpoint", "duplicate-endpoint"])
def test_ambiguous_vocabulary_is_rejected(graph_fixture, which):
    record = graph_fixture.vocabulary.record
    if which == "types":
        record = record.model_copy(update={"entity_types": ("concept", "concept")})
    elif which == "predicates":
        record = record.model_copy(update={"predicates": (record.predicates[0], record.predicates[0])})
    else:
        allowed = ("unknown",) if which == "endpoint" else ("concept", "concept")
        predicate = record.predicates[0].model_copy(update={"subject_types": allowed})
        record = record.model_copy(update={"predicates": (predicate,)})
    with pytest.raises(KnowledgeError):
        Vocabulary(record)


def test_endpoint_rules_are_enforced_independently_of_predicate_spelling(graph_fixture):
    vocabulary = graph_fixture.vocabulary
    with pytest.raises(KnowledgeError, match="unknown_entity_type"):
        vocabulary.require_type("mystery")
    with pytest.raises(KnowledgeError, match="predicate_endpoint_mismatch"):
        vocabulary.require_relation("causes", "concept", "mystery")


@pytest.mark.parametrize("value", [True, 0, 4097, 1.5])
def test_invalid_policy_limits_fail_before_application(value):
    with pytest.raises(KnowledgeError, match="invalid_structural_policy"):
        StructuralPolicy(max_entities=value)
