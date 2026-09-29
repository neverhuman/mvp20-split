"""Runtime-owned durable graph coordination; no independent scheduler service."""

from .admission import GraphAdmission
from .frontier import FrontierPlanner, ScopeAddress
from .plans import PlanCatalog, ReviewedPlan
from .reads import GraphReads

__all__ = ["FrontierPlanner", "GraphAdmission", "GraphAdvancer", "GraphReads", "PlanCatalog", "ReviewedPlan", "ScopeAddress"]


def __getattr__(name):
    # Lifecycle cleanup imports graph state. Loading the interpreter eagerly here
    # would re-enter binding storage before its classes have been initialized.
    if name == "GraphAdvancer":
        from .advance import GraphAdvancer
        return GraphAdvancer
    raise AttributeError(name)
