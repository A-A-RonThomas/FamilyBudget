from fastapi import HTTPException
from models.database import Transaction, Account, Vendor, VendorCode
from sqlalchemy.orm import Session
from sqlalchemy import extract


class TransactionController:

    @staticmethod
    def get_all_purchases(db: Session, year=None, month=None):
        try:
            query = db.query(Transaction).filter(Transaction.amount < 0)

            if year:
                query = query.filter(extract('year', Transaction.date) == year)
            if month:
                query = query.filter(extract('month', Transaction.date) == month)

            query = query.order_by(Transaction.date.asc())
            purchases = query.all()
            account_dict = {a.id: a.name for a in db.query(Account).all()}

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
                }
                for t in incomes
            ]

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"{str(e)}")

    @staticmethod
    def update_transaction(trans_id: int, date, description: str, budget_item_id: int | None, fund_item_id: int | None, is_income: bool | None, db: Session) -> dict:
        try:
            print(f"update_transaction called: trans_id={trans_id}, budget_item_id={budget_item_id}, fund_item_id={fund_item_id}")
            t = db.query(Transaction).filter(Transaction.id == trans_id).first()
            if not t:
                raise HTTPException(status_code=404, detail="Transaction not found")

            t.date = date
            t.budget_item_id = budget_item_id
            t.fund_item_id = fund_item_id
            if is_income is not None:
                t.is_income = is_income

            # Save or find vendor by name
            vendor = db.query(Vendor).filter(Vendor.name == description.lower().strip()).first()
            if not vendor:
                vendor = Vendor(name=description.lower().strip())
                db.add(vendor)
                db.flush()

            t.vendor_id = vendor.id

            # Bulk match: update all unreviewed transactions with same description
            matches = db.query(Transaction).filter(
                Transaction.description == t.description,
                Transaction.vendor_id == None,
                Transaction.id != trans_id
            ).all()

            for match in matches:
                match.budget_item_id = budget_item_id
                match.fund_item_id = fund_item_id
                match.vendor_id = vendor.id

            db.commit()
            return {"message": "success", "also_updated": len(matches)}

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