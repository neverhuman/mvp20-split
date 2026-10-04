"""Reviewed prompt bytes remain separate from JSON-escaped source data."""

import hashlib
import json
from dataclasses import dataclass

from amphora_contracts_core import ArtifactRef

from ..context.policy import require
from .snapshot import ExtractionSnapshot
from .sources import SourceBundle


@dataclass(frozen=True)
class PromptTemplate:
    canonical_reference: bytes
    instructions: bytes

    @classmethod
    def bind(cls, reference, raw):
        reference = ArtifactRef.model_validate_json(reference.model_dump_json(warnings=False))
        require(type(raw) is bytes and 0 < len(raw) <= 65536, "extraction_prompt_size")
        require(reference.media_type == "text/plain" and len(raw) == reference.size_bytes and
                hashlib.sha256(raw).hexdigest() == reference.sha256, "extraction_prompt_digest")
        try:
            raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ValueError("extraction_prompt_utf8") from exc
        return cls(reference.model_dump_json().encode("utf-8"), raw)

    def render(self, snapshot, bundle):
        reference = ArtifactRef.model_validate_json(self.canonical_reference)
        self.bind(reference, self.instructions)
        snapshot = ExtractionSnapshot.from_bytes(snapshot.canonical, snapshot.request)
        require(reference == snapshot.request.document().context.prompt, "extraction_prompt_binding")
        bundle = SourceBundle.bind(snapshot, bundle.sources)
        packet = {"profile": "planning-extraction-input.v1",
                  "trusted_instructions": self.instructions.decode("utf-8"),
                  "task": snapshot.document().model_dump(mode="json"),
                  "source_data": [{"source": row.descriptor().source.model_dump(mode="json"),
                                   "text": row.content.decode("utf-8")} for row in bundle.sources]}
        return json.dumps(packet, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
                          allow_nan=False).encode("utf-8")
