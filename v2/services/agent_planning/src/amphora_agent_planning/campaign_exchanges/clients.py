"""Compiled owner operations only; transport success does not authorize activation."""

from urllib.parse import quote

from amphora_contracts_graph_runtime import (
    DraftCommandReceipt,
    DraftRevision,
    DraftValidation,
)
from amphora_contracts_tools import RegistryReceipt, parse_registry_command

from ..campaign_authoring import AuthoringOutcome
from ..context.policy import require
from .transport import CompilerTransport


class RuntimeAuthoringClient(CompilerTransport):
    def __init__(self, owner_id, actor_id, endpoint, token):
        super().__init__('runtime', owner_id, actor_id, endpoint, token)

    def _request(self, request):
        command = request.command()
        require(request.owner_id == self.owner_id and command.identity.actor_id == self.actor_id,
                'compiler_owner_binding')
        return command

    def submit(self, request, window, *, guard):
        command = self._request(request)
        path = '/v1/definition-drafts/' + ('save' if command.identity.command_family == 'definition.save' else 'validate')
        receipt = self._exchange('POST', path, command.canonical_bytes, DraftCommandReceipt, 262144, window, guard=guard)
        return AuthoringOutcome.bind(request, receipt)

    def receipt(self, request, window):
        command = self._request(request)
        path = '/v1/definition-commands/' + quote(command.identity.command_family, safe='') + '/' + quote(command.identity.command_id, safe='')
        receipt = self._exchange('GET', path, None, DraftCommandReceipt, 262144, window)
        return AuthoringOutcome.bind(request, receipt)

    def readback(self, outcome, window):
        self._request(outcome.request)
        verified = AuthoringOutcome.bind(outcome.request, outcome.receipt, outcome.readback)
        require(verified == outcome and outcome.receipt.outcome.status == 'accepted', 'compiler_accepted_required')
        commit = outcome.receipt.outcome.committed
        if commit.kind == 'draft_revision':
            path = '/v1/definition-drafts/' + quote(commit.object_id, safe='') + '?revision=' + str(commit.revision)
            model = DraftRevision
        else:
            path = '/v1/definition-validations/' + quote(commit.object_id, safe='')
            model = DraftValidation
        value = self._exchange('GET', path, None, model, 1048576, window)
        return AuthoringOutcome.bind(outcome.request, outcome.receipt, value)


class RegistryEligibilityClient(CompilerTransport):
    def __init__(self, owner_id, actor_id, endpoint, token):
        super().__init__('registry', owner_id, actor_id, endpoint, token)

    def resolve(self, owner_id, command, window, *, guard):
        require(owner_id == self.owner_id and command.identity.actor_id == self.actor_id, 'compiler_owner_binding')
        verified = parse_registry_command('registry.resolve', command.canonical_bytes)
        require(verified == command, 'compiler_registry_command')
        # The Registry DTO does not echo command identity/hash. Later eligibility
        # policy binds exact scoped locks and expiry, without inventing that proof.
        return self._exchange('POST', '/v1/registry/resolve', verified.canonical_bytes,
                              RegistryReceipt, 262144, window, guard=guard)
