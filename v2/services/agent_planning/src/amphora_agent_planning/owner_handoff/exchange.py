"""One bounded reconciliation window; all peer calls occur outside owner SQL."""

import json

from ..context.policy import require
from .receipt import OwnerOutcome
from .transport import (
    OwnerAbsent,
    OwnerConflict,
    OwnerDenied,
    OwnerInvalid,
    OwnerUnavailable,
)


class OwnerExchange:
    def __init__(self, journal, principal, lease, transport, window, state):
        self.journal, self.principal, self.lease = journal, principal, lease
        self.transport, self.window, self.state = transport, window, state
        self.reason = None

    @property
    def request(self):
        return self.state.payload.request

    def guard(self):
        self.journal.store.guard(self.principal, self.lease)

    def _advance(self, action, data=None):
        self.state = self.journal.advance(self.principal, self.lease, self.state.position, action, data)

    def block(self, reason):
        self.reason = reason
        if not self.state.terminal and self.state.position < 63:
            self._advance("blocked", reason)

    def _uncertain(self, reason):
        self.reason = reason
        if self.state.position < 63 and self.state.progress.state == "dispatching":
            self._advance("uncertain")
        elif self.state.progress.state != "dispatching":
            self.block(reason)

    def _fault(self, error, *, writing=False):
        code = str(error)
        if code.startswith(("handoff_lease", "stored_")):
            raise error
        if isinstance(error, OwnerDenied):
            self.block("owner_access_denied")
        elif isinstance(error, OwnerConflict) or code in {
            "handoff_status_binding", "handoff_record_mismatch", "handoff_decision_binding", "handoff_accepted_binding"}:
            self.block("identity_conflict")
        elif isinstance(error, OwnerInvalid):
            self.block("request_rejected")
        else:
            reason = "owner_unavailable" if isinstance(error, (OwnerUnavailable, OwnerAbsent)) else "owner_protocol"
            if writing:
                self._uncertain(reason)
            else:
                self.block(reason)

    def observe(self, outcome):
        # A pending observation may not take the terminal slot. Its exact
        # terminal successor can still be read and appended in this window.
        terminal = outcome.state in {"acknowledged", "rejected", "conflict"}
        if self.state.position >= 63 and not terminal:
            self.reason = "event_limit"
            return
        self._advance("observed", json.loads(outcome.canonical))
        self.reason = None

    def read(self, expected_decision=None):
        try:
            record = self.transport.read(self.request, self.window, guard=self.guard)
            if self.request.owner == "research":
                outcome = OwnerOutcome.research(self.request, record)
            else:
                require(expected_decision is None or record.decision == expected_decision, "handoff_post_decision_binding")
                outcome = OwnerOutcome.knowledge(self.request, record)
        except OwnerAbsent as error:
            if expected_decision is None:
                return True
            self._fault(error, writing=True)
            return False
        except ValueError as error:
            self._fault(error, writing=expected_decision is not None)
            return False
        self.observe(outcome)
        if outcome.state == "awaiting_accepted_readback":
            try:
                accepted = self.transport.accepted(self.request, record.decision.decision.head.change,
                    self.window, guard=self.guard)
                outcome = OwnerOutcome.knowledge(self.request, record, accepted)
            except ValueError as error:
                self._fault(error)
                return False
            self.observe(outcome)
        return outcome.state == "pending"

    def submit(self):
        self._advance("dispatch")
        try:
            response = self.transport.submit(self.request, self.window, guard=self.guard)
            if self.request.owner == "research":
                outcome = OwnerOutcome.research(self.request, response)
            else:
                proposal = self.request.document()
                require(response.graph == proposal.graph and response.change_id == proposal.change_id and
                        response.request_sha256 == self.request.sha256, "handoff_decision_binding")
                outcome = None
        except ValueError as error:
            self._fault(error, writing=True)
            return
        if outcome is not None:
            self.observe(outcome)
        else:
            self.read(expected_decision=response)
