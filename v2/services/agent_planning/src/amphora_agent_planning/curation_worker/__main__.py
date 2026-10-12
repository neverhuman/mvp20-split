"""Bounded curation process; check never claims work or loads the provider key."""
import argparse
import json
import signal
import sys
from threading import Event

from .hosting import CurationHost


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['check', 'run'])
    parser.add_argument('--config', required=True)
    parser.add_argument('--seconds', type=float, default=20)
    parser.add_argument('--interval', type=float, default=1)
    args = parser.parse_args()
    host, stop, handlers = None, Event(), {}
    try:
        for name in ('SIGINT', 'SIGTERM', 'SIGBREAK'):
            number = getattr(signal, name, None)
            if number is not None:
                handlers[number] = signal.signal(number, lambda *_: stop.set())
        host = CurationHost.load(args.config, enable_provider=args.action == 'run')
        result = {'status': 'ready', 'mode': 'curation_worker', 'provider_checked': False} if args.action == 'check' else (
            host.poller.sweep(host.principal, seconds=args.seconds, interval=args.interval, stop=stop))
        print(json.dumps(result))
        return 0
    except Exception:  # Do not expose SQL, peer credentials, human intent or model bytes.
        print('Planning curation configuration or operation failed; retained history remains authoritative.', file=sys.stderr)
        return 2
    finally:
        for number, handler in handlers.items():
            signal.signal(number, handler)
        if host is not None:
            host.close()


if __name__ == '__main__':
    raise SystemExit(main())
