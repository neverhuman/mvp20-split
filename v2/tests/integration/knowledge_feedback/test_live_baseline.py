"""Actual installed source/graph baseline; later Runtime/manifest assertions extend it."""
import json
import os
import secrets
import subprocess
import uuid
from pathlib import Path

import pytest
from sqlalchemy import URL
from postgres_fixture import owned_state

from .live.process import base_environment, owned_setup
from .live.source_graph import SourceGraphScenario
from .live.runtime import CampaignScenario
from .live.representation import publish_representation
from .live.manifest import observed_manifest

pytestmark = pytest.mark.postgres


def test_actual_source_graph_baseline(tmp_path):
    if os.environ.get('AMPHORA_TEST_FEEDBACK_LIVE') != '1':
        pytest.skip('Explicit actual feedback integration opt-in required')
    assert os.environ.get('AMPHORA_TEST_POSTGRES') == '1'
    assert os.environ.get('AMPHORA_TEST_QDRANT') == '1'
    interpreters = {owner: Path(os.environ[key]).absolute() for owner, key in [
        ('data_artifacts', 'AMPHORA_TEST_DATA_PYTHON'), ('research', 'AMPHORA_TEST_RESEARCH_PYTHON'),
        ('knowledge', 'AMPHORA_TEST_KNOWLEDGE_PYTHON'), ('campaign_runtime', 'AMPHORA_TEST_RUNTIME_PYTHON')]}
    assert all(path.is_file() for path in interpreters.values())
    state = owned_state()
    host, port = state['endpoint'].split(':')
    tokens = {owner: secrets.token_hex(24) for owner in interpreters}
    environments = {}
    for owner, role in [('data_artifacts', 'artifact'), ('research', 'research'), ('knowledge', 'knowledge'), ('campaign_runtime', 'runtime')]:
        url = URL.create('postgresql+psycopg', username=role + '_service', password=state['password'],
            host=host, port=int(port), database=state['database'])
        environment = dict(base_environment(), OWNER_DATABASE=url.render_as_string(hide_password=False),
            OWNER_TOKEN=tokens[owner])
        setup = dict(environment, OWNER_MIGRATION=url.set(username=role + '_migrator').render_as_string(hide_password=False))
        owned_setup(interpreters[owner], 'import os; from amphora_' + owner +
            '.persistence.migrate import upgrade; upgrade(os.environ["OWNER_MIGRATION"])', setup)
        environments[owner] = environment
    environments['knowledge'].update(DATA_TOKEN=tokens['data_artifacts'], RESEARCH_TOKEN=tokens['research'])
    import qdrant_fixture
    qdrant = qdrant_fixture.owned_state()
    environments['data_artifacts']['QDRANT_TOKEN'] = qdrant['api_key']
    scope = {'tenant_id': 'feedback-fixture', 'project_id': uuid.uuid4().hex}
    runtime = CampaignScenario(tmp_path, scope, interpreters['campaign_runtime'], environments['campaign_runtime'])
    scenario = SourceGraphScenario(tmp_path, scope, interpreters, environments, runtime,
        {'endpoint': qdrant['endpoint'], 'token_env': 'QDRANT_TOKEN'})
    try:
        result = scenario.run()
        result['representation'] = publish_representation(scenario.data, result['span'])
        result['runtime'] = runtime.consume(scenario.data, result['publication']['outcome']['receipt'])
        result['manifest'] = observed_manifest(scope, result)
        root = Path(__file__).absolute().parents[3]
        owners = {name: {'endpoint': owner.endpoint, 'token': owner.token} for name, owner in
            [('data', scenario.data), ('research', scenario.research), ('knowledge', scenario.knowledge)]}
        probe = subprocess.run(['node', str(root / 'studio/scripts/probe-scientific.mjs')],
            input=json.dumps({'owners': owners, 'records': result}), env=base_environment(),
            capture_output=True, text=True, encoding='utf-8', timeout=45,
            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        assert probe.returncode == 0, 'Compiled Studio actual-owner probe failed: ' + probe.stderr[-1200:]
        result['studio'] = json.loads(probe.stdout)
        path = os.environ.get('AMPHORA_TEST_FEEDBACK_EVIDENCE')
        if path:
            Path(path).write_text(json.dumps({'scope': scope, 'status': 'integrated_baseline_verified',
                'limits': ['Synthetic hypothesis; no scientific-validity claim', 'Browser/correction/distinct-specimen acceptance remain later gates'],
                'records': result}, indent=2) + '\n', encoding='utf-8')
    finally:
        runtime.close()
        scenario.close()
