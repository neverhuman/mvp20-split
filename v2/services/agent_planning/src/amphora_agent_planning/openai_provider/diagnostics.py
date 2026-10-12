"""Bounded response classification; no remote prose, credentials or acceptance authority."""
import hashlib
from dataclasses import dataclass, asdict


@dataclass(frozen=True)
class ResponseShape:
    message_items: int
    reasoning_items: int
    other_items: int
    output_text_blocks: int
    output_text_bytes: int
    usage_present: bool
    input_tokens_present: bool
    output_tokens_present: bool

    @classmethod
    def capture(cls, value):
        output = value.get('output')
        items = output if type(output) is list else []
        messages = sum(type(row) is dict and row.get('type') == 'message' for row in items)
        reasoning = sum(type(row) is dict and row.get('type') == 'reasoning' for row in items)
        texts = [block['text'] for row in items if type(row) is dict
                 for block in (row.get('content') if type(row.get('content')) is list else [])
                 if type(block) is dict and block.get('type') == 'output_text' and type(block.get('text')) is str]
        usage = value.get('usage')
        return cls(messages, reasoning, len(items) - messages - reasoning, len(texts),
                   sum(len(text.encode('utf-8', errors='replace')) for text in texts),
                   type(usage) is dict, type(usage) is dict and 'input_tokens' in usage,
                   type(usage) is dict and 'output_tokens' in usage)


@dataclass(frozen=True)
class ResponseDiagnostic:
    response_sha256: str
    response_bytes: int
    status: str
    error_code: str | None
    incomplete_reason: str | None
    refused: bool
    shape: ResponseShape

    @classmethod
    def capture(cls, raw, value):
        statuses = {'completed', 'failed', 'incomplete', 'queued', 'in_progress', 'cancelled'}
        codes = {'server_error', 'rate_limit_exceeded', 'invalid_prompt', 'invalid_json_schema',
                 'invalid_request_error', 'schema_validation_error', 'insufficient_quota'}
        reasons = {'max_output_tokens', 'content_filter'}
        error = value.get('error')
        detail = value.get('incomplete_details')
        code = error.get('code') if type(error) is dict else None
        reason = detail.get('reason') if type(detail) is dict else None
        status = value.get('status')
        def selected(item, accepted):
            return item if type(item) is str and item in accepted else 'unclassified'
        output = value.get('output')
        refused = any(type(block) is dict and block.get('type') == 'refusal'
            for row in (output if type(output) is list else []) if type(row) is dict
            for block in (row.get('content') if type(row.get('content')) is list else []))
        return cls(hashlib.sha256(raw).hexdigest(), len(raw), selected(status, statuses),
                   None if error is None else selected(code, codes),
                   None if detail is None else selected(reason, reasons), refused,
                   ResponseShape.capture(value))

    def document(self):
        return asdict(self)
