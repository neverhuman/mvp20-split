"""Reviewed owner launch identities; manifest data never supplies arbitrary commands."""

from dataclasses import dataclass

from ..profile import require


@dataclass(frozen=True)
class OwnerRecipe:
    name: str
    package: str
    module: str
    schema: str

    @property
    def migration_environment(self):
        return "AMPHORA_" + self.name.upper() + "_MIGRATION_URL"

    @property
    def database_environment(self):
        return "AMPHORA_" + self.name.upper() + "_DATABASE_URL"

    @property
    def service_role(self):
        return self.name + "_service"

    @property
    def migration_role(self):
        return self.name + "_migrator"

    def migration_command(self, python):
        return (str(python), "-I", "-m", self.module + ".persistence.migrate")

    def serve_command(self, python, configuration, port):
        require(type(port) is int and 1 <= port <= 65535, "installation_port")
        if self.name == "planning":
            return (str(python), "-I", "-m", self.module + ".supervision_api", "--host", "127.0.0.1", "--port", str(port))
        return (str(python), "-I", "-m", self.module, "serve", "--config", str(configuration), "--port", str(port))


OWNERS = {recipe.name: recipe for recipe in (
    OwnerRecipe("runtime", "amphora-campaign-runtime", "amphora_campaign_runtime", "runtime"),
    OwnerRecipe("artifact", "amphora-data-artifacts", "amphora_data_artifacts", "artifacts"),
    OwnerRecipe("registry", "amphora-capability-registry", "amphora_capability_registry", "registry"),
    OwnerRecipe("research", "amphora-research", "amphora_research", "research"),
    OwnerRecipe("knowledge", "amphora-knowledge", "amphora_knowledge", "knowledge"),
    OwnerRecipe("planning", "amphora-agent-planning", "amphora_agent_planning", "planning"),
)}
