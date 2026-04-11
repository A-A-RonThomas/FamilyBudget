from sqlalchemy import Column, Integer, String, Numeric, ForeignKey
from sqlalchemy.orm import relationship
from core.database import Base


class FundItem(Base):
    __tablename__ = "fund_item"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    starting_value = Column(Numeric(10, 2), default=0)
    plus = Column(Numeric(10, 2), default=0)
    minus = Column(Numeric(10, 2), default=0)
    ending_value = Column(Numeric(10, 2), default=0)
    budget_table_id = Column(Integer, ForeignKey("budget_table.id"), nullable=False)

    budget_table = relationship("BudgetTable", back_populates="fund_items")
    transaction = relationship("Transaction", back_populates="fund_item")

    def __repr__(self):
        return f'<FundItem id={self.id} name={self.name}>'