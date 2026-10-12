"""One exact curation through the installed production worker; no substitute provider."""
import importlib.util
import json
import re
import sys
import time
from dataclasses import asdict
from pathlib import Path

from amphora_agent_planning.curation_worker.hosting import CurationHost


def retain(path, raw):
    if path.exists():
        assert path.read_bytes() == raw, 'Original qualification bytes changed'
    else:
        path.write_bytes(raw)


def export(host, curation_id, output):
    worker, principal = host.poller.worker, host.principal
    recovered = worker.inputs.recover(principal, curation_id)
    if recovered is None or recovered.frozen is None:
        return
    frozen = recovered.frozen
    retain(output / 'original-envelope.json', frozen.envelope.body)
    retain(output / 'original-packet.json', frozen.preparation.packet.canonical)
    limits = frozen.preparation.packet.request.document().context.limits
    assert frozen.envelope.input_bound <= limits.max_input_tokens <= 262144
    model = frozen.preparation.packet.request.document().context.model
    maximum = 16384 if model.tokenizer.schema_id == 'planning.curation-openai-input-bound.v5' else 8192
    assert limits.max_output_tokens <= maximum and limits.max_attempts == 1
    outcome = worker.results.read(principal, curation_id)
    if outcome is not None:
        observed = outcome.attempt.observation
        retain(output / 'original-output.json', observed.capture.content)
        retain(output / 'original-observation.json', observed.canonical)
        retain(output / 'provider-accounting.json', outcome.provider.model_dump_json().encode())
        provider = worker.executor.provider
        if provider is not None and provider.last_exchange is not None:
            retain(output / "transport-exchange.json", json.dumps(provider.last_exchange, sort_keys=True).encode())
        if provider is not None and provider.last_response is not None:
            retain(output / 'response-diagnostic.json', json.dumps(provider.last_response.document(), sort_keys=True).encode())
        if provider is not None and provider.last_transport_failure is not None:
            retain(output / 'transport-diagnostic.json', json.dumps(provider.last_transport_failure, sort_keys=True).encode())


def main():
    assert all(importlib.util.find_spec(name) is None for name in (
        'amphora_campaign_runtime', 'amphora_data_artifacts', 'amphora_deployment',
        'amphora_research', 'amphora_knowledge', 'amphora_capability_registry'))
    config, curation_id, output = Path(sys.argv[1]), sys.argv[2], Path(sys.argv[3])
    host = CurationHost.load(config, enable_provider=True)
    try:
        for _ in range(20):
            started = time.perf_counter()
            turn = host.poller.worker.tick(host.principal, curation_id, 'live-qualification-worker')
            with (output / 'worker-turns.jsonl').open('a', encoding='utf-8') as stream:
                stream.write(json.dumps(asdict(turn) | {'elapsed_seconds': time.perf_counter() - started}) + '\n')
            # After preparation this retains the exact fitted envelope before the next
            # production tick can issue it. Export never changes the production records.
            export(host, curation_id, output)
            if turn.status == 'terminal':
                return
            time.sleep(.25)
        raise RuntimeError('live_qualification_turn_limit')
    finally:
        host.close()


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        # No traceback/SQL URL, credential, prompt or remote free-form error escapes.
        reason = str(error)
        print(reason if re.fullmatch(r'[a-z_]{1,100}', reason) else type(error).__name__, file=sys.stderr)
        raise SystemExit(2)
