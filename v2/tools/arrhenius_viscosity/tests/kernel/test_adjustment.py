import json
import math
import pytest
from amphora_arrhenius_viscosity.kernel import compute
from amphora_arrhenius_viscosity.payloads import ViscosityInput, ViscosityOutput
from amphora_arrhenius_viscosity.metadata import descriptor, schema_bytes
from amphora_arrhenius_viscosity.adapter import execute
from amphora_tool_protocol import ToolInputRejected

def parameters():
    return dict(candidate_id='fixture-polymer-A',parameter_context='Synthetic parameters; no experimental result.',
        reference_viscosity_pa_s=2.,reference_temperature_c=25.,temperature_c=50.,activation_energy_j_mol=20000.)

def test_reference_and_temperature_adjustment():
    p=parameters();r=json.loads(compute(json.dumps(p).encode()))
    expected=2*math.exp(20000/8.31446261815324*(1/323.15-1/298.15))
    assert r['viscosity_pa_s']==pytest.approx(expected) and r['viscosity_pa_s']<2
    assert r['scientific_status']=='unvalidated_screen' and len(r['procedure'])==3
    p['temperature_c']=25
    assert json.loads(compute(json.dumps(p).encode()))['viscosity_pa_s']==2

@pytest.mark.parametrize('key,value',[
    ('reference_viscosity_pa_s',0),('activation_energy_j_mol',-1),('temperature_c',-273.15),
    ('temperature_c',501),('temperature_c',True),('temperature_c','25'),('temperature_c',float('inf')),
    ('activation_energy_j_mol',1e100)])
def test_invalid_and_underflow_rejected(key,value):
    p=parameters();p[key]=value
    with pytest.raises(ToolInputRejected):execute(json.dumps(p).encode())

def test_overflow_rejected():
    p=parameters();p['temperature_c']=-273.14
    with pytest.raises(ValueError):compute(json.dumps(p).encode())

def test_exact_schema_and_descriptor():
    for kind,model in [('input',ViscosityInput),('output',ViscosityOutput)]:
        assert schema_bytes(kind)==(json.dumps(model.model_json_schema(mode='validation'),sort_keys=True,indent=2)+'\n').encode()
    assert descriptor('c'*64).tool.binding.capability_id=='materials.arrhenius-viscosity'
