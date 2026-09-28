"""Trusted tool contract snapshots; configuration changes cannot rewrite a run."""

import hashlib
import json
from dataclasses import dataclass

from .model import TransitionError


def tool_key(binding):
    return "tool:" + hashlib.sha256(json.dumps(binding, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def completion_descriptor(run, row):
    if run.get("execution_mode", "fixture") == "graph":
        descriptor = run["tool_snapshot"].get(tool_key(row["specification"]["tool"]))
        if descriptor is None:
            raise TransitionError("graph_tool_pin_unavailable")
        return descriptor
    return run["tool_snapshot"].get(row["invocation_id"])


@dataclass(frozen=True, slots=True)
class PinnedTools:
    descriptors: tuple = ()

    def __post_init__(self):
        keys = [d.binding.model_dump_json() for d in self.descriptors]
        if len(set(keys)) != len(keys):
            raise ValueError("Duplicate pinned tool binding")
        for descriptor in self.descriptors:
            if descriptor.side_effects != "pure":
                raise ValueError("Only pure fixture tools supported")
            for ports in (descriptor.inputs, descriptor.outputs):
                if len({p.name for p in ports}) != len(ports):
                    raise ValueError("Duplicate pinned tool port")

    def snapshot(self, prepared):
        return {i.invocation_id: d.model_dump(mode="json") for i in prepared.invocations
                for d in self.descriptors if d.binding == i.tool}

    def graph_snapshot(self):
        return {tool_key(descriptor.binding.model_dump(mode="json")): descriptor.model_dump(mode="json")
                for descriptor in self.descriptors}
