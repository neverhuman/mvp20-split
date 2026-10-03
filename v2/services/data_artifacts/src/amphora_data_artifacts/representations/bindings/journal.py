"""Retained publication prefixes: commands precede effects; observations come from owner state."""

import json
from dataclasses import dataclass

from amphora_contracts_artifacts import DerivedUploadReceipt, FinalizedReceipt
from sqlalchemy import text

from ...derivations.ledger import DerivationLedger
from ...persistence.commands import CommandStore
from ...publication.recovery import StreamRecovery
from ...publication.uploads import Uploads
from ...source_rights.ledger import SourceRights
from ..storage.records import authorize, decode_result, load_profile, result_row
from ..validation import canonical_record, require
from .document import VectorPublication
from .leases import BindingLease, fenced
from .receipts import BindingReceipts
from .records import BINDING, event_bytes, load_job


@dataclass(frozen=True, slots=True)
class PublicationPrefix:
    publication: VectorPublication
    attempt: int
    stage: str
    events: dict

    @property
    def upload_id(self):
        raw = self.events.get("upload_begun")
        return None if raw is None else DerivedUploadReceipt.model_validate_json(raw).upload.upload_id

    def command(self, stage):
        return self.publication.command(
            stage, self.upload_id if stage == "finalize" else None, attempt=self.attempt
        )


def load_prefix(connection, principal, job, row):
    profile = load_profile(connection, principal, job.identity.profile)
    cached = result_row(connection, principal, job.work)
    require(cached is not None, "representation_result_pending")
    encoded = decode_result(principal, job.work, profile, cached)
    events = connection.execute(
        text(
            "SELECT stage,canonical_bytes FROM artifacts.encoding_binding_events WHERE "
            + BINDING
            + " AND attempt=:attempt"
        ),
        principal.bindings | {"binding": job.identity.binding_id, "attempt": row["attempt"]},
    ).mappings()
    return PublicationPrefix(
        VectorPublication(job.identity, encoded),
        row["attempt"],
        row["stage"],
        {event["stage"]: bytes(event["canonical_bytes"]) for event in events},
    )


def append(connection, key, lease, prefix, stage, body):
    require(type(body) is bytes and 0 < len(body) <= 65536, "representation_event_bound")
    connection.execute(
        text(
            "INSERT INTO artifacts.encoding_binding_events "
            "(tenant_id,project_id,binding_id,attempt,stage,token,fence,canonical_bytes) VALUES "
            "(:tenant,:project,:binding,:attempt,:stage,:token,:fence,:body)"
        ),
        key
        | {
            "attempt": prefix.attempt,
            "stage": stage,
            "token": lease.token,
            "fence": lease.fence,
            "body": body,
        },
    )
    connection.execute(
        text("UPDATE artifacts.encoding_binding_cursors SET stage=:stage WHERE " + BINDING),
        key | {"stage": stage},
    )


class BindingJournal:
    def __init__(self, engine):
        self.engine = engine
        self.rights = SourceRights(engine)

    def _transaction(self, principal, lease, operation):
        authorize(principal, "representation_encode")
        require(type(lease) is BindingLease, "representation_claim_required")
        lease.authorize(principal)
        with self.engine.begin() as connection:
            job = load_job(connection, principal, lease.identity.binding_id)
            require(job.identity == lease.identity, "representation_binding_conflict")
            self.rights.authorize(
                connection, principal, (job.identity.source.source.raw.artifact_id,), use="process"
            )
            key, row = fenced(connection, principal, lease)
            prefix = load_prefix(connection, principal, job, row)
            return operation(connection, key, job, prefix)

    def read(self, principal, lease):
        return self._transaction(principal, lease, lambda connection, key, job, prefix: prefix)

    def prepare(self, principal, lease, stage):
        require(stage in ("begin", "finalize"), "representation_publication_stage")

        def operation(connection, key, job, prefix):
            expected = "prepared" if stage == "begin" else "streamed"
            target = stage + "_prepared"
            command = prefix.command(stage)
            if prefix.stage == target:
                require(prefix.events[target] == command.canonical_bytes, "representation_event_conflict")
                return command
            require(prefix.stage == expected, "representation_publication_order")
            append(connection, key, lease, prefix, target, command.canonical_bytes)
            return command

        return self._transaction(principal, lease, operation)

    def observe(self, principal, lease, stage):
        require(stage in ("begin", "finalize"), "representation_publication_stage")

        def operation(connection, key, job, prefix):
            require(prefix.stage == stage + "_prepared", "representation_publication_order")
            command = prefix.command(stage)
            require(prefix.events[prefix.stage] == command.canonical_bytes, "representation_event_conflict")
            principal.require("upload" if stage == "begin" else "finalize", command.identity)
            record = CommandStore.inspect_in(connection, command)
            if record is None or record.status == "pending":
                return False
            if record.status == "rejected":
                append(
                    connection,
                    key,
                    lease,
                    prefix,
                    "rejected",
                    event_bytes(
                        {
                            "command": stage,
                            "request_sha256": command.sha256,
                            "receipt": json.loads(record.receipt_bytes),
                        }
                    ),
                )
                return True
            require(record.status == "accepted", "representation_command_state")
            if stage == "begin":
                receipt = DerivedUploadReceipt.model_validate_json(record.receipt_bytes)
                require(
                    receipt.upload.scope == job.identity.scope
                    and receipt.upload.content == prefix.publication.content
                    and receipt.declaration == prefix.publication.declaration,
                    "representation_upload_receipt",
                )
                append(connection, key, lease, prefix, "upload_begun", canonical_record(receipt))
            else:
                final = FinalizedReceipt.model_validate_json(record.receipt_bytes)
                receipt = DerivationLedger.read(connection, principal, final.artifact.artifact_id)
                binding = BindingReceipts(prefix.publication, prefix.attempt).finalized(
                    prefix.upload_id, receipt
                )
                require(final.artifact == binding.vector, "representation_vector_artifact")
                append(connection, key, lease, prefix, "artifact_finalized", canonical_record(binding))
            return True

        return self._transaction(principal, lease, operation)

    def streamed(self, principal, lease):
        def operation(connection, key, job, prefix):
            require(prefix.stage == "upload_begun", "representation_publication_order")
            selected = Uploads.selected_in(connection, principal, prefix.upload_id)
            if selected is None:
                return False
            require(
                selected["actual_bytes"] == prefix.publication.content.size_bytes,
                "representation_upload_receipt",
            )
            append(connection, key, lease, prefix, "streamed", event_bytes(selected))
            return True

        return self._transaction(principal, lease, operation)

    def prepare_unavailable_upload(self, principal, lease, limits):
        """Only an owner-proven exhausted/abandoned upload may skip streaming for terminal disposition."""

        def operation(connection, key, job, prefix):
            require(prefix.stage == "upload_begun", "representation_publication_order")
            state = StreamRecovery.inspect_in(connection, principal, prefix.upload_id)
            require(state.terminal_reason(limits) is not None, "representation_upload_recoverable")
            command = prefix.command("finalize")
            append(connection, key, lease, prefix, "finalize_prepared", command.canonical_bytes)
            return command

        return self._transaction(principal, lease, operation)

    def retry(self, principal, lease):
        def operation(connection, key, job, prefix):
            require(prefix.stage == "rejected", "representation_retry_unproven")
            rejected = json.loads(prefix.events["rejected"])
            command = prefix.command(rejected["command"])
            record = CommandStore.inspect_in(connection, command)
            require(
                record is not None
                and record.status == "rejected"
                and command.sha256 == rejected["request_sha256"]
                and json.loads(record.receipt_bytes) == rejected["receipt"],
                "representation_retry_unproven",
            )
            require(prefix.attempt < 9007199254740991, "representation_attempt_exhausted")
            connection.execute(
                text(
                    "UPDATE artifacts.encoding_binding_cursors SET attempt=attempt+1,stage='prepared' WHERE "
                    + BINDING
                ),
                key,
            )
            return prefix.attempt + 1

        return self._transaction(principal, lease, operation)

    def publish(self, principal, lease):
        def operation(connection, key, job, prefix):
            require(prefix.stage == "artifact_finalized", "representation_publication_order")
            final = FinalizedReceipt.model_validate_json(
                CommandStore.inspect_in(connection, prefix.command("finalize")).receipt_bytes
            )
            receipt = DerivationLedger.read(connection, principal, final.artifact.artifact_id)
            binding = BindingReceipts(prefix.publication, prefix.attempt).finalized(prefix.upload_id, receipt)
            body = canonical_record(binding)
            require(body == prefix.events["artifact_finalized"], "representation_event_conflict")
            # Visibility and rights are committed together. The cache and exact Artifact must already exist.
            self.rights.authorize(connection, principal, (binding.vector.artifact_id,), use="process")
            connection.execute(
                text(
                    "INSERT INTO artifacts.representation_bindings "
                    "(tenant_id,project_id,binding_id,work_sha256,artifact_id,artifact_sha256,canonical_bytes) VALUES "
                    "(:tenant,:project,:binding,:work,:artifact,:digest,:body)"
                ),
                key
                | {
                    "work": job.work.sha256,
                    "artifact": binding.vector.artifact_id,
                    "digest": binding.vector.sha256,
                    "body": body,
                },
            )
            append(connection, key, lease, prefix, "published", body)
            return binding

        return self._transaction(principal, lease, operation)
