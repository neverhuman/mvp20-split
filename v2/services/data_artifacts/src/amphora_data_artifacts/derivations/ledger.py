"""Private declaration/lineage SQL; callers own the surrounding transaction."""

from amphora_contracts_artifacts import DerivationReceipt, parse_command
from amphora_contracts_core import ArtifactRef
from sqlalchemy import text

from ..publication.model import UploadError
from ..publication.uploads import SCOPE
from .model import DeclaredTransformation


class DerivationLedger:
    @staticmethod
    def check_inputs(connection, principal, transformation):
        for reference in transformation.request.declaration.inputs:
            row = connection.execute(text("SELECT * FROM artifacts.catalog WHERE " + SCOPE +
                " AND artifact_id=:artifact"), principal.bindings | {"artifact": reference.artifact_id}).mappings().one_or_none()
            if row is None:
                raise UploadError("derivation_input_unavailable")
            actual = ArtifactRef(artifact_id=row["artifact_id"], scope=principal.scope, sha256=row["content_sha256"],
                                 size_bytes=row["size_bytes"], media_type=row["media_type"], schema_ref=row["schema_ref"])
            if actual != reference:
                raise UploadError("derivation_input_mismatch")

    @staticmethod
    def declare(connection, principal, transformation, upload_id):
        identity = transformation.command.identity
        connection.execute(text("INSERT INTO artifacts.derived_uploads "
            "(tenant_id,project_id,upload_id,actor_id,family,command_id) "
            "VALUES (:tenant,:project,:upload,:actor,:family,:command)"),
            principal.bindings | {"upload": upload_id, "family": identity.command_family, "command": identity.command_id})

    @staticmethod
    def load(connection, principal, upload_id):
        row = connection.execute(text("SELECT c.canonical_bytes,c.request_sha256,d.actor_id FROM artifacts.derived_uploads d "
            "JOIN artifacts.commands c USING(tenant_id,project_id,actor_id,family,command_id) "
            "WHERE d.tenant_id=:tenant AND d.project_id=:project AND d.upload_id=:upload"),
            principal.bindings | {"upload": upload_id}).mappings().one_or_none()
        if row is None:
            return None
        command = parse_command("artifacts.begin_derived_upload", bytes(row["canonical_bytes"]))
        if command.sha256 != row["request_sha256"]:
            raise UploadError("derivation_state_invalid")
        return DeclaredTransformation.authorized(principal, command)

    @staticmethod
    def retain(connection, principal, transformation, finalized):
        receipt = transformation.receipt(finalized.upload_id, finalized.artifact)
        params = principal.bindings | {"upload": finalized.upload_id, "artifact": finalized.artifact.artifact_id,
                                       "body": receipt.model_dump_json().encode()}
        connection.execute(text("INSERT INTO artifacts.derivations "
            "(tenant_id,project_id,artifact_id,upload_id,canonical_bytes) VALUES (:tenant,:project,:artifact,:upload,:body)"), params)
        for ordinal, artifact_id in enumerate(transformation.input_ids):
            connection.execute(text("INSERT INTO artifacts.derivation_inputs "
                "(tenant_id,project_id,artifact_id,input_artifact_id,ordinal) VALUES (:tenant,:project,:artifact,:input,:ordinal)"),
                params | {"input": artifact_id, "ordinal": ordinal})

    @staticmethod
    def read(connection, principal, artifact_id):
        principal.require("read")
        raw = connection.execute(text("SELECT canonical_bytes FROM artifacts.derivations WHERE " + SCOPE +
            " AND artifact_id=:artifact"), principal.bindings | {"artifact": artifact_id}).scalar_one_or_none()
        if raw is None:
            raise UploadError("derivation_unavailable")
        receipt = DerivationReceipt.model_validate_json(bytes(raw))
        if receipt.artifact.scope != principal.scope or receipt.artifact.artifact_id != artifact_id:
            raise UploadError("derivation_state_invalid")
        return receipt
