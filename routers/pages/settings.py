from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from core.database import get_db
from models.database.account import Account

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/settings", response_class=HTMLResponse, include_in_schema=False)
def settings_page(request: Request, db: Session = Depends(get_db)):
    accounts = db.query(Account).order_by(Account.name).all()
    return templates.TemplateResponse(
        "settings.html",
        {
            "request": request,
            "title": "Settings",
            "active_page": "settings",
            "accounts": accounts,
        }
    )