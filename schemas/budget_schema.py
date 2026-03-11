from pydantic import BaseModel


class CreateBudgetItemBase(BaseModel):
    name:str

class CreateBudgetItemRequest(CreateBudgetItemBase):
    pass

class CreateBudgetItemResponse(CreateBudgetItemBase):
    id: int
