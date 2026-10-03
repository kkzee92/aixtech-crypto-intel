"""Defensive control catalog for the research information system.

Mapped loosely to NIST CSF functions so a reviewer can see coverage. This is
not a certification, not a penetration method, and not legal advice.
"""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse

from crypto_intel.catalog import CATALOG_VERSION, parameter_digest
from crypto_intel.posture import Role

ALLOWED_HOSTS = frozenset(
    {
        "api.coingecko.com",
        "api.binance.com",
        "fapi.binance.com",
        "api.bybit.com",
    }
)
REFUSED_PATH_MARKERS = ("/order", "/withdraw", "/transfer", "/sapi/")


@dataclass(frozen=True)
class Control:
    control_id: str
    function: str
    name: str
    implementation: str


CONTROL_CATALOG: tuple[Control, ...] = (
    Control("ID.AM-1", "identify", "Research asset inventory", "fixtures labelled SYNTHETIC; catalog version recorded"),
    Control("ID.GV-1", "identify", "Paper-only policy", "assert_paper_only refuses non-paper modes"),
    Control("PR.AC-1", "protect", "Role separation", "researcher, auditor, operator; no trader role"),
    Control("PR.AC-4", "protect", "Credential refusal", "trade, withdraw, transfer, and order names are refused"),
    Control("PR.DS-1", "protect", "Secret redaction", "audit details pass through redact before storage"),
    Control("PR.DS-5", "protect", "Egress allowlist", "public market hosts only; order paths refused"),
    Control("PR.IP-3", "protect", "Parameter integrity", "catalog digest recorded on each control report"),
    Control("DE.CM-1", "detect", "Feed integrity", "non-positive, stale, or 25 percent jump prints are flagged"),
    Control("DE.CM-3", "detect", "Audit chain", "SHA-256 hash chain over sequence, action, and redacted detail"),
    Control("RS.MI-1", "respond", "Kill switch", "operator engage; clear needs operator request plus auditor confirm"),
    Control("RC.RP-1", "recover", "Human clear", "kill switch cannot be cleared by the same role that requested it"),
    Control("PR.DS-6", "protect", "Data retention", "secrets and personal data have zero retention"),
    Control("PR.AC-6", "protect", "Read-key rotation", "read-only market names rotate at 90 days"),
    Control("DE.CM-4", "detect", "Series quality", "duplicate time, zero volume, or 40 percent jump blocks size"),
    Control("DE.CM-5", "detect", "Clock skew", "feed clock skew above 120 seconds is not accepted"),
    Control("PR.IP-4", "protect", "Confirmation overlay", "directional ideas need a second class-specific check"),
    Control(
        "DE.CM-6",
        "detect",
        "Cross-asset overlay",
        "benchmark stress, breadth, and stablecoin contagion veto paper size",
    ),
    Control("PR.DS-7", "protect", "Data classification", "unlabelled, personal, and secret payloads are refused"),
    Control("PR.AC-7", "protect", "Key scope allowlist", "only market_read and public_ticker; trade scopes refused"),
    Control("RS.RP-1", "respond", "Incident playbook", "contain with kill switch; no automated live resume"),
    Control("PR.IP-5", "protect", "Class enhancement", "per-class overlay can shrink paper size and cannot raise it"),
)


class DualControl:
    """Kill switch with two-person clear. Neither role can place an order."""

    def __init__(self) -> None:
        self.engaged = False
        self.clear_requested_by: Role | None = None

    def engage(self, role: Role) -> None:
        if role is not Role.OPERATOR:
            raise PermissionError("only the operator may engage the kill switch")
        self.engaged = True
        self.clear_requested_by = None

    def request_clear(self, role: Role) -> None:
        if role is not Role.OPERATOR:
            raise PermissionError("only the operator may request a clear")
        if not self.engaged:
            raise ValueError("kill switch is not engaged")
        self.clear_requested_by = role

    def confirm_clear(self, role: Role) -> None:
        if role is not Role.AUDITOR:
            raise PermissionError("auditor confirmation is required to clear")
        if self.clear_requested_by is not Role.OPERATOR:
            raise PermissionError("clear requires a prior operator request")
        self.engaged = False
        self.clear_requested_by = None


def assert_read_only_endpoint(url: str) -> None:
    """Refuse non-HTTPS, unknown hosts, and order or withdrawal paths.

    This does not open a connection. It is an egress policy check.
    """
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    if parsed.scheme != "https" or not host:
        raise PermissionError("market reads must be https")
    if host not in ALLOWED_HOSTS:
        raise PermissionError("host is outside the research egress allowlist")
    path = parsed.path.lower()
    if any(marker in path for marker in REFUSED_PATH_MARKERS):
        raise PermissionError("order or withdrawal paths are refused")


def control_report() -> dict[str, object]:
    return {
        "catalog_version": CATALOG_VERSION,
        "parameter_digest": parameter_digest(),
        "paper_only": True,
        "live_enabled": False,
        "egress_hosts": sorted(ALLOWED_HOSTS),
        "controls": [
            {
                "id": item.control_id,
                "function": item.function,
                "name": item.name,
                "implementation": item.implementation,
            }
            for item in CONTROL_CATALOG
        ],
    }
