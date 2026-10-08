"""Sanitized gateway boundary validation failures."""
class GatewayError(ValueError):
    pass

def require(value,reason):
    if not value:
        raise GatewayError(reason)
