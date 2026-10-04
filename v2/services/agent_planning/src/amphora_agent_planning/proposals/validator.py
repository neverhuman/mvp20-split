"""Deterministic candidate construction; Knowledge retains final acceptance."""

import hashlib

from amphora_contracts_knowledge import (
    AddAssertion,
    AddEntity,
    AssertionRevisionRef,
    CorrectAssertion,
    DomainAssertion,
    DomainEntity,
    EntityRevisionRef,
    GraphChangeProposal,
    MergeEntities,
    RetractAssertion,
    ReviseEntityContext,
)

from ..context.policy import require
from .context import canonical, label_key
from .result import Findings
from .selection import CandidateSelection


class GraphCandidateValidator:
    def validate(self, inputs):
        return _Validation(inputs).run()


class _Validation:
    def __init__(self, inputs):
        self.inputs, self.draft = inputs, inputs.draft()
        self.task = inputs.task.document()
        self.graph = self.task.target.graph
        self.facts = inputs.knowledge.index()
        self.vocabulary = inputs.knowledge.profile().vocabulary
        self.findings = Findings()
        self.selection = CandidateSelection(self.draft, self.findings)
        self.bindings, self.operations, self.support = {}, [], []
        self.selected_context = tuple(entry.artifact for entry in inputs.task.request.document().context.entries)

    def identity(self, kind, local_id):
        return "p-" + hashlib.sha256(f"{self.inputs.task.sha256}:{kind}:{local_id}".encode()).hexdigest()

    def context(self, reference):
        require(reference is not None, "required_context_missing")
        require(reference in self.selected_context, "context_not_selected")
        return reference

    def attribution(self, value):
        self.inputs.sources.verify_attribution(value)

    def entity(self, item, *, prior=None):
        self.attribution(item.attribution)
        require(item.entity_type in self.vocabulary.entity_types, "unknown_entity_type")
        require(bool(label_key(item.label)), "empty_entity_label")
        context = getattr(item, "context", self.task.target.applicability)
        if prior is not None:
            require(prior in self.task.existing_entities, "entity_prior_not_selected")
            original = self.facts.entity(prior, editable=True)
            require(item.entity_type == original.entity_type and item.label == original.label,
                    "context_edit_changes_identity")
            require(not item.matches or item.matches == (prior,), "context_edit_match_conflict")
            require(prior.revision < 9007199254740991, "entity_revision_limit")
            reference = prior.model_copy(update={"revision": prior.revision + 1})
        elif item.matches:
            require(len(item.matches) == 1, "ambiguous_entity_match")
            reference = item.matches[0]
            require(reference in self.task.existing_entities, "entity_match_not_selected")
            original = self.facts.entity(reference)
            require(item.entity_type == original.entity_type and label_key(item.label) == label_key(original.label),
                    "entity_match_label_or_type")
            collisions = self.facts.labels(item.label, item.entity_type)
            require(len({self.facts.resolve(row.reference).entity_id for row in collisions}) <= 1,
                    "ambiguous_entity_label")
            require(context is None or context == original.context, "context_change_requires_edit")
            return original, None
        else:
            require(not self.facts.labels(item.label, item.entity_type), "existing_identity_requires_match")
            peers = [other for other in self.draft.entities if not other.matches and
                     not self.selection.owned("entities", other.local_id) and
                     other.entity_type == item.entity_type and label_key(other.label) == label_key(item.label)]
            require(len(peers) == 1, "ambiguous_candidate_label")
            identifier = self.identity("entity", item.local_id)
            require(not any(ref.entity_id == identifier for ref in self.facts.entities), "proposed_identity_exists")
            reference = EntityRevisionRef(graph=self.graph, entity_id=identifier, revision=1)
        record = DomainEntity(reference=reference, entity_type=item.entity_type, label=item.label,
                              context=self.context(context), supersedes=prior)
        operation = AddEntity(operation="add_entity", entity=record) if prior is None else ReviseEntityContext(
            operation="revise_entity_context", prior=prior, replacement=record)
        return record, operation

    def assertion(self, item, *, prior=None, edit_attribution=None):
        self.attribution(item.attribution)
        require(item.subject in self.bindings and item.object in self.bindings, "assertion_endpoint_unresolved")
        left, right = self.bindings[item.subject], self.bindings[item.object]
        predicate = next((p for p in self.vocabulary.predicates if p.predicate_id == item.predicate), None)
        require(predicate is not None, "unknown_predicate")
        require(left.entity_type in predicate.subject_types and right.entity_type in predicate.object_types,
                "predicate_endpoint_mismatch")
        require(item.attribution.origin != "inferred" or item.posture != "reported", "inferred_claim_requires_hypothesis")
        if prior is None:
            identifier = self.identity("assertion", item.local_id)
            require(not any(ref.assertion_id == identifier for ref in self.facts.assertions), "proposed_identity_exists")
            reference = AssertionRevisionRef(graph=self.graph, assertion_id=identifier, revision=1)
        else:
            require(prior in getattr(self.task, "existing_assertions", ()), "assertion_prior_not_selected")
            self.facts.assertion(prior)
            require(prior.revision < 9007199254740991, "assertion_revision_limit")
            reference = prior.model_copy(update={"revision": prior.revision + 1})
        support = (item.attribution,) if edit_attribution is None else (item.attribution, edit_attribution)
        record = DomainAssertion(reference=reference, subject=left.reference, predicate=item.predicate,
            object=right.reference, statement=item.statement, polarity=item.polarity, posture=item.posture,
            applicability=self.context(item.applicability), grounding=self.inputs.grounding(support),
            research_links=(), supersedes=prior)
        operation = AddAssertion(operation="add_assertion", assertion=record) if prior is None else CorrectAssertion(
            operation="correct_assertion", prior=prior, replacement=record)
        return operation, support

    def append(self, operation, support):
        if operation is not None:
            self.operations.append(operation)
            self.support.extend(support)

    def entity_candidates(self):
        for index, item in enumerate(self.draft.entities):
            if not self.selection.available("entities", index) or self.selection.owned("entities", item.local_id):
                continue
            found = self.findings.check(f"/entities/{index}", lambda item=item: self.entity(item))
            if found is not None:
                record, operation = found
                self.bindings[item.local_id] = record
                self.append(operation, (item.attribution,))
        for index, edit in enumerate(self.selection.edits):
            if edit.operation != "revise_entity_context" or not self.selection.available("edits", index):
                continue
            path = f"/edits/{index}"
            def revise(edit=edit):
                self.attribution(edit.attribution)
                candidate_index, candidate = self.selection.replacement("entities", edit.replacement_local_id)
                found = self.findings.check(f"/entities/{candidate_index}", lambda: self.entity(candidate, prior=edit.prior))
                require(found is not None, "replacement_candidate_unresolved")
                record, operation = found
                self.bindings[candidate.local_id] = record
                self.append(operation, (candidate.attribution, edit.attribution))
            self.findings.check(path, revise)

    def edit(self, edit):
        self.attribution(edit.attribution)
        if edit.operation == "merge_entities":
            require(edit.source in self.task.existing_entities and edit.target in self.task.existing_entities,
                    "merge_targets_not_selected")
            left, right = self.facts.entity(edit.source, editable=True), self.facts.entity(edit.target, editable=True)
            require(left.reference.entity_id != right.reference.entity_id and left.entity_type == right.entity_type,
                    "invalid_entity_merge")
            self.append(MergeEntities(operation="merge_entities", source=edit.source, target=edit.target), (edit.attribution,))
        elif edit.operation == "retract_assertion":
            require(edit.assertion in getattr(self.task, "existing_assertions", ()), "assertion_prior_not_selected")
            self.facts.assertion(edit.assertion)
            self.append(RetractAssertion(operation="retract_assertion", assertion=edit.assertion), (edit.attribution,))
        elif edit.operation == "correct_assertion":
            index, candidate = self.selection.replacement("assertions", edit.replacement_local_id)
            found = self.findings.check(f"/assertions/{index}", lambda: self.assertion(
                candidate, prior=edit.prior, edit_attribution=edit.attribution))
            require(found is not None, "replacement_candidate_unresolved")
            self.append(*found)

    def proposal(self):
        require(1 <= len(self.operations) <= 128, "proposal_operation_limit")
        identity = hashlib.sha256(self.inputs.task.canonical + self.inputs.candidate_bytes +
                                   self.inputs.interpretation_bytes).hexdigest()
        proposal = GraphChangeProposal(wire_version="1", graph=self.graph, change_id="p-" + identity,
            base=self.task.target.base, vocabulary=self.task.target.vocabulary, policy=self.task.target.policy,
            description="Attributed extraction candidates for " + self.task.task_id, rationale=self.draft.rationale,
            grounding=self.inputs.grounding(tuple(self.support)), operations=tuple(self.operations))
        encoded = canonical(proposal)
        require(len(encoded) <= 262144, "graph_proposal_size")
        return encoded

    def run(self):
        for diagnostic in self.draft.diagnostics:
            self.findings.add(diagnostic.target_path, "model_reported_" + diagnostic.kind, withhold=False)
        if self.draft.action == "abstain":
            return self.findings.result(abstained=True)
        if self.draft.action != "propose_knowledge_change":
            self.findings.add("/action", "research_handoff_required", withhold=False)
            return self.findings.result()
        self.entity_candidates()
        for index, item in enumerate(self.draft.assertions):
            if not self.selection.available("assertions", index) or self.selection.owned("assertions", item.local_id):
                continue
            found = self.findings.check(f"/assertions/{index}", lambda item=item: self.assertion(item))
            if found is not None:
                self.append(*found)
        for index, edit in enumerate(self.selection.edits):
            if edit.operation != "revise_entity_context" and self.selection.available("edits", index):
                self.findings.check(f"/edits/{index}", lambda edit=edit: self.edit(edit))
        if not self.operations:
            self.findings.add("/operations", "no_structural_operations", withhold=False)
            return self.findings.result()
        encoded = self.findings.check("/operations", self.proposal)
        return self.findings.result(encoded)
