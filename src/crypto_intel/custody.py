"""Data-security policy checks. No secrets are created or stored.

Rotation ages and name classes are research controls. A production secret
manager is still required before any market-data credential exists.
"""

from __future__ import annotations

from crypto_intel.posture import refuse_trade_secret

READ_KEY_MAX_AGE_DAYS = 90
AUDIT_EXPORT_MAX_AGE_DAYS = 365
CLOCK_SKEW_SECONDS = 120

RETENTION_DAYS: dict[str, int] = {
    "public_market": 400,
    "research_audit": 365,
    "synthetic_fixture": 3650,
    "secret": 0,
    "personal": 0,
}


def classify_name(name: str) -> str:
    """Return a handling class. Trade-like names are refused."""
    refuse_trade_secret(name)
    lowered = name.lower()
    if any(token in lowered for token in ("secret", "token", "key", "password")):
        if any(token in lowered for token in ("read", "market", "public")):
            return "read_market"
        raise PermissionError("unqualified secret name is refused")
    return "non_secret"


def rotation_status(age_days: int, kind: str) -> str:
    if age_days < 0:
        raise ValueError("age_days cannot be negative")
    if kind == "trade":
        raise PermissionError("trade credentials are refused")
    limit = READ_KEY_MAX_AGE_DAYS if kind == "read_market" else AUDIT_EXPORT_MAX_AGE_DAYS
    if age_days > limit:
        return "rotate"
    if age_days > int(limit * 0.8):
        return "due_soon"
    return "current"


def clock_skew_ok(skew_seconds: float) -> bool:
    return abs(skew_seconds) <= CLOCK_SKEW_SECONDS


def retention_days(data_class: str) -> int:
    if data_class not in RETENTION_DAYS:
        raise KeyError(f"unknown data class {data_class}")
    return RETENTION_DAYS[data_class]
