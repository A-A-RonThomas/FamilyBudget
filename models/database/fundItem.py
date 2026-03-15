from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from core.database import Base


class FundItem(Base):
    __tablename__ = "fund_item"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    starting_value = Column(Float, default=0)
    plus = Column(Float, default=0)
    minus = Column(Float, default=0)
    ending_value = Column(Float, default=0)
    budget_table_id = Column(Integer, ForeignKey("budget_table.id"), nullable=False)

    budget_table = relationship("BudgetTable", back_populates="fund_items")
    transaction = relationship("Transaction", back_populates="fund_item")

    def __repr__(self):
        return f'<FundItem id={self.id} name={self.name}>'