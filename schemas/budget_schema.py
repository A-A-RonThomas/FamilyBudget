from decimal import Decimal
from pydantic import BaseModel


class CreateBudgetItemBase(BaseModel):
    name:str

class CreateBudgetItemRequest(CreateBudgetItemBase):
    pass

class CreateBudgetItemResponse(CreateBudgetItemBase):
    id: int

# BudgetTable
class BudgetTableBase(BaseModel):
    name: str
    is_fund: bool

class BudgetTableCreateRequest(BudgetTableBase):
    budget_id: int

class BudgetTableResponse(BudgetTableBase):
    id: int
    budget_id: int

    class Config:
        from_attributes = True

# BudgetItem
class BudgetItemBase(BaseModel):
    name: str
    expected: Decimal = Decimal('0')

class BudgetItemCreateRequest(BudgetItemBase):
    budget_table_id: int

class BudgetItemResponse(BudgetItemBase):
    id: int
    actual: Decimal
    budget_table_id: int

    class Config:
        from_attributes = True

# FundItem
class FundItemBase(BaseModel):
    name: str
    plus: Decimal = Decimal('0')
    minimum: Decimal | None = None
    maximum: Decimal | None = None

class FundItemCreateRequest(FundItemBase):
    budget_table_id: int
    starting_value: Decimal = Decimal('0')

class FundItemResponse(FundItemBase):
    id: int
    starting_value: Decimal
    minus: Decimal
    ending_value: Decimal
    budget_table_id: int

    class Config:
        from_attributes = True

# Copy/Init
class BudgetInitRequest(BaseModel):
    year: int
    month: int
    copy_previous: bool