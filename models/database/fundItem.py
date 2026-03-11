from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from core.database import Base


class FundItem(Base):
    __tablename__ = "fund_item"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    starting_value = Column(Float)
    plus = Column(Float)
    minus = Column(Float)
    ending_value = Column(Float)
    budget_table_id = Column(Integer, ForeignKey("budget_table.id"))

    transaction = relationship("Transaction", back_populates="fund_item")