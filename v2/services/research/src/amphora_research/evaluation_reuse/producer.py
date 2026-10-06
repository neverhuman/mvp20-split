"""Bounded authenticated Runtime inspection; no claim, dispatch or table access."""
import re
from dataclasses import dataclass

from amphora_contracts_core import Scope
from amphora_contracts_execution_proofs import AcceptedToolExecution
from amphora_tool_protocol import HttpTransport, ProtocolError

from ..assessment.reader import AssessmentPeerUnavailable, _decode
from ..transport.access import AccessDenied
from .errors import ReuseError, ReusePeerUnavailable, require


@dataclass(frozen=True, slots=True)
class ProducerSelection:
    scope: Scope
    run_id: str
    completion_id: str

    def __post_init__(self):
        object.__setattr__(self, 'scope', Scope.model_validate_json(self.scope.model_dump_json()))
        require(all(isinstance(value, str) and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._:-]{0,127}', value)
            for value in (self.run_id, self.completion_id)), 'reuse_producer_identity_invalid')


class ProducerReader:
    """Fresh per resolution, at most three owner reads; no implicit retry or shared cache."""
    def __init__(self, endpoint, token, scope):
        self.scope = scope
        self._transport = HttpTransport(endpoint, token, timeout=5)
        self._calls = 0

    def read(self, selection: ProducerSelection):
        require(selection.scope == self.scope, 'reuse_producer_scope_mismatch')
        require(self._calls < 3, 'reuse_producer_read_limit')
        self._calls += 1
        try:
            reply = self._transport.request('GET',
                f'/v1/runs/{selection.run_id}/completions/{selection.completion_id}/producer', limit=262144)
        except ProtocolError as error:
            raise ReusePeerUnavailable('reuse_runtime_unavailable') from error
        if reply.status in {401, 403}:
            raise AccessDenied('access_denied')
        if reply.status == 404:
            raise ReuseError('reuse_producer_unavailable')
        if reply.status != 200:
            raise ReusePeerUnavailable('reuse_runtime_unavailable')
        try:
            proof = _decode(AcceptedToolExecution, reply.body)
        except AssessmentPeerUnavailable as error:
            raise ReusePeerUnavailable('reuse_runtime_protocol_error') from error
        report, invocation = proof.completion, proof.invocation
        require(report.scope == selection.scope and report.run_id == selection.run_id
            and report.completion_id == selection.completion_id, 'reuse_producer_selection_mismatch')
        require(report.canonical_result and report.result.outcome.status == 'succeeded'
            and invocation.activation_id == report.activation_id
            and invocation.invocation_id == report.result.invocation_id, 'reuse_producer_not_canonical_success')
        return proof
