"""Read-only owner preflight; Deployment never reads Runtime tables."""

import re
from sqlalchemy import text

from . import InvocationCapacity
from ..lifecycle.model import TransitionError
from ..completion.profiles import RetentionProfile


def require_supported_resources(conn, target_release=None):
    supports_capacity = True
    supports_retention = True
    if target_release is not None:
        match = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)", target_release)
        if match is None:
            raise TransitionError("unqualified_runtime_release")
        supports_capacity = tuple(map(int, match.groups())) >= (0, 68, 0)
        supports_retention = tuple(map(int, match.groups())) >= (0, 69, 0)
    snapshots = conn.execute(text("SELECT input_snapshot,tool_snapshot FROM runtime.runs "
                                  "WHERE status='running' OR reserved>0")).mappings()
    for snapshot in snapshots:
        capacity = InvocationCapacity.from_snapshot(snapshot["input_snapshot"])
        if capacity.maximum is not None and not supports_capacity:
            raise TransitionError("active_resource_profile_requires_runtime_0_68")
        if RetentionProfile.from_snapshot(snapshot["tool_snapshot"]).name is not None and not supports_retention:
            raise TransitionError("active_retention_profile_requires_runtime_0_69")
