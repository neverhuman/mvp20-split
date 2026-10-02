"""Bounded scoped provenance traversal with explicit cycle rejection."""

from sqlalchemy import text

from .model import RightsError

MAX_ARTIFACTS = 4096
MAX_PARENTS = 128

PARENTS = """
SELECT input_artifact_id FROM artifacts.derivation_inputs
 WHERE tenant_id=:tenant AND project_id=:project AND artifact_id=:artifact
UNION
SELECT s.raw_artifact_id FROM artifacts.conversion_traces t
 JOIN artifacts.source_revisions s ON (s.tenant_id,s.project_id,s.source_id,s.revision_id)=
 (t.tenant_id,t.project_id,t.source_id,t.source_revision_id)
 WHERE t.tenant_id=:tenant AND t.project_id=:project AND t.output_artifact_id=:artifact
 AND s.raw_artifact_id<>t.output_artifact_id
LIMIT 129
"""


def traverse(roots, parents):
    """Iterative DFS: shared ancestors are valid, back edges fail closed."""
    seen, active, complete = set(), set(), set()
    for root in roots:
        stack = [(root, False)]
        while stack:
            artifact, leaving = stack.pop()
            if leaving:
                active.remove(artifact)
                complete.add(artifact)
                continue
            if artifact in active:
                raise RightsError("rights_lineage_cycle")
            if artifact in complete:
                continue
            seen.add(artifact)
            if len(seen) > MAX_ARTIFACTS:
                raise RightsError("rights_lineage_limit")
            related = tuple(parents(artifact))
            if len(related) > MAX_PARENTS:
                raise RightsError("rights_lineage_limit")
            active.add(artifact)
            stack.append((artifact, True))
            stack.extend((parent, False) for parent in related)
    return tuple(sorted(seen))


def identities(connection, principal, roots):
    def parents(artifact):
        return connection.execute(text(PARENTS), principal.bindings | {"artifact": artifact}).scalars().all()
    return traverse(roots, parents)
