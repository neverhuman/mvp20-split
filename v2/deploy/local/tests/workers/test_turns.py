import pytest
from amphora_deployment.profile import ProfileError
from amphora_deployment.workers import WorkerSlot


class Turn:
    def __init__(self):
        self.code = None
        self.released = False
        self.release_error = False

    def poll(self):
        return self.code

    def release(self):
        assert self.code is not None
        if self.release_error:
            raise OSError('private diagnostic')
        self.released = True


class Binding:
    def __init__(self):
        self.turns = []
        self.failure = False
        self.recoveries = 0

    def launch(self):
        if self.failure:
            raise OSError('credential-bearing launch uncertainty')
        turn = Turn()
        self.turns.append(turn)
        return turn

    def recover(self):
        if self.failure:
            raise ProfileError('worker_binding_unreconciled')
        self.recoveries += 1


def test_turns_repeat_only_after_exit_and_interval_status_never_launches():
    binding, now = Binding(), [10]
    slot = WorkerSlot(binding, clock=lambda: now[0])
    assert slot.status()['state'] == 'quiescent'
    slot.tick()
    assert not binding.turns
    slot.start()
    assert slot.status()['state'] == 'waiting'
    assert not binding.turns
    slot.tick()
    slot.start()
    slot.tick()
    assert len(binding.turns) == 1
    binding.turns[0].code = 0
    slot.tick()
    assert binding.turns[0].released
    assert len(binding.turns) == 1
    now[0] += 1
    assert slot.status()['completed_turns'] == 1
    assert len(binding.turns) == 1
    slot.tick()
    assert len(binding.turns) == 2


def test_quiescence_never_interrupts_active_turn_and_blocks_restart():
    binding = Binding()
    slot = WorkerSlot(binding)
    slot.start()
    slot.tick()
    assert slot.quiesce()['state'] == 'quiescing'
    for operation in (slot.start, slot.recover, slot.require_quiescent):
        with pytest.raises(ProfileError, match='requires_quiescence'):
            operation()
    slot.tick()
    assert binding.turns[0].code is None
    binding.turns[0].code = 0
    assert slot.quiesce()['state'] == 'quiescent'
    slot.require_quiescent()
    slot.tick()
    assert len(binding.turns) == 1


@pytest.mark.parametrize('failed_launch', [True, False])
def test_failures_latch_until_binding_reconciles_and_explicit_start(failed_launch):
    binding = Binding()
    binding.failure = failed_launch
    slot = WorkerSlot(binding)
    slot.start()
    slot.tick()
    if not failed_launch:
        binding.turns[0].code = 2
        slot.tick()
    assert slot.status()['state'] == 'failed'
    assert 'credential' not in str(slot.status())
    with pytest.raises(ProfileError, match='explicit_recovery'):
        slot.start()
    with pytest.raises(ProfileError, match='requires_quiescence'):
        slot.require_quiescent()
    binding.failure = True
    with pytest.raises(ProfileError, match='unreconciled'):
        slot.recover()
    binding.failure = False
    assert slot.recover()['state'] == 'quiescent'
    slot.tick()
    assert len(binding.turns) == (0 if failed_launch else 1)
    slot.start()
    assert slot.status()['state'] == 'waiting'


def test_uncertain_cleanup_retains_handle_and_blocks_duplicate_launch():
    binding = Binding()
    slot = WorkerSlot(binding)
    slot.start()
    slot.tick()
    turn = binding.turns[0]
    turn.code, turn.release_error = 0, True
    assert slot.tick()['state'] == 'quiescing'
    assert slot.turn is turn
    slot.tick()
    assert len(binding.turns) == 1
    turn.release_error = False
    assert slot.status()['state'] == 'failed'
    slot.recover()
    slot.require_quiescent()


@pytest.mark.parametrize('interval', [0, 61, True, float('nan'), float('inf')])
def test_invalid_interval(interval):
    with pytest.raises(ProfileError, match='worker_interval'):
        WorkerSlot(Binding(), interval=interval)
