import os
import logging
import requests
from dotenv import load_dotenv

load_dotenv()

NTFY_URL = os.getenv("NTFY_URL", "https://ntfy.sh").rstrip("/")
NTFY_TOPIC = os.getenv("NTFY_TOPIC")
NTFY_TOKEN = os.getenv("NTFY_TOKEN")
APP_BASE_URL = os.getenv("APP_BASE_URL", "").rstrip("/")

log = logging.getLogger(__name__)


def send_notification(
        title: str,
        message: str,
        click_path: str | None = None,
        tags: list[str] | None = None,
        priority: str = "default"
    ) -> bool:
    """Publish to ntfy. Never raises -- a notification failure shouldn't break the caller."""
    if not NTFY_TOPIC:
        log.info("NTFY_TOPIC not configured; skipping notification")
        return False

    headers = {"Title": title, "Priority": priority}
    if tags:
        headers["Tags"] = ",".join(tags)
    if click_path is not None and APP_BASE_URL:
        headers["Click"] = f"{APP_BASE_URL}{click_path}"
    if NTFY_TOKEN:
        headers["Authorization"] = f"Bearer {NTFY_TOKEN}"

    try:
        response = requests.post(
            f"{NTFY_URL}/{NTFY_TOPIC}",
            data=message.encode("utf-8"),
            headers=headers,
            timeout=10
        )
        response.raise_for_status()
        return True
    except requests.RequestException as e:
        log.warning("ntfy notification failed: %s", e)
        return False
