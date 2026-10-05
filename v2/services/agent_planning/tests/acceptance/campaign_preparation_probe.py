"""Installed-owner SQL restart/replacement proof; no peer service implementation."""

import argparse
import json
import os
import runpy
from pathlib import Path

from amphora_agent_planning.access import Principal
from amphora_agent_planning.campaign_packet import prepare
from amphora_agent_planning.campaign_packet.assembly import original_artifacts
from amphora_agent_planning.campaign_preparations import CampaignPreparation
from amphora_agent_planning.campaign_preparations.journal import (
    CampaignPreparationJournal,
)
from amphora_agent_planning.campaign_slice_plan import CampaignSlicePlan
from amphora_agent_planning.persistence.journal import PlanningJournal
from sqlalchemy import create_engine


def run(args):
    value = json.loads(args.fixture.read_bytes())
    source = runpy.run_path(str(args.loader))['source']
    plan = source(value)
    packet = prepare(plan).packet
    principal = Principal(plan.request.document().actor_id, plan.request.document().reference.scope,
        frozenset({'record_requests', 'record_attempts', 'read_attempts'}))
    engine = create_engine(os.environ['AMPHORA_TEST_PLANNING_SERVICE_URL'])
    journal = CampaignPreparationJournal(engine)
    try:
        reference = plan.request.document().reference
        if args.stage == 'absent':
            PlanningJournal(engine).register(principal, plan.request)
            assert journal.read(principal, reference) is None
            print(json.dumps({'status': 'absent', 'engagement': reference.model_dump(mode='json')}))
            return
        if args.stage == 'commit-crash':
            journal.register(principal, plan, packet)
            # The transaction committed; deliberately lose acknowledgement and process state.
            os._exit(91)
        if args.stage == 'replay':
            stored = journal.register(principal, plan, packet)
        else:
            stored = journal.read(principal, reference)
        assert stored is not None and stored.record == CampaignPreparation.bind(plan, packet)
        result = {'engagement': reference.model_dump(mode='json'), 'request_sha256': plan.request.sha256,
            'manifest_sha256': stored.record.sha256, 'packet_sha256': stored.record.document().packet.sha256,
            'plan_sha256': stored.record.document().plan_sha256, 'registered_at': stored.registered_at.isoformat(),
            'packet_bytes': len(stored.record.packet.canonical)}
        if args.stage == 'recover':
            assert not args.expected.exists()
            args.expected.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
        else:
            assert result == json.loads(args.expected.read_bytes())
        if args.stage == 'conflict':
            changed = CampaignSlicePlan.from_artifacts(original_artifacts(plan)).with_runtime_unavailable('metadata_denied')
            try:
                journal.register(principal, changed, prepare(changed).packet)
            except ValueError as error:
                assert str(error) == 'campaign_preparation_conflict'
            else:
                raise AssertionError('conflicting preparation replaced history')
            assert journal.read(principal, reference) == stored
        print(json.dumps({'status': 'passed', 'stage': args.stage, **result}))
    finally:
        engine.dispose()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', choices=('absent', 'commit-crash', 'recover', 'read', 'replay', 'conflict'))
    parser.add_argument('--fixture', type=Path, required=True)
    parser.add_argument('--loader', type=Path, required=True)
    parser.add_argument('--expected', type=Path, required=True)
    run(parser.parse_args())
