from __future__ import annotations
from typing import Optional, Literal, TypedDict, List, Annotated, Union
from fastmcp import FastMCP
from db.connection import SessionLocal
from sqlalchemy.sql import text
from datetime import date, datetime, time
from decimal import Decimal
from uuid import UUID
from enum import Enum
import json

mcp_projects = FastMCP("projects")

# ---- JSON-safe helpers -------------------------------------------------------
def _to_jsonable(v):
    if isinstance(v, (datetime, date, time)):
        return v.isoformat()
    if isinstance(v, Decimal):
        return float(v)  # hoặc str(v) nếu muốn giữ chính xác tuyệt đối
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
        # CSV / single token: "A,B" hoặc "A"
        return [x.strip() for x in s.split(",") if x.strip()]
    # tuple/set…
    return [str(x) for x in list(val)]
# -----------------------------------------------------------------------------

class ProjectRow(TypedDict, total=False):
    id: str  # id có thể là int hoặc str, và có thể NULL
    name: Optional[str]  # cho phép NULL
    project_number: Optional[str]  # cho phép NULL
    created_at: Optional[str]  # cho phép NULL (nếu DB có bản ghi thiếu)
    completed_date: Optional[str]
    end_date: Optional[str]
    is_deleted: Optional[bool]

class ProjectGetResult(TypedDict):
    total: int           # tổng số bản ghi thỏa điều kiện
    returned: int        # số bản ghi đã trả về (tối đa 5)
    order_by: str
    order_dir: Literal["asc", "desc"]
    items: List[ProjectRow]

ALLOWED_ORDER_BY = {
    "id", "name", "project_number", "created_at", "completed_date", "end_date"
}

@mcp_projects.tool(
    name="project_search",
    description="Query projects with dynamic filters; safe sort by id, name, project_number, created_at, completed_date, end_date. Returns up to 5 rows."
)
def project_search(
    id: Annotated[Optional[str], "Project ID (str). If string digits, will be cast to int"] = None,
    name: Annotated[Optional[str], "Project name (ILIKE fuzzy)"] = None,
    project_number: Annotated[Optional[str], "Exact project number/code"] = None,
    created_at_from: Annotated[Optional[str], "Created at from (ISO 8601)"] = None,
    created_at_to: Annotated[Optional[str], "Created at to (ISO 8601)"] = None,
    completed_date_from: Annotated[Optional[str], "Completed date from (ISO 8601)"] = None,
    completed_date_to: Annotated[Optional[str], "Completed date to (ISO 8601)"] = None,
    end_date_from: Annotated[Optional[str], "End date from (ISO 8601)"] = None,
    end_date_to: Annotated[Optional[str], "End date to (ISO 8601)"] = None,
    order_by: Annotated[str, "Sort column (id, name, project_number, created_at, completed_date, end_date)"] = "created_at",
    order_dir: Annotated[Literal["asc", "desc"], "Sort direction"] = "desc",
) -> ProjectGetResult:
    """
    Truy vấn bảng projects với lọc động, sắp xếp an toàn.
    Trả về tối đa 5 bản ghi đầu tiên theo thứ tự đã chọn.
    """

    # --- normalize sort ---
    if order_by not in ALLOWED_ORDER_BY:
        order_by = "created_at"
    if order_dir not in ("asc", "desc"):
        order_dir = "desc"

    # --- base where ---
    where_parts = ["p.is_deleted = false"]
    params: dict = {}

    # --- filters ---
    if id is not None:
        # nhận cả str|int, nếu str là số thì ép int
        if isinstance(id, str) and id.isdigit():
            id = int(id)
        where_parts.append("p.id = :id")
        params["id"] = id

    if name:
        # Postgres: ILIKE; nếu không dùng Postgres, thay bằng LOWER(...) LIKE LOWER(:name)
        where_parts.append("p.name ILIKE :name")
        params["name"] = f"%{name}%"

    if project_number:
        where_parts.append("p.project_number = :project_number")
        params["project_number"] = project_number

    if created_at_from:
        where_parts.append("p.created_at >= :created_at_from")
        params["created_at_from"] = created_at_from
    if created_at_to:
        where_parts.append("p.created_at <= :created_at_to")
        params["created_at_to"] = created_at_to

    if completed_date_from:
        where_parts.append("p.completed_date >= :completed_date_from")
        params["completed_date_from"] = completed_date_from
    if completed_date_to:
        where_parts.append("p.completed_date <= :completed_date_to")
        params["completed_date_to"] = completed_date_to

    if end_date_from:
        where_parts.append("p.end_date >= :end_date_from")
        params["end_date_from"] = end_date_from
    if end_date_to:
        where_parts.append("p.end_date <= :end_date_to")
        params["end_date_to"] = end_date_to

    where_sql = " AND ".join(where_parts)

    count_sql = f"""
        SELECT COUNT(*) AS total
        FROM projects p
        WHERE {where_sql}
    """

    data_sql = f"""
        SELECT
            p.id,
            p.name,
            p.project_number,
            p.created_at,
            p.completed_date,
            p.end_date,
            p.is_deleted
        FROM projects p
        WHERE {where_sql}
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

class QuotationRow(TypedDict, total=False):
    project_id: Optional[str]
    project_code: Optional[str]
    project_number: Optional[str]
    tax: Optional[float]
    amount: Optional[float]
    total_amount: Optional[float]


class QuotationResult(TypedDict):
    total: int
    returned: int
    items: List[QuotationRow]

@mcp_projects.tool(
    name="cost_quotation_for_project",
    description="Query quotation information for projects by project id or code",
)
def cost_quotation_for_project(ids: Annotated[Optional[Union[List[str], str]], "List of project ids. Example: [\"PJ00001\",\"PJ00002\"]"] = None,
                               project_codes: Annotated[Optional[Union[List[str], str]], "List of project codes. Example: [\"25-1-ADMADM-0565\",\"5-1-ADMADM-05\"]"] = None) -> QuotationResult:
    ids = _norm_str_list(ids)
    project_codes = _norm_str_list(project_codes)
    # print(f"{ids} type : {type(ids)}")
    # --- Validate input ---
    if not ids and not project_codes:
        raise ValueError("Either 'ids' or 'project_codes' must be provided (non-empty).")

    # Nếu có nhưng rỗng []
    if ids is not None and len(ids) == 0 and (project_codes is None or len(project_codes) == 0):
        raise ValueError("Either 'ids' or 'project_codes' must be a non-empty list.")

    sql = """
            SELECT
                p.id as project_id,
                p.name as project_name,
                p.project_number as project_code,
                p.tax,
                p.amount,
                p.entry_cost as total_amount
            FROM projects p
            WHERE p.is_deleted = false
        """
    params = {}
    if ids and len(ids) > 0:
        sql += " AND p.id IN :ids"
        params["ids"] = tuple(ids)

    if project_codes and len(project_codes) > 0:
        sql += " AND p.project_number IN :project_code"
        params["project_code"] = tuple(project_codes)

    sql += " LIMIT 5"

    count_sql = f"""
            SELECT COUNT(*) FROM projects p
            WHERE p.is_deleted = false
        """

    if ids:
        count_sql += " AND p.id IN :ids"
    if project_codes:
        count_sql += " AND p.project_number IN :project_code"

    with SessionLocal() as db:
        total = db.execute(text(count_sql), params).scalar_one()
        rows = db.execute(text(sql), params).mappings().all()

    items = _rows_to_dicts(rows)

    return {
        "total": int(total),
        "returned": len(items),
        "items": items,
    }

@mcp_projects.tool(
    name="project_list_by_customer_ids",
    description="Query project list by customer ids",
)
def project_list_by_customer_ids(
    ids: Annotated[Optional[Union[List[str], str]], "List of customer ids"] = None
) -> ProjectGetResult:
    """
    Truy vấn danh sách dự án theo danh sách customer_id.
    Chỉ trả về tối đa 5 bản ghi, sắp xếp theo created_at DESC.
    """

    ids = _norm_str_list(ids)

    if not ids:
        raise ValueError("At least one customer_id must be provided.")

    where_sql = "p.is_deleted = false AND p.customer_id IN :ids"

    count_sql = f"""
        SELECT COUNT(*) FROM projects p
        WHERE {where_sql}
    """

    data_sql = f"""
        SELECT
            p.id,
            p.name,
            p.project_number,
            p.customer_id,
            p.created_at,
            p.completed_date,
            p.end_date,
            p.is_deleted
        FROM projects p
        WHERE {where_sql}
        ORDER BY p.created_at DESC
        LIMIT 5
    """

    with SessionLocal() as db:
        total = db.execute(text(count_sql), {"ids": tuple(ids)}).scalar_one()
        rows = db.execute(text(data_sql), {"ids": tuple(ids)}).mappings().all()

    items = _rows_to_dicts(rows)

    return {
        "total": int(total),
        "returned": len(items),
        "order_by": "created_at",
        "order_dir": "asc",
        "items": items,
    }

@mcp_projects.tool()
def project_create():
    return "Sorry !!! Function not implemented yet"

@mcp_projects.tool()
def project_update():
    return "Sorry !!! Function not implemented yet"

@mcp_projects.tool()
def project_list():
    return "Sorry !!! Function not implemented yet"

@mcp_projects.tool()
def get_list_projects_by_creation_date():
    return "Sorry !!! Function not implemented yet"
