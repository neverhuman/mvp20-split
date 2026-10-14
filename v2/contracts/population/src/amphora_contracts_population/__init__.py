"""Public population DTO boundary; old search roots remain unchanged."""

from .profiles import population_specification_schema, membership_page_schema, membership_manifest_schema
from .profiles import candidate_birth_schema, evaluation_key_schema, method_observation_schema
from .profiles import population_record_schema
from .membership import CandidateMember, GenerationIdentity, MembershipManifest, MembershipPage, MembershipPageReference
from .candidates import CandidateBirth
from .evaluations import EvaluationKey, ExecutionPointer, MethodOutput, EvaluatedMethod, UnavailableMethod, MethodObservation
from .fitness import ObjectiveAssessment, AvailableFitness, UnavailablePopulationFitness, FitnessRecord, FitnessPage
from .selection import RankedPopulationMember, ExcludedPopulationMember, SelectionPage, PopulationSelectionReceipt
from .pages import BirthPage, EvaluationKeyPage, MethodObservationPage, EvaluationManifest, ObservationManifest, FitnessManifest
from .specification import (
    FitnessAssembly,
    MethodBinding,
    MethodGraph,
    ObjectiveBinding,
    PopulationBudget,
    PopulationSelectionPolicy,
    PopulationSpecification,
)

__all__ = [
    "FitnessAssembly", "MethodBinding", "MethodGraph", "ObjectiveBinding",
    "PopulationBudget", "PopulationSelectionPolicy", "PopulationSpecification",
    "population_specification_schema",
    "CandidateMember", "GenerationIdentity", "MembershipManifest", "MembershipPage", "MembershipPageReference",
    "membership_page_schema", "membership_manifest_schema",
    "CandidateBirth", "EvaluationKey", "ExecutionPointer", "MethodOutput", "EvaluatedMethod", "UnavailableMethod", "MethodObservation",
    "candidate_birth_schema", "evaluation_key_schema", "method_observation_schema",
    "ObjectiveAssessment", "AvailableFitness", "UnavailablePopulationFitness", "FitnessRecord", "FitnessPage",
    "RankedPopulationMember", "ExcludedPopulationMember", "SelectionPage", "PopulationSelectionReceipt",
    "BirthPage", "EvaluationKeyPage", "MethodObservationPage", "EvaluationManifest", "ObservationManifest", "FitnessManifest",
    "population_record_schema",
]

from .successor import PopulationProgress, PopulationCheckpoint, BirthManifest, ProposedSuccessor
__all__ += ["PopulationProgress", "PopulationCheckpoint", "BirthManifest", "ProposedSuccessor"]

from .process import (ProcessContext, MaterialAmount, MaterialState, ProcessPort, ProcessBinding, MaterialUse, AbsentProcessInput, ProcessDerivation, MaterialMappingPolicy, MaterialMappingItem, MaterialMappingPair, MaterialMappingExclusion, MaterialMappingPage)

from .process import MaterialMappingManifest

__all__ += ["ProcessContext", "MaterialAmount", "MaterialState", "ProcessPort", "ProcessBinding", "MaterialUse", "AbsentProcessInput", "ProcessDerivation", "MaterialMappingPolicy", "MaterialMappingItem", "MaterialMappingPair", "MaterialMappingExclusion", "MaterialMappingPage", "MaterialMappingManifest"]

from .declarations import EvaluationSlot, EvaluationSlotPage, EvaluationDeclarationManifest, EvaluationResolutionManifest
__all__ += ["EvaluationSlot", "EvaluationSlotPage", "EvaluationDeclarationManifest", "EvaluationResolutionManifest"]
