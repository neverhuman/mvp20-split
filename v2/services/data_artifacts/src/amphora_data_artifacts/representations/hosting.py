"""Explicit representation configuration and readiness, with no registration or migration."""

from sqlalchemy import text

from ..publication.model import ContentPolicy
from .bindings.content_rule import VectorContentRule


def content_policy(policy):
    rule = VectorContentRule()
    return ContentPolicy(policy.allowed | {rule.identity}, policy.rules + (rule,))


def probe(connection):
    for table in (
        "encoding_profiles",
        "encoding_work",
        "encoding_leases",
        "encoding_results",
        "encoding_binding_jobs",
        "encoding_requests",
        "encoding_binding_cursors",
        "encoding_binding_events",
        "representation_bindings",
    ):
        connection.execute(text("SELECT tenant_id FROM artifacts." + table + " LIMIT 0"))
