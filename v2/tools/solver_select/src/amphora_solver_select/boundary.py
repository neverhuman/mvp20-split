"""Packaged source identity is owned by this independently replaceable fixture tool."""

import json
from dataclasses import dataclass
from importlib.resources import files

from amphora_contracts_solver_fixture import SourcePins


@dataclass(frozen=True)
class Baseline:
    pins: SourcePins
    module_ids: tuple[str, ...]

    @classmethod
    def packaged(cls):
        raw = json.loads(files(__package__).joinpath("baseline.json").read_bytes())
        return cls(SourcePins.model_validate(raw["source_pins"]), tuple(raw["module_ids"]))

    def require(self, pins):
        if pins != self.pins:
            raise ValueError("solver_source_hash_changed")
