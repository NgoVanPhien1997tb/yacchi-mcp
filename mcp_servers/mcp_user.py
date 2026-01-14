from __future__ import annotations
from fastmcp import FastMCP
from typing import Optional, Literal, TypedDict, List, Annotated, Union
from datetime import datetime, date, time
from decimal import Decimal
from uuid import UUID
from enum import Enum
from sqlalchemy.sql import text
from db.connection import SessionLocal

mcp_users = FastMCP("users")

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

class UserRow(TypedDict, total=False):
    id: Union[int, str]
    username: Optional[str]
    email: Optional[str]
    full_name: Optional[str]
    phone_number: Optional[str]
    role: Optional[str]
    status: Optional[int]
    created_at: Optional[str]
    is_deleted: Optional[bool]

class UserSearchResult(TypedDict):
    total: int           # total number of records matching the criteria
    returned: int        # number of records returned (<=5)
    order_by: str
    order_dir: Literal["asc", "desc"]
    items: List[UserRow]


ALLOWED_ORDER_BY = {"id", "username", "email", "full_name", "role", "created_at"}


@mcp_users.tool(
    name="search_users",
    description="Query users with dynamic filters; safe sort by id, username, email, full_name, role. Returns up to 5 rows."
)
def users_search(
    id: Annotated[Optional[str], "User ID (String)"] = None,
    username: Annotated[Optional[str], "Username (fuzzy match, ILIKE)"] = None,
    email: Annotated[Optional[str], "Exact email or suffix with % for LIKE"] = None,
    full_name: Annotated[Optional[str], "Full name (fuzzy match, ILIKE)"] = None,
    role: Annotated[Optional[str], "User role (exact match)"] = None,
    phone_number: Annotated[Optional[str], "Exact phone or suffix with % for LIKE"] = None,
    created_at_from: Annotated[Optional[str], "Created-at from (ISO 8601)"] = None,
    created_at_to: Annotated[Optional[str], "Created-at to (ISO 8601)"] = None,
    order_by: Annotated[str, "Sort column: id, username, email, full_name, role, created_at"] = "created_at",
    order_dir: Annotated[Literal["asc", "desc"], "Sort direction"] = "desc",
) -> UserSearchResult:
    """
    Query users table with dynamic filters & safe sorting, returns up to 5 records.
    Note: ILIKE is used for Postgres. For other DBs, use LOWER(...) LIKE LOWER(...).
    """

    # --- normalize sort ---
    if order_by not in ALLOWED_ORDER_BY:
        order_by = "created_at"
    if order_dir not in ("asc", "desc"):
        order_dir = "desc"

    where_parts = ["u.is_deleted = false"]
    params: dict = {}

    # --- filters ---
    if id is not None:
        where_parts.append("u.id = :id")
        params["id"] = id

    if username:
        where_parts.append("u.username ILIKE :username")
        params["username"] = f"%{username}%"

    if email:
        # Allow LIKE if user passes wildcard characters
        if "%" in email or "_" in email:
            where_parts.append("u.email ILIKE :email")
            params["email"] = email
        else:
            where_parts.append("u.email = :email")
            params["email"] = email

    if full_name:
        where_parts.append("u.full_name ILIKE :full_name")
        params["full_name"] = f"%{full_name}%"

    if role:
        where_parts.append("u.role = :role")
        params["role"] = role

    if phone_number:
        if "%" in phone_number or "_" in phone_number:
            where_parts.append("u.phone_number ILIKE :phone_number")
            params["phone_number"] = phone_number
        else:
            where_parts.append("u.phone_number = :phone_number")
            params["phone_number"] = phone_number

    if created_at_from:
        where_parts.append("u.created_at >= :created_at_from")
        params["created_at_from"] = created_at_from
    if created_at_to:
        where_parts.append("u.created_at <= :created_at_to")
        params["created_at_to"] = created_at_to

    where_sql = " AND ".join(where_parts)

    count_sql = f"""
        SELECT COUNT(*) AS total
        FROM users u
        WHERE {where_sql}
    """

    data_sql = f"""
        SELECT
            u.id,
            u.username,
            u.email,
            u.full_name,
            u.phone_number,
            u.role,
            u.status,
            u.created_at,
            u.is_deleted
        FROM users u
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


@mcp_users.tool(
    name="update_user",
    description="Update user details",
)
def users_update(
        id: Annotated[str, "User ID"],
        username: Annotated[Optional[str], "Username"] = None,
        email: Annotated[Optional[str], "User email"] = None,
        full_name: Annotated[Optional[str], "User full name"] = None,
        phone_number: Annotated[Optional[str], "User phone number"] = None,
        role: Annotated[Optional[str], "User role"] = None,
        status: Annotated[Optional[int], "User status"] = None,
):
    # build SET clause dynamically
    set_parts: List[str] = []
    params: dict = {"id": id}
    
    if username is not None:
        set_parts.append("username = :username")
        params["username"] = username
    if email is not None:
        set_parts.append("email = :email")
        params["email"] = email
    if full_name is not None:
        set_parts.append("full_name = :full_name")
        params["full_name"] = full_name
    if phone_number is not None:
        set_parts.append("phone_number = :phone_number")
        params["phone_number"] = phone_number
    if role is not None:
        set_parts.append("role = :role")
        params["role"] = role
    if status is not None:
        set_parts.append("status = :status")
        params["status"] = status

    if not set_parts:
        return {"error": "no fields to update"}

    set_sql = ", ".join(set_parts)
    update_sql = f"""
        UPDATE users
        SET {set_sql}
        WHERE id = :id AND is_deleted = false
        RETURNING id, username, email, full_name, phone_number, role, status, created_at, is_deleted
    """

    with SessionLocal() as db:
        result = db.execute(text(update_sql), params)
        try:
            updated = result.mappings().first()
        except Exception:
            updated = None
        # commit so change is persisted
        db.commit()

    if not updated:
        return {"error": "user not found or already deleted"}

    return {k: _to_jsonable(v) for k, v in dict(updated).items()}
