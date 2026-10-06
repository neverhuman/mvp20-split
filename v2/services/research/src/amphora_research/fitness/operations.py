from amphora_contracts_fitness import FitnessRequest, FitnessSelection

from .document import FitnessDocument
from .policy import require
from .resolution import FitnessResolver
from .store import FitnessStore

ACTIONS = frozenset({"assemble_fitness", "read_fitness"})


class FitnessOperations:
    def __init__(self, ledger, profiles, reader_factory):
        require(type(profiles) is tuple and 1 <= len(profiles) <= 128, "fitness_profiles_bound")
        self.profiles = {profile.reference:profile for profile in profiles}
        require(len(self.profiles) == len(profiles), "fitness_duplicate_profile")
        self.resolver = FitnessResolver(ledger)
        self.store = FitnessStore(ledger.engine)
        self.reader_factory = reader_factory

    def assemble(self, principal, request):
        request = FitnessRequest.model_validate_json(request.model_dump_json())
        principal.require("assemble_fitness", request.profile.scope)
        configured = self.profiles.get(request.profile)
        require(configured is not None, "fitness_profile_unavailable")
        configured.bind(request)
        assembly, sources = self.resolver.resolve(principal, configured, request, self.reader_factory(principal.scope))
        document = FitnessDocument.prepare(configured, request, principal.actor_id, assembly, sources)
        return self.store.publish(document)

    def read(self, principal, selection):
        selection = FitnessSelection.model_validate_json(selection.model_dump_json())
        principal.require("read_fitness", selection.scope)
        return self.store.read(principal.actor_id, selection)
