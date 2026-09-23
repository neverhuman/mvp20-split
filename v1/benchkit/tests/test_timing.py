import time

from amphora_benchkit import timing


def test_stopwatch_emits_wall_seconds():
    diag = {}
    with timing.stopwatch(diag, "step"):
        time.sleep(0.01)
    assert diag["step"]["wall_seconds"] >= 0.01


def test_stopwatch_records_on_exception():
    diag = {}
    try:
        with timing.stopwatch(diag, "boom"):
            raise ValueError
    except ValueError:
        pass
    assert "wall_seconds" in diag["boom"]


def test_timed_decorator_passthrough_and_accumulation():
    diag = {}

    @timing.timed(diag, "f")
    def f(x):
        time.sleep(0.005)
        return x * 2

    assert f(21) == 42
    assert f(2) == 4
    assert diag["f"]["calls"] == 2
    assert diag["f"]["total_wall_seconds"] >= diag["f"]["wall_seconds"] > 0


def test_timed_default_key_is_function_name():
    diag = {}

    @timing.timed(diag)
    def named():
        return 1

    named()
    assert "named" in diag
