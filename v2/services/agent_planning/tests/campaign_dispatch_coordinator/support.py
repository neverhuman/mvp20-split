"""Actual owned SQL with scripted peers; real HTTP acceptance is a separate gate."""

from datetime import UTC, datetime, timedelta

from amphora_agent_planning.campaign_authoring import AuthoringOutcome
from amphora_agent_planning.campaign_dispatch.dispatcher import CompilerDispatcher
from amphora_agent_planning.campaign_exchanges import (
    ExchangeAbsent,
    ExchangeUnavailable,
)
from amphora_agent_planning.campaign_refresh.result import RefreshFinding, RefreshResult

from ..campaign_authoring.test_values import receipt, saved, validation
from ..campaign_dispatch_storage.support import setup
from ..campaign_eligibility.test_observations import response


class Refresh:
    def __init__(self):
        self.denied, self.calls = False, 0

    def collect(self, plan):
        self.calls += 1
        failures = (RefreshFinding('data', b'fixture', 'source_access_denied'),) if self.denied else ()
        return RefreshResult(plan, datetime.now(UTC), () if self.denied else plan.artifacts, (), failures, ())


class Runtime:
    owner_id, actor_id = 'runtime', 'planning-agent'

    def __init__(self, stored, journal, lease, authoring):
        self.stored, self.journal, self.lease, self.authoring = stored, journal, lease, authoring
        self.outcomes, self.sent = {}, []
        self.read_error = self.receipt_error = self.before_send = None
        self.lose_reply, self.valid = False, True

    def receipt(self, request, window):
        if self.receipt_error is not None:
            raise self.receipt_error
        found = self.outcomes.get(request.canonical)
        if found is None:
            raise ExchangeAbsent('fixture absent')
        return AuthoringOutcome.bind(request, found.receipt)

    def readback(self, outcome, window):
        if self.read_error is not None:
            raise self.read_error
        return self.outcomes[outcome.request.canonical]

    def submit(self, request, window, *, guard):
        if self.before_send:
            self.before_send()
        guard()
        self.sent.append(request.canonical)
        value = saved(self.authoring) if request.command().identity.command_family == 'definition.save' else (
            AuthoringOutcome.bind(request, receipt(request), validation(request, valid=self.valid)))
        self.outcomes[request.canonical] = value
        if self.lose_reply:
            raise ExchangeUnavailable('fixture reply lost after commit')
        return AuthoringOutcome.bind(request, value.receipt)


class Registry:
    owner_id, actor_id = 'registry-fixture', 'planning-agent'

    def __init__(self, journal, principal, lease):
        self.journal, self.principal, self.lease = journal, principal, lease
        self.sent, self.lose_reply = [], False

    def resolve(self, owner_id, command, window, *, guard):
        guard()
        self.sent.append(command.canonical_bytes)
        if self.lose_reply:
            raise ExchangeUnavailable('fixture Registry reply lost')
        operations = self.journal.context(self.principal, self.lease.selection)
        request = next(request for _, request in operations.batch('check-1') if request.command == command)
        now = datetime.now(UTC)
        def fresh(value):
            value['decision'].update(assessed_at=now.isoformat(), capacity_valid_until=(now + timedelta(seconds=30)).isoformat())
        return response(request, change=fresh)


def fixture(stored, *, tools=False):
    store, journal, lease, authoring = setup(stored, tools=tools)
    refresh = Refresh()
    runtime, registry = Runtime(stored, journal, lease, authoring), Registry(journal, stored.principal, lease)
    dispatcher = CompilerDispatcher(journal, refresh, runtime, registry)
    return store, journal, lease, dispatcher, refresh, runtime, registry
