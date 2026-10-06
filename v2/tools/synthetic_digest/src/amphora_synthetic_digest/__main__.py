"""One-shot compute/worker; safe diagnostics and explicit capability discovery."""

import argparse
import json
import sys

from amphora_tool_protocol import ProtocolError, run_worker

from .adapter import MAX_PAYLOAD, DigestWorkerAdapter
from .capability import DigestCapability
from .profile import METHOD, APPLICABILITY, UNCERTAINTY


def main():
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("compute", "describe", "schema", "profiles", "worker"):
        command = commands.add_parser(name)
        if name in {"compute", "describe"}:
            command.add_argument("--image-sha256", required=True)
        elif name == "schema":
            command.add_argument(
                "--direction", choices=("input", "output"), required=True
            )
        elif name == "worker":
            command.add_argument("--config", required=True)
    args = parser.parse_args()
    try:
        adapter = DigestWorkerAdapter()
        if args.command == "describe":
            print(adapter.descriptor(args.image_sha256).model_dump_json())
        elif args.command == "schema":
            sys.stdout.buffer.write(DigestCapability().schema_bytes(args.direction))
        elif args.command == "profiles":
            print(
                json.dumps(
                    {
                        "method": METHOD.model_dump(mode="json"),
                        "applicability": APPLICABILITY.model_dump(mode="json"),
                        "uncertainty": UNCERTAINTY.model_dump(mode="json"),
                    }
                )
            )
        elif args.command == "worker":
            print(
                json.dumps(run_worker(args.config, adapter.descriptor, adapter.execute))
            )
        else:
            adapter.descriptor(args.image_sha256)
            sys.stdout.buffer.write(
                adapter.execute(sys.stdin.buffer.read(MAX_PAYLOAD + 1))
            )
    except ProtocolError:
        print("synthetic_digest_worker_incomplete", file=sys.stderr)
        raise SystemExit(3) from None
    except (ValueError, OSError, KeyError, TypeError):
        print("invalid_synthetic_digest_input_or_configuration", file=sys.stderr)
        raise SystemExit(2) from None


if __name__ == "__main__":
    main()
