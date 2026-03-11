from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from fastapi import HTTPException
from models.database import *
from datetime import datetime


class BudgetController:
    

    @staticmethod
    def save_budget(data, db: Session):

        if not data:
            raise HTTPException(status_code=400, detail="No data supplied")

        budget = db.query(Budget).filter(
            func.strftime('%Y-%m', Budget.date) == data['date']
        ).first()

        if not budget:
            budget = Budget(date=datetime.strptime(data['date'], '%Y-%m'))
            db.add(budget)
            db.commit()
            db.refresh(budget)

        for budget_table_type in data['budget_tables']:

            for budget_table in data['budget_tables'][budget_table_type]:

                db_budget_table = db.query(BudgetTable).filter(
                    BudgetTable.id == budget_table
                ).first()

                if not db_budget_table:
                    db_budget_table = BudgetTable(
                        name=data['budget_tables'][budget_table_type][budget_table]['name'],
                        budget_id=budget.id,
                        isFund=0 if budget_table_type == 'non_funds' else 1
                    )
                    db.add(db_budget_table)
                    db.commit()
                    db.refresh(db_budget_table)

                db_budget_table.name = data['budget_tables'][budget_table_type][budget_table]['name']

                for budget_item in data['budget_tables'][budget_table_type][budget_table]['items']:

                    if db_budget_table.isFund:

                        if 'id' not in budget_item:
                            db.add(
                                FundItem(
                                    name=budget_item['name'],
                                    plus=budget_item['plus'],
                                    minus=budget_item['minus'],
                                    ending_value=budget_item['ending_value'],
                                    starting_value=budget_item['starting_value'],
                                    budget_table_id=db_budget_table.id
                                )
                            )

                        else:
                            db_budget_item = db.query(FundItem).filter(
                                FundItem.id == budget_item['id']
                            ).first()

                            for key in budget_item:
                                setattr(db_budget_item, key, budget_item[key])

                    else:

                        if 'id' not in budget_item:
                            db.add(
                                BudgetItem(
                                    name=budget_item['name'],
                                    expected=budget_item['expected'],
                                    actual=budget_item['actual'],
                                    budget_table_id=db_budget_table.id
                                )
                            )

                        else:
                            db_budget_item = db.query(BudgetItem).filter(
                                BudgetItem.id == budget_item['id']
                            ).first()

                            for key in budget_item:
                                setattr(db_budget_item, key, budget_item[key])

        db.commit()

        return {"message": "Save successful"}
    
    @staticmethod
    def create_budget_item(name: str, db: Session) -> dict:
        try:
            budget_item = BudgetItem(name=name, expected=0, actual=0)
            db.add(budget_item)
            db.commit()
            db.refresh(budget_item)
            return {"id": budget_item.id, "name": budget_item.name}
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=str(e))