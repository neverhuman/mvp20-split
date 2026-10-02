"""Configured structural limits; proposals cannot select a weaker implicit policy."""

import hashlib
import json
from dataclasses import dataclass

from amphora_contracts_knowledge import StructuralPolicyRef

from .canonical import KnowledgeError


@dataclass(frozen=True)
class StructuralPolicy:
    max_entities: int = 4096
    max_assertions: int = 8192
    max_aliases: int = 4096
    max_retractions: int = 8192

    def __post_init__(self):
        for value, ceiling in ((self.max_entities, 4096), (self.max_assertions, 8192),
                               (self.max_aliases, 4096), (self.max_retractions, 8192)):
            if type(value) is not int or not 1 <= value <= ceiling:
                raise KnowledgeError("invalid_structural_policy")

    def definition(self):
        return {"policy_id": "synthetic-structural", "version": "1", "authority": "structural_only",
                "max_entities": self.max_entities, "max_assertions": self.max_assertions,
                "max_aliases": self.max_aliases, "max_retractions": self.max_retractions}

    @classmethod
    def from_definition(cls, record):
        limits = ("max_entities", "max_assertions", "max_aliases", "max_retractions")
        if (not isinstance(record, dict) or set(record) != {"policy_id", "version", "authority", *limits}
                or record["policy_id"] != "synthetic-structural" or record["version"] != "1"
                or record["authority"] != "structural_only"):
            raise KnowledgeError("unsupported_structural_policy")
        return cls(**{name: record[name] for name in limits})

    @property
    def canonical_bytes(self):
        return json.dumps(self.definition(), sort_keys=True, separators=(",", ":")).encode()

    @property
    def reference(self):
        return StructuralPolicyRef(policy_id="synthetic-structural", version="1",
                                   sha256=hashlib.sha256(self.canonical_bytes).hexdigest())

    def check_size(self, entities, assertions):
        if (len(entities.records) > self.max_entities or len(assertions.records) > self.max_assertions
                or len(entities.aliases) > self.max_aliases or len(assertions.retractions) > self.max_retractions):
            raise KnowledgeError("graph_history_limit")
