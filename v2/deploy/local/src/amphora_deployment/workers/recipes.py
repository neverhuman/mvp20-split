"""Closed native worker commands; user configuration never supplies code or argv."""

from dataclasses import dataclass
from pathlib import Path

from ..profile import label, require


@dataclass(frozen=True)
class WorkerScope:
    actor: str
    tenant: str
    project: str

    def __post_init__(self):
        for value in (self.actor, self.tenant, self.project):
            label(value, "worker_scope")

    def arguments(self):
        return ("--actor", self.actor, "--tenant", self.tenant, "--project", self.project)


@dataclass(frozen=True)
class NativeRecipe:
    name: str
    owner: str
    module: str
    action: str
    scoped: bool

    def command(self, python, configuration, scope=None):
        require(Path(python).is_absolute() and Path(configuration).is_absolute(), "worker_absolute_paths")
        require(isinstance(scope, WorkerScope) if self.scoped else scope is None, "worker_scope_binding")
        command = (str(python), "-I", "-m", self.module, self.action, "--config", str(configuration))
        if self.scoped:
            command += scope.arguments() + ("--time-budget", "2")
            if self.action == "coordinate":
                command += ("--poll-interval", "1")
            else:
                command += ("--limit", "100")
        else:
            command += ("--seconds", "2", "--interval", "1")
        return command


NATIVE_RECIPES = {item.name: item for item in (
    NativeRecipe("runtime-coordinate", "runtime", "amphora_campaign_runtime", "coordinate", True),
    NativeRecipe("runtime-deliver", "runtime", "amphora_campaign_runtime", "deliver", True),
    NativeRecipe("runtime-checkpoint", "runtime", "amphora_campaign_runtime.supervision_loop", "run", False),
    NativeRecipe("planning-curation", "planning", "amphora_agent_planning.curation_worker", "run", False),
    NativeRecipe("planning-checkpoint", "planning", "amphora_agent_planning.supervision_scheduling", "run", False),
)}
