"""Fresh exact-source authorization before any binding intent or encoding side effect."""

from dataclasses import dataclass

from ...acquisition.ledger import AcquisitionLedger
from ...acquisition.provenance import SourceDocument
from ...source_rights.model import RightsSnapshot
from ..fixture import FixtureEncoder
from ..identity import EncodingInput, EncodingWorkIdentity
from ..mapping import profile_reference
from ..payloads import EncodedRepresentation
from ..profiles import RepresentationProfile
from ..storage.records import authorize
from ..storage.registry import ProfileRegistry
from ..storage.results import EncodingResults
from ..validation import RepresentationError, require
from .identity import SourceBindingIdentity


@dataclass(frozen=True, slots=True)
class PreparedBindingSource:
    identity: SourceBindingIdentity
    profile: RepresentationProfile
    input: EncodingInput
    rights: RightsSnapshot
    cached: EncodedRepresentation | None

    def __post_init__(self):
        require(type(self.identity) is SourceBindingIdentity, "representation_binding_required")
        require(
            type(self.profile) is RepresentationProfile and type(self.input) is EncodingInput,
            "representation_prepared_input",
        )
        require(
            profile_reference(self.identity.scope, self.profile) == self.identity.profile
            and self.input.sha256 == self.identity.source.sha256,
            "representation_prepared_identity",
        )
        require(
            type(self.rights) is RightsSnapshot
            and self.rights.scope == self.identity.scope
            and self.rights.artifacts == (self.identity.source.source.raw.artifact_id,)
            and self.rights.use == "process",
            "representation_prepared_rights",
        )
        if self.cached is not None:
            require(
                type(self.cached) is EncodedRepresentation
                and self.cached.profile == self.profile
                and (self.cached.input_sha256, self.cached.context_sha256)
                == (self.input.sha256, self.input.context_sha256),
                "representation_prepared_cache",
            )

    @property
    def work(self):
        return EncodingWorkIdentity.prepare(self.identity.scope, self.profile, self.input)


class SourcePreflight:
    def __init__(self, reads):
        self.reads = reads
        self.sources = AcquisitionLedger(reads.engine)
        self.profiles = ProfileRegistry(reads.engine)
        self.results = EncodingResults(reads.engine)

    def load(self, principal, request):
        authorize(principal, "representation_encode")
        for action in ("read", "source_history", "representation_read"):
            principal.require(action)
        identity = SourceBindingIdentity.prepare(principal, request)
        profile = self.profiles.read(principal, identity.profile)
        require(profile.inputs.context_schema is None, "representation_context_unavailable")
        ref = identity.source.source
        source = self.sources.history(principal, ref.source_id, ref.revision_id)
        require(source is not None and source.reference == ref, "representation_source_reference")
        snapshot = self.reads.rights.capture(principal, (ref.raw.artifact_id,), (source.rights,), "process")
        stored, content = self.reads.content(principal, ref.raw.artifact_id)
        require(stored.reference == ref.raw, "representation_source_artifact")
        selected = SourceDocument(ref, content).extract(identity.source)
        input = EncodingInput(selected)
        work = EncodingWorkIdentity.prepare(principal.scope, profile, input)
        try:
            cached = self.results.read(principal, work)
        except RepresentationError as error:
            if str(error) != "representation_work_missing":
                raise
            cached = None
        require(cached is not None or FixtureEncoder.available(profile), "representation_encoder_unavailable")
        self.reads.rights.recheck(principal, snapshot)
        return PreparedBindingSource(identity, profile, input, snapshot, cached)
