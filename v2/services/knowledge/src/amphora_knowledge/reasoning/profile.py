"""Owner-configured ground rules; requests only select exact pinned definitions."""

from dataclasses import dataclass

from amphora_contracts_knowledge import ReasoningRequest, ReasoningRuleSet, RuleSetRef
from pydantic import BaseModel

from ..authoring.canonical import KnowledgeError, canonical, digest
from .binding import GraphInputs
from .evaluator import Evaluator
from .model import Atom, Fact, Limits, Program, Rule


def raw(value):
    """Preserve invalid constructed scalar types until strict DTO validation."""
    if isinstance(value, BaseModel):
        return {field: raw(getattr(value, field)) for field in type(value).model_fields} | (value.model_extra or {})
    if isinstance(value, (tuple, list)):
        return tuple(raw(item) for item in value)
    if isinstance(value, dict):
        return {key: raw(item) for key, item in value.items()}
    return value


def fact(literal):
    return Fact(Atom(digest(literal.subject), literal.predicate, digest(literal.object)), literal.polarity)


@dataclass(frozen=True)
class RuleProfile:
    record: ReasoningRuleSet

    def __post_init__(self):
        record = ReasoningRuleSet.model_validate(raw(self.record))
        if record.context.scope != record.graph.scope:
            raise KnowledgeError("reasoning_profile_scope_mismatch")
        for rule in record.rules:
            for literal in (*rule.premises, rule.conclusion):
                if literal.subject.graph != record.graph or literal.object.graph != record.graph:
                    raise KnowledgeError("reasoning_profile_scope_mismatch")
        # Domain objects validate identity uniqueness and the closed finite rule shape.
        Program(record.version, tuple(Rule(rule.rule_id, tuple(fact(p) for p in rule.premises),
            fact(rule.conclusion)) for rule in record.rules))
        rules = tuple(rule.model_copy(update={"premises": tuple(sorted(rule.premises, key=canonical))})
            for rule in sorted(record.rules, key=lambda rule: rule.rule_id))
        object.__setattr__(self, "record", record.model_copy(update={"rules": rules}))

    @property
    def reference(self):
        return RuleSetRef(graph=self.record.graph, rule_set_id=self.record.rule_set_id,
            version=self.record.version, sha256=digest(self.record))

    def evaluate(self, principal, state, request):
        from .projection import Evaluation

        request = ReasoningRequest.model_validate(raw(request))
        principal.require("reason_graph", request.snapshot.graph.scope)
        if request.snapshot != state.reference:
            raise KnowledgeError("reasoning_snapshot_mismatch")
        if request.rule_set != self.reference or state.graph != self.record.graph:
            raise KnowledgeError("reasoning_profile_mismatch")
        if request.context != self.record.context or request.subject.scope != state.graph.scope:
            raise KnowledgeError("reasoning_applicability_mismatch")
        if len(set(request.targets)) != len(request.targets):
            raise KnowledgeError("duplicate_reasoning_target")
        # No undeclared predicates, foreign graph refs or invented entity revisions.
        literals = list(request.targets)
        for rule in self.record.rules:
            literals.extend((*rule.premises, rule.conclusion))
        for literal in literals:
            if literal.subject.graph != state.graph or literal.object.graph != state.graph:
                raise KnowledgeError("reasoning_literal_graph_mismatch")
            left, right = state.entities.find(literal.subject), state.entities.find(literal.object)
            state.vocabulary.require_relation(literal.predicate, left.entity_type, right.entity_type)
        bound = GraphInputs.from_state(state, request.context)
        program = Program(self.record.version, tuple(Rule(rule.rule_id, tuple(fact(p) for p in rule.premises),
            fact(rule.conclusion)) for rule in self.record.rules))
        limits = self.record.limits
        closure = Evaluator(Limits(limits.depth, limits.work, limits.facts)).evaluate(program, bound.seeds)
        return Evaluation(request, bound, closure, tuple(literals), state)
