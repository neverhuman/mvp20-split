"""Pure retained-byte oracle; no Data server, worker completion or Runtime authority."""

import hashlib
import json

import pytest
from amphora_contracts_core import ArtifactRef
from amphora_contracts_population import (
    AvailableFitness, CandidateMember, EvaluationKey, EvaluatedMethod, ExecutionPointer, FitnessRecord,
    GenerationIdentity, MembershipManifest, MembershipPageReference, MethodObservation, MethodOutput,
    ObjectiveAssessment, PopulationCheckpoint, PopulationProgress, UnavailableMethod, UnavailablePopulationFitness,
    candidate_birth_schema, membership_manifest_schema, membership_page_schema, population_record_schema,
)
from amphora_contracts_search import ObjectiveValue
from amphora_evolution_search.population import (
    BoundEvaluation, DeclaredEvaluations, FitnessEvidence, GenerationMembership, OriginalPopulation,
    PopulationArtifact, PopulationSelection, RecordPages, SelectedGeneration, canonical,
)
from amphora_evolution_search.population.closure import GenerationPageClosure
from amphora_evolution_search.population.planning import PrimaryBirthBatch


class OracleArtifacts:
    def __init__(self, scope):
        self.scope = scope
        self.values = {}
        self.pages = {}

    def put(self, name, schema, record):
        raw = canonical(record) if hasattr(record, "model_dump") else json.dumps(record, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
        item = PopulationArtifact(ArtifactRef(artifact_id=name, scope=self.scope, schema_ref=schema,
            media_type="application/json", sha256=hashlib.sha256(raw).hexdigest(), size_bytes=len(raw)), raw)
        assert name not in self.values or self.values[name] == item
        self.values[name] = item
        return item

    def page_set(self, label, kind, generation, records):
        refs = []
        for i, page in enumerate(RecordPages(generation, kind, records).pack()):
            item = self.put(label + "-" + str(i), population_record_schema(kind), page)
            self.pages[item.reference.artifact_id] = item
            rows = page.members if kind == "population.selection-page" else page.records
            refs.append(MembershipPageReference(ordinal=i, members=len(rows), artifact=item.reference))
        return tuple(refs)

    def membership(self, label, membership):
        refs, payloads = [], []
        for i, page in enumerate(membership.pages()):
            item = self.put(label + "-" + str(i), membership_page_schema(), page)
            self.pages[item.reference.artifact_id] = item
            refs.append(MembershipPageReference(ordinal=i, members=len(page.members), artifact=item.reference))
            payloads.append(item.content)
        root = MembershipManifest(schema_version="1", profile="population-membership-manifest-v1", generation=membership.identity,
            role=membership.role, member_count=len(membership.members), pages=tuple(refs))
        item = self.put(label, membership_manifest_schema(), root)
        assert GenerationMembership.verified(membership.original, item.content, tuple(payloads)) == membership
        return item.reference


def evolution(original, batch_size, reverse, *, fail_one=False):
    artifacts = OracleArtifacts(original.record.scope)
    batch = PrimaryBirthBatch.seed(original)
    previous = None
    parent_members, parent_fitness, genes = {}, {}, {}
    issued, journal, last_best, front_count = 0, [], float("inf"), 0
    for generation in range(4):
        identity = GenerationIdentity(scope=original.record.scope, run_id="pure-oracle", specification_sha256=original.digest,
            generation=generation, predecessor=previous.artifact.reference if previous else None)
        prefix = "g" + str(generation)
        cohort_members = []
        artifacts.page_set(prefix + "-births", "population.birth-page", identity, tuple(b.record for b in batch.births))
        for birth in batch.proposed:
            record = birth.record
            genes[record.candidate_id] = record.genes
            born = artifacts.put("birth-" + record.candidate_id, candidate_birth_schema(), record)
            represented = artifacts.put("vector-" + record.candidate_id, original.record.representation, {"genes": record.genes})
            cohort_members.append(CandidateMember(candidate_id=record.candidate_id, birth=born.reference,
                                                  representation=represented.reference, source="seed" if generation == 0 else "offspring"))
        cohort = GenerationMembership(original, identity, "cohort", tuple(sorted(cohort_members, key=lambda m: m.candidate_id)))
        artifacts.membership(prefix + "-cohort", cohort)
        declared = DeclaredEvaluations.primary(cohort)
        artifacts.page_set(prefix + "-slots", "population.evaluation-slot-page", identity, declared.slots)
        keys, observations = [], []
        failed_candidate = cohort.members[-1].candidate_id if fail_one and cohort.members else None
        for start in range(0, len(cohort.members), batch_size):
            for member in cohort.members[start:start + batch_size]:
                for method in original.record.method_graph.methods:
                    key = BoundEvaluation(cohort, EvaluationKey(schema_version="1", profile="population-evaluation-key-v1",
                        generation=identity, candidate_id=member.candidate_id, method_id=method.method_id, occurrence_id="primary",
                        tool=method.tool, material=member.representation, inputs=(member.representation,), conditions=method.conditions,
                        objective_policy_sha256=original.record.assembly.policy.sha256))
                    keys.append(key)
                    if member.candidate_id == failed_candidate and method == original.record.method_graph.methods[0]:
                        outcome = UnavailableMethod(status="failed", reason_code="synthetic_failure", producer=None, evidence=())
                    else:
                        pointer = ExecutionPointer(run_id=identity.run_id, activation_id="a-" + key.digest,
                            invocation_id="i-" + key.digest, attempt_id="t-" + key.digest, completion_id="c-" + key.digest)
                        outcome = EvaluatedMethod(status="evaluated", producer=pointer,
                                                  outputs=(MethodOutput(port="result", artifact=member.representation),))
                    observations.append(MethodObservation(schema_version="1", profile="population-method-observation-v1",
                        key=key.record, evaluation_sha256=key.digest, outcome=outcome))
        frozen = declared.resolve(tuple(reversed(keys)) if reverse else tuple(keys))
        evidence = FitnessEvidence(frozen, tuple(reversed(observations)) if reverse else tuple(observations))
        issued += len(keys)
        artifacts.page_set(prefix + "-keys", "population.evaluation-key-page", identity, tuple(k.record for k in frozen.keys))
        artifacts.page_set(prefix + "-observations", "population.method-observation-page", identity, evidence.observations)
        fitness = dict(parent_fitness)
        objective = original.record.assembly.objectives[0].objective
        for member in cohort.members:
            if member.candidate_id == failed_candidate:
                outcome = UnavailablePopulationFitness(status="unavailable", reason_code="synthetic_failure")
            else:
                # Independent closed-form synthetic oracle, not an imported evaluator.
                value = sum(x * x for x in genes[member.candidate_id])
                supporting = tuple(k.digest for k in frozen.keys if k.record.candidate_id == member.candidate_id)
                outcome = AvailableFitness(status="evaluated", objectives=(ObjectiveAssessment(
                    value=ObjectiveValue(objective_id=objective.objective_id, unit=objective.unit, value=value),
                    evaluations=supporting, quality="synthetic", confidence=None),), constraint_violation=0.0)
            record = FitnessRecord(schema_version="1", profile="population-fitness-v1", generation=identity,
                candidate_id=member.candidate_id, assembly=original.record.assembly.tool, policy=original.record.assembly.policy,
                evaluation_set_sha256=frozen.digest, outcome=outcome)
            fitness[member.candidate_id] = evidence.bind(record)
        pool_members = tuple(sorted((*cohort.members, *(m.model_copy(update={"source": "parent"}) for m in parent_members.values())),
                                    key=lambda m: m.candidate_id))
        pool = GenerationMembership(original, identity, "selection_pool", pool_members)
        pool_reference = artifacts.membership(prefix + "-pool", pool)
        selection = PopulationSelection(pool, tuple(fitness[m.candidate_id] for m in pool.members))
        decision = selection.decide()
        front_count = selection.front_progress(front_count)
        rank_refs = artifacts.page_set(prefix + "-ranks", "population.selection-page", identity, decision.members)
        artifacts.page_set(prefix + "-fitness", "population.fitness-page", identity, tuple(f.record for f in selection.fitness))
        # Reference pin only: full fitness-manifest resolution has separate byte-chain tests.
        fitness_reference = artifacts.put(prefix + "-fitness-source", population_record_schema("population.fitness-manifest"), {}).reference
        receipt = decision.receipt(pool_reference, fitness_reference, rank_refs)
        retained_receipt = artifacts.put(prefix + "-selection", population_record_schema("population.selection-receipt"), receipt)
        checkpoint = PopulationCheckpoint(schema_version="1", profile="population-checkpoint-v1", generation=identity,
            selection=retained_receipt.reference, rng=batch.rng.to_record(), progress=PopulationProgress(
                evaluations_issued=issued, evaluations_terminal=issued, attempts_issued=issued + 5 * (generation + 1),
                activations_created=issued + 10 * (generation + 1), unchanged_front_generations=front_count))
        retained = artifacts.put(prefix + "-checkpoint", population_record_schema("population.checkpoint"), checkpoint)
        members = pool.by_id
        parents = tuple(artifacts.values[members[key].birth.artifact_id] for key in decision.selected)
        selected = SelectedGeneration.verify(retained, retained_receipt, decision, pool_reference, fitness_reference, parents)
        best = min(sum(x * x for x in genes[key]) for key in decision.selected)
        assert best <= last_best
        last_best = best
        page_budget = GenerationPageClosure.verify(identity, tuple(artifacts.pages.values()))
        journal.append((decision.selected, tuple(genes[key] for key in decision.selected), batch.rng.counter,
                        receipt.observation_cut_sha256, page_budget.size_bytes, selected.stop_reason))
        if generation < 3:
            assert selected.stop_reason is None
            batch = PrimaryBirthBatch.successor(selected)
            previous = selected
            parent_members = {key: members[key] for key in decision.selected}
            parent_fitness = {key: fitness[key] for key in decision.selected}
        else:
            assert selected.stop_reason == "generation_budget"
    assert batch.rng.counter == 12 + 3 * 12 * 6
    return tuple(journal)


@pytest.fixture
def population_oracle(population_original):
    record = population_original.record
    original = OriginalPopulation(record.model_copy(update={"budget": record.budget.model_copy(update={
        "population_size": 12, "successor_generations": 3, "max_evaluations": 500, "dispatch_slice": 32})}))
    return lambda batch, reverse, fail=False: evolution(original, batch, reverse, fail_one=fail)
