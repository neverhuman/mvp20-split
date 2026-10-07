"""Owner-local no-SQL exporter for reviewed synthetic live checkpoint materials."""

import json
import os
import sys
from pathlib import Path

from amphora_agent_planning.campaign_packet_profiles import reviewed_instructions
from amphora_agent_planning.checkpoint_budget import CheckpointAllowance
from amphora_agent_planning.checkpoint_input import checkpoint_tokenizer_reference
from amphora_agent_planning.openai_provider.pricing import MODEL
from amphora_agent_planning.supervision_execution.budget_template import ReviewedBudgetTemplate
from amphora_contracts_planning import checkpoint_draft_schema


def main():
    assert not any('DATABASE_URL' in key or 'API_KEY' in key for key in os.environ)
    output = Path(sys.argv[2])
    if sys.argv[1] == 'profile':
        (output / 'prompt.txt').write_bytes(reviewed_instructions())
        record = {'model': MODEL, 'tokenizer': checkpoint_tokenizer_reference('2').model_dump(mode='json'),
                  'output_schema': checkpoint_draft_schema().model_dump(mode='json')}
        (output / 'planning-profile.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
    elif sys.argv[1] == 'measure':
        from amphora_agent_planning.campaign_artifact_context import CampaignArtifactContextReader
        from amphora_agent_planning.campaign_packet.assembly import original_artifacts
        from amphora_agent_planning.campaign_packet.render import render
        from amphora_agent_planning.campaign_packet_profiles import CampaignInstructions, PacketBudget
        from amphora_agent_planning.campaign_slice_plan import CampaignSlicePlan
        from amphora_agent_planning.context import RequestSnapshot
        from amphora_agent_planning.source_access.transport import DataReader
        from amphora_contracts_supervision import CheckpointRequest

        request = CheckpointRequest.model_validate_json((output / 'checkpoint-request.json').read_bytes()).planning_request
        bound = RequestSnapshot.bind(request, actor_id=request.actor_id, scope=request.reference.scope)
        data = DataReader(os.environ['PUBLIC_DATA_ENDPOINT'], os.environ['PUBLIC_DATA_TOKEN'])
        projection = CampaignArtifactContextReader(data).read(bound).projection
        plan = CampaignSlicePlan.from_artifacts(projection)
        artifacts = original_artifacts(plan)
        prompt = next(item for item in artifacts.items if 'prompt' in item.planned.roles)
        instructions = CampaignInstructions.bind(bound, prompt.planned.reference, prompt.body)
        included = tuple(index for index, row in enumerate(plan.slices) if row.required)
        packet = render(plan, instructions, included)
        fit = PacketBudget.bind(bound).inspect(packet)
        record = {'fit': fit.document(), 'artifacts': [
            {'roles': item.planned.roles, 'bytes': len(item.body) if item.body is not None else None}
            for item in artifacts.items]}
        (output / 'measured.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
        print(json.dumps(record))
    else:
        record = json.loads((output / 'template-input.json').read_bytes())
        template = ReviewedBudgetTemplate.from_bytes(json.dumps(record).encode())
        required = CheckpointAllowance.cost(template.document().model, template.document().limits)
        assert template.document().per_attempt_accounting_units >= required
        (output / 'template.json').write_bytes(template.canonical)
        print(json.dumps({'template_sha256': template.sha256, 'required_nanodollars': required}))


if __name__ == '__main__':
    main()
