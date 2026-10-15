"""Reconstruct accepted successor preparation through strictly decreasing history."""
from dataclasses import dataclass

from amphora_contracts_population import (
    MembershipManifest, PopulationCheckpoint, PopulationSelectionReceipt,
    PopulationSpecification, membership_manifest_schema, population_record_schema,
    population_specification_schema,
)
from amphora_contracts_population_steps import (
    PreparedPopulationGeneration, ProposePopulationSuccessorRequest,
    SelectPopulationRequest, population_step_schema,
)
from amphora_contracts_tools import ToolBinding

from ..population.closure import GenerationPageClosure
from ..population.membership import GenerationMembership
from ..population.pages import RecordPages
from ..population.planning import EvaluationCapacity, PrimaryBirthBatch
from ..population.retained import PopulationArtifact, RetainedFitness, RetainedObservations
from ..population.specification import OriginalPopulation
from ..population.successor import SelectedGeneration
from ..ranking import require
from .inspection import PopulationInspection
from .method_plan import authored_invocation, payload_schema, read_plan
from .payloads import (
    CollectPrimaryRequest, FittedPrimaryGeneration, PreparedPrimarySuccessor,
    PrimaryOwnerEvidence, PrimarySuccessorDecision, SelectedPrimaryGeneration,
)
from .selection_evidence import SelectionEvidence


def accepted_output(owner, artifacts):
    """A canonical Runtime output and the independently read Data origin must agree."""
    producer = owner.producer
    outputs = producer.completion.result.outcome.outputs
    require(len(outputs) == 1 and outputs[0].port == "result", "successor_source_output")
    source = artifacts.read(outputs[0].artifact)
    lineage = artifacts.derivation(source.reference)
    binding = producer.invocation.tool
    transform = lineage.declaration.transformation
    require((transform.transformation_id, transform.version, transform.sha256) ==
            (binding.capability_id, binding.release, binding.image_sha256)
            and lineage.origin.actor_id == producer.worker_id, "successor_source_origin")
    require(all(item.artifact in lineage.declaration.inputs for item in producer.invocation.inputs),
            "successor_source_input_ancestry")
    return source, lineage


def unique_carrier(reference, model, schema, artifacts):
    parents = artifacts.derivation(reference).declaration.inputs
    carriers = tuple(ref for ref in parents if ref.schema_ref == schema)
    require(len(carriers) == 1, "successor_source_carrier")
    return artifacts.read(carriers[0]).decode(model, schema, artifacts.scope)


@dataclass(frozen=True)
class PreparedSuccessorSource:
    prepared: PopulationArtifact
    record: PreparedPopulationGeneration
    detail: PreparedPrimarySuccessor
    selected: SelectedGeneration
    batch: PrimaryBirthBatch
    source_pages: tuple[PopulationArtifact, ...]
    fitness: RetainedFitness
    observations: tuple[RetainedObservations, ...]

    def verify_pool(self, source, artifacts):
        from .collection import prepared_pages
        from ..population.dispatch import PreparedGeneration

        cohort = source.membership
        pool = artifacts.read(self.detail.pool)
        record = pool.decode(MembershipManifest, membership_manifest_schema(), artifacts.scope)
        pages = tuple(artifacts.read(page.artifact) for page in record.pages)
        membership = GenerationMembership.verified(cohort.original, pool.content, tuple(page.content for page in pages))
        parents = tuple(self.selected.decision.pool.by_id[key].model_copy(update={"source": "parent"})
            for key in self.selected.decision.selected)
        require(membership.identity == cohort.identity and membership.role == "selection_pool"
                and membership.members == tuple(sorted((*parents, *cohort.members), key=lambda m: m.candidate_id)),
                "successor_source_parent_union")
        prepared = PreparedGeneration.verify(self.prepared, source.declarations, self.record.specification,
            self.record.cohort, self.record.births, self.record.declarations)
        GenerationPageClosure.verify(cohort.identity, (*self.source_pages, *prepared_pages(prepared, artifacts), *pages))

    @classmethod
    def load(cls, reference, artifacts, runtime):
        prepared = artifacts.read(reference)
        record = prepared.decode(PreparedPopulationGeneration,
            population_step_schema("population-step.prepared"), artifacts.scope)
        identity = record.generation
        require(runtime is not None and 1 <= identity.generation <= 100
                and identity.run_id == artifacts.attempt.invocation.run_id
                and identity.predecessor is not None, "successor_source_generation")
        original = OriginalPopulation(artifacts.read(record.specification).decode(
            PopulationSpecification, population_specification_schema(), artifacts.scope))
        require(artifacts.implementation in original.record.implementations, "successor_source_implementation")
        checkpoint = artifacts.read(identity.predecessor)
        cp = checkpoint.decode(PopulationCheckpoint, population_record_schema("population.checkpoint"), artifacts.scope)
        require(cp.generation.scope == identity.scope and cp.generation.run_id == identity.run_id
                and cp.generation.specification_sha256 == identity.specification_sha256 == original.digest
                and cp.generation.generation + 1 == identity.generation <= original.record.budget.successor_generations
                and (cp.generation.generation == 0) == (cp.generation.predecessor is None),
                "successor_source_predecessor_generation")
        selection_request = unique_carrier(identity.predecessor, SelectPopulationRequest,
            population_step_schema("population-step.select"), artifacts)
        require(selection_request.specification == record.specification
                and selection_request.predecessor == cp.generation.predecessor,
                "successor_source_original")
        collection_request = unique_carrier(selection_request.resolution, CollectPrimaryRequest,
            payload_schema(CollectPrimaryRequest, "population-worker.collect-request"), artifacts)
        plan = read_plan(collection_request.execution_plan, artifacts)
        reads = PopulationInspection(runtime, artifacts.attempt)
        capture = reads.capture(identity.run_id, original.record.budget.max_activations)
        require(capture.snapshot.cut.plan_sha256 == plan.sha256, "successor_source_admitted_plan")
        bindings = {name: ToolBinding(capability_id="numeric.population-" + name,
            release=artifacts.implementation.version, image_sha256=artifacts.implementation.sha256,
            contract_version="1") for name in ("prepare-successor", "select-primary")}
        bindings["assemble-primary"] = original.record.assembly.tool
        owners = {name: [] for name in bindings}
        # Finish every cut-bound read before Data I/O refreshes the lease/revision.
        for node in capture.nodes:
            if node.kind != "invoke" or node.status != "succeeded":
                continue
            binding = authored_invocation(plan, node).tool
            for name, expected in bindings.items():
                if binding == expected:
                    owner = reads.method(capture, node)
                    require(owner.producer.invocation.tool == expected, "successor_source_producer_tool")
                    owners[name].append(owner)
        selected_sources = []
        for owner in owners["select-primary"]:
            source, lineage = accepted_output(owner, artifacts)
            envelope = source.decode(SelectedPrimaryGeneration,
                payload_schema(SelectedPrimaryGeneration, "population-worker.selected"), artifacts.scope)
            if envelope.checkpoint == identity.predecessor:
                selected_sources.append((source, envelope, owner, lineage))
        require(len(selected_sources) == 1, "successor_source_selection_not_accepted")
        selected_source, envelope, selector, selection_lineage = selected_sources[0]
        require(envelope.specification == record.specification and envelope.selection == cp.selection
                and envelope.generation == cp.generation and not envelope.stopped
                and envelope.stop_reason is None and envelope.work_cut.scope == artifacts.scope
                and envelope.work_cut.run_id == identity.run_id and envelope.work_cut.plan_sha256 == plan.sha256
                and envelope.work_cut.revision <= selector.producer.completion.accepted_run_revision
                and envelope.pool == selection_request.pool and envelope.fitness == selection_request.fitness
                and envelope.resolution == selection_request.resolution,
                "successor_source_selected_binding")
        require(cp.selection in selection_lineage.declaration.inputs
                and identity.predecessor in selection_lineage.declaration.inputs,
                "successor_source_selected_ancestry")
        cp_origin = artifacts.derivation(identity.predecessor)
        selector_inputs = selector.producer.invocation.inputs
        require(cp_origin.origin.actor_id == selector.producer.worker_id
                and cp_origin.declaration.transformation == selection_lineage.declaration.transformation
                and len(selector_inputs) == 1 and selector_inputs[0].port == "parameters"
                and selector_inputs[0].artifact in cp_origin.declaration.inputs,
                "successor_source_checkpoint_origin")
        require(artifacts.read(selector_inputs[0].artifact).decode(SelectPopulationRequest,
            population_step_schema("population-step.select"), artifacts.scope) == selection_request,
            "successor_source_selection_request")
        # Authenticate and replay immutable predecessor fitness without asserting a new
        # serial-selection counter cut while parallel successor work is running.
        source_proof = artifacts.read(envelope.source_proof).decode(PrimaryOwnerEvidence,
            payload_schema(PrimaryOwnerEvidence, "population-worker.owner-evidence"), artifacts.scope)
        assemblers = tuple(owner for owner in owners["assemble-primary"] if owner.producer == source_proof.producer)
        require(len(assemblers) == 1, "successor_source_fitness_not_accepted")
        fitted, fitted_lineage = accepted_output(assemblers[0], artifacts)
        fitted_record = fitted.decode(FittedPrimaryGeneration,
            payload_schema(FittedPrimaryGeneration, "population-worker.fitted"), artifacts.scope)
        require(fitted_lineage == source_proof.derivation and fitted_record.specification == record.specification
                and fitted_record.pool == selection_request.pool and fitted_record.fitness == selection_request.fitness
                and fitted_record.resolution == selection_request.resolution, "successor_source_fitness_binding")
        fitted_inputs = assemblers[0].producer.invocation.inputs
        require(len(fitted_inputs) == 1 and fitted_inputs[0].port == "parameters"
                and fitted_inputs[0].artifact == fitted_record.collected
                and all(ref in fitted_lineage.declaration.inputs for ref in
                    (fitted_record.collected, selection_request.pool, selection_request.fitness, selection_request.resolution)),
                "successor_source_fitness_input")
        evidence = SelectionEvidence.load(selection_request, original, fitted_record, collection_request, artifacts, runtime)
        fitness, pages, observations = evidence.fitness, evidence.pages, evidence.observations
        decision = fitness.selection.decide()
        receipt = artifacts.read(cp.selection)
        parent_artifacts = tuple(artifacts.read(decision.pool.by_id[key].birth) for key in decision.selected)
        selected = SelectedGeneration.verify(checkpoint, receipt, decision,
            selection_request.pool, selection_request.fitness, parent_artifacts)
        selection_record = receipt.decode(PopulationSelectionReceipt,
            population_record_schema("population.selection-receipt"), artifacts.scope)
        selection_pages = tuple(artifacts.read(page.artifact) for page in selection_record.pages)
        RecordPages.verified(cp.generation, "population.selection-page", selection_record.pages,
            tuple(page.content for page in selection_pages), selection_record.member_count)
        candidates = []
        for owner in owners["prepare-successor"]:
            source, lineage = accepted_output(owner, artifacts)
            proposal = source.decode(PrimarySuccessorDecision,
                payload_schema(PrimarySuccessorDecision, "population-worker.successor-decision"), artifacts.scope)
            if proposal.checkpoint != identity.predecessor or proposal.stopped:
                continue
            detail_source = artifacts.read(proposal.successor)
            detail = detail_source.decode(PreparedPrimarySuccessor,
                payload_schema(PreparedPrimarySuccessor, "population-worker.prepared-successor"), artifacts.scope)
            if detail.prepared == reference:
                candidates.append((owner, proposal, detail, detail_source, lineage))
        require(len(candidates) == 1, "successor_source_preparation_not_accepted")
        owner, proposal, detail, detail_source, lineage = candidates[0]
        require(detail.generation == identity and detail.source_selected == selected_source.reference
                and proposal.source_selected == selected_source.reference
                and proposal.work_cut.scope == artifacts.scope and proposal.work_cut.run_id == identity.run_id
                and proposal.work_cut.plan_sha256 == plan.sha256
                and envelope.work_cut.revision <= proposal.work_cut.revision
                <= owner.producer.completion.accepted_run_revision <= capture.snapshot.cut.revision,
                "successor_source_preparation_binding")
        invocation = owner.producer.invocation
        require(len(invocation.inputs) == 1 and invocation.inputs[0].port == "parameters", "successor_source_request")
        request = artifacts.read(invocation.inputs[0].artifact).decode(ProposePopulationSuccessorRequest,
            population_step_schema("population-step.successor"), artifacts.scope)
        require(request.specification == record.specification and request.checkpoint == identity.predecessor,
                "successor_source_request_binding")
        for child, required in ((prepared, (identity.predecessor, selected_source.reference)),
                (detail_source, (reference, detail.pool, identity.predecessor, selected_source.reference))):
            origin = artifacts.derivation(child.reference)
            require(origin.origin.actor_id == owner.producer.worker_id
                    and origin.declaration.transformation == lineage.declaration.transformation
                    and all(ref in origin.declaration.inputs for ref in (*required, invocation.inputs[0].artifact)),
                    "successor_source_child_origin")
        require(proposal.successor in lineage.declaration.inputs, "successor_source_result_ancestry")
        batch = PrimaryBirthBatch.successor(selected,
            EvaluationCapacity(detail.logical_evaluation_capacity, detail.method_attempt_capacity))
        require(detail.rng == batch.rng.to_record() and detail.disposition == batch.disposition
                and detail.evaluations_planned == batch.evaluations_reserved, "successor_source_allocator_replay")
        GenerationPageClosure.verify(identity, (*pages, *selection_pages))
        return cls(prepared, record, detail, selected, batch, (*pages, *selection_pages), fitness, observations)
