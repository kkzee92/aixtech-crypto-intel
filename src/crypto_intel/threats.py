"""STRIDE threat map for the paper information system.

Each row names a defensive control already implemented in this repository.
It does not describe an attack procedure.
"""

from __future__ import annotations

from crypto_intel.controls import CONTROL_CATALOG

THREATS: tuple[dict[str, str], ...] = (
    {
        "stride": "spoofing",
        "scenario": "A fixture or ticker is presented as market data without a source label.",
        "control_id": "ID.AM-1",
        "response": "Require SYNTHETIC or PUBLIC_READ attestation before a scan.",
    },
    {
        "stride": "tampering",
        "scenario": "Research parameters change without a reviewer noticing.",
        "control_id": "PR.IP-3",
        "response": "Publish the catalog version and parameter digest on the control report.",
    },
    {
        "stride": "repudiation",
        "scenario": "A paper decision cannot be traced to the rule that produced it.",
        "control_id": "DE.CM-3",
        "response": "Append a hash-chained audit event for signal, risk, and paper fill.",
    },
    {
        "stride": "information_disclosure",
        "scenario": "A secret-like string or personal identifier reaches a log or fixture.",
        "control_id": "PR.DS-1",
        "response": "Redact secret-like strings and refuse personal or secret data classes.",
    },
    {
        "stride": "denial_of_service",
        "scenario": "A stale or jumping feed keeps producing directional paper size.",
        "control_id": "DE.CM-1",
        "response": "Flag non-positive, stale, or large-jump prints and halt size on quality failure.",
    },
    {
        "stride": "elevation",
        "scenario": "A research role is used to place an order or clear a kill switch alone.",
        "control_id": "PR.AC-1",
        "response": "No trader role. Paper-only mode. Kill-switch clear needs operator plus auditor.",
    },
    {
        "stride": "tampering",
        "scenario": "A single-symbol signal ignores benchmark stress or a stablecoin basket break.",
        "control_id": "DE.CM-6",
        "response": "Cross-asset spillover and contagion overlays set directional paper size to zero.",
    },
)


def threat_report() -> dict[str, object]:
    known = {item.control_id for item in CONTROL_CATALOG}
    rows = []
    for threat in THREATS:
        rows.append({**threat, "control_present": threat["control_id"] in known})
    return {
        "model": "STRIDE",
        "paper_only": True,
        "live_enabled": False,
        "coverage": all(row["control_present"] for row in rows),
        "threats": rows,
    }
