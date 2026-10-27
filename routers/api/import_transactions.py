from fastapi import APIRouter, UploadFile, File, Form, Depends
from sqlalchemy.orm import Session
from core.database import get_db
from controllers import ImportController

router = APIRouter()


@router.get("/accounts")
def get_accounts(db: Session = Depends(get_db)):
    accounts = ImportController.get_all_accounts(db)
    return [{"id": a.id, "name": a.name} for a in accounts]


@router.post("/accounts")
def create_account(name: str, db: Session = Depends(get_db)):
    account = ImportController.get_or_create_account(name, db)
    db.commit()
    return {"id": account.id, "name": account.name}


@router.post("/import")
async def import_transactions(
    file: UploadFile = File(...),
    account_id: int = Form(...),
    negate: bool = Form(False),
    db: Session = Depends(get_db)
):
    return await ImportController.process_import(file, account_id, negate, db)