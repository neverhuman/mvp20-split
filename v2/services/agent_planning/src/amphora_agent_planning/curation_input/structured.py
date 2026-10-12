"""Closed provider generation schema; never an output repair or acceptance authority."""
import hashlib
import json
from dataclasses import dataclass

from amphora_contracts_campaign_curation import CampaignCurationDraft
from ..campaign_context.records import canonical
from ..context.policy import require


@dataclass(frozen=True)
class GenerationSchema:
    canonical: bytes

    @classmethod
    def bind(cls, schema):
        definitions = schema.get('$defs', {})
        allowed = {'$defs', '$ref', 'type', 'properties', 'required', 'additionalProperties',
                   'items', 'anyOf', 'oneOf', 'const', 'enum', 'pattern', 'minLength',
                   'maxLength', 'minimum', 'maximum', 'minItems', 'maxItems'}
        metadata = {'title', 'description', 'default', 'discriminator'}
        def project(node):
            require(type(node) is dict and not set(node) - allowed - metadata,
                    'curation_generation_schema_keyword')
            value = {key: child for key, child in node.items() if key not in metadata}
            if '$ref' in value:
                ref = value['$ref']
                require(type(ref) is str and ref.startswith('#/$defs/') and
                        ref[8:] in definitions, 'curation_generation_schema_reference')
            if 'oneOf' in value:
                literals = []
                for branch in value['oneOf']:
                    record = definitions.get(branch.get('$ref', '')[8:], branch)
                    literals.append({key: prop['const'] for key, prop in record.get('properties', {}).items()
                                     if 'const' in prop and key in record.get('required', [])})
                common = set.intersection(*(set(row) for row in literals)) if literals else set()
                require(any(len({canonical(row[key]) for row in literals}) == len(literals)
                            for key in common), 'curation_generation_schema_union')
                value['anyOf'] = value.pop('oneOf')
            for key in ('$defs', 'properties'):
                if key in value: value[key] = {name: project(child) for name, child in value[key].items()}
            if 'items' in value: value['items'] = project(value['items'])
            if 'anyOf' in value: value['anyOf'] = [project(child) for child in value['anyOf']]
            if value.get('type') == 'object':
                require(value.get('additionalProperties') is False, 'curation_generation_schema_open_object')
                value['required'] = list(value.get('properties', {}))
            return value
        require(schema.get('type') == 'object' and 'anyOf' not in schema and 'oneOf' not in schema,
                'curation_generation_schema_root')
        return cls(canonical(project(schema)))

    @classmethod
    def reviewed(cls):
        return cls.bind(CampaignCurationDraft.model_json_schema(mode='validation'))

    @property
    def sha256(self):
        return hashlib.sha256(self.canonical).hexdigest()

    def format(self):
        return {'type': 'json_schema', 'name': 'campaign_curation_v3', 'strict': True,
                'schema': json.loads(self.canonical)}
