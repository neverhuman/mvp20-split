"""Eligibility policy owns verdicts; this store atomically retains exact results and dependencies."""
from amphora_contracts_research import SampleIdentity

from ..material_state.links import read as read_state
from ..persistence.decision_document import require
from ..persistence.decision_journal import DecisionJournal, require_candidate, require_observation
from ..persistence.ledger import IdentityLedger
from .decision import prepare


def validate_links(connection, record):
    subject = record.assessment.policy.context.subject
    require_candidate(connection,subject.candidate)
    if subject.material_state is not None:
        state = read_state(connection,subject.material_state)
        require(state is not None and state.candidate == subject.candidate,"decision_material_candidate_mismatch")
    if subject.sample is not None:
        ref = subject.sample
        raw = IdentityLedger._read(connection,{"tenant":ref.scope.tenant_id,"project":ref.scope.project_id,
            "kind":"sample","id":ref.sample_id,"revision":ref.revision})
        require(raw is not None,"unknown_decision_sample")
        sample = SampleIdentity.model_validate_json(bytes(raw))
        require(sample.candidate == subject.candidate and sample.material_state == subject.material_state,
                "decision_sample_context_mismatch")
    for review in record.assessment.reviews:
        origin = review.claim.origin
        if origin.observation is not None:
            require_observation(connection,origin.observation,origin.source)


class EligibilityStore:
    def __init__(self, engine):
        self.journal = DecisionJournal(engine)

    def assess(self, policy, claims, actor, decision_id):
        return self.journal.publish(prepare(policy,claims,actor,decision_id),validate_links)

    def read(self, scope, reference):
        require(reference.kind == "eligibility","eligibility_decision_kind")
        return self.journal.read(scope,reference)
