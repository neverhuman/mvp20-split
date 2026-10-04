import hashlib
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Event

import pytest
from amphora_agent_planning.context import AttemptBinding, RequestSnapshot
from amphora_agent_planning.providers import FixtureProvider, observe
from amphora_agent_planning.providers.capture import MAX_CHUNKS, MAX_OUTPUT_BYTES
from amphora_agent_planning.providers.port import ProviderReply
from amphora_contracts_core import Scope
from amphora_contracts_planning import ProviderUsage, reference_proposal_schema

SCOPE = Scope(tenant_id="planning-fixture", project_id="context")


def attempt(change=None):
    document = json.loads((Path(__file__).parent / "fixtures/request.json").read_bytes())
    document["context"]["output_schema"] = reference_proposal_schema().model_dump(mode="json")
    if change:
        change(document)
    request = RequestSnapshot.from_bytes(json.dumps(document).encode(), actor_id="fixture", scope=SCOPE)
    return AttemptBinding(request, 1)


@pytest.mark.parametrize("variant,status,complete", [
    ("abstain", "abstained", True), ("proposal", "proposed", True),
    ("invented_action", "invalid", True), ("oversized", "invalid", False),
    ("malformed", "invalid", True), ("unknown_usage", "abstained", True),
    ("unavailable", "unavailable", False), ("interrupted", "unknown", False),
])
def test_adversarial_provider_outcomes_remain_distinct(variant, status, complete):
    binding = attempt()
    observation = observe(binding, FixtureProvider(variant))
    wire = observation.document()
    assert wire.attempt == binding.reference()
    assert wire.status == status
    assert wire.output_complete is complete
    assert wire.output_sha256 == hashlib.sha256(observation.capture.content).hexdigest()
    assert wire.captured_bytes == len(observation.capture.content) <= MAX_OUTPUT_BYTES
    assert (wire.proposal is not None) == (status in {"proposed", "abstained"})
    if variant in {"unknown_usage", "unavailable", "interrupted"}:
        assert wire.usage.certainty == "unknown" and wire.usage.input_tokens is None
    if variant == "oversized":
        assert wire.captured_bytes == MAX_OUTPUT_BYTES
    if variant == "proposal":
        assert wire.proposal.payload == binding.request.document().context.entries[0].artifact


class ControlledProvider:
    def __init__(self, chunks, usage=None, raises=None):
        self.chunks = chunks
        self.usage = usage or ProviderUsage(input_tokens=1, output_tokens=1, accounting_units=1,
                                           certainty="reported")
        self.raises = raises
        self.calls = 0

    def supports(self, model):
        return FixtureProvider("abstain").supports(model)

    def reply(self, binding):
        self.calls += 1
        if self.raises:
            raise self.raises
        return ProviderReply(self.chunks, self.usage)


def encoded(action="abstain", payload=None):
    return json.dumps({"schema_version": "1", "action": action, "rationale": "Synthetic", "payload": payload}).encode()


@pytest.mark.parametrize("field,value", [("provider_id", "remote"), ("model_id", "different"),
                                         ("model_revision", "2")])
def test_unreviewed_model_rejected_before_call(field, value):
    binding = attempt(lambda d: d["context"]["model"].update({field: value}))
    provider = ControlledProvider([encoded()])
    assert observe(binding, provider).document().status == "policy_rejected"
    assert provider.calls == 0


def test_schema_mismatch_and_action_policy_are_not_permission():
    binding = attempt(lambda d: d["context"]["output_schema"].update(sha256="f" * 64))
    provider = ControlledProvider([encoded()])
    assert observe(binding, provider).document().status == "policy_rejected"
    assert provider.calls == 0
    binding = attempt(lambda d: d["context"].update(allowed_actions=["propose_campaign"]))
    observation = observe(binding, provider).document()
    assert observation.status == "policy_rejected"
    assert observation.reason_code == "action_not_allowed"


@pytest.mark.parametrize("variant,code", [
    ("missing", "missing_proposal_payload"), ("abstain", "abstention_payload"),
    ("foreign", "proposal_scope_mismatch"), ("invented", "unselected_payload"),
    ("modified", "unselected_payload"),
])
def test_proposal_cannot_invent_or_substitute_artifact(variant, code):
    binding = attempt()
    payload = binding.request.document().context.entries[0].artifact.model_dump(mode="json")
    action = "propose_knowledge_change"
    if variant == "missing":
        payload = None
    elif variant == "abstain":
        action = "abstain"
    elif variant == "foreign":
        payload["scope"]["project_id"] = "foreign"
    elif variant == "invented":
        payload["artifact_id"] = "invented"
    else:
        payload["sha256"] = "f" * 64
    wire = observe(binding, ControlledProvider([encoded(action, payload)])).document()
    assert wire.reason_code == code
    assert wire.proposal is None


@pytest.mark.parametrize("raw,code", [
    (b"\xff", "invalid_output"), (b'{"x":NaN}', "nonfinite_output"),
    (b'{"action":"abstain","action":"execute_code"}', "duplicate_output_key"),
    (b"[" * 1100, "invalid_output"), (b"{}", "invalid_output"),
], ids=["utf8", "nonfinite", "duplicate", "deep", "shape"])
def test_strict_provider_json(raw, code):
    wire = observe(attempt(), ControlledProvider([raw])).document()
    assert wire.status == "invalid" and wire.reason_code == code


def test_empty_chunk_flood_and_wrong_type_are_bounded():
    for chunks in [[b""] * (MAX_CHUNKS + 1), ["text"]]:
        wire = observe(attempt(), ControlledProvider(chunks)).document()
        assert wire.status == "invalid" and wire.reason_code == "output_stream_limit"
        assert not wire.output_complete and wire.captured_bytes == 0


def test_unknown_dispatch_does_not_leak_error_or_invent_usage():
    observation = observe(attempt(), ControlledProvider([], raises=RuntimeError("private provider secret")))
    wire = observation.document()
    assert wire.status == "unknown" and wire.reason_code == "dispatch_outcome_unknown"
    assert wire.usage.accounting_units is None
    assert b"private provider secret" not in observation.canonical


def test_malformed_and_partial_usage_preserve_uncertainty():
    original = ProviderUsage(input_tokens=1, output_tokens=None, accounting_units=None, certainty="reported")
    observation = observe(attempt(), ControlledProvider([encoded()], original)).document()
    assert observation.usage.certainty == "unknown" and observation.usage.input_tokens == 1
    forged = original.model_copy(update={"input_tokens": "not a count"})
    observation = observe(attempt(), ControlledProvider([encoded()], forged)).document()
    assert observation.usage.certainty == "unknown" and observation.usage.input_tokens is None


def test_delayed_reply_retains_original_attempt_and_does_not_block_other_call():
    entered, release = Event(), Event()
    def barrier():
        entered.set()
        assert release.wait(5)
    original = attempt()
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(observe, original, FixtureProvider("delayed", barrier))
        try:
            assert entered.wait(5)
            changed = attempt(lambda d: d.update(decision_scope="f" * 64))
            assert observe(changed, FixtureProvider("abstain")).document().status == "abstained"
        finally:
            release.set()
        delayed = future.result(5).document()
    assert delayed.attempt == original.reference()
    with pytest.raises(ValueError, match="attempt_binding_mismatch"):
        changed.validate(delayed.attempt)


def test_fixture_configuration_fails_explicitly():
    with pytest.raises(ValueError, match="unknown_fixture_variant"):
        FixtureProvider("invented")
    wire = observe(attempt(), FixtureProvider("delayed")).document()
    assert wire.status == "unknown" and wire.reason_code == "dispatch_outcome_unknown"
