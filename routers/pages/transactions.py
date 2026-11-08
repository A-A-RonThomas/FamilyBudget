from fastapi import APIRouter, Request, Depends, Query
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlalchemy import extract
from sqlalchemy.orm import Session
from core.database import get_db
from controllers import TransactionController
from models.database import BudgetItem, BudgetTable, Budget, FundItem
from datetime import datetime
from calendar import month_name as cal_month_name

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/", response_class=HTMLResponse, include_in_schema=False)
def transactions(
    request: Request,
    type: str | None = Query("purchases"),
    year: int | None = Query(None),
    month: int | None = Query(None),
    view_all: bool = Query(False),
    db: Session = Depends(get_db)
):
    now = datetime.now()

    if not view_all:
        year = year or now.year
        month = month or now.month


    # Desktop shows both lists side by side; on mobile `type` picks which one starts visible
    purchases = TransactionController.get_all_purchases(db, year=year, month=month)
    incomes = TransactionController.get_all_incomes(db, year=year, month=month)
    if type != "incomes":
        type = "purchases"


    budget = db.query(Budget).filter(
        extract('year', Budget.date) == year,
        extract('month', Budget.date) == month
    ).first()


    #  Here is where I need to also get the funditems to be able to select them in transactions.
    if budget:
        budget_items = db.query(BudgetItem)\
            .join(BudgetTable, BudgetItem.budget_table_id == BudgetTable.id)\
            .filter(BudgetTable.budget_id == budget.id)\
            .order_by(BudgetItem.name)\
            .all()
        fund_items = db.query(FundItem)\
            .join(BudgetTable, FundItem.budget_table_id == BudgetTable.id)\
            .filter(BudgetTable.budget_id == budget.id)\
            .order_by(FundItem.name)\
            .all()
    else:
        budget_items = []
        fund_items = []

    return templates.TemplateResponse(
        "transactions.html",
        {
            "request": request,
            "title": "Transactions",
            "active_page": "transactions",
            "purchases": purchases,
            "incomes": incomes,
            "year": year,
            "month": month,
            "default_year": now.year,
            "default_month": now.month,
            "month_name": cal_month_name[month] if month else "selected month",
            "type": type,
            "budget_items": budget_items,
            "fund_items": fund_items
        }
    )