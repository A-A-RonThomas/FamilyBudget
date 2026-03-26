from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from core.database import get_db
from models.database.account import Account

router = APIRouter()


class RenameAccountRequest(BaseModel):
    name: str


@router.patch("/accounts/{account_id}")
def rename_account(
    account_id: int,
    body: RenameAccountRequest,
    db: Session = Depends(get_db)
):
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    name = body.name.lower().strip()
    if not name:
        raise HTTPException(status_code=400, detail="Name cannot be empty")

    # Check for duplicates
    existing = db.query(Account).filter(
        Account.name == name,
        Account.id != account_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="An account with that name already exists")

    account.name = name
    db.commit()
    return {"id": account.id, "name": account.name}