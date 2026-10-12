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
def curation_tokenizer_reference(version='1'):
    require(version in {'1', '2', '3', '4', '5'}, 'curation_input_profile')
    value = {'format': 'planning.curation-openai-input-bound.v' + version,
        'algorithm': 'serialized_responses_utf8_bytes_plus_1024', 'model': MODEL,
        'envelope': 'curation-responses-v' + version,
        'output_schema': campaign_curation_draft_schema().model_dump(mode='json'),
        'unit': 'conservative_input_token_bound', 'authorization': 'none'}
    if version in {'3', '4', '5'}:
        from .structured import GenerationSchema
        value['generation_schema_sha256'] = GenerationSchema.reviewed().sha256
    if version in {'4', '5'}:
        value['reasoning_effort'] = 'none'
    if version == '5':
        value['maximum_output_tokens'] = 16384
    descriptor = canonical(value)
    name = 'planning.curation-openai-input-bound' + ('' if version == '1' else '.v' + version)
    return SchemaRef(schema_id=name, version='1',
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
        require(model.tokenizer in (curation_tokenizer_reference('1'), curation_tokenizer_reference('2'), curation_tokenizer_reference('3'), curation_tokenizer_reference('4'), curation_tokenizer_reference('5')), 'curation_input_profile')
        return cls(model.tokenizer)

    @property
    def envelope_version(self):
        require(self.reference in (curation_tokenizer_reference('1'), curation_tokenizer_reference('2'), curation_tokenizer_reference('3'), curation_tokenizer_reference('4'), curation_tokenizer_reference('5')), 'curation_input_profile')
        return next(version for version in ('1', '2', '3', '4', '5') if self.reference == curation_tokenizer_reference(version))

    def measure(self, request, raw):
        from .envelope import CurationEnvelope
        require(self == self.bind(request.document().context.model), 'curation_input_binding')
        envelope = CurationEnvelope.bind(request, raw)
        return CurationMeasurement(envelope.packet_sha256, envelope.packet_bytes,
            envelope.input_bound, envelope.sha256, len(envelope.body))
