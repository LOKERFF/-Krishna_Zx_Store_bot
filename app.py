import html
import json
import os
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse

STORE_NAME = os.environ.get("STORE_NAME", "Krishna_Zx_Store")
BOT_USERNAME = os.environ.get("BOT_USERNAME", "@Krishna_Zx_Store_bot")
FETCH_TIMEOUT_SECONDS = 8


def _bot_url():
    url = os.environ.get("RENDER_BOT_URL", "").strip().rstrip("/")
    if url and not url.startswith(("http://", "https://")):
        url = "https://" + url
    return url


def _fetch_bot_status(request_host):
    """Render par chal rahe bot ka /status padhta hai. Yeh request bot ko ping bhi karti hai."""
    url = _bot_url()
    if not url:
        return {"ok": False, "reason": "not_configured"}
    if request_host and urlparse(url).netloc.lower() == request_host.lower():
        # Apne aap ko fetch karne se infinite loop ban jata.
        return {"ok": False, "reason": "points_to_self"}
    try:
        req = urllib.request.Request(
            url + "/status", headers={"User-Agent": "KrishnaStore-StatusPage/1.0"}
        )
        with urllib.request.urlopen(req, timeout=FETCH_TIMEOUT_SECONDS) as resp:
            data = json.loads(resp.read(65536).decode("utf-8"))
        if not isinstance(data, dict):
            return {"ok": False, "reason": "bad_response"}
        return {"ok": True, "bot": data}
    except (TimeoutError, urllib.error.URLError, OSError):
        return {"ok": False, "reason": "unreachable"}
    except ValueError:
        return {"ok": False, "reason": "bad_response"}


NOTICES = {
    "not_configured": (
        "Setup baaki hai",
        "Vercel ke Vars mein <code>RENDER_BOT_URL</code> set karein (jaise "
        "<code>https://krishna-zx-bot.onrender.com</code>). Bot khud Render par chalta hai, "
        "yeh page sirf uska status dikhata hai.",
    ),
    "points_to_self": (
        "Galat URL",
        "<code>RENDER_BOT_URL</code> isi Vercel site ki taraf hai. Yahan Render service ka "
        "<code>onrender.com</code> URL daalein.",
    ),
    "unreachable": (
        "Bot se sampark nahi hua",
        "Render service ne jawab nahi diya. Agar service so rahi thi to yeh request use jaga "
        "degi, 1 minute baad page dobara kholein. Warna Render dashboard ke logs dekhein.",
    ),
    "bad_response": (
        "Galat jawab",
        "Render URL se bot ka status nahi mila. <code>RENDER_BOT_URL</code> check karein.",
    ),
}


def _stat(label, value):
    return (
        '<div class="stat"><dt>{}</dt><dd>{}</dd></div>'.format(
            html.escape(label), html.escape(str(value if value not in (None, "") else "-"))
        )
    )


def _render_page(result):
    if result["ok"]:
        bot = result["bot"]
        running = bot.get("status") == "running"
        badge = "ONLINE" if running else str(bot.get("status", "unknown")).upper()
        tone = "ok" if running else "warn"
        body = "<dl class=\"grid\">{}</dl>".format(
            "".join(
                [
                    _stat("Uptime", bot.get("uptime")),
                    _stat("Keep-alive pings", bot.get("ping_count")),
                    _stat("Auto-restarts", bot.get("restart_count")),
                    _stat("Last heartbeat", bot.get("last_heartbeat")),
                    _stat("Last ping", bot.get("last_ping")),
                    _stat("Started at", bot.get("started_at")),
                ]
            )
        )
        if bot.get("last_error"):
            body += '<p class="notice"><strong>Last error:</strong> {}</p>'.format(
                html.escape(str(bot["last_error"]))
            )
    else:
        title, text = NOTICES[result["reason"]]
        badge = "OFFLINE" if result["reason"] == "unreachable" else "SETUP"
        tone = "warn"
        body = '<p class="notice"><strong>{}:</strong> {}</p>'.format(html.escape(title), text)

    return """<!doctype html>
<html lang="hi">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <meta name="theme-color" content="#0b0f19" />
  <meta http-equiv="refresh" content="60" />
  <title>{store} - Bot Status</title>
  <meta name="description" content="{store} Telegram bot ka live status." />
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
      background: #0b0f19; color: #f9fafb; min-height: 100vh;
      display: flex; align-items: center; justify-content: center; padding: 24px;
    }}
    main {{
      width: 100%; max-width: 720px; background: #111827;
      border: 1px solid #1f2937; border-radius: 16px; padding: 28px;
    }}
    header {{
      display: flex; align-items: center; justify-content: space-between;
      gap: 16px; flex-wrap: wrap; padding-bottom: 20px; border-bottom: 1px solid #1f2937;
    }}
    h1 {{ font-size: 22px; letter-spacing: -0.02em; }}
    header p {{ color: #9ca3af; font-size: 14px; margin-top: 4px; }}
    .badge {{
      display: inline-flex; align-items: center; gap: 8px; padding: 6px 14px;
      border-radius: 6px; font-size: 13px; font-weight: 600; border: 1px solid currentColor;
    }}
    .badge::before {{ content: ""; width: 8px; height: 8px; border-radius: 50%; background: currentColor; }}
    .ok {{ color: #34d399; }}
    .warn {{ color: #fbbf24; }}
    .grid {{
      display: grid; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
      gap: 14px; margin-top: 20px;
    }}
    .stat {{ border: 1px solid #1f2937; border-radius: 12px; padding: 14px 16px; }}
    dt {{ color: #9ca3af; font-size: 12px; text-transform: uppercase; letter-spacing: 0.05em; }}
    dd {{ font-size: 16px; font-weight: 600; margin-top: 6px; font-variant-numeric: tabular-nums; }}
    .notice {{
      margin-top: 20px; padding: 14px 16px; border: 1px solid #374151;
      border-radius: 12px; font-size: 14px; line-height: 1.6; color: #e5e7eb;
    }}
    code {{ background: #030712; padding: 2px 6px; border-radius: 4px; color: #93c5fd; word-break: break-all; }}
  </style>
</head>
<body>
  <main>
    <header>
      <div>
        <h1>{store}</h1>
        <p>Telegram Bot: {bot_username}</p>
      </div>
      <span class="badge {tone}" role="status">{badge}</span>
    </header>
    {body}
  </main>
</body>
</html>""".format(
        store=html.escape(STORE_NAME),
        bot_username=html.escape(BOT_USERNAME),
        tone=tone,
        badge=html.escape(badge),
        body=body,
    )


class handler(BaseHTTPRequestHandler):
    def _send(self, code, content_type, body=b""):
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "strict-origin-when-cross-origin")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def _respond(self):
        path = self.path.split("?", 1)[0].rstrip("/") or "/"
        if path not in ("/", "/ping", "/health", "/status", "/api/status"):
            self._send(404, "text/plain; charset=utf-8", b"Not Found")
            return

        result = _fetch_bot_status(self.headers.get("Host", ""))

        if path == "/":
            self._send(200, "text/html; charset=utf-8", _render_page(result).encode("utf-8"))
            return

        code = 200 if result["ok"] else 503
        if path in ("/status", "/api/status"):
            payload = json.dumps(result, ensure_ascii=False, indent=2).encode("utf-8")
            self._send(code, "application/json; charset=utf-8", payload)
            return

        text = "OK - bot is alive\n" if result["ok"] else "DOWN - {}\n".format(result["reason"])
        self._send(code, "text/plain; charset=utf-8", text.encode("utf-8"))

    def do_GET(self):
        self._respond()

    def do_HEAD(self):
        self._respond()

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    from python import main

    main()
