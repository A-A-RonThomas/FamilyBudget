from fastapi import APIRouter, HTTPException
from core.notify import NTFY_TOPIC, send_notification

router = APIRouter()


@router.post("/notifications/test")
def send_test_notification():
    if not NTFY_TOPIC:
        raise HTTPException(status_code=500, detail="NTFY_TOPIC not configured in .env")

    sent = send_notification(
        title="FamilyBudget test",
        message="Test notification from FamilyBudget. Tap to open transactions.",
        click_path="/",
        tags=["white_check_mark"]
    )
    if not sent:
        raise HTTPException(status_code=502, detail="Failed to reach ntfy server; check NTFY_URL / NTFY_TOKEN and the server logs")
    return {"sent": True}
