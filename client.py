import asyncio
from fastmcp import Client

client = Client("http://localhost:8000/mcp")

async def call_tool(name: str):
    async with client:
        # result = await client.call_tool("weather_get_forecast", {"city": name})
        print("Call function here")
        response = await client.call_tool("customers_update_customer", {"id": "CS00000276", "name": "Đạt"})
        print(response)
        # response1 = await client.call_tool("bills_bills_get")
        # print(response1)

    #     weather_content = await client.read_resource("data://weather/cities/supported")
    
    # # Access the generated content
    #     print(weather_content[0].text)

        resources = await client.list_resources()
    # resources -> list[mcp.types.Resource]
    
    for resource in resources:
        print(f"Resource URI: {resource.uri}")
        print(f"Name: {resource.name}")
        print(f"Description: {resource.description}")
        print(f"MIME Type: {resource.mimeType}")
        # Access tags and other metadata
        if hasattr(resource, '_meta') and resource._meta:
            fastmcp_meta = resource._meta.get('_fastmcp', {})
            print(f"Tags: {fastmcp_meta.get('tags', [])}")
    
asyncio.run(call_tool("Ford"))