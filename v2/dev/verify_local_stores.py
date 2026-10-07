"""Verify dedicated local stores without owner migrations or credential output."""
import hashlib
import json
import os
from datetime import datetime
from pathlib import Path
import urllib.error
import urllib.request

import psycopg

from amphora_deployment.credentials import CredentialVault
from amphora_deployment.installation import OWNERS
from amphora_deployment.persistence import ensure_local_stores


def verify(root):
    first = ensure_local_stores(root)
    encrypted = (root / 'credentials.dpapi').read_bytes()
    bundle = CredentialVault(root / 'credentials.dpapi', first['deployment_id']).load()
    observations = []
    for owner in OWNERS.values():
        for role in (owner.migration_role, owner.service_role):
            password = bundle.environment(['PG_' + role.upper() + '_PASSWORD'])['PG_' + role.upper() + '_PASSWORD']
            with psycopg.connect(host='127.0.0.1', port=first['postgres']['port'], dbname='amphora_local',
                                 user=role, password=password, connect_timeout=5) as connection:
                assert connection.execute('SELECT current_user').fetchone()[0] == role
                for target in OWNERS.values():
                    usage, create = connection.execute("SELECT has_schema_privilege(current_user,%s,'USAGE'), has_schema_privilege(current_user,%s,'CREATE')", (target.schema, target.schema)).fetchone()
                    assert usage == (target.name == owner.name)
                    assert create == (target.name == owner.name and role == owner.migration_role)
                flags = connection.execute('SELECT rolsuper,rolcreatedb,rolcreaterole,rolreplication FROM pg_roles WHERE rolname=current_user').fetchone()
                assert flags == (False, False, False, False)
                if role == owner.service_role:
                    try:
                        connection.execute('CREATE TABLE ' + owner.schema + '.deployment_denial_probe (id integer)')
                    except psycopg.errors.InsufficientPrivilege:
                        connection.rollback()
                    else:
                        connection.rollback()
                        raise AssertionError('serving role unexpectedly permitted DDL')
            observations.append({'role': role, 'authenticated': True, 'schema_scope': owner.schema, 'ddl': role == owner.migration_role})
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    endpoint = 'http://127.0.0.1:' + str(first['qdrant']['port']) + '/collections'
    denied = []
    for headers in ({}, {'api-key': 'deliberately-invalid-deployment-probe'}):
        try:
            opener.open(urllib.request.Request(endpoint, headers=headers), timeout=5)
        except urllib.error.HTTPError as error:
            assert error.code in (401, 403)
            denied.append(error.code)
        else:
            raise AssertionError('unauthorized Qdrant request accepted')
    second = ensure_local_stores(root)
    assert first == second
    assert encrypted == (root / 'credentials.dpapi').read_bytes()
    return {'checked_at': datetime.now().astimezone().isoformat(timespec='seconds'),
            'state': second, 'roles': observations, 'qdrant_denials': denied,
            'authenticated_qdrant': True, 'resume_preserved_identity_and_ciphertext': True,
            'vault_ciphertext_sha256': hashlib.sha256(encrypted).hexdigest(),
            'limitations': 'No owner migrations, service startup, container restart, backup or power-loss proof.'}


if __name__ == '__main__':
    try:
        result = verify(Path(os.environ['LOCALAPPDATA']) / 'Amphora/local-v2/installation')
    except Exception:
        # Driver libraries can embed credentials in exceptions. Never print them.
        raise SystemExit('Local store verification failed; no raw diagnostics emitted.') from None
    output = Path('.test-results/local-stores-20261006a')
    output.mkdir(parents=True, exist_ok=True)
    (output / 'evidence.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print('Local store role/auth/resume verification passed; evidence:', output / 'evidence.json')
