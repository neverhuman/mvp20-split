"""Explicit public mapping of a bound domain evaluation, not a scientific receipt."""

from dataclasses import dataclass

from amphora_contracts_knowledge import (
    CompleteReasoning,
    DerivationStep,
    GroundLiteral,
    IncompleteReasoning,
    ReasoningFinding,
    ReasoningRequest,
    ReasoningResult,
)

from ..authoring.canonical import KnowledgeError, canonical
from ..authoring.state import GraphState
from .binding import GraphInputs
from .model import Closure
from .profile import fact

MAX_EXPLANATION_REFERENCES = 16384


@dataclass(frozen=True)
class Evaluation:
    request: ReasoningRequest
    inputs: GraphInputs
    closure: Closure
    literals: tuple[GroundLiteral, ...]
    state: GraphState

    def to_record(self):
        retained = 0

        def references(origins):
            nonlocal retained
            retained += len(origins)
            if retained > MAX_EXPLANATION_REFERENCES:
                raise KnowledgeError("reasoning_explanation_limit")
            return self.inputs.references(origins)

        known = {fact(literal): literal for literal in self.literals}
        for assertion in self.state.assertions.active():
            literal = GroundLiteral(subject=assertion.subject, predicate=assertion.predicate,
                object=assertion.object, polarity=assertion.polarity)
            known[fact(literal)] = literal
        findings = []
        for target in self.request.targets:
            query = fact(target)
            conclusion = self.closure.assess(query)
            findings.append(ReasoningFinding(target=target, status=conclusion.status,
                positive=conclusion.positive, negative=conclusion.negative, conflict=conclusion.conflict,
                supporting_assertions=references(self.closure.origins(query)),
                opposing_assertions=references(self.closure.origins(query.opposite()))))
        steps = tuple(DerivationStep(fact=known[proof.fact], depth=proof.depth, rule_id=proof.rule_id,
            premises=tuple(known[premise] for premise in proof.premises),
            assertions=references(proof.origins)) for proof in self.closure.proofs)
        outcome = (CompleteReasoning(status="complete") if self.closure.complete else
            IncompleteReasoning(status="incomplete", code=self.closure.stop_code))
        result = ReasoningResult(wire_version="1", authority="synthetic_logical_entailment", request=self.request,
            outcome=outcome, work=self.closure.work, findings=tuple(findings), steps=steps,
            excluded_context=self.inputs.excluded_context)
        if len(canonical(result)) > 16 * 1024 * 1024:
            raise KnowledgeError("reasoning_result_size_limit")
        return result
