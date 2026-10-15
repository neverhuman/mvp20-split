"""Standalone numeric capability modes; diagnostics contain no input values."""

import argparse
import json
import re
import sys

from amphora_tool_protocol import ProtocolError, run_worker

from .adapter import MAX_PAYLOAD, NumericWorkerAdapter
from .capabilities import PROFILES, NumericCapability
from .population_workers.capabilities import PROFILES as POPULATION_PROFILES, PopulationCapability
from .population_workers.worker import run_population_worker


def main():
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("compute", "describe", "schema", "worker"):
        command = commands.add_parser(name)
        command.add_argument("--operation", choices=tuple(PROFILES), required=True)
        if name in {"compute", "describe"}:
            command.add_argument("--image-sha256", required=True)
        elif name == "schema":
            command.add_argument("--direction", choices=("input", "output"), required=True)
        else:
            command.add_argument("--config", required=True)
    for name in ("population-describe", "population-schema", "population-worker"):
        command = commands.add_parser(name)
        command.add_argument("--operation", choices=tuple(POPULATION_PROFILES), required=True)
        if name == "population-describe":
            command.add_argument("--image-sha256", required=True)
        elif name == "population-schema":
            command.add_argument("--direction", choices=("input", "output"), required=True)
        else:
            command.add_argument("--config", required=True)
    args = parser.parse_args()
    try:
        if args.command.startswith("population-"):
            capability = PopulationCapability(args.operation)
            if args.command == "population-describe":
                print(capability.descriptor(args.image_sha256).model_dump_json())
            elif args.command == "population-schema":
                sys.stdout.buffer.write(capability.schema_bytes(args.direction))
            else:
                print(json.dumps(run_population_worker(args.config, args.operation)))
            return
        adapter = NumericWorkerAdapter(args.operation)
        if args.command == "describe":
            print(adapter.descriptor(args.image_sha256).model_dump_json())
        elif args.command == "schema":
            sys.stdout.buffer.write(NumericCapability(args.operation).schema_bytes(args.direction))
        elif args.command == "worker":
            print(json.dumps(run_worker(args.config, adapter.descriptor, adapter.execute)))
        else:
            adapter.descriptor(args.image_sha256)
            payload = sys.stdin.buffer.read(MAX_PAYLOAD + 1)
            sys.stdout.buffer.write(adapter.execute(payload))
    except ProtocolError as error:
        if args.command.startswith("population-"):
            reason = str(error)
            if re.fullmatch(r"[A-Za-z0-9_.-]{1,128}", reason) is None:
                reason = "protocol_error"
            print("population_worker_incomplete:" + reason, file=sys.stderr)
        else:
            print("numeric_worker_incomplete", file=sys.stderr)
        raise SystemExit(3) from None
    except (ValueError, OSError, KeyError, TypeError):
        print("invalid_numeric_input_or_configuration", file=sys.stderr)
        raise SystemExit(2) from None


if __name__ == "__main__":
    main()
