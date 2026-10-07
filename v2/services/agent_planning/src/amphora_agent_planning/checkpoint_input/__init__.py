"""Pure versioned checkpoint request framing; no provider or issuance authority."""

from .envelope import CheckpointEnvelope
from .profile import CheckpointInputBound, checkpoint_tokenizer_reference

__all__ = ['CheckpointEnvelope', 'CheckpointInputBound', 'checkpoint_tokenizer_reference']
