# client.py
import asyncio
from fastmcp.client import Client

async def main():
    async with Client("http://127.0.0.1:8000") as client:
        tools = await client.list_tools()
        print("TOOLS:", [t["name"] for t in tools])  # xem tên thực tế

        # gọi đúng tên như in ra ở trên
        # result = await client.call_tool("weather_get_forecast", {"city": "London"})
        # print("RESULT:", result)

if __name__ == "__main__":
    asyncio.run(main())
