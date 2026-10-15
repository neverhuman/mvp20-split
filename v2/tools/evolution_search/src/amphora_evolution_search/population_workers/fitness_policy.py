"""Explicit dimensionless synthetic sum policy; no missing-value or constraint inference."""
import math
from dataclasses import dataclass
from types import MappingProxyType

from amphora_contracts_population import FitnessRecord, ObjectiveAssessment
from amphora_contracts_search import ObjectiveValue
from amphora_contracts_tools import ToolBinding

from ..population.fitness import FitnessEvidence
from ..ranking import require
from .method_plan import payload_schema
from .payloads import PrimarySumPolicy, UnconstrainedSynthetic


@dataclass(frozen=True)
class PrimaryFitness:
    evidence: FitnessEvidence
    values: tuple[tuple[str,ObjectiveValue], ...]
    binding: ToolBinding
    policy: PrimarySumPolicy
    constraints: UnconstrainedSynthetic

    def __post_init__(self):
        PrimarySumPolicy.model_validate_json(self.policy.model_dump_json())
        UnconstrainedSynthetic.model_validate_json(self.constraints.model_dump_json())
        original=self.evidence.evaluations.membership.original.record
        require(original.assembly.tool==self.binding and self.binding.capability_id=="numeric.population-assemble-primary",
            "primary_fitness_assembly_binding")
        require(all(item.objective.unit in {"1","dimensionless"} for item in original.assembly.objectives),
            "primary_fitness_dimensionless_only")
        require(all(method.tool.capability_id in {"numeric.population-evaluate-squares","numeric.population-evaluate-negative-sum"}
            and method.output_schema==payload_schema(ObjectiveValue,"population-method.objective-value")
            for method in original.method_graph.methods),"primary_fitness_method_profile")
        require(type(self.values) is tuple and len({key for key,_ in self.values})==len(self.values),"primary_fitness_values_duplicate")
        values={key:ObjectiveValue.model_validate_json(value.model_dump_json()) for key,value in self.values}
        expected={row.evaluation_sha256 for row in self.evidence.observations if row.outcome.status=="evaluated"}
        require(set(values)==expected,"primary_fitness_values_coverage")
        object.__setattr__(self,"_values",MappingProxyType(values))

    def records(self):
        original=self.evidence.evaluations.membership.original.record
        required={method.method_id for method in original.method_graph.methods if method.required}
        result=[]
        for member in self.evidence.evaluations.membership.members:
            observations=self.evidence.by_candidate.get(member.candidate_id,{})
            if any(row.key.method_id in required and row.outcome.status!="evaluated" for row in observations.values()):
                outcome={"status":"unavailable","reason_code":"required_method_unavailable"}
            else:
                assessments=[]
                for objective in original.assembly.objectives:
                    rows=tuple(row for _,row in sorted(observations.items()) if row.key.method_id in objective.method_ids)
                    require(len(rows)==len(objective.method_ids) and {row.key.method_id for row in rows}==set(objective.method_ids),
                        "primary_fitness_objective_coverage")
                    if any(row.outcome.status!="evaluated" for row in rows):
                        break
                    values=tuple(self._values[row.evaluation_sha256] for row in rows)
                    require(all((value.objective_id,value.unit)==(objective.objective.objective_id,objective.objective.unit)
                        for value in values),"primary_fitness_value_identity")
                    assessments.append(ObjectiveAssessment(value=ObjectiveValue(objective_id=objective.objective.objective_id,
                        unit=objective.objective.unit,value=math.fsum(value.value for value in values)),
                        evaluations=tuple(row.evaluation_sha256 for row in rows),quality="synthetic",confidence=None))
                outcome=({"status":"evaluated","objectives":tuple(assessments),"constraint_violation":0.0}
                    if len(assessments)==len(original.assembly.objectives) else
                    {"status":"unavailable","reason_code":"objective_method_unavailable"})
            record=FitnessRecord(schema_version="1",profile="population-fitness-v1",
                generation=self.evidence.evaluations.membership.identity,candidate_id=member.candidate_id,
                assembly=self.binding,policy=original.assembly.policy,evaluation_set_sha256=self.evidence.evaluations.digest,
                outcome=outcome)
            result.append(self.evidence.bind(record))
        return tuple(result)
