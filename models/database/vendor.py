from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from core.database import Base


class Vendor(Base):
    __tablename__ = "vendor"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)

    always_ignore = Column(Boolean, nullable=False, default=False)
    default_category_name = Column(String, nullable=True)
    default_category_is_fund = Column(Boolean, nullable=True)

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