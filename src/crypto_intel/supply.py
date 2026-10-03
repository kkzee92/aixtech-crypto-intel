"""Version 0.7 cyber and data-security architecture checks.

Supply-chain and data-flow policy for the information system. These functions
do not fetch dependencies, generate keys, store seeds, or enable live trading.
"""

from __future__ import annotations

import hashlib

RUNTIME_THIRD_PARTY: tuple[str, ...] = ()
DATA_FLOW: tuple[dict[str, object], ...] = (
    {"stage": "fixture", "classification": "research", "retention": "repository", "pii": False},
    {"stage": "attestation", "classification": "restricted_ops", "retention": "session", "pii": False},
    {"stage": "brief", "classification": "research", "retention": "session", "pii": False},
    {"stage": "audit", "classification": "restricted_ops", "retention": "local_operator", "pii": False},
)
ROLE_MATRIX: dict[str, dict[str, bool]] = {
    "researcher": {"scan": True, "approve_clear": False, "kill_switch": False, "place_order": False},
    "reviewer": {"scan": True, "approve_clear": True, "kill_switch": False, "place_order": False},
    "auditor": {"scan": False, "approve_clear": False, "kill_switch": False, "place_order": False},
    "operator": {"scan": False, "approve_clear": False, "kill_switch": True, "place_order": False},
}


def dependency_posture() -> dict[str, object]:
    """Runtime third-party imports are intentionally empty. Dev tools stay out of this path."""
    return {
        "runtime_third_party": list(RUNTIME_THIRD_PARTY),
        "network_imports": False,
        "live_enabled": False,
        "order_path": False,
    }


def data_flow() -> list[dict[str, object]]:
    """Declared data classes. No stage is allowed to carry personal data."""
    rows = []
    for stage in DATA_FLOW:
        if stage["pii"]:
            raise PermissionError("personal data is refused in the information flow")
        rows.append(dict(stage))
    return rows


def role_allows(role: str, action: str) -> bool:
    """Least-privilege check. No role can place an order."""
    if role not in ROLE_MATRIX:
        raise PermissionError("unknown information-system role")
    if action == "place_order":
        return False
    return bool(ROLE_MATRIX[role].get(action, False))


def assert_break_glass(*, requested_live: bool) -> dict[str, object]:
    """Break-glass can contain a paper run. It cannot enable live trading."""
    if requested_live:
        raise PermissionError("break-glass cannot enable live trading")
    return {"live_enabled": False, "paper_only": True, "order_path": False}


def fixture_integrity(label: str, text: str) -> dict[str, object]:
    """Bind a fixture body to a research label. Not a signature over orders."""
    if label != "SYNTHETIC":
        raise ValueError("fixture integrity requires the SYNTHETIC label")
    if "SYNTHETIC" not in text:
        raise ValueError("fixture body must carry the SYNTHETIC label")
    return {
        "label": label,
        "digest": hashlib.sha256(text.encode()).hexdigest(),
        "live_enabled": False,
    }


def architecture_report() -> dict[str, object]:
    """Single defensive snapshot for the v0.7 information system."""
    return {
        "version": "0.7.0",
        "dependencies": dependency_posture(),
        "data_flow": data_flow(),
        "roles": ROLE_MATRIX,
        "break_glass_can_enable_live": False,
        "live_enabled": False,
    }
