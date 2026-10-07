"""Wrong-role startup is denied before a network connection and never echoes credentials."""

import json
import os
import subprocess
import sys

import pytest

from amphora_agent_planning.supervision_api.hosting import serving_engine


@pytest.mark.parametrize('url',[
    'postgresql+psycopg://planning_migrator:must-not-echo@127.0.0.1:1/demo',
    'postgresql+psycopg://postgres:must-not-echo@127.0.0.1:1/demo',
    'sqlite://',
])
def test_role_or_driver_rejected_without_database(url):
    with pytest.raises(ValueError,match='planning_service_role_required'):
        serving_engine(url)


def test_actual_cli_rejects_migrator_without_secret_echo():
    environment=os.environ.copy()
    environment['AMPHORA_PLANNING_DATABASE_URL']='postgresql+psycopg://planning_migrator:must-not-echo@127.0.0.1:1/demo'
    token='restricted-role-regression-token-1234567890'
    environment['AMPHORA_PLANNING_SUPERVISION_CREDENTIALS']=json.dumps([{'token':token,'actor_id':'operator',
        'scope':{'tenant_id':'internal','project_id':'demo'},'actions':['read_attempts']}])
    result=subprocess.run([sys.executable,'-I','-m','amphora_agent_planning.supervision_api','--port','19177'],
        env=environment,capture_output=True,timeout=15,creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
    assert result.returncode != 0
    assert b'Valid Planning database' in result.stderr
    assert b'must-not-echo' not in result.stderr and token.encode() not in result.stderr
    assert b'Traceback' not in result.stderr
