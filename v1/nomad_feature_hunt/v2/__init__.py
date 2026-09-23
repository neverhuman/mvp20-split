"""NOMAD Feature Foundry v2.

The v2 package is deliberately isolated from :mod:`nomad_feature_hunt` v1.  It
may reuse immutable helpers, but it never mutates v1 campaign state or the
``nomad_crystal360`` package.
"""

from .constants import CAMPAIGN_VERSION, EXPECTED_JNOCCIO_ROLES
from .schemas import expand_feature_spec, parse_strict_json

__all__ = [
    "CAMPAIGN_VERSION",
    "EXPECTED_JNOCCIO_ROLES",
    "expand_feature_spec",
    "parse_strict_json",
]

