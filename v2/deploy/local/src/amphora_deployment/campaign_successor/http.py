"""Only approved successor routes, served under the existing launch authentication."""
import json
import re
from urllib.parse import unquote

from amphora_contracts_campaign_successor_launch import SuccessorLaunchReceiptQuery
from ..campaign_launch.intent import LaunchError
from .intent import SuccessorIntent

ROOT = '/v1/campaign-successor-launches'


def route(path):
    if path in {ROOT, ROOT + '/receipts/query'}:
        return path, None
    parts = path.split('/')
    if len(parts) == 4 and '/'.join(parts[:3]) == ROOT:
        identity = unquote(parts[3])
        if re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._:-]{0,127}', identity):
            return ROOT + '/receipt', identity
    return None, None


def _query(raw):
    def unique(pairs):
        value = {}
        for key, item in pairs:
            if key in value: raise ValueError()
            value[key] = item
        return value
    try:
        json.loads(raw, object_pairs_hook=unique)
        query = SuccessorLaunchReceiptQuery.model_validate_json(raw)
        if query.identity.command_family != 'campaign.launch_successor': raise ValueError()
        return query
    except ValueError:
        raise LaunchError('launch_request_invalid') from None


def handle(handler, route_name, request_id, post, raw):
    server = handler.server
    scope = server.policy.view.scope
    if post and route_name == ROOT:
        if not server.accepting(): raise LaunchError('launch_unavailable')
        intent = SuccessorIntent.parse(raw)
        intent.authorize(server.actor_id, scope)
        state = server.journal.submit(intent, server.policy.check)
        if state.phase == 'recovery_required' and state.run_id is not None and server.recover is not None:
            server.recover(intent.key)
        handler._respond(200 if state.terminal else 202, state.receipt().model_dump(mode='json'))
        return True
    query = None
    if post and route_name == ROOT + '/receipts/query':
        query = _query(raw)
        if query.identity.actor_id != server.actor_id or query.identity.scope != scope:
            raise LaunchError('launch_scope_denied')
        request_id = query.identity.command_id
    elif post or route_name != ROOT + '/receipt':
        return False
    state = server.journal.get((scope.tenant_id, scope.project_id, server.actor_id, request_id, 'campaign.launch_successor'))
    if state is None: raise LaunchError('launch_receipt_unavailable')
    if query is not None and query.request_sha256 != state.intent.request.sha256:
        raise LaunchError('launch_request_conflict')
    handler._respond(200, state.receipt().model_dump(mode='json'))
    return True
