from decimal import Decimal
from fastapi import HTTPException
from models.database import Transaction, Account, Vendor, VendorCode, BudgetItem, FundItem, Budget
from controllers.BudgetController import BudgetController
from sqlalchemy.orm import Session
from sqlalchemy import extract, or_


def _category_name(t):
    return t.budget_item.name if t.budget_item else t.fund_item.name if t.fund_item else None


def _category_value(t):
    """Matches the option values used by the category selects on the transactions page."""
    if t.budget_item_id:
        return f"budget-{t.budget_item_id}"
    if t.fund_item_id:
        return f"fund-{t.fund_item_id}"
    return ""


class TransactionController:

    @staticmethod
    def _locked_months(db: Session) -> set:
        return {(r.date.year, r.date.month) for r in db.query(Budget.date).filter(Budget.is_locked == True).all()}

    @staticmethod
    def get_all_purchases(db: Session, year=None, month=None):
        try:
            # Split pieces are listed under their original rather than as their own rows
            query = db.query(Transaction).filter(Transaction.amount < 0, Transaction.parent_id == None)

            if year:
                query = query.filter(extract('year', Transaction.date) == year)
            if month:
                query = query.filter(extract('month', Transaction.date) == month)

            query = query.order_by(Transaction.date.asc())
            purchases = query.all()
            account_dict = {a.id: a.name for a in db.query(Account).all()}
            locked = TransactionController._locked_months(db)

            return [
                {
                    'id': t.id,
                    'date': t.date.strftime('%Y-%m-%d'),
                    'description': t.vendor.name if t.vendor else t.description,
                    'memo': t.memo,
                    'amount': t.amount,
                    'account': account_dict[t.account_id].title(),
                    'budget_category': (
                        t.budget_item.name if t.budget_item
                        else t.fund_item.name if t.fund_item
                        else None
                    ),
                    'budget_item_id': t.budget_item_id,
                    'fund_item_id': t.fund_item_id,
                    'vendor_id': t.vendor_id,
                    'simplefin_id': t.simplefin_id,
                    'is_deleted': t.is_deleted,
                    'is_locked': (t.date.year, t.date.month) in locked,
                    'is_split': t.is_split,
                    'splits': [
                        {
                            'id': c.id,
                            'amount': str(abs(c.amount)),
                            'category': _category_name(c),
                            'category_value': _category_value(c),
                        }
                        for c in t.children
                    ] if t.is_split else [],
                }
                for t in purchases
            ]

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"{str(e)}")

    @staticmethod
    def get_all_incomes(db: Session, year=None, month=None):
        try:
            query = db.query(Transaction).filter(Transaction.amount >= 0)

            if year:
                query = query.filter(extract('year', Transaction.date) == year)
            if month:
                query = query.filter(extract('month', Transaction.date) == month)

            query = query.order_by(Transaction.date.asc())
            incomes = query.all()
            account_dict = {a.id: a.name for a in db.query(Account).all()}
            locked = TransactionController._locked_months(db)

            return [
                {
                    'id': t.id,
                    'date': t.date.strftime('%Y-%m-%d'),
                    'description': t.vendor.name if t.vendor else t.description,
                    'memo': t.memo,
                    'amount': t.amount,
                    'account': account_dict[t.account_id].title(),
                    'budget_category': t.budget_item.name if t.budget_item else None,
                    'budget_item_id': t.budget_item_id,
                    'fund_item_id': t.fund_item_id,
                    'vendor_id': t.vendor_id,
                    'simplefin_id': t.simplefin_id,
                    'is_income': t.is_income,
                    'is_deleted': t.is_deleted,
                    'is_locked': (t.date.year, t.date.month) in locked,
                }
                for t in incomes
            ]

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"{str(e)}")

    @staticmethod
    def update_transaction(
        trans_id: int, date, description: str, budget_item_id: int | None, fund_item_id: int | None,
        is_income: bool | None, db: Session, always_ignore: bool = False, always_categorize: bool = False
    ) -> dict:
        try:
            t = db.query(Transaction).filter(Transaction.id == trans_id).first()
            if not t:
                raise HTTPException(status_code=404, detail="Transaction not found")
            BudgetController.assert_month_unlocked(t.date, db)
            BudgetController.assert_month_unlocked(date, db)

            t.date = date
            if is_income is not None:
                t.is_income = is_income

            # Save or find vendor by name
            vendor = db.query(Vendor).filter(Vendor.name == description.lower().strip()).first()
            if not vendor:
                vendor = Vendor(name=description.lower().strip())
                db.add(vendor)
                db.flush()

            t.vendor_id = vendor.id

            # Changes spread to like-named transactions in the same month only; other months
            # are left alone (future imports still pick up the vendor rules).
            same_month = (
                extract('year', Transaction.date) == t.date.year,
                extract('month', Transaction.date) == t.date.month,
            )

            if always_ignore:
                vendor.always_ignore = True
                t.is_deleted = True
                t.budget_item_id = None
                t.fund_item_id = None

                # Always ignore applies to this month's transactions from this vendor (including
                # ones never vendor-linked yet, matched by the same raw description) and to
                # future imports via the vendor rule
                matches = db.query(Transaction).filter(
                    Transaction.id != trans_id,
                    *same_month,
                    or_(
                        Transaction.vendor_id == vendor.id,
                        Transaction.description == t.description
                    )
                ).all()
                for match in matches:
                    match.is_deleted = True
                    match.vendor_id = vendor.id

            else:
                t.budget_item_id = budget_item_id
                t.fund_item_id = fund_item_id

                if always_categorize:
                    category_name = None
                    if budget_item_id:
                        bi = db.query(BudgetItem).filter(BudgetItem.id == budget_item_id).first()
                        category_name = bi.name if bi else None
                    elif fund_item_id:
                        fi = db.query(FundItem).filter(FundItem.id == fund_item_id).first()
                        category_name = fi.name if fi else None
                    if category_name:
                        vendor.default_category_name = category_name
                        vendor.default_category_is_fund = fund_item_id is not None

                # Fill in the same category for other uncategorized transactions from this vendor
                # this month, without overwriting anything already categorized manually
                # Split originals and split pieces are skipped -- pieces are categorized
                # individually through the split dialog.
                matches = db.query(Transaction).filter(
                    Transaction.id != trans_id,
                    Transaction.budget_item_id == None,
                    Transaction.fund_item_id == None,
                    Transaction.is_split == False,
                    Transaction.parent_id == None,
                    *same_month,
                    or_(
                        Transaction.vendor_id == vendor.id,
                        Transaction.description == t.description
                    )
                ).all()
                for match in matches:
                    match.budget_item_id = budget_item_id
                    match.fund_item_id = fund_item_id
                    match.vendor_id = vendor.id

            db.commit()
            return {"message": "success", "also_updated": len(matches)}

        except HTTPException:
            db.rollback()
            raise
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=str(e))


    @staticmethod
    def delete_transaction(trans_id: int, db: Session) -> dict:
        try:
            t = db.query(Transaction).filter(Transaction.id == trans_id).first()
            if not t:
                raise HTTPException(status_code=404, detail="Transaction not found")
            BudgetController.assert_month_unlocked(t.date, db)
            t.is_deleted = True
            for c in t.children:
                c.is_deleted = True
            db.commit()
            return {"message": "success"}
        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=str(e))

    @staticmethod
    def restore_transaction(trans_id: int, db: Session) -> dict:
        try:
            t = db.query(Transaction).filter(Transaction.id == trans_id).first()
            if not t:
                raise HTTPException(status_code=404, detail="Transaction not found")
            BudgetController.assert_month_unlocked(t.date, db)
            t.is_deleted = False
            for c in t.children:
                c.is_deleted = False
            db.commit()
            return {"message": "success"}
        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=str(e))

    @staticmethod
    def split_transaction(trans_id: int, pieces: list, db: Session) -> dict:
        """Split a transaction into pieces, replacing any existing split. Each piece is a
        dict with a positive amount and at most one of budget_item_id / fund_item_id."""
        t = db.query(Transaction).filter(Transaction.id == trans_id).first()
        if not t:
            raise HTTPException(status_code=404, detail="Transaction not found")
        BudgetController.assert_month_unlocked(t.date, db)
        if t.parent_id is not None:
            raise HTTPException(status_code=400, detail="A split piece can't be split again")
        if t.is_deleted:
            raise HTTPException(status_code=400, detail="Restore this transaction before splitting it")
        if len(pieces) < 2:
            raise HTTPException(status_code=400, detail="A split needs at least two pieces")

        for p in pieces:
            if p["amount"] <= 0:
                raise HTTPException(status_code=400, detail="Each piece must have an amount greater than $0")
            if p.get("budget_item_id") and p.get("fund_item_id"):
                raise HTTPException(status_code=400, detail="A piece can't have both a budget item and a sinking fund")

        total = sum(Decimal(p["amount"]) for p in pieces)
        if total != abs(t.amount):
            raise HTTPException(
                status_code=400,
                detail=f"Pieces add up to ${total:.2f} but the transaction is ${abs(t.amount):.2f}"
            )

        try:
            sign = -1 if t.amount < 0 else 1
            t.children.clear()
            for p in pieces:
                t.children.append(Transaction(
                    date=t.date,
                    description=t.description,
                    memo=t.memo,
                    amount=sign * Decimal(p["amount"]),
                    account_id=t.account_id,
                    vendor_id=t.vendor_id,
                    budget_item_id=p.get("budget_item_id"),
                    fund_item_id=p.get("fund_item_id"),
                    is_income=t.is_income,
                    is_deleted=False,
                ))
            t.is_split = True
            db.commit()
            return {"message": "success", "pieces": len(pieces)}
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=str(e))

    @staticmethod
    def unsplit_transaction(trans_id: int, db: Session) -> dict:
        t = db.query(Transaction).filter(Transaction.id == trans_id).first()
        if not t:
            raise HTTPException(status_code=404, detail="Transaction not found")
        BudgetController.assert_month_unlocked(t.date, db)
        if not t.is_split:
            raise HTTPException(status_code=400, detail="Transaction isn't split")
        try:
            t.children.clear()
            t.is_split = False
            db.commit()
            return {"message": "success"}
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=str(e))

    @staticmethod
    def save_purchases(db: Session, purchases):
        if not purchases:
            raise HTTPException(status_code=400, detail="No Supplied Purchases")

        try:
            for purchase in purchases:
                db_trans = db.query(Transaction).filter(Transaction.id == purchase['id']).first()
                if db_trans:
                    if db_trans.budget_item_id != purchase.get('budget_item_id'):
                        db_trans.budget_item_id = purchase.get('budget_item_id')

            db.commit()
            return {'message': 'success'}

        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=400, detail=f"{str(e)}")