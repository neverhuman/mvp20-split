import copy
import hashlib
import json
from pathlib import Path

import pytest
from amphora_agent_planning.context import AttemptBinding, RequestSnapshot
from amphora_contracts_core import Scope
from amphora_contracts_planning import EngagementRequest

FIXTURE = Path(__file__).parent / "fixtures/request.json"
SCOPE = Scope(tenant_id="planning-fixture", project_id="context")


def bind(document=None, **kwargs):
    raw = FIXTURE.read_bytes() if document is None else json.dumps(document).encode()
    return RequestSnapshot.from_bytes(raw, actor_id=kwargs.get("actor_id", "fixture"),
                                      scope=kwargs.get("scope", SCOPE))


def test_canonical_order_revalidation_and_caller_mutation():
    source = json.loads(FIXTURE.read_bytes())
    snapshot = bind(source)
    assert bind(dict(reversed(list(source.items())))).canonical == snapshot.canonical
    assert snapshot.sha256 == hashlib.sha256(snapshot.canonical).hexdigest()
    source["context"]["entries"].clear()
    assert len(snapshot.document().context.entries) == 1
    dto = snapshot.document()
    assert RequestSnapshot.bind(dto, actor_id="fixture", scope=SCOPE) == snapshot
    forged = dto.model_copy(update={"actor_id": 42})
    with pytest.raises(ValueError, match="invalid_request"):
        RequestSnapshot.bind(forged, actor_id="fixture", scope=SCOPE)


@pytest.mark.parametrize("path,value,code", [
    (("reference", "scope", "project_id"), "foreign", "scope_mismatch"),
    (("context", "scope", "project_id"), "foreign", "scope_mismatch"),
    (("context", "objective", "scope", "project_id"), "foreign", "artifact_scope_mismatch"),
    (("actor_id",), "other", "actor_mismatch"),
    (("purpose",), "supervision", "missing_runtime_cut"),
    (("context", "limits", "total_tokens"), 2047, "insufficient_attempt_budget"),
    (("context", "model", "context_window_tokens"), 2047, "context_window_exceeded"),
    (("context", "allowed_actions"), ["abstain", "abstain"], "duplicate_action"),
])
def test_relationship_guards(path, value, code):
    document = json.loads(FIXTURE.read_bytes())
    item = document
    for key in path[:-1]:
        item = item[key]
    item[path[-1]] = value
    with pytest.raises(ValueError, match=code):
        bind(document)


def test_supervision_cut_scope_and_immutable_fingerprint():
    document = json.loads(FIXTURE.read_bytes())
    document["purpose"] = "supervision"
    document["runtime_cut"] = {"scope": SCOPE.model_dump(), "run_id": "run", "plan_sha256": "a" * 64,
                               "revision": 4, "frontier_revision": 3}
    original = bind(document)
    document["runtime_cut"]["frontier_revision"] = 4
    assert bind(document).sha256 != original.sha256
    document["runtime_cut"]["scope"]["project_id"] = "foreign"
    with pytest.raises(ValueError, match="runtime_scope_mismatch"):
        bind(document)


@pytest.mark.parametrize("variant,code", [
    ("entry", "duplicate_context_entry"), ("omission", "duplicate_omission"),
    ("mandatory", "included_omission"), ("source", "included_omission"),
    ("conflict", "artifact_identity_conflict"),
])
def test_context_cannot_hide_duplicate_identity_or_mandatory_omission(variant, code):
    document = json.loads(FIXTURE.read_bytes())
    context = document["context"]
    if variant == "entry":
        context["entries"].append(copy.deepcopy(context["entries"][0]))
    elif variant == "omission":
        context["omissions"].append(copy.deepcopy(context["omissions"][0]))
    else:
        context["omissions"][0]["artifact"] = copy.deepcopy(
            context["objective"] if variant == "mandatory" else context["entries"][0]["artifact"])
        if variant == "conflict":
            context["omissions"][0]["artifact"]["sha256"] = "f" * 64
    with pytest.raises(ValueError, match=code):
        bind(document)


@pytest.mark.parametrize("raw,code", [
    (b"", "request_size"), (b"x" * 262145, "request_size"), (b"\xff", "invalid_request"),
    (b"{", "invalid_request"), (b"[]", "invalid_request"),
    (b'{"x":1,"x":2}', "duplicate_json_key"), (b'{"x":NaN}', "nonfinite_json"),
    (b"[" * 1100, "invalid_request"),
], ids=["empty", "oversized", "utf8", "syntax", "array", "duplicate", "nonfinite", "deep"])
def test_bounded_strict_json(raw, code):
    with pytest.raises(ValueError, match=code):
        RequestSnapshot.from_bytes(raw, actor_id="fixture", scope=SCOPE)


def test_attempt_identity_binds_exact_request_and_number():
    snapshot = bind()
    first, second = AttemptBinding(snapshot, 1), AttemptBinding(snapshot, 2)
    first.validate(first.reference())
    assert first.reference().engagement == second.reference().engagement
    assert first.reference().request_sha256 == second.reference().request_sha256
    with pytest.raises(ValueError, match="attempt_binding_mismatch"):
        first.validate(second.reference())
    modified = snapshot.document().model_copy(update={"decision_scope": "f" * 64})
    changed = RequestSnapshot.bind(modified, actor_id="fixture", scope=SCOPE)
    with pytest.raises(ValueError, match="attempt_binding_mismatch"):
        first.validate(AttemptBinding(changed, 1).reference())


@pytest.mark.parametrize("ordinal", [0, 3, True, 1.0])
def test_attempt_bound(ordinal):
    with pytest.raises(ValueError, match="attempt_limit"):
        AttemptBinding(bind(), ordinal)


def test_valid_json_does_not_grant_owner_authority():
    dto = EngagementRequest.model_validate_json(FIXTURE.read_bytes())
    foreign = Scope(tenant_id=SCOPE.tenant_id, project_id="another")
    with pytest.raises(ValueError, match="scope_mismatch"):
        RequestSnapshot.bind(dto, actor_id="fixture", scope=foreign)
