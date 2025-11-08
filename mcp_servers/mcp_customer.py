from __future__ import annotations
from fastmcp import FastMCP
from typing import Optional, Literal, TypedDict, List, Annotated, Union
from datetime import datetime, date, time
from decimal import Decimal
from uuid import UUID
from enum import Enum
from sqlalchemy.sql import text
from db.connection import SessionLocal

mcp_customers = FastMCP("customers")

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

class CustomerRow(TypedDict, total=False):
    id: Union[int, str]
    name: Optional[str]
    email: Optional[str]
    phone_number: Optional[str]
    created_at: Optional[str]
    is_deleted: Optional[bool]

class CustomerSearchResult(TypedDict):
    total: int           # tổng số bản ghi thỏa điều kiện
    returned: int        # số bản ghi đã trả về (<=5)
    order_by: str
    order_dir: Literal["asc", "desc"]
    items: List[CustomerRow]


ALLOWED_ORDER_BY = {"id", "name", "email", "phone_number", "created_at"}


@mcp_customers.tool(
    name="search_customers",
    description="Query customers with dynamic filters; safe sort by id, name, email, phone_number. Returns up to 5 rows."
)
def customers_search(
    id: Annotated[Optional[str], "Customer ID (String)"] = None,
    name: Annotated[Optional[str], "Customer name (fuzzy match, ILIKE)"] = None,
    email: Annotated[Optional[str], "Exact email or suffix with % for LIKE"] = None,
    phone_number: Annotated[Optional[str], "Exact phone or suffix with % for LIKE"] = None,
    created_at_from: Annotated[Optional[str], "Created-at from (ISO 8601)"] = None,
    created_at_to: Annotated[Optional[str], "Created-at to (ISO 8601)"] = None,
    order_by: Annotated[str, "Sort column: id, name, email, phone_number, created_at"] = "created_at",
    order_dir: Annotated[Literal["asc", "desc"], "Sort direction"] = "desc",
) -> CustomerSearchResult:
    """
    Truy vấn bảng customers với lọc động & sắp xếp an toàn, trả tối đa 5 bản ghi.
    Ghi chú: ILIKE dùng cho Postgres. Nếu dùng DB khác, thay bằng LOWER(...) LIKE LOWER(...).
    """


    # --- chuẩn hóa sort ---
    if order_by not in ALLOWED_ORDER_BY:
        order_by = "created_at"
    if order_dir not in ("asc", "desc"):
        order_dir = "desc"

    where_parts = ["c.is_deleted = false"]
    params: dict = {}

    # --- filters ---
    if id is not None:
        where_parts.append("c.id = :id")
        params["id"] = id

    if name:
        where_parts.append("c.name ILIKE :name")
        params["name"] = f"%{name}%"

    if email:
        # Cho phép LIKE nếu người dùng truyền ký tự wildcard
        if "%" in email or "_" in email:
            where_parts.append("c.email ILIKE :email")
            params["email"] = email
        else:
            where_parts.append("c.email = :email")
            params["email"] = email

    if phone_number:
        if "%" in phone_number or "_" in phone_number:
            where_parts.append("c.phone_number ILIKE :phone_number")
            params["phone_number"] = phone_number
        else:
            where_parts.append("c.phone_number = :phone_number")
            params["phone_number"] = phone_number

    if created_at_from:
        where_parts.append("c.created_at >= :created_at_from")
        params["created_at_from"] = created_at_from
    if created_at_to:
        where_parts.append("c.created_at <= :created_at_to")
        params["created_at_to"] = created_at_to

    where_sql = " AND ".join(where_parts)

    count_sql = f"""
        SELECT COUNT(*) AS total
        FROM customers c
        WHERE {where_sql}
    """

    data_sql = f"""
        SELECT
            c.id,
            c.name,
            c.email,
            c.phone_number,
            c.created_at,
            c.is_deleted
        FROM customers c
        WHERE c.is_contractor = false AND {where_sql}
        ORDER BY {order_by} {order_dir}
        LIMIT 5
    """

    with SessionLocal() as db:
        total = db.execute(text(count_sql), params).scalar_one()
        rows = db.execute(text(data_sql), params).mappings().all()

    items = _rows_to_dicts(rows)

    return {
        "total": int(total),
        "returned": len(items),
        "order_by": order_by,
        "order_dir": order_dir,
        "items": items,
    }

@mcp_customers.tool()
def customers_create():
    return "Sorry !!! Function not implemented yet"

@mcp_customers.tool()
def customers_update():
    return "Sorry !!! Function not implemented yet"

@mcp_customers.tool()
def customers_list():
    return "Sorry !!! Function not implemented yet"

@mcp_customers.tool()
def customers_list_by_creation_date():
   return "Sorry !!! Function not implemented yet"

