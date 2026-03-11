from fastapi import APIRouter, Request, Depends, Query
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from core.database import get_db
from controllers import TransactionController
from models.database import BudgetItem
from datetime import datetime

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/", response_class=HTMLResponse, include_in_schema=False)
def transactions(
    request: Request, 
    type: str | None = Query("purchases", description="Choose purchases or incomes"),
    year: int | None = Query(None, description="Filter by year"),
    month: int | None = Query(None, description="Filter by month"),
    db: Session = Depends(get_db)
):
    now = datetime.now()

    if type == "incomes":
        rows = TransactionController.get_all_incomes(db, year=year, month=month)
    else:
        rows = TransactionController.get_all_purchases(db, year=year, month=month)

    budget_items = db.query(BudgetItem).order_by(BudgetItem.name).all()

    return templates.TemplateResponse(
        "transactions.html",
        {
            "request": request,
            "title": "Transactions",
            "active_page": "transactions",
            "rows": rows,
            "year": year,
            "month": month,
            "default_year": now.year,
            "default_month": now.month,
            "type": type,
            "budget_items": budget_items
        }
    )