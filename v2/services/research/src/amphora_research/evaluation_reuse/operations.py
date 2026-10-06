from amphora_contracts_evaluation_reuse import ReuseRequest, ReuseSelection

from .document import ReuseDocument
from .errors import require
from .resolution import ReuseResolver
from .store import ReuseStore

ACTIONS = frozenset({'qualify_evaluation_reuse','read_evaluation_reuse'})


class ReuseOperations:
    def __init__(self, ledger, profiles, data_factory, runtime_factory):
        require(type(profiles) is tuple and len(profiles) <= 128, 'reuse_profiles_bound')
        self.profiles = {profile.reference:profile for profile in profiles}
        require(len(self.profiles) == len(profiles), 'reuse_duplicate_profile')
        self.resolver = ReuseResolver(ledger)
        self.store = ReuseStore(ledger.engine)
        self.data_factory, self.runtime_factory = data_factory, runtime_factory

    def qualify(self, principal, request):
        request = ReuseRequest.model_validate_json(request.model_dump_json())
        principal.require('qualify_evaluation_reuse',request.profile.scope)
        configured = self.profiles.get(request.profile)
        require(configured is not None,'reuse_profile_unavailable')
        configured.bind(request)
        qualification,sources = self.resolver.resolve(principal,configured,request,
            self.data_factory(principal.scope),self.runtime_factory(principal.scope))
        document = ReuseDocument.prepare(configured,request,principal.actor_id,qualification,sources)
        return self.store.publish(document)

    def read(self, principal, selection):
        selection = ReuseSelection.model_validate_json(selection.model_dump_json())
        principal.require('read_evaluation_reuse',selection.scope)
        return self.store.read(principal.actor_id,selection)
