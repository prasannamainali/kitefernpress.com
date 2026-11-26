"""Parsing TradingView alert bodies.

TradingView sends whatever text you put in the alert's "Message" box. If that text
is valid JSON it is sent with Content-Type application/json, otherwise text/plain.
We accept both: JSON is mapped onto known fields, plain text is kept as-is.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

from pydantic import BaseModel, Field

# Common names people use in their alert templates -> our field names.
_ALIASES: dict[str, tuple[str, ...]] = {
    "symbol": ("symbol", "ticker", "pair", "instrument"),
    "exchange": ("exchange",),
    "interval": ("interval", "timeframe", "tf"),
    "price": ("price", "close", "last"),
    "action": ("action", "side", "signal", "direction", "order_action"),
    "indicator": ("indicator", "strategy", "study", "source"),
    "message": ("message", "text", "comment", "alert_message"),
}

SECRET_FIELDS = ("passphrase", "secret", "token")


class Alert(BaseModel):
    symbol: str | None = None
    exchange: str | None = None
    interval: str | None = None
    price: float | None = None
    action: str | None = None
    indicator: str | None = None
    message: str | None = None
    # Every field TradingView sent (minus secrets), so Claude sees custom values too.
    raw: dict[str, Any] = Field(default_factory=dict)
    raw_text: str = ""

    def fingerprint(self) -> str:
        """Stable hash used to drop duplicate deliveries."""
        return hashlib.sha256(self.raw_text.encode("utf-8")).hexdigest()

    def title(self) -> str:
        parts = [p for p in (self.symbol, self.interval, self.action) if p]
        return " · ".join(parts) or "TradingView alert"


def _pick(data: dict[str, Any], names: tuple[str, ...]) -> Any:
    lowered = {k.lower(): v for k, v in data.items()}
    for n in names:
        if n in lowered and lowered[n] not in (None, ""):
            return lowered[n]
    return None


def _to_float(v: Any) -> float | None:
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def parse_alert(body: bytes | str) -> tuple[Alert, str | None]:
    """Return the parsed alert and any secret found in the body."""
    text = body.decode("utf-8", errors="replace") if isinstance(body, bytes) else body
    text = text.strip()

    try:
        data = json.loads(text)
    except ValueError:
        data = None

    if not isinstance(data, dict):
        return Alert(message=text, raw_text=text), None

    secret = None
    for f in SECRET_FIELDS:
        if f in data:
            secret = str(data.pop(f))
    clean_text = json.dumps(data, sort_keys=True)

    return (
        Alert(
            symbol=_str(_pick(data, _ALIASES["symbol"])),
            exchange=_str(_pick(data, _ALIASES["exchange"])),
            interval=_str(_pick(data, _ALIASES["interval"])),
            price=_to_float(_pick(data, _ALIASES["price"])),
            action=_str(_pick(data, _ALIASES["action"])),
            indicator=_str(_pick(data, _ALIASES["indicator"])),
            message=_str(_pick(data, _ALIASES["message"])),
            raw=data,
            raw_text=clean_text,
        ),
        secret,
    )


def _str(v: Any) -> str | None:
    return None if v is None else str(v)
