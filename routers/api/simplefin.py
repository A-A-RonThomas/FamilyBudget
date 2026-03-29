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
    account = db.query(Account).filter(Account.simplefin_id == simplefin_id).first()
    if not account:
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
# 2. Sync Transactions — deduplicates on simplefin_id
# ---------------------------------------------------------------------------
@router.post("/simplefin/sync")
def sync_transactions(payload: dict = {}, db: Session = Depends(get_db)):
    if not SIMPLEFIN_ACCESS_URL:
        raise HTTPException(status_code=500, detail="SIMPLEFIN_ACCESS_URL not configured")
 
    days = payload.get("days", 90)
    account_ids = payload.get("account_ids", [])  # list of simplefin_ids; empty = all
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
            simplefin_account_id = acct.get("id", "")
 
            # Skip accounts not in the selected list (if a list was provided)
            if account_ids and simplefin_account_id not in account_ids:
                continue
 
            fallback_name = acct.get("name", "unknown")
            account = get_or_create_account_by_simplefin_id(simplefin_account_id, fallback_name, db)
 
            for txn in acct.get("transactions", []):
                simplefin_id = txn.get("id")
                if not simplefin_id:
                    total_skipped += 1
                    continue
 
                existing = db.query(Transaction).filter(
                    Transaction.simplefin_id == simplefin_id
                ).first()
                if existing:
                    total_skipped += 1
                    continue
 
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
 
                description = (
                    txn.get("payee") or
                    txn.get("description") or
                    simplefin_id
                ).lower().strip()
 
                memo = txn.get("memo", None)
 
                normalized, vendor_id = ImportController.auto_categorize(description, db)
 
                db.add(Transaction(
                    date=txn_date,
                    description=normalized,
                    memo=memo,
                    amount=amount,
                    simplefin_id=simplefin_id,
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