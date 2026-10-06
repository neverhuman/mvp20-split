"""Labeled-tree fixture legality; no chemical graph or BigSMILES interpretation."""

import hashlib
import json
import math
from collections import Counter
from dataclasses import dataclass

from amphora_contracts_candidate_spaces import (
    PolymerDesign,
    PolymerMoveRequest,
    ProposedDesignChange,
)

from .profile import OPERATOR, PROFILE, canonical


class PolymerDesignError(ValueError):
    pass


def require(condition, code):
    if not condition:
        raise PolymerDesignError(code)


@dataclass(frozen=True)
class PolymerSpace:
    record: PolymerDesign

    def __post_init__(self):
        record = PolymerDesign.model_validate_json(self.record.model_dump_json())
        object.__setattr__(self, "record", record)
        require(record.profile == PROFILE, "polymer_profile_mismatch")
        units = {unit.unit_id: unit for unit in record.repeat_units}
        sites = {site.site_id: site.unit_id for site in record.sites}
        require(
            len(units) == len(record.repeat_units)
            and all(unit.label.strip() for unit in units.values()),
            "polymer_unit_declarations",
        )
        require(
            len(sites) == len(record.sites)
            and all(unit in units for unit in sites.values()),
            "polymer_site_declarations",
        )
        neighbors = {site: set() for site in sites}
        edges = set()
        for bond in record.bonds:
            require(
                bond.left in sites and bond.right in sites and bond.left != bond.right,
                "polymer_invalid_bond",
            )
            edge = tuple(sorted((bond.left, bond.right)))
            require(edge not in edges, "polymer_duplicate_bond")
            edges.add(edge)
            neighbors[bond.left].add(bond.right)
            neighbors[bond.right].add(bond.left)
        visited, pending = set(), [next(iter(sites))]
        while pending:
            site = pending.pop()
            if site not in visited:
                visited.add(site)
                pending.extend(neighbors[site] - visited)
        require(
            len(visited) == len(sites) and len(edges) == len(sites) - 1,
            "polymer_not_tree",
        )
        metadata = record.metadata
        branched = any(len(adjacent) > 2 for adjacent in neighbors.values())
        require(
            metadata.branching is None
            or (metadata.branching == "branched") == branched,
            "polymer_branching_mismatch",
        )
        if metadata.sequence_arrangement == "alternating":
            require(
                all(sites[left] != sites[right] for left, right in edges),
                "polymer_alternation_mismatch",
            )
        if metadata.end_groups is not None:
            ends = [end.site_id for end in metadata.end_groups]
            require(
                len(set(ends)) == len(ends)
                and all(
                    site in neighbors and len(neighbors[site]) <= 1 for site in ends
                )
                and all(end.label.strip() for end in metadata.end_groups),
                "polymer_end_groups",
            )
        self._distribution(metadata.distribution)
        if record.composition is not None:
            fractions = {item.unit_id: item.fraction for item in record.composition}
            require(
                len(fractions) == len(record.composition)
                and set(fractions) == set(units),
                "polymer_composition_membership",
            )
            counts = Counter(sites.values())
            require(
                all(
                    math.isclose(
                        fractions[unit],
                        counts[unit] / len(sites),
                        rel_tol=0,
                        abs_tol=1e-12,
                    )
                    for unit in units
                ),
                "polymer_composition_mismatch",
            )

    @staticmethod
    def _distribution(distribution):
        if distribution is None:
            return
        number, weight, dispersity = (
            distribution.number_average_dp,
            distribution.weight_average_dp,
            distribution.dispersity,
        )
        if number is not None and weight is not None:
            require(weight >= number, "polymer_distribution_order")
            if dispersity is not None:
                require(
                    math.isclose(
                        weight / number, dispersity, rel_tol=1e-9, abs_tol=1e-12
                    ),
                    "polymer_distribution_ratio",
                )

    def apply(self, request: PolymerMoveRequest) -> ProposedDesignChange:
        request = PolymerMoveRequest.model_validate_json(request.model_dump_json())
        require(
            request.source == self.record and request.operator == OPERATOR,
            "polymer_move_binding_mismatch",
        )
        data = self.record.model_dump(mode="json")
        target = next(
            (site for site in data["sites"] if site["site_id"] == request.move.site_id),
            None,
        )
        require(
            target is not None
            and request.move.unit_id
            in {unit.unit_id for unit in self.record.repeat_units},
            "polymer_move_target_missing",
        )
        changed = target["unit_id"] != request.move.unit_id
        require(
            not changed or self.record.metadata.bigsmiles is None,
            "polymer_external_encoding_recompute_required",
        )
        target["unit_id"] = request.move.unit_id
        if data["composition"] is not None:
            counts = Counter(site["unit_id"] for site in data["sites"])
            for fraction in data["composition"]:
                fraction["fraction"] = counts[fraction["unit_id"]] / len(data["sites"])
        result = PolymerSpace(
            PolymerDesign.model_validate_json(json.dumps(data, allow_nan=False))
        ).record
        return ProposedDesignChange(
            wire_version="1",
            source_sha256=hashlib.sha256(canonical(self.record)).hexdigest(),
            operator=OPERATOR,
            move=request.move,
            result=result,
        )
