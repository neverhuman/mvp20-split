"""Resolve repair authority from Planning's immutable records before peer I/O."""

from dataclasses import dataclass

from ..context.policy import require
from ..extraction import ExtractionSnapshot, TraceProjection
from ..persistence.extraction import ExtractionJournal
from ..persistence.journal import PlanningJournal
from ..persistence.repair import RepairJournal
from ..providers.capture import Observation
from .binding import RepairRoot


@dataclass(frozen=True)
class RepairHistory:
    root: RepairRoot
    task: ExtractionSnapshot
    projection: TraceProjection
    observation: Observation
    prior: TraceProjection | None

    @classmethod
    def read(cls, engine, principal, root_reference, parent_reference):
        families, traces = RepairJournal(engine), ExtractionJournal(engine)
        root = families.read(principal, root_reference)
        require(root is not None and root.root.task.document().engagement == root_reference, "repair_root_unknown")
        parent = traces.read_trace(principal, parent_reference)
        require(parent is not None, "extraction_parent_unknown")
        document = parent.projection.document()
        membership = families.read(principal, document.attempt.engagement)
        require(membership is not None and membership.root.canonical == root.root.canonical, "repair_parent_membership")
        task = traces.read_task(principal, document.task_id)
        attempt = PlanningJournal(engine).read_attempt(principal, document.attempt)
        require(task is not None and attempt is not None and attempt.observation is not None, "repair_parent_history")
        prior = None if document.prior is None else traces.read_trace(principal, document.prior).projection
        return cls(root.root, task.snapshot, parent.projection, attempt.observation, prior)
