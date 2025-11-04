from mcp.server.fastmcp import FastMCP
# import sys
# import os

# # Lấy đường dẫn tới thư mục cha (chứa folder db)
# BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# sys.path.append(BASE_DIR)
from db.connection import SessionLocal
from db.models.projects import Projects

mcp_projects = FastMCP("projects")

@mcp_projects.tool()
def get_projects(include_deleted: bool = False):
    """Trả về danh sách project từ database"""
    session = SessionLocal()
    try:
        query = session.query(Projects)
        if not include_deleted:
            query = query.filter(Projects.is_deleted == False)
        results = query.all()
        return [
            {"id": p.id, "name": p.name, "tax": p.tax, "is_deleted": p.is_deleted}
            for p in results
        ]
    finally:
        session.close()

