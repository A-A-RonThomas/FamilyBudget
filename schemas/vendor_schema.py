from pydantic import BaseModel

class SaveVendorBase(BaseModel):
    name: str


class SaveVendorRequest(SaveVendorBase):
    budget_item_id: int
    codes: list[str]

class SaveVendorResponse(SaveVendorBase):
    id: int
    default_budget_item_id: int | None = None
    default_fund_item_id: int | None = None