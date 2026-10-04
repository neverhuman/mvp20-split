"""Owned trace to published diagnostics for the bounded repair chain."""

import hashlib

from amphora_tool_protocol import TransportLost

from ..context.policy import require
from ..publication.records import encode
from ..repair.chain import RepairInputs
from ..repair.runner import RepairInputUnavailable
from .diagnostics import NoRepairNeeded
from .selection import ResultSelection


class DiagnosticProducer:
    def __init__(self, principal, traces, results):
        self.principal, self.traces, self.results = principal, traces, results

    def next(self, step):
        require(step.trace is not None, "diagnostic_trace_missing")
        return self.produce(step.trace.reference())

    def produce(self, reference):
        # A supplied step is only a selector. State and disposition come from owned history.
        stored = self.traces.journal.store.extractions.read_trace(self.principal, reference)
        require(stored is not None, "diagnostic_trace_unknown")
        if stored.projection.document().outcome.status in {"abstained", "policy_rejected"}:
            return None
        identifier = "d-" + hashlib.sha256(encode({"format": "planning-diagnostic-interpretation.v1",
            "actor_id": self.principal.actor_id, "trace": reference.model_dump(mode="json")})).hexdigest()
        try:
            interpretation = self.traces.publish(self.principal, identifier, reference)
            if interpretation.attempt.stage != "finalized":
                raise RepairInputUnavailable("diagnostic_interpretation_rejected")
            selection = ResultSelection.bind(self.principal, reference, identifier, "feedback", "diagnostics",
                self.results.journal.store.publisher_id)
            result = self.results.publish(self.principal, selection)
            if result.attempt.stage != "finalized":
                raise RepairInputUnavailable("diagnostic_feedback_rejected")
            return RepairInputs(reference, result.attempt.result.artifact, interpretation.attempt.result.artifact)
        except NoRepairNeeded:
            return None
        except TransportLost as error:
            raise RepairInputUnavailable("diagnostic_publication_uncertain") from error
        except (ValueError, PermissionError) as error:
            raise RepairInputUnavailable(str(error)) from error
