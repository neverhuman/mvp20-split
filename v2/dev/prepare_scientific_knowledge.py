"""Prepare or publish a scoped, source-backed illustrative Knowledge graph."""
import argparse
import hashlib
import json
import uuid
from pathlib import Path
from amphora_deployment.credentials import CredentialVault
from amphora_deployment.lifecycle.routes import Routes
from amphora_deployment.persistence.state import LocalState
from local_numeric_configuration import write
from local_records_controller import RecordsController
from verify_local_owner_records import configure
from scientific_execution.knowledge_records import ScientificKnowledge


def run(args):
    out = args.output.absolute()
    routes = Routes.load(args.root)
    fixture = json.loads((Path(__file__).parents[1] / 'services/knowledge/tests/fixtures/initial.json').read_bytes())
    if not args.publish:
        out.mkdir(parents=True, exist_ok=False)
        scope = {'tenant_id': 'internal', 'project_id': 'knowledge-demo-' + uuid.uuid4().hex}
        schema = configure(out, args.source_manifest, scope, routes, fixture)
        schema = {'schema_id': 'demo.authored-text', 'version': '1',
            'sha256': hashlib.sha256(b'{"type":"string"}').hexdigest()}
        configuration = json.loads((out / 'artifact.json').read_bytes())
        configuration['profiles'] = [{'media_type': 'text/plain', **schema}]
        write(out / 'artifact.json', configuration)
        write(out / 'prepared.json', {'scope': scope, 'schema': schema})
        print('Knowledge owner configurations prepared; no processes or records changed', flush=True)
        return
    prepared = json.loads((out / 'prepared.json').read_bytes())
    state = LocalState.snapshot(args.root)
    tokens = CredentialVault(args.root / 'credentials.dpapi', state['deployment_id']).load().environment(
        ['ARTIFACT_OPERATOR_TOKEN', 'KNOWLEDGE_OPERATOR_TOKEN', 'RESEARCH_OPERATOR_TOKEN'])
    controller = RecordsController(args.root, out, routes)
    try:
        controller.start()
        ScientificKnowledge(controller, tokens, prepared['scope'], out).create(fixture, prepared['schema'])
        write(out / 'drain.json', controller.drain())
        print('Sourced Knowledge graph published and read back; owners drained', flush=True)
    finally:
        controller.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ('root', 'output', 'source-manifest'):
        parser.add_argument('--' + key, type=Path, required=True)
    parser.add_argument('--publish', action='store_true')
    run(parser.parse_args())
