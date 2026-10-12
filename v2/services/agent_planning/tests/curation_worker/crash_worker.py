"""Test-only process barrier after durable issuance; never a production provider."""
import json
import os
from pathlib import Path
import sys

from amphora_agent_planning.curation_budget import CurationAllowance
from amphora_agent_planning.curation_worker.hosting import CurationHost


def main():
    path = Path(sys.argv[1])
    probe = json.loads(path.with_suffix('.probe.json').read_bytes())
    class Data:
        def artifact(self, reference, budget):
            budget.start()
            return reference
        def content(self, reference, budget):
            budget.start()
            body = bytes.fromhex(probe['bodies'][reference.artifact_id])
            budget.consume(len(body))
            return body
    class Crash:
        def supports(self, model): return True
        def validate_policy(self, policy): CurationAllowance.validate_policy(policy)
        def reply(self, binding, packet, *, deadline_unix_ms):
            with path.with_suffix('.issued.json').open('x', encoding='utf-8') as stream:
                json.dump({'pid': os.getpid(), 'ordinal': binding.ordinal, 'deadline_unix_ms': deadline_unix_ms}, stream)
            os._exit(73)
    host = CurationHost.load(path)
    try:
        worker = host.poller.worker
        worker.executor.data, worker.executor.provider, worker.executor.timeout = Data(), Crash(), 2
        host.poller.tick(host.principal)
        raise RuntimeError('Issuance barrier was not reached')
    finally:
        host.close()


if __name__ == '__main__':
    try:
        main()
    except Exception:
        print('Curation process probe failed', file=sys.stderr)
        sys.exit(1)
