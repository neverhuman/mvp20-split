"""Replacement ownership and conflicting edit targets are explicit, not prose."""

from collections import defaultdict


class CandidateSelection:
    def __init__(self, draft, findings):
        self.groups = {name: tuple(getattr(draft, name)) for name in ("entities", "assertions")}
        self.edits = tuple(getattr(draft, "edits", ()))
        self.findings, self.replacements, self.paths = findings, defaultdict(list), {}
        self.blocked = set()
        for group, items in (*self.groups.items(), ("edits", self.edits)):
            identities = defaultdict(list)
            for index, item in enumerate(items):
                path = f"/{group}/{index}"
                self.paths[(group, index)] = path
                identities[item.local_id].append(path)
            for paths in identities.values():
                if len(paths) > 1:
                    self.reject(paths, "duplicate_candidate_identity")
        targets = defaultdict(list)
        for index, edit in enumerate(self.edits):
            path = self.paths[("edits", index)]
            if edit.operation in {"correct_assertion", "revise_entity_context"}:
                group = "assertions" if edit.operation == "correct_assertion" else "entities"
                self.replacements[(group, edit.replacement_local_id)].append(path)
                if not any(item.local_id == edit.replacement_local_id for item in self.groups[group]):
                    self.reject((path,), "replacement_candidate_missing")
            references = (edit.source, edit.target) if edit.operation == "merge_entities" else (
                edit.assertion if edit.operation == "retract_assertion" else edit.prior,)
            for ref in references:
                kind, key = ("entity", ref.entity_id) if hasattr(ref, "entity_id") else ("assertion", ref.assertion_id)
                targets[(kind, key)].append(path)
        for paths in targets.values():
            if len(paths) > 1:
                self.reject(paths, "conflicting_edit_targets")
        for key, paths in self.replacements.items():
            if len(paths) > 1:
                self.reject(paths, "conflicting_replacement_ownership")
                for index, item in enumerate(self.groups[key[0]]):
                    if item.local_id == key[1]:
                        self.reject((self.paths[(key[0], index)],), "conflicting_replacement_ownership")

    def reject(self, paths, code):
        self.blocked.update(paths)
        for path in paths:
            self.findings.add(path, code)

    def available(self, group, index):
        return self.paths[(group, index)] not in self.blocked

    def owned(self, group, local_id):
        return (group, local_id) in self.replacements

    def replacement(self, group, local_id):
        matches = [(index, item) for index, item in enumerate(self.groups[group]) if item.local_id == local_id]
        if len(matches) != 1 or not self.available(group, matches[0][0]):
            raise ValueError("replacement_candidate_unresolved")
        return matches[0]
