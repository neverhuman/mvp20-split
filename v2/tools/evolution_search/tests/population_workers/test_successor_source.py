"""Accepted preparation is required before any successor context can be consumed."""
import copy
import math
from types import SimpleNamespace

import pytest
from amphora_contracts_population_steps import PopulationMemberSlice, PopulationSliceRequest, population_step_schema
from amphora_evolution_search.population_workers.capabilities import PopulationCapability
from amphora_evolution_search.population_workers.methods import PrimaryMethod
from amphora_evolution_search.population_workers.payloads import PrimarySuccessorDecision, PreparedPrimarySuccessor
from amphora_evolution_search.population_workers.slices import SeedSlices
from amphora_evolution_search.population_workers.successor_preparation import SuccessorPreparation

from .successor_fixture import successor_fixture
from .test_inspection import Scripted


def consumer_fixture(e):
    c = successor_fixture(e)
    replies = copy.deepcopy(c.runtime.transport.replies)
    result = SuccessorPreparation.load(c.request, c.session, c.runtime).publish(c.session)
    decision = PrimarySuccessorDecision.model_validate_json(result.content)
    detail = PreparedPrimarySuccessor.model_validate_json(e.client.contents[decision.successor.artifact_id])
    page = replies[0]
    cut = dict(page["snapshot"]["cut"], revision=500)
    page["snapshot"]["cut"] = cut
    details = {item["node"]["activation_id"]: item for item in replies if "node" in item}
    current = next(node for node in page["nodes"] if node["path"]["node_id"] == "prepare_successor")
    current["status"] = "succeeded"
    invocation = e.attempt.invocation
    prepared_invocation = dict(node_id="prepare_successor", activation_id=current["activation_id"],
        invocation_id=current["activation_id"], tool=invocation.tool.model_dump(mode="json"),
        inputs=[dict(port="parameters", artifact=invocation.inputs[0].artifact.model_dump(mode="json"))],
        checkpoint=None, timeout_seconds=3600, side_effects="pure")
    inputs = dict(schema_version="1", profile="runtime-node-inputs-v1", scope=cut["scope"], run_id=cut["run_id"],
        activation_id=current["activation_id"], scope_key="c"*64, observed_run_revision=500,
        scope_inputs=[], invocation=prepared_invocation)
    completion = dict(scope=cut["scope"], run_id=cut["run_id"], completion_id="prepare_successor-completion",
        activation_id=current["activation_id"], accepted_run_revision=450, canonical_result=True,
        retention_reservation_ids=[], result=dict(schema_version="1", invocation_id=current["activation_id"],
            attempt_id="prepare_successor-attempt", fence=1,
            outcome=dict(status="succeeded", outputs=[dict(port="result", artifact=result.reference.model_dump(mode="json"))])))
    proof = dict(wire_version="1", authority="accepted_execution", worker_id="worker",
        invocation=prepared_invocation, completion=completion)
    responses = [page]
    proofs = {"assemble": (c.source.inputs, c.source.proof), "select": (None, c.proof),
        "prepare_successor": (inputs, proof)}
    for node in page["nodes"]:
        name = node["path"]["node_id"]
        if name not in proofs:
            continue
        detail_record = details[node["activation_id"]]
        detail_record.update(cut=cut, node=node)
        if name == "prepare_successor":
            detail_record["attempts"][0].update(status="succeeded", settled=True, canonical_result=True,
                completion_id="prepare_successor-completion")
        node_inputs, producer = copy.deepcopy(proofs[name])
        if node_inputs is None:
            node_inputs = dict(inputs, activation_id=node["activation_id"], invocation=producer["invocation"])
        node_inputs["observed_run_revision"] = 500
        responses.extend((detail_record, node_inputs, producer))
    def runtime():
        return SimpleNamespace(identity=e.client.identity, transport=Scripted(copy.deepcopy(responses)))
    return SimpleNamespace(c=c, prepared=detail.prepared, runtime=runtime, responses=responses)


def test_successor_contexts_replay_the_accepted_births_and_methods(worker_artifacts):
    e = worker_artifacts
    fixture = consumer_fixture(e)
    slices = SeedSlices.load(fixture.prepared, fixture.c.session, fixture.runtime())
    request = PopulationSliceRequest(schema_version="1", prepared=fixture.prepared, start_index=0, limit=4)
    sliced = slices.publish(request, fixture.c.session).decode(PopulationMemberSlice,
        population_step_schema("population-step.member-slice"), e.client.identity.scope)
    assert sliced.generation.generation == 1 and sliced.complete and len(sliced.members) == 4
    e.attempt.invocation.node_id = "cost"
    binding = PopulationCapability("evaluate-squares").descriptor("f"*64).tool.binding
    method = PrimaryMethod.load(fixture.c.session.read(sliced.members[0]), fixture.c.session, binding, fixture.runtime())
    assert method.record.member.source == "offspring"
    capability = PopulationCapability("evaluate-squares")
    from amphora_contracts_search import ObjectiveValue
    value = ObjectiveValue.model_validate_json(method.publish("evaluate-squares",
        capability.schema_ref("output"), fixture.c.session).content)
    assert value.value == math.fsum(g*g for g in method.birth.record.genes)


def test_successor_prepared_upload_without_accepted_output_rejects(worker_artifacts):
    e = worker_artifacts
    fixture = consumer_fixture(e)
    # Keep every Artifact valid, but remove canonical acceptance of the preparer.
    next(node for node in fixture.responses[0]["nodes"]
        if node["path"]["node_id"] == "prepare_successor")["status"] = "waiting"
    with pytest.raises(ValueError, match="not_accepted"):
        SeedSlices.load(fixture.prepared, fixture.c.session, fixture.runtime())


def test_successor_cannot_be_sliced_without_owner_inspection(worker_artifacts):
    fixture = consumer_fixture(worker_artifacts)
    with pytest.raises(ValueError, match="successor_source_generation"):
        SeedSlices.load(fixture.prepared, fixture.c.session)


def test_prepared_child_origin_must_match_the_accepted_worker(worker_artifacts):
    e = worker_artifacts
    fixture = consumer_fixture(e)
    derivation = e.client.derivation
    def mismatched_origin(reference):
        receipt = derivation(reference)
        if reference == fixture.prepared:
            return receipt.model_copy(update={"origin": receipt.origin.model_copy(update={"actor_id": "another-worker"})})
        return receipt
    e.client.derivation = mismatched_origin
    with pytest.raises(ValueError, match="child_origin"):
        SeedSlices.load(fixture.prepared, fixture.c.session, fixture.runtime())


def test_selection_work_cut_cannot_postdate_its_accepted_completion(worker_artifacts):
    fixture = consumer_fixture(worker_artifacts)
    proof = next(item for item in fixture.responses if item.get("wire_version") == "1"
        and item["invocation"]["node_id"] == "select")
    proof["completion"]["accepted_run_revision"] = 299
    with pytest.raises(ValueError, match="selected_binding"):
        SeedSlices.load(fixture.prepared, fixture.c.session, fixture.runtime())


def test_producer_tool_must_match_the_admitted_plan(worker_artifacts):
    fixture = consumer_fixture(worker_artifacts)
    proof = next(item for item in fixture.responses if item.get("wire_version") == "1"
        and item["invocation"]["node_id"] == "select")
    proof["invocation"]["tool"]["release"] = "9.9.9"
    with pytest.raises(ValueError, match="producer_tool"):
        SeedSlices.load(fixture.prepared, fixture.c.session, fixture.runtime())
