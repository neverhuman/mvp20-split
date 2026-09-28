"""Trusted tool contract snapshots; configuration changes cannot rewrite a run."""

from dataclasses import dataclass


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
