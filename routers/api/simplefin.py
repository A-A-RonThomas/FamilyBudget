import os
import requests
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from dotenv import load_dotenv

from core.database import get_db
from models.database.transaction import Transaction
from models.database.account import Account
from controllers.ImportController import ImportController

load_dotenv()

SIMPLEFIN_ACCESS_URL = os.getenv("SIMPLEFIN_ACCESS_URL")

router = APIRouter()


def get_or_create_account_by_simplefin_id(
    simplefin_id: str,
    fallback_name: str,
    db: Session
) -> Account:
    """
    Look up an account by its SimpleFIN account ID.
    If not found, create a new one using the fallback name from SimpleFIN.
    This means renamed accounts are always found by ID, not by name.
    """
    account = db.query(Account).filter(Account.simplefin_id == simplefin_id).first()
    if not account:
        # New account — create it with the SimpleFIN name as a starting point
        name = fallback_name.lower().strip()
        account = Account(name=name, simplefin_id=simplefin_id)
        db.add(account)
        db.flush()
    return account


# ---------------------------------------------------------------------------
# 1. Get Accounts — fetches live account info from SimpleFIN
# ---------------------------------------------------------------------------
@router.get("/simplefin/accounts")
def get_accounts(db: Session = Depends(get_db)):
    if not SIMPLEFIN_ACCESS_URL:
        raise HTTPException(status_code=500, detail="SIMPLEFIN_ACCESS_URL not configured")

    try:
        response = requests.get(f"{SIMPLEFIN_ACCESS_URL}/accounts", timeout=30)
        response.raise_for_status()
        data = response.json()

        accounts = []
        for acct in data.get("accounts", []):
            simplefin_id = acct.get("id", "")

            # Look up local account to get the user's renamed version
            local = db.query(Account).filter(Account.simplefin_id == simplefin_id).first()
            display_name = local.name if local else acct.get("name", "Unknown").lower()

            accounts.append({
                "simplefin_id": simplefin_id,
                "name": display_name,
                "balance": acct.get("balance", "0"),
                "currency": acct.get("currency", "USD"),
                "org": acct.get("org", {}).get("name", "Unknown"),
            })

        return accounts

    except requests.RequestException as e:
        raise HTTPException(status_code=400, detail=f"SimpleFIN error: {str(e)}")


# ---------------------------------------------------------------------------
# 2. Sync Transactions — pulls from SimpleFIN and saves using ImportController
#    logic (same hash deduplication + auto-categorization as CSV import)
# ---------------------------------------------------------------------------
@router.post("/simplefin/sync")
def sync_transactions(payload: dict = {}, db: Session = Depends(get_db)):
    if not SIMPLEFIN_ACCESS_URL:
        raise HTTPException(status_code=500, detail="SIMPLEFIN_ACCESS_URL not configured")

    days = payload.get("days", 30)
    start_date = datetime.now() - timedelta(days=days)
    start_unix = int(start_date.timestamp())

    try:
        url = f"{SIMPLEFIN_ACCESS_URL}/accounts?start-date={start_unix}&transactions=1"
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()

    except requests.RequestException as e:
        raise HTTPException(status_code=400, detail=f"SimpleFIN error: {str(e)}")

    total_imported = 0
    total_skipped = 0

    try:
        for acct in data.get("accounts", []):
            simplefin_id = acct.get("id", "")
            fallback_name = acct.get("name", "unknown")

            # Always look up by SimpleFIN ID — safe even after renaming
            account = get_or_create_account_by_simplefin_id(simplefin_id, fallback_name, db)

            for txn in acct.get("transactions", []):
                try:
                    amount = float(txn.get("amount", "0"))
                except ValueError:
                    total_skipped += 1
                    continue

                posted = txn.get("posted")
                if not posted:
                    total_skipped += 1
                    continue
                txn_date = datetime.fromtimestamp(posted).date()

                # Prefer payee (clean merchant name) over raw description
                description = (
                    txn.get("payee") or
                    txn.get("description") or
                    txn.get("id", "unknown")
                ).lower().strip()

                hash_str = ImportController.generate_hash(txn_date, amount, description)

                existing = db.query(Transaction).filter(
                    Transaction.hash == hash_str
                ).first()
                if existing:
                    total_skipped += 1
                    continue

                normalized, vendor_id = ImportController.auto_categorize(description, db)

                db.add(Transaction(
                    date=txn_date,
                    description=normalized,
                    orig_description=description,
                    amount=amount,
                    hash=hash_str,
                    account_id=account.id,
                    vendor_id=vendor_id,
                    budget_item_id=None,
                    fund_item_id=None,
                ))
                total_imported += 1

        db.commit()

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    return {"imported": total_imported, "skipped": total_skipped}