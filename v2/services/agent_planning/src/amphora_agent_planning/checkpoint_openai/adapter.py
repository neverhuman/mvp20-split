"""Original retained envelope, narrowed deadline and one direct provider request."""

import math
import time

from ..checkpoint_budget import CheckpointAllowance
from ..checkpoint_input import CheckpointEnvelope, CheckpointInputBound
from ..context.policy import require
from ..openai_provider.adapter import OpenAIProvider
from ..openai_provider.http import OpenAIHTTP
from ..providers.port import ProviderUnavailable


class CheckpointOpenAI:
    revision = 'checkpoint-responses-v1'

    def __init__(self, api_key, *, timeout_seconds=45, transport_factory=OpenAIHTTP):
        # Validate at configuration time without opening a connection or retaining
        # credential values in a dataclass repr, manifest or error message.
        transport_factory(api_key, timeout_seconds=timeout_seconds, maximum_body_bytes=65536)
        self._key, self.timeout, self._factory = api_key, timeout_seconds, transport_factory

    def supports(self, model):
        try:
            CheckpointInputBound.bind(model)
        except ValueError:
            return False
        return True

    def validate_policy(self, policy):
        CheckpointAllowance.validate_policy(policy)

    def reply(self, binding, packet, *, deadline_unix_ms):
        limits = binding.request.document().context.limits
        CheckpointAllowance.cost(binding.request.document().context.model, limits)
        prepared = CheckpointEnvelope.bind(binding.request, packet)
        require(prepared.input_bound <= limits.max_input_tokens, 'checkpoint_input_reservation_exceeded')
        require(type(deadline_unix_ms) is int, 'checkpoint_provider_deadline')
        remaining = math.floor((deadline_unix_ms - time.time() * 1000) / 1000)
        if remaining < 1:
            raise ProviderUnavailable()
        transport = self._factory(self._key, timeout_seconds=min(self.timeout, remaining), maximum_body_bytes=65536)
        # Reuse the bounded decoder and usage policy, not the evaluation input builder.
        return OpenAIProvider(transport, None).reply_prepared(prepared)
