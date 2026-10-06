"""Exact selected synthetic Artifact bytes; no arbitrary URI/content retrieval."""
import hashlib
import json
from dataclasses import dataclass

from amphora_contracts_core import SchemaRef

from ..context.policy import require
from .format import response_format
from .pricing import MODEL, OpenAIPrice

DESCRIPTOR = b'{"format":"planning.openai-input-bound.v1","algorithm":"serialized_utf8_bytes_plus_1024","model":"gpt-5.4-mini-2026-03-17","purpose":"conservative_reservation_not_actual_tokenizer"}'

def tokenizer_reference():
    return SchemaRef(schema_id="planning.openai-input-bound", version="1", sha256=hashlib.sha256(DESCRIPTOR).hexdigest())

@dataclass(frozen=True)
class PreparedInput:
    request_sha256: str
    body: bytes
    reservation: int
    @classmethod
    def bind(cls, attempt, content, *, revision="openai-responses-synthetic-v1"):
        require(revision in {"openai-responses-synthetic-v1", "openai-responses-synthetic-v2", "openai-responses-synthetic-v3"}, "openai_transport_revision")
        request = attempt.request.document()
        context = request.context
        require((context.model.provider_id,context.model.model_id,context.model.model_revision)==("openai",MODEL,MODEL), "openai_model_binding")
        require(context.model.tokenizer == tokenizer_reference(), "openai_input_bound_profile")
        def body(ref):
            value = content(ref)
            require(type(value) is bytes and len(value) == ref.size_bytes and hashlib.sha256(value).hexdigest() == ref.sha256, "openai_artifact_binding")
            return value.decode("utf-8")
        instructions = body(context.prompt)
        # Every transmitted body comes from an explicitly selected scoped Artifact.
        artifacts = [context.objective,context.policy,context.model.configuration,*(row.artifact for row in context.entries)]
        selected = [{"artifact": ref.model_dump(mode="json"), "text": body(ref)} for ref in artifacts]
        envelope = {"request":request.model_dump(mode="json"),"selected_artifacts":selected}
        value = {"model":MODEL,"store":False,"stream":False,"service_tier":"default",
                 "reasoning":{"effort":"low"},"max_output_tokens":context.limits.max_output_tokens,
                 "instructions":instructions,"input":[{"role":"user","content":("Return JSON only.\n" if revision != "openai-responses-synthetic-v1" else "") + json.dumps(envelope,ensure_ascii=False)}],
                 "text":{"format": response_format(context.output_schema) if revision == "openai-responses-synthetic-v3" else {"type":"json_object"}}}
        raw=json.dumps(value,ensure_ascii=False,separators=(",",":")).encode("utf-8")
        require(len(raw)+1024 <= context.limits.max_input_tokens, "openai_input_reservation_exceeded")
        return cls(attempt.request.sha256,raw,OpenAIPrice().reservation(context.limits, input_limit=32768 if revision == "openai-responses-synthetic-v3" else 16384))
