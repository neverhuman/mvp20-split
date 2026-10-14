import pytest
from amphora_contracts_population import MaterialMappingItem, MaterialMappingPolicy, MembershipPageReference, population_record_schema
from amphora_process_mapping import MaterialMapping, canonical


def policy(mode="pairwise", maximum=10, unmatched="reject", opt_in=False):
    return MaterialMappingPolicy(mode=mode, unmatched=unmatched, cartesian_opt_in=opt_in, maximum_outputs=maximum)


def setup(factory):
    context, _, _, _, material = factory
    materials = tuple(material(name) for name in ("a", "b", "c", "d"))
    items = tuple(MaterialMappingItem(key=key, state=m.reference) for key, m in zip(("z", "a", "a", "z"), materials))
    return context, items[:2], items[2:], materials


def test_pairwise_declared_order_differs_from_keyed_identity(material_factory):
    context, left, right, materials = setup(material_factory)
    paired = MaterialMapping.create(context, policy(), left, right, materials)
    keyed = MaterialMapping.create(context, policy("keyed"), left, right, materials)
    assert [(p.left_key, p.right_key) for p in paired.pairs] == [("z", "a"), ("a", "z")]
    assert [(p.left_key, p.right_key) for p in keyed.pairs] == [("a", "a"), ("z", "z")]
    assert keyed == MaterialMapping.create(context, policy("keyed"), tuple(reversed(left)), tuple(reversed(right)), materials)


def test_unmatched_keys_retained_and_no_silent_truncation(material_factory):
    context, left, right, materials = setup(material_factory)
    right = right[:1]; materials = materials[:3]
    with pytest.raises(ValueError, match="mapping_pairwise_cardinality"):
        MaterialMapping.create(context, policy(), left, right, materials)
    with pytest.raises(ValueError, match="mapping_unmatched_key"):
        MaterialMapping.create(context, policy("keyed"), left, right, materials)
    mapped = MaterialMapping.create(context, policy("keyed", unmatched="retain_excluded"), left, right, materials)
    assert len(mapped.pairs) == 1 and mapped.excluded[0].key == "z" and mapped.excluded[0].side == "left"


def test_cartesian_requires_opt_in_and_preflight_bound(material_factory):
    context, left, right, materials = setup(material_factory)
    with pytest.raises(ValueError, match="mapping_cartesian_opt_in"):
        MaterialMapping.create(context, policy("cartesian"), left, right, materials)
    with pytest.raises(ValueError, match="mapping_output_bound"):
        MaterialMapping.create(context, policy("cartesian", maximum=3, opt_in=True), left, right, materials)
    assert len(MaterialMapping.create(context, policy("cartesian", maximum=4, opt_in=True), left, right, materials).pairs) == 4


def test_mapping_cross_candidate_batch_and_generation_reject(material_factory):
    context, left, right, materials = setup(material_factory)
    for changed in (context.model_copy(update={"candidate_id": "f" * 64}),
                    context.model_copy(update={"process_batch_id": "other"}),
                    context.model_copy(update={"generation": context.generation.model_copy(update={"run_id": "other"})})):
        with pytest.raises(ValueError, match="material_context_or_bytes"):
            MaterialMapping.create(changed, policy(), left, right, materials)
    with pytest.raises(ValueError, match="mapping_key_duplicate"):
        MaterialMapping.create(context, policy(), (left[0], left[0]), right, materials)


def test_mapping_pages_and_manifest_detect_valid_hash_false_policy(material_factory):
    context, schema, _, artifact, material = material_factory
    materials = tuple(material(str(i)) for i in range(18))
    left = tuple(MaterialMappingItem(key=str(i), state=m.reference) for i, m in enumerate(materials[:9]))
    right = tuple(MaterialMappingItem(key=str(i), state=m.reference) for i, m in enumerate(materials[9:]))
    mapped = MaterialMapping.create(context, policy("cartesian", maximum=81, opt_in=True), left, right, materials)
    pages = mapped.pages()
    assert [len(p.pairs) for p in pages] == [64, 17]
    refs = tuple(MembershipPageReference(ordinal=i, members=len(page.pairs),
        artifact=artifact("page" + str(i), population_record_schema("population.material-mapping-page"), page).reference)
        for i, page in enumerate(pages))
    left_ref, right_ref = artifact("left", schema).reference, artifact("right", schema).reference
    manifest = mapped.manifest(left_ref, right_ref, refs)
    retained = artifact("mapping", population_record_schema("population.material-mapping-manifest"), manifest)
    assert mapped.verify_manifest(retained, left_ref, right_ref, tuple(canonical(p) for p in pages)) == manifest
    with pytest.raises(ValueError, match="mapping_page_replay"):
        mapped.verify_manifest(retained, left_ref, right_ref, (canonical(pages[0]),))
    changed = artifact("mapping", retained.reference.schema_ref, manifest.model_copy(update={"pair_count": 80}))
    with pytest.raises(ValueError, match="mapping_manifest_replay"):
        mapped.verify_manifest(changed, left_ref, right_ref, tuple(canonical(p) for p in pages))
