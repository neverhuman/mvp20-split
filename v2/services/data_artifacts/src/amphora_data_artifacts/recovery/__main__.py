"""Explicit local operator audit; credentials remain in the existing owner environment."""

import argparse
import json
from contextlib import ExitStack
from pathlib import Path

from ..hosting import Host
from .inventory import CatalogAudit


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--inventory-output', type=Path)
    args = parser.parse_args()
    host = None
    try:
        with ExitStack() as stack:
            # Exclusive outputs make partial/failed audits distinguishable from old success.
            output = stack.enter_context(args.output.open('x', encoding='utf-8'))
            inventory = stack.enter_context(args.inventory_output.open('x', encoding='utf-8')) if args.inventory_output else None
            host = Host.load(args.config)
            result = CatalogAudit(host.uploads.commands.engine, host.storage).run(inventory=inventory)
            output.write(json.dumps(result, sort_keys=True, indent=2) + '\n')
            return 0 if result['status'] == 'verified' else 3
    except Exception:  # noqa: BLE001 - driver/config errors may contain credentials
        print('Data catalog audit incomplete; no restore acceptance granted.')
        return 2
    finally:
        if host is not None:
            host.close()


if __name__ == '__main__':
    raise SystemExit(main())
