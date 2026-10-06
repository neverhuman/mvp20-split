"""One effective input resolver for conversion opening and every source-cut revalidation."""

from sqlalchemy import text

from ..coordinator.values import BoundValues, ensure
from ..lifecycle.claims import RUN
from ..lifecycle.model import TransitionError
from .model import BindingInput


def resolve_effective(conn, params, activation_id, node, environment):
    original = BindingInput.resolve(node, environment)
    if node.kind != 'artifact_materialize':
        return original
    row = conn.execute(text('SELECT decision_id FROM runtime.supervision_checkpoints WHERE ' + RUN +
        ' AND activation_id=:activation'), {**params, 'activation': activation_id}).mappings().one_or_none()
    if row is None:
        return original
    # Fixed local boundary loaded after interpreter initialization; no dynamic handler dispatch.
    from ..supervision_winners.storage import WinnerStore, slot_for
    values = {**params, 'decision': row['decision_id']}
    slot = slot_for(conn, values)
    winner = WinnerStore.load(conn, values, slot)
    ensure(winner is not None, 'binding_checkpoint_pending')
    outcome = winner.document().outcome
    ensure(outcome.kind != 'cancelled' and not (outcome.kind == 'fallback' and outcome.action == 'block_target'),
           'binding_checkpoint_blocked')
    if winner.selection is None:
        return original
    try:
        fields = winner.selection.resolve(original.values.bindings)
    except ValueError as error:
        raise TransitionError('binding_supervision_original_changed') from error
    return BindingInput(node, BoundValues(fields))
