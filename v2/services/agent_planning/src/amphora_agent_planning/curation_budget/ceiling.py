"""Packaged owner-reviewed qualification extension; never browser/worker-selected."""
from dataclasses import dataclass


@dataclass(frozen=True)
class ScopeCeiling:
    maximum_calls: int = 4
    maximum_units: int = 1000000000
    authorization: str = 'UI-01.08'


# UI-01.08i additional $10 approved 2026-10-12 20:48:00. UI-01.08j transfers
# only its unreserved remainder to the existing demo after qualification success.
# All sixteen original holds remain. Sum: 53 slots/$13.30; no extra authority.
# Exact tenant AND project required; not a general budget-management interface.
REVIEWED_EXTENSION = ('internal', 'owner-records-7e21ca85bd6044198b1585aa2c41d336')
REVIEWED_DEMO = ('internal', 'knowledge-demo-1b1dc25768334153b58973882627b858')


def ceiling_for(key):
    if (key['tenant'], key['project']) == REVIEWED_EXTENSION:
        return ScopeCeiling(16, 4050000000, 'UI-01.08j-retained-qualification')
    if (key['tenant'], key['project']) == REVIEWED_DEMO:
        return ScopeCeiling(37, 9250000000, 'UI-01.08j-demo-remainder')
    return ScopeCeiling()
