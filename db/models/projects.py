from sqlalchemy import Column, Integer, String, Date, DateTime, Boolean, Float, Numeric
from db.connection import Base
class Projects(Base):
    __tablename__ = "projects"
	

    id = Column(String, primary_key=True)
    name = Column(String)
    status = Column(Integer)
    plan_start_date = Column(Date)
    plan_complete_date = Column(Date)
    customer_id = Column(String)
    company_name = Column(String)
    created_at = Column(DateTime)
    created_by = Column(String)
    updated_at = Column(DateTime)
    updated_by = Column(String)
    is_deleted = Column(Boolean)
    project_number = Column(String)
    completed_date = Column(Date)
    end_date = Column(Date)
    tax = Column(Float)
    amount = Column(Numeric)
    entry_cost = Column(Numeric)
    profit = Column(Numeric)
    profit_rate = Column(Float)
    paid_amount = Column(Numeric)
