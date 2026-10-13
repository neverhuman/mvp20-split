import hashlib
import json
from pathlib import Path
import sys
import pytest

sys.path.insert(0,str(Path(__file__).absolute().parents[2]))
from curation_managed_demo.backup_demo import CurrentDemoCut


def write(path,value):
    path.write_text(json.dumps(value))


def fixture(tmp_path):
    inventory=tmp_path/'inventory';inventory.mkdir()
    serving=tmp_path/'serving';serving.mkdir()
    write(inventory/'readbacks.json',{'runs':{'retained-run':{'status':'completed'}}})
    record={'status':'passed','all_owned_processes_drained':True,'source':str(serving),
        'run_ids':['retained-run'],'timestamp_local':'2026-10-12 21:00:00',
        'readbacks_sha256':hashlib.sha256((inventory/'readbacks.json').read_bytes()).hexdigest()}
    write(inventory/'inventory-evidence.json',record)
    write(inventory/'drain.json',{'status':'drained'})
    return inventory,serving,record


def test_cut_preserves_actual_readback_identity(tmp_path):
    inventory,serving,record=fixture(tmp_path)
    basis=CurrentDemoCut(inventory,serving)
    assert basis.readback_evidence()==[{'sha256':record['readbacks_sha256'],
        'run_id':'retained-run','timestamp_local':record['timestamp_local']}]


@pytest.mark.parametrize('change',['bytes','runs','status','drain','source'])
def test_invalid_cut_cannot_authorize_capture(tmp_path,change):
    inventory,serving,record=fixture(tmp_path)
    if change=='bytes': write(inventory/'readbacks.json',{'runs':{}})
    elif change=='runs': record['run_ids']=['different-run']
    elif change=='status': record['status']='failed'
    elif change=='drain': write(inventory/'drain.json',{'status':'failed'})
    elif change=='source': record['source']=str(tmp_path/'different-source')
    write(inventory/'inventory-evidence.json',record)
    with pytest.raises(AssertionError):CurrentDemoCut(inventory,serving)
