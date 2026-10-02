"""Data classification for the research information system.

Unlabelled payloads are refused. Personal data and secrets are refused even
if a caller tries to label them as research. This is a policy check, not a
data-loss-prevention product.
"""

from __future__ import annotations

from enum import Enum


class DataClass(str, Enum):
    SYNTHETIC = "synthetic"
    PUBLIC_MARKET = "public_market"
    OPERATIONAL_AUDIT = "operational_audit"
    PERSONAL = "personal"
    SECRET = "secret"  # noqa: S105


_SECRET_MARKERS = ("secret", "api_key", "private_key", "seed_phrase", "mnemonic")
_PERSONAL_MARKERS = ("nric", "fin", "passport", "email", "phone", "address")
_ALLOWED = {
    DataClass.SYNTHETIC: None,
    DataClass.PUBLIC_MARKET: 30,
    DataClass.OPERATIONAL_AUDIT: 365,
    DataClass.PERSONAL: 0,
    DataClass.SECRET: 0,
}


def classify_label(label: str) -> DataClass:
    text = label.lower()
    if any(marker in text for marker in _SECRET_MARKERS):
        return DataClass.SECRET
    if any(marker in text for marker in _PERSONAL_MARKERS):
        return DataClass.PERSONAL
    if "synthetic" in text:
        return DataClass.SYNTHETIC
    if "public" in text:
        return DataClass.PUBLIC_MARKET
    if "audit" in text:
        return DataClass.OPERATIONAL_AUDIT
    raise ValueError("unlabelled data is refused")


def assert_research_label(label: str) -> DataClass:
    kind = classify_label(label)
    if kind in {DataClass.PERSONAL, DataClass.SECRET}:
        raise PermissionError(f"{kind.value} data is refused in the research system")
    return kind


def retention_days(kind: DataClass) -> int | None:
    """None means the labelled synthetic fixture has no operational expiry."""
    return _ALLOWED[kind]
