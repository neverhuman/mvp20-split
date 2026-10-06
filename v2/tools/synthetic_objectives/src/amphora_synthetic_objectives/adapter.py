"""Image-bound adapter for the existing pure tool worker protocol."""

import json

from amphora_contracts_search import EvaluationRequest
from amphora_multi_input_worker import InputBundle
from amphora_tool_protocol import ToolInputRejected

from .kernel import PolicyBinding, SyntheticProblem, require
from .metadata import descriptor, schema_ref


class SyntheticWorkerAdapter:
    def __init__(self):
        self.binding = None

    def descriptor(self, image_sha256):
        release = descriptor(image_sha256)
        require(self.binding is None or self.binding == release.tool.binding, "synthetic_worker_image_changed")
        self.binding = release.tool.binding
        return release

    def _result(self, request, policy):
        require(self.binding is not None, "synthetic_worker_unbound")
        result = SyntheticProblem(request, self.binding, policy).evaluate()
        raw = json.dumps(result.model_dump(mode="json"), sort_keys=True, separators=(",", ":"),
                         ensure_ascii=False, allow_nan=False).encode()
        require(len(raw) <= 262144, "synthetic_output_bound")
        return raw

    def execute(self, inputs):
        try:
            require(type(inputs) is InputBundle and {i.port for i in inputs.inputs} == {"parameters", "policy"}, "synthetic_input_ports")
            request = EvaluationRequest.model_validate_json(inputs["parameters"].data)
            reference = inputs["parameters"].artifact
            require(reference.scope == request.scope and reference.schema_ref == schema_ref("input")
                    and reference.media_type == "application/json", "synthetic_request_binding")
            return self._result(request, PolicyBinding(inputs["policy"].artifact, inputs["policy"].data))
        except (ValueError, TypeError, KeyError, OverflowError):
            raise ToolInputRejected("invalid_synthetic_objective_input") from None

    def offline(self, payload, declared_policy_bytes):
        """CLI arithmetic check only; no claim that declared Artifacts exist or are authorized."""
        try:
            require(type(payload) is bytes and len(payload) <= 262144, "synthetic_input_bound")
            request = EvaluationRequest.model_validate_json(payload)
            return self._result(request, PolicyBinding(request.evaluator.constraints, declared_policy_bytes))
        except (ValueError, TypeError, KeyError, OverflowError):
            raise ToolInputRejected("invalid_synthetic_objective_input") from None
