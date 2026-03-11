from sqlalchemy import Column, Integer, Date
from core.database import Base


class Budget(Base):
    __tablename__ = "budget"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False)

    def __repr__(self):
        return f'<Budget - Id: {self.id} - Date: {self.date}>'