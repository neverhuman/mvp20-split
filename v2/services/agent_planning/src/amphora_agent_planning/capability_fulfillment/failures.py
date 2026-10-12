"""Closed public-peer failure classification; unknown integrity faults propagate."""
from ..capability_acceptance.review import AcceptanceRejected
from ..source_access.budget import SourceUnavailable

REJECTIONS = frozenset({'source_access_denied', 'source_reference_unavailable',
    'metadata_denied', 'metadata_missing', 'registry_scope', 'registry_lock',
    'registry_duplicate_port', 'registry_descriptor_size', 'source_peer_response_limit',
    'source_review_byte_limit'})
PENDING = frozenset({'metadata_unavailable', 'metadata_protocol', 'metadata_media', 'metadata_deadline'})


def rejection(error):
    return str(error) if isinstance(error, AcceptanceRejected) or str(error) in REJECTIONS else None


def retryable(error):
    return isinstance(error, (SourceUnavailable, TimeoutError, OSError)) or (
        type(error) is ValueError and str(error) in PENDING)
