from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from sqlalchemy import extract
from models.database import Transaction, BudgetItem, FundItem, BudgetTable, Budget
from datetime import date
from dateutil.relativedelta import relativedelta


class ChartController:

    @staticmethod
    def get_monthly_cashflow(months: int, db: Session) -> list:
        """Income vs spending for the last N months."""
        end_date = date.today().replace(day=1)
        start_date = end_date - relativedelta(months=months - 1)

        income_rows = db.query(
            extract('year', Transaction.date).label('year'),
            extract('month', Transaction.date).label('month'),
            func.sum(Transaction.amount).label('total')
        ).filter(
            Transaction.amount > 0,
            Transaction.is_income == True,
            Transaction.date >= start_date
        ).group_by(
            extract('year', Transaction.date),
            extract('month', Transaction.date)
        ).all()

        spending_rows = db.query(
            extract('year', Transaction.date).label('year'),
            extract('month', Transaction.date).label('month'),
            func.sum(Transaction.amount).label('total')
        ).filter(
            Transaction.amount < 0,
            Transaction.date >= start_date
        ).group_by(
            extract('year', Transaction.date),
            extract('month', Transaction.date)
        ).all()

        income_map = {(int(r.year), int(r.month)): float(abs(r.total or 0)) for r in income_rows}
        spending_map = {(int(r.year), int(r.month)): float(abs(r.total or 0)) for r in spending_rows}

        result = []
        current = start_date
        while current <= end_date:
            key = (current.year, current.month)
            result.append({
                "label": current.strftime("%b %Y"),
                "income": round(income_map.get(key, 0), 2),
                "spending": round(spending_map.get(key, 0), 2),
            })
            current += relativedelta(months=1)

        return result

    @staticmethod
    def get_savings_trend(months: int, db: Session) -> list:
        """Net savings (income - spending) for the last N months."""
        cashflow = ChartController.get_monthly_cashflow(months, db)
        return [
            {
                "label": m["label"],
                "savings": round(m["income"] - m["spending"], 2)
            }
            for m in cashflow
        ]

    @staticmethod
    def get_spending_by_category(year: int, month: int | None, db: Session) -> list:
        """Spending broken down by budget category for a year or specific month."""
        q = db.query(
            BudgetItem.name,
            func.sum(func.abs(Transaction.amount)).label('total')
        ).join(
            Transaction, Transaction.budget_item_id == BudgetItem.id
        ).filter(Transaction.amount < 0)

        q = q.filter(extract('year', Transaction.date) == year)
        if month:
            q = q.filter(extract('month', Transaction.date) == month)

        rows = q.group_by(BudgetItem.name).order_by(
            func.sum(func.abs(Transaction.amount)).desc()
        ).all()

        return [{"name": r.name.title(), "total": round(float(r.total), 2)} for r in rows]

    @staticmethod
    def get_budget_vs_actual(year: int, month: int, db: Session) -> list:
        """Planned vs actual per budget item for a given month."""
        budget = db.query(Budget).filter(
            Budget.date == date(year, month, 1)
        ).first()
        if not budget:
            return []

        result = []
        for table in budget.tables:
            if table.isFund:
                continue
            for bi in table.budget_items:
                actual = db.query(func.sum(Transaction.amount)).filter(
                    Transaction.budget_item_id == bi.id,
                    Transaction.amount < 0,
                    extract('year', Transaction.date) == year,
                    extract('month', Transaction.date) == month
                ).scalar()
                result.append({
                    "name": bi.name.title(),
                    "planned": round(float(bi.expected), 2),
                    "actual": round(float(abs(actual or 0)), 2)
                })

        return sorted(result, key=lambda x: x["planned"], reverse=True)

    @staticmethod
    def get_fund_balances_over_time(months: int, db: Session) -> dict:
        """Ending balance per sinking fund across the last N months."""
        end_date = date.today().replace(day=1)
        start_date = end_date - relativedelta(months=months - 1)

        # Collect all budget months in range
        budgets = db.query(Budget).filter(
            Budget.date >= start_date,
            Budget.date <= end_date
        ).order_by(Budget.date).all()

        # Gather all unique fund names across all budgets
        fund_names = set()
        for b in budgets:
            for table in b.tables:
                if table.isFund:
                    for fi in table.fund_items:
                        fund_names.add(fi.name.title())

        labels = []
        # fund_name -> list of ending values (None if not present that month)
        series = {name: [] for name in fund_names}

        for b in budgets:
            labels.append(b.date.strftime("%b %Y"))
            year, month = b.date.year, b.date.month

            # Build map of fund name -> ending value for this month
            month_map = {}
            for table in b.tables:
                if not table.isFund:
                    continue
                for fi in table.fund_items:
                    minus = db.query(func.sum(Transaction.amount)).filter(
                        Transaction.fund_item_id == fi.id,
                        Transaction.amount < 0,
                        extract('year', Transaction.date) == year,
                        extract('month', Transaction.date) == month
                    ).scalar() or 0
                    ending = float(fi.starting_value) + float(fi.plus) - float(abs(minus))
                    month_map[fi.name.title()] = round(ending, 2)

            for name in fund_names:
                series[name].append(month_map.get(name))

        return {"labels": labels, "series": series}