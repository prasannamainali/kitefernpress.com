# TradingView Alert Analyzer

A small web service that sits between TradingView and your phone:

```
TradingView alert ──webhook──▶ this service ──▶ Claude analyzes it ──▶ Telegram / Discord / Slack / ntfy
                               (answers in <1s)   (notify or suppress,
                                                   bias, confidence, risks)
```

1. A TradingView indicator or strategy alert fires and POSTs its message to `/webhook`.
2. The service checks the secret, drops duplicates, saves the alert in SQLite and answers `200` straight away. TradingView cancels webhooks that take longer than about 3 seconds, so the analysis runs afterwards in the background.
3. Claude gets the alert plus the last few alerts for the same symbol, along with your own trading rules (`TRADER_CONTEXT`). It returns structured JSON: `decision` (notify/suppress), `bias`, `confidence`, `headline`, `summary`, `reasoning`, `risks`, `key_levels`, `suggested_action`.
4. The alert is pushed only if Claude says `notify` **and** `confidence >= MIN_CONFIDENCE`. If the analysis fails, the raw alert is still sent, marked "not analyzed", so you never miss a signal silently.

The analysis is decision support, not financial advice. The service never places orders.

## Run it

```bash
cp .env.example .env        # then fill in ANTHROPIC_API_KEY, WEBHOOK_SECRET and a channel
pip install -r requirements.txt
uvicorn app.main:create_app --factory --host 0.0.0.0 --port 8000
```

Or with Docker:

```bash
docker build -t tv-analyzer .
docker run -d --env-file .env -v tvdata:/data -p 8000:8000 tv-analyzer
```

TradingView only sends webhooks to ports 80 and 443 over a public URL, so put it behind HTTPS: a small VPS with Caddy, or a host such as Render, Railway or Fly.io. To test from your own computer, use a tunnel like `cloudflared tunnel --url http://localhost:8000`.

Check it's up: `GET /health` shows the model and which channels are configured.

## Set up the TradingView alert

1. On the chart, create an alert on your indicator (Alerts ▸ Create alert ▸ Condition: your indicator).
2. **Notifications** tab ▸ tick **Webhook URL** and enter
   `https://your-host/webhook/YOUR_WEBHOOK_SECRET`
   (webhooks need a paid TradingView plan with 2-factor auth on).
3. **Message**: JSON gives Claude the most to work with. TradingView fills in the `{{...}}` placeholders:

```json
{
  "ticker": "{{ticker}}",
  "exchange": "{{exchange}}",
  "interval": "{{interval}}",
  "close": "{{close}}",
  "volume": "{{volume}}",
  "time": "{{timenow}}",
  "indicator": "RSI 14 cross",
  "action": "buy",
  "message": "RSI crossed above 30"
}
```

For strategy alerts you can add `"action": "{{strategy.order.action}}"` and `"position": "{{strategy.market_position}}"`. Any extra field you add (indicator values from `{{plot("RSI")}}` and so on) is passed to Claude as-is. Plain-text messages work too.

You can send the secret in the URL path (above), as `?token=`, or as a `"passphrase"` field in the JSON. It is removed before anything reaches Claude or the database.

## Notification channels

Set any of these in `.env`; each one that's set gets every notification.

| Channel | What to set |
|---|---|
| Telegram | Create a bot with @BotFather → `TELEGRAM_BOT_TOKEN`. Message the bot, then open `https://api.telegram.org/bot<token>/getUpdates` to find your chat id → `TELEGRAM_CHAT_IDS` (comma-separated for several people). |
| Discord | Channel ▸ Edit ▸ Integrations ▸ Webhooks → `DISCORD_WEBHOOK_URL` |
| Slack | Incoming Webhook app → `SLACK_WEBHOOK_URL` |
| ntfy (push to phone, no account) | Pick a hard-to-guess topic → `NTFY_TOPIC_URL=https://ntfy.sh/your-topic`, then subscribe in the ntfy app |

## Tuning

| Setting | Default | Effect |
|---|---|---|
| `CLAUDE_MODEL` | `claude-opus-5-5` | Model used for analysis |
| `CLAUDE_EFFORT` | `medium` | `low` is faster and cheaper; `high` thinks harder |
| `MIN_CONFIDENCE` | `60` | Pushes below this are held back |
| `SEND_SUPPRESSED` | `false` | `true` also sends filtered alerts, marked 🔕 FILTERED (useful while you calibrate) |
| `DEDUP_WINDOW_SECONDS` | `60` | Identical alerts within this window are ignored |
| `HISTORY_SIZE` | `10` | Earlier alerts per symbol shown to Claude |
| `TRADER_CONTEXT` | empty | Your strategy and rules in plain words. This has the biggest effect on what Claude filters out |

`GET /alerts?token=YOUR_WEBHOOK_SECRET` returns the latest alerts with Claude's verdict and whether each one was sent, so you can review what got filtered.

## Cost

Each alert is one Claude request: a few hundred to a couple of thousand tokens in, a few hundred out. The system prompt is cached. If you raise `CLAUDE_EFFORT` the model thinks longer, which costs more. Watch usage in the Claude Console if your alerts fire often.

## Tests

```bash
pip install -r requirements-dev.txt
python -m pytest
```

The tests replace Claude and the channels with fakes, so they need no API key and send nothing.

## Files

```
app/main.py       webhook endpoints, background processing
app/alerts.py     parses TradingView JSON / plain-text bodies
app/analyzer.py   Claude prompt, JSON schema, refusal handling
app/notifier.py   message formatting + Telegram / Discord / Slack / ntfy
app/storage.py    SQLite log and per-symbol history
app/config.py     environment settings
```
