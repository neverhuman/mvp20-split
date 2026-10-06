"""Immutable reviewed graph-specific policy, separate from admission and dispatch."""

import hashlib
from dataclasses import dataclass

from amphora_contracts_campaigns import ActivationPath, parse_execution_plan

from ..compiler.addresses import ActivationAddress
from ..compiler.catalog import canonical
from ..supervision_scope.observations import require
from .records import read_policy
from .scalars import ScalarRule


def address_key(address):
    return tuple(address.scope_path), address.node_id


def authored_node(plan, address):
    body = plan.document.definition.body
    for name in address.scope_path:
        parent = next((node for node in body.nodes if node.node_id == name), None)
        require(parent is not None and parent.kind in {'scatter', 'iterate'}, 'policy_scope_missing')
        body = parent.body
    node = next((node for node in body.nodes if node.node_id == address.node_id), None)
    require(node is not None, 'policy_node_missing')
    return node


def validate_rule(plan, rule, ceilings):
    definition = authored_node(plan, rule.target)
    require(definition.kind == rule.kind, 'policy_target_kind')
    require(bool(rule.fields) == (rule.kind == 'artifact_materialize'), 'policy_fields_for_kind')
    require(len({field.name for field in rule.fields}) == len(rule.fields), 'policy_duplicate_field')
    require(rule.max_requests <= ceilings.max_requests and rule.max_model_calls <= ceilings.max_model_calls,
            'policy_slot_ceiling')
    reads = tuple(address_key(item) for item in rule.reads)
    require(len(set(reads)) == len(reads) and address_key(rule.target) not in reads, 'policy_duplicate_read')
    for read in rule.reads:
        authored_node(plan, read)
        require(rule.target.scope_path[:len(read.scope_path)] == read.scope_path, 'policy_read_occurrence_ambiguous')
    if rule.kind == 'invoke':
        return
    fields = {field.name: field for field in definition.fields}
    scope = next((item for item in plan.document.scopes if item.path == rule.target.scope_path), None)
    require(scope is not None, 'policy_compiled_scope_missing')
    binding = next((item for item in scope.nodes if item.node_id == rule.target.node_id), None)
    require(binding is not None, 'policy_compiled_node_missing')
    inputs = {port.name: port.value_type for port in binding.inputs}
    for field in rule.fields:
        require(field.name in fields and field.name in inputs, 'policy_field_missing')
        require(fields[field.name].mode == 'inline', 'policy_field_not_inline')
        require(inputs[field.name] == field.value_type, 'policy_field_type_mismatch')
        ScalarRule(field)


def normalized(record):
    data = record.model_dump(mode='json')
    data['checkpoints'].sort(key=lambda rule: rule['checkpoint_id'])
    for rule in data['checkpoints']:
        rule['fields'].sort(key=lambda field: field['name'])
        for field in rule['fields']:
            if field['constraint']['kind'] == 'choices':
                field['constraint']['values'].sort(key=canonical)
        rule['reads'].sort(key=lambda item: (item['scope_path'], item['node_id']))
    return canonical(data)


@dataclass(frozen=True)
class ReviewedPolicy:
    canonical: bytes
    plan: object

    def __post_init__(self):
        require(type(self.canonical) is bytes and 0 < len(self.canonical) <= 262144, 'policy_size')
        record = self.document()
        require(normalized(record) == self.canonical, 'noncanonical_policy')
        plan = parse_execution_plan(self.plan.model_dump_json())
        require(hashlib.sha256(canonical(plan.document.model_dump(mode='json'))).hexdigest() == plan.sha256,
                'policy_plan_digest')
        require(record.scope == plan.document.definition.scope and record.plan_sha256 == plan.sha256,
                'policy_plan_binding')
        ids = [rule.checkpoint_id for rule in record.checkpoints]
        targets = [address_key(rule.target) for rule in record.checkpoints]
        require(len(set(ids)) == len(ids) and len(set(targets)) == len(targets), 'policy_duplicate_checkpoint')
        for rule in record.checkpoints:
            validate_rule(plan, rule, record.ceilings)
        object.__setattr__(self, 'plan', plan)

    @classmethod
    def bind(cls, plan, record):
        record = read_policy(record.model_dump_json())
        return cls(normalized(record), plan)

    @classmethod
    def from_bytes(cls, plan, raw):
        return cls(raw, plan)

    def document(self):
        return read_policy(self.canonical)

    @property
    def sha256(self):
        return hashlib.sha256(self.canonical).hexdigest()

    def rule_for(self, path):
        ActivationAddress.for_plan(self.plan, path)
        key = (tuple(item.node_id for item in path.occurrences), path.node_id)
        return next((rule for rule in self.document().checkpoints if address_key(rule.target) == key), None)

    def read_paths(self, path):
        rule = self.rule_for(path)
        require(rule is not None, 'policy_checkpoint_missing')
        return (path, *(ActivationPath(schema_version='2', node_id=read.node_id,
            occurrences=path.occurrences[:len(read.scope_path)]) for read in rule.reads))
