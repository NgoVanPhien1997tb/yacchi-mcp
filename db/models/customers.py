from sqlalchemy import Column, Integer, String, Date, DateTime, Boolean, Float, Numeric
from db.connection import Base
class customers(Base):
    __tablename__ = "customers"
	

    id = Column(String, primary_key=True)
    name = Column(String)
    name_kana = Column(String)
    phone_number = Column(String)
    email = Column(String)
    status = Column(Integer)
    created_at = Column(DateTime)
    created_by = Column(String)
    updated_at = Column(DateTime)
    updated_by = Column(String)
    is_deleted = Column(Boolean)
    tax_code = Column(String)
    cooperation_membership_fee = Column(Float)
    various_membership_fee = Column(Numeric)
    address_1 = Column(String)
    address_2 = Column(String)