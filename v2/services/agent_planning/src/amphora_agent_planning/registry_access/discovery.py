"""Finite inventory scan; accepted pages survive later transport failure."""

from dataclasses import dataclass
from urllib.parse import urlencode

from amphora_contracts_tools import ReleasePage
from pydantic import ValidationError

from ..context import RequestSnapshot
from ..context.policy import require
from ..metadata_reads import MetadataWindow
from ..metadata_reads.targets import target
from .releases import ObservedRelease

CODES = frozenset({"metadata_denied", "metadata_missing", "metadata_unavailable", "metadata_media", "metadata_response_limit",
    "metadata_protocol", "metadata_deadline", "metadata_call_limit", "metadata_byte_limit", "registry_record_type",
    "registry_scope", "registry_descriptor_size", "registry_duplicate_port", "registry_lock", "registry_page_size",
    "registry_page_order", "registry_page_filter", "registry_page_cursor"})


@dataclass(frozen=True)
class DiscoveryQuery:
    request: RequestSnapshot
    capability_id: str | None = None
    release: str | None = None
    after: str | None = None
    limit: int = 100
    max_pages: int = 4

    def validated(self):
        original = self.request.document()
        request = RequestSnapshot.bind(original, actor_id=original.actor_id, scope=original.reference.scope)
        require(original.purpose in {"campaign_proposal", "supervision"}, "registry_purpose")
        require(type(self.limit) is int and 1 <= self.limit <= 100 and type(self.max_pages) is int and
                1 <= self.max_pages <= 4, "registry_scan_limits")
        query = DiscoveryQuery(request, self.capability_id, self.release, self.after, self.limit, self.max_pages)
        target("registry", query.path(query.after))
        return query

    def path(self, after):
        pairs = [("limit", str(self.limit))]
        for name, value in (("after", after), ("capability_id", self.capability_id), ("release", self.release)):
            if value is not None:
                require(type(value) is str, "registry_query_type")
                pairs.append((name, value))
        return "/v1/releases?" + urlencode(pairs)


@dataclass(frozen=True)
class DiscoveryResult:
    query: DiscoveryQuery
    records: tuple[ObservedRelease, ...]
    complete: bool
    next_after: str | None
    failure: str | None
    pages: int
    calls: int
    bytes: int


class RegistryReader:
    def __init__(self, transport):
        self.transport = transport

    def discover(self, supplied, window=None):
        query = supplied.validated()
        window = MetadataWindow("registry") if window is None else window
        require(window.owner == "registry", "metadata_window")
        calls, consumed = window.calls, window.consumed
        cursor, records, pages, complete, failure = query.after, (), 0, False, None
        for _ in range(query.max_pages):
            try:
                page = self.transport.read(query.path(cursor), window)
                require(type(page) is ReleasePage, "registry_record_type")
                page = ReleasePage.model_validate(page.model_dump(mode="python", warnings=False))
                require(len(page.items) <= query.limit, "registry_page_size")
                entries = tuple(ObservedRelease.bind(item, query.request.document().reference.scope) for item in page.items)
                previous = cursor
                for entry in entries:
                    record = entry.document()
                    digest = record.lock.descriptor_sha256
                    require(previous is None or digest > previous, "registry_page_order")
                    require((query.capability_id is None or record.lock.tool.capability_id == query.capability_id) and
                            (query.release is None or record.lock.tool.release == query.release), "registry_page_filter")
                    previous = digest
                require(page.next_after is None or (len(entries) == query.limit and page.next_after == previous), "registry_page_cursor")
                window.remaining()
            except ValueError as error:
                if isinstance(error, ValidationError):
                    failure = "registry_record_invalid"
                elif str(error) in CODES:
                    failure = str(error)
                else:
                    raise
                break
            records += entries
            pages += 1
            cursor = page.next_after
            if cursor is None:
                complete = True
                break
        return DiscoveryResult(query, records, complete, cursor, failure, pages,
                               window.calls - calls, window.consumed - consumed)

    def exact(self, request, lock, window=None):
        query = DiscoveryQuery(request).validated()
        window = MetadataWindow("registry") if window is None else window
        require(window.owner == "registry", "metadata_window")
        # Revalidate caller-owned DTO before constructing the closed path.
        from amphora_contracts_tools import LockEntry
        lock = LockEntry.model_validate(lock.model_dump(mode="python", warnings=False))
        response = self.transport.read("/v1/releases/" + lock.descriptor_sha256, window)
        result = ObservedRelease.bind(response, query.request.document().reference.scope, lock)
        window.remaining()
        return result
