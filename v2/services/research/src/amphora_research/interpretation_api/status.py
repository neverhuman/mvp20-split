"""Explicit status mapping does not turn operational pending work into a scientific verdict."""
from amphora_contracts_research import InterpretationComplete, InterpretationPending, InterpretationStatus


def to_wire(stored):
    if stored is None:
        return None
    outcome = (InterpretationPending(status="pending") if stored.result is None else
        InterpretationComplete(status="interpreted",projection=stored.result))
    return InterpretationStatus(wire_version="1",request=stored.intent.request,actor_id=stored.intent.actor,outcome=outcome)
