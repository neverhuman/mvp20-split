"""Installed client compatibility with actual owners; synthetic proposals only."""

import json
import os
from datetime import UTC, datetime
from pathlib import Path

import pytest
from amphora_agent_planning.campaign_authoring import AuthoringPlan
from amphora_agent_planning.campaign_decisions import CampaignDecisionReview
from amphora_agent_planning.campaign_eligibility import (
    EligibilityConfiguration,
    EligibilityObservation,
)
from amphora_agent_planning.campaign_eligibility.request import EligibilityRequest
from amphora_agent_planning.campaign_exchanges import (
    CompilerWindow,
    ExchangeDenied,
    RegistryEligibilityClient,
    RuntimeAuthoringClient,
)
from amphora_agent_planning.registry_access import ObservedRelease
from amphora_contracts_core import Scope
from amphora_contracts_tools import ReleaseSnapshot

from ..campaign_decisions.test_policy import fixture


@pytest.mark.skipif('COMPILER_OWNER_CASE' not in os.environ, reason='Actual-owner fixture opt-in')
def test_installed_compiler_owner_compatibility():
    case = json.loads(Path(os.environ['COMPILER_OWNER_CASE']).read_bytes())
    scope = Scope.model_validate(case['scope'])
    def numeric(value):
        value['candidate']['definition']['body'] = {
            'inputs': [], 'outputs': [{'name': 'result', 'value_type': {'kind': 'scalar', 'scalar': 'number', 'unit': '1'}}],
            'nodes': [{'kind': 'finish', 'node_id': 'finish', 'outputs': [
                {'port': 'result', 'source': {'kind': 'number', 'value': 1.25, 'unit': '1'}}]}], 'edges': []}

    proposal, declaration, budget = fixture(scope=scope, change=numeric)
    authoring = AuthoringPlan.bind(CampaignDecisionReview.bind(proposal, declaration, budget), budget,
                                  owner_id='fixture-runtime', actor_id='fixture')
    runtime = RuntimeAuthoringClient('fixture-runtime', 'fixture', os.environ['COMPILER_RUNTIME'], os.environ['CTX_TOKEN'])
    save = authoring.save()
    # This is a test-owned invocation of transport primitives, not a production
    # coordinator. The production journal/fence remains a subsequent gate.
    saved = runtime.readback(runtime.submit(save, CompilerWindow('runtime'), guard=lambda: None), CompilerWindow('runtime'))
    assert saved.status == 'saved' and saved.readback.head.revision == 1
    assert runtime.readback(runtime.receipt(save, CompilerWindow('runtime')), CompilerWindow('runtime')) == saved
    validate = authoring.validate(saved)
    compiled = runtime.readback(runtime.submit(validate, CompilerWindow('runtime'), guard=lambda: None), CompilerWindow('runtime'))
    assert compiled.status == 'compiled' and compiled.readback.structurally_valid, compiled.readback.findings
    assert runtime.readback(runtime.receipt(validate, CompilerWindow('runtime')), CompilerWindow('runtime')) == compiled
    # The original fixture needs an unconfigured projection schema. Runtime
    # may store its validation, but Planning must retain structural_invalid.
    original, bounds, accounting = fixture(scope=scope)
    invalid_plan = AuthoringPlan.bind(CampaignDecisionReview.bind(original, bounds, accounting), accounting,
                                     owner_id='fixture-runtime-invalid', actor_id='fixture')
    invalid_client = RuntimeAuthoringClient('fixture-runtime-invalid', 'fixture', os.environ['COMPILER_RUNTIME'], os.environ['CTX_TOKEN'])
    invalid_saved = invalid_client.readback(invalid_client.submit(invalid_plan.save(), CompilerWindow('runtime'),
        guard=lambda: None), CompilerWindow('runtime'))
    invalid = invalid_client.readback(invalid_client.submit(invalid_plan.validate(invalid_saved), CompilerWindow('runtime'),
        guard=lambda: None), CompilerWindow('runtime'))
    assert invalid.status == 'structural_invalid' and invalid.readback.findings
    denied = RuntimeAuthoringClient('fixture-runtime', 'fixture', os.environ['COMPILER_RUNTIME'], os.environ['CTX_DENIED'])
    with pytest.raises(ExchangeDenied):
        denied.receipt(save, CompilerWindow('runtime'))

    config = EligibilityConfiguration.bind(owner_id='fixture-registry', actor_id='fixture', policy_sha256=case['policy_sha256'],
                                           maximum_age_seconds=60)
    selected = ObservedRelease.bind(ReleaseSnapshot.model_validate_json(json.dumps(case['release'])), scope)
    request = EligibilityRequest.bind(config, 'original', proposal.attempt, selected, 'synthetic-tests')
    registry = RegistryEligibilityClient('fixture-registry', 'fixture', os.environ['COMPILER_REGISTRY'], os.environ['CTX_TOKEN'])
    receipt = registry.resolve('fixture-registry', request.command, CompilerWindow('registry'), guard=lambda: None)
    observed = EligibilityObservation.bind(request, receipt)
    assert observed.status == 'candidate', receipt.model_dump(mode='json')
    if case['stage'] == 'original':
        observed.require_fresh(datetime.now(UTC))
    # Repeating the same check must return historical bytes, even after drain.
    assert registry.resolve('fixture-registry', request.command, CompilerWindow('registry'), guard=lambda: None) == receipt
    result = {'save': saved.receipt.model_dump(mode='json'), 'saved': saved.readback.model_dump(mode='json'),
              'validation': compiled.receipt.model_dump(mode='json'), 'compiled': compiled.readback.model_dump(mode='json'),
              'eligibility': receipt.model_dump(mode='json'), 'invalid': invalid.readback.model_dump(mode='json'),
              'save_command': save.canonical.decode(),
              'validate_command': validate.canonical.decode(), 'resolve_command': request.command.canonical_bytes.decode()}
    if case['stage'] == 'drained':
        fresh = EligibilityRequest.bind(config, 'after-drain', proposal.attempt, selected, 'synthetic-tests')
        negative = EligibilityObservation.bind(fresh, registry.resolve('fixture-registry', fresh.command,
            CompilerWindow('registry'), guard=lambda: None))
        assert negative.status == 'rejected' and negative.receipt.reason_code == 'release_not_active'
    Path(os.environ['COMPILER_OWNER_RESULT']).write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
