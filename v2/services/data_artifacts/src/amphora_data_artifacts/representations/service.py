"""Focused representation facade; transport does not acquire persistence authority."""

from .bindings.views import BindingViews
from .bindings.workflow import BindingWorkflow
from .fixture import fixture_profile
from .mapping import profile_from_wire, profile_to_wire
from .storage.records import authorize
from .storage.registry import ProfileRegistry


class RepresentationService:
    def __init__(self, reads, uploads, storage):
        self.registry = ProfileRegistry(reads.engine)
        self.workflow = BindingWorkflow(reads, uploads, storage)
        self.bindings = BindingViews(reads.engine)

    @staticmethod
    def available_profiles(principal):
        authorize(principal, "representation_read")
        return (profile_to_wire(fixture_profile()),)

    def register(self, principal, record):
        authorize(principal, "representation_manage")
        return self.registry.register(principal, profile_from_wire(record))

    def profile(self, principal, reference):
        return profile_to_wire(self.registry.read(principal, reference))
