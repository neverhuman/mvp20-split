import copy
import hashlib
import json
from pathlib import Path

import pytest
from amphora_agent_planning.context import AttemptBinding, RequestSnapshot
from amphora_agent_planning.persistence.records import verified_observation
from amphora_agent_planning.providers import FixtureProvider, observe
from amphora_agent_planning.providers.capture import Observation
from amphora_agent_planning.providers.port import ProviderReply
from amphora_agent_planning.providers.profiles import OutputProfiles
from amphora_agent_planning.providers.wire import observation_document
from amphora_contracts_core import Scope
from amphora_contracts_planning import ProviderUsage


def documents():
    value = json.loads((Path(__file__).parents[1] / "extraction/fixtures/extraction.json").read_bytes())
    request = RequestSnapshot.from_bytes(json.dumps(value["request"]).encode(), actor_id="fixture",
        scope=Scope.model_validate(value["request"]["reference"]["scope"]))
    return AttemptBinding(request, 1), value["draft"]


class Response:
    def __init__(self, raw):
        self.raw = raw
        self.calls = 0

    def supports(self, model):
        return True

    def reply(self, binding):
        self.calls += 1
        return ProviderReply([self.raw], ProviderUsage(input_tokens=10, output_tokens=10,
                                                      accounting_units=1, certainty="reported"))


def test_typed_candidate_derives_exact_envelope_and_preserves_capture():
    binding, draft = documents()
    raw = json.dumps(draft).encode()
    observed = observe(binding, Response(raw))
    wire = observed.document()
    assert wire.schema_version == "2" and wire.status == "proposed"
    assert wire.proposal.output_schema == binding.request.document().context.output_schema
    assert json.loads(wire.proposal.payload_json) == draft
    assert wire.proposal.payload_sha256 == hashlib.sha256(wire.proposal.payload_json.encode()).hexdigest()
    assert wire.output_sha256 == hashlib.sha256(raw).hexdigest()
    assert wire.proposal.action == draft["action"] and wire.proposal.rationale == draft["rationale"]
    assert verified_observation(binding, observed) == observed


@pytest.mark.parametrize("field,value", [("payload_sha256", "f" * 64), ("rationale", "forged"),
                                        ("action", "abstain"), ("payload_json", "{}")])
def test_typed_envelope_cannot_reinterpret_retained_raw_response(field, value):
    binding, draft = documents()
    observed = observe(binding, Response(json.dumps(draft).encode()))
    wire = observed.document().model_dump(mode="json")
    wire["proposal"][field] = value
    with pytest.raises(ValueError, match="proposal_capture_mismatch"):
        verified_observation(binding, Observation(observed.capture, json.dumps(wire).encode()))


def test_encoded_overhead_can_exceed_legacy_bound_without_larger_raw_capture():
    binding, draft = documents()
    draft["diagnostics"] = [{"code": "fixture", "target_path": "/entities/0", "kind": "unsupported",
                              "description": '"' * 4000} for _ in range(7)]
    raw = json.dumps(draft).encode()
    assert len(raw) <= 65536
    observed = observe(binding, Response(raw))
    assert 65536 < len(observed.canonical) < 262144
    assert observed.document().captured_bytes == len(raw)
    assert verified_observation(binding, observed) == observed


@pytest.mark.parametrize("case,status,reason", [
    ("malformed", "invalid", "invalid_output"), ("oversized", "invalid", "output_size"),
    ("duplicate", "invalid", "duplicate_json_key"), ("abstain-data", "invalid", "abstention_payload"),
    ("foreign", "policy_rejected", "proposal_scope_mismatch"),
    ("unselected", "policy_rejected", "unselected_payload"),
])
def test_task_profile_rejections_remain_distinct(case, status, reason):
    binding, draft = documents()
    if case == "abstain-data":
        draft["action"] = "abstain"
    elif case == "foreign":
        draft["entities"][0]["attribution"]["quotations"][0]["span"]["source"]["scope"]["project_id"] = "foreign"
    elif case == "unselected":
        draft["entities"][0]["attribution"]["quotations"][0]["span"]["source"]["raw"]["sha256"] = "f" * 64
    raw = {"malformed": b"{", "oversized": b"x" * 65537,
           "duplicate": b'{"action":"abstain","action":"request_evidence"}'}.get(case, json.dumps(draft).encode())
    wire = observe(binding, Response(raw)).document()
    assert wire.schema_version == "2" and wire.status == status and wire.reason_code == reason
    assert wire.proposal is None


def test_task_abstention_and_unknown_profile_do_not_grant_calls_or_proposals():
    binding, draft = documents()
    draft.update(action="abstain", entities=[])
    wire = observe(binding, Response(json.dumps(draft).encode())).document()
    assert wire.schema_version == "2" and wire.status == "abstained"
    raw = binding.request.document().model_dump(mode="json")
    raw["context"]["output_schema"]["sha256"] = "f" * 64
    changed = AttemptBinding(RequestSnapshot.from_bytes(json.dumps(raw).encode(), actor_id="fixture",
                                                       scope=binding.reference().engagement.scope), 1)
    response = Response(json.dumps(draft).encode())
    assert observe(changed, response).document().status == "policy_rejected" and response.calls == 0
    with pytest.raises(ValueError, match="unsupported_output_profile"):
        OutputProfiles.parse(response.raw, changed)


@pytest.mark.parametrize("raw,reason", [(b"[]", "invalid_observation"), (b"\xff", "invalid_observation"),
    (b'{"schema_version":"3"}', "observation_version"), (b'{"schema_version":2}', "observation_version"),
    (b'{"schema_version":"1"}' + b" " * 65536, "observation_size"),
    (b'{"schema_version":"2"}' + b" " * 262144, "observation_size")],
    ids=["array", "utf8", "unknown", "numeric-version", "legacy-size", "task-size"])
def test_wire_decoder_retains_version_specific_limits(raw, reason):
    with pytest.raises(ValueError, match=reason):
        observation_document(raw)


def test_every_research_group_and_entity_match_remains_scoped_and_selected():
    binding, draft = documents()
    attribution = draft["entities"][0]["attribution"]
    scope = binding.reference().engagement.scope.model_dump(mode="json")
    draft["entities"][0]["matches"] = [{"graph": {"scope": scope, "graph_id": "domain"},
                                        "entity_id": "known", "revision": 1}]
    question = {"scope": scope, "question_id": "known-q", "revision": 1}
    draft["questions"] = [{"local_id": "q", "objective": "Question?", "applicability": None,
        "criteria": [{"criterion_id": "criterion", "description": "Synthetic criterion"}], "attribution": attribution}]
    draft["answers"] = [{"local_id": "answer", "question_local_id": None, "question": question,
        "answer": "An opinion", "validation_method": None, "context": None, "attribution": attribution}]
    draft["evidence_needs"] = [{"local_id": "need", "question_local_id": "q", "question": None,
        "criterion_ids": ["criterion"], "method": None, "required_context": None, "attribution": attribution}]
    assert observe(binding, Response(json.dumps(draft).encode())).document().status == "proposed"
    bad = copy.deepcopy(draft)
    bad["answers"][0]["question"]["scope"]["project_id"] = "foreign"
    assert observe(binding, Response(json.dumps(bad).encode())).document().status == "policy_rejected"

    bad = copy.deepcopy(draft)
    bad["entities"][0]["matches"][0]["graph"]["scope"]["project_id"] = "foreign"
    assert observe(binding, Response(json.dumps(bad).encode())).document().status == "policy_rejected"


def test_legacy_canonical_bytes_match_the_predecessor_installation_exactly():
    fixture = json.loads((Path(__file__).parent / "fixtures/legacy-observation-v1.json").read_bytes())
    raw = fixture["request"]
    snapshot = RequestSnapshot.from_bytes(json.dumps(raw).encode(), actor_id="fixture",
                                         scope=Scope.model_validate(raw["reference"]["scope"]))
    binding = AttemptBinding(snapshot, 1)
    observed = observe(binding, FixtureProvider("proposal"))
    assert observed.canonical == fixture["observation_json"].encode()
    assert hashlib.sha256(observed.canonical).hexdigest() == fixture["observation_sha256"]
    assert observed.capture.content == fixture["capture_utf8"].encode()
    assert observed.document().schema_version == "1"
    assert verified_observation(binding, observed) == observed
