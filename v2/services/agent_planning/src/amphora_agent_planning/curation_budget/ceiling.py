"""Packaged owner-reviewed qualification extension; never browser/worker-selected."""
from dataclasses import dataclass


@dataclass(frozen=True)
class ScopeCeiling:
    maximum_calls: int = 4
    maximum_units: int = 1000000000
    authorization: str = 'UI-01.08'


# UI-01.08g explicit owner approval 2026-10-12 20:03:38. Exact tenant AND project are required.
# This is a bounded release policy, not a general budget-management interface.
REVIEWED_EXTENSION = ('internal', 'owner-records-7e21ca85bd6044198b1585aa2c41d336')


def ceiling_for(key):
    if (key['tenant'], key['project']) == REVIEWED_EXTENSION:
        return ScopeCeiling(12, 3050000000, 'UI-01.08g')
    return ScopeCeiling()
