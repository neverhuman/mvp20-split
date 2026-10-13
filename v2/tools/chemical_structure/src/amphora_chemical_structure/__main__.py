"""Standalone kernel and worker entry point; diagnostics never echo input."""

import argparse
import json
import sys

from amphora_tool_protocol import ProtocolError, run_worker

from .adapter import execute
from .kernel import compute
from .metadata import descriptor, schema_bytes


def main():
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("compute")
    describe = commands.add_parser("describe")
    describe.add_argument("--image-sha256", required=True)
    schema = commands.add_parser("schema")
    schema.add_argument("--kind", choices=("input", "output"), required=True)
    worker = commands.add_parser("worker")
    worker.add_argument("--config", required=True)
    args = parser.parse_args()
    try:
        if args.command == "describe":
            print(descriptor(args.image_sha256).model_dump_json())
        elif args.command == "schema":
            sys.stdout.buffer.write(schema_bytes(args.kind))
        elif args.command == "worker":
            print(json.dumps(run_worker(args.config, descriptor, execute)))
        else:
            payload = sys.stdin.buffer.read(262145)
            if len(payload) > 262144:
                raise ValueError("payload_too_large")
            sys.stdout.buffer.write(compute(payload) + b"\n")
    except ProtocolError:
        print("worker_execution_incomplete", file=sys.stderr)
        raise SystemExit(3) from None
    except (ValueError, OSError, KeyError):
        print("invalid_tool_input_or_configuration", file=sys.stderr)
        raise SystemExit(2) from None


if __name__ == "__main__":
    main()
