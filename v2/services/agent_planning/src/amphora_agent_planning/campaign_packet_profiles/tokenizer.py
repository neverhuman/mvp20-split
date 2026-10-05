"""Closed deterministic byte-count fixture; deliberately not a live-model tokenizer."""

import hashlib
import json
from dataclasses import dataclass

from amphora_contracts_core import SchemaRef
from amphora_contracts_planning import ModelBinding

from ..context.policy import require

MODEL = ('deterministic', 'adversarial-fixture', '1')
DESCRIPTOR = b'{"algorithm":"utf8_byte_count","format":"planning.fixture-tokenizer.v1","framing":"exact_packet_bytes","model":["deterministic","adversarial-fixture","1"],"unit":"synthetic_byte_token"}\n'


def fixture_tokenizer_reference():
    return SchemaRef(schema_id='planning.fixture-byte-tokenizer', version='1', sha256=hashlib.sha256(DESCRIPTOR).hexdigest())


@dataclass(frozen=True)
class PacketMeasurement:
    sha256: str
    size_bytes: int
    input_tokens: int


@dataclass(frozen=True)
class FixturePacketTokenizer:
    reference: SchemaRef

    @classmethod
    def bind(cls, supplied):
        model = ModelBinding.model_validate(supplied.model_dump(mode='python', warnings=False))
        require((model.provider_id, model.model_id, model.model_revision) == MODEL, 'campaign_tokenizer_model')
        require(model.tokenizer == fixture_tokenizer_reference(), 'campaign_tokenizer_profile')
        return cls(model.tokenizer)

    def measure(self, raw):
        require(self.reference == fixture_tokenizer_reference(), 'campaign_tokenizer_profile')
        require(type(raw) is bytes and 0 < len(raw) <= 8388608, 'campaign_packet_size')
        try:
            raw.decode('utf-8')
        except UnicodeDecodeError as error:
            raise ValueError('campaign_packet_utf8') from error
        return PacketMeasurement(hashlib.sha256(raw).hexdigest(), len(raw), len(raw))

    def descriptor(self):
        return json.loads(DESCRIPTOR)
