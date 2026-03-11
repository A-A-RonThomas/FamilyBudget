from sqlalchemy import Column, Integer, String, Boolean
from core.database import Base


class BudgetTable(Base):
    __tablename__ = "budget_table"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    budget_id = Column(Integer, nullable=False)
    isFund = Column(Boolean)

    def __repr__(self):
        return f'<Budget Table - Id: {self.id} - Name: {self.name} - Budget ID: {self.budget_id} - IsFund: {self.isFund}>'