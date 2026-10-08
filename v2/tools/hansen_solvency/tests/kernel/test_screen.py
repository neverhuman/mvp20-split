import json
import math
import pytest
from amphora_hansen_solvency.kernel import compute
from amphora_hansen_solvency.payloads import SolvencyInput, SolvencyOutput
from amphora_hansen_solvency.metadata import descriptor, schema_bytes
from amphora_hansen_solvency.adapter import execute
from amphora_tool_protocol import ToolInputRejected

def parameters():
    return dict(candidate_id='fixture-polymer-A', parameter_context='Synthetic parameters; no experimental result.',
        polymer=dict(dispersion=18., polar=8., hydrogen_bond=6.),
        solvent=dict(dispersion=17., polar=6., hydrogen_bond=4.), interaction_radius=4.)

def test_known_distance_and_retained_procedure():
    p=parameters();raw=json.dumps(p).encode();r=json.loads(compute(raw))
    assert r['distance_squared']==12
    assert r['relative_energy_difference']==pytest.approx(math.sqrt(12)/4)
    assert r['sphere_position']=='inside' and r['scientific_status']=='unvalidated_screen'
    assert r['input_parameters']['candidate_id']==p['candidate_id'] and len(r['procedure'])==3
    assert compute(raw)==compute(raw)

def test_boundary_and_outside_are_explicit():
    p=parameters();p['interaction_radius']=math.sqrt(12)
    assert json.loads(compute(json.dumps(p).encode()))['sphere_position']=='boundary'
    p['interaction_radius']=1
    assert json.loads(compute(json.dumps(p).encode()))['sphere_position']=='outside'

@pytest.mark.parametrize('value',[0,-1,True,'4',float('nan'),float('inf')])
def test_bad_radius_rejected(value):
    p=parameters();p['interaction_radius']=value
    with pytest.raises(ToolInputRejected):execute(json.dumps(p).encode())

def test_negative_parameter_rejected():
    p=parameters();p['polymer']['polar']=-1
    with pytest.raises(ValueError):compute(json.dumps(p).encode())

def test_exact_schema_and_descriptor():
    for kind,model in [('input',SolvencyInput),('output',SolvencyOutput)]:
        assert schema_bytes(kind)==(json.dumps(model.model_json_schema(mode='validation'),sort_keys=True,indent=2)+'\n').encode()
    assert descriptor('c'*64).tool.binding.capability_id=='materials.hansen-solvency'
