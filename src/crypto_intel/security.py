"""Cyber and data-security controls for the information system.

This is a research control plane, not a certified security product.
Version 0.5 expands redaction patterns further (tokens, base64, phone),
improves sanitization, and retains integrity helpers.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass

from crypto_intel.models import AuditEvent, Candle, ExecutionMode

SECRET_PATTERNS = (
    re.compile(r"(?i)(api[_-]?key|secret|password|token|private[_-]?key|mnemonic|seed)\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{8,}"),
    re.compile(r"\b(?:sk|pk)_(?:live|test)_[A-Za-z0-9]{8,}\b"),
    re.compile(r"\b[A-Z0-9._%+\-]+@[A-Z0-9.\-]+\.[A-Z]{2,}\b", re.IGNORECASE),
    re.compile(r"\b(5[HJK][1-9A-HJ-NP-Za-km-z]{49}|L[1-9A-HJ-NP-Za-km-z]{51}|K[1-9A-HJ-NP-Za-km-z]{51})\b"),  # WIF-like
    re.compile(r"(?i)(abandon|ability|able|about|above)\s+(abandon|ability|able|about|above)"),  # seed phrase start proxy
    re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b"),  # JWT-like
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),  # AWS access key style
    re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b"),  # Slack token style
    re.compile(r"\b[A-Za-z0-9+/]{40,}={0,2}\b"),  # longer base64-like
)

WALLET_PATTERN = re.compile(r"\b0x[a-fA-F0-9]{40}\b")
PHONE_PATTERN = re.compile(r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b")


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
    DataClassification("phone", "personal", "do not collect"),
)


def redact(text: str) -> str:
    cleaned = text
    for pattern in SECRET_PATTERNS:
        cleaned = pattern.sub("[REDACTED]", cleaned)
    cleaned = WALLET_PATTERN.sub("[WALLET]", cleaned)
    cleaned = PHONE_PATTERN.sub("[PHONE]", cleaned)
    return cleaned


def contains_secret(text: str) -> bool:
    return (
        any(pattern.search(text) for pattern in SECRET_PATTERNS)
        or bool(WALLET_PATTERN.search(text))
        or bool(PHONE_PATTERN.search(text))
    )


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


def sanitize_input(text: str, max_len: int = 2000) -> str:
    """Research sanitization: redact, strip control characters, and length-limit."""
    cleaned = redact(text)
    cleaned = re.sub(r"[\x00-\x1F\x7F]", "", cleaned)
    return cleaned[:max_len]


class AuditLog:
    """Append-only hash chain. Tampering changes the next digest."""

    def __init__(self) -> None:
        self.events: list[AuditEvent] = []
        self._previous = "GENESIS"

    def append(self, action: str, detail: str) -> AuditEvent:
        safe_detail = sanitize_input(detail)
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
