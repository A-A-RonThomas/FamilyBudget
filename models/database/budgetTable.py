from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from core.database import Base


class BudgetTable(Base):
    __tablename__ = "budget_table"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    budget_id = Column(Integer, ForeignKey("budget.id"), nullable=False)
    isFund = Column("isfund", Boolean)

    budget = relationship("Budget", back_populates="tables")
    
    budget_items = relationship("BudgetItem", back_populates="budget_table", cascade="all, delete-orphan", order_by="BudgetItem.id")
    fund_items = relationship("FundItem", back_populates="budget_table", cascade="all, delete-orphan", order_by="FundItem.id")
   

    def __repr__(self):
        return f'<Budget Table - Id: {self.id} - Name: {self.name} - Budget ID: {self.budget_id} - IsFund: {self.isFund}>'