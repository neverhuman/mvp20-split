"""Versioned synthetic encoding equivalence; no cache-access authority."""

import hashlib
import json
from dataclasses import dataclass

from amphora_contracts_candidate_spaces import PolymerDesign

from .domain import PolymerSpace
from .profile import pin

EQUIVALENCE = pin(
    "synthetic-polymer-equivalence",
    "sort unit declarations by unit_id, sites/end groups by site_id, composition by unit_id, undirected bond endpoints then pairs; retain every other field including scope and explicit unknowns; no site renaming or chemical isomorphism",
)


@dataclass(frozen=True)
class PolymerCanonical:
    record: PolymerDesign

    def __post_init__(self):
        object.__setattr__(self, "record", PolymerSpace(self.record).record)

    @property
    def bytes(self):
        data = self.record.model_dump(mode="json")
        data["repeat_units"].sort(key=lambda item: item["unit_id"])
        data["sites"].sort(key=lambda item: item["site_id"])
        bonds = (tuple(sorted((bond["left"], bond["right"]))) for bond in data["bonds"])
        data["bonds"] = [
            {"left": left, "right": right} for left, right in sorted(bonds)
        ]
        if data["composition"] is not None:
            data["composition"].sort(key=lambda item: item["unit_id"])
        if data["metadata"]["end_groups"] is not None:
            data["metadata"]["end_groups"].sort(key=lambda item: item["site_id"])
        return json.dumps(
            data,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")

    @property
    def sha256(self):
        return hashlib.sha256(self.bytes).hexdigest()

    @property
    def policy(self):
        return EQUIVALENCE
