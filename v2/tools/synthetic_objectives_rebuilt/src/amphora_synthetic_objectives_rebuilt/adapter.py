"""Image-bound pure compute adapter; public SDK owns transport and leases."""

from amphora_contracts_search import EvaluationRequest
from amphora_tool_protocol import ToolInputRejected

from .domain import PolicyBinding, SyntheticProblem, canonical
from .metadata import descriptor

MAX_BYTES = 262144


class SyntheticWorkerAdapter:
    def __init__(self):
        self.binding = None

    def descriptor(self, image_sha256):
        release = descriptor(image_sha256)
        if self.binding is not None and self.binding != release.tool.binding:
            raise ValueError("synthetic_worker_image_changed")
        self.binding = release.tool.binding
        return release

    def execute(self, bundle):
        try:
            if (self.binding is None or len(bundle.inputs) != 2
                    or {item.port for item in bundle.inputs} != {"parameters", "policy"}
                    or sum(len(item.data) for item in bundle.inputs) > MAX_BYTES):
                raise ValueError("invalid_bundle")
            request = EvaluationRequest.model_validate_json(bundle["parameters"].data)
            policy = PolicyBinding(bundle["policy"].artifact, bundle["policy"].data)
            return canonical(SyntheticProblem(request, self.binding, policy).evaluate())
        except (ValueError, KeyError) as error:
            raise ToolInputRejected("invalid_synthetic_objective_input") from error
