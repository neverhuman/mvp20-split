import copy
import hashlib
import json
from pathlib import Path

import pytest
from amphora_agent_planning.metadata_reads import MetadataWindow
from amphora_agent_planning.registry_access import (
    DiscoveryQuery,
    ObservedRelease,
    RegistryReader,
)
from amphora_agent_planning.registry_access.releases import canonical
from amphora_contracts_tools import ReleasePage, ReleaseSnapshot

from ..campaign_context.test_selection import SCOPE, request

CASES = json.loads((Path(__file__).parent / "fixtures/tool_releases.json").read_bytes())


def record(index=0, *, status="registered"):
    case = copy.deepcopy(CASES[index % len(CASES)])
    return ReleaseSnapshot.model_validate_json(json.dumps({"scope": SCOPE.model_dump(mode="json"),
        "descriptor": case["descriptor"], "lock": case["lock"], "revision": 1, "status": status}))


class Scripted:
    def __init__(self, *responses):
        self.responses, self.paths = list(responses), []

    def read(self, path, window):
        window.start()
        self.paths.append(path)
        value = self.responses.pop(0)
        if isinstance(value, Exception):
            raise value
        window.consume(len(value.model_dump_json().encode()))
        return value


@pytest.mark.parametrize("index", range(len(CASES)))
def test_public_literal_vectors_bind_whole_descriptor_and_full_lock(index):
    source = record(index)
    observed = ObservedRelease.bind(source, SCOPE)
    assert observed.document() == source
    assert hashlib.sha256(CASES[index]["canonical_utf8"].encode()).hexdigest() == source.lock.descriptor_sha256
    assert len(observed.sha256) == 64
    assert canonical({"profile": "amphora-tool-release-v1", "descriptor": source.descriptor.model_dump(mode="json")}) == CASES[index]["canonical_utf8"].encode()


@pytest.mark.parametrize("fault", ["scope", "descriptor", "image", "ports", "expected", "boolean"])
def test_misbound_and_forged_records_reject(fault):
    source = record()
    raw = source.model_dump(mode="json")
    expected = None
    if fault == "scope":
        raw["scope"]["project_id"] = "foreign"
    elif fault == "descriptor":
        raw["descriptor"]["tool"]["purpose"] = "Changed"
    elif fault == "image":
        raw["lock"]["tool"]["image_sha256"] = "d" * 64
    elif fault == "ports":
        raw["lock"]["output_schemas"][0]["schema_ref"]["sha256"] = "d" * 64
    elif fault == "expected":
        expected = source.lock.model_copy(update={"descriptor_sha256": "d" * 64})
    else:
        source = source.model_copy(update={"revision": True})
    if fault != "boolean":
        source = ReleaseSnapshot.model_validate_json(json.dumps(raw))
    with pytest.raises(ValueError):
        ObservedRelease.bind(source, SCOPE, expected)


def test_two_pages_retain_inactive_and_revoked_without_granting_eligibility():
    records = sorted((record(0, status="registered"), record(1, status="revoked")), key=lambda r: r.lock.descriptor_sha256)
    peer = Scripted(ReleasePage(items=(records[0],), next_after=records[0].lock.descriptor_sha256),
                    ReleasePage(items=(records[1],), next_after=None))
    result = RegistryReader(peer).discover(DiscoveryQuery(request(), limit=1))
    assert result.complete and result.next_after is None and result.failure is None
    assert [r.document() for r in result.records] == records
    assert result.calls == result.pages == 2
    assert peer.paths[1] == "/v1/releases?limit=1&after=" + records[0].lock.descriptor_sha256


@pytest.mark.parametrize("failure", ["metadata_denied", "metadata_unavailable", "metadata_byte_limit", "registry_lock"])
def test_partial_scan_retains_only_verified_pages_with_explicit_resume(failure):
    item = record()
    peer = Scripted(ReleasePage(items=(item,), next_after=item.lock.descriptor_sha256), ValueError(failure))
    result = RegistryReader(peer).discover(DiscoveryQuery(request(), limit=1))
    assert not result.complete and len(result.records) == 1 and result.failure == failure
    assert result.next_after == item.lock.descriptor_sha256 and result.pages == 1 and result.calls == 2


def test_max_pages_is_explicit_incomplete_without_unrequested_calls():
    item = record()
    peer = Scripted(ReleasePage(items=(item,), next_after=item.lock.descriptor_sha256))
    result = RegistryReader(peer).discover(DiscoveryQuery(request(), limit=1, max_pages=1))
    assert not result.complete and result.failure is None and result.next_after == item.lock.descriptor_sha256
    assert result.pages == len(peer.paths) == 1


@pytest.mark.parametrize("fault,code", [("duplicate", "registry_page_order"), ("cursor", "registry_page_cursor"),
    ("filter", "registry_page_filter"), ("limit", "registry_page_size"), ("wire", "registry_record_invalid")])
def test_untrusted_page_does_not_enter_scan(fault, code):
    item = record()
    page = ReleasePage(items=(item,), next_after=None)
    query = DiscoveryQuery(request())
    if fault == "duplicate":
        page = ReleasePage(items=(item, item), next_after=None)
    elif fault == "cursor":
        page = ReleasePage(items=(item,), next_after="f" * 64)
    elif fault == "filter":
        query = DiscoveryQuery(request(), capability_id="other")
    elif fault == "limit":
        page = ReleasePage(items=(item, item), next_after=None)
        query = DiscoveryQuery(request(), limit=1)
    else:
        page = page.model_copy(update={"schema_version": "invalid"})
    result = RegistryReader(Scripted(page)).discover(query)
    assert result.records == () and result.pages == 0 and result.failure == code


def test_empty_inventory_is_complete_but_missing_exact_release_is_not():
    result = RegistryReader(Scripted(ReleasePage(items=(), next_after=None))).discover(DiscoveryQuery(request()))
    assert result.complete and result.records == ()
    with pytest.raises(ValueError, match="metadata_missing"):
        RegistryReader(Scripted(ValueError("metadata_missing"))).exact(request(), record().lock)


def test_exact_release_keeps_observed_status_and_checks_complete_selected_lock():
    item = record(status="draining")
    peer = Scripted(item)
    assert RegistryReader(peer).exact(request(), item.lock).document() == item
    assert peer.paths == ["/v1/releases/" + item.lock.descriptor_sha256]


@pytest.mark.parametrize("kwargs", [{"limit": True}, {"limit": 101}, {"max_pages": 5}, {"max_pages": False},
    {"after": "../escape"}, {"capability_id": "x&limit=99"}, {"release": "1.2.3?bad"}])
def test_scan_input_bounds_reject_before_io(kwargs):
    with pytest.raises(ValueError):
        RegistryReader(None).discover(DiscoveryQuery(request(), **kwargs))


def test_wrong_window_and_unknown_programming_error_propagate():
    with pytest.raises(ValueError, match="metadata_window"):
        RegistryReader(None).discover(DiscoveryQuery(request()), MetadataWindow("runtime"))
    with pytest.raises(ValueError, match="implementation_bug"):
        RegistryReader(Scripted(ValueError("implementation_bug"))).discover(DiscoveryQuery(request()))
