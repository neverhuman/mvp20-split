"""Frozen explicit assembly policy; required failures never become numeric scores."""
import json
import math

import pytest
from amphora_contracts_population import CandidateBirth
from amphora_contracts_search import ObjectiveValue
from amphora_contracts_tools import ToolBinding
from amphora_evolution_search.population.fitness import FitnessEvidence
from amphora_evolution_search.population_workers.collection import PrimaryCollection
from amphora_evolution_search.population_workers.fitness_policy import PrimaryFitness
from amphora_evolution_search.population_workers.payloads import PrimarySumPolicy,UnconstrainedSynthetic
from amphora_evolution_search.population_workers.capabilities import PopulationCapability

from .collection_fixture import fixture


def policy_case(e,status="succeeded"):
    binding=ToolBinding(capability_id="numeric.population-assemble-primary",release=PopulationCapability("seed").release,
        image_sha256="f"*64,contract_version="1")
    c=fixture(e,status,assembly_binding=binding)
    collected=PrimaryCollection.load(c.request,c.session,c.runtime)
    evidence=FitnessEvidence(c.prepared.declarations.resolve(collected.keys),collected.observations)
    values=tuple((row.evaluation_sha256,ObjectiveValue.model_validate_json(e.client.contents[row.outcome.outputs[0].artifact.artifact_id]))
        for row in collected.observations if row.outcome.status=="evaluated")
    policy=PrimaryFitness(evidence,values,binding,PrimarySumPolicy(schema_version="1",profile="primary-dimensionless-sum-v1"),
        UnconstrainedSynthetic(schema_version="1",profile="unconstrained-synthetic-v1"))
    return c,policy


@pytest.mark.parametrize("status",["succeeded","failed","skipped","blocked"])
def test_available_values_match_frozen_genes_and_unavailable_never_has_score(worker_artifacts,status):
    e=worker_artifacts;c,policy=policy_case(e,status)
    records=policy.records()
    assert len(records)==4
    available=tuple(item for item in records if item.record.outcome.status=="evaluated")
    unavailable=tuple(item for item in records if item.record.outcome.status=="unavailable")
    assert len(available)==(4 if status=="succeeded" else 3)
    for item in available:
        member=c.prepared.declarations.membership.by_id[item.record.candidate_id]
        birth=CandidateBirth.model_validate_json(e.client.contents[member.birth.artifact_id])
        assert item.score.objectives==(math.fsum(gene*gene for gene in birth.genes),)
        assert item.record.outcome.constraint_violation==0.0
        assert item.record.outcome.objectives[0].quality=="synthetic"
    for item in unavailable:
        assert item.record.outcome.reason_code=="required_method_unavailable"
        with pytest.raises(ValueError,match="fitness_not_available"):item.score


def test_missing_value_cannot_default_to_zero(worker_artifacts):
    _,policy=policy_case(worker_artifacts)
    with pytest.raises(ValueError,match="values_coverage"):
        PrimaryFitness(policy.evidence,policy.values[:-1],policy.binding,policy.policy,policy.constraints)


def test_wrong_units_cannot_be_summed(worker_artifacts):
    _,policy=policy_case(worker_artifacts)
    values=tuple((key,value.model_copy(update={"unit":"kelvin"})) for key,value in policy.values)
    bad=PrimaryFitness(policy.evidence,values,policy.binding,policy.policy,policy.constraints)
    with pytest.raises(ValueError,match="value_identity"):bad.records()


def test_constraint_or_policy_profile_cannot_be_inferred(worker_artifacts):
    _,policy=policy_case(worker_artifacts)
    with pytest.raises(ValueError):
        PrimaryFitness(policy.evidence,policy.values,policy.binding,policy.policy,
            policy.constraints.model_copy(update={"profile":"unknown-scientific-constraints"}))


def test_old_tool_payload_schema_bytes_remain_pinned():
    import hashlib
    from pathlib import Path
    pins=json.loads(Path(__file__).with_name("predecessor-schema-pins.json").read_bytes())
    assert len(pins)==22
    for key,digest in pins.items():
        operation,direction=key.split("/")
        assert hashlib.sha256(PopulationCapability(operation).schema_bytes(direction)).hexdigest()==digest


@pytest.mark.parametrize("optional_missing",[False,True])
def test_named_sum_combines_all_mapped_methods_and_preserves_optional_missing(worker_artifacts,optional_missing):
    import hashlib
    from amphora_contracts_core import ArtifactRef
    from amphora_contracts_population import CandidateMember,GenerationIdentity,EvaluationKey,MethodObservation,ExecutionPointer
    from amphora_evolution_search.population import OriginalPopulation,NumericBirth,GenerationMembership,BoundEvaluation,FrozenEvaluations,canonical
    from amphora_evolution_search.population_workers.method_plan import payload_schema
    _,base=policy_case(worker_artifacts)
    first=base.evidence.evaluations.membership.original.record.method_graph.methods[0]
    second=first.model_copy(update={"method_id":"second","node_path":("second",),"required":not optional_missing,
        "tool":first.tool.model_copy(update={"capability_id":"numeric.population-evaluate-negative-sum"})})
    source=base.evidence.evaluations.membership.original.record
    objective=source.assembly.objectives[0].model_copy(update={"method_ids":(first.method_id,) if optional_missing else (first.method_id,"second")})
    original=OriginalPopulation(source.model_copy(update={"method_graph":source.method_graph.model_copy(update={"methods":(first,second)}),
        "assembly":source.assembly.model_copy(update={"objectives":(objective,)})}))
    identity=GenerationIdentity(scope=source.scope,run_id="sum-fixture",specification_sha256=original.digest,generation=0,predecessor=None)
    members=[]
    for ordinal in range(2):
        birth=NumericBirth.seed(original,ordinal);raw=canonical(birth.record)
        ref=ArtifactRef(artifact_id="birth-"+str(ordinal),scope=source.scope,sha256=hashlib.sha256(raw).hexdigest(),
            size_bytes=len(raw),media_type="application/json",schema_ref=original.record.representation)
        members.append(CandidateMember(candidate_id=birth.record.candidate_id,birth=ref,representation=ref,source="seed"))
    membership=GenerationMembership(original,identity,"cohort",tuple(sorted(members,key=lambda member:member.candidate_id)))
    keys=[];observations=[];values=[]
    for member in membership.members:
        for method,value in ((first,2.0),(second,3.0)):
            key=BoundEvaluation(membership,EvaluationKey(schema_version="1",profile="population-evaluation-key-v1",generation=identity,
                candidate_id=member.candidate_id,occurrence_id="primary",method_id=method.method_id,tool=method.tool,
                material=member.representation,inputs=(member.representation,),conditions=method.conditions,
                objective_policy_sha256=original.record.assembly.policy.sha256))
            if optional_missing and method.method_id=="second":
                outcome={"status":"failed","reason_code":"optional_annotation_missing","producer":None,"evidence":[]}
            else:
                metric=ObjectiveValue(objective_id=objective.objective.objective_id,unit=objective.objective.unit,value=value)
                raw=canonical(metric)
                output=ArtifactRef(artifact_id="value-"+key.digest,scope=source.scope,sha256=hashlib.sha256(raw).hexdigest(),
                    size_bytes=len(raw),media_type="application/json",schema_ref=payload_schema(ObjectiveValue,"population-method.objective-value"))
                pointer=ExecutionPointer(run_id=identity.run_id,activation_id="a-"+key.digest,invocation_id="i-"+key.digest,
                    attempt_id="attempt-"+key.digest,completion_id="c-"+key.digest)
                outcome={"status":"evaluated","producer":pointer.model_dump(mode="json"),"outputs":[{"port":"result","artifact":output.model_dump(mode="json")}]}
                values.append((key.digest,metric))
            observations.append(MethodObservation.model_validate_json(json.dumps({"schema_version":"1","profile":"population-method-observation-v1",
                "key":key.record.model_dump(mode="json"),"evaluation_sha256":key.digest,"outcome":outcome})))
            keys.append(key)
    evidence=FitnessEvidence(FrozenEvaluations(membership,tuple(keys)),tuple(reversed(observations)))
    policy=PrimaryFitness(evidence,tuple(reversed(values)),base.binding,base.policy,base.constraints)
    assert all(item.score.objectives==(2.0 if optional_missing else 5.0,) for item in policy.records())
