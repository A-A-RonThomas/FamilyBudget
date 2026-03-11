from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from core.database import get_db
from controllers import BudgetController
from schemas.budget_schema import CreateBudgetItemRequest, CreateBudgetItemResponse

router = APIRouter()


@router.post("/budget-items", response_model=CreateBudgetItemResponse)
def create_budget_item(body: CreateBudgetItemRequest, db: Session = Depends(get_db)):
    return BudgetController.create_budget_item(body.name, db)