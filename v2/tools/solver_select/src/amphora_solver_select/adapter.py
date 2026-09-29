"""Map explicit fixture rejection to the public worker failure vocabulary."""

from amphora_tool_protocol import ToolInputRejected

from .kernel import compute


def execute(payload):
    try:
        return compute(payload)
    except ValueError as error:
        raise ToolInputRejected("invalid_solver_fixture") from error
