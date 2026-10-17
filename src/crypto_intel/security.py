"""Cyber and data-security controls for the information system.

This is a research control plane, not a certified security product.
Version 0.12 expands secret patterns further (additional base58/WIF proxies, volume outlier in anomaly), adds rolling series digest helper, and reinforces zero-trust re-validation and data resilience notes.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from statistics import mean, pstdev, median

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
    re.compile(r"\bghp_[A-Za-z0-9]{36}\b"),  # GitHub PAT style
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),  # PEM private key header
    re.compile(r"\bsk-[A-Za-z0-9]{20,}\b"),  # OpenAI-style or similar
    re.compile(r"\b[A-Za-z0-9]{24}\.[A-Za-z0-9_-]{6}\.[A-Za-z0-9_-]{27}\b"),  # Discord token style
    re.compile(r"\bAIza[0-9A-Za-z\-_]{35}\b"),  # Google API key style
    re.compile(r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b"),  # UUID-like secrets proxy (cautious)
    re.compile(r"\b[0-9a-fA-F]{64}\b"),  # 64-hex private key style
    re.compile(r"\b[0-9a-fA-F]{128}\b"),  # longer hex private key style
    re.compile(r"\b\d{8,10}:[A-Za-z0-9_-]{35}\b"),  # Telegram bot token style
    re.compile(r"\b[1-9A-HJ-NP-Za-km-z]{87,88}\b"),  # Solana base58 private key proxy (approx length)
    re.compile(r"\b[1-9A-HJ-NP-Za-km-z]{44,50}\b"),  # shorter base58 proxy for some chains
    re.compile(r"(?i)wif\s*[:=]\s*['\"]?[5KL][1-9A-HJ-NP-Za-km-z]{50,}\b"),  # explicit WIF label
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
    DataClassification("exchange_api_key", "secret", "never stored", "read-only market keys only if ever added; separate from any trade key"),
    DataClassification("wallet_address", "sensitive-identifier", "do not fixture"),
    DataClassification("account_email", "personal", "do not collect"),
    DataClassification("seed_phrase", "secret", "never stored"),
    DataClassification("private_key", "secret", "never stored"),
    DataClassification("phone", "personal", "do not collect"),
    DataClassification("github_pat", "secret", "never stored"),
    DataClassification("discord_token", "secret", "never stored"),
    DataClassification("google_api_key", "secret", "never stored"),
    DataClassification("telegram_token", "secret", "never stored"),
    DataClassification("hex_private_key", "secret", "never stored"),
    DataClassification("solana_base58_key", "secret", "never stored"),
    DataClassification("wif_key", "secret", "never stored"),
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


def rolling_series_digest(candles: list[Candle], window: int = 20) -> str:
    """Research rolling digest over last window candles for anomaly detection."""
    if len(candles) < window:
        window = len(candles)
    return candles_integrity_digest(candles[-window:])


def anomaly_score(candles: list[Candle]) -> float:
    """Enhanced research anomaly score: max single-bar return + volume spike + return Z-score + volume Z-score + optional funding jump + volume IQR outlier.
    Higher values flag potential jumps or thin prints. Not a risk model.
    """
    if len(candles) < 5:
        return 0.0
    returns = [abs(candles[i].close / candles[i - 1].close - 1.0) for i in range(1, len(candles))]
    max_ret = max(returns) if returns else 0.0
    volumes = [c.volume for c in candles[-5:]]
    med_vol = median(volumes) if volumes else 1.0
    last_vol = candles[-1].volume
    vol_spike = last_vol / max(med_vol, 1.0)
    # Z-score on last few returns
    recent_rets = returns[-4:] if len(returns) >= 4 else returns
    if len(recent_rets) > 1:
        mu = mean(recent_rets)
        sigma = pstdev(recent_rets) or 1.0
        z = abs((recent_rets[-1] - mu) / sigma)
    else:
        z = 0.0
    # Volume Z-score
    if len(volumes) > 1:
        vmu = mean(volumes)
        vsigma = pstdev(volumes) or 1.0
        vz = abs((last_vol - vmu) / vsigma)
    else:
        vz = 0.0
    # Funding jump proxy if present
    funding_jump = 0.0
    if len(candles) > 1 and abs(candles[-1].funding_rate - candles[-2].funding_rate) > 0.001:
        funding_jump = 0.5
    # Simple IQR outlier on volume
    iqr_outlier = 0.0
    if len(volumes) >= 4:
        sorted_v = sorted(volumes)
        q1, q3 = sorted_v[1], sorted_v[-2]
        iqr = q3 - q1
        if last_vol > q3 + 1.5 * iqr:
            iqr_outlier = 0.3
    return round(max_ret * 10 + min(vol_spike, 5.0) * 0.2 + min(z, 5.0) * 0.15 + min(vz, 5.0) * 0.1 + funding_jump + iqr_outlier, 4)


def timestamp_freshness(candles: list[Candle], max_age_minutes: int = 15) -> bool:
    """Research helper: check if the latest timestamp is within max_age_minutes of now.
    Assumes ISO-like timestamps; returns False on parse failure or stale.
    """
    if not candles:
        return False
    try:
        last_ts = candles[-1].timestamp
        if "T" in last_ts:
            dt = datetime.fromisoformat(last_ts.replace("Z", "+00:00"))
        else:
            return False
        now = datetime.now(timezone.utc)
        age = (now - dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else now - dt).total_seconds() / 60
        return age <= max_age_minutes
    except Exception:
        return False


def series_consistency_check(candles: list[Candle], max_jump: float = 0.25) -> bool:
    """Research helper: flag if any consecutive close jump exceeds max_jump.
    Returns True if consistent (no extreme jumps).
    """
    if len(candles) < 2:
        return True
    for i in range(1, len(candles)):
        if candles[i].close / candles[i - 1].close - 1.0 > max_jump:
            return False
    return True


def sanitize_input(text: str, max_len: int = 2000) -> str:
    """Research sanitization: redact, strip control characters, and length-limit.
    Zero-trust: callers re-evaluate independently; no assumed clean state.
    Key separation: any future market keys must be read-only and distinct from trade credentials.
    Recommend encryption at rest for logs in production research deployments; prefer local residency.
    """
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
