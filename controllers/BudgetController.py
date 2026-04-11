from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from sqlalchemy import extract
from fastapi import HTTPException
from models.database import *
from datetime import datetime, date
from dateutil.relativedelta import relativedelta


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
    def get_or_create_budget(year: int, month: int, db: Session) -> Budget:
        target_date = date(year, month, 1)
        budget = db.query(Budget).filter(Budget.date == target_date).first()
        return budget


    @staticmethod
    def compute_actual(budget_item_id: int, year: int, month: int, db: Session) -> Decimal:
        result = db.query(func.sum(Transaction.amount)).filter(
            Transaction.budget_item_id == budget_item_id,
            Transaction.is_deleted == False,
            extract('year', Transaction.date) == year,
            extract('month', Transaction.date) == month
        ).scalar()
        return abs(result or Decimal('0'))


    @staticmethod
    def compute_fund_minus(fund_item_id: int, year: int, month: int, db: Session) -> Decimal:
        result = db.query(func.sum(Transaction.amount)).filter(
            Transaction.fund_item_id == fund_item_id,
            Transaction.amount < 0,
            Transaction.is_deleted == False,
            extract('year', Transaction.date) == year,
            extract('month', Transaction.date) == month
        ).scalar()
        return abs(result or Decimal('0'))


    @staticmethod
    def get_budget(year: int, month: int, db: Session) -> dict | None:
        db.expire_all()
        target_date = date(year, month, 1)
        budget = db.query(Budget).filter(Budget.date == target_date).first()
        if not budget:
            return None

        tables = []
        overview = []

        for table in budget.tables:
            if table.isFund:
                line_items = []
                for fi in table.fund_items:
                    minus = BudgetController.compute_fund_minus(fi.id, year, month, db)
                    ending = fi.starting_value + fi.plus - minus
                    line_items.append({
                        "id": fi.id,
                        "name": fi.name,
                        "starting_value": fi.starting_value,
                        "plus": fi.plus,
                        "minus": minus,
                        "ending_value": ending
                    })

                overview.append({
                    "name": table.name,
                    "is_fund": True,
                    "starting": sum(i["starting_value"] for i in line_items),
                    "plus": sum(i["plus"] for i in line_items),
                    "minus": sum(i["minus"] for i in line_items),
                    "ending": sum(i["ending_value"] for i in line_items),
                    "planned": 0,
                    "actual": 0,
                    "remaining": 0
                })

            else:
                line_items = []
                for bi in table.budget_items:
                    actual = BudgetController.compute_actual(bi.id, year, month, db)
                    line_items.append({
                        "id": bi.id,
                        "name": bi.name,
                        "expected": bi.expected,
                        "actual": actual
                    })

                planned = sum(i["expected"] for i in line_items)
                actual = sum(i["actual"] for i in line_items)

                overview.append({
                    "name": table.name,
                    "is_fund": False,
                    "planned": planned,
                    "actual": actual,
                    "remaining": planned - actual,
                    "starting": 0,
                    "plus": 0,
                    "minus": 0,
                    "ending": 0
                })

            tables.append({
                "id": table.id,
                "name": table.name,
                "is_fund": table.isFund,
                "line_items": line_items
            })

        # Income: all positive transactions for the month
        income = db.query(func.sum(Transaction.amount)).filter(
            Transaction.amount > 0,
            Transaction.is_income == True,
            Transaction.is_deleted == False,
            extract('year', Transaction.date) == year,
            extract('month', Transaction.date) == month
        ).scalar() or Decimal('0')

        total_planned = sum(o["planned"] for o in overview if not o["is_fund"])
        total_actual  = sum(o["actual"]  for o in overview if not o["is_fund"])

        return {
            "id": budget.id,
            "date": budget.date.strftime("%Y-%m"),
            "tables": tables,
            "overview": overview,
            "income": income,
            "total_planned": total_planned,
            "total_actual": total_actual,
            "savings": income - total_actual
        }


    @staticmethod
    def init_budget(year: int, month: int, copy_previous: bool, db: Session) -> dict:
        try:
            target_date = date(year, month, 1)

            existing = db.query(Budget).filter(Budget.date == target_date).first()
            if existing:
                db.delete(existing)
                db.flush()

            budget = Budget(date=target_date)
            db.add(budget)
            db.flush()

            if copy_previous:
                prev_date = target_date - relativedelta(months=1)
                prev_budget = db.query(Budget).filter(Budget.date == prev_date).first()

                if prev_budget:
                    prev_year = prev_date.year
                    prev_month = prev_date.month

                    for table in prev_budget.tables:
                        new_table = BudgetTable(
                            name=table.name,
                            budget_id=budget.id,
                            isFund=table.isFund
                        )
                        db.add(new_table)
                        db.flush()

                        if table.isFund:
                            for fi in table.fund_items:
                                prev_minus = BudgetController.compute_fund_minus(fi.id, prev_year, prev_month, db)
                                prev_ending = fi.starting_value + fi.plus - prev_minus
                                db.add(FundItem(
                                    name=fi.name,
                                    starting_value=prev_ending,
                                    plus=fi.plus,
                                    minus=0,
                                    ending_value=prev_ending,
                                    budget_table_id=new_table.id
                                ))
                        else:
                            for bi in table.budget_items:
                                db.add(BudgetItem(
                                    name=bi.name,
                                    expected=bi.expected,
                                    actual=0,
                                    budget_table_id=new_table.id
                                ))

            db.commit()
            return {"message": "success", "budget_id": budget.id}

        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=str(e))


    @staticmethod
    def add_table(budget_id: int, name: str, is_fund: bool, db: Session) -> dict:
        try:
            table = BudgetTable(name=name, budget_id=budget_id, isFund=is_fund)
            db.add(table)
            db.commit()
            db.refresh(table)
            return {"id": table.id, "name": table.name, "is_fund": table.isFund}
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=str(e))


    @staticmethod
    def add_budget_item(budget_table_id: int, name: str, expected: Decimal, db: Session) -> dict:
        try:
            item = BudgetItem(name=name, expected=expected, actual=0, budget_table_id=budget_table_id)
            db.add(item)
            db.commit()
            db.refresh(item)
            return {"id": item.id, "name": item.name, "expected": item.expected, "actual": 0}
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=str(e))


    @staticmethod
    def add_fund_item(budget_table_id: int, name: str, starting_value: Decimal, plus: Decimal, db: Session) -> dict:
        try:
            item = FundItem(
                name=name,
                starting_value=starting_value,
                plus=plus,
                minus=0,
                ending_value=starting_value + plus,
                budget_table_id=budget_table_id
            )
            db.add(item)
            db.commit()
            db.refresh(item)
            return {
                "id": item.id,
                "name": item.name,
                "starting_value": item.starting_value,
                "plus": item.plus,
                "minus": 0,
                "ending_value": item.ending_value
            }
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=str(e))


    @staticmethod
    def update_budget_item(item_id: int, name: str, expected: Decimal, db: Session) -> dict:
        try:
            item = db.query(BudgetItem).filter(BudgetItem.id == item_id).first()
            if not item:
                raise HTTPException(status_code=404, detail="Budget item not found")
            item.name = name
            item.expected = expected
            db.commit()
            return {"id": item.id, "name": item.name, "expected": item.expected}
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=str(e))


    @staticmethod
    def update_fund_item(item_id: int, name: str, plus: Decimal, starting_value: Decimal, db: Session) -> dict:
        try:
            item = db.query(FundItem).filter(FundItem.id == item_id).first()
            if not item:
                raise HTTPException(status_code=404, detail="Fund item not found")
            item.name = name
            item.plus = plus
            item.starting_value = starting_value
            db.commit()
            return {"id": item.id, "name": item.name, "plus": item.plus, "starting_value": item.starting_value}
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=str(e))


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


    @staticmethod
    def update_table(table_id: int, name: str, db: Session) -> dict:
        try:
            table = db.query(BudgetTable).filter(BudgetTable.id == table_id).first()
            if not table:
                raise HTTPException(status_code=404, detail="Table not found")
            table.name = name
            db.commit()
            return {"id": table.id, "name": table.name}
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=str(e))


    @staticmethod
    def delete_table(table_id: int, db: Session) -> dict:
        try:
            table = db.query(BudgetTable).filter(BudgetTable.id == table_id).first()
            if not table:
                raise HTTPException(status_code=404, detail="Table not found")
            db.delete(table)
            db.commit()
            return {"message": "Table deleted"}
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=str(e))


    @staticmethod
    def delete_budget_item(item_id: int, db: Session) -> dict:
        try:
            item = db.query(BudgetItem).filter(BudgetItem.id == item_id).first()
            if not item:
                raise HTTPException(status_code=404, detail="Budget item not found")
            db.query(Transaction).filter(Transaction.budget_item_id == item_id).update({"budget_item_id": None})
            db.delete(item)
            db.commit()
            return {"message": "Budget item deleted"}
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=str(e))


    @staticmethod
    def delete_fund_item(item_id: int, db: Session) -> dict:
        try:
            item = db.query(FundItem).filter(FundItem.id == item_id).first()
            if not item:
                raise HTTPException(status_code=404, detail="Fund item not found")
            db.query(Transaction).filter(Transaction.fund_item_id == item_id).update({"fund_item_id": None})
            db.delete(item)
            db.commit()
            return {"message": "Fund item deleted"}
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=str(e))