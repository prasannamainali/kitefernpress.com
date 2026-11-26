"""End-to-end tests with Claude and the notification channels faked out (no network, no cost)."""

from __future__ import annotations

import json
from dataclasses import replace
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.alerts import parse_alert
from app.analyzer import Analyzer
from app.config import Settings
from app.main import create_app
from app.storage import Store

SECRET = "test-secret"


def fake_response(payload: dict, stop_reason: str = "end_turn"):
    return SimpleNamespace(stop_reason=stop_reason,
                           content=[SimpleNamespace(type="text", text=json.dumps(payload))])


def analysis(decision="notify", confidence=80, bias="bullish"):
    return {
        "decision": decision, "bias": bias, "confidence": confidence,
        "headline": "BTC breakout above range", "summary": "RSI crossed up with momentum.",
        "reasoning": ["Agrees with prior 4h buy"], "risks": ["Close back below 67000"],
        "key_levels": ["67000"], "suggested_action": "Watch next 1h close",
    }


class FakeClaude:
    def __init__(self, payload=None, stop_reason="end_turn"):
        self.calls = []
        self.payload = payload or analysis()
        self.stop_reason = stop_reason
        self.beta = SimpleNamespace(messages=SimpleNamespace(create=self._create))

    def _create(self, **kwargs):
        self.calls.append(kwargs)
        return fake_response(self.payload, self.stop_reason)


class FakeNotifier:
    def __init__(self):
        self.sent = []

    def channels(self):
        return ["fake"]

    def send(self, title, body):
        self.sent.append((title, body))
        return True


@pytest.fixture
def make(tmp_path):
    def _make(claude=None, **overrides):
        cfg = replace(Settings(), webhook_secret=SECRET, db_path=str(tmp_path / "a.db"), **overrides)
        claude = claude or FakeClaude()
        notifier = FakeNotifier()
        app = create_app(cfg, analyzer=Analyzer("claude-opus-5-5", "medium", client=claude),
                         notifier=notifier, store=Store(cfg.db_path))
        return TestClient(app), claude, notifier
    return _make


ALERT = {"ticker": "BTCUSD", "interval": "60", "close": "67250.5", "action": "buy",
         "indicator": "RSI cross", "passphrase": SECRET}


def test_rejects_bad_secret(make):
    client, _, notifier = make()
    r = client.post("/webhook", json={**ALERT, "passphrase": "wrong"})
    assert r.status_code == 401
    assert notifier.sent == []


def test_notify_flow_with_body_secret(make):
    client, claude, notifier = make()
    r = client.post("/webhook", json=ALERT)
    assert r.status_code == 200 and r.json()["status"] == "accepted"
    assert len(notifier.sent) == 1
    title, body = notifier.sent[0]
    assert "BTC breakout" in title and "Confidence: 80/100" in body
    # The secret never reaches Claude.
    assert SECRET not in json.dumps(claude.calls[0]["messages"])
    assert claude.calls[0]["output_config"]["format"]["type"] == "json_schema"


def test_path_token_and_plain_text(make):
    client, claude, notifier = make()
    r = client.post(f"/webhook/{SECRET}", content="BTCUSD crossing 67000",
                    headers={"content-type": "text/plain"})
    assert r.status_code == 200
    assert "BTCUSD crossing 67000" in claude.calls[0]["messages"][0]["content"]
    assert len(notifier.sent) == 1


def test_suppressed_and_low_confidence(make):
    client, _, notifier = make(FakeClaude(analysis(decision="suppress")))
    client.post("/webhook", json=ALERT)
    assert notifier.sent == []

    client, _, notifier = make(FakeClaude(analysis(confidence=40)), min_confidence=60)
    client.post("/webhook", json={**ALERT, "close": "1"})
    assert notifier.sent == []


def test_send_suppressed_marks_filtered(make):
    client, _, notifier = make(FakeClaude(analysis(decision="suppress")), send_suppressed=True)
    client.post("/webhook", json=ALERT)
    assert notifier.sent[0][0].startswith("🔕 FILTERED")


def test_duplicate_ignored(make):
    client, claude, _ = make()
    client.post("/webhook", json=ALERT)
    r = client.post("/webhook", json=ALERT)
    assert r.json()["status"] == "duplicate_ignored"
    assert len(claude.calls) == 1


def test_history_passed_to_claude(make):
    client, claude, _ = make()
    client.post("/webhook", json=ALERT)
    client.post("/webhook", json={**ALERT, "action": "sell", "close": "66000"})
    second = claude.calls[1]["messages"][0]["content"]
    assert "recent_alerts_for_symbol_oldest_first" in second and '"buy"' in second


def test_refusal_fails_open(make):
    client, _, notifier = make(FakeClaude(stop_reason="refusal"))
    client.post("/webhook", json=ALERT)
    assert "not analyzed" in notifier.sent[0][0]


def test_alerts_endpoint_requires_secret(make):
    client, _, _ = make()
    client.post("/webhook", json=ALERT)
    assert client.get("/alerts").status_code == 401
    rows = client.get("/alerts", params={"token": SECRET}).json()
    assert rows[0]["symbol"] == "BTCUSD" and rows[0]["notified"]


def test_parse_alert_aliases():
    alert, secret = parse_alert(json.dumps(ALERT))
    assert (alert.symbol, alert.price, alert.action, secret) == ("BTCUSD", 67250.5, "buy", SECRET)
    assert "passphrase" not in alert.raw
