import pytest
from amphora_knowledge.authoring.canonical import KnowledgeError
from amphora_knowledge.replay.chain import GraphReplay

from .test_chain import history as history


def test_watermark_then_catch_up_is_identical_to_full_replay(history):
    case, edits = history
    replay = GraphReplay(case.state.graph, case.vocabulary, case.policy)
    prefix = replay.cursor().through([edits[0].record], edits[0].head)
    caught_up = prefix.through([edit.record for edit in edits[1:]], edits[-1].head)
    assert caught_up.result == replay.rebuild(edit.record for edit in edits)
    assert prefix.state.revision == 1 and prefix.state.assertions.active()[0].polarity == "affirmed"
    assert caught_up.state.revision == 3 and not caught_up.state.assertions.active()
    assert caught_up.through([], caught_up.head) == caught_up


@pytest.mark.parametrize("variant,code", [("missing", "replay_watermark_mismatch"),
    ("extra", "replay_watermark_exceeded"), ("wrong_hash", "replay_watermark_mismatch"),
    ("regression", "replay_watermark_regression"), ("foreign", "replay_graph_mismatch"),
    ("duplicate", "duplicate_accepted_change")])
def test_catch_up_cannot_move_backward_skip_or_accept_another_head(history, variant, code):
    case, edits = history
    prefix = GraphReplay(case.state.graph, case.vocabulary, case.policy).cursor().through([edits[0].record], edits[0].head)
    tail, watermark = [edits[1].record], edits[1].head
    if variant == "missing":
        tail = []
    elif variant == "extra":
        tail.append(edits[2].record)
    elif variant == "wrong_hash":
        watermark = watermark.model_copy(update={"snapshot": watermark.snapshot.model_copy(update={"sha256": "0"*64})})
    elif variant == "regression":
        tail, watermark = [], None
    elif variant == "foreign":
        watermark = watermark.model_copy(update={"snapshot": watermark.snapshot.model_copy(update={
            "graph": case.state.graph.model_copy(update={"graph_id": "another"})})})
    else:
        tail = [edits[0].record]
    with pytest.raises(KnowledgeError, match=code):
        prefix.through(tail, watermark)
    assert prefix.head == edits[0].head


def test_replay_limit_applies_across_catch_up_rounds(history):
    case, edits = history
    prefix = GraphReplay(case.state.graph, case.vocabulary, case.policy, max_changes=2).cursor()
    prefix = prefix.through([edit.record for edit in edits[:2]], edits[1].head)
    with pytest.raises(KnowledgeError, match="replay_limit"):
        prefix.through([edits[2].record], edits[2].head)
