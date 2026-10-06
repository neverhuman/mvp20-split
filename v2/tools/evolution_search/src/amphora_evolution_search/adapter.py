"""Bounded pure worker adapter; actual image binding comes from the configured SDK."""

from amphora_contracts_search import ImplementationPin
from amphora_contracts_search_steps import SearchStepContext
from amphora_tool_protocol import ToolInputRejected

from .capabilities import NumericCapability
from .generation import SuccessorPopulation
from .ranking import require
from .reduction import GenerationReducer
from .seeding import InitialPopulation
from .specification import OriginalSearch, canonical_bytes
from .step_context import BoundCheckpoint

MAX_PAYLOAD = 262144


class NumericWorkerAdapter:
    def __init__(self, operation):
        self.capability = NumericCapability(operation)
        self.implementation = None

    def descriptor(self, image_sha256):
        descriptor = self.capability.descriptor(image_sha256)
        pin = ImplementationPin(name="numeric-search", version=self.capability.release, sha256=image_sha256)
        require(self.implementation is None or self.implementation == pin, "worker_image_changed")
        self.implementation = pin
        return descriptor

    def execute(self, payload):
        try:
            require(type(payload) is bytes and len(payload) <= MAX_PAYLOAD, "numeric_payload_bound")
            require(self.implementation is not None, "numeric_implementation_unbound")
            record = self.capability.input_model.model_validate_json(payload)
            original = OriginalSearch(record if self.capability.operation == "seed" else record.original_specification)
            require(self.implementation in original.record.implementations, "numeric_implementation_mismatch")
            if self.capability.operation == "seed":
                result = InitialPopulation.generate(original).checkpoint().record
            else:
                context = SearchStepContext(original_specification=record.original_specification,
                                            checkpoint=record.checkpoint, checkpoint_artifact=record.checkpoint_artifact)
                bound = BoundCheckpoint.from_context(context)
                if self.capability.operation == "requests":
                    result = bound.request_batch()
                elif self.capability.operation == "vary":
                    result = SuccessorPopulation(bound).create().record
                else:
                    result = GenerationReducer(bound).collect(record.results).record
            output = canonical_bytes(result)
            require(len(output) <= MAX_PAYLOAD, "numeric_payload_bound")
            return output
        except (ValueError, TypeError, KeyError, OverflowError):
            raise ToolInputRejected("invalid_numeric_search_step") from None
