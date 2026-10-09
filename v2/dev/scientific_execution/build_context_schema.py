"""Build the additive demo context schema from pinned public Knowledge definitions."""
import hashlib
import json
from pathlib import Path


def build():
    here = Path(__file__).parent
    studio = here.parents[1] / 'studio'
    schema = json.loads((here / 'context.schema.json').read_bytes())
    public = json.loads((studio / 'src/contracts/generated/knowledge/schemas.json').read_bytes())['search_request']
    schema['$defs'] = public['$defs']
    schema['required'].append('knowledge')
    schema['properties']['format']['const'] = 'amphora.demo-campaign-context.v2'
    identifier = {'type': 'string', 'minLength': 1, 'maxLength': 128}
    schema['properties']['knowledge'] = {
        'type': 'object', 'additionalProperties': False,
        'required': ['role', 'revision', 'methods'],
        'properties': {
            'role': {'const': 'planning_context'},
            'revision': {'$ref': '#/$defs/DomainRevisionRef'},
            'methods': {'type': 'array', 'minItems': 1, 'maxItems': 32,
                'items': {'type': 'object', 'additionalProperties': False,
                    'required': ['method_id', 'entity_ids'],
                    'properties': {'method_id': identifier,
                        'entity_ids': {'type': 'array', 'minItems': 1, 'maxItems': 32,
                            'uniqueItems': True, 'items': identifier}}}}}}
    body = (json.dumps(schema, indent=2) + '\n').encode()
    for destination in (here, studio / 'src/page_models/campaign_flow'):
        (destination / 'context.v2.schema.json').write_bytes(body)
    pin = "export const knowledgeContextSchema = {schema_id:'demo.campaign-knowledge-context',version:'1',sha256:'" + hashlib.sha256(body).hexdigest() + "'} as const;\n"
    (studio / 'src/page_models/campaign_flow/knowledge_schema_pin.ts').write_text(pin, encoding='utf-8', newline='\n')


if __name__ == '__main__':
    build()
