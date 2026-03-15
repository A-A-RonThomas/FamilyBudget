from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from core.database import get_db

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/import", response_class=HTMLResponse, include_in_schema=False)
def import_transactions_page(request: Request):
    return templates.TemplateResponse(
        "import_transactions.html",
        {
            "request": request,
            "title": "Import Transactions",
            "active_page": "import_transactions_page"
        }
    )


