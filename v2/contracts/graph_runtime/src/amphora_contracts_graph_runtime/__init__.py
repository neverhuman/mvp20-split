"""Public graph orchestration DTOs; domain transitions belong to Campaign Runtime."""

import json

from amphora_contracts_commands import CanonicalCommand, CommandEncodingError

from .authoring import (
    DraftCommandReceipt,
    DraftHead,
    DraftPage,
    DraftRevision,
    DraftValidation,
    SaveDraft,
    ValidateDraft,
    parse_authoring_command,
)
from .bindings import GraphNodeViewV3, GraphRunPageV3
from .draft_admission import AdmitDraft, DraftSelection
from .models import AdmitGraphRun, AdvanceGraph, GraphLimits, GraphNodeView, GraphRunPage
from .navigation import (
    GraphControlLink,
    GraphScopePage,
    GraphScopeView,
    GraphTopologyNode,
    GraphTopologyPage,
    GraphTopologyQuery,
)
from .observations import (
    GraphAttemptView,
    GraphInvalidation,
    GraphInvalidationPage,
    GraphNodeDetail,
    GraphOutputSummary,
    GraphReadBudget,
    GraphReadCut,
    GraphReadQuery,
    GraphReadSnapshot,
    GraphSnapshotPage,
    GraphValueItem,
    GraphValuePage,
)
from .successors import (
    CarriedBinding,
    CarrySources,
    CarrySourceView,
    NodeOutputSource,
    PredecessorCut,
    RunOutputSource,
    SuccessorLineage,
    SuccessorProposal,
)
from .values import (
    CollectionValue,
    GraphBinding,
    GraphValue,
    MissingValue,
    NumberValue,
    PresentValue,
    ScalarValue,
)
from .views import DigestViewFilter, GraphViewCatalog, GraphViewDefinition, RadiusViewFilter
from .waits import (
    DomainReceipt,
    GraphNodeViewV2,
    GraphRunPageV2,
    SubmitDomainReceipt,
    WaitClosure,
    WaitExpectation,
    WaitObservation,
)


def parse_graph_command(family, raw):
    try:
        model = {"graph.admit": AdmitGraphRun, "graph.admit_draft": AdmitDraft, "graph.admit_successor": SuccessorProposal, "graph.advance": AdvanceGraph,
                 "graph.submit_receipt": SubmitDomainReceipt}[family]
    except KeyError as error:
        raise CommandEncodingError("unknown_family") from error
    command = CanonicalCommand.for_family(raw, family, model)
    payload = json.loads(command.canonical_bytes)["payload"]
    if family == "graph.submit_receipt":
        receipt = payload["receipt"]
        scopes = [receipt["scope"], receipt["subject"]["scope"]]
        if receipt["outcome"]["status"] == "accepted":
            scopes.append(receipt["outcome"]["output"]["artifact"]["scope"])
        if any(scope != command.identity.scope.model_dump() for scope in scopes):
            raise CommandEncodingError("scope_mismatch")
        if receipt["issuer_id"] != command.identity.actor_id:
            raise CommandEncodingError("issuer_mismatch")
    for binding in payload.get("inputs", ()):
        value = binding["value"]
        items = value["items"] if value["kind"] == "collection" else (value,)
        for item in items:
            if item["kind"] == "artifact" and item["artifact"]["scope"] != command.identity.scope.model_dump():
                raise CommandEncodingError("scope_mismatch")
    return command


__all__ = ["AdmitDraft", "DraftSelection", "DraftCommandReceipt", "DraftHead", "DraftPage", "DraftRevision", "DraftValidation", "SaveDraft", "ValidateDraft", "parse_authoring_command", "DigestViewFilter", "GraphViewCatalog", "GraphViewDefinition", "RadiusViewFilter", "GraphControlLink", "GraphScopePage", "GraphScopeView", "GraphTopologyNode", "GraphTopologyPage", "GraphTopologyQuery",
           "AdmitGraphRun", "AdvanceGraph", "CollectionValue", "GraphBinding", "GraphLimits", "GraphNodeView",
           "GraphAttemptView", "GraphInvalidation", "GraphInvalidationPage", "GraphNodeDetail", "GraphOutputSummary",
           "GraphReadBudget", "GraphReadCut", "GraphReadQuery", "GraphReadSnapshot", "GraphSnapshotPage", "GraphValueItem", "GraphValuePage",
           "GraphRunPage", "GraphValue", "MissingValue", "NumberValue", "PresentValue", "ScalarValue", "parse_graph_command",
           "DomainReceipt", "GraphNodeViewV2", "GraphRunPageV2", "SubmitDomainReceipt", "WaitExpectation",
           "WaitClosure", "WaitObservation", "GraphNodeViewV3", "GraphRunPageV3",
           "CarriedBinding", "CarrySources", "CarrySourceView", "NodeOutputSource", "PredecessorCut",
           "RunOutputSource", "SuccessorLineage", "SuccessorProposal"]
