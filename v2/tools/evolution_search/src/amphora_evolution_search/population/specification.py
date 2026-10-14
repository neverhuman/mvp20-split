"""Intrinsic population pins; never grants Runtime or scientific authority."""

import hashlib
import json
from dataclasses import dataclass

from amphora_contracts_population import PopulationSpecification

from ..ranking import require
from ..specification import NumericBox


def canonical(record):
    """population-json-v1: validated DTO, explicit defaults, finite UTF-8 JSON."""
    return json.dumps(record.model_dump(mode="json"), sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


@dataclass(frozen=True)
class OriginalPopulation:
    record: PopulationSpecification

    def __post_init__(self):
        # Revalidate even model_construct input; callers cannot bypass the boundary.
        checked = PopulationSpecification.model_validate_json(self.record.model_dump_json())
        object.__setattr__(self, "record", checked)
        require(len(canonical(checked)) <= 262144, "population_specification_bytes")
        require(checked.selection.minimum_parents <= checked.budget.population_size, "population_minimum_parents")
        self._unique((v.variable_id for v in checked.variables), "population_variable_identity")
        require(all(v.lower <= v.upper and v.unit.strip() for v in checked.variables), "population_variable_bounds")
        methods = {method.method_id: method for method in checked.method_graph.methods}
        self._unique((m.method_id for m in checked.method_graph.methods), "population_method_identity")
        self._unique((m.node_path for m in checked.method_graph.methods), "population_method_node")
        objectives = checked.assembly.objectives
        self._unique((o.objective.objective_id for o in objectives), "population_objective_identity")
        for objective in objectives:
            require(bool(objective.objective.unit.strip()), "population_objective_unit")
            self._unique(objective.method_ids, "population_objective_method_duplicate")
            require(all(key in methods for key in objective.method_ids), "population_objective_method_unknown")
            require(all(methods[key].required for key in objective.method_ids), "population_objective_method_optional")
        self._unique((p.name for p in checked.implementations), "population_implementation_identity")
        references = (checked.method_graph.definition, checked.assembly.policy, checked.constraints,
                      *checked.context, *checked.knowledge, *(m.conditions for m in methods.values()))
        known = {}
        for reference in references:
            require(reference.scope == checked.scope, "population_reference_scope")
            previous = known.setdefault(reference.artifact_id, reference)
            require(previous == reference, "population_reference_conflict")
        self._unique((r.artifact_id for r in checked.context), "population_context_duplicate")
        self._unique((r.artifact_id for r in checked.knowledge), "population_knowledge_duplicate")

    @staticmethod
    def _unique(values, code):
        items = tuple(values)
        require(len(set(items)) == len(items), code)

    @property
    def digest(self):
        return hashlib.sha256(b"amphora.population/specification-v1\0" + canonical(self.record)).hexdigest()

    @property
    def box(self):
        return NumericBox(tuple((v.lower, v.upper) for v in self.record.variables))

    def require_binding(self, record, digest):
        other = OriginalPopulation(record)
        require(other.digest == digest == self.digest and other.record == self.record,
                "population_original_specification")
