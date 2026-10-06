"""Explicit bounded checkpoint worker; separate from API hosting and graph advancement."""

import argparse
import json
import sys

from .configuration import CheckpointHost


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['check', 'run'])
    parser.add_argument('--config', required=True)
    parser.add_argument('--seconds', type=float, default=20)
    parser.add_argument('--interval', type=float, default=1)
    args = parser.parse_args()
    host = None
    try:
        host = CheckpointHost.load(args.config)
        result = {'status': 'ready', 'mode': 'checkpoint_worker'} if args.action == 'check' else host.poller.sweep(
            host.principal, seconds=args.seconds, interval=args.interval)
        print(json.dumps(result))
        return 0
    except Exception:  # noqa: BLE001 - CLI boundary must not print SQL parameters or credentials.
        print('Checkpoint worker configuration or operation failed; durable state remains authoritative.', file=sys.stderr)
        return 2
    finally:
        if host is not None:
            host.close()


if __name__ == '__main__':
    raise SystemExit(main())
