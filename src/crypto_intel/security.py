"""Cyber and data-security controls for the information system.

This is a research control plane, not a certified security product.
Version 0.3 expands redaction patterns, data classification, and integrity helpers.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass

from crypto_intel.models import AuditEvent, Candle, ExecutionMode

SECRET_PATTERNS = (
    re.compile(r"(?i)(api[_-]?key|secret|password|token|private[_-]?key)\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{12,}"),
    re.compile(r"\b(?:sk|pk)_(?:live|test)_[A-Za-z0-9]{8,}\b"),
    re.compile(r"\b[A-Z0-9._%+\-]+@[A-Z0-9.\-]+\.[A-Z]{2,}\b", re.IGNORECASE),
    re.compile(r"\b(5[HJK][1-9A-HJ-NP-Za-km-z]{49}|L[1-9A-HJ-NP-Za-km-z]{51}|K[1-9A-HJ-NP-Za-km-z]{51})\b"),  # WIF-like
    re.compile(r"(?i)(abandon|ability|able|about|above)\s+(abandon|ability|able|about|above)"),  # seed phrase start proxy
)

WALLET_PATTERN = re.compile(r"\b0x[a-fA-F0-9]{40}\b")


@dataclass(frozen=True)
class DataClassification:
    field: str
    level: str
    retention: str
    notes: str = ""


CLASSIFICATION = (
    DataClassification("symbol", "public", "research retention"),
    DataClassification("ohlcv", "public-market", "research retention"),
    DataClassification("funding_rate", "public-market", "research retention"),
    DataClassification("exchange_api_key", "secret", "never stored", "read-only market keys only if ever added"),
    DataClassification("wallet_address", "sensitive-identifier", "do not fixture"),
    DataClassification("account_email", "personal", "do not collect"),
    DataClassification("seed_phrase", "secret", "never stored"),
    DataClassification("private_key", "secret", "never stored"),
)


def redact(text: str) -> str:
    cleaned = text
    for pattern in SECRET_PATTERNS:
        cleaned = pattern.sub("[REDACTED]", cleaned)
    return WALLET_PATTERN.sub("[WALLET]", cleaned)


def contains_secret(text: str) -> bool:
    return any(pattern.search(text) for pattern in SECRET_PATTERNS) or bool(WALLET_PATTERN.search(text))


def assert_paper_only(mode: ExecutionMode) -> None:
    if mode is not ExecutionMode.PAPER:
        raise PermissionError("live execution is disabled; this system is paper-only")


def hash_event(previous_hash: str, sequence: int, action: str, detail: str) -> str:
    material = f"{previous_hash}|{sequence}|{action}|{detail}".encode()
    return hashlib.sha256(material).hexdigest()


def candles_integrity_digest(candles: list[Candle]) -> str:
    """SHA-256 over ordered OHLCV fields for fixture or series attestation."""
    material = "|".join(
        f"{c.symbol}:{c.timestamp}:{c.open}:{c.high}:{c.low}:{c.close}:{c.volume}:{c.funding_rate}"
        for c in candles
    ).encode()
    return hashlib.sha256(material).hexdigest()


class AuditLog:
    """Append-only hash chain. Tampering changes the next digest."""

    def __init__(self) -> None:
        self.events: list[AuditEvent] = []
        self._previous = "GENESIS"

    def append(self, action: str, detail: str) -> AuditEvent:
        safe_detail = redact(detail)
        sequence = len(self.events) + 1
        digest = hash_event(self._previous, sequence, action, safe_detail)
        event = AuditEvent(sequence, action, safe_detail, self._previous, digest)
        self.events.append(event)
        self._previous = digest
        return event

    def verify(self) -> bool:
        previous = "GENESIS"
        for event in self.events:
            expected = hash_event(previous, event.sequence, event.action, event.detail)
            if event.previous_hash != previous or event.digest != expected:
                return False
            previous = event.digest
        return True
