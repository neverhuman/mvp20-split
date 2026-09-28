"""Preserve explicit alphabet/symbol failures without exposing the input sequence."""

from amphora_tool_protocol import ToolInputRejected
from pydantic import ValidationError

from .kernel import compute


def execute(payload):
    try:
        return compute(payload)
    except ValidationError as error:
        raise ToolInputRejected("invalid_sequence_parameters") from error
    except ValueError as error:
        reason = str(error)
        if reason not in {"duplicate_alphabet_symbol", "invalid_sequence_symbol"}:
            reason = "invalid_sequence_parameters"
        raise ToolInputRejected(reason) from error
