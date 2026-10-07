"""Public Artifact materials and isolated owner-local compilation; no peer internals."""

import hashlib
import json
import subprocess
import uuid
from pathlib import Path

from amphora_contracts_planning import checkpoint_followup_draft_schema

from campaign_context_fixture.support import environment
from check_boundaries import ROOT


def write(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')
    return path


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode()


def run_owner(python, arguments, output, env=None):
    result = subprocess.run([str(python), '-I', *map(str, arguments)], env=environment() if env is None else env,
        cwd=output, capture_output=True, timeout=90, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    with (output / 'owner-stages.log').open('ab') as log:
        log.write(result.stdout + result.stderr)
    assert result.returncode == 0, 'Installed owner stage failed; inspect sanitized owner-stage diagnostics'
    return result.stdout


def profiles(python, output):
    run_owner(python, [ROOT / 'services/campaign_runtime/tests/supervision_loop/owners/export_demo.py', 'profiles', output], output)
    return json.loads((output / 'profiles.json').read_bytes())


def publish(owner, scope, body, profile):
    schema = {key: profile[key] for key in ('schema_id', 'version', 'sha256')}
    content = {'sha256': hashlib.sha256(body).hexdigest(), 'size_bytes': len(body), 'media_type': profile['media_type'], 'schema_ref': schema}

    def command(family, payload):
        return {'identity': {'scope': scope, 'actor_id': 'operator', 'command_id': uuid.uuid4().hex, 'command_family': family}, 'payload': payload}

    upload = owner.call('POST', '/v1/uploads', command('artifacts.begin_upload', {'content': content}))
    owner.call('PUT', '/v1/uploads/' + upload['upload_id'] + '/content', body)
    return owner.call('POST', '/v1/artifacts/finalize', command('artifacts.finalize', {'upload_id': upload['upload_id'], 'content': content}))['artifact']


def prepare(data, records, admitted, pythons, output):
    scope = records['scope']
    profile = next(row for row in admitted if row['media_type'] == 'text/plain')
    prompt = run_owner(pythons['planning'], ['-c', 'import sys; from amphora_agent_planning.campaign_packet_profiles import reviewed_instructions; sys.stdout.buffer.write(reviewed_instructions())'], output)
    tokenizer = b'{"algorithm":"utf8_byte_count","format":"planning.fixture-tokenizer.v1","framing":"exact_packet_bytes","model":["deterministic","adversarial-fixture","1"],"unit":"synthetic_byte_token"}\n'
    model = {'provider_id': 'deterministic', 'model_id': 'adversarial-fixture', 'model_revision': '1', 'context_window_tokens': 216384,
        'tokenizer': {'schema_id': 'planning.fixture-byte-tokenizer', 'version': '1', 'sha256': hashlib.sha256(tokenizer).hexdigest()},
        'configuration': publish(data, scope, b'Deterministic acceptance fixture; no scientific judgement.', profile)}
    limits = {'accounting_unit': 'fixture-unit', 'max_attempts': 1, 'max_input_tokens': 200000, 'max_output_tokens': 16384,
              'total_tokens': 216384, 'total_accounting_units': 60}
    common = {'scope': scope, 'model': model, 'prompt': publish(data, scope, prompt, profile),
              'allowed_actions': ['abstain', 'request_evidence', 'propose_campaign'], 'limits': limits}
    output_schema = checkpoint_followup_draft_schema().model_dump(mode='json')
    template = dict(common, profile='planning-supervision-budget-template.v1', output_schema=output_schema, per_attempt_accounting_units=60)
    template_raw = canonical(template)
    (output / 'template.json').write_bytes(template_raw)
    template_ref = publish(data, scope, template_raw, next(row for row in admitted if row['schema_id'] == 'demo.budget-template'))
    write(output / 'recipe-input.json', dict(common, profile='runtime-supervision-followup-recipe.v1', output_schema=output_schema,
        objective=publish(data, scope, b'Target a retained criterion in a future synthetic campaign, preserving uncertainty.', profile),
        budget_policy=template_ref, entries=[{'artifact': records['artifact'], 'role': 'source', 'required': True}], omissions=[]))
    write(output / 'followup-seed.json', {'profile': 'planning-followup-seed.v1', 'budget_template': template_ref,
                                        'criteria': records['criteria'], 'focus_artifact': None})
    run_owner(pythons['runtime'], [ROOT / 'services/campaign_runtime/tests/supervision_followup/export_acceptance.py', output], output)
    return json.loads((output / 'compiled.json').read_bytes()), template_ref
