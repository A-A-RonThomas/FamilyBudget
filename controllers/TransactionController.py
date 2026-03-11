from fastapi import HTTPException
from models.database import Transaction, Account, Vendor, VendorCode
from datetime import datetime
import hashlib

from sqlalchemy.orm import Session
from sqlalchemy import extract

class TransactionController:
    @staticmethod
    def generate_transaction_hash(el):
        hash_input = f"{el[0]}|{el[1]}|{el[2]}|{el[4]}|{el[6]}"
        return hashlib.sha256(hash_input.encode('utf-8')).hexdigest()


    @staticmethod
    def filter_new_purchases(db: Session, data):
        incoming = data
        for each in incoming:
            each.append(TransactionController.generate_transaction_hash(each))

        target_date = datetime.strptime(data[0][0], "%Y-%m-%d").date()
        logged_hashes = [
            t.hash for t in db.query(Transaction)
            .filter(Transaction.date >= target_date)
            .all()
        ]

        filtered = [el for el in incoming if el[len(el) - 1] not in logged_hashes]
        return filtered


    @staticmethod
    def insert_transactions(data, db: Session):
        if data:
            try:
                for el in TransactionController.filter_new_purchases(data):
                    new_trans = Transaction(
                        date=datetime.strptime(el[0], "%Y-%m-%d"),
                        description=el[1],
                        orig_description=el[2],
                        amount=float(el[4]) * -1 if el[6] == 4 else float(el[4]),
                        hash=el[7],
                        account_id=el[6]
                    )
                    db.add(new_trans)
                db.commit()
                return {'message': 'Data Inserted'}

            except Exception as e:
                raise HTTPException(status_code=500, detail=f'{str(e)}')
        else:
            raise HTTPException(status_code=400, detail="No Data Supplied")


    @staticmethod
    def get_all(db: Session):
        try:
            transactions = db.query(Transaction).order_by(Transaction.date.desc()).all()
            account_dict = {a.id: a.name for a in db.query(Account).all()}

            to_send = [{
                'date': t.date.strftime('%Y-%m-%d'),
                'description': t.description,
                'amount': t.amount,
                'account': account_dict[t.account_id]
            } for t in transactions]

            return {"message": to_send}

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"{str(e)}")


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
                    'orig_description': t.orig_description,
                    'amount': t.amount,
                    'account': account_dict[t.account_id].title(),
                    'budget_category': t.budget_item.name if t.budget_item else None,
                    'budget_item_id': t.budget_item_id,
                    'vendor_id': t.vendor_id
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
                    'orig_description': t.orig_description,
                    'amount': t.amount,
                    'account': account_dict[t.account_id].title(),
                    'budget_category': t.budget_item.name if t.budget_item else None,
                    'budget_item_id': t.budget_item_id,
                    'vendor_id': t.vendor_id
                }
                for t in incomes
            ]

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"{str(e)}")


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
    
    @staticmethod
    def update_transaction(trans_id: int, date, description: str, budget_item_id: int | None, db: Session) -> dict:
        try:
            t = db.query(Transaction).filter(Transaction.id == trans_id).first()
            if not t:
                raise HTTPException(status_code=404, detail="Transaction not found")

            t.date = date
            t.budget_item_id = budget_item_id

            # auto save vendor for non-checks
            if "check #" not in t.orig_description.lower():
                vendor = db.query(Vendor).filter(Vendor.name == description).first()
                if not vendor:
                    vendor = Vendor(name=description)
                    db.add(vendor)
                    db.flush()

                existing_code = db.query(VendorCode).filter(VendorCode.code == t.orig_description).first()
                if not existing_code:
                    db.add(VendorCode(code=t.orig_description, vendor_id=vendor.id))

                t.vendor_id = vendor.id
                # do not update t.description — display name comes from vendor.name via FK
            else:
                t.description = description  # only checks update description directly

            # update matching transactions with no vendor yet
            matches = db.query(Transaction).filter(
                Transaction.orig_description == t.orig_description,
                Transaction.vendor_id == None,
                Transaction.id != trans_id
            ).all()

            for match in matches:
                match.budget_item_id = budget_item_id
                match.vendor_id = t.vendor_id

            db.commit()
            return {"message": "success", "also_updated": len(matches)}

        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=str(e))