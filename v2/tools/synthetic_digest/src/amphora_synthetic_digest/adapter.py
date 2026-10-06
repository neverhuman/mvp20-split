from amphora_tool_protocol import ToolInputRejected

from .capability import DigestCapability
from .domain import DigestEvaluation, MAX_PAYLOAD


class DigestWorkerAdapter:
    def __init__(self):
        self.binding = None

    def descriptor(self, image_sha256):
        descriptor = DigestCapability().descriptor(image_sha256)
        if self.binding is not None and self.binding != descriptor.tool.binding:
            raise ValueError('worker_image_changed')
        self.binding = descriptor.tool.binding
        return descriptor

    def execute(self, payload):
        try:
            if self.binding is None:
                raise ValueError('worker_not_bound')
            return DigestEvaluation.parse(payload, self.binding).output()
        except (ValueError, TypeError, KeyError, OverflowError, RecursionError):
            raise ToolInputRejected('invalid_synthetic_digest_input') from None
