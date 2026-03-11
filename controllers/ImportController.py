from fastapi import HTTPException
from models.database import Transaction, Account, Vendor, VendorCode
from datetime import datetime
from sqlalchemy.orm import Session
import hashlib
import csv
import io


class ImportController:

    @staticmethod
    def get_or_create_account(name: str, db: Session) -> Account:
        account = db.query(Account).filter(Account.name == name).first()
        if not account:
            account = Account(name=name)
            db.add(account)
            db.flush()
        return account


    @staticmethod
    def parse_csv(contents: bytes, account: Account) -> list[dict]:
        transactions = []
        reader = csv.reader(io.StringIO(contents.decode("utf-8")))
        for row in reader:
            if not row or row[0] == "Date":
                continue
            if "transfer" in row[1].lower():
                continue
            try:
                transactions.append({
                    "date": datetime.strptime(row[0], "%Y-%m-%d").date(),
                    "description": row[1].lower().strip(),
                    "amount": float(row[4]) * -1 if account.name == "credit" else float(row[4]),
                    "account": account
                })
            except (ValueError, IndexError):
                continue
        return transactions


    @staticmethod
    def generate_hash(date, amount, description) -> str:
        return hashlib.sha256(
            f"{date}|{amount}|{description}".encode("utf-8")
        ).hexdigest()


    @staticmethod
    def auto_categorize(description: str, db: Session) -> tuple[str, int | None]:
        """
        Returns (normalized_description, vendor_id)
        """
        if "check #" in description:
            return description, None

        vendor_code = db.query(VendorCode).filter(VendorCode.code == description).first()
        if vendor_code:
            return vendor_code.vendor.name, vendor_code.vendor.id

        return description, None


    @staticmethod
    async def process_import(files: dict, db: Session) -> dict:
        try:
            imported = 0
            skipped = 0

            for account_name, file in files.items():
                if file is None:
                    continue

                contents = await file.read()
                account = ImportController.get_or_create_account(account_name, db)
                transactions = ImportController.parse_csv(contents, account)

                for t in transactions:
                    hash_str = ImportController.generate_hash(
                        t["date"], t["amount"], t["description"]
                    )

                    existing = db.query(Transaction).filter(Transaction.hash == hash_str).first()
                    if existing:
                        skipped += 1
                        continue

                    normalized, vendor_id = ImportController.auto_categorize(
                        t["description"], db
                    )

                    db.add(Transaction(
                        date=t["date"],
                        description=normalized,
                        orig_description=t["description"],
                        amount=t["amount"],
                        hash=hash_str,
                        vendor_id=vendor_id,
                        account_id=t["account"].id,
                        budget_item_id=None,
                        fund_item_id=None
                    ))
                    imported += 1

            db.commit()
            return {"imported": imported, "skipped": skipped}

        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=str(e))


    @staticmethod
    def get_unreviewed(db: Session) -> list:
        try:
            transactions = db.query(Transaction).order_by(Transaction.date.asc()).all()

            return [
                {
                    "id": t.id,
                    "date": t.date.strftime("%Y-%m-%d"),
                    "description": t.description,
                    "orig_description": t.orig_description,
                    "amount": t.amount,
                    "account": t.account.name.title(),
                    "budget_item": t.budget_item.name if t.budget_item else None,
                    "is_reviewed": t.is_reviewed
                }
                for t in transactions
            ]

        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


    @staticmethod
    def review_transaction(trans_id: int, budget_item_id: int, vendor_name: str | None, orig_description: str, db: Session) -> dict:
        try:
            t = db.query(Transaction).filter(Transaction.id == trans_id).first()
            if not t:
                raise HTTPException(status_code=404, detail="Transaction not found")

            t.budget_item_id = budget_item_id
            t.is_reviewed = True
            if vendor_name:
                t.description = vendor_name

            # apply same category and vendor name to all matching unreviewed transactions
            matches = db.query(Transaction).filter(
                Transaction.orig_description == orig_description,
                Transaction.is_reviewed == False,
                Transaction.id != trans_id
            ).all()

            for match in matches:
                match.budget_item_id = budget_item_id
                match.is_reviewed = True
                if vendor_name:
                    match.description = vendor_name

            db.commit()

            return {"message": "success", "also_updated": len(matches)}

        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=str(e))


    @staticmethod
    def save_vendor(name: str, budget_item_id: int, codes: list[str], db: Session) -> Vendor:
        try:
            vendor = db.query(Vendor).filter(Vendor.name == name).first()
            if not vendor:
                vendor = Vendor(name=name, default_budget_item_id=budget_item_id)
                db.add(vendor)
                db.flush()

            for code in codes:
                existing_code = db.query(VendorCode).filter(VendorCode.code == code).first()
                if not existing_code:
                    db.add(VendorCode(code=code, vendor_id=vendor.id))

            db.commit()
            return {
                "id": vendor.id,
                "name": vendor.name,
                "default_budget_item_id": vendor.default_budget_item_id,
                "default_fund_item_id": vendor.default_fund_item_id
            }

        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=str(e))