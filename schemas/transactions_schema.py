from pydantic import BaseModel
from datetime import date
from typing import Optional


class TransactionBase(BaseModel):
    pass


class TransactionCreateRequest(TransactionBase):
    date: date
    description: str
    amount: float
    account_id: int
    budget_item_id: Optional[int] = None
    fund_item_id: Optional[int] = None


class TransactionUpdateRequest(TransactionBase):
    date: date
    description: str
    budget_item_id: Optional[int] = None


class TransactionUpdateResponse(TransactionBase):
    message: str
    also_updated: int


class TransactionResponse(TransactionBase):
    id: int
    date: date
    description: str
    orig_description: str
    amount: float
    account: str
    budget_category: Optional[str] = None
    budget_item_id: Optional[int] = None
    vendor_id: Optional[int] = None

    class Config:
        from_attributes = True


class ReviewTransactionBase(BaseModel):
    pass


class ReviewTransactionRequest(ReviewTransactionBase):
    budget_item_id: int
    vendor_name: str | None = None
    save_vendor: bool = False
    orig_description: str | None = None


class ReviewTransactionResponse(ReviewTransactionBase):
    message: str
    also_updated: int