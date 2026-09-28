"""Public graph orchestration DTOs; domain transitions belong to Campaign Runtime."""

import json

from amphora_contracts_commands import CanonicalCommand, CommandEncodingError

from .models import AdmitGraphRun, AdvanceGraph, GraphLimits, GraphNodeView, GraphRunPage
from .values import (
    CollectionValue,
    GraphBinding,
    GraphValue,
    MissingValue,
    NumberValue,
    PresentValue,
    ScalarValue,
)


def parse_graph_command(family, raw):
    try:
        model = {"graph.admit": AdmitGraphRun, "graph.advance": AdvanceGraph}[family]
    except KeyError as error:
        raise CommandEncodingError("unknown_family") from error
    command = CanonicalCommand.for_family(raw, family, model)
    payload = json.loads(command.canonical_bytes)["payload"]
    for binding in payload.get("inputs", ()):
        value = binding["value"]
        items = value["items"] if value["kind"] == "collection" else (value,)
        for item in items:
            if item["kind"] == "artifact" and item["artifact"]["scope"] != command.identity.scope.model_dump():
                raise CommandEncodingError("scope_mismatch")
    return command


__all__ = ["AdmitGraphRun", "AdvanceGraph", "CollectionValue", "GraphBinding", "GraphLimits", "GraphNodeView",
           "GraphRunPage", "GraphValue", "MissingValue", "NumberValue", "PresentValue", "ScalarValue", "parse_graph_command"]
