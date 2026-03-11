from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from core.database import Base


class Vendor(Base):
    __tablename__ = "vendor"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)

    default_budget_item_id = Column(Integer, ForeignKey("budget_item.id"), nullable=True)
    default_fund_item_id = Column(Integer, ForeignKey("fund_item.id"), nullable=True)

    default_budget_item = relationship("BudgetItem")
    default_fund_item = relationship("FundItem")

    codes = relationship("VendorCode", back_populates="vendor")
    transactions = relationship("Transaction", back_populates="vendor")

    def __repr__(self):
        return f"<Vendor id={self.id} name={self.name}>"


class VendorCode(Base):
    __tablename__ = "vendor_code"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, nullable=False, unique=True)
    vendor_id = Column(Integer, ForeignKey("vendor.id"), nullable=False)

    vendor = relationship("Vendor", back_populates="codes")

    def __repr__(self):
        return f"<VendorCode id={self.id} code={self.code}>"