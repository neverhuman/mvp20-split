"""One repeatable-read catalog cut; no payload, reservation or rights writes."""
from dataclasses import dataclass
import json

from amphora_contracts_artifact_ancestry import ArtifactAncestryFootprint
from pydantic import ValidationError
from sqlalchemy import text

from ..publication.model import UploadError
from ..publication.uploads import SCOPE
from ..retention_closures.model import ProtectedClosure
from ..retention_closures.storage import discover,_reference


@dataclass(frozen=True)
class AncestryFootprint:
    closure: ProtectedClosure

    def response(self):
        total=0
        for member in self.closure.members:
            if member.size_bytes>9007199254740991-total:
                raise UploadError("ancestry_bytes_limit")
            total+=member.size_bytes
        result=ArtifactAncestryFootprint(schema_version="1",profile="artifact-ancestry-footprint-v1",
            artifact=self.closure.root,artifact_count=len(self.closure.members),
            content_bytes=total,members_sha256=self.closure.digest)
        if len(json.dumps(result.model_dump(mode="json"),ensure_ascii=False,separators=(",",":"),
            allow_nan=False).encode())>262144:
            raise UploadError("ancestry_response_limit")
        return result


class AncestryFootprints:
    def __init__(self,engine):self.engine=engine

    def get(self,principal,artifact_id):
        principal.require("read")
        with self.engine.connect() as conn:
            conn.execute(text("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY"))
            row=conn.execute(text("SELECT * FROM artifacts.catalog WHERE "+SCOPE+" AND artifact_id=:artifact"),
                {**principal.bindings,"artifact":artifact_id}).mappings().one_or_none()
            if row is None:raise UploadError("artifact_unavailable")
            try:
                root=_reference(row,principal.scope)
                closure=discover(conn,principal,root)
                return AncestryFootprint(closure).response()
            except UploadError as error:
                if str(error)=="artifact_unavailable":
                    raise UploadError("ancestry_incomplete") from None
                raise
            except (ValidationError,ValueError,TypeError,KeyError):
                raise UploadError("ancestry_invalid") from None
