from fastmcp import FastMCP
from mcp_servers.mcp_projects import mcp_projects
from mcp_servers.mcp_bills import mcp_bills
from mcp_servers.mcp_payment import mcp_payment
from mcp_servers.mcp_customer import mcp_customers
from mcp_servers.mcp_user import mcp_users
import asyncio

main_mcp = FastMCP(name="MainApp")

async def setup():
    await main_mcp.import_server(mcp_projects, prefix="projects")
    await main_mcp.import_server(mcp_bills, prefix="bills")
    await main_mcp.import_server(mcp_payment, prefix="payment")
    await main_mcp.import_server(mcp_customers, prefix="customers")
    await main_mcp.import_server(mcp_users, prefix="users")

if __name__ == "__main__":
    asyncio.run(setup())
    main_mcp.run(transport="http", host="0.0.0.0", port=8000)