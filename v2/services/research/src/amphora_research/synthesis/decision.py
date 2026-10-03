"""Build route assessment history with exact alternatives, policy and all consumed source references."""
from ..persistence.decision_document import DecisionDocument
from .wire import assess_to_wire


def context_sources(context):
    return (context.conditions,) if context.purity is None else (context.conditions,context.purity)


def option_sources(option):
    route = option.evidence
    sources = list(context_sources(route.context))
    sources.extend(route.provenance.sources)
    if route.route is not None:
        sources.append(route.route)
    if route.search is not None:
        sources.append(route.search.scope)
    for step in route.steps:
        sources.extend((step.record,*step.sources))
    for check in option.checks:
        sources.extend(check.evidence)
    return tuple(sources)


def prepare(policy, options, actor, decision_id, *, consumed=()):
    assessment = assess_to_wire(policy,options)
    sources = [*context_sources(assessment.policy.context),*consumed]
    for decision in assessment.alternatives:
        sources.extend(option_sources(decision.option))
    return DecisionDocument.prepare("synthesis",policy.context.candidate.scope,actor,decision_id,assessment,sources)
