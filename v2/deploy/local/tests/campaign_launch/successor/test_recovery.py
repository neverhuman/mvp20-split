from amphora_deployment.campaign_launch.coordinator import LaunchCoordinator
from amphora_deployment.campaign_launch.journal import LaunchJournal
from amphora_deployment.campaign_successor.state import SuccessorState
from ..coordinator.test_reconciliation import Peers
from ..journal.test_run_bindings import bindings_setup
from ..transport.test_runtime_peer import peer
from .test_journal import successor


def test_lost_successor_reply_replacement_engagement_and_drain(tmp_path,make_intent,admission_receipt,clock):
    intent=successor(make_intent()); journal=LaunchJournal(tmp_path)
    journal.submit(intent,lambda _:None,now=clock)
    peers=Peers(journal,admission_receipt(intent)); peers.lost_reply=True
    coordinator=LaunchCoordinator(journal,peers,peers,peers,now=clock)
    assert coordinator.tick().phase=='admission_unresolved'
    assert coordinator.tick().reason=='launch_peer_unavailable'
    replacement=LaunchJournal(tmp_path); peers.journal=replacement
    coordinator=LaunchCoordinator(replacement,peers,peers,peers,now=clock)
    assert coordinator.tick().phase=='admitted_not_engaged'
    assert coordinator.tick().phase=='engaging'
    assert coordinator.tick().phase=='engaged'
    peers.worker_failure=True
    assert coordinator.tick().phase=='admitted_not_engaged'
    peers.worker_failure=False
    coordinator.tick(); assert coordinator.tick().phase=='engaged'
    peers.status='completed'
    assert coordinator.tick().phase=='draining'
    assert coordinator.tick().phase=='draining'
    peers.drained=True
    final=coordinator.tick()
    assert final.phase=='released' and replacement.active() is None
    assert final.receipt().predecessor==intent.predecessor
    assert peers.submissions==[intent.admission.canonical_bytes]
    assert replacement.verify_quiescent()==1


def test_successor_uses_exact_runtime_routes_and_original_bytes(peer,make_intent,admission_receipt):
    client,connection=peer; intent=successor(make_intent())
    connection.body=admission_receipt(intent).model_dump_json().encode()
    assert client.receipt(intent)==admission_receipt(intent)
    assert connection.calls[-1][1]=='/v1/commands/graph.admit_draft_successor/launch-1?actor_id=researcher'
    assert client.admit(intent)==admission_receipt(intent)
    assert connection.calls[-1][:3]==('POST','/v1/graph-runs/draft-successors',intent.admission.canonical_bytes)


def test_successor_worker_binding_is_stable_and_preserves_prior_files(bindings_setup,admission_receipt,clock):
    store,fresh,template=bindings_setup
    previous=store.prepare(fresh)['hansen-solvency']
    original=previous.profile.configuration.read_bytes()
    intent=successor(fresh.intent)
    state=SuccessorState.initial(intent,clock()).move('admission_unresolved',clock())
    state=state.observe_admission(admission_receipt(intent,run='successor-run'),clock())
    bound=store.prepare(state)['hansen-solvency']
    assert bound.profile==store.prepare(state)['hansen-solvency'].profile
    assert bound.profile.configuration!=previous.profile.configuration
    assert previous.profile.configuration.read_bytes()==original
    assert bound.journal.read() is None
