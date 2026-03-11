from sqlalchemy.orm import Session
from fastapi import HTTPException
from models.database import Account


class AccountController:

    @staticmethod
    def populate_default_accounts(db: Session):

        accounts = db.query(Account).all()

        if not accounts:
            db.add(Account(name="joint"))
            db.add(Account(name="grocery"))
            db.add(Account(name="sinking"))
            db.add(Account(name="credit"))

            db.commit()


    @staticmethod
    def get_account_dict(db: Session):

        accounts = db.query(Account).all()

        if not accounts:
            raise HTTPException(
                status_code=500,
                detail="Error retrieving account dictionary"
            )

        return {a.name: a.id for a in accounts}