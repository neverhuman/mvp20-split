"""Explicit campaign-wide invocation capacity; Runtime owns enforcement."""

import json
from typing import Annotated, Literal

from pydantic import Field
from amphora_contracts_commands import CanonicalCommand, CommandEncodingError
from amphora_contracts_core import WireModel
from amphora_contracts_graph_runtime import AdmitDraft


class CampaignInvocationResources(WireModel):
    profile: Literal["campaign-invocation-cap-v1"]
    max_active_attempts: Annotated[int, Field(ge=1, le=8)]


class AdmitResourceBoundedDraft(AdmitDraft):
    resources: CampaignInvocationResources


def parse_resource_bounded_draft(raw):
    command = CanonicalCommand.for_family(
        raw, "graph.admit_draft_bounded", AdmitResourceBoundedDraft, allow_numeric=True
    )
    payload = json.loads(command.canonical_bytes)["payload"]
    for binding in payload["inputs"]:
        value = binding["value"]
        items = value["items"] if value["kind"] == "collection" else (value,)
        for item in items:
            if item["kind"] == "artifact" and item["artifact"]["scope"] != command.identity.scope.model_dump():
                raise CommandEncodingError("scope_mismatch")
    return command


__all__ = ["CampaignInvocationResources", "AdmitResourceBoundedDraft", "parse_resource_bounded_draft"]
