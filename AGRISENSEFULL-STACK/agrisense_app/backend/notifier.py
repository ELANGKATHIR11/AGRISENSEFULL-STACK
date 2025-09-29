"""
Lightweight notification helper for alerts (SMS/app/email stubs).

Providers are controlled via environment variables. In development, this
module logs notifications to the console. Integrate real providers by
implementing the send_* functions and enabling via env flags.

Env variables (optional):
  AGRISENSE_NOTIFY_CONSOLE=1       -> log to console (default)
  AGRISENSE_NOTIFY_TWILIO=0/1      -> enable Twilio SMS (requires creds)
  AGRISENSE_TWILIO_SID=...
  AGRISENSE_TWILIO_TOKEN=...
  AGRISENSE_TWILIO_FROM=+1...
  AGRISENSE_TWILIO_TO=+91...
  AGRISENSE_NOTIFY_WEBHOOK_URL=... -> generic webhook sink for alerts
"""

from __future__ import annotations

import os
import json
from typing import Dict, Any, Optional

import requests  # type: ignore[reportMissingImports]


def _bool_env(name: str, default: bool = False) -> bool:
    v = os.getenv(name)
    if v is None:
        return default
    return v not in ("0", "false", "False", "no", "")


def notify_console(title: str, message: str, extra: Optional[Dict[str, Any]] = None) -> bool:
    payload = {"title": title, "message": message, **(extra or {})}
    print("[ALERT]", json.dumps(payload, ensure_ascii=False))
    return True


def notify_webhook(title: str, message: str, extra: Optional[Dict[str, Any]] = None) -> bool:
    url = os.getenv("AGRISENSE_NOTIFY_WEBHOOK_URL")
    if not url:
        return False
    try:
        r = requests.post(url, json={"title": title, "message": message, **(extra or {})}, timeout=10)
        return r.status_code // 100 == 2
    except Exception:
        return False


def notify_twilio_sms(title: str, message: str) -> bool:
    if not _bool_env("AGRISENSE_NOTIFY_TWILIO", False):
        return False
    # Minimal Twilio REST call without SDK
    sid = os.getenv("AGRISENSE_TWILIO_SID")
    token = os.getenv("AGRISENSE_TWILIO_TOKEN")
    from_ = os.getenv("AGRISENSE_TWILIO_FROM")
    to_ = os.getenv("AGRISENSE_TWILIO_TO")
    if not (sid and token and from_ and to_):
        return False
    try:
        auth = (sid, token)
        body = f"{title}: {message}"
        url = f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json"
        data = {"From": from_, "To": to_, "Body": body}
        r = requests.post(url, data=data, auth=auth, timeout=10)
        return r.status_code // 100 == 2
    except Exception:
        return False


def send_alert(title: str, message: str, extra: Optional[Dict[str, Any]] = None) -> bool:
    ok = False
    if _bool_env("AGRISENSE_NOTIFY_CONSOLE", True):
        ok = notify_console(title, message, extra) or ok
    ok = notify_webhook(title, message, extra) or ok
    ok = notify_twilio_sms(title, message) or ok
    return ok
