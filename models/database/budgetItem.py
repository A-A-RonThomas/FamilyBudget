from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from core.database import Base


class BudgetItem(Base):
    __tablename__ = "budget_item"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    expected = Column(Float, default=0)
    actual = Column(Float, default=0)
    budget_table_id = Column(Integer, ForeignKey("budget_table.id"), nullable=False)

    budget_table = relationship("BudgetTable", back_populates="budget_items")
    transaction = relationship("Transaction", back_populates="budget_item")

    def __repr__(self):
        return f'<BudgetItem id={self.id} name={self.name}>'