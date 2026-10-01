"""Explicit deployment-installed validators for the reviewed preparation profiles."""

import json
from dataclasses import dataclass
from typing import Literal

from amphora_contracts_evidence import PreparedDocument, PreparedLabRecord, prepared_schema


@dataclass(frozen=True)
class PreparedContentRule:
    profile: Literal["document", "lab"]

    def __post_init__(self):
        if self.profile not in {"document", "lab"}:
            raise ValueError("Unknown prepared content profile")

    @property
    def identity(self) -> tuple[str, str, str, str]:
        reference = prepared_schema(self.profile)
        return "application/json", reference.schema_id, reference.version, reference.sha256

    def validate(self, value) -> None:
        model = PreparedDocument if self.profile == "document" else PreparedLabRecord
        model.model_validate_json(json.dumps(value, ensure_ascii=False, allow_nan=False))
