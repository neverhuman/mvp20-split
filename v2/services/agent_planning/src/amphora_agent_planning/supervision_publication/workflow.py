"""Bounded capture publication and original response recovery outside owner SQL."""

from ..context.policy import require
from ..publication.driver import drive_upload
from ..supervision_client import ExchangeAbsent, ExchangeUnavailable, ExchangeWindow


def release(journal, principal, lease):
    try:
        journal.release(principal, lease)
    except ValueError as error:
        if str(error) != 'capture_lease_lost':
            raise


class CapturePublisher:
    def __init__(self, journal, client):
        self.journal, self.client = journal, client

    def publish(self, principal, attempt, *, kind='primary'):
        state = self.journal.register(principal, attempt, kind=kind)
        if state.payload is None or state.attempt.stage in {'finalized', 'rejected'}:
            return state
        require(self.client.identity.actor_id == principal.actor_id and self.client.identity.scope == principal.scope,
            'capture_publication_client')
        lease = self.journal.acquire(principal, state.identity.publication_id)
        try:
            state = self.journal.read(principal, state.identity.publication_id)
            return drive_upload(self.journal, self.client, principal, lease, state)
        finally:
            release(self.journal, principal, lease)


class CaptureResponder:
    def __init__(self, journal, client):
        self.journal, self.client = journal, client

    @staticmethod
    def finished(state):
        return state.observation is not None and state.observation.status in {'recorded', 'rejected'}

    def send(self, principal, publication_id):
        principal.require('record_attempts', principal.scope)
        state = self.journal.read(principal, publication_id)
        if self.finished(state):
            return state
        require(self.client.actor_id == principal.actor_id and self.client.scope == principal.scope,
            'capture_response_client')
        captures = self.journal.captures
        lease = captures.acquire(principal, publication_id)
        try:
            state = self.journal.prepare(principal, lease)
            if self.finished(state):
                return state
            window = ExchangeWindow()
            def guard():
                captures.guard(principal, lease)
            if state.observation is None or state.observation.status == 'pending':
                guard()
                try:
                    observation = self.client.receipt(state.command, window, previous=state.observation)
                except ExchangeAbsent:
                    # A receipt that previously existed cannot safely become a new write.
                    if state.observation is not None:
                        raise ExchangeUnavailable('capture_receipt_disappeared') from None
                    observation = self.client.submit(state.command, window, guard=guard)
                state = self.journal.record(principal, lease, state.position, observation)
            if state.observation.status == 'awaiting_readback':
                guard()
                observation = self.client.readback(state.command, state.observation, window)
                state = self.journal.record(principal, lease, state.position, observation)
            return state
        finally:
            release(captures, principal, lease)
