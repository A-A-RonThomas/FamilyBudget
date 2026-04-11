from sqlalchemy import Column, Integer, String, Numeric, Date, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from core.database import Base


class Transaction(Base):
    __tablename__ = "transaction"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False)
    description = Column(String, nullable=False)       # payee from SimpleFIN (clean)
    memo = Column(String, nullable=True)               # memo from SimpleFIN
    amount = Column(Numeric(10, 2), nullable=False)
    simplefin_id = Column(String, nullable=True, unique=True, index=True)  # null for manual entries

    account_id = Column(Integer, ForeignKey("account.id"), nullable=False)
    account = relationship("Account", back_populates="transaction")

    vendor_id = Column(Integer, ForeignKey("vendor.id"), nullable=True)
    vendor = relationship("Vendor", back_populates="transactions")

    budget_item_id = Column(Integer, ForeignKey("budget_item.id"), nullable=True)
    budget_item = relationship("BudgetItem", back_populates="transaction")

    fund_item_id = Column(Integer, ForeignKey("fund_item.id"), nullable=True)
    fund_item = relationship("FundItem", back_populates="transaction")

    is_income = Column(Boolean, default=True, nullable=False)

    def __repr__(self):
        return f"<Transaction id={self.id} date={self.date} amount={self.amount}>"