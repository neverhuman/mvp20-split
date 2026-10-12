"""Fixed-scope, bounded one-call transport for the exact retained campaign envelope."""
import math
import time

from amphora_contracts_core import Scope

from ..curation_budget import CurationAllowance
from ..curation_input import CurationEnvelope, CurationInputBound
from ..context.policy import require
from ..openai_provider.adapter import OpenAIProvider
from ..openai_provider.http import OpenAIHTTP
from ..providers.port import ProviderUnavailable


class CurationOpenAI:
    revision = 'curation-responses-v1'

    def __init__(self, api_key, *, scope, egress, timeout_seconds=60, transport_factory=OpenAIHTTP):
        require(egress == 'approved_synthetic_engineering_only', 'curation_egress_required')
        require(type(timeout_seconds) is int and 1 <= timeout_seconds <= 60, 'curation_provider_timeout')
        self.scope = Scope.model_validate(scope.model_dump(mode='python', warnings=False))
        transport_factory(api_key, timeout_seconds=timeout_seconds, maximum_body_bytes=262144)
        self._key, self.timeout, self._factory = api_key, timeout_seconds, transport_factory
        self.last_response = None
        self.last_transport_failure = None
        self.last_exchange = None

    def supports(self, model):
        try:
            CurationInputBound.bind(model)
        except ValueError:
            return False
        return True

    def validate_policy(self, policy):
        return CurationAllowance.validate_policy(policy)

    def reply(self, binding, packet, *, deadline_unix_ms):
        self.last_response = None
        self.last_transport_failure = None
        self.last_exchange = None
        original = binding.request.document()
        require(original.reference.scope == self.scope, 'curation_provider_scope')
        CurationAllowance.cost(original.context.model, original.context.limits)
        prepared = CurationEnvelope.bind(binding.request, packet)
        require(prepared.input_bound <= original.context.limits.max_input_tokens, 'curation_input_reservation_exceeded')
        require(type(deadline_unix_ms) is int, 'curation_provider_deadline')
        remaining = math.floor((deadline_unix_ms - time.time() * 1000) / 1000)
        if remaining < 1:
            raise ProviderUnavailable()
        transport = self._factory(self._key, timeout_seconds=min(self.timeout, remaining), maximum_body_bytes=262144)
        decoder = OpenAIProvider(transport, None)
        try:
            return decoder.reply_prepared(prepared)
        finally:
            self.last_response = decoder.last_response
            self.last_transport_failure = getattr(transport, "last_failure", None)
            self.last_exchange = getattr(transport, "last_exchange", None)
