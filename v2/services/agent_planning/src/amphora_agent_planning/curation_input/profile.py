"""Conservative complete-envelope input bound for the reviewed campaign model."""
import hashlib
from dataclasses import dataclass
from functools import cache

from amphora_contracts_campaign_curation import campaign_curation_draft_schema
from amphora_contracts_core import SchemaRef
from amphora_contracts_planning import ModelBinding

from ..campaign_context.records import canonical
from ..context.policy import require
from ..openai_provider.pricing import MODEL


@cache
def curation_tokenizer_reference():
    descriptor = canonical({'format': 'planning.curation-openai-input-bound.v1',
        'algorithm': 'serialized_responses_utf8_bytes_plus_1024', 'model': MODEL,
        'envelope': 'curation-responses-v1',
        'output_schema': campaign_curation_draft_schema().model_dump(mode='json'),
        'unit': 'conservative_input_token_bound', 'authorization': 'none'})
    return SchemaRef(schema_id='planning.curation-openai-input-bound', version='1',
                     sha256=hashlib.sha256(descriptor).hexdigest())


@dataclass(frozen=True)
class CurationMeasurement:
    sha256: str
    size_bytes: int
    input_tokens: int
    envelope_sha256: str
    envelope_bytes: int


@dataclass(frozen=True)
class CurationInputBound:
    reference: SchemaRef

    @classmethod
    def bind(cls, supplied):
        model = ModelBinding.model_validate(supplied.model_dump(mode='python', warnings=False))
        require((model.provider_id, model.model_id, model.model_revision) == ('openai', MODEL, MODEL),
                'curation_input_model')
        require(model.tokenizer == curation_tokenizer_reference(), 'curation_input_profile')
        return cls(model.tokenizer)

    def measure(self, request, raw):
        from .envelope import CurationEnvelope
        require(self == self.bind(request.document().context.model), 'curation_input_binding')
        envelope = CurationEnvelope.bind(request, raw)
        return CurationMeasurement(envelope.packet_sha256, envelope.packet_bytes,
            envelope.input_bound, envelope.sha256, len(envelope.body))
