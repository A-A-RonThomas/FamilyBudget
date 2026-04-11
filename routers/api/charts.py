from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from core.database import get_db
from controllers.ChartController import ChartController

router = APIRouter()


@router.get("/charts/cashflow")
def get_cashflow(months: int = Query(12), db: Session = Depends(get_db)):
    return ChartController.get_monthly_cashflow(months, db)


@router.get("/charts/savings-trend")
def get_savings_trend(months: int = Query(12), db: Session = Depends(get_db)):
    return ChartController.get_savings_trend(months, db)


@router.get("/charts/spending-by-category")
def get_spending_by_category(
    year: int,
    month: int | None = Query(None),
    db: Session = Depends(get_db)
):
    return ChartController.get_spending_by_category(year, month, db)


@router.get("/charts/budget-vs-actual")
def get_budget_vs_actual(year: int, month: int, db: Session = Depends(get_db)):
    return ChartController.get_budget_vs_actual(year, month, db)


@router.get("/charts/fund-balances")
def get_fund_balances(months: int = Query(12), db: Session = Depends(get_db)):
    return ChartController.get_fund_balances_over_time(months, db)