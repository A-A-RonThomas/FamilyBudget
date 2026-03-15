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
        name = name.lower().strip()
        account = db.query(Account).filter(Account.name == name).first()
        if not account:
            account = Account(name=name)
            db.add(account)
            db.flush()
        return account

    @staticmethod
    def get_all_accounts(db: Session) -> list:
        return db.query(Account).order_by(Account.name).all()

    @staticmethod
    def parse_csv(contents: bytes, account: Account, negate: bool) -> list[dict]:
        transactions = []
        reader = csv.reader(io.StringIO(contents.decode("utf-8")))
        for row in reader:
            if not row or row[0] == "Date":
                continue
            if "transfer" in row[1].lower():
                continue
            try:
                amount = float(row[4])
                if negate:
                    amount = amount * -1
                transactions.append({
                    "date": datetime.strptime(row[0], "%Y-%m-%d").date(),
                    "description": row[1].lower().strip(),
                    "amount": amount,
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
        if "check #" in description:
            return description, None

        vendor_code = db.query(VendorCode).filter(VendorCode.code == description).first()
        if vendor_code:
            return vendor_code.vendor.name, vendor_code.vendor.id

        return description, None

    @staticmethod
    async def process_import(file, account_id: int, negate: bool, db: Session) -> dict:
        try:
            account = db.query(Account).filter(Account.id == account_id).first()
            if not account:
                raise HTTPException(status_code=404, detail="Account not found")

            contents = await file.read()
            transactions = ImportController.parse_csv(contents, account, negate)

            imported = 0
            skipped = 0

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
                    account_id=account.id,
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