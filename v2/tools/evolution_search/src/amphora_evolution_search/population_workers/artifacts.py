"""Attempt-scoped, fenced publication with complete declared direct ancestry."""

import hashlib
import uuid

from amphora_contracts_artifacts import ContentDescriptor, DerivationDeclaration, TransformationDescriptor

from ..population.retained import PopulationArtifact
from ..population.specification import canonical
from ..ranking import require


class PopulationArtifacts:
    def __init__(self, client, attempt, implementation, *, transformation_id="population.numeric-steps"):
        self.client, self.attempt, self.implementation = client, attempt, implementation
        self.published = {}
        self.transformation_id = transformation_id

    @property
    def scope(self):
        return self.client.identity.scope

    def read(self, reference):
        require(reference.scope == self.scope and reference.size_bytes <= 262144,
                "population_source_binding")
        self.attempt.refresh()
        content = self.client.read(reference)
        self.attempt.check()
        return PopulationArtifact(reference, content)

    def derivation(self, reference):
        require(reference.scope == self.scope, "population_derivation_scope")
        self.attempt.refresh()
        result = self.client.derivation(reference)
        self.attempt.check()
        return result

    def publish(self, record, schema, parents, label):
        raw = canonical(record)
        require(len(raw) <= 262144, "population_output_bytes")
        references = {}
        # Retain the exact admitted input carrier as well as references inside it.
        sources = tuple(binding.artifact for binding in self.attempt.invocation.inputs)
        for parent in (*sources, *parents):
            require(parent.scope == self.scope, "population_parent_scope")
            require(references.setdefault(parent.artifact_id, parent) == parent, "population_parent_conflict")
        parents = tuple(references[key] for key in sorted(references))
        require(1 <= len(parents) <= 128, "population_direct_ancestry_bound")
        content = ContentDescriptor(sha256=hashlib.sha256(raw).hexdigest(), size_bytes=len(raw),
            media_type="application/json", schema_ref=schema)
        declaration = DerivationDeclaration(transformation=TransformationDescriptor(
            transformation_id=self.transformation_id, version=self.implementation.version,
            sha256=self.implementation.sha256), inputs=parents)
        identity = (content.model_dump_json(), declaration.model_dump_json())
        if label in self.published:
            previous, artifact = self.published[label]
            require(previous == identity, "population_publication_label_conflict")
            self.attempt.check()
            return artifact
        require(len(self.published) < 4096, "population_publication_bound")
        key = uuid.uuid5(uuid.NAMESPACE_URL,
            "amphora.population/publication-v1:" + self.attempt.invocation.attempt_id + ":" + label).hex
        self.attempt.refresh()
        upload = self.client.begin_derived(content, declaration, "begin-" + key, guard=self.attempt.check).upload
        self.attempt.refresh()
        self.client.stream(upload, raw, guard=self.attempt.check)
        self.attempt.refresh()
        finalized = self.client.finalize(upload, "finalize-" + key, guard=self.attempt.check)
        self.attempt.check()
        artifact = PopulationArtifact(finalized.artifact, raw)
        self.published[label] = identity, artifact
        return artifact
