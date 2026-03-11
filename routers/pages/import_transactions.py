from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from core.database import get_db
from controllers import ImportController
from models.database import BudgetItem

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/import", response_class=HTMLResponse, include_in_schema=False)
def import_transactions_page(request: Request, db: Session = Depends(get_db)):
    return templates.TemplateResponse(
        "import_transactions.html",
        {
            "request": request,
            "title": "Import Transactions",
            "active_page": "import_transactions_page"
        }
    )


@router.get("/import/review", response_class=HTMLResponse, include_in_schema=False)
def import_review_page(request: Request, db: Session = Depends(get_db)):
    transactions = ImportController.get_unreviewed(db)
    budget_items = db.query(BudgetItem).order_by(BudgetItem.name).all()
    return templates.TemplateResponse(
        "import_review.html",
        {
            "request": request,
            "title": "Review Transactions",
            "active_page": "import_transactions_page",
            "transactions": transactions,
            "budget_items": budget_items
        }
    )

