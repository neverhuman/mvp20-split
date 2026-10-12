import json
import sqlite3
from concurrent.futures import ThreadPoolExecutor

import pytest
from amphora_deployment.campaign_launch.intent import LaunchError, LaunchIntent
from amphora_deployment.campaign_launch.journal import LaunchJournal
from amphora_deployment.campaign_launch.state import LaunchState
from amphora_deployment.campaign_successor.intent import SuccessorIntent
from amphora_deployment.campaign_successor.state import SuccessorState


def successor(fresh):
    raw = json.loads(fresh.request.canonical_bytes)
    raw['identity']['command_family'] = 'campaign.launch_successor'
    inner = raw['payload']['admission']
    inner['encoding'] = 'amphora-command-v2'
    inner['identity']['command_family'] = 'graph.admit_draft_successor'
    inner['payload']['predecessor'] = {'run_id':'original-run','plan_sha256':'e'*64,'revision':9}
    inner['payload']['carried'] = [{'target_port':'mixture','source':{'kind':'run_output','port':'mixture'},'expected_value_sha256':'f'*64}]
    return SuccessorIntent.parse(json.dumps(raw).encode())


def test_successor_replay_retains_predecessor_and_cannot_be_fresh(make_intent, clock, admission_receipt):
    intent = successor(make_intent())
    assert SuccessorIntent.parse(intent.request.canonical_bytes) == intent
    with pytest.raises(LaunchError): LaunchIntent.parse(intent.request.canonical_bytes)
    state = SuccessorState.initial(intent,clock()).move('admission_unresolved',clock())
    state = state.observe_admission(admission_receipt(intent),clock())
    assert SuccessorState.restore(intent,state.receipt().model_dump_json().encode()) == state
    assert state.receipt().predecessor == intent.predecessor
    raw = state.receipt().model_dump(mode='json'); raw['predecessor']['revision'] += 1
    with pytest.raises(LaunchError,match='journal_corrupt'): SuccessorState.restore(intent,json.dumps(raw).encode())


def test_families_share_active_slot_but_not_command_identity(tmp_path, make_intent, clock):
    journal = LaunchJournal(tmp_path); fresh = make_intent(); next_intent = successor(fresh)
    first = journal.submit(fresh,lambda _:None,now=clock)
    with pytest.raises(LaunchError,match='slot_busy'): journal.submit(next_intent,lambda _:None,now=clock)
    rejected = journal.change(first.intent.key,0,lambda s:s.move('rejected',clock(),'fixture_rejection'))
    second = journal.submit(next_intent,lambda _:None,now=clock)
    reopened = LaunchJournal(tmp_path)
    assert reopened.get(fresh.key) == rejected
    assert reopened.get(next_intent.key) == second == reopened.active()
    assert reopened.submit(next_intent,lambda _:pytest.fail('replay checked mutable profile'),now=clock) == second
    changed = json.loads(next_intent.request.canonical_bytes); changed['payload']['admission']['payload']['predecessor']['revision'] += 1
    with pytest.raises(LaunchError,match='request_conflict'): reopened.submit(SuccessorIntent.parse(json.dumps(changed).encode()),lambda _:None)


def test_competing_families_cannot_acquire_two_slots(tmp_path,make_intent,clock):
    journal = LaunchJournal(tmp_path)
    def submit(intent):
        try: return journal.submit(intent,lambda _:None,now=clock)
        except LaunchError as error: return str(error)
    with ThreadPoolExecutor(2) as pool:
        results = list(pool.map(submit,[make_intent(),successor(make_intent())]))
    assert sum(result=='launch_slot_busy' for result in results) == 1
    assert journal.active() in results


@pytest.mark.parametrize('corrupt',[False,True])
def test_legacy_upgrade_preserves_bytes_or_rolls_back(tmp_path,make_intent,clock,corrupt):
    intent=make_intent(); state=LaunchState.initial(intent,clock())
    raw=state.receipt().model_dump_json().encode(); request=intent.request.canonical_bytes
    with sqlite3.connect(tmp_path/'launches.sqlite3') as db:
        db.execute('CREATE TABLE launches (tenant TEXT,project TEXT,actor TEXT,request_id TEXT,request BLOB,receipt BLOB,revision INTEGER,active INTEGER UNIQUE,PRIMARY KEY(tenant,project,actor,request_id))')
        db.execute('INSERT INTO launches VALUES (?,?,?,?,?,?,?,1)',(*intent.key,request,raw,1 if corrupt else 0))
    if corrupt:
        with pytest.raises(LaunchError,match='journal_corrupt'): LaunchJournal(tmp_path)
        with sqlite3.connect(tmp_path/'launches.sqlite3') as db: assert len(db.execute('PRAGMA table_info(launches)').fetchall())==8
    else:
        journal=LaunchJournal(tmp_path); assert journal.get(intent.key)==state
        with sqlite3.connect(journal.path) as db:
            assert db.execute('SELECT request,receipt FROM launches').fetchone()==(request,raw)
