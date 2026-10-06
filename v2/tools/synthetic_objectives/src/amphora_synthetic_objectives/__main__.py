"""Standalone synthetic evaluator; no input content appears in diagnostics."""

import argparse
import json
import sys
from pathlib import Path

from amphora_multi_input_worker import run_multi_input_worker
from amphora_tool_protocol import ProtocolError

from .adapter import SyntheticWorkerAdapter
from .metadata import policy_bytes, schema_bytes


def main():
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("compute", "describe"):
        command = commands.add_parser(name)
        command.add_argument("--image-sha256", required=True)
        if name == "compute":
            command.add_argument("--policy-file", required=True)
    commands.add_parser("policy")
    commands.add_parser("schema").add_argument("--kind", choices=("input", "output", "policy"), required=True)
    commands.add_parser("worker").add_argument("--config", required=True)
    args = parser.parse_args()
    try:
        adapter = SyntheticWorkerAdapter()
        if args.command == "policy":
            sys.stdout.buffer.write(policy_bytes())
        elif args.command == "schema":
            sys.stdout.buffer.write(schema_bytes(args.kind))
        elif args.command == "worker":
            print(json.dumps(run_multi_input_worker(args.config, adapter.descriptor, adapter.execute)))
        else:
            release = adapter.descriptor(args.image_sha256)
            if args.command == "describe":
                print(release.model_dump_json())
            else:
                with Path(args.policy_file).open("rb") as stream:
                    policy = stream.read(262145)
                sys.stdout.buffer.write(adapter.offline(sys.stdin.buffer.read(262145), policy))
    except ProtocolError:
        print("synthetic_worker_incomplete", file=sys.stderr)
        raise SystemExit(3) from None
    except (ValueError, OSError, KeyError, TypeError):
        print("invalid_synthetic_input_or_configuration", file=sys.stderr)
        raise SystemExit(2) from None


if __name__ == "__main__":
    main()
