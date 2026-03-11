from sqlalchemy import Column, Integer, String, Float
from sqlalchemy.orm import relationship
from core.database import Base


class BudgetItem(Base):
    __tablename__ = "budget_item"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    expected = Column(Float)
    actual = Column(Float)
    budget_table_id = Column(Integer)

    transaction = relationship("Transaction", back_populates="budget_item")


    def __repr__(self):
        return f'<Budget Item - Id: {self.id} - Name: {self.name}>'