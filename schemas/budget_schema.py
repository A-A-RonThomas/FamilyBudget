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
    expected: float = 0

class BudgetItemCreateRequest(BudgetItemBase):
    budget_table_id: int

class BudgetItemResponse(BudgetItemBase):
    id: int
    actual: float
    budget_table_id: int

    class Config:
        from_attributes = True

# FundItem
class FundItemBase(BaseModel):
    name: str
    plus: float = 0

class FundItemCreateRequest(FundItemBase):
    budget_table_id: int
    starting_value: float = 0

class FundItemResponse(FundItemBase):
    id: int
    starting_value: float
    minus: float
    ending_value: float
    budget_table_id: int

    class Config:
        from_attributes = True

# Copy/Init
class BudgetInitRequest(BaseModel):
    year: int
    month: int
    copy_previous: bool