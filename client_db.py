# main.py
from datetime import date, datetime
from db.connection import SessionLocal
from db.models.bills import PaymentPlan
from db.models.bills_details import PaymentPlanDetail


def create_payment_plan_with_details():
    db = SessionLocal()
    try:
        # 1️⃣ Tạo đối tượng PaymentPlan (KHÔNG cần id)
        plan = PaymentPlan(
            project_id="PJ00001283",
            plan_date=date(2025, 11, 7),
            amount=25_000_000,
            tax=2_500_000,
            status="DRAFT",
            created_at=datetime.now(),
            created_by="admin",
            is_deleted=False,
            payer="Công ty CP Xây dựng ABC",
            customer_name="Nguyễn Văn A",
            execution_team="Đội thi công 1",
            project_name="Dự án nhà máy X",
            payer_code="PAY001",
            customer_id="CUS001",
            project_number="PRJ-2025-001",
            invoice_date=date(2025, 11, 10),
            pay_for_year=2025,
            pay_for_month=11,
            tax_percent=10.0,
            taxable=True,
        )

        # 2️⃣ Thêm các chi tiết (PaymentPlanDetail)
        detail_1 = PaymentPlanDetail(
            attribute="Vật tư chính",
            product="Xi măng Holcim",
            specification="Bao 50kg",
            quantity=100,
            unit_price=120_000,
            tax=10,
            amount=12_000_000,
            tax_amount=1_200_000,
            note="Đợt 1",
            created_at=datetime.now(),
        )

        detail_2 = PaymentPlanDetail(
            attribute="Nhân công",
            product="Thợ xây",
            specification="Đội 2",
            quantity=10,
            unit_price=1_000_000,
            tax=10,
            amount=10_000_000,
            tax_amount=1_000_000,
            note="Đợt 1",
            created_at=datetime.now(),
        )

        # 3️⃣ Gắn chi tiết vào kế hoạch
        plan.details = [detail_1, detail_2]

        # 4️⃣ Thêm vào session và commit
        db.add(plan)
        db.commit()

        # 5️⃣ Refresh để lấy giá trị id đã auto-generate
        db.refresh(plan)
        for d in plan.details:
            db.refresh(d)

        print("✅ Tạo thành công PaymentPlan:")
        print(f"  ID: {plan.id} | Project: {plan.project_name}")
        for d in plan.details:
            print(f"   ↳ Detail: {d.id} | {d.product} | Amount: {d.amount}")

    except Exception as e:
        db.rollback()
        print("❌ Lỗi:", e)
    finally:
        db.close()


if __name__ == "__main__":
    create_payment_plan_with_details()
