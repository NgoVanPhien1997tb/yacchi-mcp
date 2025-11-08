from typing import Annotated, Optional, List, Union, TypedDict, Literal, cast
from sqlalchemy.sql import text
from db.connection import SessionLocal
import json
from datetime import date, datetime, time
from decimal import Decimal
from uuid import UUID
from enum import Enum
from pydantic import BaseModel, Field, field_validator, ValidationInfo
from db.models.bills import PaymentPlan
from db.models.bills_details import PaymentPlanDetail
from fastmcp import FastMCP

mcp_bills = FastMCP("bills")


def _to_jsonable(v):
    if isinstance(v, (datetime, date, time)):
        return v.isoformat()
    if isinstance(v, Decimal):
        return float(v)
    if isinstance(v, UUID):
        return str(v)
    if isinstance(v, Enum):
        return v.value
    return v

def _rows_to_dicts(rows):
    out = []
    for r in rows:
        m = r if isinstance(r, dict) else dict(r)
        out.append({k: _to_jsonable(v) for k, v in m.items()})
    return out

def _norm_str_list(val: Optional[Union[List[str], str]]) -> Optional[List[str]]:
    if val is None:
        return None
    if isinstance(val, list):
        return [str(x) for x in val]
    if isinstance(val, str):
        s = val.strip()
        # JSON array string: '["A","B"]'
        if s.startswith("[") and s.endswith("]"):
            try:
                parsed = json.loads(s)
                if isinstance(parsed, list):
                    return [str(x) for x in parsed]
            except json.JSONDecodeError:
                pass
        # CSV / single token
        return [x.strip() for x in s.split(",") if x.strip()]
    # tuple/set…
    return [str(x) for x in list(val)]

class BillRow(TypedDict, total=False):
    bill_number:str
    created_at:str
    tax:float
    amount:float
    project_number:str
    project_name:str
    customer_id:str
    project_id:str
    customer_name:str
    expected_date_of_payment:str

class BillsResult(TypedDict):
    total: int
    returned: int
    order_by: str
    order_dir: Literal["asc", "desc"]
    items: List[BillRow]

ALLOWED_ORDER_BY_BILLS = {"created_at", "amount", "project_id", "customer_id"}

@mcp_bills.tool(
    name="search_bills",
    description="Query invoice lists by project and customer. Accepts array strings. Returns up to 5 rows."
)
def bills_get(
    # Cho phép Claude gửi list thật hoặc chuỗi JSON/CSV
    project_ids: Annotated[Optional[Union[List[str], str]], "List of project IDs"] = None,
    customer_ids: Annotated[Optional[Union[List[str], str]], "List of customer IDs"] = None,
    created_at_from: Annotated[Optional[str], "Created date from (ISO 8601)"] = None,
    created_at_to: Annotated[Optional[str], "Created date to (ISO 8601)"] = None,
    order_by: Annotated[str, f"Sort by one of: {', '.join(sorted(ALLOWED_ORDER_BY_BILLS))}"] = "created_at",
    order_dir: Annotated[Literal["asc", "desc"], "Sort direction"] = "desc",
) -> BillsResult:
    """
    Tìm hóa đơn theo danh sách project_id / customer_id và khoảng thời gian tạo.
    Trả tối đa 5 bản ghi, mặc định sắp xếp theo created_at desc.
    """

    # Chuẩn hoá input từ Claude
    project_ids = _norm_str_list(project_ids)
    customer_ids = _norm_str_list(customer_ids)

    # Ràng buộc: ít nhất một trong hai nên có để tránh full-scan (tuỳ bạn muốn bắt buộc hay không)
    if not project_ids and not customer_ids and not (created_at_from or created_at_to):
        raise ValueError("Provide at least one filter: project_ids, customer_ids, or created_at range.")

    if order_by not in ALLOWED_ORDER_BY_BILLS:
        order_by = "created_at"
    if order_dir not in ("asc", "desc"):
        order_dir = "desc"

    where_parts = ["pl.is_deleted = false"]
    params: dict = {}

    if project_ids:
        where_parts.append("pl.project_id IN :project_ids")
        params["project_ids"] = tuple(project_ids)

    if customer_ids:
        where_parts.append("pl.customer_id IN :customer_ids")
        params["customer_ids"] = tuple(customer_ids)

    if created_at_from:
        where_parts.append("pl.created_at >= :created_at_from")
        params["created_at_from"] = created_at_from

    if created_at_to:
        where_parts.append("pl.created_at <= :created_at_to")
        params["created_at_to"] = created_at_to

    where_sql = " AND ".join(where_parts)

    # Đếm tổng
    count_sql = f"""
        SELECT COUNT(*) AS total
        FROM payment_plans
        WHERE {where_sql}
    """

    # Lấy dữ liệu (giới hạn 5)
    data_sql = f"""
        SELECT
            pl.id as bill_number,
            pl.created_at,
            pl.tax,
            pl.amount,
            p.project_number,
            p.name as project_name,
            c.id as customer_id,
            p.id as project_id,
            c.name as customer_name,
            pl.execution_date as expected_date_of_payment
        FROM payment_plans pl 
        LEFT JOIN projects p on p.id = pl.project_id
        LEFT JOIN customers c on c.id = pl.customer_id
        WHERE {where_sql}
        ORDER BY {order_by} {order_dir}
        LIMIT 5
    """

    with SessionLocal() as db:
        total = db.execute(text(count_sql), params).scalar_one()
        rows = db.execute(text(data_sql), params).mappings().all()

    items = _rows_to_dicts(rows)

    # Ensure order_dir has the Literal type for the return value
    order_dir_out = cast(Literal["asc", "desc"], order_dir)

    return {
        "total": int(total),
        "returned": len(items),
        "order_by": order_by,
        "order_dir": order_dir_out,
        "items": items,
    }

class BillDetailsInfo(BaseModel):
    attribute: str|None = Field(None, description="Name of the specific item or task in the invoice")
    product: str|None = Field(None, description="Name or code of the product or service provided")
    quantity: int|None = Field(None, description="Quantity of items")
    tax_amount: float = Field(..., description="Tax amount(VND)")         # 0.1 = 10%
    amount: int = Field(..., description="Amount before tax (VND)")        # số tiền trước thuế (tổng dòng)

    @field_validator("quantity")
    @classmethod
    def _quantity_positive(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("quantity must be > 0")
        return v

    # @field_validator("tax")
    # @classmethod
    # def _tax_range(cls, v: float) -> float:
    #     if not (0.0 <= v <= 1.0):
    #         raise ValueError("tfoax must be in [0.0, 1.0] (e.g., 0.1 r 10%)")
    #     return v

    @field_validator("amount")
    @classmethod
    def _non_negative_money(cls, v: int) -> int:
        if v < 0:
            raise ValueError("money fields must be >= 0")
        return v


class BillCreateInfo(BaseModel):
    id: str|None = Field(None, description="Bill ID")
    customer_id: str = Field(..., description="Customer ID")
    payer_code: str = Field(..., description="Payer code")
    project_id: str = Field(..., description="Project or construction ID related to this bill")
    payment_date: str|None = Field(None, description="Payment date (format: YYYY-MM-DD)")                 # "YYYY-MM-DD"
    expected_date_of_payment: str|None = Field(None, description="Expected payment date")     # "YYYY-MM-DD"
    execution_team: str|None = Field(None, description="Team or department executing the project")
    details: list[BillDetailsInfo] = Field(..., description="Detailed list of items in the bill")

    @field_validator("payment_date", "expected_date_of_payment")
    @classmethod
    def _is_iso_date(cls, v: str) -> str:
        date.fromisoformat(v)
        return v

    @field_validator("details")
    @classmethod
    def _non_empty_details(cls, v: list[BillDetailsInfo]) -> list[BillDetailsInfo]:
        if not v:
            raise ValueError("details must not be empty")
        return v

    @field_validator("project_id", "customer_id", "payer_code")
    @classmethod
    def _non_empty_and_exits_in_db(cls, v: str, info: ValidationInfo) -> str:
        # 1) không rỗng
        if not isinstance(v, str) or not v.strip():
            raise ValueError(f"{info.field_name} must not be empty")
        v = v.strip()

        # 2) ánh xạ field -> (table, column, nhãn)
        #   - Điều chỉnh tên bảng/cột theo schema thực tế của bạn.
        mapping = {
            "project_id": ("projects", "id", "project_id"),
            "customer_id": ("customers", "id", "customer_id"),
            "payer_code": ("customers", "id", "payer_code"),
        }

        table, col, label = mapping.get(info.field_name, (None, None, None))
        if table is None:
            # không ràng buộc DB cho field lạ
            return v

        # 3) kiểm tra tồn tại trong DB (truy vấn nhẹ, LIMIT 1)
        with SessionLocal() as db:
            row = db.execute(
                text(f"SELECT 1 FROM {table} WHERE {col} = :val LIMIT 1"),
                {"val": v}
            ).first()

        if row is None:
            raise ValueError(f"{label} '{v}' does not exist in {table}.{col}")

        return v


@mcp_bills.tool(
    name="create_bill",
    description="Create bill",
)
def bills_create(
    information_create_invoice: Annotated[BillCreateInfo, Field(description="Information Create Invoice")]
):
    """Create a PaymentPlan and its details from the provided BillCreateInfo.

    Behaviour / contract:
    - Input: a validated BillCreateInfo (Pydantic will validate formats and required fields).
    - Persist a PaymentPlan record and PaymentPlanDetail rows inside a DB transaction.
    - Compute totals from details: amount (sum of detail.amount) and tax (sum of detail.tax_amount).
    - Return a summary dict with created payment plan id and created rows.
    """

    # Pydantic ensures the shape/validation; convert to native objects
    info: BillCreateInfo = information_create_invoice

    # Compute totals
    total_amount = sum(int(d.amount) for d in info.details)
    total_tax_amount = sum(int(d.tax_amount) for d in info.details)

    # Build PaymentPlan instance
    plan = PaymentPlan(
        # id is generated by the before_insert listener, so don't set it here
        project_id=info.project_id,
        customer_id=info.customer_id,
        payer_code=info.payer_code,
        execution_team=info.execution_team,
        execution_date=date.fromisoformat(info.expected_date_of_payment),
        amount=total_amount,
        tax=total_tax_amount,
        created_at=datetime.now(),
        is_deleted=False,
    )

    # Attach details
    for d in info.details:
        detail = PaymentPlanDetail(
            attribute=d.attribute,
            product=d.product,
            quantity=d.quantity,
            amount=d.amount,
            tax_amount=d.tax_amount,
            created_at=datetime.now(),
        )
        plan.details.append(detail)

    # Persist in DB
    db = SessionLocal()
    try:
        db.add(plan)
        db.commit()
        # Refresh to populate generated fields (like id)
        db.refresh(plan)

        # Prepare return payload
        items = []
        for d in plan.details:
            items.append({
                "id": getattr(d, "id", None),
                "attribute": d.attribute,
                "product": d.product,
                "quantity": d.quantity,
                "tax": float(d.tax) if d.tax is not None else None,
                "amount": float(getattr(d, "amount")) if getattr(d, "amount") is not None else None
            })

        return {
            "bill_id": plan.id,
            "customer_id": plan.customer_id,
            "project_id": plan.project_id,
            "amount": float(getattr(plan, "amount")) if getattr(plan, "amount") is not None else None,
            "tax": float(getattr(plan, "tax")) if getattr(plan, "tax") is not None else None,
            "details_created": len(items),
            "details": items,
        }
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

@mcp_bills.prompt(
    name="bills_create_prompt",
    description="Details of the bill creation action"
)
def bills_create_prompt():
    return """
    Before performing the bill creation action:
        1. Confirm that the user has filled in all the **required information**.
        2. Confirm with the user
    """


@mcp_bills.tool()
def bills_update():
    return "Sorry !!! Function not implemented yet"

@mcp_bills.tool()
def bills_list():
    return "Sorry !!! Function not implemented yet"

@mcp_bills.tool()
def bills_list_by_creation_date():
   return "Sorry !!! Function not implemented yet"
