from fastapi import APIRouter, Request, Depends, Query
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from core.database import get_db
from controllers import BudgetController
from datetime import datetime, date
from calendar import month_name
from dateutil.relativedelta import relativedelta

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
    existing_months = BudgetController.get_existing_months(db)
    latest_month = existing_months[0] if existing_months else None

    # With no month requested, open the most recent month that has a budget
    # rather than the calendar month, so a new month is only started on purpose.
    if year is None and month is None and latest_month:
        year, month = latest_month["year"], latest_month["month"]
    year = year or now.year
    month = month or now.month

    budget = BudgetController.get_budget(year, month, db)

    target_date = date(year, month, 1)
    prev_date = target_date - relativedelta(months=1)
    next_date = target_date + relativedelta(months=1)

    default_copy_source = None
    if not budget:
        prior_months = [m for m in existing_months if date(m["year"], m["month"], 1) < target_date]
        if prior_months:
            default_copy_source = prior_months[0]

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
            "default_month": now.month,
            "prev_year": prev_date.year,
            "prev_month": prev_date.month,
            "next_year": next_date.year,
            "next_month": next_date.month,
            "existing_months": existing_months,
            "default_copy_source": default_copy_source,
            "latest_month": latest_month,
        }
    )