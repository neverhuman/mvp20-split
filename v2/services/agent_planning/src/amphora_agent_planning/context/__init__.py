"""Private immutable request identity and bounded context policy."""

from .snapshot import AttemptBinding, RequestSnapshot

__all__ = ["AttemptBinding", "RequestSnapshot"]
