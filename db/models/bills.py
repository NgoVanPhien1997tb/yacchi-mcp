from datetime import date, datetime
from typing import Optional, List

from sqlalchemy import (
    Column, String, Date, Numeric, Boolean, Float, CHAR, ForeignKey, SmallInteger, BigInteger, TIMESTAMP, event
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from db.connection import Base
import sqlalchemy as sa


class PaymentPlan(Base):
    __tablename__ = "payment_plans"

    id: Mapped[str] = mapped_column(String(15), primary_key=True)
    project_id: Mapped[Optional[str]] = mapped_column(String(15))
    plan_date: Mapped[Optional[date]] = mapped_column(Date)
    amount: Mapped[Optional[float]] = mapped_column(Numeric(10, 2))
    tax: Mapped[Optional[float]] = mapped_column(Numeric(10, 2))
    status: Mapped[Optional[str]] = mapped_column(String(25))
    is_pay_all: Mapped[Optional[bool]] = mapped_column(Boolean)
    created_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=False))
    created_by: Mapped[Optional[str]] = mapped_column(String(150))
    updated_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=False))
    updated_by: Mapped[Optional[str]] = mapped_column(String(150))
    is_deleted: Mapped[Optional[bool]] = mapped_column(Boolean)
    payment_plan_date_1: Mapped[Optional[date]] = mapped_column(Date)
    payment_plan_date_2: Mapped[Optional[date]] = mapped_column(Date)
    pay_for_month: Mapped[Optional[int]] = mapped_column(SmallInteger)
    taxable: Mapped[Optional[bool]] = mapped_column(Boolean)
    tax_percent: Mapped[Optional[float]] = mapped_column(Float)
    round_tax: Mapped[Optional[str]] = mapped_column(CHAR(1))
    round_amount: Mapped[Optional[str]] = mapped_column(CHAR(1))
    payer: Mapped[Optional[str]] = mapped_column(String(255))
    customer_name: Mapped[Optional[str]] = mapped_column(String(255))
    execution_team: Mapped[Optional[str]] = mapped_column(String(255))
    execution_date: Mapped[Optional[date]] = mapped_column(Date)
    project_name: Mapped[Optional[str]] = mapped_column(String(255))
    payer_code: Mapped[Optional[str]] = mapped_column(String(25))
    customer_id: Mapped[Optional[str]] = mapped_column(String(15))
    project_number: Mapped[Optional[str]] = mapped_column(String(25))
    invoice_date: Mapped[Optional[date]] = mapped_column(Date)
    pay_for_year: Mapped[Optional[int]] = mapped_column(SmallInteger)

    # Quan hệ 1-nhiều
    details: Mapped[List["PaymentPlanDetail"]] = relationship(
        "PaymentPlanDetail",
        back_populates="payment_plan",
        cascade="all, delete-orphan",
    )


@event.listens_for(PaymentPlan, "before_insert")
def _gen_payment_plan_id(mapper, connection, target: "PaymentPlan"):
    # gọi nextval từ Postgres (an toàn concurrency)
    next_val = connection.execute(sa.text("SELECT nextval('payment_plans_id_seq')")).scalar_one()
    target.id = f"PP{next_val:08d}"
