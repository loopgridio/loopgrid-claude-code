"""Offline LoopGrid Core origin validation for diagnostics (stdlib only)."""
from urllib.parse import urlsplit


def validate_core_origin(value: str) -> str:
    origin = value.strip().rstrip("/")
    try:
        parsed = urlsplit(origin)
        _ = parsed.port
    except ValueError as exc:
        raise ValueError("Invalid LoopGrid Core URL") from exc
    if (parsed.scheme not in ("http", "https") or not parsed.hostname
            or parsed.username is not None or parsed.password is not None
            or parsed.path or parsed.query or parsed.fragment
            or any(c.isspace() for c in origin)):
        raise ValueError("LoopGrid Core URL must be a plain http(s) origin")
    if parsed.scheme == "http" and parsed.hostname not in ("localhost", "127.0.0.1", "::1"):
        raise ValueError("Remote Core connections require HTTPS")
    return origin
