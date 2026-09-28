"""Map tool-local validation into an explicit execution failure vocabulary."""

from amphora_tool_protocol import ToolInputRejected

from .kernel import compute


def execute(payload):
    try:
        return compute(payload)
    except ValueError as error:
        raise ToolInputRejected("invalid_numeric_parameters") from error
