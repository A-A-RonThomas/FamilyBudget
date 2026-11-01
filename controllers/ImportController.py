from decimal import Decimal
from fastapi import HTTPException
from models.database import Transaction, Account, Vendor, VendorCode, Budget, BudgetTable, BudgetItem, FundItem
from datetime import datetime, date as date_type
from sqlalchemy.orm import Session
from sqlalchemy import extract, func
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
                amount = Decimal(row[4])
                if negate:
                    amount = amount * Decimal('-1')
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
    def auto_categorize(description: str, db: Session) -> tuple[str, int | None]:
        if "check #" in description:
            return description, None

        vendor_code = db.query(VendorCode).filter(VendorCode.code == description).first()
        if vendor_code:
            return vendor_code.vendor.name, vendor_code.vendor.id

        vendor = db.query(Vendor).filter(Vendor.name == description).first()
        if vendor:
            return vendor.name, vendor.id

        return description, None

    @staticmethod
    def apply_vendor_rules(vendor_id: int | None, txn_date: date_type, db: Session) -> dict:
        """Resolve a vendor's persistent rules (always-ignore / default category) for a
        transaction landing on txn_date. Category names are matched against whichever
        budget exists for that month, since budget items are recreated each month."""
        result = {"is_deleted": False, "budget_item_id": None, "fund_item_id": None}
        if not vendor_id:
            return result

        vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
        if not vendor:
            return result

        if vendor.always_ignore:
            result["is_deleted"] = True
            return result

        if vendor.default_category_name:
            budget = db.query(Budget).filter(
                extract('year', Budget.date) == txn_date.year,
                extract('month', Budget.date) == txn_date.month
            ).first()
            if budget:
                if vendor.default_category_is_fund:
                    item = db.query(FundItem).join(
                        BudgetTable, FundItem.budget_table_id == BudgetTable.id
                    ).filter(
                        BudgetTable.budget_id == budget.id,
                        func.lower(FundItem.name) == vendor.default_category_name.lower()
                    ).first()
                    if item:
                        result["fund_item_id"] = item.id
                else:
                    item = db.query(BudgetItem).join(
                        BudgetTable, BudgetItem.budget_table_id == BudgetTable.id
                    ).filter(
                        BudgetTable.budget_id == budget.id,
                        func.lower(BudgetItem.name) == vendor.default_category_name.lower()
                    ).first()
                    if item:
                        result["budget_item_id"] = item.id

        return result

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

            from controllers.BudgetController import BudgetController

            for t in transactions:
                # Late transactions for a locked month are recorded in the earliest open month;
                # dedupe against both dates so re-importing the same file doesn't duplicate them
                original_date = t["date"]
                t["date"] = BudgetController.open_date_for(original_date, db)
                existing = db.query(Transaction).filter(
                    Transaction.date.in_({original_date, t["date"]}),
                    Transaction.amount == t["amount"],
                    Transaction.description == t["description"],
                    Transaction.account_id == account.id
                ).first()
                if existing:
                    skipped += 1
                    continue

                normalized, vendor_id = ImportController.auto_categorize(
                    t["description"], db
                )
                rules = ImportController.apply_vendor_rules(vendor_id, t["date"], db)

                db.add(Transaction(
                    date=t["date"],
                    description=normalized,
                    memo=f"Originally dated {original_date.isoformat()}" if t["date"] != original_date else None,
                    amount=t["amount"],
                    vendor_id=vendor_id,
                    account_id=account.id,
                    budget_item_id=rules["budget_item_id"],
                    fund_item_id=rules["fund_item_id"],
                    is_deleted=rules["is_deleted"]
                ))
                imported += 1

            db.commit()
            return {"imported": imported, "skipped": skipped}

        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=str(e))

