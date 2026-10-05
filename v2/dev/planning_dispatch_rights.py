"""Bounded actual source-rights sequence, separate from compiler crash acceptance."""


def verify_rights(worker, heartbeat, data, scope):
    def rights(revision, granted):
        data.call('POST', '/v1/acquisition/rights', {'wire_version': '1',
            'reference': {'scope': scope, 'rights_id': 'packet-roots', 'revision': revision},
            'supersedes': {'scope': scope, 'rights_id': 'packet-roots', 'revision': revision - 1},
            'status': 'granted' if granted else 'revoked', 'allowed_uses': ['read', 'process'] if granted else [],
            'expires_at': None, 'retention': 'retain_audit_payload'})

    # Original request/packet/body consumption and accounting already exist.
    rights(2, False)
    blocked = worker('rights-revoked')
    assert blocked['pause_reason'] == 'input_unavailable' and blocked['dispatches'] == 0
    assert worker('assert-absent')['state'] == 'absent'
    rights(3, True)
    for _ in range(4):
        heartbeat()
        saved = worker('rights-restored-save')
        if saved['state'] == 'saved':
            break
        assert saved['state'] == 'candidate'
    assert saved['state'] == 'saved'
    rights(4, False)
    blocked = worker('rights-revoked-validation')
    assert blocked['pause_reason'] == 'input_unavailable' and blocked['dispatches'] == 0
    assert worker('saved-history')['state'] == 'saved_history_exact'
    rights(5, True)
    for _ in range(4):
        heartbeat()
        compiled = worker('rights-restored-validation')
        if compiled['terminal']:
            break
        assert compiled['state'] == 'candidate'
    assert compiled['state'] == 'compiled'
    return saved, compiled
