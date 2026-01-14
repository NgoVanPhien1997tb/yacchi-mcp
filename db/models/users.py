from sqlalchemy import Column, Integer, String, DateTime, Boolean
from db.connection import Base

class Users(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True)
    username = Column(String)
    email = Column(String)
    full_name = Column(String)
    phone_number = Column(String)
    role = Column(String)
    status = Column(Integer)
    created_at = Column(DateTime)
    created_by = Column(String)
    updated_at = Column(DateTime)
    updated_by = Column(String)
    is_deleted = Column(Boolean)
