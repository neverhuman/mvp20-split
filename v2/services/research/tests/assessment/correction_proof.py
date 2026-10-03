"""Actual owner HTTP correction proof; Runtime consumption is a separate B3 gate."""
import json
from dataclasses import dataclass

from amphora_contracts_graph_runtime import ReceiptCorrectionView
from amphora_tool_protocol import HttpTransport


def _chain(owner, family, scope, issuer, first_source, next_source, source_key, expected_status):
    route = "/v1/" + family + "-receipts"
    chain = {"scope":scope, "issuer_id":issuer, "chain_id":family + "-quality"}
    first = {"wire_version":"1", "chain":chain, "change_id":"initial", "reason_code":"initial_evidence",
             "expected_head":None, source_key:first_source}
    root = owner.request(route + "/correct", first)
    root_view = ReceiptCorrectionView.model_validate_json(json.dumps(root))
    assert root_view.record.receipt.outcome.status == "accepted"
    pinned = root_view.record.receipt.model_dump_json()
    successor = first | {"change_id":"correction", "reason_code":"reassessed", source_key:next_source,
                         "expected_head":root["reference"]}
    revised = owner.request(route + "/correct", successor)
    view = ReceiptCorrectionView.model_validate_json(json.dumps(revised))
    assert view.record.receipt.outcome.status == expected_status
    assert view.record.predecessor == root_view.reference
    assert view.record.notice.outcome.status == "superseded"
    assert view.record.notice.revision == root_view.record.receipt.revision
    assert view.record.notice.outcome.replacement_revision == view.record.receipt.revision
    query = {"wire_version":"1", "chain":chain, "revision":None}
    historical = owner.request(route + "/select", query | {"revision":root["reference"]})
    assert historical == root
    assert ReceiptCorrectionView.model_validate_json(json.dumps(historical)).record.receipt.model_dump_json() == pinned
    assert owner.request(route + "/select", query) == revised
    conflict = HttpTransport(owner.endpoint, owner.token).request("POST", route + "/correct",
        json.dumps(successor | {"reason_code":"changed_identity"}).encode())
    assert conflict.status == 409
    foreign = query | {"chain":chain | {"scope":scope | {"project_id":"foreign"}}}
    denied = HttpTransport(owner.endpoint, owner.token).request("POST", route + "/select",json.dumps(foreign).encode())
    assert denied.status == 403
    return {"route":route, "first_request":first, "next_request":successor, "query":query,
            "root":root, "corrected":revised, "history":historical,
            "cases":["accepted_to_" + expected_status,"exact_history_preserved","latest_explicit",
                     "identity_conflict","foreign_scope_denied","pinned_receipt_bytes_unchanged"],
            "runtime_execution":"not_exercised_here_B3"}


@dataclass(frozen=True)
class CorrectionProof:
    research: dict
    knowledge: dict

    def replay(self, research, knowledge):
        for owner, evidence in ((research,self.research),(knowledge,self.knowledge)):
            route = evidence["route"]
            assert owner.request(route + "/correct",evidence["first_request"]) == evidence["root"]
            assert owner.request(route + "/correct",evidence["next_request"]) == evidence["corrected"]
            assert owner.request(route + "/select",evidence["query"]) == evidence["corrected"]
            assert owner.request(route + "/select",evidence["query"] | {"revision":evidence["root"]["reference"]}) == evidence["root"]

    def evidence(self):
        return {"research":self.research,"knowledge":self.knowledge}


def prove(research, knowledge, scope, assessment_request, original_publication, reason):
    weak_request = assessment_request | {"assessment_id":"weak-assessment","receipts":[]}
    weak = research.request("/v1/assessments",weak_request)
    assert weak["outcome"]["status"] == "assessed"
    assert not weak["outcome"]["assessment"]["sufficient"]
    published = research.request("/v1/assessment-publications",{"wire_version":"1","scope":scope,"assessment_id":"weak-assessment"})
    assert published["outcome"]["receipt"]["outcome"]["status"] == "abstained"
    research_proof = _chain(research,"assessment",scope,original_publication["outcome"]["receipt"]["issuer_id"],
                            assessment_request["assessment_id"],"weak-assessment","assessment_id","abstained")
    contradicted = reason | {"request_id":"negative-reason","targets":[reason["targets"][0] | {"polarity":"negated"}]}
    evaluated = knowledge.request("/v1/graph-reasoning",contradicted)
    assert evaluated["decision"]["outcome"] == "evaluated"
    original = {"wire_version":"1","graph":reason["snapshot"]["graph"],"publication_id":"publish","reasoning_request_id":"reason"}
    revised = original | {"publication_id":"negative-publication","reasoning_request_id":"negative-reason"}
    publication = knowledge.request("/v1/reasoning-publications",revised)
    assert publication["outcome"]["receipt"]["outcome"]["status"] == "rejected"
    knowledge_proof = _chain(knowledge,"reasoning",scope,publication["outcome"]["receipt"]["issuer_id"],
                             original,revised,"source","rejected")
    assert research.request("/v1/assessment-publications/read",{"wire_version":"1","scope":scope,
        "assessment_id":assessment_request["assessment_id"]}) == original_publication
    return CorrectionProof(research_proof,knowledge_proof)
