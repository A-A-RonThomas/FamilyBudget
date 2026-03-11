from fastapi import APIRouter, UploadFile, File, Depends
from sqlalchemy.orm import Session
from core.database import get_db
from controllers import ImportController
from schemas.vendor_schema import SaveVendorRequest, SaveVendorResponse
from schemas.transactions_schema import ReviewTransactionRequest, ReviewTransactionResponse

router = APIRouter()

@router.post("/import")
async def import_transactions(
    joint: UploadFile = File(None),
    grocery: UploadFile = File(None),
    credit: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    files = {
        "joint": joint,
        "grocery": grocery,
        "credit": credit
    }
    return await ImportController.process_import(files, db)


@router.post("/import/review/{trans_id}", response_model=ReviewTransactionResponse)
def review_transaction(
    trans_id: int,
    body: ReviewTransactionRequest,
    db: Session = Depends(get_db)
):
    result = ImportController.review_transaction(
        trans_id=trans_id,
        budget_item_id=body.budget_item_id,
        vendor_name=body.vendor_name,
        orig_description=body.orig_description,
        db=db
    )

    if body.save_vendor and body.vendor_name and body.orig_description:
        ImportController.save_vendor(
            name=body.vendor_name,
            budget_item_id=body.budget_item_id,
            codes=[body.orig_description],
            db=db
        )

    return result


@router.post("/import/vendor", response_model=SaveVendorResponse)
def save_vendor(
    body: SaveVendorRequest,
    db: Session = Depends(get_db)
):
    return ImportController.save_vendor(
        name=body.name,
        budget_item_id=body.budget_item_id,
        codes=body.codes,
        db=db
    )