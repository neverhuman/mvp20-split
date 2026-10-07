"""Bounded offline computation and one-invocation configured worker CLI."""

import argparse
import json
import sys
from pathlib import Path

from amphora_contracts_search import EvaluationRequest
from amphora_multi_input_worker import run_multi_input_worker
from amphora_tool_protocol import ProtocolError

from .adapter import MAX_BYTES, SyntheticWorkerAdapter
from .domain import PolicyBinding, SyntheticProblem, canonical
from .metadata import descriptor, policy_bytes, schema_bytes, tool_binding


def main(argv=None):
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("policy")
    commands.add_parser("schema").add_argument("--kind", choices=("input", "output", "policy"), required=True)
    commands.add_parser("describe").add_argument("--image-sha256", required=True)
    compute = commands.add_parser("compute")
    compute.add_argument("--image-sha256", required=True)
    compute.add_argument("--policy-file", required=True)
    commands.add_parser("worker").add_argument("--config", required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "policy":
            output = policy_bytes()
        elif args.command == "schema":
            output = schema_bytes(args.kind)
        elif args.command == "describe":
            output = canonical(descriptor(args.image_sha256))
        elif args.command == "worker":
            worker = SyntheticWorkerAdapter()
            result = run_multi_input_worker(args.config, worker.descriptor, worker.execute)
            output = json.dumps(result, sort_keys=True, separators=(",", ":")).encode()
        else:
            body = sys.stdin.buffer.read(MAX_BYTES + 1)
            with Path(args.policy_file).open("rb") as stream:
                policy = stream.read(MAX_BYTES + 1)
            if len(body) + len(policy) > MAX_BYTES:
                raise ValueError("input_too_large")
            request = EvaluationRequest.model_validate_json(body)
            problem = SyntheticProblem(request, tool_binding(args.image_sha256),
                                       PolicyBinding(request.evaluator.constraints, policy))
            output = canonical(problem.evaluate())
        sys.stdout.buffer.write(output)
        return 0
    except (ValueError, OSError, ProtocolError):
        sys.stderr.write("invalid_synthetic_input_or_configuration\n")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
