"""Cyber and data-security control checks for the information system.

This is a research control plane. It is not a certified security product.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from enum import Enum

from crypto_intel.models import ExecutionMode

TRADE_MARKERS = ("trade", "withdraw", "transfer", "order")
READ_MARKERS = ("read", "market", "public")


class Role(str, Enum):
    RESEARCHER = "researcher"
    AUDITOR = "auditor"
    OPERATOR = "operator"


class Severity(str, Enum):
    INFO = "info"
    WATCH = "watch"
    HIGH = "high"


ALLOWED = {
    Role.RESEARCHER: frozenset({"scan", "backtest", "read_audit"}),
    Role.AUDITOR: frozenset({"read_audit", "verify_chain", "scan"}),
    Role.OPERATOR: frozenset({"scan", "kill_switch", "read_audit"}),
}


@dataclass(frozen=True)
class ControlResult:
    name: str
    ok: bool
    severity: Severity
    detail: str


def attest_source(label: str, body: str) -> str:
    if label != "SYNTHETIC" and label != "PUBLIC_READ":
        raise ValueError("source label must be SYNTHETIC or PUBLIC_READ")
    material = f"{label}|{body}".encode()
    return hashlib.sha256(material).hexdigest()


def refuse_trade_secret(name: str) -> None:
    lowered = name.lower()
    if any(marker in lowered for marker in TRADE_MARKERS):
        raise PermissionError("trade or withdrawal credentials are out of scope")
    if "key" in lowered and not any(marker in lowered for marker in READ_MARKERS):
        raise PermissionError("only explicitly read-only market credentials are discussable")


def allow(role: Role, action: str) -> bool:
    if action in {"place_order", "withdraw", "enable_live"}:
        return False
    return action in ALLOWED[role]


def feed_status(price: float, previous: float | None, age_seconds: float) -> ControlResult:
    if price <= 0:
        return ControlResult("feed", False, Severity.HIGH, "non-positive price")
    if age_seconds > 900:
        return ControlResult("feed", False, Severity.WATCH, "stale public ticker")
    if previous and previous > 0 and abs(price / previous - 1.0) > 0.25:
        return ControlResult("feed", False, Severity.HIGH, "jump above 25 percent versus prior print")
    return ControlResult("feed", True, Severity.INFO, "public ticker within research bounds")


def mode_status(mode: ExecutionMode) -> ControlResult:
    if mode is not ExecutionMode.PAPER:
        return ControlResult("mode", False, Severity.HIGH, "non-paper mode refused")
    return ControlResult("mode", True, Severity.INFO, "paper mode")
