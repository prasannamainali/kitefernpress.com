"""Webhook service: TradingView alert -> Claude analysis -> notification.

TradingView cancels a webhook request that takes longer than about 3 seconds, so the
endpoint stores the alert, answers 200 right away and does the analysis in the background.
"""

from __future__ import annotations

import hmac
import logging

from fastapi import BackgroundTasks, FastAPI, HTTPException, Request

from .alerts import Alert, parse_alert
from .analyzer import Analyzer
from .config import Settings, settings
from .notifier import Notifier, format_message
from .storage import Store

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("tv-analyzer")


def create_app(cfg: Settings = settings, analyzer: Analyzer | None = None,
               notifier: Notifier | None = None, store: Store | None = None) -> FastAPI:
    if not cfg.webhook_secret:
        raise RuntimeError("Set WEBHOOK_SECRET before starting the service.")

    app = FastAPI(title="TradingView Alert Analyzer")
    store = store or Store(cfg.db_path)
    analyzer = analyzer or Analyzer(cfg.claude_model, cfg.claude_effort, cfg.trader_context)
    notifier = notifier or Notifier(cfg)

    def process(alert_id: int, alert: Alert) -> None:
        history = store.history(alert.symbol, alert_id, cfg.history_size)
        try:
            analysis = analyzer.analyze(alert, history)
        except Exception as e:
            log.exception("Analysis failed for alert %s", alert_id)
            store.update(alert_id, error=str(e))
            # Fail open: a signal the trader never sees is worse than an unanalyzed one.
            title, body = format_message(alert, None, error=str(e))
            notifier.send(title, body)
            return

        passes = analysis.decision == "notify" and analysis.confidence >= cfg.min_confidence
        sent = False
        if passes or cfg.send_suppressed:
            title, body = format_message(alert, analysis, filtered=not passes)
            sent = notifier.send(title, body)
        log.info("Alert %s %s: %s %s/100 -> %s", alert_id, alert.title(), analysis.decision,
                 analysis.confidence, "sent" if sent else "not sent")
        store.update(alert_id, analysis=analysis.model_dump(), notified=sent)

    def authorized(request: Request, path_token: str | None, body_secret: str | None) -> bool:
        candidates = [path_token, request.query_params.get("token"), body_secret,
                      request.headers.get("x-webhook-secret")]
        return any(c and hmac.compare_digest(c, cfg.webhook_secret) for c in candidates)

    async def receive(request: Request, background: BackgroundTasks, token: str | None = None):
        body = await request.body()
        if len(body) > 64_000:
            raise HTTPException(413, "Alert too large")
        alert, body_secret = parse_alert(body)
        if not authorized(request, token, body_secret):
            raise HTTPException(401, "Bad or missing secret")

        if store.is_duplicate(alert.fingerprint(), cfg.dedup_window_seconds):
            return {"status": "duplicate_ignored"}

        alert_id = store.insert(alert.fingerprint(), alert.symbol, alert.model_dump(exclude={"raw_text"}))
        background.add_task(process, alert_id, alert)
        return {"status": "accepted", "id": alert_id}

    @app.post("/webhook/{token}")
    async def webhook_with_path_token(token: str, request: Request, background: BackgroundTasks):
        return await receive(request, background, token)

    @app.post("/webhook")
    async def webhook(request: Request, background: BackgroundTasks):
        return await receive(request, background)

    @app.get("/alerts")
    def recent(request: Request, limit: int = 50):
        if not authorized(request, None, None):
            raise HTTPException(401, "Bad or missing secret")
        return store.recent(min(limit, 500))

    @app.get("/health")
    def health():
        return {"ok": True, "model": cfg.claude_model, "channels": notifier.channels()}

    return app

# Start with:  uvicorn app.main:create_app --factory --host 0.0.0.0 --port 8000
