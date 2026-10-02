"""Entity history and explicit aliases preserve both sides of every merge."""

from dataclasses import dataclass

from amphora_contracts_knowledge import DomainEntity, EntityAlias

from .canonical import KnowledgeError


@dataclass(frozen=True)
class EntityHistory:
    records: tuple[DomainEntity, ...] = ()
    aliases: tuple[EntityAlias, ...] = ()

    def find(self, reference):
        record = next((r for r in self.records if r.reference == reference), None)
        if record is None:
            raise KnowledgeError("unknown_entity_revision")
        return record

    def current(self, reference):
        record = self.find(reference)
        if any(r.reference.entity_id == reference.entity_id and r.reference.revision > reference.revision
               for r in self.records):
            raise KnowledgeError("stale_entity_revision")
        if any(a.source.entity_id == reference.entity_id for a in self.aliases):
            raise KnowledgeError("entity_already_merged")
        return record

    def add(self, record):
        if any(r.reference.entity_id == record.reference.entity_id for r in self.records):
            raise KnowledgeError("entity_identity_reuse")
        if record.reference.revision != 1 or record.supersedes is not None:
            raise KnowledgeError("invalid_entity_genesis")
        return EntityHistory(self.records + (record,), self.aliases)

    def revise_context(self, prior, replacement):
        original = self.current(prior)
        if (replacement.supersedes != prior or replacement.reference.graph != prior.graph
                or replacement.reference.entity_id != prior.entity_id or replacement.reference.revision != prior.revision + 1):
            raise KnowledgeError("invalid_entity_successor")
        if replacement.entity_type != original.entity_type or replacement.label != original.label:
            raise KnowledgeError("context_edit_changes_identity")
        return EntityHistory(self.records + (replacement,), self.aliases)

    def merge(self, source, target, change_id):
        left, right = self.current(source), self.current(target)
        if source.entity_id == target.entity_id or left.entity_type != right.entity_type:
            raise KnowledgeError("invalid_entity_merge")
        alias = EntityAlias(source=source, target=target, change_id=change_id)
        return EntityHistory(self.records, self.aliases + (alias,))

    def resolve(self, reference):
        self.find(reference)
        visited = set()
        while True:
            if reference.entity_id in visited:
                raise KnowledgeError("alias_cycle")
            visited.add(reference.entity_id)
            alias = next((a for a in self.aliases if a.source.entity_id == reference.entity_id), None)
            if alias is None:
                return reference
            self.find(alias.target)
            reference = alias.target
