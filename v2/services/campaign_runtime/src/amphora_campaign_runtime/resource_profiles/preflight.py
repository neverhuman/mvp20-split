"""Read-only owner preflight; Deployment never reads Runtime tables."""

import re
from sqlalchemy import text

from . import InvocationCapacity
from ..lifecycle.model import TransitionError


def require_supported_resources(conn, target_release=None):
    supports_capacity = True
    if target_release is not None:
        match = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)", target_release)
        if match is None:
            raise TransitionError("unqualified_runtime_release")
        supports_capacity = tuple(map(int, match.groups())) >= (0, 68, 0)
    snapshots = conn.execute(text("SELECT input_snapshot FROM runtime.runs "
                                  "WHERE status='running' OR reserved>0")).scalars()
    for snapshot in snapshots:
        capacity = InvocationCapacity.from_snapshot(snapshot)
        if capacity.maximum is not None and not supports_capacity:
            raise TransitionError("active_resource_profile_requires_runtime_0_68")
