from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from core.database import Base


class Account(Base):
    __tablename__ = "account"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    simplefin_id = Column(String, nullable=True, unique=True, index=True)

    transaction = relationship(
        "Transaction",
        back_populates="account",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Account id={self.id} name={self.name}>"