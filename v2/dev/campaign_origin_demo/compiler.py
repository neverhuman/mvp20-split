"""Run only with the isolated Planning interpreter; no peer implementation imports."""
import importlib.util
import json
import os
import sys
from pathlib import Path

from amphora_agent_planning.access import Principal
from amphora_agent_planning.budget import BudgetPolicy
from amphora_agent_planning.campaign_authoring import AuthoringPlan
from amphora_agent_planning.campaign_data_access import CampaignArtifactReader
from amphora_agent_planning.campaign_decisions import CampaignDecisionReview, DecisionDeclaration
from amphora_agent_planning.campaign_dispatch import CompilerSelection
from amphora_agent_planning.campaign_dispatch.dispatcher import CompilerDispatcher
from amphora_agent_planning.campaign_dispatch.journal import CompilerJournal
from amphora_agent_planning.campaign_dispatch.store import CompilerStore
from amphora_agent_planning.campaign_dispatch.progression import CompilerProgression
from amphora_agent_planning.campaign_eligibility import EligibilityConfiguration
from amphora_agent_planning.campaign_exchanges import RuntimeAuthoringClient, RegistryEligibilityClient
from amphora_agent_planning.campaign_origin.reader import CampaignOriginReader
from amphora_agent_planning.campaign_packet import prepare
from amphora_agent_planning.campaign_preparations.journal import CampaignPreparationJournal
from amphora_agent_planning.campaign_proposals import PreparedCampaignProposal
from amphora_agent_planning.campaign_refresh import RefreshCollector
from amphora_agent_planning.context import RequestSnapshot, AttemptBinding
from amphora_agent_planning.persistence.journal import PlanningJournal
from amphora_agent_planning.persistence.budget import BudgetLedger
from amphora_agent_planning.persistence.settlement import SettlementJournal
from amphora_agent_planning.providers import observe
from amphora_agent_planning.providers.port import ProviderReply
from amphora_agent_planning.source_access import DataReader
from amphora_contracts_core import Scope
from amphora_contracts_planning import ProviderUsage, CampaignOriginDraft
from sqlalchemy import create_engine

# Only this test/operator module directory is added, never service source roots.
sys.path.insert(0, str(Path(__file__).parent))
from context import assemble


class DeterministicProposal:
    def __init__(self, value):
        self.raw = json.dumps(value).encode()
        self.calls = 0

    def supports(self, model):
        return model.provider_id == 'deterministic'

    def reply(self, binding):
        self.calls += 1
        return ProviderReply([self.raw], ProviderUsage(input_tokens=0, output_tokens=0,
            accounting_units=0, certainty='reported'))


def compile(case_path):
    assert all(importlib.util.find_spec(name) is None for name in (
        'amphora_campaign_runtime', 'amphora_research', 'amphora_knowledge',
        'amphora_data_artifacts', 'amphora_capability_registry'))
    case = json.loads(case_path.read_bytes())
    output = case_path.parent
    def write(name, value):
        (output / name).write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')
    scope = Scope.model_validate(case['scope'])
    request = RequestSnapshot.from_bytes(json.dumps(case['request']).encode(), actor_id='compiler-demo', scope=scope)
    principal = Principal('compiler-demo', scope, frozenset({'record_requests', 'record_attempts', 'read_attempts', 'read_campaign_origin'}))
    context = request.document().context.model_dump(mode='json')
    budget = BudgetPolicy.from_bytes(json.dumps({**{key: context[key] for key in (
        'model', 'prompt', 'policy', 'output_schema', 'allowed_actions', 'limits')},
        'format': 'planning-budget-policy.v1', 'per_attempt_accounting_units': 1}).encode())
    engine = create_engine(os.environ['ORIGIN_PLANNING_DATABASE'], connect_args={'options': '-c statement_timeout=5000'})
    token = lambda name: os.environ['ORIGIN_' + name.upper() + '_TOKEN']
    endpoints = case['endpoints']
    config = EligibilityConfiguration.bind(owner_id='registry', actor_id='admin',
        policy_sha256=case['eligibility_policy_sha256'], maximum_age_seconds=60)
    store = CompilerStore(engine, 'runtime', 'admin', config)
    journal = CompilerJournal(store)
    try:
        if (output / 'compiler-selection.json').exists():
            selection_id = json.loads((output / 'compiler-selection.json').read_bytes())['selection_id']
            # Resume the retained selection; no fresh provider call or original packet replacement.
            from amphora_agent_planning.metadata_reads import MetadataTransport
            from amphora_agent_planning.registry_access import RegistryReader
            from amphora_agent_planning.runtime_metadata import RuntimeMetadataReader
            from amphora_agent_planning.campaign_research_access import ResearchRecordReader, CampaignResearchTransport
            registry = RegistryReader(MetadataTransport('registry', endpoints['registry'], token('registry')))
            runtime = RuntimeMetadataReader(MetadataTransport('runtime', endpoints['runtime'], token('runtime')))
            research = ResearchRecordReader(CampaignResearchTransport(endpoints['research'], token('research')))
        else:
            attempts = PlanningJournal(engine)
            attempts.register(principal, request)
            attempt = AttemptBinding(request, 1)
            assert attempts.read_attempt(principal, attempt.reference()) is None, (
                'Original attempt already exists without a retained helper selection; inspect history, do not recapture')
            plan, registry, runtime, research = assemble(case, request)
            packet = prepare(plan)
            assert packet.failure is None and packet.packet is not None
            retained = CampaignPreparationJournal(engine).register(principal, plan, packet.packet)
            BudgetLedger(engine).reserve(principal, attempt, budget)
            provider = DeterministicProposal(case['proposal'])
            observed = observe(attempt, provider)
            attempts.record(principal, attempt, observed)
            SettlementJournal(engine).settle(principal, attempt)
            proposal = PreparedCampaignProposal.bind(retained.record, attempt, observed)
            declaration = DecisionDeclaration.from_bytes(json.dumps(case['declaration']).encode())
            review = CampaignDecisionReview.bind(proposal, declaration, budget)
            assert review.next_step == 'compile_future_draft'
            authoring = AuthoringPlan.bind(review, budget, owner_id='runtime', actor_id='admin')
            selection = CompilerSelection.bind(principal, authoring, config)
            store.register(principal, selection)
            selection_id = selection.effect_id
            write('compiler-selection.json', {'selection_id': selection_id, 'selection_sha256': selection.sha256,
                'provider': 'deterministic', 'fixture_calls': provider.calls, 'paid_provider_calls': 0})
        refresh = RefreshCollector(artifacts=CampaignArtifactReader(DataReader(endpoints['artifact'], token('artifact'))),
            research=research, registry=registry, runtime=runtime)
        dispatcher = CompilerDispatcher(journal, refresh,
            RuntimeAuthoringClient('runtime', 'admin', endpoints['runtime'], token('runtime')),
            RegistryEligibilityClient('registry', 'admin', endpoints['registry'], token('registry')))
        for turn in range(12):
            result = CompilerProgression(dispatcher).advance(principal, selection_id)
            operation = None if result.dispatch is None else result.dispatch.operation
            write('compiler-progress.json', {'turn': turn, 'stage': result.stage, 'terminal': result.terminal,
                'pause_reason': result.pause_reason, 'state': None if operation is None else operation.progress.state})
            if result.terminal:
                assert operation is not None and operation.progress.state == 'compiled', 'Compilation did not succeed'
                selected = journal.selected(principal, selection_id)
                retained = journal.context(principal, selected.selection)
                effect, _ = retained.save()
                saved = journal.read(principal, selection_id, effect.effect_id).progress.observation.outcome
                draft = saved.readback
                expected = CampaignOriginDraft(scope=scope, draft_id=draft.head.draft_id,
                    revision=draft.head.revision, content_sha256=draft.head.content_sha256)
                origin = CampaignOriginReader(engine).read(principal, expected)
                assert origin is not None and origin.document().origin.knowledge.status == 'available'
                write('compiler-origin.json', origin.document().model_dump(mode='json'))
                write('draft-record.json', draft.model_dump(mode='json'))
                write('compiler-completed.json', {'status': 'compiled', 'draft': expected.model_dump(mode='json'),
                    'origin_sha256': origin.document().origin_sha256, 'paid_provider_calls': 0})
                return
        raise AssertionError('Compiler did not reach a terminal state; retained selection can be resumed')
    finally:
        engine.dispose()


if __name__ == '__main__':
    compile(Path(sys.argv[1]))
