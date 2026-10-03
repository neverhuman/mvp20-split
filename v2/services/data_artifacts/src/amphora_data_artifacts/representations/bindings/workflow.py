"""Bounded synchronous recovery over durable source, cache and publication owners."""

import json
from dataclasses import dataclass

from amphora_contracts_representations import EncodeSourceRequest

from ...derivations.publication import DerivedPublications
from ...publication.finalize import Finalizer
from ...publication.model import UploadError
from ...publication.recovery import StreamRecovery
from ..fixture import FixtureEncoder
from ..mapping import _validated
from ..payloads import EncodedRepresentation
from ..storage.claims import CacheHit, WorkBusy
from ..storage.leases import WorkLeases
from ..storage.records import authorize
from ..storage.results import EncodingResults
from ..validation import require
from .journal import BindingJournal
from .leases import BindingBusy, BindingLease, BindingLeases
from .requests import BindingRequests
from .source import SourcePreflight


@dataclass(frozen=True, slots=True)
class RecoveryBudget:
    steps: int = 16

    def __post_init__(self):
        require(type(self.steps) is int and 1 <= self.steps <= 64, "representation_recovery_bound")


class BindingWorkflow:
    def __init__(self, reads, uploads, storage, *, budget=None):
        self.budget = RecoveryBudget() if budget is None else budget
        require(type(self.budget) is RecoveryBudget, "representation_recovery_budget")
        self.reads, self.uploads, self.storage = reads, uploads, storage
        engine = uploads.commands.engine
        require(reads.engine is engine, "representation_owner_configuration")
        self.preflight = SourcePreflight(reads)
        self.requests = BindingRequests(engine)
        self.compute = WorkLeases(engine)
        self.results = EncodingResults(engine)
        self.claims = BindingLeases(engine)
        self.journal = BindingJournal(engine)
        self.derived = DerivedPublications(uploads)
        self.finalizer = Finalizer(uploads, storage)
        self.streams = StreamRecovery(uploads, storage)

    def encode(self, principal, request):
        authorize(principal, "representation_encode")
        for action in ("representation_read", "read", "source_history", "upload", "finalize"):
            principal.require(action)
        request = _validated(request, EncodeSourceRequest)
        prior = self.requests.read(principal, request.encoding_id)
        if prior is not None:
            require(prior.request == request, "representation_request_conflict")
            if prior.outcome.state == "published":
                return prior
        prepared = self.preflight.load(principal, request)
        self.requests.register(principal, request, prepared)
        compute = self.compute.claim(principal, request.profile, prepared.input)
        if isinstance(compute, WorkBusy):
            return self.requests.read(principal, request.encoding_id)
        if not isinstance(compute, CacheHit):
            try:
                self.reads.rights.recheck(principal, prepared.rights)
                vector = FixtureEncoder().encode(prepared.profile, prepared.input)
                self.reads.rights.recheck(principal, prepared.rights)
                self.results.complete(
                    principal,
                    compute,
                    EncodedRepresentation.prepare(prepared.profile, prepared.input, vector),
                )
            finally:
                self.compute.release(principal, compute)
        lease = self.claims.claim(principal, prepared.identity.binding_id)
        if isinstance(lease, BindingBusy) or not isinstance(lease, BindingLease):
            return self.requests.read(principal, request.encoding_id)
        try:
            for _ in range(self.budget.steps):
                if not self._step(principal, lease):
                    break
            return self.requests.read(principal, request.encoding_id)
        finally:
            self.claims.release(principal, lease)

    def _step(self, principal, lease):
        prefix = self.journal.read(principal, lease)
        if prefix.stage == "published":
            return False
        if prefix.stage == "prepared":
            self.journal.prepare(principal, lease, "begin")
        elif prefix.stage in ("begin_prepared", "finalize_prepared"):
            stage = "begin" if prefix.stage == "begin_prepared" else "finalize"
            self._command(principal, lease, stage)
        elif prefix.stage == "upload_begun":
            return self._stream(principal, lease, prefix)
        elif prefix.stage == "streamed":
            self.journal.prepare(principal, lease, "finalize")
        elif prefix.stage == "artifact_finalized":
            self.journal.publish(principal, lease)
        elif prefix.stage == "rejected":
            self.journal.retry(principal, lease)
        else:
            raise AssertionError("Unknown retained publication stage")
        return True

    def _command(self, principal, lease, stage):
        if not self.journal.observe(principal, lease, stage):
            command = self.journal.read(principal, lease).command(stage)
            try:
                if stage == "begin":
                    self.derived.begin(principal, command)
                else:
                    self.finalizer.finalize(principal, command)
            except UploadError:
                self.journal.observe(principal, lease, stage)
                raise
            self.journal.observe(principal, lease, stage)
        prefix = self.journal.read(principal, lease)
        if prefix.stage == "rejected":
            raise UploadError(json.loads(prefix.events["rejected"])["receipt"]["reason_code"])

    def _stream(self, principal, lease, prefix):
        if self.journal.streamed(principal, lease):
            return True
        state = self.streams.inspect(principal, prefix.upload_id)
        if state.expired_stream:
            return self.streams.settle_expired(principal, prefix.upload_id)
        if state.live_stream:
            return False
        if state.terminal_reason(self.uploads.limits) is not None:
            self.journal.prepare_unavailable_upload(principal, lease, self.uploads.limits)
            return True
        attempt = self.uploads.start(principal, prefix.upload_id)
        writer = None
        settled = False
        try:
            writer = self.storage.writer(attempt)
            writer.write(prefix.publication.payload)
            writer.seal()
            writer.close()
            state = self.uploads.finish(principal, attempt, verified=True, actual_bytes=writer.count)
            settled = True
            require(state == "streamed", "representation_stream_unsettled")
        finally:
            if not settled:
                if writer is not None:
                    writer.close()
                self.uploads.finish(
                    principal, attempt, verified=False, actual_bytes=None if writer is None else writer.count
                )
        return self.journal.streamed(principal, lease)
