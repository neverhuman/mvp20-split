"""Bounded worker mapping; Runtime alone grants and accepts the invocation."""

from amphora_contracts_candidate_spaces import PolymerMoveRequest
from amphora_tool_protocol import ToolInputRejected

from .capability import SpaceCapability
from .domain import PolymerSpace
from .profile import canonical

MAX_PAYLOAD = 262144


class SpaceWorkerAdapter:
    def __init__(self):
        self.capability = SpaceCapability()
        self.binding = None

    def descriptor(self, image_sha256):
        descriptor = self.capability.descriptor(image_sha256)
        binding = descriptor.tool.binding
        if self.binding is not None and self.binding != binding:
            raise ValueError("worker_image_changed")
        self.binding = binding
        return descriptor

    def execute(self, payload):
        try:
            if (
                self.binding is None
                or type(payload) is not bytes
                or len(payload) > MAX_PAYLOAD
            ):
                raise ValueError("unbound_or_invalid_payload")
            request = PolymerMoveRequest.model_validate_json(payload)
            result = PolymerSpace(request.source).apply(request)
            output = canonical(result)
            if len(output) > MAX_PAYLOAD:
                raise ValueError("output_capacity")
            return output
        except (ValueError, TypeError, KeyError, OverflowError):
            raise ToolInputRejected("invalid_polymer_space_move") from None
