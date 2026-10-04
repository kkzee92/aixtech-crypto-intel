"""Version 0.8 data-security zones for the paper information system.

Zones describe where a research field may live. Forbidden fields are refused.
This is a control description, not a certification and not legal advice.
"""

from __future__ import annotations

import hashlib
import re

ZONES: tuple[dict[str, object], ...] = (
    {
        "zone": "public-market",
        "fields": ("symbol", "ohlcv", "funding_rate"),
        "retention": "research retention",
        "pii": False,
    },
    {
        "zone": "research-derived",
        "fields": ("signal", "paper_size", "audit_digest", "dossier"),
        "retention": "research retention",
        "pii": False,
    },
    {
        "zone": "restricted-ops",
        "fields": ("kill_switch", "source_attestation"),
        "retention": "ops log, no secrets",
        "pii": False,
    },
    {
        "zone": "forbidden",
        "fields": ("exchange_api_key", "withdrawal_destination", "private_key", "account_email", "wallet_address"),
        "retention": "never stored",
        "pii": True,
    },
)

ROLE_ZONE_READ: dict[str, tuple[str, ...]] = {
    "researcher": ("public-market", "research-derived"),
    "reviewer": ("public-market", "research-derived", "restricted-ops"),
    "auditor": ("public-market", "research-derived", "restricted-ops"),
    "operator": ("restricted-ops",),
}

FORBIDDEN_FIELD = re.compile(
    r"(?i)\b(api[_-]?key|private[_-]?key|withdrawal|seed[_-]?phrase|account[_-]?email|wallet[_-]?address)\b"
)
EMAIL_PATTERN = re.compile(r"\b[A-Z0-9._%+\-]+@[A-Z0-9.\-]+\.[A-Z]{2,}\b", re.IGNORECASE)
WALLET_PATTERN = re.compile(r"\b0x[a-fA-F0-9]{40}\b")


def zone_catalog() -> dict[str, object]:
    return {
        "version": "0.8.0",
        "zones": list(ZONES),
        "role_zone_read": {role: list(zones) for role, zones in ROLE_ZONE_READ.items()},
        "live_enabled": False,
        "order_path": False,
        "secret_retention": "never stored",
    }


def assert_zone_read(role: str, zone: str) -> dict[str, object]:
    if role not in ROLE_ZONE_READ:
        raise PermissionError(f"unknown role {role}")
    if zone == "forbidden":
        raise PermissionError("forbidden zone cannot be read")
    allowed = zone in ROLE_ZONE_READ[role]
    if not allowed:
        raise PermissionError(f"{role} cannot read zone {zone}")
    return {"role": role, "zone": zone, "allowed": True, "live_enabled": False}


def refuse_forbidden(text: str) -> dict[str, object]:
    """Refuse personal data, wallet identifiers, and secret-like field names."""
    if FORBIDDEN_FIELD.search(text) or EMAIL_PATTERN.search(text) or WALLET_PATTERN.search(text):
        raise ValueError("forbidden field or identifier cannot enter a research zone")
    return {"accepted": True, "zone": "research-derived", "live_enabled": False}


def seal(label: str, body: str) -> dict[str, object]:
    """Hash a research body. The seal is an integrity check, not an authorization."""
    if label not in {"SYNTHETIC", "PUBLIC_READ"}:
        raise ValueError("seal requires a research label")
    digest = hashlib.sha256(f"{label}|{body}".encode()).hexdigest()
    return {"label": label, "digest": digest, "algorithm": "sha256", "authorizes_live": False}
