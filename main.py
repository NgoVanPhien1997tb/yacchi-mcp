from fastmcp import FastMCP

mcp = FastMCP("My MCP Server")

@mcp.tool
def greet(name: str) -> str:
    return f"Hello, {name}!"

if __name__ == "__main__":
    mcp.run(transport="http", port=8000)

# from db.models.projects import Projects
# from db.connection import SessionLocal
# import asyncio
# from mcp import ClientSession
# from fastmcp import Client, FastMCP

# import asyncio
# from fastmcp import Client, FastMCP
# client = Client("http://127.0.0.1:8000/mcp")

# def hello():
#     print("A")
#     asyncio.sleep(2)
#     print("B")

# hello()

# async def main():
#     async with client:
#         # Basic server interaction
#         await client.ping()
        
#         # Execute operations
#         result = await client.call_tool("get_projects", {"include_deleted": False})
#         print(result)

# asyncio.run(main())
# def main():
#     print("Hello from yacchi-mcp!")
#     session = SessionLocal()
#     try:
#         projects = session.query(Projects).all()

#         for p in projects:
#             print(f"ID: {p.id}, Name: {p.name}, Deleted: {p.is_deleted}, Tax: {p.tax}")

#     finally:
#         session.close()

# if __name__ == "__main__":
#     main()
