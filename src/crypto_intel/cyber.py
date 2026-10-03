"""Cyber and data-security policy checks for the information system.

These functions refuse trade scopes and describe an incident path. They do not
generate keys, store seeds, open sockets, or automate a return to live trading.
"""

from __future__ import annotations

import hashlib
import re

ALLOWED_SCOPES = frozenset({"market_read", "public_ticker"})
REFUSED_SCOPE_MARKERS = ("trade", "withdraw", "transfer", "order", "futures_write", "margin")
SEED_MARKERS = re.compile(r"\b(seed phrase|mnemonic|private key|xprv)\b", re.IGNORECASE)


def assert_key_scope(scope: str) -> str:
    """Allow only a read-only market scope. Never a trade or withdrawal scope."""
    normalized = scope.strip().lower().replace("-", "_")
    if any(marker in normalized for marker in REFUSED_SCOPE_MARKERS):
        raise PermissionError("key scope is refused on the information system")
    if normalized not in ALLOWED_SCOPES:
        raise PermissionError("key scope is outside the research allowlist")
    return normalized


def assert_no_seed_material(text: str) -> None:
    """Refuse text that looks like key ceremony material. Does not parse secrets."""
    if SEED_MARKERS.search(text):
        raise PermissionError("seed or private-key material is refused")


def key_ceremony() -> dict[str, object]:
    """Checklist only. This module cannot create or custody a key."""
    return {
        "live_enabled": False,
        "seed_in_repo": False,
        "automated_keygen": False,
        "steps": [
            "two people present; neither role can place an order",
            "offline machine, no copy into git or chat logs",
            "read scope only if a market key is ever issued outside this repo",
            "trade and withdrawal keys are never created here",
            "rotation evidence is a date and a scope name, not key material",
        ],
    }


def incident_playbook() -> dict[str, object]:
    """Containment path. Recovery cannot re-enable live execution."""
    return {
        "live_enabled": False,
        "automated_remediation": False,
        "phases": [
            {"phase": "detect", "action": "verify the audit chain and source attestation"},
            {"phase": "contain", "action": "operator engages the kill switch; paper size goes to zero"},
            {"phase": "eradicate", "action": "a human rotates any pasted secret outside this repository"},
            {"phase": "recover", "action": "auditor confirms clear; live trading stays disabled"},
        ],
    }


def research_packet(catalog_digest: str, label: str) -> dict[str, object]:
    """Bind a catalog digest to a fixture label. Not a signature over orders."""
    if label not in {"SYNTHETIC", "PUBLIC_READ"}:
        raise ValueError("research packet requires a research label")
    material = f"{catalog_digest}:{label}".encode()
    return {
        "catalog_digest": catalog_digest,
        "label": label,
        "packet_digest": hashlib.sha256(material).hexdigest(),
        "live_enabled": False,
    }
