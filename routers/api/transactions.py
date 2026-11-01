from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from core.database import get_db
from controllers import TransactionController
from schemas.transactions_schema import TransactionUpdateRequest, TransactionUpdateResponse, TransactionResponse, SplitRequest

router = APIRouter()


@router.get("/transactions", response_model=list[TransactionResponse])
def get_transactions(
    db: Session = Depends(get_db),
    type: str = Query("purchases", description="Type of transaction: purchases or incomes"),
    year: int | None = Query(None, description="Filter by year"),
    month: int | None = Query(None, description="Filter by month")
):
    type = type.lower()
    if type == "purchases":
        return TransactionController.get_all_purchases(db, year, month)
    elif type == "incomes":
        return TransactionController.get_all_incomes(db, year, month)
    else:
        return {"error": "Invalid type. Must be 'purchases' or 'incomes'."}


@router.post("/transactions")
def save_transactions(purchases: list, db: Session = Depends(get_db)):
    return TransactionController.save_purchases(db, purchases)



@router.patch("/transactions/{trans_id}", response_model=TransactionUpdateResponse)
def update_transaction(trans_id: int, body: TransactionUpdateRequest, db: Session = Depends(get_db)):
    return TransactionController.update_transaction(
        trans_id, body.date, body.description,
        body.budget_item_id, body.fund_item_id, body.is_income, db,
        always_ignore=body.always_ignore, always_categorize=body.always_categorize
    )

@router.delete("/transactions/{trans_id}")
def delete_transaction(trans_id: int, db: Session = Depends(get_db)):
    return TransactionController.delete_transaction(trans_id, db)

@router.post("/transactions/{trans_id}/restore")
def restore_transaction(trans_id: int, db: Session = Depends(get_db)):
    return TransactionController.restore_transaction(trans_id, db)

@router.post("/transactions/{trans_id}/split")
def split_transaction(trans_id: int, body: SplitRequest, db: Session = Depends(get_db)):
    return TransactionController.split_transaction(trans_id, [p.model_dump() for p in body.pieces], db)

@router.delete("/transactions/{trans_id}/split")
def unsplit_transaction(trans_id: int, db: Session = Depends(get_db)):
    return TransactionController.unsplit_transaction(trans_id, db)
