"""Route alternative provenance is lossless and purpose-bound."""
from dataclasses import replace

from amphora_research.synthesis.decision import prepare
from amphora_research.synthesis.evidence import SearchRecord

from ..material_state.test_context import artifact, q
from .test_policy import option, policy


def test_blocked_and_useful_alternatives_retain_every_source():
    document = prepare(policy(),(option("blocked",status="failed"),option("useful")),"fixture","decision")
    assert [row.disposition for row in document.record.assessment.alternatives] == ["blocked","eligible"]
    ids = {item.artifact_id for item in document.record.sources}
    assert ids == {"conditions","purity","source","step","step-evidence","blocked","useful","equipment-evidence","precursor_access-evidence"}
    assert document.record.reference.kind == "synthesis"


def test_bounded_no_route_search_remains_unknown_with_search_dependency():
    original = option()
    evidence = replace(original.evidence,route=None,posture="no_route_found",steps=(),
        search=SearchRecord(artifact("search-context"),q("12","attempts")))
    document = prepare(policy(),(replace(original,evidence=evidence,checks=()),),"fixture","decision")
    assert document.record.assessment.alternatives[0].disposition == "unknown"
    assert "search-context" in {item.artifact_id for item in document.record.sources}
