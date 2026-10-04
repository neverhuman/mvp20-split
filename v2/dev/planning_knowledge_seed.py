"""Knowledge-local synthetic read fixture; never imported into Planning.

Run with the independently installed Knowledge interpreter and its service role.
Synthetic reference observations deliberately do not establish real Data rights
or Planning-proposal acceptance. Only actual public historical reads are tested.
"""

import json
import os
import sys
from datetime import UTC, datetime
from importlib.metadata import version
from pathlib import Path

from amphora_contracts_knowledge import (
    DomainVocabulary,
    GraphChangeProposal,
    ReferenceValidation,
    RetractAssertion,
)
from amphora_knowledge.access import Principal
from amphora_knowledge.authoring.policy import StructuralPolicy
from amphora_knowledge.authoring.references import ReferencedInputs
from amphora_knowledge.authoring.vocabulary import Vocabulary
from amphora_knowledge.persistence.ledger import KnowledgeLedger
from sqlalchemy import create_engine


def run(stage, fixture):
    assert version('amphora-knowledge') == '0.17.0'
    raw = json.loads(fixture.read_bytes())
    vocabulary = Vocabulary(DomainVocabulary.model_validate_json(json.dumps(raw['vocabulary'])))
    policy = StructuralPolicy()
    raw['proposal'].update(vocabulary=vocabulary.reference.model_dump(mode='json'), policy=policy.reference.model_dump(mode='json'))
    proposal = GraphChangeProposal.model_validate_json(json.dumps(raw['proposal']))
    principal = Principal('synthetic-read-fixture', proposal.graph.scope, frozenset({'read_graph', 'propose_graph'}))
    engine = create_engine(os.environ['PLANNING_KNOWLEDGE_DATABASE'], connect_args={'options': '-c statement_timeout=5000'})
    try:
        ledger = KnowledgeLedger(engine, vocabulary, policy)
        if stage == 'advance':
            head = ledger.head(principal, proposal.graph)
            snapshot = ledger.snapshot(principal, head.snapshot)
            proposal = proposal.model_copy(update={'change_id': 'future-retraction', 'base': head,
                'operations': (RetractAssertion(operation='retract_assertion', assertion=snapshot.content.assertions[0].reference),)})
        refs = ReferencedInputs.collect(proposal)
        observation = ReferenceValidation(checked_at=datetime.now(UTC), artifacts=refs.artifacts, sources=refs.sources,
            conversion_traces=refs.traces, questions=refs.questions, evidence_needs=refs.needs)
        result = ledger.accept(principal, proposal, observation)
        assert result.decision.outcome == 'accepted'
        snapshot = ledger.snapshot(principal, result.decision.head.snapshot)
        return {'pid': os.getpid(), 'head': result.decision.head.model_dump(mode='json'),
                'profile': ledger.profile(principal, proposal.graph).model_dump(mode='json'),
                'snapshot': snapshot.model_dump(mode='json'), 'policy_definition': policy.definition(),
                'authority': 'synthetic_owner_local_read_fixture_only'}
    finally:
        engine.dispose()


if __name__ == '__main__':
    try:
        print(json.dumps(run(sys.argv[1], Path(sys.argv[2]))))
    except Exception as error:
        raise SystemExit('Knowledge read fixture failed: ' + type(error).__name__) from None
