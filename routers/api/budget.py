from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from core.database import get_db
from controllers import BudgetController
from schemas.budget_schema import (
    CreateBudgetItemRequest, CreateBudgetItemResponse,
    BudgetTableCreateRequest, BudgetInitRequest,
    BudgetItemCreateRequest, FundItemCreateRequest
)

router = APIRouter()


@router.patch("/budget/table/{table_id}")
def update_table(table_id: int, body: BudgetTableCreateRequest, db: Session = Depends(get_db)):
    return BudgetController.update_table(table_id, body.name, db)

@router.post("/budget/init")
def init_budget(body: BudgetInitRequest, db: Session = Depends(get_db)):
    return BudgetController.init_budget(body.year, body.month, body.copy_previous, db)


@router.get("/budget")
def get_budget(year: int, month: int, db: Session = Depends(get_db)):
    return BudgetController.get_budget(year, month, db)


@router.post("/budget/table")
def add_table(body: BudgetTableCreateRequest, db: Session = Depends(get_db)):
    return BudgetController.add_table(body.budget_id, body.name, body.is_fund, db)


@router.post("/budget/item")
def add_budget_item(body: BudgetItemCreateRequest, db: Session = Depends(get_db)):
    return BudgetController.add_budget_item(body.budget_table_id, body.name, body.expected, db)


@router.post("/budget/fund-item")
def add_fund_item(body: FundItemCreateRequest, db: Session = Depends(get_db)):
    return BudgetController.add_fund_item(body.budget_table_id, body.name, body.starting_value, body.plus, db, body.minimum, body.maximum)


@router.patch("/budget/item/{item_id}")
def update_budget_item(item_id: int, body: BudgetItemCreateRequest, db: Session = Depends(get_db)):
    return BudgetController.update_budget_item(item_id, body.name, body.expected, db)


@router.patch("/budget/fund-item/{item_id}")
def update_fund_item(item_id: int, body: FundItemCreateRequest, db: Session = Depends(get_db)):
    return BudgetController.update_fund_item(item_id, body.name, body.plus, body.starting_value, db, body.minimum, body.maximum)

@router.delete("/budget/table/{table_id}")
def delete_table(table_id: int, db: Session = Depends(get_db)):
    return BudgetController.delete_table(table_id, db)

@router.delete("/budget/item/{item_id}")
def delete_budget_item(item_id: int, db: Session = Depends(get_db)):
    return BudgetController.delete_budget_item(item_id, db)

@router.delete("/budget/fund-item/{item_id}")
def delete_fund_item(item_id: int, db: Session = Depends(get_db)):
    return BudgetController.delete_fund_item(item_id, db)