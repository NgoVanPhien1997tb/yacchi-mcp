from mcp.server.fastmcp import FastMCP
# import sys
# import os

# # Lấy đường dẫn tới thư mục cha (chứa folder db)
# BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# sys.path.append(BASE_DIR)
from db.connection import SessionLocal
from db.models.projects import Projects

mcp_customers = FastMCP("customers")

@mcp_customers.tool()
def customers_get():
    return "Hello from project_get"

@mcp_customers.tool()
def customers_create():
    return "Hello from project_get"

@mcp_customers.tool()
def customers_update():
    return "Hello from project_get"

@mcp_customers.tool()
def customers_list():
    return "Hello from project_get"

@mcp_customers.tool()
def customers_list_by_creation_date():
   return "Hello from project_get"

