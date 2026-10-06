class ReuseError(ValueError):
    """Safe invalid evidence or unsupported request code."""


class ReusePeerUnavailable(ReuseError):
    """Indeterminate peer failure; never a negative scientific finding or cache miss."""


def require(condition, reason):
    if not condition:
        raise ReuseError(reason)
