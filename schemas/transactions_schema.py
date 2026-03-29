from pydantic import BaseModel
from datetime import date
from typing import Optional


class TransactionBase(BaseModel):
    pass


class TransactionUpdateRequest(TransactionBase):
    date: date
    description: str
    budget_item_id: Optional[int] = None
    fund_item_id: Optional[int] = None
    is_income: Optional[bool] = None


class TransactionUpdateResponse(TransactionBase):
    message: str
    also_updated: int


class TransactionResponse(TransactionBase):
    id: int
    date: date
    description: str
    memo: Optional[str] = None
    amount: float
    account: str
    budget_category: Optional[str] = None
    budget_item_id: Optional[int] = None
    vendor_id: Optional[int] = None
    simplefin_id: Optional[str] = None
    is_income: Optional[bool] = True

    class Config:
        from_attributes = True