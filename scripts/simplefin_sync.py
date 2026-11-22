"""Scheduled SimpleFIN sync. Run by deploy/simplefin-sync.timer hourly, 7am-7pm Eastern.

Usage (from the project root):
    python -m scripts.simplefin_sync [--days N]
"""
import argparse
import calendar
import logging
import sys

from core.database import SessionLocal
from core.notify import send_notification
from models.database import *  # noqa: F401,F403 -- register all models with SQLAlchemy
from routers.api.simplefin import run_simplefin_sync

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("simplefin_sync")


def main() -> int:
    parser = argparse.ArgumentParser()
    # Hourly runs only need a short lookback; dedupe on simplefin_id handles overlap.
    # A few days covers pending -> posted delays and any missed runs.
    parser.add_argument("--days", type=int, default=5)
    args = parser.parse_args()

    db = SessionLocal()
    try:
        result = run_simplefin_sync(db, days=args.days)
        log.info("SimpleFIN sync complete: imported=%s skipped=%s", result["imported"], result["skipped"])
        if result["imported"]:
            count = result["imported"]
            months = result["months"]  # newest first
            message = f"{count} new transaction{'s' if count != 1 else ''} imported from SimpleFIN."
            if len(months) > 1:
                # Late-posting charges can land in a different month than the current one
                breakdown = ", ".join(f"{m['count']} in {calendar.month_name[m['month']]}" for m in months)
                message += f" ({breakdown})"
            # Open the newest month with this batch highlighted
            newest = months[0]
            send_notification(
                title="New transactions",
                message=message,
                click_path=f"/?year={newest['year']}&month={newest['month']}&new_since={result['imported_at']}",
                tags=["moneybag"]
            )
        return 0
    except Exception:
        log.exception("SimpleFIN sync failed")
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
