"""Synthetic material provenance and bounded mapping; no chemical modeling or I/O."""

from dataclasses import dataclass
import hashlib

from amphora_contracts_population import (
    MaterialMappingExclusion, MaterialMappingItem, MaterialMappingPage, MaterialMappingPair,
    MaterialMappingPolicy, MaterialMappingManifest, MaterialState, ProcessBinding, ProcessContext, ProcessDerivation,
    MembershipPageReference,
    population_record_schema,
)

from .validation import require, consistent_references, PopulationArtifact, canonical


@dataclass(frozen=True)
class BoundMaterial:
    artifact: PopulationArtifact
    record: MaterialState

    @classmethod
    def verify(cls, artifact, context):
        context = ProcessContext.model_validate_json(context.model_dump_json())
        record = artifact.decode(MaterialState, population_record_schema("population.material-state"), context.generation.scope)
        require(len(canonical(record)) <= 8192 and record.context == context, "material_context_or_bytes")
        refs = (record.representation, record.conditions, *((record.composition,) if record.composition else ()))
        require(all(r.scope == context.generation.scope for r in refs), "material_reference_scope")
        consistent_references((artifact.reference, *refs))
        require(len(set(record.unknowns)) == len(record.unknowns), "material_unknown_duplicate")
        require(record.amount is None or bool(record.amount.unit.strip()), "material_amount_unit")
        require(record.phase is None or bool(record.phase.strip()), "material_phase")
        return cls(artifact, record)


@dataclass(frozen=True)
class MaterialDerivation:
    record: ProcessDerivation
    inputs: tuple[BoundMaterial, ...]
    outputs: tuple[BoundMaterial, ...]

    @classmethod
    def verify(cls, artifact, context, binding, input_materials, output_materials):
        record = artifact.decode(ProcessDerivation, population_record_schema("population.process-derivation"), context.generation.scope)
        result=cls.from_record(record,context,binding,input_materials,output_materials)
        consistent_references((artifact.reference,record.conditions,
            *(item.artifact.reference for item in (*result.inputs,*result.outputs))))
        return result

    @classmethod
    def from_record(cls,record,context,binding,input_materials,output_materials):
        """Validate record semantics; Runtime acceptance is checked by its consumer."""
        binding = ProcessBinding.model_validate_json(binding.model_dump_json())
        record = ProcessDerivation.model_validate_json(record.model_dump_json())
        require(len(canonical(record)) <= 8192 and record.context == context, "derivation_context_or_bytes")
        require(record.tool == binding.tool and record.producer.run_id == context.generation.run_id, "derivation_producer_binding")
        require(record.conditions.scope == context.generation.scope, "derivation_conditions_scope")
        require(len(set(record.unknowns)) == len(record.unknowns), "derivation_unknown_duplicate")
        inputs = cls._ports(context, binding.inputs, record.inputs, record.absent, input_materials, True)
        outputs = cls._ports(context, binding.outputs, record.outputs, (), output_materials, False)
        input_refs = {m.artifact.reference.artifact_id for m in inputs}
        require(all(m.artifact.reference.artifact_id not in input_refs for m in outputs), "derivation_output_not_new")
        input_states = {(m.record.state_id, m.record.revision) for m in inputs}
        require(all((m.record.state_id, m.record.revision) not in input_states for m in outputs), "derivation_state_not_new")
        require(len({(m.record.state_id, m.record.revision) for m in outputs}) == len(outputs), "derivation_output_duplicate")
        for output in outputs:
            revisions = [m.record.revision for m in inputs if m.record.state_id == output.record.state_id]
            require(not revisions or output.record.revision > max(revisions), "derivation_revision_regression")
            require(output.record.conditions == record.conditions, "derivation_output_conditions")
        consistent_references((record.conditions, *(m.artifact.reference for m in (*inputs, *outputs))))
        return cls(record, inputs, outputs)

    @staticmethod
    def _ports(context, ports, uses, absent, materials, require_absence):
        by_port = {p.port: p for p in ports}
        require(len(by_port) == len(ports), "derivation_port_duplicate")
        require(type(materials) is tuple and len(materials) == len(uses), "derivation_material_coverage")
        require(tuple((u.port, u.ordinal) for u in uses) == tuple(sorted(set((u.port, u.ordinal) for u in uses))),
                "derivation_port_order")
        missing = {a.port for a in absent}
        require(len(missing) == len(absent) and missing <= by_port.keys(), "derivation_absence")
        checked = []
        for use, material in zip(uses, materials, strict=True):
            require(use.port in by_port and use.material == material.reference, "derivation_material_binding")
            bound = BoundMaterial.verify(material, context)
            require(bound.record.representation.schema_ref == by_port[use.port].representation, "derivation_representation")
            checked.append(bound)
        for name, port in by_port.items():
            ordinals = tuple(u.ordinal for u in uses if u.port == name)
            require(ordinals == tuple(range(len(ordinals))) and len(ordinals) <= port.maximum, "derivation_port_cardinality")
            if port.required:
                require(bool(ordinals) and name not in missing, "derivation_required_port")
            elif require_absence:
                require((not ordinals) == (name in missing), "derivation_optional_absence")
        return tuple(checked)


@dataclass(frozen=True)
class MaterialMapping:
    context: ProcessContext
    policy: MaterialMappingPolicy
    pairs: tuple[MaterialMappingPair, ...]
    excluded: tuple[MaterialMappingExclusion, ...]

    @classmethod
    def create(cls, context, policy, left, right, materials):
        context = ProcessContext.model_validate_json(context.model_dump_json())
        policy = MaterialMappingPolicy.model_validate_json(policy.model_dump_json())
        require(type(left) is tuple and type(right) is tuple and len(left) <= 10000 and len(right) <= 10000,
                "mapping_input_count")
        left = tuple(MaterialMappingItem.model_validate_json(i.model_dump_json()) for i in left)
        right = tuple(MaterialMappingItem.model_validate_json(i.model_dump_json()) for i in right)
        for side in (left, right):
            require(len({i.key for i in side}) == len(side), "mapping_key_duplicate")
        require(type(materials) is tuple, "mapping_material_tuple")
        by_id = {m.reference.artifact_id: m for m in materials}
        require(len(by_id) == len(materials), "mapping_material_duplicate")
        require(set(by_id) == {i.state.artifact_id for i in (*left, *right)}, "mapping_material_coverage")
        require(sum(len(m.content) for m in materials) <= 67108864, "mapping_source_bytes")
        for material in materials:
            BoundMaterial.verify(material, context)
        for item in (*left, *right):
            require(by_id[item.state.artifact_id].reference == item.state, "mapping_material_binding")
            require(len(canonical(item)) <= 8192, "mapping_input_bytes")
        excluded = []
        if policy.mode == "pairwise":
            require(not policy.cartesian_opt_in and policy.unmatched == "reject" and len(left) == len(right), "mapping_pairwise_cardinality")
            count = len(left)
            iterator = zip(left, right, strict=True)
        elif policy.mode == "keyed":
            require(not policy.cartesian_opt_in, "mapping_unexpected_cartesian")
            a, b = {i.key: i for i in left}, {i.key: i for i in right}
            extra = sorted(a.keys() ^ b.keys())
            require(not extra or policy.unmatched == "retain_excluded", "mapping_unmatched_key")
            for key in extra:
                side, item = ("left", a[key]) if key in a else ("right", b[key])
                excluded.append(MaterialMappingExclusion(side=side, key=key, state=item.state, reason_code="unmatched_key"))
            count = len(a.keys() & b.keys())
            iterator = ((a[key], b[key]) for key in sorted(a.keys() & b.keys()))
        else:
            require(policy.cartesian_opt_in and policy.unmatched == "reject", "mapping_cartesian_opt_in")
            count = len(left) * len(right)
            iterator = ((a, b) for a in left for b in right)
        require(count <= policy.maximum_outputs, "mapping_output_bound")
        pairs = tuple(MaterialMappingPair(left_key=a.key, right_key=b.key, left=a.state, right=b.state) for a, b in iterator)
        result = cls(context, policy, pairs, tuple(excluded))
        result.pages()  # Enforce total retained byte/page closure before returning.
        return result

    def pages(self):
        pages, pairs, excluded = [], [], []
        def page():
            return MaterialMappingPage(schema_version="1", profile="synthetic-process-mapping-page-v1",
                context=self.context, ordinal=len(pages), pairs=tuple(pairs), excluded=tuple(excluded))
        for kind, rows in (("pairs", self.pairs), ("excluded", self.excluded)):
            for row in rows:
                require(len(canonical(row)) <= 8192, "mapping_row_bytes")
                target = pairs if kind == "pairs" else excluded
                if len(pairs) + len(excluded) == 64:
                    pages.append(page()); pairs, excluded = [], []
                    target = pairs if kind == "pairs" else excluded
                target.append(row)
                if len(canonical(page())) > 131072:
                    target.pop()
                    require(bool(pairs or excluded), "mapping_page_bytes")
                    pages.append(page()); pairs, excluded = [], []
                    (pairs if kind == "pairs" else excluded).append(row)
        if pairs or excluded:
            pages.append(page())
        require(len(pages) <= 512 and sum(len(canonical(p)) for p in pages) <= 67108864, "mapping_closure_bytes")
        return tuple(pages)

    def manifest(self, left, right, references):
        """Bind separately verified ordered source manifests; no authority from refs."""
        from amphora_contracts_core import ArtifactRef
        left = ArtifactRef.model_validate_json(left.model_dump_json())
        right = ArtifactRef.model_validate_json(right.model_dump_json())
        require(left.scope == right.scope == self.context.generation.scope, "mapping_source_scope")
        require(type(references) is tuple, "mapping_page_tuple")
        references = tuple(MembershipPageReference.model_validate_json(r.model_dump_json()) for r in references)
        pages = self.pages()
        require(len(references) == len(pages), "mapping_page_coverage")
        require(len({r.artifact.artifact_id for r in references}) == len(references), "mapping_page_duplicate")
        for ref, page in zip(references, pages, strict=True):
            raw = canonical(page)
            require(ref.ordinal == page.ordinal and ref.members == len(page.pairs) + len(page.excluded), "mapping_page_count")
            require(ref.artifact.scope == self.context.generation.scope
                    and ref.artifact.schema_ref == population_record_schema("population.material-mapping-page")
                    and ref.artifact.media_type == "application/json", "mapping_page_binding")
            require(ref.artifact.sha256 == hashlib.sha256(raw).hexdigest() and ref.artifact.size_bytes == len(raw), "mapping_page_digest")
        consistent_references((left, right, *(r.artifact for r in references)))
        record = MaterialMappingManifest(schema_version="1", profile="synthetic-process-mapping-manifest-v1",
            context=self.context, policy=self.policy, left=left, right=right, pair_count=len(self.pairs),
            excluded_count=len(self.excluded), pages=references)
        require(len(canonical(record)) <= 262144, "mapping_manifest_bytes")
        return record

    def verify_manifest(self, artifact, left, right, payloads):
        record = artifact.decode(MaterialMappingManifest, population_record_schema("population.material-mapping-manifest"),
                                 self.context.generation.scope)
        require(record == self.manifest(left, right, record.pages), "mapping_manifest_replay")
        require(type(payloads) is tuple and payloads == tuple(canonical(p) for p in self.pages()), "mapping_page_replay")
        return record
