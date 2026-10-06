"""Additive draft-successor transport; Runtime owns all execution authority."""

import json

from amphora_contracts_commands import CanonicalCommand, CommandEncodingError
from amphora_contracts_graph_runtime import DraftSelection, SuccessorProposal


class AdmitDraftSuccessor(SuccessorProposal):
    draft: DraftSelection


def parse_draft_successor(raw):
    command = CanonicalCommand.for_family(
        raw, "graph.admit_draft_successor", AdmitDraftSuccessor, allow_numeric=True)
    payload = json.loads(command.canonical_bytes)["payload"]
    targets = [item["target_port"] for item in payload["carried"]]
    if len(targets) != len(set(targets)):
        raise CommandEncodingError("duplicate_carried_target")
    for binding in payload["inputs"]:
        value = binding["value"]
        items = value["items"] if value["kind"] == "collection" else (value,)
        if any(item["kind"] == "artifact" and item["artifact"]["scope"] != command.identity.scope.model_dump()
               for item in items):
            raise CommandEncodingError("scope_mismatch")
    return command


__all__ = ["AdmitDraftSuccessor", "parse_draft_successor"]
