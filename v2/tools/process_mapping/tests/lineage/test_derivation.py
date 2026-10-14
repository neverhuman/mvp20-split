import pytest
from amphora_contracts_population import (AbsentProcessInput, ExecutionPointer, MaterialUse, ProcessBinding, ProcessDerivation,
                                          ProcessPort, population_record_schema)
from amphora_contracts_tools import ToolBinding
from amphora_process_mapping import BoundMaterial, MaterialDerivation


def binding(schema, optional=False):
    tool = ToolBinding(capability_id="synthetic-process", release="0.1.0", image_sha256="d" * 64, contract_version="1")
    inputs = (ProcessPort(port="precursors", required=True, representation=schema, maximum=32),)
    if optional:
        inputs += (ProcessPort(port="annotation", required=False, representation=schema, maximum=1),)
    return ProcessBinding(tool=tool, inputs=inputs, outputs=(ProcessPort(port="products", required=True, representation=schema, maximum=32),))


def derive(factory, inputs, outputs, *, optional=False, absent=(), tool=None):
    context, schema, conditions, artifact, _ = factory
    configured = binding(schema, optional)
    record = ProcessDerivation(schema_version="1", profile="synthetic-process-derivation-v1", context=context,
        occurrence_id="transform", tool=tool or configured.tool,
        inputs=tuple(MaterialUse(port="precursors", ordinal=i, material=m.reference) for i, m in enumerate(inputs)),
        outputs=tuple(MaterialUse(port="products", ordinal=i, material=m.reference) for i, m in enumerate(outputs)),
        absent=absent, conditions=conditions,
        producer=ExecutionPointer(run_id=context.generation.run_id, activation_id="activation", invocation_id="invocation",
            attempt_id="attempt", completion_id="completion"), unknowns=("conservation", "reaction_feasibility"))
    return MaterialDerivation.verify(artifact("derivation", population_record_schema("population.process-derivation"), record),
                                     context, configured, inputs, outputs)


def test_more_than_two_precursors_are_process_lineage(material_factory):
    material = material_factory[-1]
    result = derive(material_factory, tuple(material(name) for name in ("a", "b", "c")), (material("mixture"),))
    assert len(result.inputs) == 3 and len(result.outputs) == 1
    assert result.outputs[0].record.kind == "intermediate"
    assert result.record.unknowns == ("conservation", "reaction_feasibility")


def test_optional_inputs_require_explicit_absence(material_factory):
    material = material_factory[-1]
    with pytest.raises(ValueError, match="derivation_optional_absence"):
        derive(material_factory, (material("a"),), (material("b"),), optional=True)
    result = derive(material_factory, (material("a"),), (material("b"),), optional=True,
                    absent=(AbsentProcessInput(port="annotation", reason_code="not_available"),))
    assert result.record.absent[0].reason_code == "not_available"


def test_output_must_be_new_and_match_tool_conditions(material_factory):
    context, schema, conditions, _, material = material_factory
    a = material("a")
    with pytest.raises(ValueError, match="derivation_output_not_new"):
        derive(material_factory, (a,), (a,))
    with pytest.raises(ValueError, match="derivation_revision_regression"):
        derive(material_factory, (material("a", state_id="state", revision=3),), (material("b", state_id="state", revision=2),))
    with pytest.raises(ValueError, match="derivation_output_conditions"):
        derive(material_factory, (a,), (material("b", current_conditions=conditions.model_copy(update={"artifact_id": "different"})),))
    with pytest.raises(ValueError, match="derivation_producer_binding"):
        derive(material_factory, (a,), (material("b"),), tool=binding(schema).tool.model_copy(update={"release": "9.0.0"}))


def test_nineteen_stage_width_changes_preserve_exact_consumed_outputs(material_factory):
    material = material_factory[-1]
    inputs = (material("seed-a"), material("seed-b"), material("seed-c"))
    widths = (1, 3, 2, 1, 4, 2, 1, 2, 3, 1, 2, 1, 4, 1, 2, 3, 2, 1, 2)
    retained = []
    for stage, width in enumerate(widths):
        outputs = tuple(material(f"stage-{stage}-{i}") for i in range(width))
        result = derive(material_factory, inputs, outputs)
        assert tuple(m.artifact for m in result.inputs) == inputs
        retained.append(result)
        inputs = outputs
    assert len(retained) == 19
    # A lineage contract oracle, not execution/readiness/conservation evidence.
    assert tuple(m.artifact for m in retained[1].inputs) == tuple(m.artifact for m in retained[0].outputs)


def test_material_hash_rejects(material_factory):
    context, _, _, artifact, material = material_factory
    state = material("state")
    assert BoundMaterial.verify(state, context).record.state_id == "state"
    with pytest.raises(ValueError, match="process_artifact_digest"):
        BoundMaterial.verify(type(state)(state.reference, state.content + b" "), context)
