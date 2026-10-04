"""Selected Runtime schema reads retain useful metadata without silent repinning."""

from dataclasses import dataclass
from urllib.parse import urlencode

from amphora_contracts_core import SchemaRef
from pydantic import ValidationError

from ..context import RequestSnapshot
from ..context.policy import require
from ..metadata_reads import MetadataWindow
from .schemas import SchemaObservation
from .universe import ReviewedUniverse

PEER_CODES = frozenset({"metadata_denied", "metadata_missing", "metadata_unavailable", "metadata_media", "metadata_response_limit",
    "metadata_protocol", "metadata_deadline", "metadata_call_limit", "metadata_byte_limit"})
VALUE_CODES = frozenset({"runtime_metadata_type", "runtime_schema_identity", "runtime_schema_digest", "runtime_schema_document"})
STOP_CODES = frozenset({"metadata_unavailable", "metadata_deadline", "metadata_call_limit", "metadata_byte_limit"})


@dataclass(frozen=True)
class SchemaFailure:
    reference: SchemaRef
    code: str


@dataclass(frozen=True)
class SchemaReadResult:
    universe: ReviewedUniverse
    selected: tuple[SchemaRef, ...]
    records: tuple[SchemaObservation, ...]
    failures: tuple[SchemaFailure, ...]
    calls: int
    bytes: int


class RuntimeMetadataReader:
    def __init__(self, transport):
        self.transport = transport

    def universe(self, request, *, expected=None, window=None):
        original = request.document()
        request = RequestSnapshot.bind(original, actor_id=original.actor_id, scope=original.reference.scope)
        require(original.purpose in {"campaign_proposal", "supervision"}, "runtime_metadata_purpose")
        window = MetadataWindow("runtime") if window is None else window
        require(window.owner == "runtime", "metadata_window")
        response = self.transport.read("/v1/definition-universe", window)
        result = ReviewedUniverse.bind(response, request, expected)
        window.remaining()
        return result

    def schemas(self, universe, references, window=None):
        universe = ReviewedUniverse.bind(universe.document(), universe.request)
        require(type(references) is tuple and len(references) <= 256, "runtime_schema_selection")
        references = tuple(SchemaRef.model_validate(ref.model_dump(mode="python", warnings=False)) for ref in references)
        require(len(set(references)) == len(references) and all(ref in universe.document().schemas for ref in references),
                "runtime_schema_selection")
        window = MetadataWindow("runtime") if window is None else window
        require(window.owner == "runtime", "metadata_window")
        calls, consumed = window.calls, window.consumed
        records, failures, stopped = [], [], None
        for ref in references:
            code = stopped
            if code is None:
                path = "/v1/definition-schemas/" + ref.sha256 + "?" + urlencode({"schema_id": ref.schema_id,
                    "version": ref.version, "universe_sha256": universe.sha256})
                try:
                    response = self.transport.read(path, window)
                    record = SchemaObservation.bind(universe, ref, response)
                    window.remaining()
                except ValueError as error:
                    if isinstance(error, ValidationError) or str(error) in VALUE_CODES:
                        code = "runtime_schema_invalid"
                    elif str(error) in PEER_CODES:
                        code = str(error)
                    else:
                        raise
                    if code in STOP_CODES:
                        stopped = code
                else:
                    records.append(record)
                    continue
            failures.append(SchemaFailure(ref, code))
        return SchemaReadResult(universe, references, tuple(records), tuple(failures),
                                window.calls - calls, window.consumed - consumed)
