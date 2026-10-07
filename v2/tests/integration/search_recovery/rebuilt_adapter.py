"""Independent test adapter reconstruction using only documented public exports."""

import argparse
import json
import sys
from importlib.metadata import version
from pathlib import Path

from amphora_contracts_search import ImplementationPin, SearchSpec
from amphora_contracts_search_steps import CollectedEvaluations, SearchStepContext
from amphora_contracts_tools import ReleaseDescriptor
from amphora_evolution_search import BoundCheckpoint, GenerationReducer, InitialPopulation, OriginalSearch, SuccessorPopulation
from amphora_tool_protocol import ProtocolError, ToolInputRejected, run_worker

LIMIT = 262144
INPUTS = {"seed": SearchSpec, "requests": SearchStepContext, "collect": CollectedEvaluations, "vary": SearchStepContext}


class ReconstructedAdapter:
    def __init__(self, operation, reviewed_descriptor):
        if operation not in INPUTS:
            raise ValueError("rebuild_operation")
        descriptor = ReleaseDescriptor.model_validate_json(reviewed_descriptor)
        if descriptor.tool.binding.capability_id != "numeric.search-" + operation or descriptor.tool.binding.release != version("amphora-evolution-search"):
            raise ValueError("rebuild_descriptor")
        self.operation, self.reviewed = operation, descriptor
        self.bound = False

    def descriptor(self, image):
        if image != self.reviewed.tool.binding.image_sha256:
            raise ValueError("rebuild_image")
        self.bound = True
        return self.reviewed

    def execute(self, raw):
        try:
            if not self.bound or type(raw) is not bytes or len(raw) > LIMIT:
                raise ValueError("rebuild_input")
            incoming = INPUTS[self.operation].model_validate_json(raw)
            original = OriginalSearch(incoming if self.operation == "seed" else incoming.original_specification)
            binding = self.reviewed.tool.binding
            expected = ImplementationPin(name="numeric-search", version=binding.release, sha256=binding.image_sha256)
            if expected not in original.record.implementations:
                raise ValueError("rebuild_implementation")
            if self.operation == "seed":
                result = InitialPopulation.generate(original).checkpoint().record
            else:
                context = SearchStepContext(original_specification=incoming.original_specification,
                    checkpoint=incoming.checkpoint, checkpoint_artifact=incoming.checkpoint_artifact)
                bound = BoundCheckpoint.from_context(context)
                if self.operation == "requests":
                    result = bound.request_batch()
                elif self.operation == "collect":
                    result = GenerationReducer(bound).collect(incoming.results).record
                else:
                    result = SuccessorPopulation(bound).create().record
            output = json.dumps(result.model_dump(mode="json"), sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()
            if len(output) > LIMIT:
                raise ValueError("rebuild_output")
            return output
        except (ValueError, TypeError, KeyError, OverflowError):
            raise ToolInputRejected("invalid_numeric_search_step") from None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("compute", "worker"))
    parser.add_argument("--operation", choices=tuple(INPUTS), required=True)
    parser.add_argument("--descriptor", required=True, type=Path)
    parser.add_argument("--config")
    parser.add_argument("--image-sha256")
    args = parser.parse_args()
    try:
        descriptor = args.descriptor.read_bytes()
        if len(descriptor) > 262144:
            raise ValueError("rebuild_descriptor_bound")
        adapter = ReconstructedAdapter(args.operation, descriptor)
        if args.action == "worker":
            print(json.dumps(run_worker(args.config, adapter.descriptor, adapter.execute)))
        else:
            adapter.descriptor(args.image_sha256)
            sys.stdout.buffer.write(adapter.execute(sys.stdin.buffer.read(LIMIT + 1)))
    except ProtocolError:
        print("numeric_worker_incomplete", file=sys.stderr)
        return 3
    except (ValueError, OSError, KeyError, TypeError):
        print("invalid_numeric_input_or_configuration", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
