"""Exact predecessor and parent carry validation, independent of Runtime acceptance."""

from dataclasses import dataclass
import hashlib

from amphora_contracts_population import (
    BirthManifest, CandidateBirth, PopulationCheckpoint, PopulationSelectionReceipt,
    ProposedSuccessor, candidate_birth_schema, population_record_schema, membership_manifest_schema,
)

from ..randomness import CounterRandom
from ..ranking import require
from ..variation import ParentVector
from .birth import NumericBirth
from .pages import RecordPages
from .specification import canonical
from .retained import PopulationArtifact
from .selection import PopulationDecision


@dataclass(frozen=True)
class SelectedGeneration:
    artifact: PopulationArtifact
    record: PopulationCheckpoint
    decision: PopulationDecision
    parents: tuple[NumericBirth, ...]

    @classmethod
    def verify(cls, checkpoint, selection, decision, pool_reference, fitness_reference, parent_artifacts):
        """Inputs are independently retained sources; owner must check accepted history."""
        identity = decision.pool.identity
        receipt = selection.decode(PopulationSelectionReceipt, population_record_schema("population.selection-receipt"), identity.scope)
        decision.verify_receipt(receipt, pool_reference, fitness_reference)
        record = checkpoint.decode(PopulationCheckpoint, population_record_schema("population.checkpoint"), identity.scope)
        require(record.generation == identity and record.selection == selection.reference, "checkpoint_selection_binding")
        original = decision.pool.original
        rng = CounterRandom.from_record(record.rng, expected_seed=original.record.seed)
        budget, progress = original.record.budget, record.progress
        dimensions = len(original.record.variables)
        expected_counter = budget.population_size * (dimensions + identity.generation * (3 + 3 * dimensions))
        require(rng.counter == expected_counter, "checkpoint_rng_position")
        require(progress.evaluations_terminal == progress.evaluations_issued <= budget.max_evaluations,
                "checkpoint_terminal_progress")
        # A terminal unavailable evaluation can have no physical attempt (e.g. a
        # failed prerequisite). Logical evaluations and worker attempts are distinct.
        require(progress.attempts_issued <= budget.max_attempts
                and progress.activations_created <= budget.max_activations, "checkpoint_work_budget")
        require(progress.unchanged_front_generations <= identity.generation, "checkpoint_front_progress")
        require(type(parent_artifacts) is tuple and len(parent_artifacts) == len(decision.selected), "checkpoint_parent_coverage")
        members = {m.candidate_id: m for m in decision.pool.members}
        parents = []
        for candidate_id, artifact in zip(decision.selected, parent_artifacts, strict=True):
            member = members[candidate_id]
            require(artifact.reference == member.birth, "checkpoint_parent_artifact")
            birth = NumericBirth(original, artifact.decode(CandidateBirth, candidate_birth_schema(), identity.scope))
            require(birth.record.candidate_id == candidate_id and birth.record.disposition == "proposed"
                    and birth.record.generation <= identity.generation and birth.record.draws.end <= rng.counter,
                    "checkpoint_parent_birth")
            parents.append(birth)
        return cls(checkpoint, record, decision, tuple(parents))

    @property
    def stop_reason(self):
        budget, progress = self.decision.pool.original.record.budget, self.record.progress
        # Before any fitness exists, resource exhaustion is not a scientific failure.
        if not progress.evaluations_issued:
            if budget.max_evaluations < len(self.decision.pool.original.record.method_graph.methods):
                return "evaluation_budget"
            if budget.max_attempts < len(self.decision.pool.original.record.method_graph.methods):
                return "attempt_budget"
        if self.decision.stopped:
            return self.decision.disposition
        if self.record.generation.generation == budget.successor_generations:
            return "generation_budget"
        if budget.max_evaluations - progress.evaluations_issued < len(self.decision.pool.original.record.method_graph.methods):
            return "evaluation_budget"
        if budget.max_attempts - progress.attempts_issued < len(self.decision.pool.original.record.method_graph.methods):
            return "attempt_budget"
        if progress.activations_created == budget.max_activations:
            return "activation_budget"
        if budget.unchanged_front_limit is not None and progress.unchanged_front_generations >= budget.unchanged_front_limit:
            return "unchanged_front"
        return None


@dataclass(frozen=True)
class SuccessorContinuity:
    source: SelectedGeneration
    record: ProposedSuccessor
    births: tuple[NumericBirth, ...]

    @classmethod
    def verify(cls, source, artifact, birth_manifest, birth_payloads, cohort, cohort_reference,
               pool, pool_reference, evaluations):
        old = source.record
        original = source.decision.pool.original
        require(source.stop_reason is None, "successor_stopped_predecessor")
        record = artifact.decode(ProposedSuccessor, population_record_schema("population.proposed-successor"), old.generation.scope)
        require(record.generation.generation == old.generation.generation + 1
                and record.generation.predecessor == source.artifact.reference
                and record.generation.run_id == old.generation.run_id
                and record.generation.specification_sha256 == old.generation.specification_sha256,
                "successor_predecessor")
        require(record.selection == old.selection, "successor_selection")
        require(cohort.original == pool.original == original and cohort.identity == pool.identity == record.generation
                and cohort.role == "cohort" and pool.role == "selection_pool", "successor_membership")
        require(record.cohort == cohort_reference and record.pool == pool_reference
                and evaluations.frozen.membership == cohort, "successor_source_binding")
        require(all(r.scope == old.generation.scope and r.schema_ref == membership_manifest_schema()
                    and r.media_type == "application/json" for r in (cohort_reference, pool_reference)),
                "successor_source_schema")
        require(record.evaluations == evaluations.artifact.reference, "successor_evaluation_binding")
        root = birth_manifest.decode(BirthManifest, population_record_schema("population.birth-manifest"), old.generation.scope)
        require(root.generation == record.generation and record.births == birth_manifest.reference, "successor_birth_manifest")
        rows = RecordPages.verified(root.generation, "population.birth-page", root.pages, birth_payloads, root.birth_count).records
        births = tuple(sorted((NumericBirth(original, row) for row in rows), key=lambda b: b.record.ordinal))
        require(tuple(b.record.ordinal for b in births) == tuple(range(original.record.budget.population_size)),
                "successor_birth_slots")
        rng = CounterRandom.from_record(old.rng, expected_seed=original.record.seed)
        parents = tuple(ParentVector(b.record.candidate_id, b.record.genes) for b in source.parents)
        seen = {b.record.genes: b.record.candidate_id for b in source.parents}
        proposed = {}
        rejected = 0
        costs = {}
        for key in evaluations.frozen.keys:
            costs[key.record.candidate_id] = costs.get(key.record.candidate_id, 0) + 1
        remaining_evaluations = original.record.budget.max_evaluations - old.progress.evaluations_issued
        remaining_attempts = original.record.budget.max_attempts - old.progress.attempts_issued
        required = sum(method.required for method in original.record.method_graph.methods)
        for birth in births:
            row = birth.record
            require(row.generation == record.generation.generation and row.draws.start == rng.counter, "successor_draw_continuity")
            birth.verify_parent_pool(parents)
            rng = CounterRandom(original.record.seed, row.draws.end)
            if row.genes in seen:
                require(row.disposition == "duplicate" and row.duplicate_of == seen[row.genes], "successor_duplicate")
            elif row.disposition == "rejected":
                cost = len(original.record.method_graph.methods)
                reason = "evaluation_budget" if remaining_evaluations < cost else "attempt_budget" if remaining_attempts < cost else None
                require(reason is not None and row.reason_code == reason, "successor_rejection_policy")
                rejected += 1
            else:
                require(row.disposition == "proposed", "successor_birth_disposition")
                require(required <= costs.get(row.candidate_id, 0) <= min(remaining_evaluations, remaining_attempts), "successor_birth_evaluation_budget")
                remaining_evaluations -= costs[row.candidate_id]
                remaining_attempts -= costs[row.candidate_id]
                proposed[row.candidate_id] = birth
                seen[row.genes] = row.candidate_id
        require(record.rng == rng.to_record(), "successor_rng_tail")
        require({m.candidate_id for m in cohort.members} == set(proposed)
                and all(m.source == "offspring" for m in cohort.members), "successor_offspring_coverage")
        for member in cohort.members:
            raw = canonical(proposed[member.candidate_id].record)
            # Exact independently retained birth bytes, not merely a same candidate ID.
            require(member.birth.schema_ref == candidate_birth_schema() and member.birth.media_type == "application/json"
                    and member.birth.sha256 == hashlib.sha256(raw).hexdigest() and member.birth.size_bytes == len(raw),
                    "successor_offspring_birth")
        prior = {m.candidate_id: m for m in source.decision.pool.members}
        expected = tuple(sorted((*cohort.members, *(prior[key].model_copy(update={"source": "parent"})
                          for key in source.decision.selected)), key=lambda m: m.candidate_id))
        require(pool.members == expected, "successor_parent_union")
        reserved = len(evaluations.frozen.keys)
        require(record.evaluations_reserved == reserved and old.progress.evaluations_issued + reserved <= original.record.budget.max_evaluations,
                "successor_evaluation_budget")
        require(old.progress.attempts_issued + reserved <= original.record.budget.max_attempts, "successor_attempt_budget")
        expected_disposition = "evaluate" if proposed else "evaluation_budget" if rejected else "duplicate_only"
        require(record.disposition == expected_disposition, "successor_disposition")
        # Allocation policy and resource/acceptance proof remain separate E1/E2 gates.
        return cls(source, record, births)
