from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Column, String, Numeric, SmallInteger, BigInteger, ForeignKey, TIMESTAMP
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from db.connection import Base


class PaymentPlanDetail(Base):
    __tablename__ = "payment_plan_details"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    payment_plan_id: Mapped[Optional[str]] = mapped_column(
        String(15),
        ForeignKey("payment_plans.id", ondelete="RESTRICT", onupdate="RESTRICT")
    )
    attribute: Mapped[Optional[str]] = mapped_column(String(255))
    product: Mapped[Optional[str]] = mapped_column(String(255))
    specification: Mapped[Optional[str]] = mapped_column(String(255))
    quantity: Mapped[Optional[int]] = mapped_column(SmallInteger)
    # unit_id: Mapped[Optional[str]] = mapped_column(
    #     String(15),
    #     ForeignKey("units.id", ondelete="RESTRICT", onupdate="RESTRICT")
    # )
    unit_price: Mapped[Optional[float]] = mapped_column(Numeric(12, 2))
    tax: Mapped[Optional[float]] = mapped_column(Numeric(12, 2))
    device: Mapped[Optional[str]] = mapped_column(String(255))
    amount: Mapped[Optional[float]] = mapped_column(Numeric(12, 2))
    tax_amount: Mapped[Optional[float]] = mapped_column(Numeric(12, 2))
    note: Mapped[Optional[str]] = mapped_column(String(255))
    updated_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=False))
    created_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=False))

    payment_plan: Mapped["PaymentPlan"] = relationship(
        "PaymentPlan",
        back_populates="details"
    )
