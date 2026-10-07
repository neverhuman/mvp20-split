"""Closed conservative checkpoint framing profile, not an actual token counter."""

import hashlib
from dataclasses import dataclass
from functools import cache

from amphora_contracts_core import SchemaRef
from amphora_contracts_planning import ModelBinding, checkpoint_draft_schema

from ..campaign_context.records import canonical
from ..context.policy import require
from ..openai_provider.pricing import MODEL


@cache
def checkpoint_tokenizer_reference(version='1'):
    require(version in {'1', '2'}, 'checkpoint_input_profile')
    descriptor = canonical({'format': 'planning.checkpoint-openai-input-bound.v' + version,
        'algorithm': 'serialized_responses_utf8_bytes_plus_1024', 'model': MODEL,
        'envelope': 'checkpoint-responses-v' + version, 'output_schema': checkpoint_draft_schema().model_dump(mode='json'),
        'unit': 'conservative_input_token_bound', 'authorization': 'none'})
    name = 'planning.checkpoint-openai-input-bound' + ('' if version == '1' else '.v2')
    return SchemaRef(schema_id=name, version='1',
                     sha256=hashlib.sha256(descriptor).hexdigest())


@dataclass(frozen=True)
class CheckpointMeasurement:
    sha256: str
    size_bytes: int
    input_tokens: int
    envelope_sha256: str
    envelope_bytes: int


@dataclass(frozen=True)
class CheckpointInputBound:
    reference: SchemaRef

    @classmethod
    def bind(cls, supplied):
        model = ModelBinding.model_validate(supplied.model_dump(mode='python', warnings=False))
        require((model.provider_id, model.model_id, model.model_revision) == ('openai', MODEL, MODEL),
                'checkpoint_input_model')
        require(model.tokenizer in (checkpoint_tokenizer_reference('1'), checkpoint_tokenizer_reference('2')),
                'checkpoint_input_profile')
        return cls(model.tokenizer)

    @property
    def envelope_version(self):
        require(self.reference in (checkpoint_tokenizer_reference('1'), checkpoint_tokenizer_reference('2')),
                'checkpoint_input_profile')
        return '1' if self.reference == checkpoint_tokenizer_reference('1') else '2'

    def measure(self, request, raw):
        from .envelope import CheckpointEnvelope

        require(self == self.bind(request.document().context.model), 'checkpoint_input_binding')
        envelope = CheckpointEnvelope.bind(request, raw)
        return CheckpointMeasurement(envelope.packet_sha256, envelope.packet_bytes,
            envelope.input_bound, envelope.sha256, len(envelope.body))
