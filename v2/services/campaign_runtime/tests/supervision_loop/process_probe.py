"""Explicit pytest subprocess entry for durable Runtime checkpoint barriers."""

import json
import os
from pathlib import Path

from amphora_campaign_runtime.lifecycle.access import RuntimePrincipal
from amphora_campaign_runtime.supervision_context.preparation import ContextPreparer
from amphora_campaign_runtime.supervision_winners import WinnerStore
from amphora_contracts_supervision import SupervisionRef

from ..supervision_resolution.support import record_response, save_report, setup


def test_process_boundary(graph_env):
    mode = os.environ['AMPHORA_RUNTIME_PROBE_MODE']
    path = Path(os.environ['AMPHORA_RUNTIME_PROBE_STATE'])
    if mode in {'request', 'response'}:
        actor, ref, slot, preparer, original, resolver = setup(graph_env)
        response_id = None
        if mode == 'response':
            response = record_response(actor, ref, slot, preparer, original)
            save_report(resolver, actor, original, response)
            response_id = response.response_id
        assert WinnerStore(graph_env.env.engine).read(actor, ref) is None
        path.write_text(json.dumps({'pid': os.getpid(), 'mode': mode, 'actor': actor.actor_id,
            'actions': sorted(actor.actions), 'reference': ref.model_dump(mode='json'),
            'request_sha256': original.frame.request_sha256, 'command_hex': original.canonical_command.hex(),
            'response_id': response_id}), encoding='utf-8')
        os._exit(73)

    assert mode == 'recover'
    metadata = json.loads(path.read_bytes())
    ref = SupervisionRef.model_validate(metadata['reference'])
    actor = RuntimePrincipal(metadata['actor'], ref.scope, frozenset(metadata['actions']))
    assert metadata['pid'] != os.getpid()
    preparer = ContextPreparer(graph_env.env.engine,
        {(actor.scope.tenant_id, actor.scope.project_id, actor.actor_id): 'fixture'}, None)
    original = preparer.prepare(actor, ref)
    assert original.frame.request_sha256 == metadata['request_sha256']
    assert original.canonical_command.hex() == metadata['command_hex']
    if metadata['mode'] == 'request':
        # Actual owner journal and dispatcher; explicitly scripted Planning peer.
        from amphora_campaign_runtime.supervision_delivery import RequestDispatcher
        from amphora_campaign_runtime.supervision_journal.delivery import (
            DeliveryJournal,
        )

        from .support import Planning
        peer = Planning(actor.scope)
        dispatcher = RequestDispatcher(DeliveryJournal(preparer.journal), peer)
        dispatcher.run(actor, ref, original.frame.request_sha256)
        dispatcher.run(actor, ref, original.frame.request_sha256)
        assert peer.calls.count('submit') == 1
        assert WinnerStore(graph_env.env.engine).read(actor, ref) is None
    else:
        store = WinnerStore(graph_env.env.engine)
        winner = store.resolve(actor, ref, response_id=metadata['response_id'])
        assert winner.document().outcome.kind == 'model_accepted' and winner.selection is not None
        assert store.resolve(actor, ref, response_id=metadata['response_id']) == winner
    path.with_suffix('.recovered.json').write_text(json.dumps({'pid': os.getpid(), 'mode': metadata['mode'],
        'request_sha256': original.frame.request_sha256}), encoding='utf-8')
