"""Send the analyzed alert to Telegram, Discord, Slack and/or ntfy (whichever are configured)."""

from __future__ import annotations

import logging

import httpx

from .alerts import Alert
from .analyzer import Analysis
from .config import Settings

log = logging.getLogger(__name__)

_BIAS_ICON = {"bullish": "🟢", "bearish": "🔴", "neutral": "⚪"}


def format_message(alert: Alert, a: Analysis | None, *, filtered: bool = False,
                   error: str | None = None) -> tuple[str, str]:
    """Return (title, body) as plain text."""
    if a is None:
        title = f"⚠️ {alert.title()} (not analyzed)"
        body = f"Claude analysis failed: {error}\n\nRaw alert:\n{alert.raw_text[:1500]}"
        return title, body

    prefix = "🔕 FILTERED · " if filtered else ""
    title = f"{prefix}{_BIAS_ICON[a.bias]} {a.headline}"
    lines = [
        f"{alert.title()}" + (f" @ {alert.price:g}" if alert.price is not None else ""),
        f"Bias: {a.bias} · Confidence: {a.confidence}/100",
        "",
        a.summary,
    ]
    if a.reasoning:
        lines += ["", "Why:"] + [f"• {r}" for r in a.reasoning]
    if a.key_levels:
        lines += ["", "Levels: " + ", ".join(a.key_levels)]
    if a.risks:
        lines += ["", "Risks:"] + [f"• {r}" for r in a.risks]
    lines += ["", f"Next: {a.suggested_action}", "", "AI analysis — not financial advice."]
    return title, "\n".join(lines)


class Notifier:
    def __init__(self, settings: Settings, client: httpx.Client | None = None):
        self.s = settings
        self.http = client or httpx.Client(timeout=15.0)

    def channels(self) -> list[str]:
        out = []
        if self.s.telegram_bot_token and self.s.telegram_chat_ids:
            out.append("telegram")
        if self.s.discord_webhook_url:
            out.append("discord")
        if self.s.slack_webhook_url:
            out.append("slack")
        if self.s.ntfy_topic_url:
            out.append("ntfy")
        return out

    def send(self, title: str, body: str) -> bool:
        """Send to every configured channel. True if at least one succeeded."""
        ok = False
        for ch in self.channels():
            try:
                getattr(self, f"_send_{ch}")(title, body)
                ok = True
            except Exception:  # one broken channel must not block the others
                log.exception("Sending to %s failed", ch)
        if not self.channels():
            log.warning("No notification channel configured; message was:\n%s\n%s", title, body)
        return ok

    def _send_telegram(self, title: str, body: str) -> None:
        url = f"https://api.telegram.org/bot{self.s.telegram_bot_token}/sendMessage"
        for chat_id in self.s.telegram_chat_ids:
            r = self.http.post(url, json={"chat_id": chat_id, "text": f"{title}\n\n{body}"[:4096],
                                          "disable_web_page_preview": True})
            r.raise_for_status()

    def _send_discord(self, title: str, body: str) -> None:
        r = self.http.post(self.s.discord_webhook_url,
                           json={"content": f"**{title}**\n{body}"[:2000]})
        r.raise_for_status()

    def _send_slack(self, title: str, body: str) -> None:
        r = self.http.post(self.s.slack_webhook_url, json={"text": f"*{title}*\n{body}"})
        r.raise_for_status()

    def _send_ntfy(self, title: str, body: str) -> None:
        # ntfy headers must be latin-1, so the title goes in the body if it has emoji.
        r = self.http.post(self.s.ntfy_topic_url, content=f"{title}\n\n{body}".encode("utf-8"),
                           headers={"Title": "TradingView alert", "Tags": "chart_with_upwards_trend"})
        r.raise_for_status()
