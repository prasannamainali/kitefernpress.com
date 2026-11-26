"""Settings, read from environment variables (or a .env file)."""

from __future__ import annotations

import os
from dataclasses import dataclass, field


def _load_dotenv(path: str = ".env") -> None:
    """Tiny .env loader so the service has no extra dependency for it."""
    if not os.path.exists(path):
        return
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_dotenv()


def _csv(name: str) -> list[str]:
    return [v.strip() for v in os.getenv(name, "").split(",") if v.strip()]


@dataclass(frozen=True)
class Settings:
    # Shared secret TradingView must send (in the URL path, ?token=, or a "passphrase" JSON field).
    webhook_secret: str = os.getenv("WEBHOOK_SECRET", "")

    # Claude
    claude_model: str = os.getenv("CLAUDE_MODEL", "claude-opus-5-5")
    claude_effort: str = os.getenv("CLAUDE_EFFORT", "medium")  # low | medium | high | xhigh | max

    # Only notify when Claude says "notify" AND confidence >= this (0-100).
    min_confidence: int = int(os.getenv("MIN_CONFIDENCE", "60"))
    # If true, suppressed alerts are still sent, clearly marked as "filtered".
    send_suppressed: bool = os.getenv("SEND_SUPPRESSED", "false").lower() == "true"
    # Ignore an identical alert received again within this many seconds.
    dedup_window_seconds: int = int(os.getenv("DEDUP_WINDOW_SECONDS", "60"))
    # How many earlier alerts for the same symbol Claude sees as context.
    history_size: int = int(os.getenv("HISTORY_SIZE", "10"))
    # Extra guidance for Claude: your strategy, risk rules, what matters to you.
    trader_context: str = os.getenv("TRADER_CONTEXT", "")

    db_path: str = os.getenv("DB_PATH", "alerts.db")

    # Notification channels: any that are configured are used.
    telegram_bot_token: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    telegram_chat_ids: list[str] = field(default_factory=lambda: _csv("TELEGRAM_CHAT_IDS"))
    discord_webhook_url: str = os.getenv("DISCORD_WEBHOOK_URL", "")
    slack_webhook_url: str = os.getenv("SLACK_WEBHOOK_URL", "")
    ntfy_topic_url: str = os.getenv("NTFY_TOPIC_URL", "")  # e.g. https://ntfy.sh/my-secret-topic


settings = Settings()
