from fastapi import APIRouter, Request, Depends, Query
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from core.database import get_db
from controllers import BudgetController
from datetime import datetime
from calendar import month_name

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/budget", response_class=HTMLResponse, include_in_schema=False)
def budget_page(
    request: Request,
    year: int | None = Query(None),
    month: int | None = Query(None),
    db: Session = Depends(get_db)
):
    now = datetime.now()
    year = year or now.year
    month = month or now.month

    budget = BudgetController.get_budget(year, month, db)

    return templates.TemplateResponse(
        "budget.html",
        {
            "request": request,
            "title": "Budget",
            "active_page": "budget",
            "budget": budget,
            "year": year,
            "month": month,
            "month_name": month_name[month],
            "default_year": now.year,
            "default_month": now.month
        }
    )