"""Stable publisher identity and a short-lived owner transaction capability."""

from dataclasses import dataclass
from datetime import datetime

from amphora_contracts_core import Identifier
from pydantic import TypeAdapter

from .payload import PublicationRequestDocument


@dataclass(frozen=True)
class PublisherIdentity:
    actor_id: str
    issuer_id: str

    def __post_init__(self):
        for value in (self.actor_id, self.issuer_id):
            TypeAdapter(Identifier).validate_python(value, strict=True)


@dataclass(frozen=True)
class PublicationLease:
    document: PublicationRequestDocument
    holder: str
    fence: int
    expires_at: datetime

    @property
    def key(self):
        return self.document.key | {"holder": self.holder, "fence": self.fence}
