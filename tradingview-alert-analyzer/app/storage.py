"""SQLite log of every alert and Claude's verdict (also gives Claude per-symbol history)."""

from __future__ import annotations

import json
import sqlite3
import threading
import time
from typing import Any


class Store:
    def __init__(self, path: str):
        self._lock = threading.Lock()
        self._db = sqlite3.connect(path, check_same_thread=False)
        self._db.row_factory = sqlite3.Row
        self._db.execute(
            """
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                received_at REAL NOT NULL,
                fingerprint TEXT NOT NULL,
                symbol TEXT,
                alert_json TEXT NOT NULL,
                analysis_json TEXT,
                notified INTEGER DEFAULT 0,
                error TEXT
            )
            """
        )
        self._db.execute("CREATE INDEX IF NOT EXISTS ix_symbol ON alerts(symbol, received_at)")
        self._db.execute("CREATE INDEX IF NOT EXISTS ix_fp ON alerts(fingerprint, received_at)")
        self._db.commit()

    def is_duplicate(self, fingerprint: str, window_seconds: int) -> bool:
        if window_seconds <= 0:
            return False
        with self._lock:
            row = self._db.execute(
                "SELECT 1 FROM alerts WHERE fingerprint = ? AND received_at > ? LIMIT 1",
                (fingerprint, time.time() - window_seconds),
            ).fetchone()
        return row is not None

    def insert(self, fingerprint: str, symbol: str | None, alert: dict[str, Any]) -> int:
        with self._lock:
            cur = self._db.execute(
                "INSERT INTO alerts (received_at, fingerprint, symbol, alert_json) VALUES (?, ?, ?, ?)",
                (time.time(), fingerprint, symbol, json.dumps(alert)),
            )
            self._db.commit()
            return int(cur.lastrowid)

    def update(self, alert_id: int, *, analysis: dict | None = None, notified: bool = False,
               error: str | None = None) -> None:
        with self._lock:
            self._db.execute(
                "UPDATE alerts SET analysis_json = ?, notified = ?, error = ? WHERE id = ?",
                (json.dumps(analysis) if analysis else None, int(notified), error, alert_id),
            )
            self._db.commit()

    def history(self, symbol: str | None, before_id: int, limit: int) -> list[dict[str, Any]]:
        if not symbol or limit <= 0:
            return []
        with self._lock:
            rows = self._db.execute(
                """SELECT received_at, alert_json, analysis_json FROM alerts
                   WHERE symbol = ? AND id < ? ORDER BY id DESC LIMIT ?""",
                (symbol, before_id, limit),
            ).fetchall()
        out = []
        for r in reversed(rows):
            analysis = json.loads(r["analysis_json"]) if r["analysis_json"] else None
            out.append({
                "received_at": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime(r["received_at"])),
                "alert": json.loads(r["alert_json"]),
                "verdict": analysis and {k: analysis.get(k) for k in ("decision", "bias", "confidence")},
            })
        return out

    def recent(self, limit: int = 50) -> list[dict[str, Any]]:
        with self._lock:
            rows = self._db.execute(
                "SELECT * FROM alerts ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
        return [
            {
                "id": r["id"],
                "received_at": r["received_at"],
                "symbol": r["symbol"],
                "alert": json.loads(r["alert_json"]),
                "analysis": json.loads(r["analysis_json"]) if r["analysis_json"] else None,
                "notified": bool(r["notified"]),
                "error": r["error"],
            }
            for r in rows
        ]
