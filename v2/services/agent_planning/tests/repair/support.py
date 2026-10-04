"""Scripted public inputs; no claim of Data publication or fresh owner contact."""

import json
from types import SimpleNamespace

from amphora_agent_planning.context import AttemptBinding
from amphora_agent_planning.extraction import TraceProjection
from amphora_agent_planning.providers import observe
from amphora_agent_planning.publication.payload import content_schema
from amphora_agent_planning.repair.binding import RepairRoot
from amphora_agent_planning.repair.feedback import RepairFeedback
from amphora_agent_planning.repair.request import RepairRequestPlan
from amphora_agent_planning.source_access import SourceReviewer
from amphora_contracts_core import ArtifactRef, Finding

from ..extraction.test_trace import Response
from ..persistence.test_reservations import policy
from ..source_access.test_review import inputs


def case(raw=None, *, entries=0):
    task, data = inputs(entries=entries)
    observed = observe(AttemptBinding(task.request, 1), Response(json.dumps(data.draft).encode() if raw is None else raw))
    projection = TraceProjection.derive("parent", task, observed)
    finding = Finding(code="fixture_unresolved", location="/assertions/0", message="Keep useful statements; clarify this item")
    feedback = RepairFeedback.create(task, projection, observed, (finding,), withheld_paths=("/assertions/0",))
    return SimpleNamespace(task=task, data=data, observed=observed, projection=projection, feedback=feedback,
        root=RepairRoot.bind(task, policy(task.request, units=10)))


def references(value):
    descriptor = value.feedback.descriptor()
    feedback = ArtifactRef(artifact_id="feedback", scope=value.task.document().scope, **descriptor.model_dump(mode="python"))
    interpretation = ArtifactRef(artifact_id="interpretation", scope=value.task.document().scope,
        sha256=value.projection.sha256, size_bytes=len(value.projection.canonical), media_type="application/json", schema_ref=content_schema())
    return feedback, interpretation


def planned(value):
    feedback, interpretation = references(value)
    return RepairRequestPlan.build(value.root, value.task, value.feedback, feedback, interpretation)


def review(value, plan):
    for reference, body in ((plan.feedback_reference(), plan.feedback.canonical),
                            (plan.interpretation_reference(), value.projection.canonical)):
        value.data.artifacts[reference.artifact_id] = reference
        value.data.payloads[reference.artifact_id] = body
    return SourceReviewer(value.data).review(plan.task)
