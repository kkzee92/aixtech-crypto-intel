"""Data-residency and encryption policy for the information system.

This module records where research data may live and what must never be stored.
It does not provision cloud accounts, generate keys, or open a network socket.
"""

from __future__ import annotations

ALLOWED_REGIONS = frozenset({"ap-southeast-1", "eu-central-1", "research-local"})
REFUSED_LABELS = frozenset({"personal", "customer", "secret", "production"})
ALLOWED_LABELS = frozenset({"SYNTHETIC", "PUBLIC_READ"})


def assert_research_label(label: str) -> str:
    """Accept only research labels. Personal and secret payloads are refused."""
    if label in REFUSED_LABELS or label not in ALLOWED_LABELS:
        raise PermissionError("payload label is refused by the data-security policy")
    return label


def assert_store_region(region: str) -> str:
    """Allow a declared research region. Unknown regions are refused."""
    normalized = region.strip().lower()
    if normalized not in ALLOWED_REGIONS:
        raise PermissionError("store region is outside the research residency allowlist")
    return normalized


def encryption_policy() -> dict[str, object]:
    """Requirements if a store is added later. Keys stay outside this repo."""
    return {
        "at_rest": "AES-256-GCM",
        "in_transit": "TLS 1.2 or newer",
        "key_in_repo": False,
        "automated_keygen": False,
        "seed_in_repo": False,
        "live_enabled": False,
    }


def retention_policy() -> dict[str, object]:
    """Retention by research label. Personal data is not a permitted class."""
    return {
        "SYNTHETIC": {"retention_days": 365, "personal": False},
        "PUBLIC_READ": {"retention_days": 30, "personal": False},
        "secret": {"retention_days": 0, "personal": False, "stored": False},
        "personal": {"retention_days": 0, "stored": False},
    }


def vendor_diligence() -> dict[str, object]:
    """Checklist for any future market-data vendor. Not a signed contract."""
    return {
        "dpa_required": True,
        "training_on_customer_data": False,
        "withdrawal_scope": False,
        "subprocessors_declared": True,
        "residency_declared": True,
        "live_trading": False,
    }


def residency_report() -> dict[str, object]:
    """Policy snapshot. Does not contact a region or a vendor."""
    return {
        "allowed_regions": sorted(ALLOWED_REGIONS),
        "allowed_labels": sorted(ALLOWED_LABELS),
        "encryption": encryption_policy(),
        "retention": retention_policy(),
        "vendor": vendor_diligence(),
        "live_enabled": False,
    }
